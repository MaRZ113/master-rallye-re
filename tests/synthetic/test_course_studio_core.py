"""Course Studio core: writer contract, collision, scene, registry, project format (synthetic data only).

Tests that compare against game files (the Retail cooker reference) run only
when those files exist locally and are skipped otherwise; no game bytes are
stored in the repository.
"""
import json
import math
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src")]
sys.setrecursionlimit(100000)

from master_rallye.course_tag100 import parse_course_tag100_bytes  # noqa: E402
from master_rallye.course_tag1400 import parse_course_tag1400_bytes  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402
from master_rallye.studio import ai, collision, dx_build, materials, race, templates, textures, validate  # noqa: E402
from master_rallye.studio.build import register_course  # noqa: E402
from master_rallye.studio.importer import import_gxm, import_obj  # noqa: E402
from master_rallye.studio.model import (Checkpoint, CourseProject, Material, Mesh, load_project,  # noqa: E402
                                        save_project)

GAME = ROOT.parent
COOKED = GAME / "DataGx" / "Course" / "invspaingx"
RETAIL = GAME / "corpora" / "retail" / "Data.sma_unpacked"
CATALOG = ROOT / ".research-output" / "course-cap2" / "owner" / "courses.json"


def small_project():
    return templates.valley_course("UnitValley", size=160.0, cell=10.0, retail_textures=False)


def split_dx(data):
    m = parse_course_dx_bytes(data, "t")
    tree = parse_course_tag100_bytes(m.collision.bsp.raw, "t", allow_trailing=True)
    rest = m.collision.bsp.raw[tree.consumed_size:]
    return m, tree, rest[:44], parse_course_tag1400_bytes(rest[44:], "t")


class MaterialContract(unittest.TestCase):
    # (shader, alpha, clamp, secondary, noise) -> (address, effect, flags, slot mask) from the Retail census
    CASES = [
        (("ground", "opaque", "", False, True), (1, 0, "00000101", 11)),
        (("ground", "opaque", "u", False, True), (2, 0, "00000101", 11)),
        (("ground", "opaque", "v", False, True), (4, 0, "00000101", 11)),
        (("ground", "opaque", "uv", False, True), (0, 0, "00000101", 11)),
        (("object", "opaque", "", False, False), (1, 0, "00000101", 3)),
        (("sign", "blend", "", False, False), (1, 0, "01000101", 3)),
        (("tree", "cutout", "", False, False), (1, 0, "01010101", 3)),
        (("metal", "opaque", "", True, False), (1, 0, "00000101", 7)),
        (("water", "opaque", "", False, False), (1, 1, "00000101", 19)),
        (("puddle", "opaque", "", False, False), (1, 1, "00000101", 19)),
        (("waterall", "blend", "", False, False), (1, 2, "01000101", 3)),
    ]

    def test_record_fields_match_retail_census(self):
        for (shader, alpha, clamp, sec, noise), (addr, eff, flags, mask) in self.CASES:
            f = materials.encode_record_fields(shader=shader, alpha=alpha, clamp=clamp, mip=1.0, has_secondary=sec,
                                               has_noise=noise, has_base=True, scroll=shader == "waterall")
            self.assertEqual((f.address, f.effect, f.flags.hex(), f.slot_mask), (addr, eff, flags, mask), shader)

    def test_native_name_roundtrip(self):
        name = materials.native_name(label="Road", shader="ground", surface="tarmac", alpha="opaque", clamp="u",
                                     mip=1.0, scroll=None, noise=True)
        self.assertEqual(name, "Road $surfacetype(tarmac) $clamp(u) $shader(ground) $mip(1.0)Noise Pass")
        info = materials.parse_native_name(name)
        self.assertEqual((info["surface"], info["shader"], info["clamp"], info["noise"]), ("tarmac", "ground", "u", True))
        self.assertEqual(materials.surface_of_name("x $surfacetype(gravel) $surfacetype(mud)"), "gravel")


class DxWriter(unittest.TestCase):
    def setUp(self):
        self.project = small_project()
        self.build = dx_build.build_course_dx(self.project)

    def test_reread_by_independent_parsers(self):
        self.assertTrue(dx_build.verify_course_dx(self.build.dx, self.build)["ok"])

    def test_header_bounds_and_land_database(self):
        m, tree, b1339, land = split_dx(self.build.dx)
        self.assertEqual(struct.unpack_from("<4I", self.build.dx), (0xD00D, 135, 1337, len(m.vertices.positions)))
        tag, cx, cy, cz, r, *box = struct.unpack("<I3ff3f3f", b1339)
        pts = m.vertices.positions
        self.assertEqual(tag, 1339)
        self.assertAlmostEqual(r, max(math.dist((cx, cy, cz), p) for p in pts), places=2)
        terrain = self.project.meshes[0]
        self.assertEqual(len(land.records), sum(1 for t in range(terrain.triangle_count)
                                                 if dx_build.triangle_area(*terrain.triangle_points(t)) > 1e-7))
        # record 0 = first terrain triangle wound (c, b, a); plane normal of that winding points down for ground
        a, b, c = terrain.triangle_points(0)
        rec = land.records[0]
        self.assertEqual([round(v, 3) for v in rec.float_prefix], [round(v, 3) for v in (*c, *b, *a)])
        self.assertLess(rec.float_suffix[1], 0.0)
        # grid z-major, triangle-AABB membership
        x0, _, z0 = land.vector_a
        for idx, r in enumerate(land.records[:200]):
            p = r.float_prefix
            i = int((min(p[0], p[3], p[6]) - x0) // 20.0)
            j = int((min(p[2], p[5], p[8]) - z0) // 20.0)
            self.assertIn(idx, land.cells[j * land.dimension_0 + i].entries)

    def test_render_winding_and_noise_uv(self):
        m, *_ = split_dx(self.build.dx)
        rec = next(r for r in m.course_root_records if r.texture_slots[2].value == "noise-tga")
        I, P = m.local_indices, m.vertices.positions
        tri = [P[rec.vertex_base + I[rec.index_start + k]] for k in range(3)]
        n = dx_build.triangle_normal(*tri)
        self.assertLess(n[1], 0.0, "render winding (b, a, c) of an up-facing authoring triangle")
        u1 = m.uv_sets[1].values[rec.vertex_base]
        p = P[rec.vertex_base]
        self.assertAlmostEqual(((u1[0] - p[0] / 37.0 - 0.5) / 5.0) % 1.0, 0.0, places=3)

    def test_large_material_splits_at_65536_vertices(self):
        project = CourseProject(name="Big")
        project.materials["g"] = Material("g", textures=["g-tga", None, None])
        mesh = Mesh(id="m", name="grid", role="terrain", materials=["g"])
        n = 260
        for j in range(n + 1):
            for i in range(n + 1):
                mesh.positions += [i * 2.0, math.sin(i * 0.3) + math.cos(j * 0.2), j * 2.0]
        for j in range(n):
            for i in range(n):
                a = j * (n + 1) + i
                for tri in ((a, a + n + 1, a + n + 2), (a, a + n + 2, a + 1)):
                    mesh.triangles += tri
                    mesh.tri_material.append(0)
        project.meshes.append(mesh)
        project.route.points = [(0, 0, 0), (100, 0, 100)]
        build = dx_build.build_course_dx(project)
        recs = build.report["records"]
        self.assertGreater(len(recs), 1)
        self.assertTrue(all(r["vertices"] <= 65536 for r in recs))
        self.assertTrue(dx_build.verify_course_dx(build.dx, build)["ok"])

    @unittest.skipUnless((COOKED / "invspaingx.gxm").exists() and (COOKED / "invspaingx.dx").exists(),
                         "game-cooked reference not present")
    def test_matches_the_retail_cooker(self):
        """Same GXM through the game's own cooker and through Studio: identical records/grid/strings."""
        project = import_gxm(COOKED / "invspaingx.gxm")
        build = dx_build.build_course_dx(project)
        mr, _, br, lr = split_dx((COOKED / "invspaingx.dx").read_bytes())
        mo, _, bo, lo = split_dx(build.dx)
        key = lambda m: sorted((tuple(s.value for s in r.texture_slots), r.unknown_0x14, r.unknown_0x18,
                                round(r.unknown_0x1c_float, 3), bytes(r.flags_0x20), r.unknown_0x24)
                               for r in m.course_root_records)
        self.assertEqual(key(mr), key(mo))
        self.assertEqual([s.raw_bytes for s in lr.strings], [s.raw_bytes for s in lo.strings])
        self.assertEqual((lr.dimension_0, lr.dimension_1), (lo.dimension_0, lo.dimension_1))
        valid = [r for r in lr.records if not any(math.isnan(v) for v in r.float_suffix)]
        self.assertEqual(len(valid), len(lo.records))   # the cooker keeps 3 degenerate (NaN-plane) records
        self.assertTrue(all(max(abs(x - y) for x, y in zip(a.float_prefix, b.float_prefix)) < 0.02   # cooker float rounding
                            for a, b in zip(valid, lo.records)))
        ref, ours = struct.unpack("<I3ff3f3f", br), struct.unpack("<I3ff3f3f", bo)
        self.assertTrue(all(abs(x - y) < 1e-3 for x, y in zip(ref, ours)))


class Collision(unittest.TestCase):
    def test_box_on_ground_is_solid_and_extractable(self):
        project = small_project()
        tree, prov, stats = collision.build_tree(project)
        report = collision.validate_tree(project, tree, spacing=8.0)
        self.assertEqual(report.holes, 0)
        self.assertEqual(report.route_blocked, 0)
        house = next(m for m in project.meshes if m.role == "collision")
        lo, hi = house.bounds()
        centre = ((lo[0] + hi[0]) / 2, hi[1] - 1.0, (lo[2] + hi[2]) / 2)
        self.assertTrue(collision.classify(tree, centre))
        self.assertFalse(collision.classify(tree, (centre[0], hi[1] + 2.0, centre[2])))
        # exact boundary extraction around the house: its walls come back
        tris, xs = collision.extract_native_collision(tree, (lo[0] - 3, lo[1] - 1, lo[2] - 3), (hi[0] + 3, hi[1] + 3, hi[2] + 3))
        self.assertGreater(len(tris), 4)
        tops = [t for t in tris if all(abs(p[1] - hi[1]) < 0.05 for p in t)]
        area = sum(dx_build.triangle_area(*t) for t in tops)
        self.assertAlmostEqual(area, (hi[0] - lo[0]) * (hi[2] - lo[2]), delta=1.0)

    def test_difference_detects_a_new_blocker(self):
        project = small_project()
        old, *_ = collision.build_tree(project)
        p = project.route.points[len(project.route.points) // 2]
        tris = collision.box_proxy((p[0] - 3, p[1] - 3, p[2] - 3), (p[0] + 3, p[1] + 4, p[2] + 3))
        mesh = collision.triangles_to_mesh(tris, name="block", role="collision", material="collision", source="t")
        project.meshes.append(mesh)
        new, *_ = collision.build_tree(project)
        diff = collision.tree_difference(old, new, project, spacing=2.0)
        self.assertTrue(any(now and not was for *_, was, now in diff))
        report = collision.validate_tree(project, new, spacing=8.0)
        self.assertGreater(report.route_blocked, 0, "a blocker on the road is reported")

    def test_convex_hull_outward(self):
        pts = [(x, y, z) for x in (0, 2) for y in (0, 1) for z in (0, 3)] + [(1, 0.5, 1.5)]
        hull = collision.convex_hull(pts)
        self.assertEqual(len(hull), 12)
        c = (1, 0.5, 1.5)
        for t in hull:
            n = dx_build.triangle_normal(*t)
            self.assertGreater(sum(n[k] * (t[0][k] - c[k]) for k in range(3)), 0)


class SceneAndAi(unittest.TestCase):
    @unittest.skipUnless((RETAIL / "DataScene" / "RaceTest" / "France1.xml").exists(), "Retail scene not present")
    def test_racetest_has_native_checkpoints(self):
        from master_rallye.course_xml import parse_course_xml_bytes
        project = small_project()
        xml, report = race.build_racetest(project, RETAIL / "DataScene" / "RaceTest" / "France1.xml")
        doc = parse_course_xml_bytes(xml)
        names = [e.name for e in doc.eggs]
        self.assertEqual(sum(1 for n in names if n.startswith("SplitTime") and "-" not in n), len(project.checkpoints))
        self.assertEqual(sum(1 for n in names if n.startswith("SplitTime") and "-" in n), 4 * len(project.checkpoints))
        text = xml.decode()
        self.assertIn('Name="numberOfSplitTimePoints" Type="Int" Value="%d"' % len(project.checkpoints), text)
        self.assertIn("course\\unitvalley\\unitvalley", text)
        self.assertIn("ICont/unitvalley", text)
        scene = race.read_scene_bytes(xml) if hasattr(race, "read_scene_bytes") else None
        self.assertEqual(report["checkpoints"], len(project.checkpoints))

    def test_sfl_and_ai_trace_follow_route(self):
        project = small_project()
        line = ai.raceline(project)
        sfl = ai.sfl_bytes(project, line)
        a, b = line[0], line[1]
        path = ai.simulate_ai_path(sfl, line[0], math.degrees(math.atan2(b[0] - a[0], b[2] - a[2])), stop_at=line[-1])
        self.assertLess(math.dist(path[-1], line[-1]), 30.0)

    def test_route_checks(self):
        project = small_project()
        self.assertFalse([i for i in ai.route_issues(project) if i.severity == "error"])
        project.checkpoints.reverse()
        self.assertTrue(any("before the previous" in i.message for i in ai.route_issues(project)))
        wide = ai.limit_lists(project)
        project.limits.mode = "wide"
        self.assertGreater(abs(ai.limit_lists(project)["LeftOuterLimit"][0][2] - project.route.points[0][2]) +
                           abs(ai.limit_lists(project)["LeftOuterLimit"][0][0] - project.route.points[0][0]), 100)


class ProjectFormat(unittest.TestCase):
    def test_save_load_roundtrip(self):
        project = small_project()
        project.checkpoints.append(Checkpoint(uid="x", center=(1, 2, 3), radius=9, extra_time=11))
        with tempfile.TemporaryDirectory() as tmp:
            save_project(project, Path(tmp) / "p")
            again = load_project(Path(tmp) / "p")
        for a, b in zip(again.meshes, project.meshes):      # positions are stored as float32 (the DX precision)
            self.assertTrue(all(abs(x - y) < 1e-4 * max(1.0, abs(y)) for x, y in zip(a.positions, b.positions)))
        self.assertEqual([m.triangles for m in again.meshes], [m.triangles for m in project.meshes])
        self.assertEqual(again.checkpoints[-1].center, (1.0, 2.0, 3.0))
        self.assertEqual(again.materials.keys(), project.materials.keys())
        self.assertEqual(again.route.points, [list(p) if isinstance(p, list) else p for p in again.route.points])

    def test_validator_flags_inverted_terrain(self):
        project = small_project()
        terrain = project.meshes[0]
        t = terrain.triangles
        for k in range(0, len(t), 3):
            t[k + 1], t[k + 2] = t[k + 2], t[k + 1]
        findings = validate.validate_project(project)
        self.assertTrue(any("point down" in f.message for f in findings if f.severity == "error"))

    def test_obj_import(self):
        project = CourseProject(name="Obj")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.obj"
            path.write_text("v 0 0 0\nv 10 0 0\nv 10 0 10\nv 0 0 10\nvt 0 0\nvt 1 0\nvt 1 1\nvt 0 1\nusemtl Grass\n"
                            "f 1/1 4/4 3/3 2/2\n")
            mesh = import_obj(path, project)
        self.assertEqual(mesh.triangle_count, 2)
        self.assertGreater(dx_build.triangle_normal(*mesh.triangle_points(0))[1], 0)


class Textures(unittest.TestCase):
    def test_feed_crc_and_png_roundtrip(self):
        w, h = 8, 4
        rgba = b"".join(bytes((x * 30 % 256, y * 60 % 256, 7, 255 - x)) for y in range(h) for x in range(w))
        feed = textures.encode_feed(w, h, rgba)
        self.assertTrue(textures.feed_is_valid(feed))
        self.assertEqual(struct.unpack_from("<I", feed, 8)[0], zlib.crc32(feed[20:]) & 0xFFFFFFFF)
        self.assertEqual(textures.decode_feed(feed), (w, h, rgba))
        self.assertEqual(textures.decode_png(textures.encode_png(w, h, rgba)), (w, h, rgba))
        self.assertEqual(textures.target_size(300, 60), (256, 64))


class Registry(unittest.TestCase):
    @unittest.skipUnless(CATALOG.exists(), "accepted COURSE-CAP2 catalog not present")
    def test_register_keeps_originals_and_is_stable(self):
        catalog = json.loads(CATALOG.read_text())
        new, row = register_course(catalog, key="UnitValley", title="Unit", menu_group=0, menu_position=-1,
                                   modes=["QuickRace"])
        self.assertEqual(row["id"], len(catalog["races"]))
        self.assertEqual(new["races"][:39], catalog["races"][:39])
        again, row2 = register_course(new, key="UnitValley", title="Unit 2", menu_group=0, menu_position=-1,
                                      modes=["QuickRace"])
        self.assertEqual(row2["id"], row["id"])
        self.assertEqual(len(again["races"]), len(new["races"]))


if __name__ == "__main__":
    unittest.main()
