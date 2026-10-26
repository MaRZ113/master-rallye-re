"""Build a private source-only Sound Bank Lab handoff with a strict allowlist."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ["gt_sound_lab.py", "gt_sound_lab_server.py", "gt_sound_lab.html", "start_gt_sound_lab.ps1",
         "gt_sound_jam.py", "gt_sound_native_evidence.py", "gt3_sound_lab.py", "gt3_audio_inspect.py",
         "gt3_ui_icon.py", "gt4_audio_extract.py", "inspect_gt4_core.py", "package_gt_sound_lab.py"]
TESTS = ["test_gt_sound_lab.py", "test_gt_sound_jam.py", "test_gt3_sound_lab.py", "test_gt4_audio_extract.py"]


def build(stage, archive):
    stage, archive = Path(stage).resolve(), Path(archive).resolve()
    if stage.exists() or archive.exists() or archive.is_relative_to(stage):
        raise ValueError("new separate source stage and archive paths required")
    # Constrain packaging to this research worktree; never write into the corpus.
    if not stage.is_relative_to(ROOT / "scratch") or not archive.is_relative_to(ROOT / ".research-output"):
        raise ValueError("source stage must be in scratch; archive in .research-output")
    files = [ROOT / "tools" / p for p in TOOLS]
    files += [ROOT / "tests/synthetic" / p for p in TESTS]
    files += list((ROOT / "research/vehicles/gt-sound-lab").glob("*.md"))
    files += [ROOT / "research/vehicles/gt-sound-lab/mapping.schema.json"]
    files += [ROOT / "src/master_rallye/addon_sdk" / p for p in ("gt4_spec.py", "gt4_source.py")]
    files += [p for p in (ROOT / "tools/ghidra").glob("*SoundLab.java")]
    if any(not p.is_file() for p in files):
        raise ValueError("required source deliverable missing")
    stage.mkdir(parents=True)
    manifest = []
    for path in sorted(files):
        relative = path.relative_to(ROOT)
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        manifest.append({"path": relative.as_posix(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "origin": "worktree source"})
    # Isolated source package shims avoid importing the unrelated SDK/compiler
    # graph through the repository's broad package __init__ modules.
    generated = {
        "src/master_rallye/__init__.py": '"""Isolated Sound Bank Lab source handoff package."""\n',
        "src/master_rallye/addon_sdk/__init__.py": '"""Read-only SpecDB parser dependencies only."""\n',
        ".gitignore": "scratch/\n.research-output/\n__pycache__/\n*.py[cod]\n",
        "README.md": "# GT Sound Bank Lab source handoff\n\nSee research/vehicles/gt-sound-lab/README.md and workflow.md.\n\nNo game assets, databases, native exports or audio are included. Package init files are minimal isolated source shims; the original Workshop packages are unchanged.\n"
    }
    for name, content in generated.items():
        target = stage / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        manifest.append({"path": name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "origin": "generated source shim"})
    (stage / "source-manifest.json").write_text(json.dumps({"format": "gt-sound-bank-lab-source/1", "files": manifest,
        "excluded": ["all game assets", "databases and mapping results", "audio", "executables", "Ghidra projects", "native exports", "private diagnostics"]}, indent=2) + "\n", encoding="utf-8")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(stage).as_posix())
    return {"stage": str(stage), "archive": str(archive), "files": len(manifest) + 1,
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(build(args.stage, args.archive), indent=2))
