"""Build the separate, local-only R-OBS3 Research Observatory package."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO / ".research-output/general-re"
DEFAULT_DIR = OUTPUT_ROOT / "observatory-research-r-obs3-final"
DEFAULT_ARCHIVE = OUTPUT_ROOT / "MasterRallye-Observatory-Research-R-OBS3-final.zip"
PACKAGE_NAME = "Master Rallye Observatory Research"
PACKAGE_VERSION = "R-OBS3"
LOCAL_PATH = re.compile(r"(?i)(?<![a-z0-9_])[a-z]:[\\/]|/(?:home|Users)/")
FORBIDDEN_SUFFIXES = {
    ".exe", ".dll", ".pyd", ".pyc", ".sma", ".xml", ".dx", ".dxt", ".gxm", ".gxi",
    ".gxb", ".sfl", ".hnt", ".bin", ".gpr", ".gzf", ".gdt", ".png", ".jpg", ".zip",
}

SOURCE_FILES = {
    "tools/runtime/mr_observe.py": "tools/runtime/mr_observe.py",
    "tools/runtime/broker_observatory.py": "tools/runtime/broker_observatory.py",
    "tools/runtime/dev_command_trigger.py": "tools/runtime/dev_command_trigger.py",
    "tools/runtime/observatory_build_profiles.py": "tools/runtime/observatory_build_profiles.py",
    "tools/runtime/observatory_profile_resolver.py": "tools/runtime/observatory_profile_resolver.py",
    "tools/runtime/observatory_version.py": "tools/runtime/observatory_version.py",
    "tools/research_build_profiles.py": "tools/research_build_profiles.py",
    "research/r-observatory-modded-builds/build-profiles.json": "research/r-observatory-modded-builds/build-profiles.json",
    "research/r-observatory-modded-builds/registry-profile.json": "research/r-observatory-modded-builds/registry-profile.json",
    "research/r-ai1/vehicle-class-map.json": "research/r-ai1/vehicle-class-map.json",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _launcher() -> bytes:
    return ("@echo off\r\nsetlocal\r\n"
            "py -3 -c \"import sys; sys.exit(0 if sys.version_info >= (3, 11) else 2)\" >nul 2>nul\r\n"
            "if not errorlevel 1 (set \"OBS_PY=py -3\" & goto python_ready)\r\n"
            "python -c \"import sys; sys.exit(0 if sys.version_info >= (3, 11) else 2)\" >nul 2>nul\r\n"
            "if errorlevel 1 goto no_python\r\n"
            "set \"OBS_PY=python\"\r\n"
            ":python_ready\r\n"
            "pushd \"%~dp0\"\r\n"
            "%OBS_PY% tools\\runtime\\mr_observe.py %*\r\n"
            "set \"observe_exit=%ERRORLEVEL%\"\r\n"
            "if not \"%observe_exit%\"==\"0\" pause\r\n"
            "popd\r\nexit /b %observe_exit%\r\n"
            ":no_python\r\n"
            "echo Research Observatory requires Python 3.11 or newer.\r\n"
            "pause\r\nexit /b 2\r\n").encode("utf-8")


def package_readme() -> bytes:
    return (f"# {PACKAGE_NAME}\n\n"
            f"Internal {PACKAGE_VERSION} package for audited retail-derived builds.\n\n"
            "Run `MRallye-Observatory-Research.cmd` or `py -3 tools/runtime/mr_observe.py`.\n"
            "Unknown builds are rejected unless exact profiles or the Broker read core audit.\n"
            "Capabilities are independent; locally audited profiles do not enable Flow Builder.\n"
            "This package contains no game executable or game assets. Captures and local\n"
            "profiles are written below the package's research-output folder.\n").encode("utf-8")


def collect_payloads() -> dict[str, bytes]:
    payloads = {target: (REPO / source).read_bytes() for target, source in SOURCE_FILES.items()}
    version_path = "tools/runtime/observatory_version.py"
    payloads[version_path] = (
        '"""Identity for the separately built internal Research Observatory."""\n\n'
        f'VERSION = "{PACKAGE_VERSION}"\n'
        f'TOOL_NAME = "{PACKAGE_NAME}"\n'
        'PYTHON_REQUIREMENT = ">=3.11"\n'
    ).encode("utf-8")
    payloads["MRallye-Observatory-Research.cmd"] = _launcher()
    payloads["README.md"] = package_readme()
    return payloads


def validate_payloads(payloads: dict[str, bytes]) -> None:
    if "MRallye.exe" in payloads or any(Path(name).suffix.casefold() in FORBIDDEN_SUFFIXES for name in payloads):
        raise ValueError("Research package contains a forbidden executable/game artifact")
    for name, data in payloads.items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"Unsafe Research package path: {name}")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Research package source is not UTF-8 text: {name}") from exc
        if LOCAL_PATH.search(text):
            raise ValueError(f"Local filesystem path in package input: {name}")


def build_archive(payloads: dict[str, bytes]) -> tuple[bytes, dict]:
    validate_payloads(payloads)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    raw = buffer.getvalue()
    manifest = {
        "schema_version": 1,
        "package": PACKAGE_NAME,
        "version": PACKAGE_VERSION,
        "archive_sha256": _sha(raw),
        "archive_size_bytes": len(raw),
        "files": [{"path": name, "size_bytes": len(data), "sha256": _sha(data)}
                  for name, data in sorted(payloads.items())],
        "contains_game_executable": False,
        "public_beta_modified": False,
    }
    verify_archive(raw, manifest)
    return raw, manifest


def verify_archive(raw: bytes, manifest: dict) -> None:
    if (manifest.get("schema_version") != 1 or manifest.get("package") != PACKAGE_NAME
            or manifest.get("version") != PACKAGE_VERSION or manifest.get("archive_sha256") != _sha(raw)
            or manifest.get("archive_size_bytes") != len(raw)
            or manifest.get("contains_game_executable") is not False):
        raise ValueError("Research package manifest identity mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        expected = {row["path"] for row in manifest["files"]}
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("Research archive contents differ from its manifest")
        validate_payloads({name: archive.read(name) for name in names})
        for row in manifest["files"]:
            data = archive.read(row["path"])
            if len(data) != row["size_bytes"] or _sha(data) != row["sha256"]:
                raise ValueError("Research package file integrity mismatch")


def write_directory(path: Path, payloads: dict[str, bytes], manifest: dict) -> None:
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists():
        expected = set(payloads) | {".research-package.json"}
        actual_static = {
            str(item.relative_to(path)).replace("\\", "/")
            for item in path.rglob("*") if item.is_file()
            and item.relative_to(path).parts[0].casefold() != "research-output"
            and item.suffix.casefold() != ".pyc"
            and "__pycache__" not in item.relative_to(path).parts
        }
        if actual_static != expected:
            raise ValueError("Research package directory already exists with unexpected contents")
        for name, data in payloads.items():
            if (path / name).read_bytes() != data:
                raise ValueError("Research package directory contains stale files; choose a new output path")
        if (path / ".research-package.json").read_bytes() != manifest_raw:
            raise ValueError("Research package manifest differs; choose a new output path")
        return
    path.mkdir(parents=True)
    try:
        for name, data in payloads.items():
            target = path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        (path / ".research-package.json").write_bytes(manifest_raw)
    except BaseException:
        # Keep a failed package directory for diagnosis; never recursively
        # remove a target that may contain user data.
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    args = parser.parse_args(argv)
    try:
        directory = args.directory.resolve()
        archive_path = args.archive.resolve()
        if (not directory.is_relative_to(OUTPUT_ROOT.resolve())
                or not archive_path.is_relative_to(OUTPUT_ROOT.resolve())):
            raise ValueError("Research package outputs must stay inside ignored .research-output/general-re")
        payloads = collect_payloads()
        raw, manifest = build_archive(payloads)
        write_directory(directory, payloads, manifest)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if archive_path.exists():
            if archive_path.read_bytes() != raw:
                raise ValueError("Research package archive already exists with different bytes")
        else:
            with archive_path.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        print(f"Directory: {directory}\nArchive: {archive_path}\nSize: {len(raw)}\nSHA256: {manifest['archive_sha256']}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Research Observatory package build refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
