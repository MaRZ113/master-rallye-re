"""Merge the per-phase Atmosphere* install folders into one Atmosphere\\ tree.

Every Atmosphere asset is located through a key in Atmosphere.ini (and the
profiles\\*.ini A/B files), so the merge is file moves plus key rewrites.
Default is a dry run; pass --apply to move files.  A JSON journal with every
move and the original INI texts is written next to Atmosphere.ini so the
merge can be undone with --undo <journal>.

Unified layout (relative to the game folder):
  Atmosphere/sky/<set>/            clouds.dxt + layer.dxt (CustomSet)
  Atmosphere/materials/            materials.lsm + common.json (LightingMetadata)
  Atmosphere/normals/              normals.lnh (NormalHints)
  Atmosphere/vehicles/             vehicles.blm (BodyMaterials)
  Atmosphere/courses/<SceneID>/    per-course packages (LightingPackageRoot)
  Atmosphere/regions/              regional catalogs (RegionalAtmospheres)
  Atmosphere/sun/                  optional sun sprites (SunRaysTexture)
  Atmosphere/private/              private A/B assets, never part of a release
  Atmosphere/legacy/<old folder>/  files no current key points at
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

# (source relative path, destination relative path); directories move whole.
MOVES = [
    ("Atmosphere/sets", "Atmosphere/sky"),
    ("Atmosphere2/sets/r_deepforest", "Atmosphere/sky/r_deepforest"),
    ("Atmosphere2/sets/r_grandvalley", "Atmosphere/sky/r_grandvalley"),
    ("Atmosphere2/sky-provenance.json", "Atmosphere/sky/sky-provenance.json"),
    ("Atmosphere2/scene.atlas", "Atmosphere/legacy/Atmosphere2/scene.atlas"),
    ("Atmosphere2/scene-provenance.json", "Atmosphere/legacy/Atmosphere2/scene-provenance.json"),
    ("Atmosphere21", "Atmosphere/legacy/Atmosphere21"),
    ("Atmosphere22/normals.lnh", "Atmosphere/normals/normals.lnh"),
    ("Atmosphere22/normals.lnh.provenance.json", "Atmosphere/normals/normals.lnh.provenance.json"),
    ("Atmosphere22", "Atmosphere/legacy/Atmosphere22"),
    ("Atmosphere25/materials.lsm", "Atmosphere/materials/materials.lsm"),
    ("Atmosphere25/common.json", "Atmosphere/materials/common.json"),
    ("Atmosphere25", "Atmosphere/legacy/Atmosphere25"),
    ("Atmosphere27/courses", "Atmosphere/courses"),
    ("Atmosphere27", "Atmosphere/legacy/Atmosphere27"),
    ("Atmosphere28", "Atmosphere/regions"),
    ("Atmosphere29/vehicles.blm", "Atmosphere/vehicles/vehicles.blm"),
    ("Atmosphere29", "Atmosphere/legacy/Atmosphere29"),
    ("AtmospherePrivate", "Atmosphere/private"),
]

# Old path prefix -> new prefix, applied to INI values (longest first).
PREFIXES = [
    ("Atmosphere2/sets/", "Atmosphere/sky/"),
    ("Atmosphere2/scene.atlas", "Atmosphere/legacy/Atmosphere2/scene.atlas"),
    ("Atmosphere/sets/", "Atmosphere/sky/"),
    ("Atmosphere21/", "Atmosphere/legacy/Atmosphere21/"),
    ("Atmosphere22/normals.lnh", "Atmosphere/normals/normals.lnh"),
    ("Atmosphere22/", "Atmosphere/legacy/Atmosphere22/"),
    ("Atmosphere25/materials.lsm", "Atmosphere/materials/materials.lsm"),
    ("Atmosphere25/", "Atmosphere/legacy/Atmosphere25/"),
    ("Atmosphere27/courses", "Atmosphere/courses"),
    ("Atmosphere27/", "Atmosphere/legacy/Atmosphere27/"),
    ("Atmosphere28/", "Atmosphere/regions/"),
    ("Atmosphere29/vehicles.blm", "Atmosphere/vehicles/vehicles.blm"),
    ("Atmosphere29/", "Atmosphere/legacy/Atmosphere29/"),
    ("AtmospherePrivate/", "Atmosphere/private/"),
]
PATH_KEYS = {"customset", "lightingmetadata", "normalhints", "bodymaterials", "lightingpackageroot",
             "regionalatmospheres", "sunraystexture", "sceneatlas"}
KEY_RE = re.compile(r"^(\s*;?\s*)([A-Za-z0-9_]+)(\s*=\s*)(.*?)(\s*)$")


def rewrite_value(value: str) -> str:
    norm = value.replace("\\", "/")
    for old, new in PREFIXES:
        if norm.lower().startswith(old.lower()):
            return new + norm[len(old):]
    return value


def rewrite_ini(text: str) -> str:
    out = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        eol = line[len(body):]
        m = KEY_RE.match(body)
        if m and m.group(2).lower() in PATH_KEYS:
            body = m.group(1) + m.group(2) + m.group(3) + rewrite_value(m.group(4)) + m.group(5)
        elif m and body.lstrip().startswith(";"):
            # comments mentioning paths (e.g. "SunRaysTexture=Atmosphere25/...") stay readable
            body = re.sub(r"(Atmosphere\w*[/\\][^\s;]*)", lambda x: rewrite_value(x.group(1)), body)
        out.append(body + eol)
    return "".join(out)


def ini_files(root: Path) -> list[Path]:
    files = [root / "Atmosphere.ini"]
    files += sorted((root / "profiles").glob("*.ini")) if (root / "profiles").is_dir() else []
    return [f for f in files if f.is_file()]


def merge_move(src: Path, dst: Path, moved: list) -> None:
    if src.is_dir() and dst.is_dir():
        for child in sorted(src.iterdir()):
            merge_move(child, dst / child.name, moved)
        src.rmdir()
        return
    if dst.exists():
        raise SystemExit(f"refusing to overwrite {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    moved.append([str(src), str(dst)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("game_root", type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--undo", type=Path, help="journal written by a previous --apply")
    a = ap.parse_args()
    root = a.game_root.resolve()

    if a.undo:
        j = json.loads(a.undo.read_text(encoding="utf-8"))
        for src, dst in reversed(j["moved"]):
            Path(src).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(dst, src)
        for name, text in j["ini"].items():
            (root / name).write_bytes(text.encode("latin-1"))
        print(f"undone {len(j['moved'])} moves, {len(j['ini'])} INI files restored")
        return 0

    plan = [(s, d) for s, d in MOVES if (root / s).exists()]
    for s, d in plan:
        print(f"move  {s}  ->  {d}")
    ini_changes = {}
    for f in ini_files(root):
        old = f.read_bytes().decode("latin-1")
        new = rewrite_ini(old)
        if new != old:
            ini_changes[f] = (old, new)
            for o, n in zip(old.splitlines(), new.splitlines()):
                if o != n:
                    print(f"ini   {f.relative_to(root)}: {o.strip()}  ->  {n.strip()}")
    if not a.apply:
        print("dry run; pass --apply")
        return 0

    moved: list = []
    journal = root / f"Atmosphere-unify-{time.strftime('%Y%m%d-%H%M%S')}.json"
    try:
        for s, d in plan:
            if (root / s).exists():
                merge_move(root / s, root / d, moved)
    finally:
        journal.write_text(json.dumps({"moved": moved,
                                       "ini": {str(f.relative_to(root)): o for f, (o, _) in ini_changes.items()}},
                                      indent=1), encoding="utf-8")
    for f, (_, new) in ini_changes.items():
        f.write_bytes(new.encode("latin-1"))
    leftovers = [p.name for p in root.glob("Atmosphere?*") if p.is_dir()]
    print(f"moved {len(moved)} entries; journal {journal}; leftover folders: {leftovers or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
