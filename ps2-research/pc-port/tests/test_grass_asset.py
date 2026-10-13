"""Synthetic private-grass format checks; no proprietary geometry fixture."""
import importlib.util
import math
from pathlib import Path
import struct
import tempfile
import unittest

PORT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_grass_pilot", PORT / "tools/prepare_grass_pilot.py")
asset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset)


def synthetic_points():
    # Explicit synthetic input; order within a bin must survive batching.
    return [(1., 2., 1.), (-.25, 3., -8.), (1., 2., 1.), (8., 4., 8.), (2., 2., 1.)]


def synthetic_artifact():
    return asset.serialize_artifact(synthetic_points(), bytes(4096), "01" * 32, "02" * 32, "03" * 32)


class GrassAssetTests(unittest.TestCase):
    def test_versioned_layout_round_trip_and_determinism(self):
        data = synthetic_artifact()
        self.assertEqual(asset.HEADER.size, 128)
        self.assertEqual(asset.BIN.size, 16)
        self.assertEqual(asset.POINT.size, 12)
        self.assertEqual(data, synthetic_artifact())
        info = asset.validate_artifact(data, asset.sha(data), ("01" * 32, "02" * 32, "03" * 32))
        self.assertEqual(info["point_count"], 5)
        self.assertEqual(info["bin_count"], 3)
        self.assertEqual(info["bounds"], {"min": [-.25, 2., -8.], "max": [8., 4., 8.]})
        self.assertEqual(info["layout"]["point_offset"], 176)
        self.assertEqual(info["layout"]["texture_offset"], 236)
        self.assertEqual(info["size"], 4332)

    def test_lex_bins_and_stable_duplicate_source_order(self):
        data = synthetic_artifact()
        self.assertEqual([asset.BIN.unpack_from(data, 128 + n * 16) for n in range(3)],
                         [(-1, -1, 0, 1), (0, 0, 1, 3), (1, 1, 4, 1)])
        info = asset.validate_artifact(data)
        points = [asset.POINT.unpack_from(data, info["layout"]["point_offset"] + i * 12) for i in range(5)]
        self.assertEqual(points, [(-.25, 3., -8.), (1., 2., 1.), (1., 2., 1.), (2., 2., 1.), (8., 4., 8.)])

    def test_negative_and_float32_bin_boundaries(self):
        self.assertEqual(asset.point_bin((-0.01, 0., 0.)), (-1, 0))
        self.assertEqual(asset.point_bin((-8., 0., -8.)), (-1, -1))
        self.assertEqual(asset.point_bin((-8.0001, 0., -8.0001)), (-2, -2))
        # Serializing this host-double precursor rounds across a bin boundary.
        data = asset.serialize_artifact([(7.99999999999, 0., 0.)], bytes(4096))
        self.assertEqual(asset.BIN.unpack_from(data, 128), (1, 0, 0, 1))
        asset.validate_artifact(data)

    def test_bin_major_z_minor_x_order(self):
        data = asset.serialize_artifact([(1., 0., 17.), (9., 0., 1.), (1., 0., 1.), (9., 0., 9.)], bytes(4096))
        self.assertEqual([asset.BIN.unpack_from(data, 128 + i * 16)[:2] for i in range(4)],
                         [(0, 0), (1, 0), (1, 1), (0, 2)])
        asset.validate_artifact(data)

    def test_wrong_magic_version_size_and_trailing_bytes(self):
        data = synthetic_artifact()
        for invalid in (b"", data[:127], data[:-1], data + b"x", b"UNKNOWN0" + data[8:],
                        data[:8] + struct.pack("<I", 2) + data[12:]):
            with self.assertRaises(ValueError):
                asset.validate_artifact(invalid)

    def test_header_count_and_texture_budgets_fail_closed(self):
        for offset, value in ((12, 0), (12, asset.MAX_POINTS + 1), (16, 0),
                              (16, asset.MAX_BINS + 1), (16, 6), (20, 64), (24, 64), (28, 4095)):
            data = bytearray(synthetic_artifact())
            struct.pack_into("<I", data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                asset.validate_artifact(data)

    def test_bins_nonempty_contiguous_and_complete(self):
        for offset, value in ((128 + 8, 1), (128 + 12, 0), (128 + 12, 6),
                              (144 + 8, 2), (160 + 8, 3)):
            data = bytearray(synthetic_artifact())
            struct.pack_into("<I", data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                asset.validate_artifact(data)

    def test_unordered_duplicate_or_wrong_membership_bin_rejected(self):
        for index, key in ((1, (-1, -1)), (1, (-2, -1)), (1, (0, 1))):
            data = bytearray(synthetic_artifact())
            struct.pack_into("<2i", data, 128 + index * 16, *key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                asset.validate_artifact(data)

    def test_nonfinite_and_out_of_bounds_positions(self):
        for value in (math.nan, math.inf, -math.inf, 1e100, asset.MAX_COORDINATE + 1):
            for axis in range(3):
                point = [1., 2., 1.]
                point[axis] = value
                with self.subTest(value=value, axis=axis), self.assertRaises(ValueError):
                    asset.serialize_artifact([point], bytes(4096))
        for value in (math.nan, math.inf):
            data = bytearray(synthetic_artifact())
            struct.pack_into("<f", data, 176 + 4, value)
            with self.assertRaises(ValueError):
                asset.validate_artifact(data)

    def test_identity_and_tamper_checks(self):
        data = synthetic_artifact()
        for wrong in ("", "00" * 32, "ff" * 32):
            with self.assertRaises(ValueError):
                asset.validate_artifact(data, wrong)
        with self.assertRaises(ValueError):
            asset.validate_artifact(data, expected_sources=("01" * 32, "ff" * 32, "03" * 32))
        tampered = bytearray(data)
        tampered[-1] ^= 1
        with self.assertRaises(ValueError):
            asset.validate_artifact(tampered, asset.sha(data))
        tampered = bytearray(data)
        tampered[176 + 4] ^= 1
        with self.assertRaises(ValueError):
            asset.validate_artifact(tampered, asset.sha(data))

    def test_serialization_limits_and_hash_format(self):
        with self.assertRaises(ValueError):
            asset.serialize_artifact([], bytes(4096))
        with self.assertRaises(ValueError):
            asset.serialize_artifact([(0., 0., 0.)] * (asset.MAX_POINTS + 1), bytes(4096))
        for data in (bytes(), bytes(4095), bytes(4104)):
            with self.assertRaises(ValueError):
                asset.serialize_artifact([(0., 0., 0.)], data)
        for value in ("", "z" * 64, "00" * 31, 5):
            with self.assertRaises(ValueError):
                asset.serialize_artifact([(0., 0., 0.)], bytes(4096), value)

    def test_output_confinement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = root / asset.ASSET_RELATIVE
            self.assertEqual(asset.asset_path(expected, root), expected.resolve())
            for path in (root / "Turkey3Grass.ps2grass", expected.with_name("Other.ps2grass"),
                         root / ".assets/grass/../Other.ps2grass"):
                with self.assertRaises(ValueError):
                    asset.asset_path(path, root)


if __name__ == "__main__":
    unittest.main()
