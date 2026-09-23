from __future__ import annotations

import math
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.collision import parse_collision_sections
from master_rallye.dx import MAGIC, parse_dx_bytes
from master_rallye.errors import BoundsError, FormatError
from tests.helpers.collision_fixture import tag101, tag102


def synthetic_dx(trailing):
    positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    blob = bytearray(struct.pack("<4I", MAGIC, 135, 1337, 3))
    for value in positions:
        blob += struct.pack("<3f", *value)
    for _ in positions:
        blob += struct.pack("<3f", 0.0, 0.0, 1.0)
    blob += bytes((255, 255, 255, 255)) * 3
    blob += struct.pack("<I", 0)
    blob += struct.pack("<I3H", 3, 0, 1, 2)
    record = bytearray(struct.pack("<7If4BI", 2, 0, 2, 0, 3, 0, 0, 1.0, 0, 0, 0, 0, 0))
    record += struct.pack("<2I", 0, 0)
    blob += struct.pack("<2I", 1, 1) + record
    blob += struct.pack("<2I3I", 1, 3, 1, 0, 2)
    blob += trailing
    return bytes(blob)


class CollisionParserTests(unittest.TestCase):
    def test_nested_tag101_boundaries_and_dx_integration(self):
        residual = struct.pack("<I", 1339) + b"R" * 40
        encoded = tag101(suffix=tag102() + residual)
        sections = parse_collision_sections(encoded, base_offset=0x1000, source="synthetic")
        hull = sections.convex_hull
        self.assertIsNotNone(hull)
        self.assertEqual(hull.tag_offset, 0x1000)
        self.assertEqual(hull.payload_offset, 0x1004)
        self.assertEqual(hull.end_offset, sections.cylinder.tag_offset)
        self.assertEqual(sections.tag_ids, (101, 102))
        self.assertEqual(sections.unparsed_data, residual)
        self.assertEqual(hull.base_geometry.vertex_count, 1)
        self.assertEqual(hull.representation_a.geometry_a.vertex_count, 4)
        self.assertEqual(hull.representation_a.face_count, 4)
        self.assertEqual(len(hull.representation_a.edges), 6)
        self.assertEqual(hull.representation_a.face_loop_indices[0], (2, 1, 0))
        self.assertTrue(math.isclose(hull.representation_a.face_scalars[0], 0.5))

        model = parse_dx_bytes(synthetic_dx(encoded))
        self.assertEqual(model.collision.tag_ids, (101, 102))
        self.assertEqual(model.collision.convex_hull.raw, hull.raw)
        self.assertTrue(model.diagnostics.validated)

    def test_negative_counts_indices_and_nonfinite_values_are_rejected(self):
        negative_vertices = bytearray(tag101())
        struct.pack_into("<i", negative_vertices, 4, -1)
        with self.assertRaisesRegex(FormatError, "unreasonable count -1"):
            parse_collision_sections(bytes(negative_vertices))

        negative_triangles = bytearray(tag101())
        struct.pack_into("<i", negative_triangles, 8, -1)
        with self.assertRaisesRegex(FormatError, "triangle count"):
            parse_collision_sections(bytes(negative_triangles))

        bad_index = tag101(base_triangles=((1, 0, 0),))
        with self.assertRaisesRegex(FormatError, "outside 0..0"):
            parse_collision_sections(bad_index)

        nonfinite = bytearray(tag101())
        struct.pack_into("<f", nonfinite, 24, float("nan"))
        with self.assertRaisesRegex(FormatError, "non-finite"):
            parse_collision_sections(bytes(nonfinite))
        preserved = parse_collision_sections(bytes(nonfinite), strict=False)
        self.assertFalse(preserved.validated)
        self.assertIn("non-finite float", preserved.errors[0])

    def test_truncation_and_nested_reference_validation(self):
        encoded = tag101()
        with self.assertRaises(BoundsError):
            parse_collision_sections(encoded[:-1])

        parsed = parse_collision_sections(encoded).convex_hull
        bad_edge = bytearray(encoded)
        struct.pack_into("<i", bad_edge, parsed.representation_a.edge_count_offset + 4, 99)
        with self.assertRaisesRegex(FormatError, "edge vertex"):
            parse_collision_sections(bytes(bad_edge))

        bad_adjacency = bytearray(encoded)
        struct.pack_into("<i", bad_adjacency, parsed.representation_a.edge_face_adjacency_offset, 99)
        with self.assertRaisesRegex(FormatError, "edge-face adjacency"):
            parse_collision_sections(bytes(bad_adjacency))

        bad_loop = bytearray(encoded)
        struct.pack_into("<i", bad_loop, parsed.representation_a.face_loop_offset + 4, 99)
        with self.assertRaisesRegex(FormatError, "face 0 loop"):
            parse_collision_sections(bytes(bad_loop))

    def test_tag102_and_unknown_tag_preservation(self):
        residual = struct.pack("<I", 777) + b"unknown"
        sections = parse_collision_sections(tag102(1.25, 2.5) + residual, base_offset=32)
        self.assertEqual(sections.tag_ids, (102,))
        self.assertEqual(sections.cylinder.value_0, 1.25)
        self.assertEqual(sections.cylinder.value_1, 2.5)
        self.assertEqual(sections.unparsed_offset, 44)
        self.assertEqual(sections.unparsed_data, residual)

    def test_tag100_is_distinguished_and_preserved_without_guessed_length(self):
        encoded = struct.pack("<I", 100) + b"bsp-payload-length-is-unresolved"
        sections = parse_collision_sections(encoded, base_offset=0x200)
        self.assertEqual(sections.tag_ids, (100,))
        self.assertEqual(sections.bsp.tag_offset, 0x200)
        self.assertEqual(sections.bsp.raw, encoded)
        self.assertEqual(sections.bsp.status, "raw-length-unresolved")
        self.assertEqual(sections.unparsed_data, b"")


if __name__ == "__main__":
    unittest.main()
