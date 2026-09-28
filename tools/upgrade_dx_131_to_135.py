#!/usr/bin/env python3
"""Convert supported revision-131 vehicle DX files to revision 135.

Single-file mode writes a separate DX and JSON report. Vehicle-directory mode
converts only direct ``car.dx``, ``complete.dx``, and ``wheel.dx`` roles into a
new output directory. DXT and other resources are not copied or changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye import __version__
from master_rallye.dx_revision_upgrade import (
    DxRevisionUpgradeError,
    REVISION_131,
    REVISION_135,
    upgrade_dx_131_to_135_with_report,
    validate_existing_rev135,
)


_ROLES = ("car.dx", "complete.dx", "wheel.dx")
_TOOL_NAME = "Master Rallye DX Upgrader"


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _write_temp(path: Path, data: bytes) -> Path:
    """Stage complete bytes in a sibling temporary file without replacing output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"output path is a directory: {path}")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return temporary


def _install_temp(temporary: Path, path: Path, *, overwrite: bool) -> None:
    if overwrite:
        os.replace(temporary, path)
    else:
        # A same-directory hard link installs completed bytes without replacing
        # a file that appeared after the initial existence check.
        os.link(temporary, path)
        temporary.unlink()


def _write_atomic(path: Path, data: bytes, *, overwrite: bool) -> None:
    """Write a complete sibling temp file, then install it atomically."""
    if path.exists() and not overwrite:
        raise FileExistsError(f"output already exists: {path}")
    temporary = _write_temp(path, data)
    try:
        _install_temp(temporary, path, overwrite=overwrite)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise OSError(f"cannot read {path}: {exc}") from exc


def _upgrade_or_copy(data: bytes, source_path: Path) -> tuple[bytes, dict[str, Any]]:
    if len(data) < 8:
        raise DxRevisionUpgradeError("truncated_header", f"DX header is truncated: {source_path}")
    revision = struct.unpack_from("<I", data, 4)[0]
    if revision == REVISION_131:
        return upgrade_dx_131_to_135_with_report(data, str(source_path))
    if revision == REVISION_135:
        validation = validate_existing_rev135(data, str(source_path))
        report = {
            "status": "already_rev135_copied",
            "source_revision": REVISION_135,
            "output_revision": REVISION_135,
            "draw_records_transformed": 0,
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "output_sha256": hashlib.sha256(data).hexdigest(),
            "source_size": len(data),
            "output_size": len(data),
            "existing_rev135_validation": validation,
            "individual_output_runtime_status": "NOT_ASSESSED_BY_CONVERTER",
        }
        return data, report
    # Route all other revisions through the public converter for one canonical,
    # structured unsupported-revision diagnostic.
    return upgrade_dx_131_to_135_with_report(data, str(source_path))


def _single_file(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.input_dx is None:
        parser.error("single-file mode requires an input DX path")
    if args.output is None:
        parser.error("single-file mode requires -o/--output")
    if args.vehicle_dir is not None or args.output_dir is not None:
        parser.error("single-file and vehicle-directory modes cannot be combined")

    source = args.input_dx.resolve(strict=True)
    if not source.is_file():
        parser.error(f"input is not a file: {source}")
    output = args.output.resolve()
    if source == output:
        parser.error("input and output paths resolve to the same file; in-place conversion is refused")
    if output.suffix.lower() != ".dx":
        parser.error("output path must have a .dx extension")

    report_path = args.report.resolve() if args.report else output.with_name(output.name + ".report.json")
    if report_path in (source, output):
        parser.error("JSON report path must be distinct from both input and output DX paths")
    if args.force:
        if output.exists() and output.is_dir():
            parser.error(f"output path is a directory: {output}")
        if report_path.exists() and report_path.is_dir():
            parser.error(f"report path is a directory: {report_path}")
    else:
        if output.exists():
            parser.error(f"output already exists: {output} (use --force to replace it)")
        if report_path.exists():
            parser.error(f"report already exists: {report_path} (use --force to replace it)")

    source_bytes = _read_bytes(source)
    candidate, report = upgrade_dx_131_to_135_with_report(source_bytes, str(source))
    report["output_path"] = str(output)
    report["report_path"] = str(report_path)
    report_bytes = _json_bytes(report)
    output_temp = None
    report_temp = None
    try:
        # Finish and fsync both files before making either visible.
        output_temp = _write_temp(output, candidate)
        report_temp = _write_temp(report_path, report_bytes)

        if args.force and report_path.exists():
            # A previous sidecar must never survive beside a newly converted
            # DX if installing the replacement report later fails.
            report_path.unlink()
        _install_temp(output_temp, output, overwrite=args.force)
        output_temp = None
        try:
            _install_temp(report_temp, report_path, overwrite=args.force)
            report_temp = None
        except OSError as exc:
            if not args.force:
                try:
                    if output.is_file() and hashlib.sha256(output.read_bytes()).hexdigest() == report["output_sha256"]:
                        output.unlink()
                except OSError:
                    pass
                raise
            raise OSError(
                f"DX was installed at {output}, but its JSON report could not be installed; "
                f"the previous report was removed to prevent stale metadata: {exc}"
            ) from exc
    finally:
        for temporary in (output_temp, report_temp):
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    print(f"{_TOOL_NAME}: PASS")
    print(f"Input:    revision 131  SHA256 {report['source_sha256']}  {source}")
    print(f"Output:   revision 135  SHA256 {report['output_sha256']}  {output}")
    print(f"Draws:    {report['draw_records_transformed']} transformed; canonical parser PASS")
    print(f"Report:   {report_path}")
    return 0


def _discover_vehicle_roles(source_dir: Path) -> list[tuple[str, Path]]:
    entries: dict[str, list[Path]] = {}
    for child in source_dir.iterdir():
        if child.is_file() and child.name.casefold() in {role.casefold() for role in _ROLES}:
            entries.setdefault(child.name.casefold(), []).append(child)
    duplicates = [name for name, paths in entries.items() if len(paths) > 1]
    if duplicates:
        raise ValueError("duplicate role filenames differ only by case: " + ", ".join(duplicates))
    roles = []
    for role in _ROLES:
        paths = entries.get(role.casefold(), [])
        if paths:
            roles.append((role, paths[0]))
    if not roles:
        raise ValueError("vehicle directory contains none of car.dx, complete.dx, or wheel.dx")
    return roles


def _stage_bytes(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _vehicle_directory(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.vehicle_dir is None or args.output_dir is None:
        parser.error("vehicle-directory mode requires both --vehicle-dir and --output-dir")
    if args.input_dx is not None or args.output is not None:
        parser.error("vehicle-directory and single-file modes cannot be combined")
    if args.report is not None:
        parser.error("vehicle-directory mode always writes manifest.json inside the output directory")
    if args.force:
        parser.error("--force is supported only in single-file mode; choose a new output directory")

    source_dir = args.vehicle_dir.resolve(strict=True)
    if not source_dir.is_dir():
        parser.error(f"vehicle input is not a directory: {source_dir}")
    output_dir = args.output_dir.resolve()
    if output_dir == source_dir or output_dir in source_dir.parents or source_dir in output_dir.parents:
        parser.error("vehicle input and output directories must be separate, non-nested paths")
    if output_dir.exists():
        parser.error(f"output directory already exists: {output_dir}")

    try:
        roles = _discover_vehicle_roles(source_dir)
    except OSError as exc:
        parser.error(f"cannot inspect vehicle directory: {exc}")
    except ValueError as exc:
        parser.error(str(exc))

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
    entries: list[dict[str, Any]] = []
    try:
        for role, source_path in roles:
            source_bytes = _read_bytes(source_path)
            output_bytes, entry = _upgrade_or_copy(source_bytes, source_path)
            entry["source_path"] = str(source_path)
            entry["output_path"] = str(output_dir / role)
            entry["role"] = role[:-3]
            _stage_bytes(staging / role, output_bytes)
            entries.append(entry)

        manifest = {
            "schema_version": 1,
            "tool": _TOOL_NAME,
            "tool_version": __version__,
            "status": "PASS",
            "mode": "vehicle-directory",
            "source_directory": str(source_dir),
            "output_directory": str(output_dir),
            "converted_or_copied_dx_count": len(entries),
            "dx_files": entries,
            "non_dx_policy": "not copied; DXT and all other resources are left untouched",
            "runtime_evidence_profile": {
                "families_confirmed": ["Trooper", "Forester"],
                "this_package_runtime_status": "NOT_ASSESSED_BY_CONVERTER",
            },
        }
        _stage_bytes(staging / "manifest.json", _json_bytes(manifest))
        # Staging is a sibling, so the final directory rename stays on-volume.
        staging.rename(output_dir)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    print(f"{_TOOL_NAME}: PASS")
    print(f"Input package:  {source_dir}")
    print(f"Output package: {output_dir}")
    for entry in entries:
        print(
            f"{entry['role']}.dx: revision {entry['source_revision']} -> "
            f"{entry['output_revision']}, draws transformed {entry['draw_records_transformed']}, "
            f"parser PASS, SHA256 {entry['output_sha256']}"
        )
    print(f"Manifest: {output_dir / 'manifest.json'}")
    print("DXT and other non-DX resources were not copied or modified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dx", nargs="?", type=Path,
                        help="revision-131 vehicle DX (single-file mode)")
    parser.add_argument("-o", "--output", type=Path,
                        help="new revision-135 DX output path")
    parser.add_argument("--vehicle-dir", type=Path,
                        help="input vehicle package directory (directory mode)")
    parser.add_argument("--output-dir", type=Path,
                        help="new output directory for supported DX roles")
    parser.add_argument("--report", type=Path,
                        help="JSON report path (default: <output>.report.json)")
    parser.add_argument("--force", action="store_true",
                        help="atomically replace existing single-file output/report; never permits in-place conversion")
    parser.add_argument("--version", action="version",
                        version=f"{_TOOL_NAME} {__version__}")
    args = parser.parse_args(argv)

    if args.vehicle_dir is not None:
        try:
            return _vehicle_directory(args, parser)
        except (DxRevisionUpgradeError, OSError, ValueError) as exc:
            if isinstance(exc, DxRevisionUpgradeError):
                print(f"error [{exc.code}]: {exc}", file=sys.stderr)
            else:
                print(f"error: {exc}", file=sys.stderr)
            return 1
    if args.input_dx is None:
        parser.error("provide an input DX path or use --vehicle-dir")
    try:
        return _single_file(args, parser)
    except DxRevisionUpgradeError as exc:
        print(f"error [{exc.code}]: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (ValueError, struct.error) as exc:
        print(f"error: invalid input or path: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
