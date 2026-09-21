#!/usr/bin/env python3
"""Build an installable legacy Blender add-on ZIP from canonical repository sources."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

EXCLUDED_PARTS = {"__pycache__", ".git", ".research-output", "dist", "tests", "research"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".dx", ".dxt", ".png", ".blend", ".gltf", ".bin"}
FIXED_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def source_files(root: Path):
    addon = root / "blender" / "master_rallye_io"
    library = root / "src" / "master_rallye"
    roots = (
        (addon, Path("master_rallye_io")),
        (library, Path("master_rallye_io/vendor/master_rallye")),
    )
    for base, archive_root in roots:
        for path in sorted(base.rglob("*.py")):
            relative = path.relative_to(base)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            yield path, (archive_root / relative).as_posix()


def build(output: Path, root: Path) -> dict:
    files = list(source_files(root))
    if not files:
        raise RuntimeError("no add-on files found")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        vendor_info = zipfile.ZipInfo("master_rallye_io/vendor/__init__.py", FIXED_TIMESTAMP)
        vendor_info.compress_type = zipfile.ZIP_DEFLATED
        vendor_info.external_attr = 0o644 << 16
        archive.writestr(vendor_info, b'"""Build-time vendor namespace."""\n')
        for source, target in files:
            info = zipfile.ZipInfo(target, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
        manifest = {
            "artifact": "Master Rallye R2 Blender add-on",
            "addon_module": "master_rallye_io",
            "bundled_library": "master_rallye_io.vendor.master_rallye",
            "source_of_truth": "src/master_rallye",
            "file_count": len(files),
        }
        info = zipfile.ZipInfo("master_rallye_io/build_manifest.json", FIXED_TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, json.dumps(manifest, indent=2) + "\n")
    return {**manifest, "output": str(output), "zip_entries": len(files) + 2}


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=repository / "dist" / "master_rallye_io-r2.zip",
    )
    args = parser.parse_args()
    result = build(args.output.resolve(), repository)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
