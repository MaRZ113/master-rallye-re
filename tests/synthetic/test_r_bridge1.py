from __future__ import annotations

import struct
import unittest
from pathlib import Path

from master_rallye.bridge_analysis import (
    audit_bridge_provenance,
    compare_dx_generations,
    validate_bridge_candidate,
)
from master_rallye.demo_dx import inspect_demo_dx
from master_rallye.dx import parse_dx


MASTER_ROOT = Path(r"D:\Game\Master Rallye")
DEMO_841 = MASTER_ROOT / "corpora" / "demo-8.4.1" / "DataGx" / "Vehicles"
DEMO_931 = MASTER_ROOT / "corpora" / "demo-9.3.1" / "DataGx" / "Vehicles"
RETAIL = MASTER_ROOT / "corpora" / "retail" / "Data.sma_unpacked" / "DataGx" / "Vehicles"


@unittest.skipUnless((DEMO_841 / "Jump" / "car.dx").is_file()
                     and (DEMO_931 / "Jump" / "car.dx").is_file()
                     and (RETAIL / "Jump" / "car.dx").is_file(),
                     "requires local read-only vehicle corpus inputs")
class RBridge1CorpusTests(unittest.TestCase):
    def test_jump_corpus_identity_and_build_headers(self):
        expected = ((DEMO_841 / "Jump" / "car.dx", (0xD00D, 127, 1337)),
                    (DEMO_931 / "Jump" / "car.dx", (0xD00D, 131, 1337)),
                    (RETAIL / "Jump" / "car.dx", (0xD00D, 135, 1337)))
        for path, words in expected:
            view = inspect_demo_dx(path.read_bytes(), str(path))
            self.assertEqual(view.header[:3], words)
        self.assertTrue((DEMO_931 / "Jump" / "car.gxm").is_file())
        self.assertFalse((RETAIL / "Jump" / "car.gxm").exists())

    def test_demo931_and_retail_jump_parser_coverage(self):
        demo_path = DEMO_931 / "Jump" / "car.dx"
        retail_path = RETAIL / "Jump" / "car.dx"
        demo_view = inspect_demo_dx(demo_path.read_bytes(), str(demo_path))
        retail_model = parse_dx(retail_path)
        self.assertEqual(len(demo_view.positions), 2361)
        self.assertEqual(len(demo_view.local_indices), 5424)
        self.assertEqual(retail_model.vertex_count, 2401)
        self.assertEqual(len(retail_model.local_indices), 5514)
        self.assertEqual(retail_model.magic, 0xD00D)

    def test_normalized_diff_separates_content_from_parser_format(self):
        result = compare_dx_generations((DEMO_931 / "Jump" / "car.dx").read_bytes(),
                                        (RETAIL / "Jump" / "car.dx").read_bytes(),
                                        demo_source="demo931 Jump/car.dx",
                                        retail_source="retail Jump/car.dx")
        self.assertEqual(result["comparison_status"], "COMPARED")
        self.assertEqual(result["format_assessment"]["classification"],
                         "RETAIL_PARSER_REJECTS_DEMO_LAYOUT")
        self.assertEqual(result["header"]["word_0x08_equal"], True)
        self.assertEqual(result["header"]["word_0x04_equal"], False)
        self.assertFalse(result["render"]["positions"]["same_shape"])
        self.assertFalse(result["render"]["local_indices"]["exact_equal"])
        self.assertFalse(result["render"]["draw_region"]["exact_equal"])
        self.assertEqual(result["collision"]["demo"]["tags"], [101])
        self.assertEqual(result["collision"]["retail"]["tags"], [101])
        self.assertFalse(result["format_assessment"]["runtime_acceptance_proven"])

    def test_static_cached_model_header_gate_distinguishes_demo_and_retail(self):
        old_demo = validate_bridge_candidate((DEMO_841 / "Jump" / "car.dx").read_bytes())
        demo = validate_bridge_candidate((DEMO_931 / "Jump" / "car.dx").read_bytes())
        retail = validate_bridge_candidate((RETAIL / "Jump" / "car.dx").read_bytes())
        self.assertEqual(old_demo["retail_cache_header_gate"]["revision"], 127)
        self.assertFalse(old_demo["retail_cache_header_gate"]["revision_pass"])
        self.assertTrue(demo["retail_cache_header_gate"]["magic_pass"])
        self.assertFalse(demo["retail_cache_header_gate"]["revision_pass"])
        self.assertTrue(retail["retail_cache_header_gate"]["magic_pass"])
        self.assertTrue(retail["retail_cache_header_gate"]["revision_pass"])
        self.assertEqual(demo["status"], "REJECTED_BY_LOCAL_RETAIL_PARSER")
        self.assertEqual(retail["status"], "STRUCTURALLY_VALIDATED_RUNTIME_UNCONFIRMED")
        self.assertFalse(retail["retail_ready"])

    def test_header_revision_patch_alone_does_not_convert_demo_draw_layout(self):
        source = (DEMO_931 / "Jump" / "car.dx").read_bytes()
        patched = bytearray(source)
        struct.pack_into("<I", patched, 4, 135)
        changed = [offset for offset, pair in enumerate(zip(source, patched)) if pair[0] != pair[1]]
        self.assertEqual(changed, [4])
        result = validate_bridge_candidate(bytes(patched), source="in-memory revision-only probe")
        self.assertTrue(result["retail_cache_header_gate"]["revision_pass"])
        self.assertEqual(result["status"], "REJECTED_BY_LOCAL_RETAIL_PARSER")
        self.assertIn("texture slot count", result["retail_parser"]["error"])

    def test_jump_car_collision_core_matches_while_auxiliary_lists_differ(self):
        result = compare_dx_generations((DEMO_931 / "Jump" / "car.dx").read_bytes(),
                                        (RETAIL / "Jump" / "car.dx").read_bytes())
        semantic = result["collision"]["semantic_diff"]["tag101"]
        self.assertTrue(semantic["base_geometry"]["triangles_equal"])
        self.assertEqual(semantic["base_geometry"]["vertices"]["max_abs_delta"], 0.0)
        self.assertEqual(semantic["base_scalar"]["max_abs_delta"], 0.0)
        for representation in ("representation_a", "representation_b"):
            rep = semantic[representation]
            self.assertEqual(rep["core_topology"]["classification"], "CORE_TOPOLOGY_EQUAL")
            self.assertTrue(rep["geometry_a"]["triangles_equal"])
            self.assertEqual(rep["geometry_a"]["vertices"]["max_abs_delta"], 0.0)
            self.assertEqual(rep["secondary_descriptor_analysis"]["semantics"], "UNRESOLVED")
            self.assertFalse(rep["secondary_descriptor_analysis"]["exact_tuples_equal"])
        bounds = result["collision"]["semantic_diff"]["bounds_1339"]
        self.assertEqual(bounds["center"]["max_abs_delta"], 0.0)
        self.assertEqual(bounds["minimum"]["max_abs_delta"], 0.0)
        self.assertEqual(bounds["maximum"]["max_abs_delta"], 0.0)
        self.assertAlmostEqual(bounds["radius"]["max_abs_delta"],
                               2.384185791015625e-7)

    def test_same_generic_parser_rules_reject_demo_exclusive_trooper_too(self):
        trooper = DEMO_931 / "Trooper" / "car.dx"
        if not trooper.is_file():
            self.skipTest("requires DEMO 9.3.1 Trooper DX")
        result = validate_bridge_candidate(trooper.read_bytes(), source="Trooper/car.dx")
        self.assertEqual(result["status"], "REJECTED_BY_LOCAL_RETAIL_PARSER")
        self.assertIn("texture slot count", result["retail_parser"]["error"])


class RBridge1LedgerAndFailClosedTests(unittest.TestCase):
    def test_ledger_covers_exact_changed_bytes_and_reports_provenance(self):
        source = b"DEMO-BASE"
        candidate = b"DEMO-RL??"
        ledger = [{"start": 5, "end": 9, "old_hex": source[5:9].hex(),
                   "new_hex": candidate[5:9].hex(), "reason": "controlled test",
                   "evidence": "test fixture"}]
        report = audit_bridge_provenance(source, candidate, ledger)
        self.assertTrue(report["complete"])
        self.assertEqual(report["changed_byte_count"], 4)
        self.assertEqual(report["uncovered_changed_offsets"], [])
        self.assertEqual(report["ledger_entries_outside_diff"], [])
        self.assertEqual(report["unchanged_source_byte_percent"], 100.0 * 5 / len(source))

    def test_ledger_rejects_undeclared_or_mismatched_changes(self):
        source = b"DEMO-BASE"
        candidate = b"DEMO-CAS?"
        report = audit_bridge_provenance(source, candidate, [])
        self.assertFalse(report["complete"])
        self.assertTrue(report["uncovered_changed_offsets"])
        bad = [{"start": 5, "end": 9, "old_hex": "00000000", "new_hex": "00000000",
                "reason": "bad", "evidence": "bad"}]
        rejected = audit_bridge_provenance(source, candidate, bad)
        self.assertFalse(rejected["complete"])
        self.assertTrue(rejected["invalid_ledger_entries"])

    def test_malformed_candidate_fails_closed(self):
        result = validate_bridge_candidate(struct.pack("<4I", 0, 0, 0, 0) + bytes(24),
                                           source="synthetic malformed DX")
        self.assertFalse(result["outer_format_valid"])
        self.assertFalse(result["section_bounds_valid"])
        self.assertFalse(result["retail_ready"])
        self.assertEqual(result["status"], "REJECTED_BY_LOCAL_RETAIL_PARSER")


if __name__ == "__main__":
    unittest.main()
