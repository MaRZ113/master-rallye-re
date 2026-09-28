#!/usr/bin/env python3
"""Build, validate, and clean-extraction smoke-test the DX Upgrader release."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
ARCHIVE_NAME = f"MasterRallye-DX-Upgrader-v{VERSION}.zip"
TOP_LEVEL = f"MasterRallye-DX-Upgrader-v{VERSION}"

# Transitive runtime import closure of tools/upgrade_dx_131_to_135.py.
# Kept explicit so the package cannot accidentally grow to the research repo.
RUNTIME_MODULES = (
    "__init__.py",
    "bounds.py",
    "collision.py",
    "collision_oracle.py",
    "collision_oracle_analysis.py",
    "demo_dx.py",
    "dx.py",
    "dx_revision_upgrade.py",
    "errors.py",
    "gxm.py",
    "gxm_chull.py",
    "model.py",
    "sidecar.py",
    "version.py",
)

RELEASE_FILES = {
    "README.md": "docs/dx-upgrader-release-readme.md",
    "LICENSE": "LICENSE",
    "RELEASE-NOTES.md": "release/dx-upgrader-v0.1.0.md",
    "docs/restoring-demo-vehicles.md": "docs/restoring-demo-vehicles.md",
    "tools/upgrade_dx_131_to_135.py": "tools/upgrade_dx_131_to_135.py",
    **{
        f"src/master_rallye/{name}": f"src/master_rallye/{name}"
        for name in RUNTIME_MODULES
    },
}
REQUIRED_MEMBERS = frozenset(f"{TOP_LEVEL}/{name}" for name in RELEASE_FILES)
FORBIDDEN_EXTENSIONS = frozenset({
    ".gxm", ".gxi", ".gxb", ".gxp", ".dx", ".dxt", ".dxb", ".sfl",
    ".hnt", ".exe", ".dll", ".pyd", ".sma", ".tga", ".blend", ".dmp",
    ".dump", ".png", ".jpg", ".jpeg", ".bmp", ".dds", ".wav", ".ogg",
})
FORBIDDEN_COMPONENTS = frozenset({
    ".git", ".github", ".research-output", "research", "inputs", "corpora",
    "ghidra", "__pycache__", ".pytest_cache", "debugger", "procmon",
    "screenshots", "runtime-backups", "backups",
})
LOCAL_PATH_PATTERNS = (
    re.compile(rb"(?i)(?<![a-z0-9_])[a-z]:[\\/]"),
    re.compile(rb"(?i)/(?:home|Users)/"),
)


def validate_member_names(members: list[str] | tuple[str, ...]) -> None:
    """Require exactly the curated file set under one safe top-level folder."""
    seen: set[str] = set()
    for name in members:
        if (not name or "\\" in name or name.startswith("/") or "//" in name
                or re.match(r"(?i)^[a-z]:", name)):
            raise ValueError(f"unsafe archive member path: {name!r}")
        path = PurePosixPath(name)
        if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
            raise ValueError(f"unsafe archive member path: {name!r}")
        if len(path.parts) < 2 or path.parts[0] != TOP_LEVEL:
            raise ValueError(f"unexpected release top-level layout: {name!r}")
        if name in seen:
            raise ValueError(f"duplicate archive member: {name!r}")
        seen.add(name)
        if any(part.lower() in FORBIDDEN_COMPONENTS for part in path.parts):
            raise ValueError(f"forbidden directory in release archive: {name!r}")
        if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
            raise ValueError(f"forbidden game or executable file: {name!r}")
        if path.name.lower().startswith("data.sma") or ".exe" in path.name.lower():
            raise ValueError(f"forbidden game archive or executable name: {name!r}")
    missing = REQUIRED_MEMBERS - seen
    if missing:
        raise ValueError("required release files missing: " + ", ".join(sorted(missing)))
    unexpected = seen - REQUIRED_MEMBERS
    if unexpected:
        raise ValueError("files outside the positive release allowlist: " + ", ".join(sorted(unexpected)))


def validate_member_content(name: str, content: bytes) -> None:
    """Reject binary payloads, local paths, and invalid shipped Python."""
    if content.startswith(b"MZ"):
        raise ValueError(f"executable signature found in {name!r}")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"non-text or non-UTF-8 content found in {name!r}") from exc
    if Path(name).suffix.lower() == ".py":
        try:
            compile(text, name, "exec")
        except SyntaxError as exc:
            raise ValueError(f"invalid Python source in {name!r}: {exc}") from exc
    if any(pattern.search(content) for pattern in LOCAL_PATH_PATTERNS):
        raise ValueError(f"machine-specific absolute path found in {name!r}")


def validate_release_zip(archive_path: Path | str) -> list[str]:
    """Fail closed on unexpected, unsafe, or proprietary ZIP content."""
    archive_path = Path(archive_path)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if any(info.is_dir() for info in infos):
                raise ValueError("explicit directory entries are not allowed in the release ZIP")
            names = [info.filename for info in infos]
            validate_member_names(names)
            contents: dict[str, bytes] = {}
            for info in infos:
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError(f"symbolic link forbidden in release: {info.filename!r}")
                content = archive.read(info)
                validate_member_content(info.filename, content)
                contents[info.filename] = content
            readme = contents[f"{TOP_LEVEL}/README.md"].decode("utf-8")
            if "Master Rallye DX Upgrader v0.1.0" not in readme:
                raise ValueError("release README has the wrong product version")
            tool = contents[f"{TOP_LEVEL}/tools/upgrade_dx_131_to_135.py"].decode("utf-8")
            if '_TOOL_NAME = "Master Rallye DX Upgrader"' not in tool:
                raise ValueError("release CLI has the wrong public name")
            version_source = contents[f"{TOP_LEVEL}/src/master_rallye/version.py"].decode("utf-8")
            if '__version__ = "0.1.0"' not in version_source:
                raise ValueError("release package version is not 0.1.0")
            return names
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError(f"invalid release ZIP: {exc}") from exc


def _synthetic_rev131_fixture() -> bytes:
    """Build a tiny test-only vehicle DX fixture; never read corpus assets."""
    import struct

    data = bytearray(struct.pack("<4I", 0xD00D, 131, 1337, 4))
    positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                 (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
    for position in positions:
        data += struct.pack("<3f", *position)
    for _ in positions:
        data += struct.pack("<3f", 0.0, 0.0, 1.0)
    data += bytes((1, 2, 3, 255)) * 4
    data += struct.pack("<I", 1)
    for uv in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)):
        data += struct.pack("<2f", *uv)
    indices = (0, 1, 2, 1, 3, 2)
    data += struct.pack("<I6H", len(indices), *indices)
    data += struct.pack("<II5I", 1, 1, 2, 0, 3, 0, len(indices))
    data += bytes((0x11, 0x22, 0x33)) + struct.pack("<II", 7, 1)
    data += struct.pack("<I", 4) + b"body" + struct.pack("<I", 0)
    data += struct.pack("<2I6I", 1, len(indices), 1, 0, 2, 3, 1, 2)
    return bytes(data)


def _clean_env() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    return environment


def _run_smoke(package_root: Path, args: list[str], *, expected_version: str | None = None) -> str:
    result = subprocess.run(
        [sys.executable, "tools/upgrade_dx_131_to_135.py", *args],
        cwd=package_root,
        env=_clean_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"clean-extraction command failed: {args!r}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    if expected_version is not None and result.stdout.strip() != expected_version:
        raise RuntimeError(f"unexpected --version output: {result.stdout.strip()!r}")
    return result.stdout


def smoke_test_release(archive_path: Path | str) -> None:
    """Exercise packaged CLI, README commands, parser, and compileall in isolation."""
    archive_path = Path(archive_path).resolve()
    validate_release_zip(archive_path)
    with tempfile.TemporaryDirectory(prefix="dx-upgrader-release-smoke-") as temporary:
        temporary_root = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(temporary_root)
        package_root = temporary_root / TOP_LEVEL
        version = _run_smoke(
            package_root,
            ["--version"],
            expected_version=f"Master Rallye DX Upgrader {VERSION}",
        )
        del version
        help_text = _run_smoke(package_root, ["--help"])
        if "--vehicle-dir" not in help_text:
            raise RuntimeError("clean-extraction --help omitted vehicle-directory mode")

        # Run both Quick Start commands verbatim against a synthetic fixture.
        demo_folder = package_root / "DemoVehicle"
        demo_folder.mkdir()
        (demo_folder / "car.dx").write_bytes(_synthetic_rev131_fixture())
        _run_smoke(
            package_root,
            ["DemoVehicle\\car.dx", "-o", "Converted\\car.dx"],
        )
        _run_smoke(
            package_root,
            ["--vehicle-dir", "DemoVehicle", "--output-dir", "DemoVehicle-Rev135"],
        )
        if not (package_root / "Converted" / "car.dx.report.json").is_file():
            raise RuntimeError("single-file Quick Start did not create its JSON report")
        if not (package_root / "DemoVehicle-Rev135" / "manifest.json").is_file():
            raise RuntimeError("directory Quick Start did not create its manifest")

        validation_code = (
            "import sys; sys.path.insert(0, 'src'); "
            "from pathlib import Path; "
            "from master_rallye.dx_revision_upgrade import validate_generated_rev135; "
            "r=validate_generated_rev135(Path('Converted/car.dx').read_bytes()); "
            "assert r['status']=='PASS' and r['revision']==135"
        )
        validation = subprocess.run(
            [sys.executable, "-c", validation_code],
            cwd=package_root,
            env=_clean_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        if validation.returncode:
            raise RuntimeError(
                "clean-extraction generated DX validation failed:\n"
                f"stdout:\n{validation.stdout}\nstderr:\n{validation.stderr}"
            )
        compile_result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "src", "tools"],
            cwd=package_root,
            env=_clean_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        if compile_result.returncode:
            raise RuntimeError(
                "clean-extraction compileall failed:\n"
                f"stdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
            )


def _write_checksums(archive_path: Path, checksum_path: Path) -> str:
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"{digest}  {archive_path.name}\n".encode("ascii")
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{checksum_path.name}.", suffix=".tmp", dir=checksum_path.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(content)
        temporary.replace(checksum_path)
    finally:
        temporary.unlink(missing_ok=True)
    return digest


def build_release(
    output_path: Path | str,
    *,
    smoke_test: bool = True,
    checksum_path: Path | str | None = None,
) -> dict[str, object]:
    """Build a deterministic positive-allowlist ZIP and its SHA256 sidecar."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dx-upgrader-release-stage-") as stage_name:
        stage_root = Path(stage_name) / TOP_LEVEL
        for destination, source in RELEASE_FILES.items():
            source_path = ROOT / source
            if not source_path.is_file():
                raise FileNotFoundError(f"release input missing: {source}")
            target_path = stage_root / destination
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)

        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
        )
        os.close(fd)
        temporary_zip = Path(temporary_name)
        try:
            with zipfile.ZipFile(
                temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
            ) as archive:
                for path in sorted(stage_root.rglob("*")):
                    if not path.is_file():
                        continue
                    member = path.relative_to(stage_root.parent).as_posix()
                    info = zipfile.ZipInfo(member, date_time=(2026, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(
                        info,
                        path.read_bytes(),
                        compress_type=zipfile.ZIP_DEFLATED,
                        compresslevel=9,
                    )
            members = validate_release_zip(temporary_zip)
            if smoke_test:
                smoke_test_release(temporary_zip)
            temporary_zip.replace(output_path)
        finally:
            temporary_zip.unlink(missing_ok=True)

    checksum_path = Path(checksum_path) if checksum_path else output_path.with_name("SHA256SUMS.txt")
    digest = _write_checksums(output_path, checksum_path)
    data = output_path.read_bytes()
    return {
        "path": output_path,
        "sha256": digest,
        "size": len(data),
        "file_count": len(members),
        "members": members,
        "checksum_path": checksum_path.resolve(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / ARCHIVE_NAME,
        help=f"output ZIP path (default: dist/{ARCHIVE_NAME})",
    )
    parser.add_argument(
        "--checksums",
        type=Path,
        default=None,
        help="checksum file path (default: SHA256SUMS.txt beside the ZIP)",
    )
    parser.add_argument("--skip-smoke-test", action="store_true", help="skip isolated CLI/README smoke tests")
    args = parser.parse_args(argv)
    result = build_release(
        args.output,
        smoke_test=not args.skip_smoke_test,
        checksum_path=args.checksums,
    )
    print(f"Release validated: {result['path']}")
    print(f"SHA256: {result['sha256']}")
    print(f"Size: {result['size']} bytes")
    print(f"Files: {result['file_count']}")
    print(f"Checksums: {result['checksum_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
