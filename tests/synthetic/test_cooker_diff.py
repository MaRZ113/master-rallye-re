from __future__ import annotations

import struct
import unittest

from master_rallye.cooker_diff import compare_cooker_dx


POSITIONS = (
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (1.0, 1.0, 0.0),
)
OLD_INDICES = (0, 1, 2, 1, 2, 3)
NEW_INDICES = (1, 2, 3, 0, 1, 2)
STORED_GLOBAL = (1, 0, 2, 2, 1, 3)
TEXTURES = ("body-tga", "glass-tga", "Null")


def _texture_payload() -> bytes:
    data = bytearray()
    for value in TEXTURES:
        raw = value.encode("ascii")
        data += struct.pack("<I", len(raw)) + raw
    data += struct.pack("<I", 0)
    return bytes(data)


def make_pair_member(revision: int, *, changed_position: bool = False) -> bytes:
    indices = OLD_INDICES if revision == 131 else NEW_INDICES
    positions = list(POSITIONS)
    if changed_position:
        positions[0] = (0.25, 0.0, 0.0)
    data = bytearray(struct.pack("<4I", 0xD00D, revision, 1337, len(positions)))
    for point in positions:
        data += struct.pack("<3f", *point)
    for _ in positions:
        data += struct.pack("<3f", 0.0, 0.0, 1.0)
    data += bytes((10, 20, 30, 255)) * len(positions)
    uv = ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0))
    data += struct.pack("<I", 1)
    for pair in uv:
        data += struct.pack("<2f", *pair)
    data += struct.pack("<I", len(indices))
    data += struct.pack(f"<{len(indices)}H", *indices)
    data += struct.pack("<2I", 1, 1)
    core = struct.pack("<5I", 2, 0, 3, 0, 6)
    if revision == 131:
        # The eleven-byte region is intentionally treated as opaque legacy data.
        record = core + bytes.fromhex("00 01 01 03 00 00 00 03 00 00 00")
    else:
        record = core + struct.pack("<II f 4s I", 1, 0, 1.0, bytes.fromhex("00000101"), 7)
        record += struct.pack("<I", len(TEXTURES))
    record += _texture_payload()
    data += record
    data += struct.pack("<2I", 1, len(STORED_GLOBAL))
    data += struct.pack(f"<{len(STORED_GLOBAL)}I", *STORED_GLOBAL)
    return bytes(data)


class CookerDiffTests(unittest.TestCase):
    def setUp(self):
        self.rev131 = make_pair_member(131)
        self.rev135 = make_pair_member(135)

    def compare(self, first=None, second=None, hashes=("a" * 64, "a" * 64)):
        return compare_cooker_dx(
            self.rev131 if first is None else first,
            self.rev135 if second is None else second,
            first_source="synthetic-rev131",
            second_source="synthetic-rev135",
            source_hashes=hashes,
        )

    def test_same_source_geometry_and_material_suffix_survive_record_growth(self):
        report = self.compare()
        self.assertEqual(report["source_identity"]["status"], "CONFIRMED_BY_BYTES")
        self.assertEqual(report["geometry_equivalence"]["classification"], "EQUIVALENT_AFTER_REMAP")
        self.assertTrue(report["geometry_equivalence"]["positions_exact"])
        self.assertTrue(report["geometry_equivalence"]["uv_exact"])
        self.assertEqual(report["draws"]["per_record_size_delta"], 13)
        self.assertEqual(report["draws"]["legacy_prefix_size"], 11)
        self.assertEqual(report["draws"]["rev135_prefix_size"], 24)
        self.assertEqual(report["draws"]["topology_status"], "EQUAL")
        self.assertEqual(report["draws"]["material_reference_status"], "EQUAL")
        self.assertEqual(len(report["draws"]["records"][0]["rev135_parsed_prefix"]), 48)
        self.assertGreater(len(report["draws"]["records"][0]["legacy_opaque_prefix_byte_differences"]), 0)
        self.assertEqual(len(report["local_indices"]["changed_value_indices"]), 6)
        self.assertTrue(report["draws"]["all_texture_reference_suffixes_identical"])
        self.assertTrue(report["draws"]["all_per_draw_oriented_triangle_multisets_equal"])
        self.assertTrue(report["normalized_byte_accounting"]["all_changed_content_accounted"])
        self.assertEqual(report["draws"]["records"][0]["old_triangle_index_to_new_triangle_index"], [1, 0])

    def test_report_keeps_source_mismatch_explicit(self):
        report = self.compare(hashes=("a" * 64, "b" * 64))
        self.assertEqual(report["source_identity"]["status"], "DIFFERENT_SOURCE_CONTENT")
        self.assertFalse(report["source_identity"]["equal"])

    def test_attribute_change_is_not_hidden_by_index_permutation(self):
        report = self.compare(second=make_pair_member(135, changed_position=True))
        self.assertEqual(report["geometry_equivalence"]["classification"], "DIFFERENT")
        self.assertFalse(report["geometry_equivalence"]["positions_exact"])

    def test_material_reference_change_is_separate_from_topology(self):
        changed = bytearray(self.rev135)
        changed[changed.index(b"glass-tga")] = ord("G")
        report = self.compare(second=bytes(changed))
        self.assertEqual(report["geometry_equivalence"]["classification"], "EQUIVALENT_AFTER_REMAP")
        self.assertEqual(report["draws"]["topology_status"], "EQUAL")
        self.assertEqual(report["draws"]["material_reference_status"], "DIFFERENT")

    def test_topology_change_is_not_hidden_by_unchanged_global_table(self):
        changed = bytearray(self.rev135)
        local_index_offset = 16 + 4 * 12 + 4 * 12 + 4 * 4 + 4 + 4 * 8 + 4
        struct.pack_into("<H", changed, local_index_offset, 2)
        report = self.compare(second=bytes(changed))
        self.assertEqual(report["geometry_equivalence"]["classification"], "DIFFERENT")
        self.assertEqual(report["draws"]["topology_status"], "DIFFERENT")

    def test_rejects_unexpected_revision_order(self):
        with self.assertRaises(ValueError):
            compare_cooker_dx(self.rev135, self.rev131)


if __name__ == "__main__":
    unittest.main()
