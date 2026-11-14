"""Course pack: built Course Studio courses + menu artwork, installed by the Vehicle Manager as their own Quick Race
category (tools/vehicle_manager.py course-pack-add / apply; native layer tools/course_layer.py).

  python tools/course_pack.py make --name EVO2 --label "4X4 EVO" --out <pack dir> \\
      --course <build dir>/<Key> --title "Deadman's Gulch" --shots <preview dir> [--course ... --title ... --shots ...]
      [--logo logo.png] [--distance-km 7.1 ...]

A course entry is a Course Studio build output folder (<Key>/resource-root/DataGx/Course/<key>/..., DataScene/RaceTest/
<Key>.xml + .hnt, DataScene/ICont/<key>.sfl) and a preview folder with screenshot1.png / screenshot2.png (128x128).
Pack layout:
  course-pack.json   {schema, name, category {label, logo}, races [{key, title, scene, icont, progress_key, distance_km,
                     screenshots}]}
  resources/         game-relative files merged into MRMods/Vehicles/active/resources by `apply`
  art/               screenshots and logo
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

SCHEMA = "mr-course-pack/1"


def course_entry(build: Path) -> dict:
    root = build / "resource-root"
    scenes = sorted((root / "DataScene" / "RaceTest").glob("*.xml"))
    sfls = sorted((root / "DataScene" / "ICont").glob("*.sfl"))
    if len(scenes) != 1 or len(sfls) != 1:
        raise ValueError(f"{build}: expected one RaceTest scene and one ICont SFL")
    key = scenes[0].stem
    report = json.loads((build / "course-build.json").read_text(encoding="utf-8")) if (build / "course-build.json").is_file() else {}
    return {"key": key, "scene": f"DataScene/RaceTest/{scenes[0].name}", "icont": f"DataScene/ICont/{sfls[0].name}",
            "root": root, "title": report.get("title") or key}


def make(args) -> dict:
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "resources").mkdir(parents=True)
    (out / "art").mkdir()
    races = []
    for k, build in enumerate(args.course):
        e = course_entry(Path(build))
        title = (args.title[k] if args.title and k < len(args.title) else e["title"])
        title = title.encode("ascii", "replace").decode("ascii")[:60]
        shots_dir = Path(args.shots[k])
        shots = []
        for n in (1, 2):
            src = shots_dir / f"screenshot{n}.png"
            dst = out / "art" / f"{e['key']}_{n}.png"
            shutil.copyfile(src, dst)
            shots.append(f"art/{dst.name}")
        for f in sorted(e["root"].rglob("*")):
            if f.is_file():
                rel = f.relative_to(e["root"])
                target = out / "resources" / rel
                if target.exists():
                    raise ValueError(f"{rel} is provided twice in this pack")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, target)
        distance = args.distance_km[k] if args.distance_km and k < len(args.distance_km) else 5.0
        races.append({"key": e["key"], "title": title, "scene": e["scene"], "icont": e["icont"],
                      "progress_key": re.sub(r"[^A-Za-z0-9_-]", "-", e["key"].lower()), "distance_km": round(float(distance), 2),
                      "screenshots": shots})
    meta = {"schema": SCHEMA, "name": args.name, "category": {"label": args.label}, "races": races}
    if args.logo:
        shutil.copyfile(args.logo, out / "art" / "logo.png")
        meta["category"]["logo"] = "art/logo.png"
    (out / "course-pack.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--name", required=True)
    m.add_argument("--label", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--course", action="append", required=True)
    m.add_argument("--title", action="append")
    m.add_argument("--shots", action="append", required=True)
    m.add_argument("--distance-km", action="append", type=float)
    m.add_argument("--logo")
    a = ap.parse_args(argv)
    print(json.dumps(make(a), indent=1))


if __name__ == "__main__":
    main()
