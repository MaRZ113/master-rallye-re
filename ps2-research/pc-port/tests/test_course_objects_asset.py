"""Corpus-independent checks for the private source-geometry preview artifact."""
import importlib.util
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

PORT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_course_objects", PORT / "tools/prepare_course_objects.py")
asset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset)


def synthetic_vertices():
    return [(0.0, 0.0, 0.0, 0x78123456, 0.25, -0.5),
            (1.0, 0.0, 0.0, 0x78123456, 1.25, -0.5),
            (0.0, 0.0, 1.0, 0x78123456, 0.25, 0.5)]


def synthetic_artifact():
    return asset.serialize_artifact([dict(node_offset=100, material_offset=110, first_vertex=0, vertex_count=3)],
                                    synthetic_vertices(), bytes(16384), "01" * 32, "02" * 32)


class CourseObjectsAssetTests(unittest.TestCase):
    def test_layout_round_trip_and_determinism(self):
        data = synthetic_artifact()
        self.assertEqual(asset.HEADER.size, 88)
        self.assertEqual(asset.MESH.size, 16)
        self.assertEqual(asset.VERTEX.size, 24)
        self.assertEqual(data, synthetic_artifact())
        report = asset.validate_artifact(data)
        self.assertEqual(report["triangle_count"], 1)
        self.assertEqual(report["psm_sha256"], "01" * 32)
        self.assertEqual(report["gxi_sha256"], "02" * 32)
        self.assertEqual(report["bounds"], {"min": [0.0, 0.0, 0.0], "max": [1.0, 0.0, 1.0]})
        self.assertEqual(report["layout"]["texture_offset"], 88 + 16 + 3 * 24)
        self.assertEqual(asset.VERTEX.unpack_from(data, 104), synthetic_vertices()[0])

    def test_packed_source_color_conversion(self):
        self.assertEqual(asset.argb_from_source(0x12345678), 0x78123456)
        self.assertEqual(asset.argb_from_source(0xffffffff), 0xffffffff)
        self.assertEqual(asset.argb_from_source(0xff000000), 0x00ff0000)
        for invalid in (-1, 0x100000000, 1.5):
            with self.assertRaises(ValueError):
                asset.argb_from_source(invalid)

    def test_adc_degenerate_and_original_uv_source_order(self):
        sys.path.insert(0, str(PORT.parent / "tools"))
        import water_runtime as w
        points = [(0., 0., 0.), (1., 0., 0.), (0., 0., 1.), (1., 0., 1.), (2., 0., 1.)]
        payload = bytearray(32 + len(points) * 52)
        for i, xyz in enumerate(points):
            at = 32 + i * 52
            struct.pack_into("<I", payload, at + 12, 1 if i == 2 else 0)
            struct.pack_into("<I", payload, at + 16, 0x12345678)
            struct.pack_into("<4f", payload, at + 20, 1.25 + i, -0.5 - i, 7., 8.)
            struct.pack_into("<3f", payload, at + 36, *xyz)
        scene = w.Scene(bytes(payload), len(points), 0, 0, [], {})
        mesh = {"strips": [dict(start=0, count=5)]}
        vertices, excluded = asset.collect_preview_vertices(scene, mesh)
        self.assertEqual(excluded, {"adc_suppressed": 1, "diagnostic_degenerate": 1})
        self.assertEqual(len(vertices), 3)
        self.assertEqual([v[:3] for v in vertices], points[1:4])
        self.assertEqual([v[3] for v in vertices], [0x78123456] * 3)
        self.assertEqual([v[4:] for v in vertices], [(2.25, -1.5), (3.25, -2.5), (4.25, -3.5)])

    def test_canonical_size_equation(self):
        self.assertEqual(asset.HEADER.size + 17 * asset.MESH.size + 2235 * asset.VERTEX.size + 16384, 70384)

    def test_output_confinement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            expected = root / asset.ASSET_RELATIVE
            self.assertEqual(asset.asset_path(expected, root), expected.resolve())
            for invalid in (root / "Turkey3Puddles.ps2obj", expected.with_name("Other.ps2obj"),
                            root / ".assets/course-objects/../Other.ps2obj"):
                with self.assertRaises(ValueError):
                    asset.asset_path(invalid, root)

    def test_bad_header_and_trailing_bytes_fail_closed(self):
        data = synthetic_artifact()
        bad_magic = b"UNKNOWN0" + data[8:]
        bad_version = data[:8] + struct.pack("<I", 2) + data[12:]
        for invalid in (b"", data[:-1], data + b"x", bad_magic, bad_version):
            with self.assertRaises(ValueError):
                asset.validate_artifact(invalid)

    def test_bad_mesh_ranges_fail_closed(self):
        vertices = synthetic_vertices()
        for row in (dict(node_offset=100, material_offset=90, first_vertex=0, vertex_count=3),
                    dict(node_offset=100, material_offset=110, first_vertex=1, vertex_count=3),
                    dict(node_offset=100, material_offset=110, first_vertex=0, vertex_count=2),
                    dict(node_offset=100, material_offset=110, first_vertex=0, vertex_count=6)):
            with self.assertRaises(ValueError):
                asset.serialize_artifact([row], vertices, bytes(16384))
        corrupted = bytearray(synthetic_artifact())
        struct.pack_into("<I", corrupted, asset.HEADER.size + 8, 1)
        with self.assertRaises(ValueError):
            asset.validate_artifact(corrupted)

    def test_nonfinite_and_float32_overflow_rejected(self):
        row = [dict(node_offset=100, material_offset=110, first_vertex=0, vertex_count=3)]
        for axis in (0, 1, 2, 4, 5):
            vertices = synthetic_vertices()
            v = list(vertices[0]); v[axis] = math.inf; vertices[0] = tuple(v)
            with self.assertRaises(ValueError):
                asset.serialize_artifact(row, vertices, bytes(16384))
        vertices = synthetic_vertices()
        v = list(vertices[0]); v[0] = 1e100; vertices[0] = tuple(v)
        with self.assertRaises(ValueError):
            asset.serialize_artifact(row, vertices, bytes(16384))
        corrupted = bytearray(synthetic_artifact())
        struct.pack_into("<f", corrupted, asset.HEADER.size + asset.MESH.size + 16, math.nan)
        with self.assertRaises(ValueError):
            asset.validate_artifact(corrupted)

    def test_wrong_texture_and_hashes_rejected(self):
        row = [dict(node_offset=100, material_offset=110, first_vertex=0, vertex_count=3)]
        for bad in (bytes(), bytes(16380), bytes(16388)):
            with self.assertRaises(ValueError):
                asset.serialize_artifact(row, synthetic_vertices(), bad)
        for bad in ("", "z" * 64, "00" * 31):
            with self.assertRaises(ValueError):
                asset.serialize_artifact(row, synthetic_vertices(), bytes(16384), bad)

    def test_unsupported_source_grammar_rejected(self):
        sys.path.insert(0, str(PORT.parent / "tools"))
        import water_runtime as w
        payload = bytearray(32 + 52 + 8)
        struct.pack_into("<3I", payload, 0, 0xd00d, 2, 0x539)
        struct.pack_into("<I", payload, 28, 1)
        struct.pack_into("<2I", payload, 32 + 52, 999, 100)
        with self.assertRaises(ValueError):
            w.decode_scene(bytes(payload))


if __name__ == "__main__":
    unittest.main()
