#!/usr/bin/env python3
"""Build an installable legacy Blender add-on ZIP from canonical repository sources."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

EXCLUDED_PARTS = {"__pycache__", ".git", ".research-output", "dist", "tests", "research"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".dx", ".dxt", ".png", ".blend", ".gltf", ".bin"}
FIXED_TIMESTAMP = (2020, 1, 1, 0, 0, 0)
FRESHNESS_FILES = (
    "master_rallye_io/ui.py",
    "master_rallye_io/operators/import_course_xml.py",
    "master_rallye_io/course_diagnostics.py",
    "master_rallye_io/operators/export_course_race_logic.py",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def verify_package_freshness(output: Path, root: Path) -> list[dict[str, str]]:
    """Fail if key generated add-on sources do not match their ZIP members."""
    source_root = root / "blender" / "master_rallye_io"
    checked = []
    with zipfile.ZipFile(output, "r") as archive:
        names = set(archive.namelist())
        for member in FRESHNESS_FILES:
            source_path = source_root / Path(member).relative_to("master_rallye_io")
            archive_path = member
            if archive_path not in names:
                raise RuntimeError(f"packaged add-on is missing freshness target {archive_path}")
            source_bytes = source_path.read_bytes()
            packaged_bytes = archive.read(archive_path)
            source_hash = _sha256(source_bytes)
            package_hash = _sha256(packaged_bytes)
            if packaged_bytes != source_bytes:
                raise RuntimeError(
                    f"stale add-on ZIP member {archive_path}: source {source_hash}, package {package_hash}"
                )
            checked.append({"member": archive_path, "sha256": source_hash})
    return checked


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
            "artifact": "Master Rallye Blender Add-on",
            "addon_module": "master_rallye_io",
            "bundled_library": "master_rallye_io.vendor.master_rallye",
            "source_of_truth": "src/master_rallye",
            "file_count": len(files),
        }
        info = zipfile.ZipInfo("master_rallye_io/build_manifest.json", FIXED_TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, json.dumps(manifest, indent=2) + "\n")
    freshness = verify_package_freshness(output, root)
    return {
        **manifest,
        "output": str(output),
        "zip_entries": len(files) + 2,
        "freshness_check": {"status": "PASS", "files": freshness},
        "zip_sha256": _sha256(output.read_bytes()),
    }


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=repository / "dist" / "master_rallye_io.zip",
    )
    args = parser.parse_args()
    result = build(args.output.resolve(), repository)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
