from __future__ import annotations

import hashlib
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
for item in (ROOT, ROOT / "src", ROOT / "tools"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

import r5t_f21_prepare as f21
from master_rallye.course_tag100 import parse_course_tag100_bytes
from master_rallye.course_tag1400 import parse_course_tag1400_bytes
from master_rallye.errors import FormatError


def _tag100_root(extra_sibling=False):
    node = struct.pack("<2I4B", 0, 0, 0, 0, 0, 0)
    if not extra_sibling:
        return struct.pack("<I5I", 100, 0, 0, 0, 0, 0) + node
    # The root's sibling flag plus selector introduces a second top-level record.
    first = struct.pack("<2I4B", 0, 0, 0, 0, 0, 1) + struct.pack("<B", 1)
    second = struct.pack("<2I4B", 0, 0, 0, 0, 0, 0)
    return struct.pack("<I5I", 100, 0, 1, 0, 1, 0) + first + second


def _tag1400_record(value=1.0):
    prefix = [0.0] * 9
    prefix[1] = value
    return struct.pack("<IfII3f3f", 1400, 1.0, 1, 1, *(0.0,) * 6) + struct.pack("<I", 0) + struct.pack("<I", 1) + struct.pack("<I", 1) + b"x" + struct.pack("<I", 1) + struct.pack("<9fI4f", *prefix, 0, *(0.0,) * 4)


class R5TF21ToolingTests(unittest.TestCase):
    def test_suffix_decomposes_exactly_into_tree_tag1339_tag1400_and_later(self):
        tree = _tag100_root()
        section_1339 = struct.pack("<I10f", 1339, *(0.0,) * 10)
        section_1400 = _tag1400_record()
        later = struct.pack("<I", 1500) + b"opaque"
        suffix = tree + section_1339 + section_1400 + later
        actual_t, actual_s, actual_u, actual_r, parsed_tree, parsed_1400 = f21.split_tag100_suffix(suffix)
        self.assertEqual((actual_t, actual_s, actual_u, actual_r), (tree, section_1339, section_1400, later))
        self.assertEqual(parsed_tree.consumed_size, len(tree))
        self.assertEqual(parsed_1400.consumed_size, len(section_1400))

    def test_mismatched_tree_hybrid_keeps_other_region_donors_exact(self):
        prefix = b"P0"
        tree0 = _tag100_root()
        tree1 = _tag100_root(extra_sibling=True)
        tag1339 = struct.pack("<I10f", 1339, *(0.0,) * 10)
        tag1400 = _tag1400_record()
        later = struct.pack("<I", 1500) + b"x"
        composed = f21._compose_regions(prefix, tree1, tag1339, tag1400, later)
        self.assertEqual(len(composed), len(prefix) + len(tree1) + len(tag1339) + len(tag1400) + len(later))
        self.assertNotEqual(len(tree0), len(tree1))
        self.assertEqual(len(tag1400), len(_tag1400_record(2.0)))
        actual = {"P": prefix, "T": tree1, "S": tag1339, "U": tag1400, "R": later}
        provenance = f21._verify_region_donors(actual, actual.copy())
        self.assertTrue(all(item["matches_donor_byte_exact"] for item in provenance.values()))

    def test_refuses_wrong_region_hash_or_donor_bytes(self):
        raw = b"expected"
        with self.assertRaises(FormatError):
            f21._verify_sha(raw, hashlib.sha256(b"other").hexdigest(), "synthetic T")
        with self.assertRaisesRegex(FormatError, "designated donor"):
            f21._verify_region_donors({"T": b"bad"}, {"T": b"good"})

    def test_typed_tag1400_differential_maps_record_field_and_offsets(self):
        base_bytes = _tag1400_record(1.0)
        modified_bytes = _tag1400_record(2.0)
        tree_bytes = _tag100_root()
        tree = parse_course_tag100_bytes(tree_bytes)
        base_1400 = parse_course_tag1400_bytes(base_bytes)
        mod_1400 = parse_course_tag1400_bytes(modified_bytes)
        base = SimpleNamespace(
            sections={"T": tree_bytes, "U": base_bytes}, ranges={"U": (1000, 1000 + len(base_bytes))},
            tag1400=base_1400, tree=tree,
        )
        mod = SimpleNamespace(
            sections={"T": tree_bytes, "U": modified_bytes}, ranges={"U": (2000, 2000 + len(modified_bytes))},
            tag1400=mod_1400, tree=tree,
        )
        diff = f21._typed_tag1400_diff(base, mod)
        field = next(item for item in diff["typed_changed_fields"] if item["path"] == "record56[0].float_prefix[1]")
        self.assertEqual(field["baseline_value"], 1.0)
        self.assertEqual(field["modified_value"], 2.0)
        self.assertEqual(field["delta"], 1.0)
        self.assertEqual(field["baseline_file_offset"], 1000 + base_1400.records[0].offset + 4)
        self.assertTrue(diff["all_changed_bytes_typed"])
        self.assertEqual(diff["family_change_counts"], {"record56": 1})


if __name__ == "__main__":
    unittest.main()
