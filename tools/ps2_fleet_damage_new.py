"""Damage (deformation) profiles for the Roster V4 fleet families (FORKLIFT -> forklift, FORESTER -> ForesterSTI).

SDK cars render from a private (deformable) mesh tree from the start of a race; the PS2 CAR model is kept only when the
family has an eligible fleet_damage profile, otherwise the renderer falls back to the PC model
(`ps2_fleet_car_fallback gate=2`, owner test 2026-11-11: ForesterSTI raced with its Demo model).

This runs the accepted VEHICLE-FLEET-PORT3 generator (docs/vehicle-fleet-port3/car/prepare_contracts.py, run()) with
the new families as input: its algorithm is not copied, only its three inputs are redirected (profile list, PC car.dx
path per family, output folder). Kia stays in the list because the generator derives its static crew templates from
it; only the new families' rows are appended to renderer/fleet_damage_registry.hpp (`--apply`).
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PORT = BASE / "ps2-research/pc-port"
GEN = PORT / "docs/vehicle-fleet-port3/car/prepare_contracts.py"


def generate(report_path: Path, out: Path):
    report = json.loads(report_path.read_text())
    mine = [dict(f["profile"]) for f in report["families"]]
    pcpaths = {f["profile"]["family"]: f["pc_car"] for f in report["families"]}
    old = json.loads((PORT / "docs/vehicle-continuity2/fleet-car/race-profiles.json").read_text())["profiles"]
    kia = next(p for p in old if p["family"] == "KiaSportage")
    src = GEN.read_text(encoding="utf-8")
    reps = [
        ("profiles=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/race-profiles.json').read_text())['profiles']", "profiles=__PROFILES__"),
        ("pcpath=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles'/p['family']/'car.dx'",
         "pcpath=Path(__PCPATHS__[p['family']]) if p['family'] in __PCPATHS__ else ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles'/p['family']/'car.dx'"),
        ("(HERE/'runtime_damage_registry.hpp')", "(__OUT__/'runtime_damage_registry.hpp')"),
        ("(HERE/'fleet_damage_draft.hpp')", "(__OUT__/'fleet_damage_draft.hpp')"),
        ("(HERE/'contracts.json')", "(__OUT__/'contracts.json')"),
    ]
    for a, b in reps:
        if src.count(a) != 1:
            raise ValueError("generator changed; refusing to redirect: " + a[:50])
        src = src.replace(a, b)
    src = src.replace("if __name__=='__main__':run()", "")
    out.mkdir(parents=True, exist_ok=True)
    g = {"__name__": "port3_damage_redirected", "__file__": str(GEN), "__PROFILES__": [kia] + mine,
         "__PCPATHS__": pcpaths, "__OUT__": out}
    exec(compile(src, str(GEN), "exec"), g)
    g["run"]()
    contracts = json.loads((out / "contracts.json").read_text())
    return {p["family"]: {"eligible": p["eligible"], "referenced": p["referenced_vertices"], "exact": p["mapped_vertices"],
                          "transfer": p["transfer_vertices"], "rigid": p["rigid_component_vertices"],
                          "unresolved": len(p["unresolved_vertices"]), "max_transfer_m": p["max_transfer_distance"]}
            for p in contracts["profiles"] if p["family"] != "KiaSportage"}


def apply(out: Path, families: list[str]):
    """Append the new families' arrays and profile rows to renderer/fleet_damage_registry.hpp."""
    generated = (out / "runtime_damage_registry.hpp").read_text().splitlines()
    registry = PORT / "renderer/fleet_damage_registry.hpp"
    text = registry.read_text()
    marker = "inline constexpr Profile profiles[]={"
    arrays, rows = [], []
    for fam in families:
        if f" {fam}_candidates[]" in text:
            raise ValueError(f"{fam} already in {registry.name}")
        arrays += [l for l in generated if l.startswith("inline constexpr") and f" {fam}_" in l]
        rows += [l for l in generated if l.startswith('{"') and f'","{fam}",' in l]
    if len(rows) != len(families):
        raise ValueError("missing generated profile rows")
    text = text.replace(marker, "\n".join(arrays) + "\n" + marker)
    head, tail = text.split(marker)
    end = tail.index("\n};")
    registry.write_text(head + marker + tail[:end] + "\n" + "\n".join(rows) + tail[end:])
    return rows


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--report", type=Path, required=True, help="race-profiles.json of tools/ps2_fleet_new_families.py")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    result = generate(a.report, a.out)
    print(json.dumps(result, indent=1))
    if a.apply:
        print("\n".join(apply(a.out, ["FORKLIFT", "FORESTER"])))
