#!/usr/bin/env python3
"""Build and validate the curated Vehicle Composer release archive."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
from master_rallye.version import __version__ as VERSION  # noqa: E402

ARCHIVE_NAME = f"MasterRallye-VehicleComposer-v{VERSION}.zip"
TOP_LEVEL = f"MasterRallye-VehicleComposer-v{VERSION}"
RUNTIME_MODULES = (
    "__init__.py", "assets.py", "bounds.py", "collision.py", "dx.py",
    "dx_writer.py", "dxt.py", "errors.py", "model.py", "r4e_writer.py",
    "sidecar.py", "vehicle_composition.py", "vehicle_config_analysis.py",
    "vehicle_config_schema.py", "vehicle_family_binder.py",
    "vehicle_family_broker.py", "vehicle_model_inventory.py",
    "vehicle_packaging.py", "vehicle_physics_binding.py", "version.py",
)
RELEASE_FILES = {
    "README.md": "docs/vehicle-composer.md",
    "LICENSE": "LICENSE",
    "tools/vehicle_composer.py": "tools/vehicle_composer.py",
    "tools/physics_bind.py": "tools/physics_bind.py",
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
    ".flac", ".avi", ".mpg", ".mpeg", ".smk", ".flc", ".vob", ".dat",
    ".pak", ".idx", ".tbl", ".bin", ".obj", ".mtl",
})
FORBIDDEN_COMPONENTS = frozenset({
    ".git", ".github", ".research-output", "research", "corpora", "ghidra",
    "__pycache__", ".pytest_cache", "debugger", "procmon", "screenshots",
    "runtime-backups", "backups",
})
LOCAL_PATH_PATTERNS = (
    re.compile(rb"(?i)(?<![a-z0-9_])[a-z]:[\\/]"),
    re.compile(rb"(?i)\\\\[^\\/]+[\\/][^\\/]+"),
)


def validate_member_names(members: list[str] | tuple[str, ...]) -> None:
    """Reject unsafe, incomplete, or non-curated archive member names."""
    seen: set[str] = set()
    for name in members:
        if not name or "\\" in name or name.startswith("/"):
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
        if path.name.lower().startswith("data.sma"):
            raise ValueError("Data.sma archives or backups must never be included")
        if ".exe" in path.name.lower():
            raise ValueError(f"executable name forbidden in release: {name!r}")
    missing = REQUIRED_MEMBERS - seen
    if missing:
        raise ValueError("required release files missing: " + ", ".join(sorted(missing)))
    unexpected = seen - REQUIRED_MEMBERS
    if unexpected:
        raise ValueError("files outside the release allowlist: " + ", ".join(sorted(unexpected)))


def validate_member_content(name: str, content: bytes) -> None:
    """Reject executable signatures and leaked machine-specific absolute paths."""
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
    text_suffixes = {".md", ".json", ".txt", ".yaml", ".yml", ".toml"}
    if Path(name).suffix.lower() in text_suffixes and any(
        pattern.search(content) for pattern in LOCAL_PATH_PATTERNS
    ):
        raise ValueError(f"machine-specific absolute path found in {name!r}")


def validate_release_zip(archive_path: Path) -> list[str]:
    """Fail closed if a ZIP is malformed or contains anything outside policy."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            validate_member_names(names)
            for info in infos:
                if info.is_dir():
                    continue
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError(f"symbolic link forbidden in release: {info.filename!r}")
                validate_member_content(info.filename, archive.read(info))
            return names
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError(f"invalid release ZIP: {exc}") from exc


def _smoke_test(archive_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="vehicle-composer-release-") as temp_name:
        temp_root = Path(temp_name)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(temp_root)
        package_root = temp_root / TOP_LEVEL
        for script, args in (
            ("tools/vehicle_composer.py", ["--help"]),
            ("tools/vehicle_composer.py", ["--version"]),
            ("tools/physics_bind.py", ["--help"]),
        ):
            result = subprocess.run(
                [sys.executable, str(package_root / script), *args],
                cwd=temp_root,
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                raise RuntimeError(
                    f"clean extraction smoke failed for {script} {' '.join(args)}:\n"
                    f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )
            if args == ["--version"] and result.stdout.strip() != (
                f"Master Rallye Vehicle Composer {VERSION}"
            ):
                raise RuntimeError(f"unexpected --version output: {result.stdout!r}")


def build_release(output_path: Path, *, smoke_test: bool = True) -> dict[str, object]:
    """Create the deterministic allowlist-only release ZIP and validate it."""
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vehicle-composer-stage-") as stage_name:
        stage_root = Path(stage_name) / TOP_LEVEL
        for destination, source in RELEASE_FILES.items():
            source_path = ROOT / source
            if not source_path.is_file():
                raise FileNotFoundError(f"release input missing: {source}")
            target_path = stage_root / destination
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)

        fd, temp_name = tempfile.mkstemp(
            prefix=output_path.name + ".", suffix=".tmp", dir=output_path.parent
        )
        os.close(fd)
        temporary_zip = Path(temp_name)
        try:
            with zipfile.ZipFile(
                temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
            ) as archive:
                for path in sorted(stage_root.rglob("*")):
                    if not path.is_file():
                        continue
                    relative = path.relative_to(stage_root.parent).as_posix()
                    info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members = validate_release_zip(temporary_zip)
            if smoke_test:
                _smoke_test(temporary_zip)
            temporary_zip.replace(output_path)
        finally:
            temporary_zip.unlink(missing_ok=True)
    data = output_path.read_bytes()
    return {
        "path": output_path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "file_count": len(members),
        "members": members,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "dist" / ARCHIVE_NAME,
        help="output ZIP path (default: dist/MasterRallye-VehicleComposer-v0.1.0.zip)",
    )
    parser.add_argument("--skip-smoke-test", action="store_true", help="skip isolated CLI smoke tests")
    args = parser.parse_args(argv)
    result = build_release(args.output, smoke_test=not args.skip_smoke_test)
    print(f"Release validated: {result['path']}")
    print(f"SHA256: {result['sha256']}")
    print(f"Size: {result['size']} bytes")
    print(f"Files: {result['file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
