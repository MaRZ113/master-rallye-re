#!/usr/bin/env python3
"""Build a compact, deterministic source/evidence review ZIP for R5V-J.2."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".research-output/vehicles/sdk/j2-reentry/j2-id27-root-cause-review-2026-10-09.zip"
FINAL_OUTPUT = ROOT / ".research-output/vehicles/sdk/j2-reentry/j2-final-closeout-review-2026-10-09.zip"
REPO_SAFE = "D:/Game/Master Rallye/master-rallye-re-vehicles"
ZIP_ROOT = "r5v-j2-id27-root-cause-review"
FINAL_ZIP_ROOT = "r5v-j2-final-closeout-review"
FIXED_ZIP_TIME = (2026, 10, 9, 0, 0, 0)


class ReviewPackageError(ValueError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={REPO_SAFE}", *args],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise ReviewPackageError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.rstrip()


def _files_to_include() -> list[Path]:
    fixed = [
        "pyproject.toml",
        "src/master_rallye/__init__.py",
        "tools/mrtool.py",
        "tools/addon_runtime.py",
        "tools/build_runtime_launcher.py",
        "tools/j2_frontend_reentry.py",
        "tools/build_j2_reentry_launcher.py",
        "tools/verify_j2_runtime_archive.py",
        "tools/package_j2_review.py",
        "runtime_launcher/CMakeLists.txt",
        "runtime_launcher/src/main.cpp",
        "README.md",
        "research/vehicles/status.md",
        "research/vehicles/architecture.md",
        "tests/synthetic/test_j2_frontend_reentry.py",
        "tests/synthetic/test_addon_sdk_j2_composition.py",
        "tests/synthetic/test_addon_sdk.py",
        "tests/synthetic/test_addon_sdk_runtime.py",
        "research/vehicles/sdk/architecture.md",
        "research/vehicles/sdk/manifest-schema.md",
        "research/vehicles/sdk/compilation.md",
        "research/vehicles/sdk/runtime-deployment.md",
        "research/vehicles/sdk/compatibility.md",
        "research/vehicles/sdk/colour-and-hud.md",
        "research/vehicles/sdk/remaining-gates.md",
        "research/vehicles/sdk/frontend-lifecycle.md",
        "research/vehicles/sdk/schema/addon-manifest-v1.schema.json",
        "research/vehicles/sdk/capabilities/retail-2001.json",
        "research/vehicles/sdk/examples/mercedes-ml320.json",
        "research/vehicles/sdk/examples/r5v-qualifier-t2.json",
        "research/vehicles/sdk/fixtures/frontend-reentry.json",
        "research/vehicles/sdk/j2/closeout-2026-10-09.md",
        "research/vehicles/sdk/j2/closeout-runtime-report-2026-10-09.json",
        "research/vehicles/sdk/j3/README.md",
        "research/vehicles/sdk/j3/plan.md",
    ]
    paths = [ROOT / rel for rel in fixed]
    paths.extend(sorted((ROOT / "src/master_rallye/addon_sdk").glob("*.py")))
    j2_docs = ROOT / "research/vehicles/sdk/j2"
    paths.extend(sorted(path for path in j2_docs.glob("*.md")
                        if path.name != "human-qualification-handoff.md"))
    paths.extend(sorted(path for path in j2_docs.glob("runtime-evidence-*.json")))
    hotfix = ROOT / "research/vehicles/sdk/j2/critical-hotfix"
    paths.extend(sorted(
        path for path in hotfix.rglob("*")
        if path.is_file() and path.relative_to(hotfix).parts[0] != "tmp"
    ))
    root_cause = ROOT / "research/vehicles/sdk/j2/root-cause"
    paths.extend(sorted(path for path in root_cause.rglob("*") if path.is_file()))
    unique = {p.resolve(): p for p in paths}
    return [unique[key] for key in sorted(unique, key=lambda p: p.as_posix().casefold())]


def _git_state() -> bytes:
    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    diff_stat = _git("diff", "--stat")
    staged_stat = _git("diff", "--cached", "--stat")
    content = [
        f"branch: {branch}",
        f"HEAD: {head}",
        "",
        "working-tree status (porcelain v1):",
        status or "(clean)",
        "",
        "unstaged diff stat:",
        diff_stat or "(none)",
        "",
        "staged diff stat:",
        staged_stat or "(none)",
    ]
    return ("\n".join(content) + "\n").encode("utf-8")


def _read_payload(*, final_closeout: bool = False) -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    for path in _files_to_include():
        if not path.is_file() or path.is_symlink():
            raise ReviewPackageError(f"required source/evidence file is missing or linked: {path}")
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.casefold() not in {".py", ".md", ".json", ".txt", ".toml", ".cpp"} and path.name != "CMakeLists.txt":
            raise ReviewPackageError(f"refusing non-text archive member: {relative}")
        data = path.read_bytes()
        if len(data) > 2_000_000:
            raise ReviewPackageError(f"refusing oversized review member: {relative}")
        payload[relative] = data
    payload["GIT-STATE.txt"] = _git_state()
    payload["README.md"] = _archive_readme(final_closeout=final_closeout).encode("utf-8")
    return payload


def _archive_readme(*, final_closeout: bool = False) -> str:
    if final_closeout:
        return """# R5V-J.2 final closeout review

This source/evidence-only archive records R5V-J.2 as FULL PASS / CLOSED. The
owner confirmed the exact corrected ID27 reverse-mapper candidate in human
runtime. That confirmation is explicitly owner-reported; no new Observatory
capture is claimed. The 19 verified JSON/raw pairs separately support the
two-addon SplitScreen, Rallye Cup persistence, Master Rallye fresh-process
persistence, and hardened Dump results.

The mapper stores T2 local7 at `this+0x18` with `C7 46 18 07`; generated
sparse mappers obey `local_field_offset = 0x14 + 4 * class_id`. The J.1 parent
remains 246 operations and is unchanged. Candidate generation-time manifests
are preserved as generated.

The archive excludes executable binaries, game assets, Data.sma, saves, raw
Broker dumps, screenshots, and generated runtime resource bundles. J.3
preparation is a plan only. Only physical IDs 26 and 27 are runtime-qualified.
"""
    return """# R5V-J.2 ID27 re-entry root-cause implementation review

This source/evidence-only package records the exact native cause of ID27
returning as Navara: the physical-ID-to-class/local reverse mapper sets T2 but
writes local ordinal 7 to the T1 slot (`this+0x14`) instead of T2's
`this+0x18`. The new candidate corrects the single mapper displacement. The
stack-ABI-correct constructor publisher remains unchanged. Status is
READY_FOR_HUMAN_RUNTIME; no new runtime pass is claimed. The archive excludes
executables, launcher binaries, game assets, Data.sma, user saves, raw Broker
dumps, screenshots, and generated runtime resource bundles.

## Reproduce the offline two-addon reference plan

Requirements: Python 3.10+ and this repository's checked-in project sources.
From the repository root, in PowerShell:

```powershell
$env:PYTHONPATH = 'src'
python tools/mrtool.py addon validate `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json `
  --capabilities research/vehicles/sdk/capabilities/retail-2001.json
python tools/mrtool.py addon build `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json `
  --capabilities research/vehicles/sdk/capabilities/retail-2001.json `
  --output .research-output/vehicles/sdk/j2/reproduced-plan
python tools/mrtool.py addon verify .research-output/vehicles/sdk/j2/reproduced-plan
Get-FileHash -Algorithm SHA256 .research-output/vehicles/sdk/j2/reproduced-plan/addon-plan.json
```

Expected plan SHA256:
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`.
This remains an offline semantic plan (`runtime_installable=false`).

## Validation and human test

The root-cause full/focused test output, compile checks, bundle hashes and
native launcher preflight are included under
`research/vehicles/sdk/j2/root-cause/`. Focused patch-plan tests require
the exact pristine retail executable and verified local J.1 runtime bundle at
the standard ignored research-output paths; those proprietary inputs are
excluded. Run the minimal in-game retest in
`research/vehicles/sdk/j2/root-cause/human-retest.md`. A human result is
required before marking re-entry confirmed.
"""


def _test_counts(payload: dict[str, bytes]) -> dict[str, int] | None:
    raw = payload.get(
        "research/vehicles/sdk/j2/root-cause/tests-full-output.txt",
        payload.get(
            "research/vehicles/sdk/j2/critical-hotfix/tests-full-output.txt",
            payload.get("research/vehicles/sdk/j2/tests-full-output.txt", b""),
        ),
    ).decode("utf-8", errors="replace")
    raw = raw.replace("\r\n", "\n")
    match = re.search(r"Ran (\d+) tests", raw)
    if not match:
        return None
    failure = re.search(r"FAILED \(failures=(\d+)(?:, errors=(\d+))?", raw)
    skipped = re.search(r"OK \(skipped=(\d+)\)", raw)
    return {
        "tests_run": int(match.group(1)),
        "failed": (int(failure.group(1)) + int(failure.group(2) or 0)) if failure else 0,
        "skipped": int(skipped.group(1)) if skipped else len(re.findall(r"\.\.\. skipped ", raw)),
    }


def create_archive(output: Path = DEFAULT_OUTPUT, *, force: bool = False,
                   final_closeout: bool = False) -> dict[str, Any]:
    output = Path(output).resolve()
    research_output = (ROOT / ".research-output").resolve()
    try:
        output.relative_to(research_output)
    except ValueError as exc:
        raise ReviewPackageError("review ZIP must remain under ignored .research-output") from exc
    if output.exists() and not force:
        raise ReviewPackageError(f"review ZIP already exists: {output}; use --force to replace it")

    payload = _read_payload(final_closeout=final_closeout)
    git = {"branch": _git("branch", "--show-current"), "head": _git("rev-parse", "HEAD")}
    index = {
        "schema_version": 1,
        "artifact": "R5V-J.2 final closeout compact implementation review" if final_closeout else "R5V-J.2 ID27 reverse-map root-cause compact implementation review",
        "status": "FULL_PASS_CLOSED" if final_closeout else "READY_FOR_HUMAN_RUNTIME_ROOT_CAUSE_FIX",
        "git": git,
        "test_summary": _test_counts(payload),
        "files": [
            {"path": name, "size": len(data), "sha256": _sha(data)}
            for name, data in sorted(payload.items())
        ],
        "excluded": [
            "retail or patched executable binaries",
            "runtime launcher binary and generated runtime bundle",
            "game assets and Data.sma",
            "raw Broker dumps, captures, screenshots, saves, and Ghidra databases",
        ],
    }
    payload["archive-index.json"] = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            member = f"{FINAL_ZIP_ROOT if final_closeout else ZIP_ROOT}/{name}"
            info = zipfile.ZipInfo(member, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(buffer.getvalue())
    digest = _sha(buffer.getvalue())
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {output.name}\n", encoding="ascii")
    return {"status": "PASS_J2_FINAL_CLOSEOUT_ARCHIVE" if final_closeout else "PASS_J2_REVIEW_ARCHIVE", "path": str(output), "size": output.stat().st_size,
            "sha256": digest, "payload_file_count": len(index["files"]), "git": git,
            "test_summary": index["test_summary"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--final-closeout", action="store_true",
                        help="create a separate archive recording the completed J.2 closeout")
    args = parser.parse_args()
    try:
        output = args.output
        if args.final_closeout and output == DEFAULT_OUTPUT:
            output = FINAL_OUTPUT
        result = create_archive(output, force=args.force, final_closeout=args.final_closeout)
    except (OSError, ReviewPackageError, subprocess.SubprocessError, ValueError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
