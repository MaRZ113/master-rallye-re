from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from master_rallye.junction_lifecycle import JunctionInspection, classify_junction_policy, inspect_junction
from master_rallye.source_cooker_jobs import (
    CookJobError,
    cleanup_authoring_links,
    ensure_authoring_links,
    job_state_summary,
    load_cook_job,
    recover_authoring_links,
    resolve_job_path,
    transition_job,
)
from master_rallye.source_cooker import _resume_job


def _manifest(job_id: str, *, link: Path, target_relative: str = "authoring-root/root-00") -> dict:
    return {
        "schema_version": 2,
        "phase": "R-COOKER3",
        "job_id": job_id,
        "state": "PREFLIGHT_OK",
        "state_history": ["CREATED", "INVENTORIED", "PREFLIGHT_OK"],
        "source_family": "Test",
        "runtime_family": "Test",
        "model_strategy": {"selected": "retail-native-gxm"},
        "paths": {"runtime": "runtime", "authoring_mirror": "authoring-root", "package": "runtime-package"},
        "authoring_links": [{
            "job_id": job_id,
            "link_path": str(link),
            "target_relative_to_job": target_relative,
            "state": "planned",
        }],
        "texture_outputs": [],
    }


def _write_job(root: Path, *, link: Path, job_id: str = "job-1") -> None:
    (root / "runtime").mkdir(parents=True, exist_ok=True)
    (root / "authoring-root" / "root-00").mkdir(parents=True, exist_ok=True)
    (root / "job-manifest.json").write_text(json.dumps(_manifest(job_id, link=link)), encoding="utf-8")


class CookJobPathTests(unittest.TestCase):
    def test_paths_with_spaces_and_job_relocation_resolve_from_current_root(self):
        with tempfile.TemporaryDirectory(prefix="source cooker job ") as temporary:
            base = Path(temporary)
            root_a = base / "root A" / "job with spaces"
            external_link = base / "historical" / "Vehicles" / "Test"
            external_link.parent.mkdir(parents=True)
            _write_job(root_a, link=external_link)
            root_b = base / "root B" / "job with spaces"
            root_b.parent.mkdir()
            shutil.copytree(root_a, root_b)
            job = load_cook_job(root_b)
            resolved = resolve_job_path(root_b, job.manifest["paths"]["authoring_mirror"])
            self.assertEqual(resolved, root_b / "authoring-root")
            self.assertNotIn(str(root_a).casefold(), json.dumps(job.manifest).casefold())
            self.assertEqual(job_state_summary(job)["family"], "Test")

    def test_absolute_or_parent_escape_job_path_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_job(root, link=root / "historic" / "Test")
            with self.assertRaises(CookJobError):
                resolve_job_path(root, "../outside")
            with self.assertRaises(CookJobError):
                resolve_job_path(root, "C:/outside")

    def test_schema_one_job_migrates_internal_paths_without_old_absolute_targets(self):
        with tempfile.TemporaryDirectory(prefix="legacy source cooker ") as temporary:
            base = Path(temporary)
            root = base / "copied job"
            link = base / "legacy" / "DataGx" / "Vehicles" / "Test"
            link.parent.mkdir(parents=True)
            (root / "runtime").mkdir(parents=True)
            (root / "authoring-root" / "root-00").mkdir(parents=True)
            (root / "embedded-authoring-paths.json").write_text(json.dumps({
                "historical_roots": [{"historical_root": str(link), "mirror_id": "root-00", "files": []}],
            }), encoding="utf-8")
            (root / "junction-ownership.json").write_text(json.dumps({
                "links": [{"job_id": "old-job", "link_path": str(link), "target": str(base / "old-job" / "authoring-root" / "root-00"), "state": "planned"}],
            }), encoding="utf-8")
            (root / "job-manifest.json").write_text(json.dumps({
                "schema_version": 1, "phase": "R-COOKER3", "job_id": "old-job",
                "status": "PREPARED_FOR_HUMAN_NATIVE_COOK", "runtime_root": "runtime",
                "runtime_family": "Test", "source_family": "Test",
                "junction_ownership_manifest": "junction-ownership.json",
            }), encoding="utf-8")
            job = load_cook_job(root)
            self.assertEqual(job.manifest["schema_version"], 2)
            self.assertEqual(job.manifest["state"], "WAITING_FOR_RUNTIME")
            self.assertEqual(job.manifest["job_kind"], "NATIVE_GXM_COOK")
            self.assertEqual(job.manifest["authoring_links"][0]["target_relative_to_job"], "authoring-root/root-00")
            self.assertNotIn(str(base / "old-job"), json.dumps(job.manifest))

    def test_schema_one_migration_rejects_external_manifest_paths(self):
        with tempfile.TemporaryDirectory(prefix="source cooker legacy path ") as temporary:
            root = Path(temporary) / "job"
            (root / "runtime").mkdir(parents=True)
            (root / "job-manifest.json").write_text(json.dumps({
                "schema_version": 1, "phase": "R-COOKER3", "job_id": "legacy",
                "runtime_root": "runtime",
                "embedded_authoring_paths": "../outside.json",
            }), encoding="utf-8")
            with self.assertRaisesRegex(CookJobError, "schema-1 embedded_authoring_paths"):
                load_cook_job(root)

    def test_state_machine_rejects_skipping_runtime_output_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_job(root, link=root / "hist" / "Test")
            job = load_cook_job(root)
            with self.assertRaisesRegex(CookJobError, "invalid cook job transition"):
                transition_job(job, "PACKAGED")

    def test_resume_stops_before_collecting_when_live_junction_is_unsafe(self):
        with tempfile.TemporaryDirectory(prefix="source cooker unsafe resume ") as temporary:
            root = Path(temporary) / "job"
            link = Path(temporary) / "historical" / "Test"
            link.parent.mkdir()
            _write_job(root, link=link)
            unsafe_summary = {
                "state": "WAITING_FOR_RUNTIME",
                "model_outputs": {
                    role: {"present": True} for role in ("complete", "car", "wheel")
                },
                "authoring_links": [{
                    "live_state": "STOP", "link_path": str(link),
                    "actual_target": r"D:\\foreign\\mirror",
                }],
            }
            with patch("master_rallye.source_cooker.job_state_summary", return_value=unsafe_summary), \
                    patch("master_rallye.source_cooker.collect_native_cook_job") as collect:
                result = _resume_job(root)
            self.assertEqual(result["status"], "RECOVERY_REQUIRED")
            self.assertIn("recover", result["diagnostic"])
            collect.assert_not_called()

    def test_status_reports_recovery_required_for_live_junction_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="source cooker status mismatch ") as temporary:
            root = Path(temporary) / "job"
            _write_job(root, link=Path(temporary) / "historical" / "Test")
            job = load_cook_job(root)
            unsafe_link = [{
                "live_state": "STOP", "link_path": "historical/Test",
                "actual_target": r"D:\foreign\mirror",
            }]
            with patch("master_rallye.source_cooker_jobs.inspect_job_links", return_value=unsafe_link):
                summary = job_state_summary(job)
            self.assertEqual(summary["state"], "RECOVERY_REQUIRED")
            self.assertIn("recover", summary["next_action"])


class JunctionPolicyTests(unittest.TestCase):
    def test_policy_blocks_foreign_type_and_wrong_target(self):
        expected = r"D:\mirror"
        self.assertEqual(classify_junction_policy(
            JunctionInspection("ABSENT"), expected_target=expected,
            owned_by_job=True, ownership_state="planned",
        ), "CREATE")
        self.assertEqual(classify_junction_policy(
            JunctionInspection("DIRECTORY"), expected_target=expected,
            owned_by_job=True, ownership_state="created",
        ), "STOP")
        self.assertEqual(classify_junction_policy(
            JunctionInspection("JUNCTION", r"D:\elsewhere"), expected_target=expected,
            owned_by_job=True, ownership_state="created",
        ), "STOP")
        self.assertEqual(classify_junction_policy(
            JunctionInspection("JUNCTION", "D:\\mirror\\"), expected_target=expected,
            owned_by_job=True, ownership_state="created",
        ), "OWNED")

    def test_create_reuse_and_cleanup_are_exact_and_idempotent(self):
        if os.name != "nt":
            self.skipTest("Windows Junction integration requires Windows")
        with tempfile.TemporaryDirectory(prefix="junction lifecycle ") as temporary:
            root = Path(temporary)
            target = root / "mirror with spaces"
            target.mkdir()
            link = root / "historical parent" / "asset path"
            link.parent.mkdir()
            _write_job(root / "job", link=link)
            job = load_cook_job(root / "job")
            job = ensure_authoring_links(job)
            self.assertEqual(job.manifest["authoring_links"][0]["state"], "created")
            reused = ensure_authoring_links(job)
            self.assertEqual(reused.manifest["authoring_links"][0]["state"], "created")
            cleaned = cleanup_authoring_links(reused)
            self.assertEqual(cleaned.manifest["authoring_links"][0]["state"], "removed")
            cleaned_again = cleanup_authoring_links(cleaned)
            self.assertEqual(cleaned_again.manifest["authoring_links"][0]["state"], "removed")
            self.assertTrue(target.is_dir())
            self.assertFalse(os.path.lexists(link))

    def test_recover_planned_exact_link_and_created_absence(self):
        if os.name != "nt":
            self.skipTest("Windows Junction integration requires Windows")
        with tempfile.TemporaryDirectory(prefix="junction recover ") as temporary:
            root = Path(temporary)
            job_root = root / "job"
            link = root / "old" / "asset"
            link.parent.mkdir()
            _write_job(job_root, link=link)
            job = load_cook_job(job_root)
            target = resolve_job_path(job_root, "authoring-root/root-00")
            from master_rallye.junction_lifecycle import create_junction
            create_junction(link, target)
            recovered = recover_authoring_links(job)
            self.assertEqual(recovered.manifest["authoring_links"][0]["state"], "created")
            cleaned = cleanup_authoring_links(recovered)
            recovered_absent = recover_authoring_links(cleaned)
            self.assertEqual(recovered_absent.manifest["authoring_links"][0]["state"], "removed")

    def test_resume_recreates_only_the_absent_job_owned_junction(self):
        if os.name != "nt":
            self.skipTest("Windows Junction integration requires Windows")
        with tempfile.TemporaryDirectory(prefix="junction resume ") as temporary:
            root = Path(temporary)
            job_root = root / "job"
            link = root / "historical parent" / "asset path"
            link.parent.mkdir()
            _write_job(job_root, link=link)
            job = ensure_authoring_links(load_cook_job(job_root))
            cleaned = cleanup_authoring_links(job)
            self.assertEqual(cleaned.manifest["state"], "AUTHORING_CLEANED")
            self.assertFalse(os.path.lexists(link))

            result = _resume_job(job_root)
            self.assertEqual(result["status"], "WAITING_FOR_RUNTIME")
            self.assertEqual(result["job"]["state"], "WAITING_FOR_RUNTIME")
            self.assertEqual(inspect_junction(link).kind, "JUNCTION")
            cleanup_authoring_links(load_cook_job(job_root))

    def test_real_directory_is_blocked_and_never_deleted(self):
        if os.name != "nt":
            self.skipTest("Windows Junction integration requires Windows")
        with tempfile.TemporaryDirectory(prefix="junction block ") as temporary:
            root = Path(temporary)
            link = root / "historic" / "asset"
            link.mkdir(parents=True)
            marker = link / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            job_root = root / "job"
            _write_job(job_root, link=link)
            recovered = recover_authoring_links(load_cook_job(job_root))
            self.assertEqual(recovered.manifest["state"], "RECOVERY_REQUIRED")
            self.assertTrue(marker.is_file())
            with self.assertRaises(CookJobError):
                ensure_authoring_links(recovered)

    def test_relocated_job_creates_and_cleans_link_against_new_job_root(self):
        if os.name != "nt":
            self.skipTest("Windows Junction integration requires Windows")
        with tempfile.TemporaryDirectory(prefix="junction relocated job ") as temporary:
            base = Path(temporary)
            original_root = base / "root A" / "job with spaces"
            link = base / "historical parent" / "asset path"
            link.parent.mkdir(parents=True)
            _write_job(original_root, link=link)
            moved_root = base / "root B" / "job with spaces"
            moved_root.parent.mkdir()
            shutil.copytree(original_root, moved_root)

            moved_job = ensure_authoring_links(load_cook_job(moved_root))
            target = Path(moved_job.manifest["authoring_links"][0]["target_relative_to_job"])
            target = moved_root / target
            live = inspect_junction(link)
            self.assertEqual(live.kind, "JUNCTION")
            self.assertEqual(live.target.casefold(), str(target).casefold())
            self.assertNotIn(str(original_root).casefold(), live.target.casefold())

            cleaned = cleanup_authoring_links(moved_job)
            self.assertEqual(cleaned.manifest["authoring_links"][0]["state"], "removed")
            self.assertFalse(os.path.lexists(link))
            self.assertTrue(target.is_dir())
            self.assertTrue((original_root / "authoring-root" / "root-00").is_dir())

    def test_foreign_junction_is_blocked_and_target_is_never_removed(self):
        if os.name != "nt":
            self.skipTest("Windows Junction integration requires Windows")
        with tempfile.TemporaryDirectory(prefix="junction foreign target ") as temporary:
            base = Path(temporary)
            link = base / "historical parent" / "asset path"
            link.parent.mkdir()
            foreign_target = base / "foreign mirror"
            foreign_target.mkdir()
            marker = foreign_target / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            job_root = base / "job"
            _write_job(job_root, link=link)

            from master_rallye.junction_lifecycle import create_junction, remove_owned_junction
            create_junction(link, foreign_target)
            try:
                recovered = recover_authoring_links(load_cook_job(job_root))
                self.assertEqual(recovered.manifest["state"], "RECOVERY_REQUIRED")
                with self.assertRaises(CookJobError):
                    cleanup_authoring_links(recovered)
                self.assertTrue(marker.is_file())
                self.assertEqual(inspect_junction(link).target.casefold(), str(foreign_target).casefold())
            finally:
                remove_owned_junction(
                    link, foreign_target, owned_by_job=True, ownership_state="created",
                )


if __name__ == "__main__":
    unittest.main()
