"""Synthetic tests for the V-MESH1 GT3 -> donor-draw converter (no GT assets needed)."""
import math
import tempfile
import unittest
from pathlib import Path

from tools import vmesh_gt3_to_dx as conv

DONOR = Path(r"D:\Game\Master Rallye\Data.sma_unpacked\DataGx\Vehicles\Navara\car.dx")


class ClassifyTests(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(conv.classify("shape38_reflection", "Mat-1_Tex510"), "exclude")
        self.assertEqual(conv.classify("shape43_tail_lamp_on", "Mat6_Tex24"), "exclude")
        self.assertEqual(conv.classify("shape39", "Mat4_Tex5"), "glass")
        self.assertEqual(conv.classify("shape41_tail_lamp_off", "Mat6_Tex24"), "tail_lamp")
        self.assertEqual(conv.classify("shape45", "Mat6_Tex26"), "head_lamp")
        self.assertEqual(conv.classify("shape33", "Mat6_Tex35"), "black")
        self.assertEqual(conv.classify("shape34", "Mat1_Tex17"), "paint")
        self.assertEqual(conv.classify("shape28", "Mat-1_Tex35"), "interior")

    def test_profiles_cover_distinct_donor_draws(self):
        for name, profile in conv.PROFILES.items():
            used = list(profile["roles"].values()) + list(profile["keep"])
            self.assertEqual(len(used), len(set(used)), name)
        self.assertIn("interior", conv.PROFILES["complete"]["roles"])
        self.assertNotIn("interior", conv.PROFILES["car"]["roles"])

    def test_wheel_relief_pushes_points_out(self):
        inside = (0.855, 0.401, 1.495)           # hub centre
        moved, flag = conv.relieve_wheel_volumes(inside)
        self.assertTrue(flag)
        self.assertGreaterEqual(math.hypot(moved[1] - 0.401, moved[2] - 1.495), conv.WHEEL_RADIUS + conv.ARCH_MARGIN - 1e-9)
        far, flag = conv.relieve_wheel_volumes((0.0, 0.9, 0.0))
        self.assertFalse(flag)
        self.assertEqual(far, (0.0, 0.9, 0.0))


class FitTests(unittest.TestCase):
    axles = {"front_z": -1.3, "rear_z": 1.24, "wheelbase": 2.54}

    def test_yaw_scale_and_axle_alignment(self):
        s, tp, tn = conv.fit_transform(self.axles, None)
        self.assertAlmostEqual(s, (1.495 + 1.463) / 2.54, places=6)
        front = tp((0.0, 0.0, -1.3))   # GT front axle -> donor front axle
        rear = tp((0.0, 0.0, 1.24))
        self.assertAlmostEqual(front[2], 1.495, places=6)
        self.assertAlmostEqual(rear[2], -1.463, places=6)
        self.assertAlmostEqual(tp((1.0, 0.0, 0.0))[0], -s, places=6)
        self.assertEqual(tn((1.0, 2.0, 3.0)), (-1.0, 2.0, -3.0))

    def test_rotation_preserves_winding(self):
        _, tp, _ = conv.fit_transform(self.axles, 1.0)
        a, b, c = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
        before = conv.face_normal(a, b, c)
        after = conv.face_normal(tp(a), tp(b), tp(c))
        self.assertAlmostEqual(before[2], -after[2], places=6)  # normal yawed by 180 deg, not flipped


class ParseTests(unittest.TestCase):
    def test_parse_obj(self):
        text = "v 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 1\no shape1\nusemtl Mat1_Tex0\nf 1//1 2//1 3//1\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.obj"
            p.write_text(text)
            r = conv.parse_gt_obj(p)
        self.assertEqual(len(r["faces"]), 1)
        self.assertEqual(r["faces"][0][:2], ("shape1", "Mat1_Tex0"))
        self.assertEqual(r["faces"][0][2][0], (0, None, 0))


@unittest.skipUnless(DONOR.exists(), "unpacked retail Navara donor not available")
class DonorSanityTests(unittest.TestCase):
    def test_donor_draw_roles_exist(self):
        from master_rallye.dx import parse_dx_bytes
        model = parse_dx_bytes(DONOR.read_bytes())
        textures = {d.draw_index: d.texture_slots[0].value for d in model.physical_draws}
        self.assertEqual(textures[3], "colour-tga")
        self.assertEqual(textures[9], "black-tga")
        self.assertEqual(textures[25], "headlamp-tga")
        self.assertEqual(model.physical_draws[35].group_label, "screenfront")


if __name__ == "__main__":
    unittest.main()
