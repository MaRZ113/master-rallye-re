#!/usr/bin/env python3
"""Build a deterministic allowlist-only Source Cooker release ZIP."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import zlib
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
from master_rallye.version import __version__ as VERSION  # noqa: E402
from master_rallye.source_cooker import SUPPORTED_RETAIL_EXE_SHA256  # noqa: E402

ARCHIVE_NAME = f"MasterRallye-SourceCooker-v{VERSION}.zip"
TOP_LEVEL = f"MasterRallye-SourceCooker-v{VERSION}"
RUNTIME_MODULES = (
    "__init__.py", "authoring_paths.py", "bounds.py", "collision.py",
    "collision_analysis.py", "collision_oracle.py", "collision_oracle_analysis.py",
    "collision_writer.py", "demo_dx.py", "dx.py", "dx_revision_upgrade.py",
    "dx_writer.py", "dxt.py", "errors.py", "gx_image.py", "gxi.py",
    "gxm.py", "gxm_chull.py", "model.py", "sidecar.py",
    "source_cooker.py", "source_cooker_jobs.py", "junction_lifecycle.py",
    "version.py",
)
RELEASE_FILES = {
    "README.md": "docs/source-cooker.md",
    "LICENSE": "LICENSE",
    "tools/source_cooker.py": "tools/source_cooker.py",
    **{f"src/master_rallye/{name}": f"src/master_rallye/{name}" for name in RUNTIME_MODULES},
}
REQUIRED_MEMBERS = frozenset(f"{TOP_LEVEL}/{name}" for name in RELEASE_FILES)
FORBIDDEN_EXTENSIONS = frozenset({
    ".exe", ".dll", ".pyd", ".sma", ".dx", ".dxt", ".gxm", ".gxi",
    ".gxb", ".gxp", ".dxb", ".tga", ".dmp", ".dump", ".png", ".jpg",
    ".jpeg", ".bmp", ".dds", ".wav", ".ogg", ".avi", ".mpg", ".mpeg",
    ".smk", ".flc", ".vob", ".blend", ".zip", ".7z", ".rar",
})
FORBIDDEN_COMPONENTS = frozenset({
    ".git", ".github", ".research-output", "research-output", "inputs",
    "corpora", "research", "ghidra", "__pycache__", ".pytest_cache",
    "screenshots", "debugger", "procmon", "runtime-backups", "backups",
})
LOCAL_PATH_PATTERNS = (
    re.compile(rb"(?i)(?<![a-z0-9_])[a-z]:[\\/]"),
    re.compile(rb"(?i)(?<![a-z0-9_])/home/"),
    re.compile(rb"(?i)(?<![a-z0-9_])/users/"),
    re.compile(rb"(?i)\\\\[^\\/]+[\\/][^\\/]+"),
)


def validate_member_names(members: list[str] | tuple[str, ...]) -> None:
    """Fail closed on unsafe or non-allowlisted ZIP paths."""
    seen: set[str] = set()
    normalized: set[str] = set()
    for name in members:
        if not name or "\\" in name or name.startswith("/"):
            raise ValueError(f"unsafe archive member path: {name!r}")
        path = PurePosixPath(name)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError(f"unsafe archive member path: {name!r}")
        if len(path.parts) < 2 or path.parts[0] != TOP_LEVEL:
            raise ValueError(f"unexpected release top-level layout: {name!r}")
        folded = name.casefold()
        if name in seen or folded in normalized:
            raise ValueError(f"duplicate or case-colliding archive member: {name!r}")
        seen.add(name)
        normalized.add(folded)
        if any(part.casefold() in FORBIDDEN_COMPONENTS for part in path.parts):
            raise ValueError(f"forbidden directory in release archive: {name!r}")
        if path.suffix.casefold() in FORBIDDEN_EXTENSIONS or ".exe" in path.name.casefold():
            raise ValueError(f"forbidden game/research file in release archive: {name!r}")
        if path.name.casefold().startswith("data.sma"):
            raise ValueError("Data.sma and its backups are forbidden in the release")
    missing = REQUIRED_MEMBERS - seen
    if missing:
        raise ValueError("required release files missing: " + ", ".join(sorted(missing)))
    extra = seen - REQUIRED_MEMBERS
    if extra:
        raise ValueError("files outside the release allowlist: " + ", ".join(sorted(extra)))


def validate_member_content(name: str, content: bytes) -> None:
    if content.startswith(b"MZ"):
        raise ValueError(f"executable signature found in {name!r}")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"non-text or non-UTF-8 content found in {name!r}") from exc
    if name.endswith(".py"):
        compile(content.decode("utf-8"), name, "exec")
    if PurePosixPath(name).suffix.casefold() in {".md", ".json", ".txt", ".toml", ".py"}:
        # Python source legitimately contains escaped UNC/path syntax in its
        # parsing and safety code. Scan those files for concrete drive and
        # Unix home paths, while applying the UNC heuristic to user-facing
        # text and serialized metadata where it is meaningful.
        patterns = LOCAL_PATH_PATTERNS[:3] if name.endswith(".py") else LOCAL_PATH_PATTERNS
        if any(pattern.search(content) for pattern in patterns):
            raise ValueError(f"developer-machine absolute path found in {name!r}")
    if name == f"{TOP_LEVEL}/README.md":
        text = content.decode("utf-8")
        if f"Master Rallye Source Cooker {VERSION}" not in text:
            raise ValueError("README release version does not match canonical version metadata")
    if name == f"{TOP_LEVEL}/src/master_rallye/version.py":
        if f'__version__ = "{VERSION}"'.encode() not in content:
            raise ValueError("packaged version metadata does not match the release version")


def validate_release_zip(archive_path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos if not item.is_dir()]
            validate_member_names(names)
            for item in infos:
                if item.is_dir():
                    continue
                if stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError(f"symlink is forbidden in release archive: {item.filename!r}")
                validate_member_content(item.filename, archive.read(item))
            return names
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"invalid Source Cooker release ZIP: {exc}") from exc


def _synthetic_rev131() -> bytes:
    points = (
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        (2.0, 0.0, 0.0), (3.0, 0.0, 0.0), (2.0, 1.0, 0.0),
    )
    local_indices = (0, 1, 2, 0, 1, 2)
    data = bytearray(struct.pack("<4I", 0xD00D, 131, 1337, len(points)))
    for point in points:
        data += struct.pack("<3f", *point)
    for _ in points:
        data += struct.pack("<3f", 0.0, 0.0, 1.0)
    data += bytes((10, 20, 30, 255)) * len(points)
    data += struct.pack("<I", 1)
    for uv in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0),
               (0.0, 0.0), (1.0, 0.0), (0.0, 1.0)):
        data += struct.pack("<2f", *uv)
    data += struct.pack("<I", len(local_indices))
    data += struct.pack("<6H", *local_indices)
    data += struct.pack("<2I", 1, 2)

    records = (
        (0, 2, 0, (0x11, 0x22, 0x33), 7),
        (3, 2, 3, (0xA1, 0xB2, 0xC3), 5),
    )
    for vertex_base, vertex_max, index_start, flags, x_value in records:
        data += struct.pack("<5I", 2, vertex_base, vertex_max, index_start, 3)
        data += bytes(flags) + struct.pack("<II", x_value, 3)
        for value in (b"body-tga", b"normal-tga", b"Null"):
            data += struct.pack("<I", len(value)) + value
        data += struct.pack("<I", 0)

    data += struct.pack("<2I6I", 1, len(local_indices), 1, 0, 2, 4, 3, 5)
    return bytes(data)


def _clean_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key.upper() not in {"PYTHONPATH", "PYTHONHOME"}}


def _run(package_root: Path, args: list[str], *, cwd: Path, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(package_root / "tools" / "source_cooker.py"), *args],
        cwd=cwd, env=_clean_env(), text=True, capture_output=True, timeout=timeout, check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"clean extraction CLI failed: {' '.join(args)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def smoke_test_release(archive_path: Path) -> dict[str, str]:
    """Smoke the extracted tool with no repository cwd/PYTHONPATH dependency."""
    with tempfile.TemporaryDirectory(prefix="source-cooker-release-smoke-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(root)
        package_root = root / TOP_LEVEL
        help_output = " ".join(_run(package_root, ["--help"], cwd=root).stdout.split())
        if ("Supported retail executable SHA256:" not in help_output
                or SUPPORTED_RETAIL_EXE_SHA256 not in help_output
                or "The release includes no game files." not in help_output):
            raise RuntimeError("clean extraction help omits supported-build or no-game-files requirements")
        version = _run(package_root, ["--version"], cwd=root).stdout.strip()
        if version != f"Master Rallye Source Cooker {VERSION}":
            raise RuntimeError(f"unexpected Source Cooker version output: {version!r}")
        compile_result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", str(package_root / "src"), str(package_root / "tools")],
            cwd=root, env=_clean_env(), text=True, capture_output=True, check=False,
        )
        if compile_result.returncode:
            raise RuntimeError(f"clean extraction compileall failed:\n{compile_result.stdout}\n{compile_result.stderr}")

        source = root / "synthetic source"
        source.mkdir()
        fixture = _synthetic_rev131()
        for role in ("complete", "car", "wheel"):
            (source / f"{role}.dx").write_bytes(fixture)
        pixels = b"\x11\x22\x33\xff"
        synthetic_dxt = struct.pack("<5I", 0xFEED, 1, zlib.crc32(pixels) & 0xFFFFFFFF, 1, 1) + pixels
        for name in ("body-tga.dxt", "normal-tga.dxt"):
            (source / name).write_bytes(synthetic_dxt)
        _run(package_root, [
            "inventory", "--source", str(source), "--family", "Synthetic",
        ], cwd=root)
        _run(package_root, [
            "plan", "--source", str(source), "--family", "Synthetic",
            "--model-strategy", "offline-131-to-135",
        ], cwd=root)
        output = root / "synthetic output"
        _run(package_root, [
            "cook", "--source", str(source), "--family", "Synthetic", "--output", str(output),
            "--model-strategy", "offline-131-to-135",
        ], cwd=root)
        _run(package_root, ["validate-package", str(output), "--family", "Synthetic"], cwd=root)
        return {"help": "PASS", "version": "PASS", "compileall": "PASS", "synthetic_offline_conversion": "PASS"}


def build_release(output_path: Path, *, smoke_test: bool = True) -> dict[str, object]:
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="source-cooker-stage-") as temporary:
        stage_root = Path(temporary) / TOP_LEVEL
        for destination, source in RELEASE_FILES.items():
            source_path = ROOT / source
            if not source_path.is_file():
                raise FileNotFoundError(f"release input missing: {source}")
            target = stage_root / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target)
        members = sorted(path.relative_to(stage_root.parent).as_posix() for path in stage_root.rglob("*") if path.is_file())
        validate_member_names(members)
        for name in members:
            validate_member_content(name, (stage_root.parent / Path(*PurePosixPath(name).parts)).read_bytes())
        fd, temporary_zip_name = tempfile.mkstemp(prefix=output_path.name + ".", suffix=".tmp", dir=output_path.parent)
        os.close(fd)
        temporary_zip = Path(temporary_zip_name)
        try:
            with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for path in sorted(stage_root.rglob("*")):
                    if not path.is_file():
                        continue
                    name = path.relative_to(stage_root.parent).as_posix()
                    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            validated_members = validate_release_zip(temporary_zip)
            if smoke_test:
                smoke_test_release(temporary_zip)
            temporary_zip.replace(output_path)
        finally:
            temporary_zip.unlink(missing_ok=True)
    data = output_path.read_bytes()
    return {
        "path": output_path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "file_count": len(validated_members),
        "members": validated_members,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / ARCHIVE_NAME)
    parser.add_argument("--skip-smoke-test", action="store_true", help="skip isolated extraction smoke tests")
    args = parser.parse_args(argv)
    result = build_release(args.output, smoke_test=not args.skip_smoke_test)
    print(f"Release validated: {result['path']}")
    print(f"SHA256: {result['sha256']}")
    print(f"Size: {result['size']} bytes")
    print(f"Files: {result['file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
