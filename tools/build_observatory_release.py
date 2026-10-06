"""Build a deterministic, standalone, allowlisted Observatory ZIP candidate."""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools/runtime"))
from observatory_version import VERSION, TOOL_NAME, PYTHON_REQUIREMENT
from broker_observatory import RETAIL_SHA256
from observatory_build_profiles import PROFILES

OUTPUT_ROOT = REPO / "dist/observatory"
FILES = {
    "MRallye-Observatory.cmd": "tools/runtime/MRallye-Observatory.cmd",
    "mr_observe.py": "tools/runtime/mr_observe.py",
    "broker_observatory.py": "tools/runtime/broker_observatory.py",
    "dev_command_trigger.py": "tools/runtime/dev_command_trigger.py",
    "observatory_version.py": "tools/runtime/observatory_version.py",
    "observatory_build_profiles.py": "tools/runtime/observatory_build_profiles.py",
    "observatory_profile_resolver.py": "tools/runtime/observatory_profile_resolver.py",
    "observatory_compatibility.py": "tools/runtime/observatory_compatibility.py",
    "data/broker-families.json": "tools/runtime/data/broker-families.json",
    "data/registry-profiles.json": "tools/runtime/data/registry-profiles.json",
    "README.md": "docs/releases/observatory-quickstart.md",
    "RELEASE-NOTES.md": f"docs/releases/observatory-{VERSION}.md",
    "NOTICE.md": "docs/releases/observatory-notice.md",
    "LICENSE": "LICENSE",
}
FORBIDDEN_EXTENSIONS = {
    ".exe", ".dll", ".pyd", ".pyc", ".sma", ".xml", ".dx", ".dxt", ".gxm", ".gxi",
    ".gxb", ".sfl", ".hnt", ".bin", ".gpr", ".gzf", ".gdt", ".zip", ".png", ".jpg",
    ".jpeg", ".wav", ".ogg", ".mp3", ".bmp", ".dds", ".fl", ".sf", ".sav", ".rep",
}
FORBIDDEN_PARTS = {"research", "research-output", "corpora", "captures", "saves", "_re-evidence", "ghidra"}
LOCAL_PATH_PATTERNS = (
    re.compile(r"(?i)(?<![a-z0-9_])[a-z]:[\\/]Game[\\/]"),
    re.compile(r"(?i)(?<![a-z0-9_])[a-z]:[\\/]Users[\\/]"),
    re.compile(r"(?i)(?<![a-z0-9_])[a-z]:[\\/].*master-rallye-re-general"),
    re.compile(r"(?i)(?<![a-z0-9_])/(?:home|Users)/"),
)
LOCAL_MODULES = {
    "mr_observe", "broker_observatory", "dev_command_trigger", "observatory_version",
    "observatory_build_profiles", "observatory_profile_resolver", "observatory_compatibility",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_forbidden(names) -> None:
    for name in names:
        path = PurePosixPath(str(name).replace("\\", "/"))
        lowered = {part.casefold() for part in path.parts}
        if (path.is_absolute() or ".." in path.parts or path.suffix.casefold() in FORBIDDEN_EXTENSIONS
                or lowered & FORBIDDEN_PARTS or path.name.casefold().startswith("mrallye_")
                or path.name.casefold() == "mrallye.exe" or path.name.casefold() == "data.sma"
                or "profile-cache" in path.name.casefold() or "local-profile" in path.name.casefold()):
            raise ValueError(f"Forbidden release or game file: {name}")


def _validate_text(name: str, data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Package input must be UTF-8 text: {name}") from exc
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"Developer-machine absolute path in package input: {name}")
    if "master-rallye-re-general\\tools" in text.casefold() or "master-rallye-re-general/tools" in text.casefold():
        raise ValueError(f"Repository checkout path in package input: {name}")
    if re.search(r"(?i)\bfrom\s+research\b|\bimport\s+research_build_profiles\b", text):
        raise ValueError(f"Repository-only research import in package input: {name}")
    return text


def validate_import_closure(payloads: dict[str, bytes]) -> None:
    available = {PurePosixPath(name).stem for name in payloads if name.endswith(".py")}
    stdlib = getattr(sys, "stdlib_module_names", set())
    for name, data in payloads.items():
        if not name.endswith(".py"):
            continue
        tree = ast.parse(data.decode("utf-8"), filename=name)
        for node in ast.walk(tree):
            module_names = []
            if isinstance(node, ast.Import):
                module_names.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_names.append(node.module.split(".", 1)[0])
            for module in module_names:
                if module in available or module in stdlib or module in sys.builtin_module_names:
                    continue
                raise ValueError(f"Unpackaged or non-stdlib import {module!r} in {name}")
    if not LOCAL_MODULES.issubset(available):
        raise ValueError("Standalone package is missing a required local Python module")


def validate_payloads(payloads: dict[str, bytes]) -> None:
    expected = set(FILES)
    if set(payloads) != expected:
        raise ValueError("Package contents differ from the explicit release allowlist")
    reject_forbidden(payloads)
    for name, data in payloads.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe package path: {name}")
        if data.startswith(b"MZ"):
            raise ValueError(f"Executable signature found in package input: {name}")
        _validate_text(name, data)
    required = {"README.md", "NOTICE.md", "LICENSE", "observatory_version.py"}
    if not required.issubset(payloads):
        raise ValueError("Public release is missing required documentation or version metadata")
    validate_import_closure(payloads)
    notice = " ".join(payloads["NOTICE.md"].decode("utf-8").casefold().split())
    if "no master rallye executable is included" not in notice or "no game assets are included" not in notice:
        raise ValueError("NOTICE must accurately state that no game executable or assets are included")


def collect_files(repo: Path) -> dict[str, bytes]:
    payloads = {}
    for target, source in FILES.items():
        reject_forbidden((target, source))
        path = repo / source
        if path.is_symlink() or not path.resolve().is_relative_to(repo.resolve()):
            raise ValueError(f"Package source escapes repository: {source}")
        data = path.read_bytes()
        if target.endswith(".cmd"):
            data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        payloads[target] = data
    validate_payloads(payloads)
    return payloads


def build_bytes(payloads: dict[str, bytes], commit: str) -> tuple[bytes, dict]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Build commit must be a full Git SHA")
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
        "schema_version": 2,
        "tool": TOOL_NAME,
        "version": VERSION,
        "archive": f"MasterRallye-Observatory-{VERSION}.zip",
        "archive_sha256": _sha(raw),
        "archive_size_bytes": len(raw),
        "supported_exact_sha256": [profile.sha256 for profile in PROFILES],
        "python_requirement": PYTHON_REQUIREMENT,
        "build_commit": commit,
        "files": [{"path": name, "size_bytes": len(data), "sha256": _sha(data)}
                  for name, data in sorted(payloads.items())],
        "game_executables": 0,
        "game_assets": 0,
        "absolute_repo_dependencies": 0,
    }
    validate_release(raw, manifest)
    return raw, manifest


def validate_release(raw: bytes, manifest: dict) -> None:
    if (manifest.get("schema_version") != 2 or manifest.get("tool") != TOOL_NAME
            or manifest.get("python_requirement") != PYTHON_REQUIREMENT
            or not re.fullmatch(r"[0-9a-f]{40}", manifest.get("build_commit", ""))
            or manifest.get("version") != VERSION
            or manifest.get("archive_sha256") != _sha(raw)
            or manifest.get("archive_size_bytes") != len(raw)
            or manifest.get("game_executables") != 0 or manifest.get("game_assets") != 0
            or manifest.get("absolute_repo_dependencies") != 0):
        raise ValueError("Release manifest identity or safety claim mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        expected = set(FILES)
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("Archive violates the explicit package allowlist")
        reject_forbidden(names)
        payloads = {name: archive.read(name) for name in names}
        validate_payloads(payloads)
        rows = {row["path"]: row for row in manifest.get("files", [])}
        if set(rows) != expected:
            raise ValueError("Release manifest file list mismatch")
        for name, data in payloads.items():
            row = rows[name]
            if row.get("size_bytes") != len(data) or row.get("sha256") != _sha(data):
                raise ValueError(f"Release file integrity mismatch: {name}")


def _clean_extraction_smoke(raw: bytes, root: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        archive.extractall(root)
    env = {key: value for key, value in os.environ.items() if key.casefold() != "pythonpath"}
    entry = root / "mr_observe.py"
    for arguments, expected in ((["--help"], "usage:"), (["--version"], VERSION),
                                (["config", "reset"], "Configuration reset."),
                                (["config", "show"], "Local configuration:")):
        result = subprocess.run([sys.executable, "-I", str(entry), *arguments], cwd=root,
                                env=env, text=True, capture_output=True, check=False)
        if result.returncode != 0 or expected.casefold() not in (result.stdout + result.stderr).casefold():
            raise ValueError(f"Clean-extraction command failed: {arguments}: {result.stderr}")
    if not (root / "observatory-data/config.json").is_file():
        raise ValueError("Clean extraction did not create local Observatory configuration")
    if os.name == "nt":
        result = subprocess.run(["cmd", "/d", "/c", str(root / "MRallye-Observatory.cmd"), "--help"],
                                cwd=root, env=env, text=True, capture_output=True, check=False)
        if result.returncode != 0 or "usage:" not in (result.stdout + result.stderr).casefold():
            raise ValueError(f"Standalone CMD launcher failed: {result.stderr}")


def clean_extraction_smoke(raw: bytes) -> None:
    # TemporaryDirectory is outside both this repository and its parent.
    with tempfile.TemporaryDirectory(prefix="mr-observatory-v021-clean-") as folder:
        root = Path(folder)
        if root.resolve().is_relative_to(REPO.resolve().parent):
            raise ValueError("Clean-extraction test location is not outside the repository tree")
        _clean_extraction_smoke(raw, root)


def _write_outputs(output: Path, archive_data: bytes, manifest_data: bytes) -> None:
    output.mkdir(parents=True, exist_ok=True)
    files = {
        f"MasterRallye-Observatory-{VERSION}.zip": archive_data,
        f"MasterRallye-Observatory-{VERSION}.manifest.json": manifest_data,
    }
    staged = []
    try:
        for name, data in files.items():
            target = output / name
            if target.is_symlink():
                raise ValueError("Release destination must not be a symlink")
            temporary = output / f".{name}.{uuid.uuid4().hex}.tmp"
            with temporary.open("xb") as stream:
                staged.append((temporary, target))
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        for temporary, target in staged:
            if target.exists() and target.read_bytes() != temporary.read_bytes():
                raise ValueError(f"Output already exists with different contents: {target.name}")
            if not target.exists():
                temporary.replace(target)
            else:
                temporary.unlink()
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        if not output.is_relative_to(OUTPUT_ROOT.resolve()):
            raise ValueError("Release output must stay inside ignored dist/observatory")
        def git(*arguments):
            return subprocess.check_output(["git", *arguments], cwd=REPO, text=True).strip()
        reject_forbidden(git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines())
        inputs = [*FILES.values(), "tools/build_observatory_release.py"]
        if git("status", "--porcelain", "--", *inputs):
            raise ValueError("Commit release inputs first so the manifest identifies the packaged source")
        payloads = collect_files(REPO)
        raw, manifest = build_bytes(payloads, git("rev-parse", "HEAD"))
        clean_extraction_smoke(raw)
        _write_outputs(output, raw, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        print(f"Candidate: Master Rallye Observatory {VERSION}\nArchive: {output / manifest['archive']}\n"
              f"Size: {manifest['archive_size_bytes']}\nSHA256: {manifest['archive_sha256']}\n"
              f"Files: {len(manifest['files'])}\nGame EXEs/assets/repository dependencies: 0")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"Observatory release build refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
