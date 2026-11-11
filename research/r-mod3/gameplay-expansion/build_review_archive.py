#!/usr/bin/env python3
"""Build a deterministic, allowlisted, source-only R-MOD3 review ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


BASE = Path("research/r-mod3/gameplay-expansion")
ALLOWLIST = (
    "README.md",
    "published-baseline.json",
    "duplicate-carid-root-cause.md",
    "per-mode-opponent-counts.md",
    "player-randomization.md",
    "forced-roster-and-grid.md",
    "forced-player-car.md",
    "cross-feature-interactions.md",
    "config-v3-proposal.ini",
    "native-hook-map.md",
    "implementation-roadmap.md",
    "evidence-and-validation.md",
    "vehicle-sdk-interoperation.md",
    "audit_evidence.py",
    "build_review_archive.py",
    "validation-report.json",
    "tests/test_audit_evidence.py",
)
ALLOWED_SUFFIXES = {".md", ".json", ".ini", ".py"}
FIXED_TIME = (2026, 10, 11, 0, 0, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(repo: Path, output: Path) -> dict[str, object]:
    repo = repo.resolve()
    output = output.resolve()
    allowed_root = (repo / ".research-output/r-mod3/gameplay-expansion").resolve()
    if output != allowed_root and allowed_root not in output.parents:
        raise ValueError("review ZIP output must stay under .research-output/r-mod3/gameplay-expansion")

    payload: list[tuple[str, bytes]] = []
    for relative in ALLOWLIST:
        source = repo / BASE / relative
        if not source.is_file():
            raise ValueError(f"required review file is missing: {source.relative_to(repo)}")
        if source.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError(f"disallowed file type in allowlist: {relative}")
        archive_path = (BASE / relative).as_posix()
        payload.append((archive_path, source.read_bytes()))

    index = {
        "schema": "r-mod3-review-archive-index-v1",
        "contents_policy": "explicit source/text allowlist; excludes game binaries, assets, captures, saves and Ghidra databases",
        "files": [
            {"path": name, "size": len(data), "sha256": sha256(data)}
            for name, data in sorted(payload)
        ],
    }
    index_bytes = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode("utf-8")
    payload.append(((BASE / "archive-index.json").as_posix(), index_bytes))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload):
            info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    result = output.read_bytes()
    return {
        "path": str(output),
        "size": len(result),
        "sha256": sha256(result),
        "payload_files": len(payload),
        "archive_index_sha256": sha256(index_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".research-output/r-mod3/gameplay-expansion/r-mod3-feasibility-review.zip"),
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output if args.output.is_absolute() else repo / args.output
    result = build(repo, output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
