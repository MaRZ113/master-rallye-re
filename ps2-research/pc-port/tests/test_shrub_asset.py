"""Separate shrub identity and shared-format checks using synthetic positions."""
import importlib.util
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PORT / "tools"))
spec = importlib.util.spec_from_file_location("prepare_shrub_pilot", PORT / "tools/prepare_shrub_pilot.py")
asset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset)


def synthetic_artifact():
    return asset.serialize_artifact([(1., 2., 1.), (-.25, 3., -8.), (1., 2., 1.), (8., 4., 8.)], bytes(4096))


class ShrubAssetTests(unittest.TestCase):
    def test_deterministic_roundtrip_shared_layout_separate_identity(self):
        data = synthetic_artifact()
        self.assertEqual(data, synthetic_artifact())
        info = asset.validate_artifact(data, asset.grass.sha(data))
        self.assertEqual(info["point_count"], 4)
        self.assertEqual(info["bin_count"], 3)
        self.assertEqual(info["psm_sha256"], asset.PSM_SHA)
        self.assertEqual(info["gxi_sha256"], asset.GXI_SHA)
        self.assertEqual(info["pc_dx_sha256"], asset.PC_DX_SHA)
        self.assertEqual(info["bounds"], {"min": [-.25, 2., -8.], "max": [8., 4., 8.]})

    def test_first_grass_texture_identity_rejected_by_shrub_reader(self):
        first = asset.grass.serialize_artifact([(0., 0., 0.)], bytes(4096))
        with self.assertRaisesRegex(ValueError, "source identities mismatch"):
            asset.validate_artifact(first)
        self.assertNotEqual(asset.GXI_SHA, asset.grass.GXI_SHA)

    def test_unknown_texture_identity_rejected(self):
        data = bytearray(synthetic_artifact())
        data[64:96] = bytes(32)
        with self.assertRaisesRegex(ValueError, "source identities mismatch"):
            asset.validate_artifact(data)

    def test_content_tamper_rejected(self):
        original = synthetic_artifact()
        modified = bytearray(original)
        modified[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            asset.validate_artifact(modified, asset.grass.sha(original))

    def test_original_spelling_singular_and_noncategory_controls(self):
        self.assertEqual(asset.source_category("$surfacetype(grass) $detail(shrubs)"), "shrubs")
        self.assertEqual(asset.source_category("$detail(SHRUBS)"), "shrubs")
        self.assertEqual(asset.source_category("$detail(shrub)"), "unrecognized")
        self.assertEqual(asset.source_category("$DETAIL(shrubs)"), "none")
        self.assertEqual(asset.source_category("$surfacetype(grass)"), "none")
        self.assertEqual(asset.source_category("$detail(grass) $detail(shrubs)"), "grass")
        self.assertEqual(asset.source_category("$detail(stones)"), "stones")

    def test_duplicate_points_and_source_order_retained(self):
        data = synthetic_artifact()
        info = asset.validate_artifact(data)
        points = [asset.grass.POINT.unpack_from(data, info["layout"]["point_offset"] + 12 * i) for i in range(4)]
        self.assertEqual(points, [(-.25, 3., -8.), (1., 2., 1.), (1., 2., 1.), (8., 4., 8.)])

    def test_shared_format_malformed_counts_and_membership_fail_closed(self):
        for offset, value in ((12, 0), (16, asset.grass.MAX_BINS + 1), (20, 64),
                              (128 + 8, 1), (128 + 12, 0), (144 + 8, 3)):
            data = bytearray(synthetic_artifact())
            struct.pack_into("<I", data, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                asset.validate_artifact(data)

    def test_nonfinite_positions_and_wrong_image_fail_closed(self):
        for value in (math.nan, math.inf, -math.inf, asset.grass.MAX_COORDINATE + 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                asset.serialize_artifact([(value, 0., 0.)], bytes(4096))
        with self.assertRaises(ValueError):
            asset.serialize_artifact([(0., 0., 0.)], bytes(4104))

    def test_new_output_cannot_overwrite_first_grass_or_elsewhere(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = root / asset.ASSET_RELATIVE
            self.assertEqual(asset.asset_path(expected, root), expected.resolve())
            for path in (root / asset.grass.ASSET_RELATIVE, root / "Turkey3Shrubs.ps2grass",
                         expected.with_name("Other.ps2grass"), root / ".assets/grass/../Other.ps2grass"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    asset.asset_path(path, root)

    def test_shared_category_placement_changes_lift_only_on_same_synthetic_surface(self):
        import detail_runtime as detail
        # Original caller's C,B,A order supplies the scanline's left/right edges.
        polygon = [(5., 2., 1.), (1., 2., 5.), (1., 2., 1.)]
        jitter, _ = detail.jitter_table()
        first = detail.scan_polygon(polygon, (2., 0., 0.), "grass", jitter)
        second = detail.scan_polygon(polygon, (2., 0., 0.), "shrubs", jitter)
        self.assertGreater(len(first), 0)
        self.assertEqual(len(first), len(second))
        self.assertEqual([(row["grid_x"], row["grid_z"], row["jitter_index"]) for row in first],
                         [(row["grid_x"], row["grid_z"], row["jitter_index"]) for row in second])
        for a, b in zip(first, second):
            self.assertEqual((a["position"][0], a["position"][2]), (b["position"][0], b["position"][2]))
            self.assertEqual(a["position"][1], detail.add(2., detail.LIFT["grass"]))
            self.assertEqual(b["position"][1], detail.add(2., detail.LIFT["shrubs"]))


if __name__ == "__main__":
    unittest.main()
