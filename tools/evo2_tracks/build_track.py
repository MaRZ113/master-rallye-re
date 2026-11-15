"""Evo 2 race -> Course Studio project -> native MR course (one call per track; universal for every SIT).

  python tools/evo2_tracks/build_track.py --pod <Evo2>/DVALLEY.POD [--sit DVALLEY] --work <dir> --resource-root <retail tree>

Needs PYTHONPATH with the Course Studio core (master-rallye-re-course/src) and this folder. Writes
<work>/projects/<SIT>/ (Course Studio project, reopenable in Blender) and <work>/builds/<Key>/resource-root/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from evo2_track import load_track  # noqa: E402
from to_course import build_project  # noqa: E402


def drop_solids_at(project, spots, margin=1.5) -> int:
    """Remove the recorded object solids (project.extras['evo2_solids']) whose bounds hold a reported route spot."""
    meshes = {m.id: m for m in project.meshes}
    removed = 0
    for mesh_id, ranges in list(project.extras.get("evo2_solids", {}).items()):
        mesh = meshes[mesh_id]
        keep_ranges, tris, mats, keep_decks = [], [], [], []
        decks = project.extras.get("evo2_deck_solids", {}).get(mesh_id) or [False] * len(ranges)
        pos = mesh.positions
        for (a0, b0), is_deck in zip(ranges, decks):
            pts = [pos[3 * mesh.triangles[3 * t + j]:3 * mesh.triangles[3 * t + j] + 3] for t in range(a0, b0) for j in range(3)]
            lo = [min(q[k] for q in pts) - margin for k in range(3)]
            hi = [max(q[k] for q in pts) + margin for k in range(3)]
            if not is_deck and any(all(lo[k] <= s[k] <= hi[k] for k in range(3)) for s in spots):   # decks stay
                removed += 1
                continue
            start = len(mats)
            for t in range(a0, b0):
                tris.extend(mesh.triangles[3 * t:3 * t + 3])
                mats.append(mesh.tri_material[t])
            keep_ranges.append([start, len(mats)])
            keep_decks.append(is_deck)
        mesh.triangles, mesh.tri_material = tris, mats
        project.extras["evo2_solids"][mesh_id] = keep_ranges
        project.extras.setdefault("evo2_deck_solids", {})[mesh_id] = keep_decks
    return removed


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod", type=Path, required=True)
    ap.add_argument("--sit")
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--resource-root", type=Path, required=True)
    ap.add_argument("--corridor", type=float, default=190.0)
    ap.add_argument("--no-objects", action="store_true")
    ap.add_argument("--object-collision", choices=("all", "boxes", "drivable", "none"), default="all")
    ap.add_argument("--project-only", action="store_true")
    ap.add_argument("--collision-radius", type=float, default=40.0)
    ap.add_argument("--ungrounded", action="store_true")
    a = ap.parse_args(argv)
    from master_rallye.studio.model import save_project
    from master_rallye.studio.build import build_course
    import object_bsp
    import render_batches
    render_batches.install()                      # Retail-sized draw records (see render_batches.py)
    t0 = time.time()
    track = load_track(a.pod, a.sit)
    pdir = a.work / "projects" / track.key
    def attempt(bridges):
        project = build_project(track, pdir, corridor_m=a.corridor, objects=not a.no_objects, object_collision=a.object_collision,
                                collision_radius_m=a.collision_radius, grounded=not a.ungrounded, bridges=bridges)
        save_project(project, pdir)
        object_bsp.install(project)                   # disjoint object solids: kd split between them (see object_bsp.py)
        timing = {"convert_s": round(time.time() - t0, 1)}
        print(json.dumps(project.extras["evo2"]), flush=True)
        marks = {}
        if a.project_only:
            return project, None, 0, timing, marks

        def say(stage, fraction=None):
            if stage not in marks:
                marks[stage] = round(time.time() - t0, 1)
                print(f"  [{stage}] t={marks[stage]}s", flush=True)
        dropped = 0
        for _try in range(4):
            result = build_course(project, project_dir=pdir, resource_root=a.resource_root, output=a.work / "builds", progress=say)
            if result.ok:
                break
            # Object solids the Course Studio route sweep still finds next to the AI line (it samples the native
            # RaceLine, +-1 m, 0.35..2.2 m above the terrain): remove those solids and build again.
            spots = [i["position"] for i in result.report.get("collision_issues", [])
                     if i.get("kind") in ("route_sweep", "route_step", "route_blocked") and i.get("position")]
            others = [f for f in result.findings if f.severity == "error" and f.category != "collision"]
            if not spots or others:
                break
            n = drop_solids_at(project, spots)
            if not n:
                break
            dropped += n
            save_project(project, pdir)
            object_bsp.install(project)
            print(f"  [route sweep] removed {n} object solids at the AI line; rebuilding", flush=True)
        return project, result, dropped, timing, marks

    marks = {}
    bridges_used = True
    project, result, dropped, timing, marks = attempt(True)
    if a.project_only:
        return 0
    if not getattr(result, "ok", True) and project.extras["evo2"].get("decks"):
        # Bridge decks make the Course Studio probes stricter (deck-end steps, holes under decks). A race that does not
        # pass with them is built as before (no decks: elevated boxes float, the route follows the terrain).
        print("  [bridges] the build with bridge decks failed; building without them", flush=True)
        bridges_used = False
        project, result, dropped, timing, marks = attempt(False)
    project.extras["evo2"]["bridges"] = bridges_used
    project.extras["evo2"]["route_sweep_solids_dropped"] = dropped
    save_project(project, pdir)
    timing["total_s"] = round(time.time() - t0, 1)
    errors = [f.to_dict() for f in result.findings if f.severity == "error"]
    summary = {"ok": result.ok, "output": str(result.output), "timing": timing, "stages": marks, "errors": errors[:20],
               "model_cache": result.report.get("model_cache"), "dx": {k: v for k, v in (result.report.get("dx") or {}).items()
                                                                        if not isinstance(v, (list, dict))}}
    (a.work / f"build-{track.key}.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
