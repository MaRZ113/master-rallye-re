"""Single-factor diagnostic scenes for the combined-course crash (R5T-INV E1.1).

The five-race package crashed at the end of loading InvFrance inside the land
database query ``FUN_006068A0`` (corrupt grid object). Each diagnostic scene
below changes exactly one factor against stock FranceM and is loaded as
Invitation race 1 by its own EXE copy (``MRallye_diagN.exe``):

1. two different landscape eggs (FranceM + France_S1, identity matrices)
2. the same landscape egg twice (FranceM + FranceM)
3. generated InvFrance scene with ONE landscape (France2) + synthesized SFL
4. stock FranceM scene with a synthesized SFL (ICont/invdiag4)
5. stock FranceM with the landscape matrix and every scene position moved
   +1000 X (and the stock SFL copied with its origin moved +1000)

It also rebuilds ``InvMech1..5`` with a 15-sample RaceLine, splits along it and
the FinishArea at its end: moving only FinishArea did not end a race, so
completion evidently also needs RaceLine progress.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.course_sfl_field import synthesize_heading_field, grid_for_route  # noqa: E402

MECH_STOCK = ("FranceM", "ItalyM2", "SpainM", "TurkeyM", "France2")
SHIFT_X = 1000.0


def lists(root):
    return {lst.get("Name"): lst for lst in root.iter("List")}


def marker_positions(lst):
    return [tuple(map(float, m.find("Value[@Name='Marker Pos']").get("Value").split())) for m in lst.findall("Marker")]


def set_marker_positions(lst, positions):
    markers = lst.findall("Marker")
    prototype, tail = markers[0], markers[0].tail
    for m in markers:
        lst.remove(m)
    for k, p in enumerate(positions):
        m = copy.deepcopy(prototype)
        m.tail = tail
        m.set("No", str(k))
        m.find("Value[@Name='Marker Pos']").set("Value", " ".join(f"{c:.2f}" for c in p))
        lst.append(m)


def write(root, path: Path):
    path.write_bytes(ET.tostring(root, encoding="unicode").encode("utf-8"))


def add_landscape(root, model):
    lst = lists(root)["landscape"]
    egg = copy.deepcopy(lst.find("Egg"))
    egg.find("Value[@Name='en3d Model Name']").set("Value", model)
    lst.append(egg)


def set_dataset(root, name):
    for v in root.iter("Value"):
        if v.get("Name") == "AI DataSet Name":
            v.set("Value", f"ICont/{name}")


def finish_box(a, b, half_length=10.0, half_width=25.0):
    fx, fz = b[0] - a[0], b[2] - a[2]
    n = math.hypot(fx, fz) or 1.0
    fx, fz, lx, lz = fx / n, fz / n, -fz / n, fx / n
    return [(a[0] + fx * u + lx * v, a[1], a[2] + fz * u + lz * v)
            for u, v in ((-half_length, -half_width), (-half_length, half_width),
                         (half_length, half_width), (half_length, -half_width))]


def shift_scene(root, dx):
    """Translate every Marker Pos and every en3d Matrix Row3 by dx along X."""
    for v in root.iter("Value"):
        if v.get("Name") == "Marker Pos":
            x, y, z = map(float, v.get("Value").split())
            v.set("Value", f"{x + dx:.2f} {y:.2f} {z:.2f}")
        elif v.get("Name") == "en3d Matrix" and v.get("Row3"):
            parts = v.get("Row3").split()
            parts[0] = f"{float(parts[0]) + dx:.2f}"
            v.set("Row3", " ".join(parts))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--retail", type=Path, default=ROOT.parent / "corpora/retail/Data.sma_unpacked")
    parser.add_argument("--concept", type=Path, default=ROOT / "research-output/invitation_concept")
    parser.add_argument("--exe", type=Path, default=ROOT.parent / "MRallye.exe")
    parser.add_argument("--output", type=Path, default=ROOT / "research-output/invitation_concept/diag")
    args = parser.parse_args()
    racetest, icont = args.retail / "DataScene/RaceTest", args.retail / "DataScene/ICont"
    scenes, sfls = args.output / "DataScene/RaceTest", args.output / "DataScene/ICont"
    scenes.mkdir(parents=True, exist_ok=True)
    sfls.mkdir(parents=True, exist_ok=True)
    stock = lambda name: ET.fromstring((racetest / f"{name}.xml").read_bytes())  # noqa: E731
    hnt = lambda name: next(p for p in racetest.glob("*.hnt") if p.stem.lower() == name.lower()).read_bytes()  # noqa: E731

    root = stock("FranceM"); add_landscape(root, "course\\france_s1\\frances1"); write(root, scenes / "InvDiag1.xml")
    (scenes / "InvDiag1.hnt").write_bytes(hnt("FranceM") + hnt("FranceS1"))
    root = stock("FranceM"); add_landscape(root, "course\\france_m\\francem"); write(root, scenes / "InvDiag2.xml")
    (scenes / "InvDiag2.hnt").write_bytes(hnt("FranceM"))

    root = ET.fromstring((args.concept / "InvFrance/InvFrance.xml").read_bytes())
    lists(root)["landscape"].find("Egg").find("Value[@Name='en3d Model Name']").set("Value", "course\\france2\\france2")
    set_dataset(root, "invdiag3")
    write(root, scenes / "InvDiag3.xml")
    (scenes / "InvDiag3.hnt").write_bytes(hnt("France2"))
    (sfls / "invdiag3.sfl").write_bytes((args.concept / "InvFrance/invfrance.sfl").read_bytes())

    root = stock("FranceM"); set_dataset(root, "invdiag4"); write(root, scenes / "InvDiag4.xml")
    (scenes / "InvDiag4.hnt").write_bytes(hnt("FranceM"))
    route = marker_positions(lists(root)["RaceLine"])
    (sfls / "invdiag4.sfl").write_bytes(synthesize_heading_field(route, grid_for_route(route)))

    root = stock("FranceM"); shift_scene(root, SHIFT_X); set_dataset(root, "invdiag5"); write(root, scenes / "InvDiag5.xml")
    (scenes / "InvDiag5.hnt").write_bytes(hnt("FranceM"))
    data = bytearray((icont / "francem.sfl").read_bytes())
    struct.pack_into("<f", data, 12, struct.unpack_from("<f", data, 12)[0] + SHIFT_X)
    (sfls / "invdiag5.sfl").write_bytes(bytes(data))

    for number, name in enumerate(MECH_STOCK, 1):
        root = stock(name)
        lst = lists(root)
        line = marker_positions(lst["RaceLine"])[:15]
        set_marker_positions(lst["RaceLine"], line)
        set_marker_positions(lst["FinishArea"], finish_box(line[-2], line[-1]))
        mains = [e for e in lst["SplitTimes"].findall("Egg")
                 if e.get("Name", "").startswith("SplitTime") and "-" not in e.get("Name", "")]
        for egg, k in zip(mains, (4, 8, 11)):
            row = egg.find("Value[@Name='en3d Matrix']")
            parts = row.get("Row3").split()
            row.set("Row3", " ".join([*(f"{c:.2f}" for c in line[k]), parts[3]]))
        write(root, scenes / f"InvMech{number}.xml")
        (scenes / f"InvMech{number}.hnt").write_bytes(hnt(name))

    exe_dir = args.output / "exe"
    exe_dir.mkdir(exist_ok=True)
    results = {}
    for n in range(1, 6):
        target = exe_dir / f"MRallye_diag{n}.exe"
        subprocess.run([sys.executable, str(ROOT / "tools/patch_invitation_entries.py"), str(args.exe), str(target),
                        "--names", f"InvDiag{n},InvTurkey,InvItaly"], check=True, capture_output=True)
        results[target.name] = f"Invitation race 1 -> InvDiag{n}"
    (args.output / "diag-manifest.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
