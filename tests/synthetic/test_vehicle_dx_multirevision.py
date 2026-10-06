from __future__ import annotations

import struct
import unittest

from master_rallye.dx import MAGIC, analyze_global_index_consistency, parse_dx_bytes
from master_rallye.errors import FormatError


def _positions(count):
    return [(float(index), float(index % 2), 0.0) for index in range(count)]


def _global_sequence(local_indices, draws):
    values = [None] * len(local_indices)
    for vertex_base, _local_max, start, count in draws:
        for relative in range(0, count, 3):
            local = local_indices[start + relative:start + relative + 3]
            tri = (local[1] + vertex_base, local[0] + vertex_base, local[2] + vertex_base)
            values[start + relative:start + relative + 3] = tri
    return values


def _legacy_record(vertex_base, local_max, index_start, index_count, slots=("body-tga",)):
    prefix = bytes((7, 8, 9)) + struct.pack("<II", 3, len(slots))
    texture_bytes = b"".join(
        struct.pack("<I", len(value.encode("ascii"))) + value.encode("ascii")
        for value in slots
    )
    return (
        struct.pack("<5I", 2, vertex_base, local_max, index_start, index_count)
        + prefix
        + texture_bytes
        + struct.pack("<I", 0)
    )


def _revision135_record(vertex_base, local_max, index_start, index_count, slots=("body-tga",)):
    core = struct.pack(
        "<5I2If4sI",
        2,
        vertex_base,
        local_max,
        index_start,
        index_count,
        1,
        0,
        1.0,
        bytes((1, 0, 1, 1)),
        3,
    )
    texture_bytes = b"".join(
        struct.pack("<I", len(value.encode("ascii"))) + value.encode("ascii")
        for value in slots
    )
    return core + struct.pack("<I", len(slots)) + texture_bytes + struct.pack("<I", 0)


def _fixture(revision, local_indices, draws, stored=None):
    vertex_count = max(6, max((base + local_max + 1 for base, local_max, _, _ in draws), default=0))
    blob = bytearray(struct.pack("<4I", MAGIC, revision, 1337, vertex_count))
    for position in _positions(vertex_count):
        blob.extend(struct.pack("<3f", *position))
    blob.extend(bytes(vertex_count * 12))
    blob.extend(bytes((255, 255, 255, 255)) * vertex_count)
    blob.extend(struct.pack("<I", 1))
    for index in range(vertex_count):
        blob.extend(struct.pack("<2f", index / 8.0, index / 16.0))
    blob.extend(struct.pack("<I", len(local_indices)))
    for index in local_indices:
        blob.extend(struct.pack("<H", index))

    blob.extend(struct.pack("<II", 1, len(draws)))
    for vertex_base, local_max, start, count in draws:
        if revision in (127, 131):
            blob.extend(_legacy_record(vertex_base, local_max, start, count))
        else:
            blob.extend(_revision135_record(vertex_base, local_max, start, count))

    values = _global_sequence(local_indices, draws) if stored is None else stored
    blob.extend(struct.pack("<II", 1, len(values)))
    for value in values:
        blob.extend(struct.pack("<I", value if value is not None else 0))
    return bytes(blob)


class MultiRevisionVehicleDxTests(unittest.TestCase):
    def test_exact_sequence_is_generated_valid(self):
        data = _fixture(135, [0, 1, 2, 3, 4, 5], [(0, 5, 0, 6)])
        model = parse_dx_bytes(data, "exact.dx")
        report = analyze_global_index_consistency(model)
        self.assertTrue(report["exact_generated_valid"])
        self.assertTrue(report["structural_import_valid"])
        self.assertEqual(report["validation_profile"], "EXACT")
        self.assertTrue(model.diagnostics.validated)

    def test_reordered_triangles_are_import_valid_but_not_writer_valid(self):
        stored = [4, 3, 5, 1, 0, 2]
        model = parse_dx_bytes(
            _fixture(135, [0, 1, 2, 3, 4, 5], [(0, 5, 0, 6)], stored),
            "reordered.dx",
        )
        report = analyze_global_index_consistency(model)
        self.assertFalse(report["exact_generated_valid"])
        self.assertFalse(model.diagnostics.validated)
        self.assertTrue(report["structural_import_valid"])
        self.assertTrue(report["oriented_triangle_sets_equal_per_draw"])
        self.assertEqual(report["validation_profile"], "VALID_WITH_INDEX_ORDERING_DIVERGENCE")
        self.assertEqual(report["mismatch_position_count"], 6)
        self.assertEqual(report["first_mismatch_position"], 0)
        self.assertIn("per-draw oriented triangle topology is equivalent", model.diagnostics.warnings[0])

    def test_cyclic_corner_rotation_is_equivalent(self):
        stored = [0, 2, 1, 3, 5, 4]
        model = parse_dx_bytes(
            _fixture(135, [0, 1, 2, 3, 4, 5], [(0, 5, 0, 6)], stored)
        )
        self.assertTrue(model.diagnostics.import_validated)
        self.assertTrue(model.diagnostics.oriented_triangle_sets_equal_per_draw)
        self.assertFalse(model.diagnostics.index_sequence_equal)

    def test_reversed_winding_is_rejected(self):
        stored = [1, 2, 0, 4, 5, 3]
        model = parse_dx_bytes(
            _fixture(135, [0, 1, 2, 3, 4, 5], [(0, 5, 0, 6)], stored)
        )
        self.assertFalse(model.diagnostics.import_validated)
        self.assertFalse(model.diagnostics.oriented_triangle_sets_equal_per_draw)
        self.assertTrue(any("topology differs" in error for error in model.diagnostics.errors))

    def test_missing_triangle_coverage_is_rejected(self):
        model = parse_dx_bytes(
            _fixture(135, [0, 1, 2, 3, 4, 5], [(0, 5, 0, 3)])
        )
        self.assertFalse(model.diagnostics.import_validated)
        self.assertEqual(model.diagnostics.index_coverage, "gaps")
        self.assertEqual(model.diagnostics.uncovered_index_count, 3)

    def test_missing_triangle_in_stored_topology_is_rejected(self):
        local = [0, 1, 2, 0, 1, 2, 3, 4, 5]
        stored = [1, 0, 2, 4, 3, 5, 4, 3, 5]
        model = parse_dx_bytes(
            _fixture(135, local, [(0, 5, 0, 9)], stored)
        )
        self.assertFalse(model.diagnostics.import_validated)
        self.assertFalse(model.diagnostics.oriented_triangle_sets_equal_per_draw)

    def test_duplicate_extra_triangle_is_rejected(self):
        local = [0, 1, 2, 0, 1, 2, 3, 4, 5]
        stored = [1, 0, 2, 1, 0, 2, 1, 0, 2]
        model = parse_dx_bytes(
            _fixture(135, local, [(0, 5, 0, 9)], stored)
        )
        self.assertFalse(model.diagnostics.import_validated)
        self.assertFalse(model.diagnostics.oriented_triangle_sets_equal_per_draw)

    def test_conflicting_overlapping_draw_ownership_is_rejected(self):
        local = [0, 1, 2, 0, 1, 2]
        draws = [(0, 2, 0, 3), (1, 2, 0, 3)]
        model = parse_dx_bytes(_fixture(135, local, draws, [1, 0, 2, 1, 0, 2]))
        self.assertFalse(model.diagnostics.import_validated)
        self.assertGreater(model.diagnostics.overlapping_index_count, 0)
        self.assertTrue(any("conflicting vertices" in error for error in model.diagnostics.errors))

    def test_exact_sequence_fact_is_separate_from_invalid_draw_coverage(self):
        local = [0, 1, 2, 3, 4, 5]
        draws = [(0, 5, 0, 6), (0, 2, 0, 3)]
        model = parse_dx_bytes(_fixture(135, local, draws))
        self.assertTrue(model.diagnostics.index_sequence_equal)
        self.assertTrue(model.global_index_table.reconstructed_match)
        self.assertFalse(model.diagnostics.import_validated)
        self.assertFalse(model.diagnostics.exact_generated_valid)
        self.assertFalse(model.diagnostics.validated)
        self.assertEqual(model.diagnostics.index_coverage, "overlap")

    def test_revision127_and_131_have_direct_read_models_and_no_writer_support(self):
        for revision in (127, 131):
            with self.subTest(revision=revision):
                model = parse_dx_bytes(
                    _fixture(revision, [0, 1, 2], [(0, 2, 0, 3)]),
                    f"rev{revision}.dx",
                )
                self.assertEqual(model.dx_revision, revision)
                self.assertEqual(model.vertex_count, 6)
                self.assertEqual(len(model.physical_draws), 1)
                self.assertEqual(model.physical_draws[0].texture_tuple, ("body-tga",))
                self.assertEqual(len(model.physical_draws[0].raw_revision_prefix), 11)
                self.assertEqual(
                    model.physical_draws[0].material_semantics,
                    "LEGACY_RAW_UNINTERPRETED",
                )
                self.assertTrue(model.diagnostics.import_validated)
                self.assertTrue(model.diagnostics.index_sequence_equal)
                self.assertFalse(model.diagnostics.writer_revision_supported)
                self.assertFalse(model.diagnostics.validated)

    def test_unsupported_revision_fails_closed(self):
        data = bytearray(_fixture(135, [0, 1, 2], [(0, 2, 0, 3)]))
        struct.pack_into("<I", data, 4, 125)
        with self.assertRaisesRegex(FormatError, "unsupported vehicle DX revision 125"):
            parse_dx_bytes(bytes(data), "unsupported.dx")


if __name__ == "__main__":
    unittest.main()
