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
def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def verify_package_freshness(output: Path, root: Path) -> list[dict[str, str]]:
    """Fail unless every canonical Python source has one exact ZIP counterpart."""
    expected: dict[str, Path] = {}
    for source, member in source_files(root):
        if member in expected:
            raise RuntimeError(f"multiple canonical sources map to ZIP member {member}")
        expected[member] = source

    vendor_init = "master_rallye_io/vendor/__init__.py"
    expected_python = set(expected) | {vendor_init}
    checked = []
    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        python_names = [name for name in names if name.endswith(".py")]
        duplicates = sorted(name for name in set(python_names) if python_names.count(name) > 1)
        if duplicates:
            raise RuntimeError(f"duplicate packaged Python source members: {duplicates}")
        actual_python = set(python_names)
        missing = sorted(expected_python - actual_python)
        unexpected = sorted(actual_python - expected_python)
        if missing:
            raise RuntimeError(f"packaged add-on is missing Python source members: {missing}")
        if unexpected:
            raise RuntimeError(f"packaged add-on has unexpected Python source members: {unexpected}")

        vendor_bytes = archive.read(vendor_init)
        if vendor_bytes != b'"""Build-time vendor namespace."""\n':
            raise RuntimeError(f"unexpected generated vendor namespace source in ZIP member {vendor_init}")
        checked.append({"member": vendor_init, "sha256": _sha256(vendor_bytes)})
        for member, source_path in sorted(expected.items()):
            source_bytes = source_path.read_bytes()
            packaged_bytes = archive.read(member)
            source_hash = _sha256(source_bytes)
            package_hash = _sha256(packaged_bytes)
            if packaged_bytes != source_bytes:
                raise RuntimeError(
                    f"stale add-on ZIP member {member}: source {source_hash}, package {package_hash}"
                )
            checked.append({"member": member, "sha256": source_hash})
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
        "freshness_check": {
            "status": "PASS",
            "python_source_members_checked": len(freshness),
            "files": freshness,
        },
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
