"""Install ATMOSPHERE6.15 lamp rigs for add-on cars into a host (Roster RCX 07, owner 2026-11-17).

At night the renderer draws lamp glints only for cars with a rig in Atmosphere/vehicles/lamp_rigs.txt (or a PS2
fleet family): a rig is matched by one of its lens draws (texture name + vertex count + car-space bounds), its
tail/brake points come from the $switch(blight) OFF mesh. The host file listed only the 25 retail families, so added
cars had headlight projection (pose based) but no tail/brake glints.

The rigs are solved offline by ps2-research/pc-port/tools/atmosphere_lamp_rig.py from the installed car.dx (the
same solver as the retail rigs); this tool runs it for the given families, replaces their blocks in the host file
(other cars untouched, first run keeps a backup) and copies their night lens masks.

usage: py -3 tools/addon_lamp_rigs.py --host <game dir> --out <work dir> FAMILY [FAMILY ...]
"""
from __future__ import annotations
import argparse, hashlib, os, shutil, subprocess, sys
from pathlib import Path

G = Path(__file__).resolve().parents[2]
SOLVER = G / 'master-rallye-re-base/ps2-research/pc-port/tools/atmosphere_lamp_rig.py'
SOLVER_SRC = G / 'master-rallye-re-vehicles/src'


def blocks(text: str):
    head, cars, cur = [], {}, None
    for line in text.splitlines():
        if line.startswith('car '):
            cur = line.split()[1]; cars[cur] = [line]
        elif cur is None:
            head.append(line)
        else:
            cars[cur].append(line)
    return head, cars


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--host', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('families', nargs='+'); a = ap.parse_args()
    root = a.host / 'MRMods/Vehicles/active/resources/DataGx/Vehicles'
    env = dict(os.environ, PYTHONPATH=str(SOLVER_SRC))
    r = subprocess.run([sys.executable, str(SOLVER), str(a.out), '--root', str(root), *a.families], env=env, capture_output=True, text=True)
    print(r.stdout[-4000:])
    if r.returncode:
        print(r.stderr[-4000:]); return r.returncode
    _, new = blocks((a.out / 'lamp_rigs.txt').read_text())
    missing = [f for f in a.families if f not in new]
    if missing:
        raise SystemExit('no rig solved for ' + ', '.join(missing))
    for fam, lines in new.items():
        if not any(l.startswith('draw ') for l in lines):
            print(f'WARNING {fam}: no lens draw, the rig cannot be matched at runtime')
    target = a.host / 'Atmosphere/vehicles/lamp_rigs.txt'
    raw = target.read_bytes()
    backup = target.with_name(target.name + '.bak-' + hashlib.sha256(raw).hexdigest()[:8])
    if not any(p.name.startswith(target.name + '.bak-') for p in target.parent.iterdir()):
        shutil.copy2(target, backup)
    head, cars = blocks(raw.decode('ascii'))
    cars.update(new)
    target.write_text('\n'.join(head + [l for c in cars.values() for l in c]) + '\n', encoding='ascii')
    for fam in new:
        src = a.out / 'lamp_masks' / fam
        if src.is_dir():
            dst = target.parent / 'lamp_masks' / fam
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    print('installed', len(new), 'rigs into', target, '(cars now %d)' % len(cars))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
