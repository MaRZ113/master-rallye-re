"""Portable job manifests and fail-closed native-cook lifecycle helpers."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .junction_lifecycle import (
    JunctionError,
    JunctionInspection,
    classify_junction_policy,
    create_junction,
    inspect_junction,
    normalize_windows_path,
    remove_owned_junction,
)
from .dx_revision_upgrade import REVISION_135, validate_existing_rev135


class CookJobError(ValueError):
    """A cook job is malformed, unsafe, or not ready for the requested step."""


JOB_SCHEMA_VERSION = 2
JOB_STATES = (
    "CREATED", "INVENTORIED", "PREFLIGHT_OK", "AUTHORING_READY",
    "WAITING_FOR_RUNTIME", "RUNTIME_OUTPUTS_PRESENT", "COLLECTED",
    "VALIDATED", "PACKAGED", "AUTHORING_CLEANED", "COMPLETE",
    "BLOCKED", "RECOVERY_REQUIRED",
)

_ALLOWED_TRANSITIONS = {
    "CREATED": {"INVENTORIED", "BLOCKED", "RECOVERY_REQUIRED"},
    "INVENTORIED": {"PREFLIGHT_OK", "BLOCKED", "RECOVERY_REQUIRED"},
    "PREFLIGHT_OK": {"AUTHORING_READY", "BLOCKED", "RECOVERY_REQUIRED"},
    "AUTHORING_READY": {"WAITING_FOR_RUNTIME", "RUNTIME_OUTPUTS_PRESENT", "BLOCKED", "RECOVERY_REQUIRED"},
    "WAITING_FOR_RUNTIME": {"RUNTIME_OUTPUTS_PRESENT", "BLOCKED", "RECOVERY_REQUIRED"},
    "RUNTIME_OUTPUTS_PRESENT": {"COLLECTED", "BLOCKED", "RECOVERY_REQUIRED"},
    "COLLECTED": {"VALIDATED", "BLOCKED", "RECOVERY_REQUIRED"},
    "VALIDATED": {"PACKAGED", "BLOCKED", "RECOVERY_REQUIRED"},
    "PACKAGED": {"AUTHORING_CLEANED", "COMPLETE", "BLOCKED", "RECOVERY_REQUIRED"},
    "AUTHORING_CLEANED": {"COMPLETE", "BLOCKED", "RECOVERY_REQUIRED"},
    "COMPLETE": {"RECOVERY_REQUIRED"},
    "BLOCKED": {"INVENTORIED", "PREFLIGHT_OK", "AUTHORING_READY", "WAITING_FOR_RUNTIME",
                "RUNTIME_OUTPUTS_PRESENT", "RECOVERY_REQUIRED"},
    "RECOVERY_REQUIRED": {"AUTHORING_READY", "WAITING_FOR_RUNTIME", "RUNTIME_OUTPUTS_PRESENT",
                          "PACKAGED", "AUTHORING_CLEANED", "COMPLETE", "BLOCKED"},
}


@dataclass(frozen=True)
class CookJob:
    root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    source_schema_version: int


def _relative_path(value: str, *, label: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise CookJobError(f"unsafe job-relative {label}: {value!r}")
    if path.parts[0].endswith(":"):
        raise CookJobError(f"absolute drive path is not allowed for {label}: {value!r}")
    return path


def resolve_job_path(job_root: Path, relative: str, *, label: str = "path") -> Path:
    """Resolve a manifest path beneath the current job root."""
    root = Path(job_root).resolve()
    path = root.joinpath(*_relative_path(relative, label=label).parts)
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise CookJobError(f"job-relative {label} escapes its root: {relative!r}") from exc
    return path


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CookJobError(f"cannot read cook job manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CookJobError(f"cook job manifest must contain an object: {path}")
    if not value.get("job_id"):
        raise CookJobError("cook job manifest has no job_id")
    return value


def _legacy_migration(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Migrate V1 internal paths at load time; external provenance stays external."""
    migrated = dict(manifest)
    try:
        runtime = str(_relative_path(str(manifest.get("runtime_root", "runtime")), label="runtime_root"))
    except CookJobError:
        raise CookJobError("schema-1 runtime_root is not a safe job-relative path")
    paths: dict[str, str] = {"runtime": runtime, "authoring_mirror": "authoring-root", "package": "runtime-package"}
    old_package = manifest.get("package_root")
    if isinstance(old_package, str):
        try:
            Path(old_package).resolve().relative_to(root.resolve())
            paths["package"] = Path(old_package).resolve().relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            # Never preserve an absolute internal package path across relocation.
            pass

    discovery_path = resolve_job_path(
        root, str(manifest.get("embedded_authoring_paths", "embedded-authoring-paths.json")),
        label="schema-1 embedded_authoring_paths",
    )
    if discovery_path.is_file():
        try:
            discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            discovery = {}
    else:
        discovery = {}
    mirror_by_link = {
        normalize_windows_path(str(row.get("historical_root", ""))): f"authoring-root/{row.get('mirror_id')}"
        for row in discovery.get("historical_roots", []) if row.get("mirror_id")
    }
    old_ownership_name = manifest.get("junction_ownership_manifest", "junction-ownership.json")
    owner_path = resolve_job_path(root, str(old_ownership_name), label="schema-1 junction_ownership_manifest")
    try:
        owner = json.loads(owner_path.read_text(encoding="utf-8")) if owner_path.is_file() else {}
    except (OSError, json.JSONDecodeError):
        owner = {}
    links = []
    for row in owner.get("links", []):
        link_path = str(row.get("link_path", ""))
        relative_target = mirror_by_link.get(normalize_windows_path(link_path))
        if not relative_target:
            links.append({
                "job_id": manifest["job_id"], "link_path": link_path,
                "target_relative_to_job": "authoring-root/unknown",
                "state": "blocked", "migration_error": "no matching mirror_id in discovery manifest",
            })
            continue
        links.append({
            "job_id": manifest["job_id"], "link_path": link_path,
            "target_relative_to_job": relative_target,
            "state": str(row.get("state", "planned")).casefold(),
        })
    status = str(manifest.get("status", "")).upper()
    state = {
        "PREPARED_FOR_HUMAN_NATIVE_COOK": "WAITING_FOR_RUNTIME",
        "NATIVE_OUTPUTS_COLLECTED": "PACKAGED",
    }.get(status, status if status in JOB_STATES else "RECOVERY_REQUIRED")
    migrated.update({
        "schema_version": JOB_SCHEMA_VERSION,
        "state": state,
        "paths": paths,
        "authoring_links": links,
        "migrated_from_schema_version": 1,
    })
    if manifest.get("phase") == "R-COOKER3" and status in {
        "PREPARED_FOR_HUMAN_NATIVE_COOK", "NATIVE_OUTPUTS_COLLECTED",
    }:
        migrated["job_kind"] = "NATIVE_GXM_COOK"
    return migrated


def load_cook_job(job_root: Path) -> CookJob:
    root = Path(job_root).resolve()
    if not root.is_dir():
        raise CookJobError(f"cook job directory does not exist: {root}")
    manifest_path = root / "job-manifest.json"
    manifest = _read_manifest(manifest_path)
    source_version = int(manifest.get("schema_version", 1))
    if source_version == 1:
        manifest = _legacy_migration(root, manifest)
    elif source_version != JOB_SCHEMA_VERSION:
        raise CookJobError(f"unsupported cook job schema_version {source_version}")
    if manifest.get("schema_version") != JOB_SCHEMA_VERSION:
        raise CookJobError("job manifest migration did not produce schema version 2")
    if not isinstance(manifest.get("paths"), dict):
        raise CookJobError("schema-2 cook job has no paths mapping")
    for key, relative in manifest["paths"].items():
        resolve_job_path(root, str(relative), label=key)
    if not isinstance(manifest.get("authoring_links", []), list):
        raise CookJobError("authoring_links must be a list")
    return CookJob(root, manifest_path, manifest, source_version)


def write_cook_job(job: CookJob, manifest: Mapping[str, Any] | None = None) -> CookJob:
    value = dict(manifest or job.manifest)
    value["schema_version"] = JOB_SCHEMA_VERSION
    state = value.get("state")
    if state not in JOB_STATES:
        raise CookJobError(f"unknown cook job state: {state!r}")
    fd, temp_name = tempfile.mkstemp(prefix="job-manifest.", suffix=".tmp", dir=job.root)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(job.manifest_path)
    finally:
        Path(temp_name).unlink(missing_ok=True)
    return CookJob(job.root, job.manifest_path, value, job.source_schema_version)


def transition_job(job: CookJob, new_state: str, *, updates: Mapping[str, Any] | None = None) -> CookJob:
    if new_state not in JOB_STATES:
        raise CookJobError(f"unknown cook job state: {new_state!r}")
    old_state = str(job.manifest.get("state", "CREATED"))
    if new_state != old_state and new_state not in _ALLOWED_TRANSITIONS.get(old_state, set()):
        raise CookJobError(f"invalid cook job transition {old_state} -> {new_state}")
    result = dict(job.manifest)
    result.update(dict(updates or {}))
    _validate_transition_evidence(job, new_state, result)
    result["state"] = new_state
    history = list(result.get("state_history", []))
    if not history:
        history.append(old_state)
    if not history or history[-1] != new_state:
        history.append(new_state)
    result["state_history"] = history
    return write_cook_job(job, result)


def _validate_transition_evidence(job: CookJob, new_state: str, manifest: Mapping[str, Any]) -> None:
    """Require real files at the gates that claim outputs or packaging."""
    if new_state == "RUNTIME_OUTPUTS_PRESENT":
        runtime_rel = str(manifest.get("paths", {}).get("runtime", ""))
        runtime = resolve_job_path(job.root, runtime_rel, label="runtime")
        family = str(manifest.get("runtime_family", ""))
        if not family:
            raise CookJobError("runtime_family is missing at the runtime-output gate")
        asset_dir = runtime / "DataGx" / "Vehicles" / family
        missing = []
        failures = []
        for role in ("complete", "car", "wheel"):
            path = asset_dir / f"{role}.dx"
            if not path.is_file():
                missing.append(role)
                continue
            try:
                validation = validate_existing_rev135(path.read_bytes(), str(path))
                if validation.get("revision") != REVISION_135:
                    failures.append(f"{role}: unexpected revision {validation.get('revision')}")
            except Exception as exc:
                failures.append(f"{role}: {exc}")
        if missing or failures:
            details = []
            if missing:
                details.append("missing=" + ",".join(missing))
            if failures:
                details.append("invalid=" + "; ".join(failures))
            raise CookJobError("runtime output evidence gate failed: " + " | ".join(details))
    if new_state in {"COLLECTED", "VALIDATED", "PACKAGED"}:
        external = manifest.get("package_output_external")
        if external:
            package = Path(str(external)).resolve()
        else:
            package = resolve_job_path(job.root, str(manifest.get("paths", {}).get("package", "")), label="package")
        manifest_path = package / "package-manifest.json"
        report_path = package / "validation-report.json"
        if not manifest_path.is_file() or not report_path.is_file():
            raise CookJobError(f"package evidence is incomplete at lifecycle state {new_state}: {package}")
        try:
            package_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CookJobError(f"package evidence JSON is invalid: {exc}") from exc
        if new_state in {"VALIDATED", "PACKAGED"} and report.get("status") != "PASS":
            raise CookJobError(f"package validation report is not PASS: {report.get('status')!r}")
        if new_state in {"VALIDATED", "PACKAGED"}:
            source_provenance = package_manifest.get("source_provenance", {})
            expected_job_id = manifest.get("job_id")
            if source_provenance.get("native_cook_job_id") != expected_job_id:
                raise CookJobError("package provenance does not match the native cook job_id")


def _link_is_owned(job: CookJob, row: Mapping[str, Any]) -> bool:
    return row.get("job_id") == job.manifest.get("job_id") and row.get("state") in {
        "planned", "created", "reused", "removed", "blocked",
    }


def expected_link_target(job: CookJob, row: Mapping[str, Any]) -> Path:
    return resolve_job_path(job.root, str(row.get("target_relative_to_job", "")), label="Junction target")


def ensure_authoring_links(job: CookJob) -> CookJob:
    """Create absent planned links or verify exact links already owned by job."""
    rows = [dict(row) for row in job.manifest.get("authoring_links", [])]
    for row in rows:
        if not _link_is_owned(job, row) or row.get("state") == "blocked":
            raise CookJobError(f"invalid or blocked Junction ownership row: {row}")
        link = Path(str(row.get("link_path", "")))
        target = expected_link_target(job, row)
        if not target.is_dir():
            raise CookJobError(f"authoring mirror target is missing: {target}")
        if not link.parent.is_dir():
            raise CookJobError(f"historical parent is missing; refusing to create it: {link.parent}")
        inspection = inspect_junction(link)
        if inspection.kind == "ABSENT":
            if row.get("state") not in {"planned", "removed"}:
                raise CookJobError(f"Junction state says {row.get('state')} but path is absent: {link}; run recover")
            create_junction(link, target)
            row["state"] = "created"
            row.pop("diagnostic", None)
        else:
            action = classify_junction_policy(
                inspection,
                expected_target=str(target),
                owned_by_job=_link_is_owned(job, row),
                ownership_state=str(row.get("state")),
            )
            if action not in {"REUSE", "OWNED"}:
                raise CookJobError(
                    f"historical path is not an exact Junction owned by this job: "
                    f"{link} ({inspection.kind}, target={inspection.target!r})"
                )
    updated = dict(job.manifest)
    updated["authoring_links"] = rows
    old_state = str(updated.get("state", "PREFLIGHT_OK"))
    updated["state"] = "AUTHORING_READY"
    history = list(updated.get("state_history", []))
    if not history:
        history.append(old_state)
    if history[-1] != "AUTHORING_READY":
        history.append("AUTHORING_READY")
    updated["state_history"] = history
    return write_cook_job(job, updated)


def inspect_job_links(job: CookJob) -> list[dict[str, Any]]:
    result = []
    for raw in job.manifest.get("authoring_links", []):
        row = dict(raw)
        if row.get("state") == "blocked":
            result.append({**row, "live_state": "BLOCKED", "actual_target": None})
            continue
        target = expected_link_target(job, row)
        live = inspect_junction(str(row.get("link_path", "")))
        policy = classify_junction_policy(
            live,
            expected_target=str(target),
            owned_by_job=_link_is_owned(job, row),
            ownership_state=str(row.get("state")),
        )
        result.append({**row, "live_state": policy, "actual_target": live.target, "target": str(target)})
    return result


def recover_authoring_links(job: CookJob) -> CookJob:
    """Reconcile only unambiguous planned/created versus live Junction states."""
    rows = [dict(row) for row in job.manifest.get("authoring_links", [])]
    for row in rows:
        if not _link_is_owned(job, row) or row.get("state") == "blocked":
            row["state"] = "blocked"
            row["diagnostic"] = "ownership record is incomplete or belongs to another job"
            continue
        target = expected_link_target(job, row)
        inspection = inspect_junction(str(row.get("link_path", "")))
        if inspection.kind == "ABSENT":
            if row.get("state") == "created":
                row["state"] = "removed"
                row["diagnostic"] = "owned Junction is already absent"
            elif row.get("state") in {"planned", "removed"}:
                row["diagnostic"] = "no live Junction; manifest state is safe"
            else:
                row["state"] = "blocked"
                row["diagnostic"] = "absent path conflicts with ownership state"
            continue
        if inspection.kind == "JUNCTION" and inspection.target and normalize_windows_path(inspection.target) == normalize_windows_path(target):
            if row.get("state") == "planned":
                row["state"] = "created"
                row["diagnostic"] = "reconciled exact Junction created before manifest update"
            elif row.get("state") == "created":
                row["diagnostic"] = "exact owned Junction remains present"
            else:
                row["state"] = "blocked"
                row["diagnostic"] = "exact Junction exists but is not recorded as created by this job"
        else:
            row["state"] = "blocked"
            row["diagnostic"] = f"live path mismatch: kind={inspection.kind}, target={inspection.target!r}"
    blocked = any(row.get("state") == "blocked" for row in rows)
    updated = dict(job.manifest)
    updated["authoring_links"] = rows
    if blocked:
        recovered_state = "RECOVERY_REQUIRED"
    elif rows and all(row.get("state") == "removed" for row in rows):
        recovered_state = "AUTHORING_CLEANED"
    elif any(row.get("state") in {"created", "planned"} for row in rows):
        recovered_state = "WAITING_FOR_RUNTIME"
    else:
        previous = str(job.manifest.get("state", "WAITING_FOR_RUNTIME"))
        recovered_state = "WAITING_FOR_RUNTIME" if previous == "RECOVERY_REQUIRED" else previous
    updated["state"] = recovered_state
    updated["last_recovery"] = "BLOCKED" if blocked else "RECONCILED"
    history = list(updated.get("state_history", []))
    if history and history[-1] != updated["state"]:
        history.append(updated["state"])
    updated["state_history"] = history
    return write_cook_job(job, updated)


def cleanup_authoring_links(job: CookJob) -> CookJob:
    """Idempotently remove only exact Junctions created by this job."""
    rows = [dict(row) for row in job.manifest.get("authoring_links", [])]
    for row in rows:
        if not _link_is_owned(job, row) or row.get("state") == "blocked":
            raise CookJobError(f"refusing cleanup with invalid ownership row: {row}")
        target = expected_link_target(job, row)
        try:
            outcome = remove_owned_junction(
                str(row.get("link_path", "")), target,
                owned_by_job=True, ownership_state=str(row.get("state")),
            )
        except JunctionError as exc:
            row["state"] = "blocked"
            row["diagnostic"] = str(exc)
            updated = dict(job.manifest)
            updated["authoring_links"] = rows
            updated["state"] = "RECOVERY_REQUIRED"
            write_cook_job(job, updated)
            raise CookJobError(str(exc)) from exc
        row["state"] = "removed"
        row["diagnostic"] = outcome
    updated = dict(job.manifest)
    updated["authoring_links"] = rows
    state = str(updated.get("state", ""))
    if state == "PACKAGED":
        updated["state"] = "COMPLETE"
    elif state not in {"COMPLETE", "AUTHORING_CLEANED"}:
        updated["state"] = "AUTHORING_CLEANED"
    history = list(updated.get("state_history", []))
    if history and history[-1] != updated["state"]:
        history.append(updated["state"])
    updated["state_history"] = history
    return write_cook_job(job, updated)


def job_state_summary(job: CookJob) -> dict[str, Any]:
    runtime = resolve_job_path(job.root, job.manifest["paths"]["runtime"], label="runtime")
    family = str(job.manifest.get("runtime_family", ""))
    asset_dir = runtime / "DataGx" / "Vehicles" / family
    role_status = {
        role: {"path": str(asset_dir / f"{role}.dx"), "present": (asset_dir / f"{role}.dx").is_file()}
        for role in ("complete", "car", "wheel")
    }
    link_status = inspect_job_links(job)
    unsafe_links = [row for row in link_status if row.get("live_state") in {"STOP", "BLOCKED"}]
    reported_state = "RECOVERY_REQUIRED" if unsafe_links else job.manifest.get("state")
    if unsafe_links or reported_state in {"BLOCKED", "RECOVERY_REQUIRED"}:
        next_action = "run recover and inspect the listed Junction diagnostics"
    elif all(row["present"] for row in role_status.values()):
        next_action = "run resume to validate and collect the runtime outputs"
    elif any(row.get("live_state") in {"ABSENT", "CREATE"} for row in link_status):
        next_action = "run resume to safely create or restore the job-owned authoring Junction before cooking"
    elif reported_state in {"PACKAGED", "COMPLETE", "AUTHORING_CLEANED"}:
        next_action = "this job is already packaged or cleaned; use a new job to cook again"
    else:
        next_action = "load the frontend preview and race model in the isolated runtime, then run resume"
    package_external = job.manifest.get("package_output_external")
    package = (
        Path(str(package_external)).resolve() if package_external else
        resolve_job_path(job.root, str(job.manifest["paths"].get("package", "runtime-package")), label="package")
    )
    return {
        "job_id": job.manifest.get("job_id"),
        "family": job.manifest.get("source_family"),
        "runtime_family": family,
        "model_strategy": job.manifest.get("model_strategy", {}).get("selected"),
        "state": reported_state,
        "job_schema_version": job.manifest.get("schema_version"),
        "runtime_root": str(runtime),
        "runtime_executable_present": (runtime / "MRallye.exe").is_file(),
        "model_outputs": role_status,
        "textures_resolved": len(job.manifest.get("texture_outputs", [])),
        "authoring_links": link_status,
        "package_root": str(package),
        "package_present": package.is_dir(),
        "validation_status": job.manifest.get("validation_status", {}),
        "next_action": next_action,
        "paths": job.manifest.get("paths", {}),
    }
