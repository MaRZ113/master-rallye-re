"""Synthetic tests for the V-MESH3 frame/wheel-aware geometry pipeline (no GT assets needed)."""
import math
import tempfile
import unittest
from pathlib import Path

from tools import vmesh_diagnose as diag
from tools import vmesh_geometry as geo

DONOR_DIR = Path(r"D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataGx\Vehicles\Navara")
HAVE_DONOR = (DONOR_DIR / "car.dx").exists() and (DONOR_DIR / "complete.dx").exists() and (DONOR_DIR / "wheel.dx").exists()
AXLES = {"front_z": -1.3, "rear_z": 1.24, "wheelbase": 2.54}

# One triangle pair per classification role, in GT frame (front -Z, ground y = 0, hub height 0.29).
SYNTHETIC_OBJ = """\
v -0.8 0.30 -2.0
v 0.8 0.30 -2.0
v 0.8 0.80 -2.0
v -0.8 0.80 -2.0
v -0.8 0.30 2.0
v 0.8 0.30 2.0
v 0.8 0.80 2.0
v -0.8 1.20 0.0
v 0.8 1.20 0.0
v 0.0 1.20 -0.5
v -0.5 0.62 -0.2
v 0.5 0.62 -0.2
v 0.0 0.62 0.6
v -0.6 1.0 0.2
v 0.6 1.0 0.2
v 0.0 1.1 -0.8
o shapeA
usemtl Mat1_Tex0
f 1 2 3
f 1 3 4
f 5 6 7
o shapeB
usemtl Mat6_Tex35
f 1 2 8
o shapeC_tail_lamp_off
usemtl Mat6_Tex24
f 5 6 9
o shapeD
usemtl Mat6_Tex26
f 2 3 10
o shapeE
usemtl Mat4_Tex5
f 3 4 10
o shapeF
usemtl Mat-1_Tex35
f 11 12 13
f 14 15 16
"""


class PlanTests(unittest.TestCase):
    def test_race_wheel_scale_grows_to_physics_radius_but_keeps_arch_margin(self):
        fit = geo.wheel_scale_from_clearance(0.3832, 0.8802, 0.0451, 0.005)
        self.assertAlmostEqual(fit["target_radius_m"], 0.3774, places=3)
        self.assertAlmostEqual(fit["scale"], 0.9849, places=3)
        self.assertLessEqual(fit["target_radius_m"], 0.3832)

    @staticmethod
    def ctx():
        hubs = tuple((sx * 0.84, 0.395, z) for sx in (-1, 1) for z in (1.495, -1.463))
        return geo.DonorContext(0.393, hubs, 0.383, 0.146)

    def test_hub_alignment_in_all_axes_and_frames(self):
        ctx = self.ctx()
        plan = geo.plan_fit(ctx, AXLES, 0.29)
        for profile in ("car", "complete"):
            tp, _ = plan.transform(ctx, profile)
            hub_y = 0.395 - (0.393 if profile == "car" else 0.0)
            front = tp((0.0, 0.29, -1.3))     # GT front hub centre
            rear = tp((0.0, 0.29, 1.24))
            self.assertAlmostEqual(front[2], 1.495, places=5)
            self.assertAlmostEqual(rear[2], -1.463, places=5)
            self.assertAlmostEqual(front[1], hub_y, places=6)

    def test_wheel_scale_from_wheelbase_and_gt_radius(self):
        ctx = self.ctx()
        plan = geo.plan_fit(ctx, AXLES, 0.29)
        self.assertAlmostEqual(plan.scale, (1.495 + 1.463) / 2.54, places=6)
        self.assertAlmostEqual(plan.wheel_scale, plan.scale * 0.29 / 0.383, places=9)
        override = geo.plan_fit(ctx, AXLES, 0.29, scale=1.0, wheel_scale=1.0)
        self.assertEqual((override.scale, override.wheel_scale), (1.0, 1.0))

    def test_race_hubs_are_complete_hubs_minus_frame_dy(self):
        ctx = self.ctx()
        race, front = geo.hubs_in_frame(ctx, "car"), geo.hubs_in_frame(ctx, "complete")
        for r, f in zip(race, front):
            self.assertAlmostEqual(f[1] - r[1], 0.393, places=9)
            self.assertEqual((r[0], r[2]), (f[0], f[2]))

    def test_scale_about_hub_fixes_hub_and_scales_radius(self):
        hubs = self.ctx().hubs_complete
        h = hubs[0]
        self.assertEqual(geo.scale_about_hub(h, hubs, 0.5), h)
        p = (h[0] + 0.1, h[1] + 0.3, h[2] - 0.1)
        q = geo.scale_about_hub(p, hubs, 0.5)
        self.assertAlmostEqual(q[1] - h[1], 0.15, places=9)
        self.assertAlmostEqual(q[2] - h[2], -0.05, places=9)

    def test_relieve_only_inside_tyre(self):
        hubs = self.ctx().hubs_complete
        h = hubs[0]
        inside = (h[0], h[1] + 0.1, h[2])
        moved, did = geo.relieve(inside, hubs, 0.35, 0.16)
        self.assertTrue(did)
        self.assertGreaterEqual(math.hypot(moved[1] - h[1], moved[2] - h[2]), 0.35 - 1e-9)
        far, did = geo.relieve((h[0], h[1] + 0.5, h[2]), hubs, 0.35, 0.16)
        self.assertFalse(did)


@unittest.skipUnless(HAVE_DONOR, "unpacked retail Navara donor not available")
class DonorPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.donor = {n: (DONOR_DIR / n).read_bytes() for n in ("car.dx", "complete.dx", "wheel.dx")}
        cls.ctx = geo.make_context(cls.donor["car.dx"], cls.donor["complete.dx"], cls.donor["wheel.dx"])
        cls.plan = geo.plan_fit(cls.ctx, AXLES, 0.29)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.obj = Path(cls.tmp.name) / "synthetic.obj"
        cls.obj.write_text(SYNTHETIC_OBJ)
        cls.out = {}
        for profile, name in (("car", "car.dx"), ("complete", "complete.dx")):
            cls.out[name] = geo.build_candidate(cls.obj, cls.donor[name], cls.ctx, cls.plan, profile)
        cls.wheel = geo.build_wheel_candidate(cls.donor["wheel.dx"], cls.plan.wheel_scale)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_donor_frame_offset_is_pure_vertical(self):
        self.assertAlmostEqual(self.ctx.frame_dy, 0.3932, places=3)
        self.assertGreater(len(self.ctx.hubs_complete), 3)

    def test_car_and_complete_body_draws_differ_by_exact_frame_offset(self):
        from master_rallye.dx import parse_dx_bytes
        car, comp = (parse_dx_bytes(self.out[n][0]) for n in ("car.dx", "complete.dx"))
        for a, b in zip(diag.BODY_DRAWS["car"], diag.BODY_DRAWS["complete"]):
            pa, pb = diag.draw_points(car, a), diag.draw_points(comp, b)
            self.assertEqual(len(pa), len(pb))
            for p, q in zip(pa, pb):
                self.assertAlmostEqual(q[1] - p[1], self.ctx.frame_dy, places=4)
                self.assertAlmostEqual(q[0], p[0], places=5)
                self.assertAlmostEqual(q[2], p[2], places=5)

    def test_draw_identity_preserved_and_validated(self):
        from master_rallye.dx import parse_dx_bytes
        for name in ("car.dx", "complete.dx"):
            donor, cand = parse_dx_bytes(self.donor[name]), parse_dx_bytes(self.out[name][0])
            self.assertTrue(cand.diagnostics.validated)
            self.assertEqual(len(donor.physical_draws), len(cand.physical_draws))
            for a, b in zip(donor.physical_draws, cand.physical_draws):
                self.assertEqual((a.tag, a.group_label, a.control_words, [t.value for t in a.texture_slots]),
                                 (b.tag, b.group_label, b.control_words, [t.value for t in b.texture_slots]))

    def test_crew_translated_rigidly_under_cabin_roof(self):
        from master_rallye.dx import parse_dx_bytes
        rep = self.out["car.dx"][1]
        donor, cand = parse_dx_bytes(self.donor["car.dx"]), parse_dx_bytes(self.out["car.dx"][0])
        dy = rep["crew"]["dy"]
        for d in rep["crew"]["draws"]:
            for p, q in zip(diag.draw_points(donor, d), diag.draw_points(cand, d)):
                self.assertAlmostEqual(q[1] - p[1], dy, places=4)
                self.assertAlmostEqual(q[0], p[0], places=5)
        top = max(p[1] for d in rep["crew"]["draws"] for p in diag.draw_points(cand, d))
        self.assertAlmostEqual(top, rep["cabin"]["roof_y"] - rep["crew"]["headroom_requested"], places=3)

    def test_embedded_wheels_scaled_about_hubs_in_complete(self):
        from master_rallye.dx import parse_dx_bytes
        donor, cand = parse_dx_bytes(self.donor["complete.dx"]), parse_dx_bytes(self.out["complete.dx"][0])
        k = self.plan.wheel_scale
        for hub in self.ctx.hubs_complete[:1]:
            for d in (20, 21, 22, 23):
                for p, q in zip(diag.draw_points(donor, d), diag.draw_points(cand, d)):
                    if math.hypot(p[0] - hub[0], p[2] - hub[2]) < 0.5:
                        self.assertAlmostEqual(q[1] - hub[1], k * (p[1] - hub[1]), places=4)

    def test_wheel_dx_scaled_about_origin(self):
        from master_rallye.dx import parse_dx_bytes
        r_donor, _ = diag.wheel_extent(parse_dx_bytes(self.donor["wheel.dx"]))
        r_new, _ = diag.wheel_extent(parse_dx_bytes(self.wheel[0]))
        self.assertAlmostEqual(r_new / r_donor, self.plan.wheel_scale, places=3)

    def test_no_tyre_intrusion_after_fit(self):
        from master_rallye.dx import parse_dx_bytes
        r_vis = self.plan.wheel_scale * self.ctx.wheel_radius
        for name, frame, draws in (("car.dx", "car", diag.BODY_DRAWS["car"]), ("complete.dx", "complete", diag.BODY_DRAWS["complete"])):
            model = parse_dx_bytes(self.out[name][0])
            res = diag.clearance(model, draws, geo.hubs_in_frame(self.ctx, frame), r_vis, self.plan.wheel_scale * self.ctx.wheel_half_width)
            for hub in res["hubs"]:
                self.assertEqual(hub["samples_inside_tyre"], 0, (name, hub))


def _png(width, height, pixel):
    """Tiny RGBA8 PNG writer; pixel(x, y) -> (r, g, b, a)."""
    import struct
    import zlib
    raw = b"".join(b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(width)) for y in range(height))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    sig = bytes([0x89]) + b"PNG" + bytes([13, 10, 26, 10])
    return (sig + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _corner(x, y, z, u, v):
    return ((x, y, z), None, ("t", x, y, z), (u, v))


class AlphaCutoutTests(unittest.TestCase):
    def tex(self, transparent_left_half=True):
        # left half transparent, right half solid; PNG rows run top-down
        png = _png(8, 8, lambda x, y: (10, 20, 30, 0 if (x < 4) == transparent_left_half else 255))
        return geo.AlphaTexture(png)

    def tri(self):
        return (_corner(0, 0, 0, 0.0, 0.0), _corner(1, 0, 0, 1.0, 0.0), _corner(0, 1, 0, 0.0, 1.0))

    def test_policy_by_transparent_fraction(self):
        self.assertEqual(self.tex().policy, "drop")                      # 50 % transparent: overlay
        solid = geo.AlphaTexture(_png(4, 4, lambda x, y: (1, 1, 1, 255)))
        self.assertEqual(solid.policy, "opaque")
        mostly = geo.AlphaTexture(_png(10, 10, lambda x, y: (1, 1, 1, 0 if x == 0 else 255)))   # 10 %
        self.assertEqual(mostly.policy, "carve")
        invisible = geo.AlphaTexture(_png(1, 1, lambda x, y: (0, 0, 0, 0)))
        self.assertEqual(invisible.policy, "drop")

    def test_solid_triangle_unchanged_and_transparent_triangle_removed(self):
        solid = geo.AlphaTexture(_png(4, 4, lambda x, y: (1, 1, 1, 255)))
        s, h = geo.carve_triangle(self.tri(), solid, True)
        self.assertEqual((len(s), len(h)), (1, 0))
        clear = geo.AlphaTexture(_png(4, 4, lambda x, y: (1, 1, 1, 0)))
        s, h = geo.carve_triangle(self.tri(), clear, True)
        self.assertEqual((len(s), len(h)), (0, 1))

    def test_mixed_triangle_conserves_area_and_splits_at_the_edge(self):
        s, h = geo.carve_triangle(self.tri(), self.tex(), True, 4)
        total = sum(geo._tri_area(t) for t in s) + sum(geo._tri_area(t) for t in h)
        self.assertAlmostEqual(total, 0.5, places=6)
        hole = sum(geo._tri_area(t) for t in h)
        self.assertGreater(hole, 0.1)
        self.assertLess(hole, 0.4)
        self.assertTrue(all(t[0][0][0] + t[1][0][0] + t[2][0][0] < 3 * 0.75 for t in h))   # holes lie on the transparent side

    def test_zone_confines_subdivision(self):
        s, h = geo.carve_triangle(self.tri(), self.tex(), True, 4, zone=lambda p: False)
        self.assertEqual((len(s), len(h)), (1, 0))
        s2, h2 = geo.carve_triangle(self.tri(), self.tex(), True, 4, zone=lambda p: p[0] < 0.4)
        self.assertGreater(len(h2), 0)

    def test_wheel_zone_and_outer_lip_snap(self):
        hubs = PlanTests.ctx().hubs_complete
        h = hubs[0]
        self.assertTrue(geo.in_wheel_zone((h[0] - 0.2, h[1] + 0.1, h[2]), hubs, 0.5))
        self.assertFalse(geo.in_wheel_zone((0.0, h[1] + 0.1, h[2]), hubs, 0.5))
        far_out = (h[0] - 0.25, h[1] + 0.2, h[2])      # outer-fender plane, inside the arch radius
        q, moved = geo.relieve(far_out, hubs, 0.37, 0.0, outer=True)
        self.assertTrue(moved)
        self.assertAlmostEqual(math.hypot(q[1] - h[1], q[2] - h[2]), 0.37, places=9)
        self.assertEqual(q[0], far_out[0])


@unittest.skipUnless(HAVE_DONOR, "unpacked retail Navara donor not available")
class ProjectValidationTests(unittest.TestCase):
    def test_scaled_wheel_needs_topology_candidate_and_passes_validation(self):
        import hashlib
        import json
        from master_rallye.vehicle_project import VehicleProject, validate_vehicle
        donor = (DONOR_DIR / "wheel.dx").read_bytes()
        ctx = geo.make_context((DONOR_DIR / "car.dx").read_bytes(), (DONOR_DIR / "complete.dx").read_bytes(), donor)
        wheel, _ = geo.build_wheel_candidate(donor, 0.88)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "wheel.dx").write_bytes(wheel)
            sha = hashlib.sha256(donor).hexdigest()
            for key, expect in (("topology_candidate", "PASS"), ("candidate", "FAIL")):
                spec = {"vehicle_name": "Navara", "source_vehicle_dir": str(DONOR_DIR),
                        "resources": {"wheel.dx": {"source_sha256": sha, key: "wheel.dx"}}}
                (tmp / "p.json").write_text(json.dumps(spec))
                self.assertEqual(validate_vehicle(VehicleProject.load(tmp / "p.json"))["status"], expect, key)


class CollisionFitTests(unittest.TestCase):
    def test_hull_floor_kept_and_top_follows_roof(self):
        if not HAVE_DONOR:
            self.skipTest("donor not available")
        from tools import build_vmesh3_impreza_experimental as drv
        from master_rallye.dx import parse_dx_bytes
        car = (DONOR_DIR / "car.dx").read_bytes()
        hull = parse_dx_bytes(car).collision.convex_hull.representation_a.geometry_a.vertices
        lo_y = min(p[1] for p in hull)
        rep = {"body_extent": {"min": [-1.0, -0.3, -2.5], "max": [1.0, 1.45, 2.5], "roof_y_p99": 1.1}}
        fit = drv.collision_fit(car, rep)
        c, sy, ty = fit["centre"][1], fit["scale"][1], fit["translation"][1]
        hi_y = max(p[1] for p in hull)
        self.assertAlmostEqual(c - sy * (c - lo_y) + ty, lo_y, places=3)          # floor unchanged
        self.assertAlmostEqual(c + sy * (hi_y - c) + ty, 1.1, places=3)           # top = roof, not antenna
        self.assertEqual(fit["translation"][0], 0.0)


if __name__ == "__main__":
    unittest.main()
