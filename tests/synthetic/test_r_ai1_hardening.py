import copy
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import r_ai1_hardening as h
import r_ai1_mixed_class as ai
from test_r_ai1_general import capture


class HardeningTests(unittest.TestCase):
    def test_exact_hash_and_size_reject_unknown_source(self):
        for source in (b"", bytes(ai.RETAIL_SIZE), bytes(ai.RETAIL_SIZE - 1)):
            for profile in ("base", "mixed"):
                with self.assertRaisesRegex(ValueError, "exact pristine"):
                    h.build(source, profile)

    def test_unknown_candidate_and_profile_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown hardening"):
            h.verify(bytes(ai.RETAIL_SIZE))
        with self.assertRaises(ValueError):
            h.ranges_for("arbitrary")

    def test_fail_closed_original_bytes(self):
        source = b"abcdefgh"
        with self.assertRaisesRegex(ValueError, "original bytes"):
            ai.apply_ranges(source, [{"offset": 0, "original": b"X", "replacement": b"Y"}], ai.sha256(source))
        with self.assertRaisesRegex(ValueError, "SHA256"):
            ai.apply_ranges(source, [], "0" * 64)

    def test_loading_failure_redirects_exact_stock_success(self):
        row = next(row for row in h.hardening_ranges() if row["va"] == 0x464F69)
        target = row["va"] + 5 + struct.unpack("<i", row["replacement"][1:])[0]
        self.assertEqual(target, 0x464F46)
        self.assertEqual(row["original"], bytes.fromhex("68841f6b00"))

    def test_native_list_guard_continuations_and_replayed_compare(self):
        code = next(row["replacement"] for row in h.hardening_ranges() if row["va"] == h.STRING_CAVE)
        self.assertEqual(code[:4], bytes.fromhex("85db0f84"))
        self.assertEqual(h.STRING_CAVE + 8 + struct.unpack("<i", code[4:8])[0], 0x602040)
        self.assertEqual(code[8:14], bytes.fromhex("8b7b043b7b08"))
        self.assertEqual(h.STRING_CAVE + 19 + struct.unpack("<i", code[15:19])[0], 0x602024)

    def test_xml_guard_restores_flags_on_both_paths(self):
        code = next(row["replacement"] for row in h.hardening_ranges() if row["va"] == h.XML_CAVE)
        self.assertEqual(code[:5], bytes.fromhex("9c85c00f84"))
        null_offset = 9 + struct.unpack("<i", code[5:9])[0]
        self.assertEqual(null_offset, 22)
        self.assertEqual(code[9:17], bytes.fromhex("9d8b108bc8ff520c"))
        self.assertEqual(code[null_offset], 0x9D)
        self.assertEqual(h.XML_CAVE + 28 + struct.unpack("<i", code[24:28])[0], 0x60218E)

    def test_composition_only_merges_declared_header(self):
        rows = h.ranges_for("mixed")
        self.assertEqual(len(rows), 10)
        chooser = ai.general_ranges()
        for original in chooser:
            row = next(row for row in rows if row["offset"] == original["offset"])
            self.assertEqual(row["original"], original["original"])
            self.assertEqual(row["replacement"], original["replacement"])
        self.assertEqual(len(h.ranges_for("base")), 6)

    def test_non_header_overlap_rejected(self):
        for first in h.hardening_ranges()[1:]:
            incoming = copy.deepcopy(first)
            incoming["offset"] += 1
            with self.assertRaisesRegex(ValueError, "overlap"):
                h.compose_ranges(h.hardening_ranges(), [incoming])

    def test_header_alias_is_not_general_overlap_permission(self):
        incoming = copy.deepcopy(ai.general_ranges()[0])
        incoming["original"] = bytes(4)
        with self.assertRaisesRegex(ValueError, "overlap"):
            h.compose_ranges(h.hardening_ranges(), [incoming])

    def test_header_size_max_and_same_aligned_pages(self):
        small = h.hardening_ranges()[0]
        big = ai.general_ranges()[0]
        for order in (([small], [big]), ([big], [small])):
            size = struct.unpack("<I", h.compose_ranges(*order)[0]["replacement"])[0]
            self.assertEqual(size, struct.unpack("<I", big["replacement"])[0])
            self.assertEqual((size + 4095) // 4096, (ai.ORIGINAL_TEXT_SIZE + 4095) // 4096)

    def test_deterministic_confined_inverse_ranges(self):
        for profile in ("base", "mixed"):
            rows = h.ranges_for(profile)
            source = bytearray(max(row["offset"] + len(row["original"]) for row in rows))
            for row in rows:
                source[row["offset"]:row["offset"] + len(row["original"])] = row["original"]
            source = bytes(source)
            result = ai.apply_ranges(source, rows, ai.sha256(source))
            self.assertEqual(result, ai.apply_ranges(source, h.ranges_for(profile), ai.sha256(source)))
            inverse = [{**row, "original": row["replacement"], "replacement": row["original"]} for row in rows]
            self.assertEqual(ai.apply_ranges(result, inverse, ai.sha256(result)), source)
            protected = ((0x65180, 0x65800), (0x49A50, 0x4A200), (0x584F0, 0x58980),
                         (0x29CEA8, 0x29CEB8), (0x25EC40, 0x25F000))
            for start, end in protected:
                self.assertEqual(result[start:end], source[start:end])

    def test_manifest_captures_semantics_without_binary_payload(self):
        for profile in ("base", "mixed"):
            manifest = h.manifest(profile)
            self.assertFalse(manifest["num_cars_changed"])
            self.assertEqual(manifest["image_size"], ai.RETAIL_SIZE)
            self.assertEqual(manifest["runtime_validation"], "PENDING")
            self.assertEqual(manifest["broker_dump_variant"], "native_hardened")
            self.assertTrue(all("purpose" in row and "original_hex" in row and "replacement_hex" in row
                                for row in manifest["ranges"]))

    def test_hardened_oracle_retains_state_only_limit(self):
        snapshot = capture()
        snapshot["source"].update(image_sha256=h.MIXED_SHA256, build_profile=h.PROFILES["mixed"],
                                  broker_dump_variant="native_hardened")
        report = ai.check_general_snapshot(snapshot, h.MIXED_SHA256)
        self.assertEqual(report["status"], "BROKER_STATE_MATCH_ONLY")
        self.assertFalse(report["runtime_full_pass"])
        self.assertIn("PREPARED", report["post_results_dump"])

    def test_hardened_oracle_rejects_wrong_provenance_and_base(self):
        for fields in ({"image_sha256": h.MIXED_SHA256},
                       {"image_sha256": h.BASE_SHA256},
                       {"image_sha256": h.MIXED_SHA256, "build_profile": h.PROFILES["mixed"],
                        "broker_dump_variant": "pristine"}):
            snapshot = capture()
            snapshot["source"].update(fields)
            with self.assertRaises(ValueError):
                ai.check_general_snapshot(snapshot, fields["image_sha256"])

    def results_fixture(self):
        return {"kind": "master-rallye-broker-dump-snapshot", "schema_version": 1,
                "source": {"image_sha256": h.MIXED_SHA256, "build_profile": h.PROFILES["mixed"],
                           "broker_dump_variant": "native_hardened", "label": "mixed-hardened-results",
                           "freshness": "post_baseline_complete_dump_proven"},
                "entries": [{"path": "Frontend/RaceResults/" + suffix, "type": kind, "value": value}
                            for suffix, kind, value in (("ResultsType", "String", "RACE TIME"),
                                                       ("NameList", "StringList", ['"AI1"']),
                                                       ("TimeList", "StringList", ['"03:10"']),
                                                       ("PointsList", "StringList", []))] +
                           [{"path": "Research/AfterPoints", "type": "Int", "value": 1}]}

    def test_results_oracle_requires_complete_continuation(self):
        snapshot = self.results_fixture()
        result = h.check_results_snapshot(snapshot)
        self.assertEqual(result["following_entries"], 1)
        self.assertFalse(result["runtime_full_pass"])
        self.assertTrue(result["empty_list_does_not_prove_allocated_empty_or_null"])
        snapshot["entries"].pop()
        with self.assertRaisesRegex(ValueError, "after PointsList"):
            h.check_results_snapshot(snapshot)

    def test_results_oracle_rejects_wrong_values_or_ambiguous_paths(self):
        for index, value in ((0, "POINTS"), (1, []), (2, None), (3, ['"10"'])):
            snapshot = self.results_fixture()
            snapshot["entries"][index]["value"] = value
            with self.assertRaises(ValueError):
                h.check_results_snapshot(snapshot)
        snapshot = self.results_fixture()
        snapshot["entries"].append(dict(snapshot["entries"][3]))
        with self.assertRaises(ValueError):
            h.check_results_snapshot(snapshot)

    def test_results_oracle_rejects_old_profile_and_recovered_dump(self):
        for key, value in (("image_sha256", ai.GENERAL_SHA256), ("freshness", "recovery"),
                           ("label", "mixed-random-race-1"), ("broker_dump_variant", "pristine")):
            snapshot = self.results_fixture()
            snapshot["source"][key] = value
            with self.assertRaises(ValueError):
                h.check_results_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
