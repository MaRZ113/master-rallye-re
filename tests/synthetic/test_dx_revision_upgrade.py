from __future__ import annotations

import struct
import unittest

from master_rallye.demo_dx import inspect_demo_dx
from master_rallye.dx import parse_dx_bytes
from master_rallye.dx_revision_upgrade import (
    DxRevisionUpgradeError,
    upgrade_dx_131_to_135,
    upgrade_dx_131_to_135_with_report,
    validate_existing_rev135,
    validate_generated_rev135,
)
from master_rallye.errors import BoundsError, FormatError


def _strings(values: tuple[bytes, ...]) -> bytes:
    data = bytearray()
    for value in values:
        data += struct.pack("<I", len(value)) + value
    data += struct.pack("<I", 0)
    return bytes(data)


def _rev131_fixture() -> bytes:
    positions = (
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        (2.0, 0.0, 0.0), (3.0, 0.0, 0.0), (2.0, 1.0, 0.0),
    )
    local_indices = (0, 1, 2, 0, 1, 2)
    data = bytearray(struct.pack("<4I", 0xD00D, 131, 1337, len(positions)))
    for point in positions:
        data += struct.pack("<3f", *point)
    for _ in positions:
        data += struct.pack("<3f", 0.0, 0.0, 1.0)
    data += bytes((10, 20, 30, 255)) * len(positions)
    data += struct.pack("<I", 1)
    for uv in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0),
               (0.0, 0.0), (1.0, 0.0), (0.0, 1.0)):
        data += struct.pack("<2f", *uv)
    data += struct.pack("<I", len(local_indices))
    data += struct.pack("<6H", *local_indices)
    data += struct.pack("<2I", 1, 2)

    records = (
        (0, 2, 0, (0x11, 0x22, 0x33), 7),
        (3, 2, 3, (0xA1, 0xB2, 0xC3), 5),
    )
    for vertex_base, vertex_max, index_start, flags, x_value in records:
        data += struct.pack("<5I", 2, vertex_base, vertex_max, index_start, 3)
        data += bytes(flags) + struct.pack("<II", x_value, 3)
        data += _strings((b"body-tga", b"normal-tga", b"Null"))

    data += struct.pack("<2I", 1, len(local_indices))
    data += struct.pack("<6I", 1, 0, 2, 4, 3, 5)
    return bytes(data)


def _rev131_two_triangle_fixture() -> bytes:
    positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                 (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
    indices = (0, 1, 2, 1, 3, 2)
    data = bytearray(struct.pack("<4I", 0xD00D, 131, 1337, 4))
    for point in positions:
        data += struct.pack("<3f", *point)
    for _ in positions:
        data += struct.pack("<3f", 0.0, 0.0, 1.0)
    data += bytes((1, 2, 3, 255)) * 4
    data += struct.pack("<I", 1)
    for uv in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)):
        data += struct.pack("<2f", *uv)
    data += struct.pack("<I6H", len(indices), *indices)
    data += struct.pack("<II5I", 1, 1, 2, 0, 3, 0, len(indices))
    data += bytes((0x11, 0x22, 0x33)) + struct.pack("<II", 7, 1)
    data += _strings((b"body",))
    global_indices = (1, 0, 2, 3, 1, 2)
    data += struct.pack("<2I6I", 1, len(indices), *global_indices)
    return bytes(data)


def _index_array_range(data: bytes) -> tuple[int, int]:
    vertex_count = struct.unpack_from("<I", data, 12)[0]
    offset = 16 + vertex_count * 12 * 2 + vertex_count * 4
    uv_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4 + uv_count * vertex_count * 8
    index_count = struct.unpack_from("<I", data, offset)[0]
    return offset + 4, index_count


def _rev135_reordered_fixture() -> bytes:
    source = _rev131_two_triangle_fixture()
    converted = bytearray(upgrade_dx_131_to_135(source, "two-triangle.dx"))
    index_offset, index_count = _index_array_range(converted)
    assert index_count == 6
    values = struct.unpack_from("<6H", converted, index_offset)
    reordered = values[3:6] + values[0:3]
    struct.pack_into("<6H", converted, index_offset, *reordered)
    return bytes(converted)


class DxRevisionUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.source = _rev131_fixture()
        self.candidate = upgrade_dx_131_to_135(self.source, "synthetic-rev131.dx")
        self.parsed = parse_dx_bytes(self.candidate, "synthetic-candidate.dx")

    def test_revision_and_inserted_prefix_constants(self):
        self.assertEqual(self.parsed.word_0x04, 135)
        draws = [draw for group in self.parsed.draw_groups for draw in group.root.flattened()]
        self.assertEqual(len(draws), 2)
        expected = ((bytes.fromhex("11 00 22 33"), 7),
                    (bytes.fromhex("a1 00 b2 c3"), 5))
        for draw, (flags, x_value) in zip(draws, expected):
            prefix = self.candidate[draw.core_offset + 20:draw.core_offset + 44]
            constant_a, constant_b, scalar, actual_flags, actual_x, slot_count = struct.unpack(
                "<IIf4sII", prefix
            )
            self.assertEqual((constant_a, constant_b, scalar), (1, 0, 1.0))
            self.assertEqual(actual_flags, flags)
            self.assertEqual(actual_x, x_value)
            self.assertEqual(slot_count, 3)

    def test_texture_suffix_and_slot_count_are_preserved(self):
        draws = [draw for group in self.parsed.draw_groups for draw in group.root.flattened()]
        for draw in draws:
            self.assertEqual([slot.value for slot in draw.texture_slots],
                             ["body-tga", "normal-tga", "Null"])

    def test_shared_cores_and_raw_texture_suffixes_are_byte_identical(self):
        source_view = inspect_demo_dx(self.source)
        source_cursor = 8
        draws = [draw for group in self.parsed.draw_groups for draw in group.root.flattened()]
        for draw in draws:
            source_core = self.source[source_view.draw_offset + source_cursor:
                                      source_view.draw_offset + source_cursor + 20]
            self.assertEqual(source_core,
                             self.candidate[draw.core_offset:draw.core_offset + 20])
            source_prefix_end = source_view.draw_offset + source_cursor + 31
            source_suffix_end = source_prefix_end
            for _ in range(3):
                source_suffix_end += 4 + struct.unpack_from(
                    "<I", self.source, source_suffix_end
                )[0]
            source_suffix_end += 4
            self.assertEqual(
                self.source[source_prefix_end:source_suffix_end],
                self.candidate[draw.core_offset + 44:draw.offset + draw.size],
            )
            source_cursor += source_suffix_end - (source_view.draw_offset + source_cursor)
        self.assertEqual(source_cursor, len(source_view.draw_raw))

    def test_local_and_global_indices_and_non_draw_bytes_are_preserved(self):
        source_view = inspect_demo_dx(self.source)
        self.assertEqual(self.parsed.local_indices, source_view.local_indices)
        self.assertEqual(self.parsed.global_index_table.indices,
                         source_view.global_indices)
        self.assertTrue(self.parsed.diagnostics.reconstructed_global_match)

        before_draw = source_view.draw_offset
        self.assertEqual(self.candidate[:4], self.source[:4])
        self.assertEqual(self.candidate[8:before_draw], self.source[8:before_draw])
        self.assertEqual(self.candidate[before_draw:before_draw + 4], struct.pack("<I", 1))
        self.assertEqual(self.candidate[before_draw + 4:before_draw + 8], struct.pack("<I", 2))

        source_global = self.source[source_view.global_offset:]
        candidate_global_start = self.parsed.global_index_table.preamble_offset
        self.assertEqual(self.candidate[candidate_global_start:], source_global)

    def test_canonical_parser_accepts_candidate_without_diagnostics(self):
        self.assertEqual(self.parsed.diagnostics.errors, [])
        self.assertEqual(self.parsed.diagnostics.warnings, [])
        self.assertEqual(tuple(self.parsed.collision.errors), ())
        self.assertEqual(tuple(self.parsed.collision.warnings), ())

    def test_output_is_deterministic(self):
        self.assertEqual(self.candidate, upgrade_dx_131_to_135(self.source))

    def test_structured_report_proves_preservation_and_scopes_runtime_evidence(self):
        candidate, report = upgrade_dx_131_to_135_with_report(self.source, "fixture/car.dx")
        self.assertEqual(candidate, self.candidate)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["source_revision"], 131)
        self.assertEqual(report["output_revision"], 135)
        self.assertEqual(report["draw_records_transformed"], 2)
        self.assertEqual(report["draw_record_size_growth_bytes"], 26)
        self.assertTrue(all(report["preservation_checks"].values()))
        self.assertEqual(report["evidence_profile"], "STATICALLY_SUPPORTED")
        self.assertEqual(
            report["runtime_evidence"]["individual_output_runtime_status"],
            "NOT_ASSESSED_BY_CONVERTER",
        )

    def test_already_135_input_is_rejected_explicitly(self):
        source = bytearray(self.source)
        struct.pack_into("<I", source, 4, 135)
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            upgrade_dx_131_to_135(bytes(source))
        self.assertEqual(caught.exception.code, "already_revision_135")

    def test_unsupported_revision_is_rejected_explicitly(self):
        source = bytearray(self.source)
        struct.pack_into("<I", source, 4, 129)
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            upgrade_dx_131_to_135(bytes(source))
        self.assertEqual(caught.exception.code, "unsupported_revision")

    def test_unsupported_draw_variant_fails_closed(self):
        view = inspect_demo_dx(self.source)
        source = bytearray(self.source)
        struct.pack_into("<I", source, view.draw_offset + 8, 7)
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            upgrade_dx_131_to_135(bytes(source))
        self.assertEqual(caught.exception.code, "unsupported_draw_record")

    def test_impossible_texture_slot_count_fails_closed(self):
        view = inspect_demo_dx(self.source)
        source = bytearray(self.source)
        # envelope + 20-byte core + 3 flag bytes + u32 X
        struct.pack_into("<I", source, view.draw_offset + 8 + 20 + 7, 33)
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            upgrade_dx_131_to_135(bytes(source))
        self.assertEqual(caught.exception.code, "invalid_texture_slot_count")

    def test_non_131_input_is_rejected(self):
        source = bytearray(self.source)
        struct.pack_into("<I", source, 4, 135)
        with self.assertRaises(FormatError):
            upgrade_dx_131_to_135(bytes(source))

    def test_truncated_source_is_rejected(self):
        with self.assertRaises((BoundsError, FormatError)):
            upgrade_dx_131_to_135(self.source[:-1])

    def test_generated_rev135_requires_exact_global_index_order(self):
        generated = upgrade_dx_131_to_135(_rev131_two_triangle_fixture())
        report = validate_generated_rev135(generated, "generated.dx")
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["global_index_validation"]["sequence_equal"])

        reordered = _rev135_reordered_fixture()
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            validate_generated_rev135(reordered, "edited-generated.dx")
        self.assertEqual(caught.exception.code, "generated_global_index_mismatch")

    def test_existing_rev135_accepts_known_triangle_order_divergence(self):
        reordered = _rev135_reordered_fixture()
        report = validate_existing_rev135(reordered, "official-style.dx")
        self.assertEqual(report["status"], "VALID_WITH_ORDERING_DIVERGENCE")
        self.assertTrue(report["global_index_validation"]["oriented_triangle_sets_equal_per_draw"])
        self.assertFalse(report["global_index_validation"]["sequence_equal"])

    def test_existing_rev135_rejects_out_of_range_local_index(self):
        data = bytearray(_rev135_reordered_fixture())
        index_offset, _ = _index_array_range(data)
        struct.pack_into("<H", data, index_offset, 4)
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            validate_existing_rev135(bytes(data), "bad-index.dx")
        self.assertIn(caught.exception.code, {"draw_local_index_out_of_range", "unexpected_parser_errors"})

    def test_existing_rev135_rejects_changed_triangle_topology(self):
        data = bytearray(_rev135_reordered_fixture())
        index_offset, _ = _index_array_range(data)
        # Keep the value in range while changing the oriented triangle set.
        struct.pack_into("<H", data, index_offset, 0)
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            validate_existing_rev135(bytes(data), "changed-topology.dx")
        self.assertEqual(caught.exception.code, "global_index_topology_mismatch")

    def test_existing_rev135_rejects_truncation_and_malformed_draw_table(self):
        valid = _rev135_reordered_fixture()
        with self.assertRaises(DxRevisionUpgradeError):
            validate_existing_rev135(valid[:-1], "truncated.dx")

        source_view = inspect_demo_dx(_rev131_two_triangle_fixture())
        generated = bytearray(upgrade_dx_131_to_135(_rev131_two_triangle_fixture()))
        # A declared root count mismatch is a parser warning and is not accepted.
        struct.pack_into("<I", generated, source_view.draw_offset + 4, 2)
        with self.assertRaises(DxRevisionUpgradeError) as caught:
            validate_existing_rev135(bytes(generated), "bad-draw-table.dx")
        self.assertIn(caught.exception.code, {"empty_draw_table", "parser_warnings"})


if __name__ == "__main__":
    unittest.main()
