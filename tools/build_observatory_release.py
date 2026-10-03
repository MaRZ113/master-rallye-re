"""Deterministic allowlisted Python ZIP; no publication or game files."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools/runtime"))
from observatory_version import VERSION, TOOL_NAME, PYTHON_REQUIREMENT
from broker_observatory import RETAIL_SHA256

FILES = {
    "MRallye-Observatory.cmd": "tools/runtime/MRallye-Observatory.cmd",
    "mr_observe.py": "tools/runtime/mr_observe.py",
    "broker_observatory.py": "tools/runtime/broker_observatory.py",
    "dev_command_trigger.py": "tools/runtime/dev_command_trigger.py",
    "observatory_version.py": "tools/runtime/observatory_version.py",
    "README.md": "docs/observatory-quickstart.md",
    "RELEASE-NOTES.md": f"docs/releases/observatory-{VERSION}.md",
    "NOTICE.md": "docs/releases/observatory-notice.md",
}
FORBIDDEN_SUFFIXES = {".exe", ".dll", ".pyd", ".pyc", ".sma", ".xml", ".dx", ".dxt", ".gxm", ".gxi", ".gxb",
                      ".sfl", ".hnt", ".bin", ".gpr", ".gzf", ".gdt", ".zip", ".png", ".jpg",
                      ".wav", ".ogg", ".mp3", ".bmp", ".dds", ".fl", ".sf"}
LOCAL_PATH = re.compile(r"(?i)(?<![a-z0-9_])[a-z]:[\\/]|/(?:home|Users)/")


def reject_forbidden(paths) -> None:
    for name in paths:
        path = Path(name)
        if (path.suffix.casefold() in FORBIDDEN_SUFFIXES
                or any(part.casefold() in {"research-output", "captures", "_re-evidence", "datagame", "datagx", "datascene"} for part in path.parts)
                or any(part.casefold().endswith(".rep") for part in path.parts)
                or path.name.casefold().endswith((".asm.txt", ".c.txt", ".dump.txt", ".dump.json"))
                or path.name.casefold() in {"config.json", "runtime-config.json", "data.sma"}):
            raise ValueError(f"Forbidden release/staged file: {name}")


def collect_files(repo: Path) -> dict[str, bytes]:
    payloads = {}
    mapping = dict(FILES)
    if (repo / "LICENSE").is_file():
        mapping["LICENSE"] = "LICENSE"
    for target, source in mapping.items():
        reject_forbidden([target, source])
        path = repo / source
        if path.is_symlink() or not path.resolve().is_relative_to(repo.resolve()):
            raise ValueError(f"Source escapes release root: {source}")
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if LOCAL_PATH.search(text):
            raise ValueError(f"Absolute machine path in release input: {source}")
        if target.endswith(".cmd"):
            text = text.replace("\n", "\r\n")
        payloads[target] = text.encode("utf-8")
    return payloads


def build_bytes(payloads: dict[str, bytes], commit: str) -> tuple[bytes, dict]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Build commit must be a full Git SHA")
    reject_forbidden(payloads)
    expected = set(FILES) | ({"LICENSE"} if "LICENSE" in payloads else set())
    if set(payloads) != expected:
        raise ValueError("Package contents differ from the explicit release allowlist")
    for name, data in payloads.items():
        if LOCAL_PATH.search(data.decode("utf-8")):
            raise ValueError(f"Absolute machine path in package: {name}")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(payloads):
            info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payloads[name], compresslevel=9)
    raw = buffer.getvalue()
    manifest = {
        "schema_version": 1, "tool": TOOL_NAME, "version": VERSION,
        "archive": f"MasterRallye-Observatory-{VERSION}.zip",
        "archive_sha256": hashlib.sha256(raw).hexdigest(), "archive_size_bytes": len(raw),
        "supported_game_sha256": RETAIL_SHA256, "python_requirement": PYTHON_REQUIREMENT,
        "build_commit": commit,
        "files": [{"path": name, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(payloads.items())],
    }
    validate_release(raw, manifest)
    return raw, manifest


def validate_release(raw: bytes, manifest: dict) -> None:
    if (manifest["schema_version"] != 1 or manifest["tool"] != TOOL_NAME
            or manifest["python_requirement"] != PYTHON_REQUIREMENT
            or not re.fullmatch(r"[0-9a-f]{40}", manifest["build_commit"])
            or manifest["version"] != VERSION or manifest["supported_game_sha256"] != RETAIL_SHA256
            or manifest["archive_sha256"] != hashlib.sha256(raw).hexdigest()
            or manifest["archive_size_bytes"] != len(raw)):
        raise ValueError("Release manifest identity mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) != len(manifest["files"]) or set(names) != {row["path"] for row in manifest["files"]}:
            raise ValueError("Release manifest/archive file mismatch")
        if set(names) not in (set(FILES), set(FILES) | {"LICENSE"}):
            raise ValueError("Archive violates release allowlist")
        reject_forbidden(names)
        for row in manifest["files"]:
            data = archive.read(row["path"])
            if len(data) != row["size_bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("Release file integrity mismatch")
            if LOCAL_PATH.search(data.decode("utf-8")):
                raise ValueError("Absolute machine path in archive")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "dist/observatory")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        if not output.is_relative_to((REPO / "dist").resolve()):
            raise ValueError("Release output must stay inside this checkout's dist directory")
        def git(*arguments):
            return subprocess.check_output(["git", *arguments], cwd=REPO, text=True).strip()
        reject_forbidden(git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines())
        inputs = [*FILES.values(), "tools/build_observatory_release.py"]
        if (REPO / "LICENSE").exists():
            inputs.append("LICENSE")
        if git("status", "--porcelain", "--", *inputs):
            raise ValueError("Commit release inputs first so build_commit identifies the packaged source")
        raw, manifest = build_bytes(collect_files(REPO), git("rev-parse", "HEAD"))
        output.mkdir(parents=True, exist_ok=True)
        archive = output / manifest["archive"]
        manifest_path = output / (archive.stem + ".manifest.json")
        for target in (archive, manifest_path):
            if target.is_symlink():
                raise ValueError("Release destination must not be a symlink")
        with tempfile.TemporaryDirectory(dir=output) as temporary:
            folder = Path(temporary)
            (folder / archive.name).write_bytes(raw)
            (folder / manifest_path.name).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (folder / archive.name).replace(archive)
            (folder / manifest_path.name).replace(manifest_path)
        print(f"Archive: {archive}\nBytes: {len(raw)}\nSHA256: {manifest['archive_sha256']}\nManifest: {manifest_path}")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Release build refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
