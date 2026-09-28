from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from master_rallye.demo_dx import inspect_demo_dx
from master_rallye.dx_corpus import (
    render_corpus_markdown,
    scan_dx_corpus,
    write_corpus_reports,
)
from test_dx_revision_upgrade import _rev131_two_triangle_fixture, _rev135_reordered_fixture


def _write_asset(root: Path, generation: str, family: str, role: str,
                 dx_bytes: bytes, gxm_bytes: bytes, *, gxm_name: str | None = None) -> Path:
    folder = root / f"{generation}_{family}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{role}.dx").write_bytes(dx_bytes)
    (folder / (gxm_name or f"{role}.gxm")).write_bytes(gxm_bytes)
    return folder / f"{role}.dx"


def _alternate_prefix(source: bytes) -> bytes:
    result = bytearray(source)
    view = inspect_demo_dx(source, "source.dx")
    result[view.draw_offset + 8 + 20] ^= 0x40
    return bytes(result)


class DxCorpusScannerTests(unittest.TestCase):
    def test_counts_duplicates_pairs_patterns_and_portable_deterministic_reports(self):
        source = _rev131_two_triangle_fixture()
        official = _rev135_reordered_fixture()
        gxm = b"same controlled GXM input"
        with tempfile.TemporaryDirectory(prefix="r-cooker2 corpus ") as directory:
            root = Path(directory)
            _write_asset(root, "9.3.1", "Test", "car", source, gxm)
            _write_asset(root, "9.10.0", "Test", "car", official, gxm)
            _write_asset(root, "9.3.1", "TestCopy", "car", source, b"other source")
            _write_asset(root, "9.3.1", "Only", "car", _alternate_prefix(source), b"only source")
            _write_asset(root, "9.3.1", "Mismatch", "car", source, b"source A")
            _write_asset(root, "9.10.0", "Mismatch", "car", official, b"source B")

            first = scan_dx_corpus(root, repository_root=root)
            second = scan_dx_corpus(root, repository_root=root)
            self.assertEqual(
                json.dumps(first, sort_keys=True),
                json.dumps(second, sort_keys=True),
            )
            markdown = render_corpus_markdown(first)
            self.assertEqual(markdown, render_corpus_markdown(second))
            serialized = json.dumps(first, sort_keys=True)
            self.assertNotIn(str(root), serialized)
            json_path = root / "out" / "coverage.json"
            markdown_path = root / "out" / "coverage.md"
            write_corpus_reports(first, json_path, markdown_path)
            first_json_bytes = json_path.read_bytes()
            first_markdown_bytes = markdown_path.read_bytes()
            self.assertNotIn(b"\r\n", first_json_bytes)
            self.assertNotIn(b"\r\n", first_markdown_bytes)
            write_corpus_reports(second, json_path, markdown_path)
            self.assertEqual(first_json_bytes, json_path.read_bytes())
            self.assertEqual(first_markdown_bytes, markdown_path.read_bytes())

            summary = first["summary"]
            self.assertEqual(summary["dx_file_instances"], 6)
            self.assertEqual(summary["unique_dx_payloads"], 3)
            self.assertEqual(summary["rev131_file_instances"], 4)
            self.assertEqual(summary["unique_rev131_payloads"], 2)
            self.assertEqual(summary["rev135_file_instances"], 2)
            self.assertEqual(summary["unique_rev135_payloads"], 1)
            base_sha = hashlib.sha256(source).hexdigest()
            duplicate_record = next(
                item for item in first["unique_payloads"] if item["sha256"] == base_sha
            )
            self.assertEqual(duplicate_record["file_instance_count"], 3)

            pairing = first["pairing_summary"]
            self.assertEqual(pairing["verified_same_source_pairs"], 1)
            self.assertEqual(pairing["unverified_pairs"], 1)
            self.assertEqual(pairing["draw_records_checked"], 1)
            self.assertEqual(pairing["formula_matches"], 1)
            self.assertEqual(pairing["formula_mismatches"], 0)
            self.assertEqual(
                len(first["verified_same_source_pairs"]),
                1,
            )
            self.assertEqual(
                first["unverified_pairs"][0]["status"],
                "UNVERIFIED_SOURCE_PAIR",
            )

            patterns = first["draw_prefix_patterns"]
            self.assertEqual(patterns["unique_full_tuples"], 2)
            evidence = {tuple(row["A_B_C"]): row["evidence_class"]
                        for row in patterns["patterns"]}
            self.assertEqual(evidence[(0x11, 0x22, 0x33)], "DIRECTLY_ORACLED")
            self.assertEqual(evidence[(0x51, 0x22, 0x33)], "STRUCTURALLY_SUPPORTED_ONLY")

    def test_complete_typo_is_used_for_source_identity(self):
        source = _rev131_two_triangle_fixture()
        official = _rev135_reordered_fixture()
        gxm = b"frontend source bytes"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_asset(root, "9.3.1", "Forester", "complete", source, gxm,
                         gxm_name="comlplete.gxm")
            _write_asset(root, "9.10.0", "Forester", "complete", official, gxm)
            report = scan_dx_corpus(root, repository_root=root)
            pair = report["pairing_summary"]["pairs"][0]
            self.assertEqual(pair["status"], "VERIFIED_SAME_SOURCE")
            self.assertEqual(
                pair["source_gxm_9_3_1"]["filename_role_normalization"],
                "comlplete.gxm treated as complete.gxm source",
            )

    def test_unknown_revision_is_counted_as_unique_dx_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "misc"
            folder.mkdir()
            (folder / "unknown.dx").write_bytes(b"\x0d\xd0\x00\x00\x99\x00\x00\x00")
            report = scan_dx_corpus(root, repository_root=root)
            self.assertEqual(report["summary"]["dx_file_instances"], 1)
            self.assertEqual(report["summary"]["unique_dx_payloads"], 1)
            self.assertEqual(report["summary"]["unrecognized_or_invalid_dx_files"], 1)


if __name__ == "__main__":
    unittest.main()
