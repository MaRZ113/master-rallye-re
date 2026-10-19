"""Per-course file locations for the PS2 -> PC course conversion, derived from data (no per-course constants).

Source: `cdelta1/course-pairs.json` (36 PS2 RaceTest XML <-> PC RaceTest XML pairs with their landscape names), the PS2 TNG.PAK manifest and the PC
retail tree. A landscape `course\\<dir>\\<name>` maps to the PS2 files `\\TNG\\DATAPSM\\COURSE\\<DIR>\\<NAME>.PSM` / `.BSP` and to the PC course DX
`DataGx/Course/<dir>/<name>.dx` (case-insensitive lookup).
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
sys.path.insert(0, str(RESEARCH / 'tools'))
import tngtool  # noqa: E402

PS2_ROOT = Path('D:/Game/Master Rallye PS2')
PC_ROOT = Path('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked')


@dataclass(frozen=True)
class Course:
    name: str               # PC RaceTest name, e.g. Turkey3
    ps2_xml: str
    pc_xml: Path
    ps2_psm: str
    ps2_bsp: str
    pc_dx: Path
    pc_landscape: str
    ps2_landscape: str


def _ci(root: Path, rel: str) -> Path:
    """Case-insensitive path below root."""
    cur = root
    for part in rel.replace('\\', '/').split('/'):
        hits = [p for p in cur.iterdir() if p.name.lower() == part.lower()]
        if not hits:
            raise FileNotFoundError(f'{part} not found under {cur}')
        cur = hits[0]
    return cur


@lru_cache(maxsize=1)
def manifest(ps2_root=PS2_ROOT):
    man, _ = tngtool.load_pak(Path(ps2_root) / 'TNG.PAK')
    return {e['path'].upper(): e for e in man['entries'] if e['kind'] == 'file'}


def read_ps2(path, ps2_root=PS2_ROOT):
    payload, _ = tngtool.read_payload(manifest(ps2_root)[path.upper()], Path(ps2_root) / 'TNG.000')
    return payload


def courses(ps2_root=PS2_ROOT, pc_root=PC_ROOT):
    out = []
    for p in json.loads((RESEARCH / 'cdelta1/course-pairs.json').read_text()):
        land = p['landscape']                     # course\dir\name (PS2)
        _, d, n = land.split('\\')
        psm = f'\\TNG\\DATAPSM\\COURSE\\{d}\\{n}.PSM'.upper()
        bsp = psm[:-4] + '.BSP'
        if psm not in manifest(ps2_root) or bsp not in manifest(ps2_root):
            raise FileNotFoundError(f'{psm} / {bsp} missing in TNG.PAK')
        pc_land = p.get('pc_landscape') or land
        _, pd, pn = pc_land.split('\\')
        out.append(Course(name=Path(p['pc']).stem, ps2_xml=p['ps2'], pc_xml=_ci(pc_root, p['pc']), ps2_psm=psm, ps2_bsp=bsp,
                          pc_dx=_ci(pc_root, f'DataGx/Course/{pd}/{pn}.dx'), pc_landscape=pc_land, ps2_landscape=land))
    return out


def course(name, **kw):
    for c in courses(**kw):
        if c.name.lower() == name.lower():
            return c
    raise KeyError(name)
