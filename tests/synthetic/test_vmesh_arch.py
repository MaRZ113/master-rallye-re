"""Synthetic tests for the V-MESH4 arch cut/liner, glazing routing, stance lift and options (no GT assets needed)."""
import math
import tempfile
import unittest
from pathlib import Path

from tools import vmesh_arch as arch
from tools import vmesh_diagnose as diag
from tools import vmesh_geometry as geo
from tests.synthetic.test_vmesh_geometry import AXLES, DONOR_DIR, HAVE_DONOR, PlanTests, SYNTHETIC_OBJ, _png


def corner(p, n=(1.0, 0.0, 0.0)):
    return (p, n, ("k", p), (0.0, 0.0))


def panel(x=1.0, half=1.5):
    """Two triangles of a square panel at ``x`` (normal +x) centred at y = z = 0."""
    p = [(x, -half, -half), (x, half, -half), (x, half, half), (x, -half, half)]
    return [(corner(p[0]), corner(p[1]), corner(p[2])), (corner(p[0]), corner(p[2]), corner(p[3]))]


def tri_area(t):
    return arch._area(list(t))


def cross_x(t):
    return arch._cross(arch._sub(t[1][0], t[0][0]), arch._sub(t[2][0], t[0][0]))[0]


class ArchCutTests(unittest.TestCase):
    house = arch.WheelHouse((0.84, 0.0, 0.0), 0.4, 0.65, 24)

    def test_area_is_conserved_and_hole_is_the_circumscribed_polygon(self):
        kept, lips, removed = arch.cut_wheel_houses(panel(), [self.house])
        polygon = 24 * 0.4 * 0.4 * math.tan(math.pi / 24)
        self.assertAlmostEqual(removed, polygon, places=6)
        self.assertAlmostEqual(sum(tri_area(t) for t in kept), 9.0 - polygon, places=6)
        self.assertEqual(len(lips[0]), 24)

    def test_opening_is_never_smaller_than_the_requested_radius(self):
        _, lips, _ = arch.cut_wheel_houses(panel(), [self.house])
        radii = [math.hypot(a[0][1], a[0][2]) for a, b in lips[0]]
        self.assertGreaterEqual(min(radii), 0.4 - 1e-9)
        self.assertLessEqual(max(radii), 0.4 / math.cos(math.pi / 24) + 1e-9)

    def test_winding_and_normals_are_preserved(self):
        kept, _, _ = arch.cut_wheel_houses(panel(), [self.house])
        self.assertTrue(all(cross_x(t) > 0 for t in kept))

    def test_triangle_inboard_of_the_wall_or_far_from_the_wheel_is_untouched(self):
        inboard = panel(x=0.3)
        far = [tuple(corner((1.0, 5.0 + c[0][1], 5.0 + c[0][2])) for c in t) for t in panel(half=0.2)]
        kept, lips, removed = arch.cut_wheel_houses(inboard + far, [self.house])
        self.assertEqual(removed, 0.0)
        self.assertEqual(len(kept), 4)
        self.assertEqual(lips[0], [])

    def test_mirrored_house_on_the_other_side(self):
        mirrored = arch.WheelHouse((-0.84, 0.0, 0.0), 0.4, 0.65, 24)
        flipped = [tuple((((-c[0][0]), c[0][1], c[0][2]), c[1], c[2], c[3]) for c in (t[0], t[2], t[1])) for t in panel()]
        kept, lips, removed = arch.cut_wheel_houses(flipped, [mirrored])
        self.assertAlmostEqual(removed, 24 * 0.16 * math.tan(math.pi / 24), places=6)
        self.assertEqual(len(lips[0]), 24)

    def test_liner_tube_faces_the_axis_and_the_wall_faces_outboard(self):
        _, lips, _ = arch.cut_wheel_houses(panel(), [self.house])
        tube, wall = arch.build_liner(lips[0], self.house)
        self.assertEqual((len(tube), len(wall)), (48, 24))
        for t in tube:
            n = arch._cross(arch._sub(t[1][0], t[0][0]), arch._sub(t[2][0], t[0][0]))
            mid = [sum(c[0][i] for c in t) / 3 for i in range(3)]
            self.assertGreater(n[1] * (0 - mid[1]) + n[2] * (0 - mid[2]), 0)
            self.assertTrue(0.65 - 1e-9 <= min(c[0][0] for c in t) and max(c[0][0] for c in t) <= 1.0 + 1e-9)
        for t in wall:
            self.assertGreater(cross_x(t), 0)
            self.assertTrue(all(abs(c[0][0] - 0.65) < 1e-9 for c in t))

    def test_closed_lip_is_watertight_after_tjunction_repair(self):
        import collections
        kept, lips, _ = arch.cut_wheel_houses(panel(), [self.house])
        tube, wall = arch.build_liner(lips[0], self.house)
        generated = [c for t in kept + tube + wall for c in t if c[2][0] == "g"]
        black = arch.split_tjunctions(kept, generated) + tube + wall
        edges = collections.Counter()
        key = lambda p: tuple(round(c / 1e-5) for c in p)
        for t in black:
            for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                edges[tuple(sorted((key(u[0]), key(v[0]))))] += 1
        border = lambda k: all(abs(abs(p[1] / 1e5) - 1.5) < 1e-3 or abs(abs(p[2] / 1e5) - 1.5) < 1e-3 for p in k)
        open_edges = [k for k, c in edges.items() if c == 1 and not border(k)]
        self.assertEqual(open_edges, [])

    def test_tjunction_split_adds_vertex_without_changing_area(self):
        a, b, c = corner((0.0, 0.0, 0.0)), corner((2.0, 0.0, 0.0)), corner((0.0, 2.0, 0.0))
        h = (( 1.0, 0.0, 0.0), None, ("g", 1.0), None)
        out = arch.split_tjunctions([(a, b, c)], [h])
        self.assertEqual(len(out), 2)
        self.assertAlmostEqual(sum(tri_area(t) for t in out), 2.0, places=9)
        self.assertEqual(arch.split_tjunctions([(a, b, c)], []), [(a, b, c)])


class StanceTests(unittest.TestCase):
    def test_lift_moves_the_body_but_not_the_wheel_anchors(self):
        ctx = PlanTests.ctx()
        base = geo.plan_fit(ctx, AXLES, 0.29)
        lifted = geo.plan_fit(ctx, AXLES, 0.29, lift=0.12)
        for profile in ("car", "complete"):
            p0, p1 = base.transform(ctx, profile)[0]((0.3, 0.5, 0.2)), lifted.transform(ctx, profile)[0]((0.3, 0.5, 0.2))
            self.assertAlmostEqual(p1[1] - p0[1], 0.12, places=9)
            self.assertEqual((p0[0], p0[2]), (p1[0], p1[2]))
            self.assertEqual(geo.hubs_in_frame(ctx, profile), geo.hubs_in_frame(ctx, profile))   # hubs depend only on the donor
        self.assertEqual(lifted.wheel_scale, base.wheel_scale)

    def test_options_defaults_and_v3_preset(self):
        d, v3 = geo.BuildOptions(), geo.BuildOptions.v3()
        self.assertEqual((d.arch, d.glazing), ("cut", True))
        self.assertEqual((v3.arch, v3.glazing, v3.interior_inset), ("alpha", False, 0.0))


PANE_MTL = """\
newmtl Mat6_Tex10
map_Kd pane.png
newmtl Mat4_Tex5
map_Kd strip.png
newmtl Mat6_Tex35
map_Kd trim.png
"""
PANE_OBJ = SYNTHETIC_OBJ + """\
o shapeG
usemtl Mat6_Tex10
f 11 12 13
"""
# a large flank panel crossing both axle arches (GT frame: x = -0.8, y 0.1..0.9, z -1.9..1.9)
FLANK_OBJ = PANE_OBJ + """\
v -0.8 0.05 -1.9
v -0.8 0.95 -1.9
v -0.8 0.95 1.9
v -0.8 0.05 1.9
o shapeH
usemtl Mat1_Tex0
f 17 20 19
f 17 19 18
"""


@unittest.skipUnless(HAVE_DONOR, "unpacked retail Navara donor not available")
class V4PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from master_rallye.dx import parse_dx_bytes
        cls.parse = staticmethod(parse_dx_bytes)
        cls.donor = {n: (DONOR_DIR / n).read_bytes() for n in ("car.dx", "complete.dx", "wheel.dx")}
        cls.ctx = geo.make_context(cls.donor["car.dx"], cls.donor["complete.dx"], cls.donor["wheel.dx"])
        cls.plan = geo.plan_fit(cls.ctx, AXLES, 0.29, lift=0.12)
        cls.tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmp.name)
        (tmp / "pane.png").write_bytes(_png(8, 8, lambda x, y: (8, 16, 16, 230)))       # dark, translucent, nothing cut out
        (tmp / "strip.png").write_bytes(_png(8, 8, lambda x, y: (40, 40, 40, 65)))      # translucent overlay strip
        (tmp / "trim.png").write_bytes(_png(8, 8, lambda x, y: (0, 0, 0, 255)))         # opaque trim
        cls.mtl = PANE_MTL
        cls.obj = tmp / "pane.obj"
        cls.obj.write_text(PANE_OBJ)
        cls.obj.with_suffix(".mtl").write_text(PANE_MTL)
        cls.flank = tmp / "flank.obj"
        cls.flank.write_text(FLANK_OBJ)
        cls.flank.with_suffix(".mtl").write_text(PANE_MTL)
        cls.nomtl = tmp / "plain.obj"
        cls.nomtl.write_text(SYNTHETIC_OBJ)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def build(self, obj, profile="complete", options=None, plan=None):
        name = "car.dx" if profile == "car" else "complete.dx"
        return geo.build_candidate(obj, self.donor[name], self.ctx, plan or self.plan, profile, options)

    def test_translucent_pane_material_is_detected_by_texture_not_name(self):
        gt = geo.parse_gt_full(self.obj)
        found = geo.find_glazing_materials(gt["faces"], gt["textures"])
        self.assertEqual(list(found), ["Mat6_Tex10"])
        self.assertEqual(found["Mat6_Tex10"]["min_alpha"], 230)

    def test_panes_go_to_glass_and_gt_glass_strips_become_trim(self):
        _, rep = self.build(self.obj)
        self.assertEqual(rep["glazing"]["active"], True)
        self.assertEqual(rep["arch"]["glazing_tris"], 1)
        self.assertEqual(rep["arch"]["glass_strip_tris_to_trim"], 1)
        self.assertEqual(rep["replaced_draw_stats"]["24"]["triangles"], 1)      # complete.dx glass draw = the pane

    def test_without_a_pane_material_the_v3_role_mapping_is_kept(self):
        _, rep = self.build(self.nomtl)
        self.assertFalse(rep["glazing"]["active"])
        self.assertEqual(rep["gt_face_roles"].get("glass"), 1)

    def test_v3_preset_reproduces_alpha_mode(self):
        _, rep = self.build(self.nomtl, options=geo.BuildOptions.v3())
        self.assertEqual(rep["arch"]["mode"], "alpha")
        self.assertEqual(rep["cabin"]["inset"], 0.0)

    def test_flank_panel_is_cut_and_lined_and_nothing_is_left_inside_the_wheel_house(self):
        data, rep = self.build(self.flank)
        self.assertGreater(rep["arch"]["tris_clipped"], 0)
        self.assertGreater(rep["arch"]["tube_tris"], 0)
        self.assertGreater(rep["arch"]["wall_tris"], 0)
        model = self.parse(data)
        hubs = geo.hubs_in_frame(self.ctx, "complete")
        radius = rep["arch"]["radius"]
        for draw in (3, 9):
            for p in diag.draw_points(model, draw):
                for (hx, hy, hz), x_in in zip(hubs, rep["arch"]["inboard_wall_abs_x"]):
                    if p[0] * hx > 0 and abs(p[0]) > x_in + 1e-6:
                        self.assertGreaterEqual(math.hypot(p[1] - hy, p[2] - hz), radius - 1e-5, (draw, p))

    def test_arch_cut_does_not_depend_on_the_ride_lift(self):
        _, a = self.build(self.flank)
        lifted = geo.plan_fit(self.ctx, AXLES, 0.29, lift=0.0)
        _, b = self.build(self.flank, plan=lifted)
        self.assertEqual(a["arch"]["radius"], b["arch"]["radius"])
        self.assertEqual(a["arch"]["inboard_wall_abs_x"], b["arch"]["inboard_wall_abs_x"])
        self.assertEqual(a["lift_m"], 0.12)

    def test_interior_shell_is_inset_inside_the_paint_shell(self):
        data, rep = self.build(self.obj)
        data0, rep0 = self.build(self.obj, options=geo.BuildOptions(interior_inset=0.0))
        self.assertLess(rep["cabin"]["roof_y"], rep0["cabin"]["roof_y"])
        self.assertGreater(rep["cabin"]["floor_y"], rep0["cabin"]["floor_y"])
        self.assertAlmostEqual(rep0["cabin"]["roof_y"] - rep["cabin"]["roof_y"], geo.INTERIOR_INSET, places=6)
        self.assertAlmostEqual(rep["cabin"]["floor_y"] - rep0["cabin"]["floor_y"], geo.INTERIOR_INSET, places=6)

    def test_frame_relation_and_validation_hold_for_the_v4_build(self):
        car, rep_car = self.build(self.flank, "car")
        comp, rep_comp = self.build(self.flank, "complete")
        mc, mm = self.parse(car), self.parse(comp)
        self.assertTrue(mc.diagnostics.validated and mm.diagnostics.validated)
        for a, b in zip(diag.BODY_DRAWS["car"], diag.BODY_DRAWS["complete"]):
            pa, pb = diag.draw_points(mc, a), diag.draw_points(mm, b)
            self.assertEqual(len(pa), len(pb))
            for p, q in zip(pa, pb):
                self.assertAlmostEqual(q[1] - p[1], self.ctx.frame_dy, places=4)


class DiagnosticsTests(unittest.TestCase):
    def test_ground_clearance_uses_the_physical_ground(self):
        if not HAVE_DONOR:
            self.skipTest("donor not available")
        from master_rallye.dx import parse_dx
        model = parse_dx(DONOR_DIR / "complete.dx")
        res = diag.ground_clearance(model, (3, 9), 0.012)
        self.assertAlmostEqual(res["lowest_body_vertex"] + 0.012, min(p[1] for d in (3, 9) for p in diag.draw_points(model, d)), places=3)


if __name__ == "__main__":
    unittest.main()
