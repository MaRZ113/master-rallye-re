"""Atmosphere lighting packages for imported RCX courses (course SDK: Atmosphere/courses/<scene>/).

Input: a course pack (tools/course_pack.py make) and the Course Studio projects the converter wrote
(rcx_to_course.py --work <dir>: <dir>/projects/<stage>/project.json). Each project carries the explicit
lighting role of every texture label (extras.rcx.lighting_roles): road / terrain for the ground, vegetation for
cutout objects and the blend layer (its own mirrored texture copy; blended draws need category 3 with AlphaTest),
static for opaque objects, exclude for water.

The packages are built by the base repo's course_lighting_batch.export_batch (materials.lsm + normals.lnh from the
DX vertex normals, which the converter welds smooth on the ground) and copied into <host>/Atmosphere/courses/<scene>.
The runtime picks a package by the RaceTest scene ID. Gameplay: NOT TESTED until the owner runs it.

    py -3 rcx_lighting.py --pack <packs/RCX-07> --projects <set6/projects> --host <host> [--base-repo <master-rallye-re-base>]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

DEFAULT_BASE = Path(__file__).resolve().parents[3] / "master-rallye-re-base"


def roles_by_scene(projects: Path) -> dict:
    roles = {}
    for pj in sorted(projects.glob("*/project.json")):
        data = json.loads(pj.read_text(encoding="utf-8"))
        rcx = data.get("extras", {}).get("rcx", {})
        if rcx.get("lighting_roles"):
            roles[data["build"]["course_key"]] = rcx["lighting_roles"]
    return roles


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", type=Path, required=True)
    ap.add_argument("--projects", type=Path, required=True)
    ap.add_argument("--host", type=Path, required=True)
    ap.add_argument("--base-repo", type=Path, default=DEFAULT_BASE)
    ap.add_argument("--keep", type=Path, help="keep the batch output (reports) here instead of a temp folder")
    a = ap.parse_args(argv)
    tool = a.base_repo / "ps2-research/pc-port/tools/course_lighting_batch.py"
    spec = importlib.util.spec_from_file_location("course_lighting_batch", tool)
    batch = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(tool.parent))
    spec.loader.exec_module(batch)
    roles = roles_by_scene(a.projects)
    source = a.pack / "resources/DataGx/Course"
    scenes = a.pack / "resources/DataScene/RaceTest"
    courses = sorted(p.name for p in source.iterdir() if p.is_dir() and p.name in roles)
    missing = sorted(p.name for p in source.iterdir() if p.is_dir() and p.name not in roles)
    if missing:
        print("no lighting roles for", missing, "(rebuild with rcx_to_course.py set 6 or later)")
    with tempfile.TemporaryDirectory() as tmp:
        out = a.keep or Path(tmp) / "lighting"
        index = batch.export_batch([source], out, roles, None, courses, [scenes])
        bindings = json.loads((out / "scene-bindings.json").read_text())
        target = a.host / "Atmosphere/courses"
        installed = []
        for b in bindings["bindings"]:
            src = out / bindings["runtime_package_dir"] / b["scene"]
            dest = target / b["scene"]
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            installed.append({"scene": b["scene"], "materials": b["material_records"], "normals": b["normal_records"]})
        report = {"courses": [{k: c.get(k) for k in ("course", "status", "counts", "error")} for c in index["courses"]],
                  "installed": installed, "unbound": bindings["unbound_scenes"]}
        print(json.dumps(report, indent=1))
        return 0 if installed and all(c["status"].startswith("OFFLINE_VALIDATED") for c in index["courses"]) else 1


if __name__ == "__main__":
    sys.exit(main())
