#!/usr/bin/env python3
"""Create a compact source-only review archive for V-LAUNCH1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".research-output/vehicles/vmesh4/vlaunch1-final/vlaunch1-source-review.zip"
FILES = (
    "runtime_launcher/CMakeLists.txt",
    "runtime_launcher/src/main.cpp",
    "tests/synthetic/test_addon_sdk_runtime.py",
    "tools/package_vlaunch1_review.py",
    "research/vehicles/sdk/compatibility.md",
    "research/vehicles/sdk/loader-decision.md",
    "research/vehicles/sdk/runtime-deployment.md",
    "research/vehicles/sdk/vlaunch1/graphics-proxy-compatibility.md",
    "research/vehicles/sdk/vlaunch1/validation.md",
)
FORBIDDEN_SUFFIXES = {".exe", ".dll", ".dx", ".dxt", ".sma", ".sav", ".dump", ".bin"}
FIXED_TIME = (2026, 10, 21, 0, 0, 0)


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def build() -> Path:
    members: dict[str, bytes] = {}
    for relative in FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"binary/proprietary file is not permitted: {relative}")
        members[relative.replace("\\", "/")] = path.read_bytes()
    readme = (
        "V-LAUNCH1 source review archive\n\n"
        "This source-only package documents the launcher D3D8 compatibility change. "
        "It excludes the candidate launcher executable and all game/proxy binaries and assets.\n\n"
        "See research/vehicles/sdk/vlaunch1/graphics-proxy-compatibility.md for the exact human test recipe.\n"
    ).encode("utf-8")
    members["README.txt"] = readme
    metadata = {
        "archive_kind": "V-LAUNCH1 compact source review",
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "included_files": {
            name: {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(members.items())
        },
        "excluded": ["retail executable", "graphics proxy DLLs", "runtime vehicle assets", "user saves", "raw captures"],
    }
    members["archive-index.json"] = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return OUTPUT


if __name__ == "__main__":
    result = build()
    digest = hashlib.sha256(result.read_bytes()).hexdigest()
    print(json.dumps({"archive": str(result), "size": result.stat().st_size, "sha256": digest}, indent=2))
