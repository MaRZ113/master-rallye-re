#!/usr/bin/env python3
"""Build a compact, source-only R-MOD1 implementation review archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".research-output" / "r-mod1"
FIXED_FILES = (
    "src/native/rmod1/core.hpp",
    "tests/rmod1/core_tests.cpp",
    "tests/synthetic/test_r_mod1_core.py",
    "tests/synthetic/test_r_mod1_composition.py",
    "tools/r_mod1_composition_audit.py",
    "tools/r_mod1_core_tests.ps1",
    "tools/build_r_mod1_review.py",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_text(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def payload_paths() -> list[Path]:
    paths = [ROOT / item for item in FIXED_FILES]
    docs = ROOT / "research" / "r-mod1"
    paths.extend(
        path for path in docs.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".ini"}
    )
    unique = sorted({path.resolve() for path in paths}, key=lambda path: path.relative_to(ROOT).as_posix())
    for path in unique:
        path.relative_to(ROOT)
        if path.suffix.lower() not in {".md", ".json", ".ini", ".hpp", ".cpp", ".py", ".ps1"}:
            raise ValueError(f"Refusing non-source review payload: {path.name}")
        if not path.is_file():
            raise FileNotFoundError(path)
    return unique


def write_archive(output: Path, archive_date: str | None = None) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    contents: list[tuple[str, bytes]] = []
    file_rows = []
    for path in payload_paths():
        relative = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        data.decode("utf-8")
        contents.append((relative, data))
        file_rows.append({"path": relative, "size": len(data), "sha256": sha256(data)})

    metadata = {
        "archive_format": 1,
        "project": "R-MOD1 Randomizer and AI Extender",
        "archive_date": archive_date or date.today().isoformat(),
        "branch": git_text("branch", "--show-current"),
        "head": git_text("rev-parse", "HEAD"),
        "worktree_status_porcelain": git_text("status", "--porcelain=v1", "--untracked-files=all").splitlines(),
        "source_only": True,
        "files": file_rows,
    }
    index_data = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, data in [*contents, ("archive-index.json", index_data)]:
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            archive.writestr(info, data)
    return {
        "path": str(output),
        "size": output.stat().st_size,
        "sha256": sha256(output.read_bytes()),
        "payload_files": len(file_rows),
        "index_sha256": sha256(index_data),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--date", help="Archive date YYYY-MM-DD; defaults to local date.")
    args = parser.parse_args()
    output = args.output or DEFAULT_OUTPUT / f"r-mod1-implementation-review-{args.date or date.today().isoformat()}.zip"
    print(json.dumps(write_archive(output.resolve(), args.date), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
