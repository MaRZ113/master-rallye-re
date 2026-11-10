"""Fast mechanism check for the five-race Invitation patch.

Five stock scenes are copied under ``InvMech1..5`` with their FinishArea moved
to a small box around RaceLine sample ``--finish-sample`` (about 200 m after
the start). G0 confirmed that FinishArea geometry drives race completion, so
each race ends within seconds and the run exercises stage advance 1 -> 5,
progress writes for stages 4/5 and the final trophy without new geometry.
Pair it with an EXE built by
``patch_invitation_entries.py --names InvMech1,InvMech2,InvMech3,InvMech4,InvMech5``.
"""
from __future__ import annotations

import argparse
import math
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOCK = ("FranceM", "ItalyM2", "SpainM", "TurkeyM", "France2")


def finish_box(raceline, index: int, half_length: float = 10.0, half_width: float = 25.0):
    a, b = raceline[index], raceline[min(index + 1, len(raceline) - 1)]
    fx, fz = b[0] - a[0], b[2] - a[2]
    n = math.hypot(fx, fz) or 1.0
    fx, fz = fx / n, fz / n
    lx, lz = -fz, fx
    corners = []
    for along, side in ((-half_length, -half_width), (-half_length, half_width),
                        (half_length, half_width), (half_length, -half_width)):
        corners.append((a[0] + fx * along + lx * side, a[1], a[2] + fz * along + lz * side))
    return corners


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--retail", type=Path, default=ROOT.parent / "corpora/retail/Data.sma_unpacked")
    parser.add_argument("--output", type=Path, default=ROOT / "research-output/invitation_concept/mech5")
    parser.add_argument("--finish-sample", type=int, default=10)
    args = parser.parse_args()
    racetest = args.retail / "DataScene/RaceTest"
    out = args.output / "DataScene/RaceTest"
    out.mkdir(parents=True, exist_ok=True)
    for number, stock in enumerate(STOCK, 1):
        data = (racetest / f"{stock}.xml").read_text(encoding="latin-1")
        root = ET.fromstring(data)
        lists = {lst.get("Name"): lst for lst in root.iter("List")}
        raceline = [tuple(map(float, m.find("Value[@Name='Marker Pos']").get("Value").split()))
                    for m in lists["RaceLine"].findall("Marker")]
        markers = lists["FinishArea"].findall("Marker")
        if len(markers) != 4:
            raise SystemExit(f"{stock}: expected four FinishArea markers")
        for marker, corner in zip(markers, finish_box(raceline, args.finish_sample)):
            marker.find("Value[@Name='Marker Pos']").set("Value", " ".join(f"{c:.2f}" for c in corner))
        (out / f"InvMech{number}.xml").write_bytes(ET.tostring(root, encoding="unicode").encode("utf-8"))
        hnt = next(p for p in racetest.glob("*.hnt") if p.stem.lower() == stock.lower())
        shutil.copyfile(hnt, out / f"InvMech{number}.hnt")
        print(f"InvMech{number} <- {stock}, finish near RaceLine[{args.finish_sample}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
