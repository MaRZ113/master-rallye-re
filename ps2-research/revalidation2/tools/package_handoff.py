#!/usr/bin/env python3
"""Create a deterministic source-only PS2-R5900-REVALIDATION2 handoff ZIP."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile

PHASE = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "PS2-R5900-REVALIDATION2"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def handoff_files() -> list[Path]:
    files = []
    for path in PHASE.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() in {".md", ".json", ".py", ".java"}:
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(PHASE).as_posix())


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_archive(output: Path) -> dict[str, object]:
    files = handoff_files()
    manifest_rows = [(path.relative_to(PHASE).as_posix(), sha256(path.read_bytes())) for path in files]
    manifest = "".join(f"{digest}  {name}\n" for name, digest in manifest_rows).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for path in files:
            name = f"{ARCHIVE_ROOT}/{path.relative_to(PHASE).as_posix()}"
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/SHA256SUMS.txt", FIXED_TIME)
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, manifest, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {
        "status": "PASS",
        "archive": str(output),
        "archive_sha256": sha256(output.read_bytes()),
        "included_file_count": len(files),
        "manifest_entries": len(manifest_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_output = PHASE.parent / "data" / "revalidation2" / "PS2-R5900-REVALIDATION2-handoff.zip"
    parser.add_argument("--output", type=Path, default=default_output)
    args = parser.parse_args()
    print(build_archive(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
