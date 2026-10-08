"""Create a compact, indexed, source-only Observatory J.1 review archive."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
RESEARCH = "research/general-re/observatory-j1-live-memory"
OUTPUT_ROOT = REPO / ".research-output/observatory-j1-live-memory"
FILES = {
    "README.md": f"{RESEARCH}/README.md",
    "findings.md": f"{RESEARCH}/findings.md",
    "human-runtime-handoff.md": f"{RESEARCH}/human-runtime-handoff.md",
    "validation.md": f"{RESEARCH}/validation.md",
    "exact-build-compatibility-report.json": f"{RESEARCH}/exact-build-compatibility-report.json",
    "reference-fingerprints.json": f"{RESEARCH}/reference-fingerprints.json",
    "test-report.txt": f"{RESEARCH}/test-report.txt",
    "observatory_compatibility.py": "tools/runtime/observatory_compatibility.py",
    "broker_observatory.py": "tools/runtime/broker_observatory.py",
    "mr_observe.py": "tools/runtime/mr_observe.py",
    "observatory_profile_resolver.py": "tools/runtime/observatory_profile_resolver.py",
    "broker-families.json": "tools/runtime/data/broker-families.json",
    "observatory_live_memory_test.py": "tests/synthetic/test_observatory_live_memory.py",
    "observatory_live_memory_fixture.json": "tests/synthetic/fixtures/observatory_j1_native_dump_memory.json",
    "observatory_compatibility_test.py": "tests/synthetic/test_observatory_compatibility.py",
    "observatory_release_notes.md": "docs/releases/observatory-0.2.2-beta.md",
    "review_archive_builder.py": "tools/build_observatory_j1_review.py",
}
FORBIDDEN_SUFFIXES = {
    ".exe", ".dll", ".pyd", ".pyc", ".bin", ".sma", ".xml", ".dx", ".dxt",
    ".gxm", ".gxi", ".wav", ".mp3", ".png", ".jpg", ".jpeg", ".bmp", ".dds",
    ".sav", ".rep", ".zip", ".gzf", ".gpr",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def _read_allowlist() -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for archive_name, source_name in FILES.items():
        path = REPO / source_name
        if path.is_symlink() or not path.resolve().is_relative_to(REPO.resolve()):
            raise ValueError(f"Review source escapes checkout: {source_name}")
        data = path.read_bytes()
        payloads[archive_name] = data
    return payloads


def _validate_payloads(payloads: dict[str, bytes]) -> None:
    if set(payloads) != set(FILES):
        raise ValueError("Review contents differ from explicit source allowlist")
    for name, data in payloads.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"Forbidden review member: {name}")
        if data.startswith(b"MZ"):
            raise ValueError(f"Executable signature in review member: {name}")
        if b"Data.sma" in data or b"DataGx/Vehicles/" in data:
            raise ValueError(f"Game resource payload referenced by review member: {name}")
    report = payloads["test-report.txt"].decode("utf-8")
    if not re.search(r"Ran\s+\d+\s+tests?", report) or "OK" not in report:
        raise ValueError("Review test report is missing unittest totals or success status")


def _metadata() -> dict:
    status = _git("status", "--porcelain", "--untracked-files=all")
    changed_in_head = _git("show", "--format=", "--name-only", "HEAD").splitlines()
    diffstat = _git("show", "--stat", "--format=short", "HEAD")
    return {
        "schema_version": 1,
        "project": "Master Rallye Observatory",
        "phase": "J.1 live-memory compatibility",
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "worktree_status_porcelain": status,
        "head_changed_files": changed_in_head,
        "head_diff_summary": diffstat,
        "python_requirement": ">=3.11",
        "runtime_tests": "Windows human validation remains pending",
        "excluded_unrelated_worktree_items": [line for line in status.splitlines()
                                               if line.endswith("ps2-research.zip")],
    }


def build_bytes(payloads: dict[str, bytes], metadata: dict) -> tuple[bytes, bytes]:
    _validate_payloads(payloads)
    payloads = dict(payloads)
    payloads["project-metadata.json"] = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
    index = {
        "schema_version": 1,
        "artifact": "source-only Observatory J.1 implementation review",
        "file_count": len(payloads),
        "files": [{"path": name, "size_bytes": len(data), "sha256": _sha(data)}
                  for name, data in sorted(payloads.items())],
    }
    index_bytes = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode()
    members = {**payloads, "archive-index.json": index_bytes}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    return buffer.getvalue(), index_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=OUTPUT_ROOT / "observatory-j1-live-memory-review-2026-10-08.zip")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not output.is_relative_to(OUTPUT_ROOT.resolve()):
        print("Review output must stay under ignored .research-output/observatory-j1-live-memory", file=sys.stderr)
        return 2
    try:
        payloads = _read_allowlist()
        raw, index_bytes = build_bytes(payloads, _metadata())
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        if output.is_symlink():
            raise ValueError("Review destination must not be a symlink")
        if output.exists():
            if output.read_bytes() != raw:
                raise ValueError(f"Output already exists with different contents: {output.name}")
        else:
            output.write_bytes(raw)
        manifest = {
            "archive": output.name,
            "archive_size_bytes": len(raw),
            "archive_sha256": _sha(raw),
            "index_sha256": _sha(index_bytes),
        }
        manifest_path = output.with_suffix(".manifest.json")
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if manifest_path.is_symlink():
            raise ValueError("Review manifest destination must not be a symlink")
        if manifest_path.exists():
            if manifest_path.read_bytes() != manifest_bytes:
                raise ValueError(f"Manifest already exists with different contents: {manifest_path.name}")
        else:
            manifest_path.write_bytes(manifest_bytes)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"Review archive refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
