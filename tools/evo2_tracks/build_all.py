"""Every 4x4 Evolution 2 race (SIT race type 2 = race, 3 = hill climb) -> built courses, previews and one course pack.

  python build_all.py --evo2 "E:\\RallyWorkshop_Sources\\sources\\4x4 Evo 2" --work <dir> --resource-root <retail tree>
                      [--jobs 6] [--only DVALLEY,PEAK] [--pack <pack dir>]

Each race is built in its own process (Course Studio collision is pure Python); results: <work>/builds/<Key>,
<work>/previews/<SIT>, <work>/build-<SIT>.json, <work>/summary.json. A race whose build fails is reported and left out
of the pack. Mission maps (type 6: Alaska, El Norte, Skull Island, The River, Washington, Obstacle Park) are skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evo2_track import Pod, list_races, parse_sit  # noqa: E402

RACE_TYPES = (2, 3)
SKIP_PODS = {"truck", "ui", "sound", "music", "ai", "driver", "engtxt", "fretxt", "gertxt", "parts", "startup", "series",
             "life", "cmaps-pc", "ps2big", "dust"}


def catalog(evo2: Path):
    races = []
    for pod_path in sorted(evo2.glob("*")):
        if pod_path.suffix.lower() != ".pod" or pod_path.stem.lower() in SKIP_PODS:
            continue
        try:
            pod = Pod(pod_path)
        except Exception:
            continue
        for stem in list_races(pod):
            sit = parse_sit(pod.read(f"WORLD/{stem}.SIT"))
            if sit.race_type in RACE_TYPES and any(b.kind == "CCheckpoint" for b in sit.boxes):
                races.append({"pod": str(pod_path), "sit": stem, "name": sit.name, "type": sit.race_type,
                              "length_km": round(sit.track_length_ft * 0.3048 / 1000, 2)})
    return races


def run(race, work: Path, resource_root: Path, env):
    log = work / f"log-{race['sit']}.txt"
    with open(log, "w") as f:
        r = subprocess.run([sys.executable, str(HERE / "build_track.py"), "--pod", race["pod"], "--sit", race["sit"],
                            "--work", str(work), "--resource-root", str(resource_root)], stdout=f, stderr=subprocess.STDOUT,
                           env=env, cwd=str(HERE))
    result = {"ok": False}
    report = work / f"build-{race['sit']}.json"
    if report.is_file():
        result = json.loads(report.read_text())
    if r.returncode == 0 and result.get("ok"):
        try:
            from previews import render
            render(work / "projects" / race["sit"], work / "previews" / race["sit"])
            result["previews"] = True
        except Exception as e:  # noqa: BLE001
            result["previews"] = f"failed: {e}"
    print(f"{race['sit']:<10} {race['name']:<26} ok={result.get('ok')} {result.get('timing')}", flush=True)
    return {**race, "ok": bool(result.get("ok")), "output": result.get("output"), "errors": result.get("errors", [])[:5],
            "previews": result.get("previews"), "model_cache": result.get("model_cache")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--evo2", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--resource-root", type=Path, required=True)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--only")
    ap.add_argument("--pack", type=Path)
    ap.add_argument("--label", default="4X4 EVO")
    a = ap.parse_args(argv)
    a.work.mkdir(parents=True, exist_ok=True)
    races = catalog(a.evo2)
    if a.only:
        wanted = {s.strip().upper() for s in a.only.split(",")}
        races = [r for r in races if r["sit"].upper() in wanted]
    print(f"{len(races)} races", flush=True)
    env = dict(os.environ)
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        results = list(pool.map(lambda r: run(r, a.work, a.resource_root, env), races))
    (a.work / "summary.json").write_text(json.dumps(results, indent=1))
    good = [r for r in results if r["ok"] and r["previews"] is True]
    print(f"built {len(good)}/{len(results)}", flush=True)
    if a.pack and good:
        sys.path.insert(0, str(HERE.parent))
        import course_pack
        args = argparse.Namespace(name=a.pack.name, label=a.label, out=str(a.pack), logo=None,
                                  course=[r["output"] for r in good], title=[r["name"] for r in good],
                                  shots=[str(a.work / "previews" / r["sit"]) for r in good],
                                  distance_km=[r["length_km"] for r in good])
        course_pack.make(args)
        print(f"pack {a.pack}: {len(good)} races", flush=True)


if __name__ == "__main__":
    main()
