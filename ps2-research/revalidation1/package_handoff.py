#!/usr/bin/env python3
"""Build a deterministic, proprietary-data-free PS2-REVALIDATION1 handoff."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
OUTPUT_DIR = RESEARCH_ROOT / "data" / "revalidation1"
ARCHIVE = OUTPUT_DIR / "PS2-REVALIDATION1-handoff.zip"
CHECKSUM = OUTPUT_DIR / "PS2-REVALIDATION1-handoff.zip.sha256"
MANIFEST_NAME = "ps2-research/revalidation1/HANDOFF-MANIFEST.json"
ARCHIVE_PREFIX = "ps2-research/revalidation1/"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_entries() -> list[tuple[str, bytes]]:
    entries = []
    for path in sorted(ROOT.iterdir(), key=lambda p: p.name.casefold()):
        if not path.is_file() or path.name == "HANDOFF-MANIFEST.json":
            continue
        if path.suffix.casefold() not in {".md", ".json", ".py"}:
            continue
        entries.append((ARCHIVE_PREFIX + path.name, path.read_bytes()))
    if not any(name.endswith("/final-report.md") for name, _ in entries):
        raise SystemExit("handoff source is missing final-report.md")
    return entries


def write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 0
    info.external_attr = 0
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = file_entries()
    manifest = {
        "schema": "ps2-revalidation1-handoff-manifest-v1",
        "proprietary_original_assets_included": False,
        "files": [
            {"path": name, "size": len(data), "sha256": sha256(data)}
            for name, data in entries
        ],
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(ARCHIVE, "w", allowZip64=True) as archive:
        for name, data in entries:
            write_member(archive, name, data)
        write_member(archive, MANIFEST_NAME, manifest_bytes)

    with zipfile.ZipFile(ARCHIVE, "r") as archive:
        if archive.testzip() is not None:
            raise SystemExit("ZIP CRC validation failed")
        for record in manifest["files"]:
            data = archive.read(record["path"])
            if len(data) != record["size"] or sha256(data) != record["sha256"]:
                raise SystemExit(f"handoff hash verification failed: {record['path']}")
        if archive.read(MANIFEST_NAME) != manifest_bytes:
            raise SystemExit("embedded manifest does not match generated manifest")

    digest = sha256(ARCHIVE.read_bytes())
    CHECKSUM.write_text(f"{digest}  {ARCHIVE.name}\n", encoding="ascii", newline="\n")
    print(f"archive={ARCHIVE}")
    print(f"files={len(entries)}")
    print(f"sha256={digest}")
    print("verification=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
