"""Retail vertex prelight for already built add-on cars in a roster base (Roster RCX 07, owner 2026-11-17).

Retail MR car.dx / complete.dx vertices carry a baked grey from the vertex normal,
c = round(255 * (0.4 + 0.3 * sqrt(max(0, n.y)))), only the brake glow card is 255 (contract and evidence:
master-rallye-re-import master_rallye/retail_vehicle_contract.py). Converter cars written with 255 everywhere look
~1.8x brighter in Vehicle Select and under the R-SURFACE1 dust pass (DIFFUSE x tint).

New pilots get the prelight in the generator (txr3_classic_pilot). This tool fixes cars whose resources were
authored later on top of the pilot output (the 4x4 Evo cars carry lamp work from Roster V4 / Evo Brake 01), without
rebuilding them: only the vertex colour bytes change, so positions, UVs, collision and the addon-brake-lamps.tsv
geometry/UV digests stay valid.

usage: py -3 tools/vehicle_prelight.py <base dir with resources/ and catalog.json> FAMILY [FAMILY ...]
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

IMPORT_SRC = Path(__file__).resolve().parents[2] / 'master-rallye-re-import' / 'src'


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('base', type=Path); ap.add_argument('families', nargs='+')
    a = ap.parse_args()
    sys.path.insert(0, str(IMPORT_SRC))
    from master_rallye.retail_vehicle_contract import prelight_dx
    res = a.base / 'resources'; report = {}
    for fam in a.families:
        for name in ('car.dx', 'complete.dx'):
            p = res / 'DataGx/Vehicles' / fam / name
            raw = p.read_bytes(); new, info = prelight_dx(raw)
            p.write_bytes(new); report[f'{fam}/{name}'] = {**info, 'before_sha256': sha(raw), 'after_sha256': sha(new)}
    cat_path = a.base / 'catalog.json'
    if cat_path.is_file():
        cat = json.loads(cat_path.read_text(encoding='utf-8'))
        for r in cat.get('resources', []):
            p = res / r['path']
            if p.is_file():
                r['sha256'] = sha(p.read_bytes()); r['size'] = p.stat().st_size
        cat['prelight'] = {'tool': 'tools/vehicle_prelight.py', 'families': a.families}
        cat_path.write_text(json.dumps(cat, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
