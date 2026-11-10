"""Synthetic tests for SFL heading fields, route stitching and new-entry scenes."""
from __future__ import annotations

import importlib.util
import math
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.course_atlas import (  # noqa: E402
    AtlasStage,
    resample_route,
    route_length,
    self_overlap_length,
    stitch_routes,
)
from master_rallye.course_entry import RouteFrame, build_entry_racetest  # noqa: E402
from master_rallye.course_sfl_field import (  # noqa: E402
    SflGrid,
    grid_for_route,
    heading_byte,
    heading_error,
    sample,
    synthesize_heading_field,
)
from master_rallye.sfl import parse_sfl_bytes  # noqa: E402

HAS_NUMPY = importlib.util.find_spec("numpy") is not None


def line(a, b, n):
    return [tuple(a[i] + (b[i] - a[i]) * k / (n - 1) for i in range(3)) for k in range(n)]


class SflFieldTests(unittest.TestCase):
    def test_heading_byte_convention(self):
        self.assertEqual(heading_byte(0.0, 1.0), 0)      # +Z
        self.assertEqual(heading_byte(-1.0, 0.0), 64)    # -X
        self.assertEqual(heading_byte(0.0, -1.0), 128)   # -Z
        self.assertEqual(heading_byte(1.0, 0.0), 192)    # +X
        self.assertEqual(heading_error(250, 4), 10)

    def test_grid_encloses_route(self):
        grid = grid_for_route([(0, 0, 0), (100, 0, 50)], margin=60)
        self.assertEqual(grid.cell_size, 3.0)
        self.assertLessEqual(grid.origin_x, -60)
        self.assertGreaterEqual(grid.max_x, 160)
        self.assertGreaterEqual(grid.max_z, 110)

    @unittest.skipUnless(HAS_NUMPY, "numpy required for synthesis")
    def test_synthesized_field_is_column_major_and_route_aligned(self):
        route = line((0, 0, 0), (300, 0, 0), 16)  # travel +X
        data = synthesize_heading_field(route, grid_for_route(route, margin=90))
        field = parse_sfl_bytes(data)
        cs, w, h, ox, oz = struct.unpack_from("<fIIff", data, 0)
        self.assertEqual(len(data), 20 + w * h)
        self.assertLessEqual(heading_error(sample(field, 150.0, 0.0), heading_byte(1, 0)), 2)
        # Far above the route (+Z) the field points back toward the nearest
        # 20-unit sample (within ~7 degrees of -Z here).
        self.assertLessEqual(heading_error(sample(field, 150.0, 85.0), heading_byte(0, -1)), 6)
        # Column-major: neighbouring payload bytes advance in Z, not X.
        grid = SflGrid(cs, w, h, ox, oz)
        i, j = grid.cell_of(150.0, 85.0)
        self.assertEqual(field.payload[i * h + j], sample(field, 150.0, 85.0))


class RouteStitchTests(unittest.TestCase):
    def test_resample_spacing(self):
        pts = resample_route(line((0, 0, 0), (100, 0, 0), 3), 20.0)
        self.assertEqual(len(pts), 6)
        self.assertAlmostEqual(route_length(pts), 100.0)

    def test_stitch_joins_without_u_turn_or_revisit(self):
        a = line((0, 0, 0), (1000, 0, 0), 51)
        b = line((1000, 0, 0), (1000, 0, 1000), 51)       # continues from a's end
        back = list(reversed(a))                           # would U-turn onto a (90 degree turns are fine)
        route = stitch_routes("t", [AtlasStage("A", Path("a"), None, a), AtlasStage("B", Path("b"), None, b),
                                    AtlasStage("Back", Path("c"), None, back)], first="A", allow_reverse=False)
        self.assertEqual([leg.stage for leg in route.legs], ["A", "B"])
        self.assertAlmostEqual(route.length, 2000.0, delta=1.0)
        self.assertEqual(self_overlap_length(route.samples), 0.0)

    def test_reversed_leg_is_used_when_direction_fits(self):
        a = line((0, 0, 0), (1000, 0, 0), 51)
        b = list(reversed(line((1000, 0, 0), (1000, 0, 1000), 51)))
        route = stitch_routes("t", [AtlasStage("A", Path("a"), None, a), AtlasStage("B", Path("b"), None, b)], first="A")
        self.assertEqual(route.legs[1].stage, "B")
        self.assertTrue(route.legs[1].reversed)


def _scene(raceline, pace_xyz=None, left_sign=1.0):
    def markers(name, pts):
        rows = "".join(
            f'<Marker No="{k}"><Value Name="Marker Type" Type="String" Value="m"/>'
            f'<Value Name="Marker Pos" Type="Vector3" Value="{p[0]:.2f} {p[1]:.2f} {p[2]:.2f}"/>'
            f'<Value Name="Marker Dir" Type="Vector3" Value="1.00 0.00 0.00"/></Marker>'
            for k, p in enumerate(pts))
        return f'<List Name="{name}">{rows}</List>'
    start = [(0, 0, -5), (0, 0, 5), (-10, 0, 5), (-10, 0, -5)]
    end = raceline[-1]
    finish = [(end[0] - 5, 0, -5), (end[0] - 5, 0, 5), (end[0] + 5, 0, 5), (end[0] + 5, 0, -5)]
    pace = ""
    if pace_xyz:
        pace = ('<List Name="RacePaceNotes"><Egg Name="PaceNote7"><Value Name="en3d Matrix" Type="Matrix" '
                'Row0="1 0 0 0" Row1="0 1 0 0" Row2="0 0 1 0" '
                f'Row3="{pace_xyz[0]} {pace_xyz[1]} {pace_xyz[2]} 1"/>'
                '<AI_List><AI No="0"><gaRacePaceNoteAI><Value Name="Pace Note Trigger ID (Unique)" Type="Int" Value="7"/>'
                '</gaRacePaceNoteAI></AI></AI_List></Egg></List>')
    limits = "".join(markers(n, [(p[0], p[1], p[2] + s * left_sign) for p in raceline])
                     for n, s in (("LeftInnerLimit", 6), ("LeftOuterLimit", 9), ("RightInnerLimit", -6), ("RightOuterLimit", -9)))
    return ('<Scene><EggLists_Version4>'
            '<List Name="landscape"><Egg Name="landscape"><Value Name="en3d Model Name" Type="String" Value="course\\old\\old"/></Egg></List>'
            '<List Name="IConManager"><Egg Name="IContManager"><Value Name="AI DataSet Name" Type="String" Value="ICont/old"/></Egg></List>'
            + pace + '</EggLists_Version4><MarkerLists>' + markers("RaceLine", raceline) + markers("StartArea", start)
            + markers("FinishArea", finish) + limits + '</MarkerLists></Scene>').encode()


class EntrySceneTests(unittest.TestCase):
    def test_route_frame_roundtrip(self):
        frame = RouteFrame(line((0, 0, 0), (100, 0, 0), 6))
        along, side, dy, _, _ = frame.local((40.0, 2.0, 3.0))
        p, _ = frame.place(along, side, dy)
        self.assertAlmostEqual(p[0], 40.0, places=5)
        self.assertAlmostEqual(p[1], 2.0, places=5)
        self.assertAlmostEqual(p[2], 3.0, places=5)

    def test_build_entry_rebuilds_route_lists_and_transfers_pace_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "T.xml"
            template.write_bytes(_scene(line((0, 0, 0), (200, 0, 0), 11), pace_xyz=(120, 0, 1)))
            new_route = line((0, 0, 0), (0, 0, 400), 21)  # heads +Z instead of +X
            data, report = build_entry_racetest(template, entry_name="InvTest", model_name="course\\inv\\inv",
                                                route=new_route, source_xmls=[template])
            root = ET.fromstring(data)
            lists = {lst.get("Name"): lst for lst in root.iter("List")}
            self.assertEqual(len(lists["RaceLine"].findall("Marker")), report["raceline_markers"])
            self.assertEqual(root.find(".//Value[@Name='AI DataSet Name']").get("Value"), "ICont/invtest")
            self.assertEqual(root.find(".//Value[@Name='en3d Model Name']").get("Value"), "course\\inv\\inv")
            finish = [tuple(map(float, m.find("Value[@Name='Marker Pos']").get("Value").split()))
                      for m in lists["FinishArea"].findall("Marker")]
            centre = [sum(c) / 4 for c in zip(*finish)]
            self.assertAlmostEqual(centre[2], 400.0, delta=1.0)  # re-anchored to the new end
            # The template pace note sits on the old +X road, not on the new route.
            self.assertEqual(report["RacePaceNotes_transferred"], 0)

    def test_pace_note_on_shared_road_is_renumbered(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "T.xml"
            template.write_bytes(_scene(line((0, 0, 0), (200, 0, 0), 11), pace_xyz=(120, 0, 1)))
            data, report = build_entry_racetest(template, entry_name="InvTest", model_name="m",
                                                route=line((0, 0, 0), (300, 0, 0), 16), source_xmls=[template])
            root = ET.fromstring(data)
            notes = [e for lst in root.iter("List") if lst.get("Name") == "RacePaceNotes" for e in lst.findall("Egg")]
            self.assertEqual(report["RacePaceNotes_transferred"], 1)
            self.assertEqual(notes[0].get("Name"), "PaceNote1")
            self.assertEqual(notes[0].find(".//Value[@Name='Pace Note Trigger ID (Unique)']").get("Value"), "1")


class LimitTransferTests(unittest.TestCase):
    def test_limits_follow_the_stage_side_and_mirror_when_reversed(self):
        from master_rallye.course_entry import RouteFrame, transfer_limits

        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "S.xml"
            # Retail convention: Left limits lie on the negative RouteFrame side.
            stage.write_bytes(_scene(line((0, 0, 0), (400, 0, 0), 21), left_sign=-1.0))
            route = line((0, 0, 0), (400, 0, 0), 21)
            limits, stats = transfer_limits(route, [(stage, False)], min_side=5.0)
            frame = RouteFrame(route)
            self.assertGreater(stats["LeftInnerLimit"]["transferred"], 10)
            self.assertTrue(all(frame.local(p)[1] <= -5.0 for p in limits["LeftInnerLimit"]))
            self.assertTrue(all(frame.local(p)[1] >= 5.0 for p in limits["RightInnerLimit"]))
            backwards = list(reversed(route))
            limits_r, stats_r = transfer_limits(backwards, [(stage, False)], min_side=5.0)
            frame_r = RouteFrame(backwards)
            # Driving the stage backwards swaps its Left/Right lists, whatever the leg flag says.
            self.assertGreater(stats_r["LeftInnerLimit"]["transferred"], 10)
            self.assertTrue(all(frame_r.local(p)[1] <= -5.0 for p in limits_r["LeftInnerLimit"]))

    def test_markers_on_the_road_are_dropped(self):
        from master_rallye.course_entry import transfer_limits

        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "S.xml"
            stage.write_bytes(_scene(line((0, 0, 0), (400, 0, 0), 21), left_sign=-1.0))
            route = line((0, 0, 0), (400, 0, 0), 21)
            _, stats = transfer_limits(route, [(stage, False)], min_side=7.0)
            # Inner limits sit 6 units from the road: closer than min_side, all dropped.
            self.assertEqual(stats["LeftInnerLimit"]["transferred"], 0)
            self.assertGreater(stats["LeftOuterLimit"]["transferred"], 10)


class InvitationPatchToolTests(unittest.TestCase):
    def test_refuses_non_retail_input(self):
        spec = importlib.util.spec_from_file_location("patch_inv", ROOT / "tools/patch_invitation_entries.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(module.PatchError):
            module.build_patch(b"MZ" + bytes(64), ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()


class LimitEmulatorTests(unittest.TestCase):
    def test_retail_like_corridor_is_inside_and_zigzag_is_outside(self):
        from master_rallye.course_limits_emulator import limit_state

        route = line((0, 0, 0), (400, 0, 0), 21)
        # Retail convention: Left lists on the negative RouteFrame side (-Z here).
        lists = {"LeftInnerLimit": [(x, 0, -20) for x, _, _ in route], "LeftOuterLimit": [(x, 0, -40) for x, _, _ in route],
                 "RightInnerLimit": [(x, 0, 20) for x, _, _ in route], "RightOuterLimit": [(x, 0, 40) for x, _, _ in route]}
        self.assertEqual(limit_state(lists, (200.0, 1.0, 0.0)), 0)
        self.assertEqual(limit_state(lists, (200.0, 1.0, -30.0)), 1)
        self.assertEqual(limit_state(lists, (200.0, 1.0, -50.0)), 2)
        # A left list that runs backwards (another route portion) puts a centred car outside.
        backwards = dict(lists, LeftInnerLimit=list(reversed(lists["LeftInnerLimit"])),
                         LeftOuterLimit=list(reversed(lists["LeftOuterLimit"])))
        self.assertEqual(limit_state(backwards, (200.0, 1.0, 0.0)), 2)


class GxmWriterTests(unittest.TestCase):
    def test_builder_output_parses_with_the_v7_reader(self):
        from master_rallye.course_gxm import parse_course_gxm_model_v7_bytes
        from master_rallye.course_gxm_writer import (GxmBuilder, GxmCorner, GxmGroup, GxmMaterial, GxmTextureSlot,
                                                     decode_materials, encode_materials)
        from master_rallye.course_source import parse_course_txt_bytes

        builder = GxmBuilder()
        corner = lambda x, z: GxmCorner((x, -z, 0.0), (0.0, 0.0, 1.0), (x / 10, z / 10, 0.5), (1.0, 1.0, 1.0, 1.0))  # noqa: E731
        ground = builder.mesh("$landdb", [(0, [corner(0, 0), corner(10, 0), corner(10, 10)]),
                                          (0, [corner(0, 0), corner(10, 10), corner(0, 10)])])
        props = builder.mesh("props", [(1, [corner(1, 1), corner(2, 1), corner(2, 2)])])
        materials = [GxmMaterial("$surfacetype(grass) $shader(ground)",
                                 [GxmTextureSlot("C:/x/grass-tga.gxi"), GxmTextureSlot(), GxmTextureSlot("C:/x/noise-tga.gxi")]),
                     GxmMaterial("props $shader(object)", [GxmTextureSlot("C:/x/p-tga.gxi", True, True)])]
        tree = [GxmGroup("$autovsphere_300", [GxmGroup("$bsp", [GxmGroup("$draw", [ground])]), GxmGroup("$objects", [props])])]
        data, txt = builder.encode(materials, "Model", tree)
        model = parse_course_gxm_model_v7_bytes(data, parse_course_txt_bytes(txt.encode("latin-1"), "t.txt"), "t.gxm")
        self.assertTrue(model.validation.passed)
        self.assertTrue(model.validation.mesh_spans_cover_bank)
        self.assertEqual(model.counts, (0, 1, 2, 1, 7, 3, 7))
        decoded = decode_materials(model.materials.raw, model.materials.count)
        self.assertEqual(encode_materials(decoded), model.materials.raw)
        self.assertTrue(decoded[1].slots[0].has_alpha)

    def test_dxt_to_gxi_reverses_rows_and_swaps_channels(self):
        import importlib.util
        import struct
        import zlib

        spec = importlib.util.spec_from_file_location("bcs", ROOT / "tools/build_course_source.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        payload = bytes([1, 2, 3, 4, 5, 6, 7, 8])  # 1x2 BGRA, bottom row first
        dxt = struct.pack("<5I", 0xFEED, 1, zlib.crc32(payload), 1, 2) + payload
        gxi = module.dxt_to_gxi(dxt)
        self.assertEqual(gxi[:8], struct.pack("<IHH", 0x13039, 1, 2))
        self.assertEqual(gxi[8:], bytes([7, 6, 5, 8, 3, 2, 1, 4]))


class CourseSourceCollisionTests(unittest.TestCase):
    @staticmethod
    def _module():
        import importlib.util
        spec = importlib.util.spec_from_file_location("bcs", ROOT / "tools/build_course_source.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_later_stage_overlap_is_dropped_but_own_triangles_kept(self):
        bcs = self._module()
        a = ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 10.0))
        b_overlap = ((1.0, 0.0, 1.0), (9.0, 0.0, 1.0), (1.0, 0.0, 9.0))
        b_free = ((20.0, 0.0, 0.0), (30.0, 0.0, 0.0), (20.0, 0.0, 10.0))
        bridge = ((1.0, 10.0, 1.0), (9.0, 10.0, 1.0), (1.0, 10.0, 9.0))
        other_layer = ((1.0, 25.0, 1.0), (9.0, 25.0, 1.0), (1.0, 25.0, 9.0))
        # Bridges/overhangs inside one stage stay; another stage's terrain version
        # over accepted land is dropped at any height (no stacked stage layers).
        surface, dropped = bcs.merge_land_surfaces([("A", [(a, "g"), (bridge, "g")]),
                                                    ("B", [(a, "g"), (b_overlap, "g"), (b_free, "g"),
                                                           (other_layer, "g")])])
        self.assertEqual(set(surface), {frozenset(a), frozenset(b_free), frozenset(bridge)})
        self.assertEqual(dropped, {frozenset(b_overlap), frozenset(other_layer)})

    def test_box_proxy_is_closed_with_outward_normals(self):
        bcs = self._module()
        faces = bcs.box_triangles((5.0, -3.0, 0.4, 2.0, 1.0, 0.0, 3.0))
        self.assertEqual(len(faces), 12)
        edges = {}
        for tri in faces:
            for i in range(3):
                edge = (tri[i], tri[(i + 1) % 3])
                edges[edge] = edges.get(edge, 0) + 1
        self.assertTrue(all((b, a) in edges for a, b in edges))  # every edge shared in opposite direction
        centre = (5.0, 3.0, 1.5)  # source space (x, -z, y)
        for tri in faces:
            n = bcs._face_normal(tri)
            c = [sum(p[k] for p in tri) / 3 - centre[k] for k in range(3)]
            self.assertGreater(sum(n[k] * c[k] for k in range(3)), 0)

    def test_boxes_skip_objects_over_the_road(self):
        bcs = self._module()
        route = [(float(x), 0.0, 0.0) for x in range(0, 100, 2)]
        cube = lambda x, z: [((x, 0.0, z), (x + 1, 0.0, z), (x, 2.0, z + 1)), ((x + 1, 2.0, z + 1), (x + 1, 0.0, z), (x, 2.0, z + 1))]  # noqa: E731
        boxes, skipped = bcs.collision_boxes(cube(50.0, 0.5) + cube(50.0, 20.0), route)
        self.assertEqual(len(boxes), 1)
        self.assertEqual(skipped, {"over_road": 1})


class ClearRouteEndTests(unittest.TestCase):
    def test_finish_moved_away_from_an_earlier_pass(self):
        from master_rallye.course_atlas import clear_route_end
        out = [(float(x), 0.0, 0.0) for x in range(0, 2000, 20)]
        back = [(2000.0 - x, 0.0, 300.0) for x in range(0, 1200, 20)]
        hook = [(800.0, 0.0, 300.0 - z) for z in range(20, 280, 20)]  # ends 20 units from the first leg
        route = out + back + hook
        trimmed = clear_route_end(route)
        self.assertLess(len(trimmed), len(route))
        end = trimmed[-1]
        self.assertGreaterEqual(min(abs(end[2] - p[2]) for p in out), 200.0)


class ClearRoadTests(unittest.TestCase):
    def test_object_on_road_goes_with_its_touching_parts_but_banner_overhead_stays(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bcs", ROOT / "tools/build_course_source.py")
        bcs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bcs)
        route = [(float(x), 0.0, 0.0) for x in range(0, 100, 2)]
        ground = lambda x, z, below: 0.0  # noqa: E731
        truck = [((49.0, 0.5, -1.0), (51.0, 0.5, -1.0), (50.0, 2.0, 1.0))]          # on the road
        wheel = [((52.0, 0.0, 5.0), (52.6, 0.0, 5.0), (52.3, 0.6, 5.4)),            # touches the truck box
                 ((51.4, 0.0, 0.9), (52.0, 0.0, 5.0), (52.3, 0.6, 5.4))]
        banner = [((20.0, 4.0, -3.0), (20.0, 4.0, 3.0), (20.0, 5.0, 0.0))]           # overhead
        post = [((70.0, 0.0, 8.0), (70.3, 0.0, 8.0), (70.1, 2.0, 8.2))]               # roadside
        dropped = bcs.clear_road(truck + wheel + banner + post, route, ground)
        self.assertEqual(dropped, {0, 1, 2})

    def test_route_owner_follows_legs(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bcs", ROOT / "tools/build_course_source.py")
        bcs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bcs)
        a = [(float(x), 0.0, 0.0) for x in range(0, 210, 10)]
        b = [(200.0, 0.0, float(z)) for z in range(0, 210, 10)]
        route = a + b[1:]
        owner, owners = bcs.route_owner(route, ["A", "B"], {"A": a, "B": b})
        self.assertEqual(owners[0], "A")
        self.assertEqual(owners[-1], "B")
        self.assertEqual(owner(50.0, 20.0), "A")
        self.assertEqual(owner(220.0, 150.0), "B")


class SnapRouteEndTests(unittest.TestCase):
    def test_route_ends_at_a_gantry_it_passes_near_the_end(self):
        from master_rallye.course_atlas import snap_route_end
        route = [(float(x), 0.0, 0.0) for x in range(0, 2000, 20)]
        snapped = snap_route_end(route, [(1800.0, 5.0), (500.0, 0.0), (1990.0, 300.0)])
        self.assertEqual(snapped[-1], (1800.0, 0.0, 0.0))
        self.assertEqual(snap_route_end(route, [(1000.0, 0.0)]), route)  # too far back


class CourseBspTests(unittest.TestCase):
    def test_tag100_roundtrip_and_closed_box_classification(self):
        from master_rallye.course_bsp import build_solid_bsp, classify, encode_tag100, polygon, tree_from_parsed
        from master_rallye.course_tag100 import parse_course_tag100_bytes
        import importlib.util
        spec = importlib.util.spec_from_file_location("bcs", ROOT / "tools/build_course_source.py")
        bcs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bcs)
        polys = []
        for i, tri in enumerate(bcs.box_triangles((0.0, 0.0, 0.3, 2.0, 1.0, 0.0, 3.0))):
            dx = [(p[0], p[2], -p[1]) for p in tri]  # source -> DX
            n = bcs._face_normal(tri)
            polys.append(polygon(dx, (n[0], n[2], -n[1]), i))
        tree = build_solid_bsp(polys)
        self.assertTrue(classify(tree, (0.0, 1.5, 0.0)))
        self.assertFalse(classify(tree, (0.0, 5.0, 0.0)))
        self.assertFalse(classify(tree, (5.0, 1.5, 0.0)))
        data = encode_tag100(tree)
        parsed = parse_course_tag100_bytes(data, "t")
        self.assertTrue(all(parsed.count_invariants().values()))
        self.assertEqual(encode_tag100(tree_from_parsed(parsed)), data)

    def test_close_land_skirts_map_edge_and_fills_small_hole(self):
        from master_rallye.course_bsp import close_land
        grid = {}
        for i in range(6):
            for j in range(6):
                grid[(i, j)] = (i * 10.0, 0.0, j * 10.0)
        tris = []
        for i in range(5):
            for j in range(5):
                if (i, j) == (2, 2):
                    continue  # a small hole in the middle
                a, b, c, d = grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]
                tris += [[a, d, c], [a, c, b]]  # right-hand normal up in DX (x, y-up, z)
        out, stats = close_land(tris, fill_extent=30.0)
        self.assertEqual(stats["filled_loops"], 1)
        self.assertEqual(stats["fill_triangles"], 4)
        self.assertEqual(stats["skirt_walls"], 20)
        fans = [n for pts, n, _ in out if len(pts) == 3]
        self.assertTrue(all(n[1] > 0 for n in fans))


RETAIL_EXE = ROOT.parent / "MRallye.exe"


@unittest.skipUnless(RETAIL_EXE.is_file(), "pristine Retail MRallye.exe not available")
class InvitationDifficultyPatchTests(unittest.TestCase):
    def test_fixed_invitation_level_replaces_the_random_hard_medium_pick(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("pie", ROOT / "tools/patch_invitation_entries.py")
        pie = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pie)
        data = RETAIL_EXE.read_bytes()
        if __import__("hashlib").sha256(data).hexdigest() != pie.RETAIL_SHA256:
            self.skipTest("game root executable is not the pristine Retail build")
        out, manifest = pie.build_patch(data, ["InvA", "InvB", "InvC"], invitation_difficulty=4)
        at = pie._va_to_offset(0x45BFB6)
        self.assertEqual(bytes(out[at:at + 13]), bytes.fromhex("be04000000") + b"\x90" * 8)
        with self.assertRaises(pie.PatchError):
            pie.build_patch(data, ["InvA", "InvB", "InvC"], invitation_difficulty=5)
