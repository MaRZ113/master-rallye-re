from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_evidence import (
    RETAIL_SHA256,
    RETAIL_SIZE,
    audit_grid,
    audit_mode_map,
    audit_patch_preimages,
    audit_patch_ranges,
    verify_exact_identity,
)


class EvidenceAuditTests(unittest.TestCase):
    def test_exact_identity_accepts_matching_file(self) -> None:
        payload = b"audited fixture"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.exe"
            path.write_bytes(payload)
            result = verify_exact_identity(path, hashlib.sha256(payload).hexdigest(), len(payload))
            self.assertEqual(result["size"], len(payload))

    def test_exact_identity_rejects_changed_hash_and_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.exe"
            path.write_bytes(b"different bytes")
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                verify_exact_identity(path, RETAIL_SHA256, RETAIL_SIZE)
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                verify_exact_identity(path, RETAIL_SHA256, len(b"different bytes"))

    def test_exact_identity_rejects_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "missing file"):
                verify_exact_identity(Path(temp) / "missing.exe", RETAIL_SHA256, RETAIL_SIZE)

    def test_mode_map_requires_all_exact_mode_owners(self) -> None:
        repo = Path(__file__).resolve().parents[4]
        data = json.loads((repo / "research/r-ai1-2/mode-map.json").read_text(encoding="utf-8"))
        result = audit_mode_map(data)
        self.assertEqual(result["QuickRace"]["race_type"], 2)
        broken = json.loads(json.dumps(data))
        next(item for item in broken["modes"] if item["mode"] == "Challenge")["builder"] = "wrong"
        with self.assertRaisesRegex(ValueError, "Challenge owner mismatch"):
            audit_mode_map(broken)

    def test_f3_plan_rejects_overlapping_native_operations(self) -> None:
        valid = {
            "source_executable": {"sha256": RETAIL_SHA256, "size": RETAIL_SIZE},
            "operations": [
                {"rva": 0x100, "expected_original_hex": "90 90", "replacement_hex": "CC CC", "id": "a"},
                {"rva": 0x102, "expected_original_hex": "90", "replacement_hex": "CC", "id": "b"},
            ],
        }
        self.assertEqual(audit_patch_ranges(valid)["overlap_count"], 0)
        valid["operations"][1]["rva"] = 0x101
        with self.assertRaisesRegex(ValueError, "overlapping F3 operations"):
            audit_patch_ranges(valid)

    def test_f3_plan_rejects_wrong_build_and_malformed_sizes(self) -> None:
        plan = {"source_executable": {"sha256": "0" * 64, "size": RETAIL_SIZE}, "operations": []}
        with self.assertRaisesRegex(ValueError, "exact retail"):
            audit_patch_ranges(plan)
        plan["source_executable"]["sha256"] = RETAIL_SHA256
        plan["operations"] = [{"rva": 10, "expected_original_hex": "90 90", "replacement_hex": "CC"}]
        with self.assertRaisesRegex(ValueError, "invalid patch size"):
            audit_patch_ranges(plan)

    def test_preimage_audit_accepts_exact_and_rejects_altered_byte(self) -> None:
        plan = {
            "operations": [
                {"file_offset": 1, "expected_original_hex": "90 91", "id": "fixture-hook"}
            ]
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "image.bin"
            path.write_bytes(b"\xcc\x90\x91\xcc")
            self.assertEqual(audit_patch_preimages(plan, path)["preimage_checked_count"], 1)
            path.write_bytes(b"\xcc\x90\x90\xcc")
            with self.assertRaisesRegex(ValueError, "preimage mismatch"):
                audit_patch_preimages(plan, path)

    def test_grid_audit_keeps_all_runtime_statuses_explicit(self) -> None:
        repo = Path(__file__).resolve().parents[4]
        data = json.loads((repo / "research/general-re/grid8/grid8-audit.json").read_text(encoding="utf-8"))
        result = audit_grid(data)
        self.assertEqual(result["course_count"], 36)
        self.assertEqual(result["scene_registration_count"], 39)
        self.assertEqual(result["runtime_status_counts"].get("NOT_TESTED"), 36)
        broken = json.loads(json.dumps(data))
        broken["courses"][0].pop("runtime_status")
        with self.assertRaisesRegex(ValueError, "lacks an explicit"):
            audit_grid(broken)


if __name__ == "__main__":
    unittest.main()
