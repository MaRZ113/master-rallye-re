"""R-SURFACE1 G0: summarise MRRRenderer/logs/grime-*.jsonl written by the Vehicle Grime probe.

Usage: python grime_probe_report.py <log or logs dir> [--output report.md]

Answers the G0 questions: do the retail particle textures reach the probe (texture matches per draw site), are the
vertex shadows readable, which families each car met in each race, how the Master Rallye mode state moves through
menu -> race -> finish -> save -> reload, and whether the persistence dry run restored a stage's grime.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PARTICLE_SITES = {0x164ED0, 0x1722EE}   # billboard / trail DrawPrimitive return RVAs (ATMOSPHERE6.2)


def records(paths):
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for number, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield path.name, number, json.loads(line)
                except json.JSONDecodeError:
                    yield path.name, number, {"type": "malformed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    paths = sorted(args.source.glob("grime-*.jsonl")) if args.source.is_dir() else [args.source]
    if not paths:
        print("no grime-*.jsonl found", file=sys.stderr)
        return 2
    out = ["# Vehicle Grime G0 probe report", "", "Logs: " + ", ".join(p.name for p in paths), ""]
    textures = Counter()
    races = []
    master = []
    saves = []
    malformed = 0
    for name, number, r in records(paths):
        kind = r.get("type")
        if kind == "malformed":
            malformed += 1
        elif kind == "grime_texture":
            textures[(r.get("rva"), r.get("family"), r.get("source") or "-", r.get("reason"), r.get("format"), r.get("width"), r.get("height"))] += 1
        elif kind == "grime_race_start":
            races.append({"start": r, "end": None, "samples": 0})
        elif kind == "grime_sample" and races:
            races[-1]["samples"] += 1
        elif kind == "grime_race_end":
            if races and races[-1]["end"] is None:
                races[-1]["end"] = r
            else:
                races.append({"start": None, "end": r, "samples": 0})
        elif kind in ("grime_master", "grime_persist_pending", "grime_store_loaded"):
            master.append((name, number, r))
        elif kind == "grime_playerstate_written":
            saves.append(r)
            master.append((name, number, r))
    out += ["## Textures seen at DrawPrimitive sites", "", "| RVA | family | source | reason | format | size | count |", "|---|---|---|---|---|---|---|"]
    for (rva, family, source, reason, fmt, w, h), n in sorted(textures.items(), key=lambda kv: (str(kv[0][1]), -kv[1])):
        if family == "unknown" and rva not in PARTICLE_SITES:
            continue   # UI/world textures at other DrawPrimitive sites
        out.append(f"| 0x{int(rva or 0):x} | {family} | {source} | {reason} | {fmt} | {w}x{h} | {n} |")
    out += ["", "## Races", ""]
    for i, race in enumerate(races, 1):
        s, e = race["start"] or {}, race["end"] or {}
        m = s.get("master", {})
        out.append(f"### Race {i}: generation {s.get('race_generation', e.get('race_generation'))}, Race/Type {s.get('race_type')}, "
                   f"replay {s.get('replay')}, stage {m.get('stage')}, samples {race['samples']}")
        out.append(f"- restored (dry run): {'yes' if s.get('restored_dry_run') not in (None, 'null') else 'no (clean start)'}")
        if e:
            out.append(f"- end: {e.get('why')}, {e.get('seconds')} s, surface draws {e.get('surface_draws')}, triangles {e.get('triangles')}, "
                       f"shadow failures {e.get('shadow_failures')}")
            out.append(f"- draw-site census: {json.dumps(e.get('census', {}))}")
            for car in e.get("cars", []):
                fam = ", ".join(f"{k} {v['tri']} (front {v['front']}/rear {v['rear']}, low {v['low']})" for k, v in car.get("exposure", {}).items()) or "none"
                mud = max(car.get("grime_dry_run", {}).get("mud", [0]))
                dust = max(car.get("grime_dry_run", {}).get("dust", [0]))
                out.append(f"  - car {car['car']}: {fam}; dry-run max dust {dust}, mud {mud}")
        out.append("")
    out += ["## Master Rallye mode timeline", ""]
    for name, number, r in master:
        kind = r.get("type")
        if kind == "grime_master":
            st = r.get("state", {})
            out.append(f"- {name}:{number} in_race={r.get('in_race')} Race/Type={r.get('race_type')} stage={st.get('stage')} saved={st.get('saved')} "
                       f"checkpoint={st.get('checkpoint')} event={r.get('event')} pending={r.get('pending')}")
        elif kind == "grime_playerstate_written":
            out.append(f"- {name}:{number} **PlayerState.xml written** in_race={r.get('in_race')} stage={r.get('master', {}).get('stage')}")
        else:
            out.append(f"- {name}:{number} {kind} {json.dumps({k: v for k, v in r.items() if k != 'type'})}")
    out += ["", f"Malformed lines: {malformed}", ""]
    text = "\n".join(out)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
