from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from tools.build_r_mod1_review import ROOT, write_archive
from tools.r_mod1_composition_audit import audit_composition


class RMod1CompositionAuditTests(unittest.TestCase):
    def test_historical_patch_plans_are_not_safe_to_overlay(self) -> None:
        report = audit_composition()
        self.assertFalse(report["historical_patch_binaries_imported"])
        self.assertFalse(report["integrated_patch_bundle_created"])
        self.assertEqual(report["baseline_executable_sha256"],
                         "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4")
        self.assertGreater(report["overlap_summary"]["identical_shared_operations_to_deduplicate"], 0)
        self.assertEqual(report["overlap_summary"]["semantic_or_code_cave_conflicts"], 2)

        conflicts = {
            tuple(pair["sources"]): [row for row in pair["overlaps"]
                                     if row["classification"] == "SEMANTIC_OR_CAVE_CONFLICT_RECOMPOSE_REQUIRED"]
            for pair in report["pairs"]
        }
        self.assertEqual(conflicts[("randomizer", "capacity")][0]["start"], "0x28E400")
        self.assertEqual(conflicts[("capacity", "ui")][0]["start"], "0x28E300")

    def test_review_archive_is_deterministic_source_only_and_hash_indexed(self) -> None:
        output = ROOT / ".research-output" / "r-mod1" / "review-archive-test.zip"
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            first = write_archive(output, "2026-10-10")
            first_bytes = output.read_bytes()
            second = write_archive(output, "2026-10-10")
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first_bytes, output.read_bytes())
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn("archive-index.json", names)
                self.assertFalse(any(name.lower().endswith((".exe", ".dll", ".dx", ".dxt", ".bin", ".dump.bin")) for name in names))
                index = json.loads(archive.read("archive-index.json"))
                self.assertTrue(index["source_only"])
                for row in index["files"]:
                    data = archive.read(row["path"])
                    self.assertEqual(len(data), row["size"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])
        finally:
            output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
