from __future__ import annotations

import math
import struct
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.collision import parse_collision_sections
from master_rallye.collision_writer import (
    patch_dx_collision_translation,
    replace_dx_tag101,
    serialize_tag101,
    translate_tag101,
)
from master_rallye.dx import MAGIC, parse_dx_bytes
from master_rallye.dx_writer import audit_binary_diff
from master_rallye.errors import BoundsError, CollisionWriteError
from tests.helpers.collision_fixture import tag101, tag102


def synthetic_dx(trailing: bytes) -> bytes:
    positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    blob = bytearray(struct.pack("<4I", MAGIC, 135, 1337, 3))
    for value in positions:
        blob += struct.pack("<3f", *value)
    for _ in positions:
        blob += struct.pack("<3f", 0.0, 0.0, 1.0)
    blob += bytes((255, 255, 255, 255)) * 3
    blob += struct.pack("<I", 0)
    blob += struct.pack("<I3H", 3, 0, 1, 2)
    record = bytearray(
        struct.pack("<7If4BI", 2, 0, 2, 0, 3, 0, 0, 1.0, 0, 0, 0, 0, 0)
    )
    record += struct.pack("<2I", 0, 0)
    blob += struct.pack("<2I", 1, 1) + record
    blob += struct.pack("<2I3I", 1, 3, 1, 0, 2)
    blob += trailing
    return bytes(blob)


def distance(left, right):
    return math.sqrt(sum((left[index] - right[index]) ** 2 for index in range(3)))


class CollisionWriterTests(unittest.TestCase):
    def setUp(self):
        self.trailing = tag101(suffix=tag102() + struct.pack("<I", 1339) + b"R" * 40)
        self.template = synthetic_dx(self.trailing)
        self.model = parse_dx_bytes(self.template)
        self.hull = self.model.collision.convex_hull

    def test_tag101_and_full_dx_zero_edit_are_byte_identical(self):
        encoded = serialize_tag101(self.hull)
        self.assertEqual(encoded, self.hull.raw)
        rebuilt = replace_dx_tag101(self.template, encoded)
        self.assertEqual(rebuilt, self.template)
        translated_zero = patch_dx_collision_translation(
            self.template, (0.0, 0.0, 0.0)
        )
        self.assertTrue(translated_zero.byte_identical)
        self.assertEqual(translated_zero.diff.changed_byte_count, 0)

    def test_translation_moves_only_proven_geometry_vertices(self):
        delta = (0.25, -0.125, 0.5)
        result = translate_tag101(self.hull, *delta)
        self.assertTrue(result.diff.valid)
        self.assertGreater(result.diff.changed_byte_count, 0)
        self.assertEqual(result.validation["status"], "PASS")
        self.assertTrue(result.validation["base_radius_unchanged"])
        self.assertTrue(result.validation["topology_unchanged"])
        self.assertTrue(result.validation["adjacency_unchanged"])
        self.assertLess(result.validation["maximum_face_area_error"], 2e-5)
        self.assertLess(result.validation["maximum_pairwise_distance_error"], 2e-5)
        self.assertLess(result.validation["maximum_aabb_shift_error"], 2e-5)
        self.assertEqual(
            struct.pack("<f", result.original.base_scalar),
            struct.pack("<f", result.translated.base_scalar),
        )
        old = result.original.representation_b.geometry_a
        new = result.translated.representation_b.geometry_a
        self.assertEqual(old.triangles, new.triangles)
        self.assertAlmostEqual(distance(old.vertices[0], old.vertices[1]), distance(new.vertices[0], new.vertices[1]), places=5)
        self.assertEqual(result.original.representation_b.edges, result.translated.representation_b.edges)
        self.assertEqual(
            result.original.representation_b.edge_face_adjacency,
            result.translated.representation_b.edge_face_adjacency,
        )

    def test_full_dx_translation_preserves_visual_and_other_collision_bytes(self):
        result = patch_dx_collision_translation(self.template, (0.25, 0.0, 0.0))
        before = result.original_model
        after = result.output_model
        self.assertEqual(before.vertices, after.vertices)
        self.assertEqual(before.local_indices, after.local_indices)
        self.assertEqual(before.physical_draws, after.physical_draws)
        self.assertEqual(before.global_index_table, after.global_index_table)
        self.assertEqual(before.collision.cylinder.raw, after.collision.cylinder.raw)
        self.assertEqual(result.to_dict()["visual_geometry_changed_bytes"], 0)
        self.assertEqual(result.to_dict()["unexpected_diff_count"], 0)
        start = before.collision.convex_hull.tag_offset
        end = before.collision.convex_hull.end_offset
        self.assertEqual(self.template[:start], result.data[:start])
        self.assertEqual(self.template[end:], result.data[end:])

    def test_unexpected_diff_detection(self):
        result = patch_dx_collision_translation(self.template, (0.25, 0.0, 0.0))
        corrupted = bytearray(result.data)
        corrupted[0] ^= 1
        audit = audit_binary_diff(
            self.template,
            bytes(corrupted),
            [(item.start, item.end) for item in result.diff.allowed_ranges],
        )
        self.assertFalse(audit.valid)
        self.assertTrue(any(item.start == 0 for item in audit.unexpected_ranges))

    def test_truncated_nonfinite_and_invalid_source_are_rejected(self):
        with self.assertRaises(BoundsError):
            patch_dx_collision_translation(
                self.template[:self.hull.end_offset - 1],
                (0.1, 0.0, 0.0),
            )
        with self.assertRaisesRegex(CollisionWriteError, "non-finite"):
            patch_dx_collision_translation(self.template, (float("nan"), 0.0, 0.0))

        bad_point = replace(
            self.hull.representation_b.geometry_b,
            vertices=((9.0, 9.0, 9.0),),
        )
        bad_representation = replace(self.hull.representation_b, geometry_b=bad_point)
        bad_hull = replace(self.hull, representation_b=bad_representation)
        with self.assertRaisesRegex(CollisionWriteError, "vertex mean"):
            translate_tag101(bad_hull, 0.1, 0.0, 0.0)

        invalid_base = replace(
            self.hull.base_geometry,
            triangles=((99, 0, 0),),
        )
        with self.assertRaisesRegex(CollisionWriteError, "structural reparse"):
            serialize_tag101(replace(self.hull, base_geometry=invalid_base))

    def test_structural_zero_edit_preserves_nonfinite_float_bits(self):
        encoded = bytearray(tag101())
        struct.pack_into("<I", encoded, 16, 0x7FC01234)
        hull = parse_collision_sections(bytes(encoded), strict=False).convex_hull
        self.assertEqual(serialize_tag101(hull), bytes(encoded))


if __name__ == "__main__":
    unittest.main()
