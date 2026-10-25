"""Synthetic tests for the V-MESH4.1 LOD0 path: content-driven roles, overlay support, native arches, source identity."""
import tempfile
import unittest
from pathlib import Path

from tools import vmesh_diagnose as diag
from tools import vmesh_geometry as geo
from tools import vmesh_lod0 as l0
from tests.synthetic.test_vmesh_geometry import AXLES, DONOR_DIR, HAVE_DONOR, _png

# GT frame: front = -Z, body z -2.0 .. 2.0 (length 4), hub height 0.29.  Faces carry vt/vn so source UVs can be checked.
VERTS = [
    (-0.8, 0.30, -2.0), (0.8, 0.30, -2.0), (0.8, 0.80, -2.0), (-0.8, 0.80, -2.0),       # 1-4 front wall
    (-0.8, 0.30, 2.0), (0.8, 0.30, 2.0), (0.8, 0.80, 2.0),                               # 5-7 rear
    (-0.5, 0.62, -0.2), (0.5, 0.62, -0.2), (0.0, 0.62, 0.6),                             # 8-10 cabin shell
    (-0.6, 1.0, 0.2), (0.6, 1.0, 0.2), (0.0, 1.1, -0.8),                                 # 11-13 pane
    (-0.7, 0.40, -1.9), (-0.5, 0.40, -1.9), (-0.6, 0.55, -1.9),                          # 14-16 left lamp (front corner)
    (0.7, 0.40, -1.9), (0.5, 0.40, -1.9), (0.6, 0.55, -1.9),                             # 17-19 right lamp
]


def face(a, b, c, n=1):
    return "f %d/1/%d %d/2/%d %d/3/%d" % (a, n, b, n, c, n)


def obj_text():
    lines = ["v %s %s %s" % p for p in VERTS]
    lines += ["vt 0.1 0.2", "vt 0.9 0.2", "vt 0.5 0.9", "vn 0 0 -1", "vn 0 1 0"]
    lines += ["o body", "usemtl Mat1_Tex0", face(1, 2, 3), face(1, 3, 4), face(5, 6, 7, 2),
              "o decal", "usemtl Mat1_Tex9", face(1, 2, 3),                       # on top of body: supported overlay
              "o lone", "usemtl Mat1_Tex9", face(8, 9, 10, 2),                    # nothing under it: kept
              "o trim", "usemtl Mat6_Tex3", face(1, 2, 5),
              "o cabin", "usemtl Mat-1_Tex39", face(8, 9, 10, 2),
              "o hollow", "usemtl Mat-1_Tex-1", "f 8//2 9//2 10//2",
              "o env_reflection", "usemtl Mat-1_Tex510", "f 1//1 2//1 3//1",
              "o pane", "usemtl Mat6_Tex37", face(11, 12, 13, 2),
              "o lampL", "usemtl Mat6_Tex23", face(14, 15, 16), "usemtl Mat6_Tex3", face(14, 15, 16),
              "o lampR", "usemtl Mat6_Tex23", face(17, 18, 19), "usemtl Mat6_Tex3", face(17, 18, 19),
              "o shape17_tail_lamp_off", "usemtl Mat6_Tex25", face(5, 6, 7, 2)]
    return "\n".join(lines) + "\n"


MTL = "".join("newmtl %s\nmap_Kd %s\n" % mf for mf in (
    ("Mat1_Tex0", "paint.png"), ("Mat1_Tex9", "overlay.png"), ("Mat6_Tex3", "trim.png"), ("Mat-1_Tex39", "trim.png"),
    ("Mat6_Tex37", "pane.png"), ("Mat6_Tex23", "lens.png"), ("Mat6_Tex25", "trim.png")))


def write_assets(tmp: Path) -> Path:
    (tmp / "paint.png").write_bytes(_png(8, 8, lambda x, y: (20, 30, 200, 255)))
    (tmp / "overlay.png").write_bytes(_png(8, 8, lambda x, y: (0, 0, 0, 0 if x < 7 else 255)))      # 87 % transparent
    (tmp / "trim.png").write_bytes(_png(4, 4, lambda x, y: (5, 5, 5, 255)))
    (tmp / "pane.png").write_bytes(_png(8, 8, lambda x, y: (8, 16, 16, 230)))
    (tmp / "lens.png").write_bytes(_png(8, 8, lambda x, y: (40, 40, 40, 0 if x < 3 else 255)))      # 37 % cut-out
    obj = tmp / "lod0.obj"
    obj.write_text(obj_text())
    obj.with_suffix(".mtl").write_text(MTL)
    return obj


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.obj = write_assets(Path(cls.tmp.name))
        gt = geo.parse_gt_full(cls.obj)
        cls.faces, cls.textures = gt["faces"], gt["textures"]
        cls.cl = l0.Lod0Classifier(cls.faces, cls.textures)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def role(self, obj, material):
        return self.cl._decide(obj, material)[0]

    def test_structural_object_names(self):
        self.assertEqual(self.role("env_reflection", "Mat-1_Tex510"), "exclude")
        self.assertEqual(self.role("shape19_tail_lamp_on", "Mat6_Tex25"), "exclude")
        self.assertEqual(self.role("shape17_tail_lamp_off", "Mat6_Tex25"), "tail_lamp")

    def test_mat_minus_one_is_interior_only_when_textured(self):
        self.assertEqual(self.role("cabin", "Mat-1_Tex39"), "interior")
        self.assertEqual(self.role("hollow", "Mat-1_Tex-1"), "exclude")

    def test_translucent_dark_pane_is_glass_regardless_of_texture_index(self):
        self.assertEqual(list(self.cl.glazing), ["Mat6_Tex37"])
        self.assertEqual(self.role("pane", "Mat6_Tex37"), "glass")
        self.assertEqual(self.role("trim", "Mat6_Tex3"), "black")

    def test_head_lamp_is_the_cutout_lens_of_front_corner_objects(self):
        self.assertEqual(self.cl.lamp_objects, {"lampL", "lampR"})
        self.assertEqual(self.role("lampL", "Mat6_Tex23"), "head_lamp")
        self.assertEqual(self.role("lampR", "Mat6_Tex23"), "head_lamp")
        self.assertEqual(self.role("lampL", "Mat6_Tex3"), "black")        # opaque trim inside the lamp object

    def test_paint_default(self):
        self.assertEqual(self.role("body", "Mat1_Tex0"), "paint")

    def test_overlay_support_keeps_lone_surfaces_and_drops_decals(self):
        keep = l0.make_overlay_keep(self.faces, self.cl)
        decal = next(t for o, m, t in self.faces if o == "decal")
        lone = next(t for o, m, t in self.faces if o == "lone")
        self.assertFalse(keep(decal))
        self.assertTrue(keep(lone))

    def test_description_and_material_table_identify_sources(self):
        rows = self.cl.describe(self.faces)
        self.assertTrue(all("reason" in r and "role" in r for r in rows))
        table = {r["material"]: r for r in l0.source_materials_table(self.faces, self.textures, self.cl)}
        self.assertEqual(table["Mat6_Tex37"]["roles"], {"glass": 1})
        self.assertEqual(table["Mat1_Tex9"]["alpha_policy"], "drop")
        self.assertEqual(len(table["Mat1_Tex0"]["texture_sha256"]), 64)


@unittest.skipUnless(HAVE_DONOR, "unpacked retail Navara donor not available")
class NativePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from master_rallye.dx import parse_dx_bytes
        cls.parse = staticmethod(parse_dx_bytes)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.obj = write_assets(Path(cls.tmp.name))
        cls.donor = {n: (DONOR_DIR / n).read_bytes() for n in ("car.dx", "complete.dx", "wheel.dx")}
        cls.ctx = geo.make_context(cls.donor["car.dx"], cls.donor["complete.dx"], cls.donor["wheel.dx"])
        cls.plan = geo.plan_fit(cls.ctx, AXLES, 0.29, lift=0.12)
        cls.gt = geo.parse_gt_full(cls.obj)
        cls.cl = l0.Lod0Classifier(cls.gt["faces"], cls.gt["textures"])
        cls.keep = staticmethod(l0.make_overlay_keep(cls.gt["faces"], cls.cl))
        cls.opt = geo.BuildOptions(arch="native")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def build(self, profile="complete"):
        smap = []
        name = "car.dx" if profile == "car" else "complete.dx"
        data, rep = geo.build_candidate(self.obj, self.donor[name], self.ctx, self.plan, profile, self.opt,
                                        classifier=self.cl, overlay_keep=self.keep, source_map=smap)
        return data, rep, smap

    def test_roles_reach_their_donor_draws_and_decals_are_dropped(self):
        _, rep, smap = self.build()
        self.assertEqual(rep["gt_face_roles"]["glass"], 1)
        self.assertEqual(rep["gt_face_roles"]["head_lamp"], 2)
        self.assertEqual(rep["alpha_cutouts"]["tris_dropped_overlay_or_invisible"], 1)
        self.assertEqual(rep["alpha_cutouts"]["overlay_tris_kept_unsupported_surface"], 1)
        self.assertEqual(rep["arch"]["mode"], "native")
        self.assertNotIn("tube_tris", rep["arch"])
        self.assertEqual(rep["replaced_draw_stats"]["24"]["triangles"], 1)            # complete.dx glass draw

    def test_native_mode_never_moves_source_vertices(self):
        data, rep, smap = self.build()
        self.assertEqual(rep["relief"]["gt_vertices_moved"], 0)
        tp, _ = self.plan.transform(self.ctx, "complete")
        verdict = l0.verify_source_map(data, smap, self.gt["faces"], tp)
        self.assertEqual(verdict["mismatches"], 0)
        self.assertGreater(verdict["verified_exact"], 5)

    def test_source_map_keeps_object_material_and_uvs(self):
        _, _, smap = self.build()
        body = [e for e in smap if e["obj"] == "body"]
        self.assertEqual(len(body), 3)
        first = body[0]
        self.assertEqual(first["material"], "Mat1_Tex0")
        self.assertEqual([c["uv"] for c in first["corners"]], [[0.1, 0.2], [0.9, 0.2], [0.5, 0.9]])
        self.assertTrue(all(c["uv"] is not None for e in smap for c in e["corners"]))

    def test_dropped_decals_are_recorded_with_their_uvs(self):
        dropped = []
        geo.build_candidate(self.obj, self.donor["complete.dx"], self.ctx, self.plan, "complete", self.opt,
                            classifier=self.cl, overlay_keep=self.keep, dropped_map=dropped)
        self.assertEqual([d["material"] for d in dropped], ["Mat1_Tex9"])
        self.assertEqual(dropped[0]["corners"][0]["uv"], [0.1, 0.2])

    def test_race_and_frontend_bodies_stay_a_pure_frame_shift(self):
        car, _, _ = self.build("car")
        comp, _, _ = self.build("complete")
        mc, mm = self.parse(car), self.parse(comp)
        self.assertTrue(mc.diagnostics.validated and mm.diagnostics.validated)
        for a, b in zip(diag.BODY_DRAWS["car"], diag.BODY_DRAWS["complete"]):
            for p, q in zip(diag.draw_points(mc, a), diag.draw_points(mm, b)):
                self.assertAlmostEqual(q[1] - p[1], self.ctx.frame_dy, places=4)

    def test_v4_defaults_are_unchanged_by_the_lod0_hooks(self):
        from tests.synthetic.test_vmesh_geometry import SYNTHETIC_OBJ
        plain = Path(self.tmp.name) / "plain.obj"
        plain.write_text(SYNTHETIC_OBJ)
        data, rep = geo.build_candidate(plain, self.donor["complete.dx"], self.ctx, self.plan, "complete")
        self.assertEqual(rep["arch"]["mode"], "cut")
        self.assertIn("tube_tris", rep["arch"])


if __name__ == "__main__":
    unittest.main()
