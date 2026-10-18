"""G-COLL census over all 36 paired courses: share of PS2-solid space above PC ground by distance from the RaceLine.

For each pair of cdelta1/course-pairs.json: PS2 BSP (PackFS) and PC tag100 (retail DX) of the paired landscapes, RaceLine from the PC scene.
Grid step 32 over the route box plus 300. Ground = PC tag100 first contact from above. PS2 solidity per T2-BSP-FORMAT.md.
"""
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import course_delta as cd  # noqa: E402
import gcoll_columns as gc  # noqa: E402
import gcoll_map as gm  # noqa: E402
import ps2_bsp  # noqa: E402
import bsp_query as q  # noqa: E402
import tngtool as t  # noqa: E402

BANDS = ((0, 50), (50, 100), (100, 200), (200, 1e9))
SLASH = chr(92)


def find_dx(pc_root, landscape):
    """DataGx/<landscape>.dx matched case-insensitively."""
    rel = landscape.replace(SLASH, '/').lower() + '.dx'
    cur = Path(pc_root) / 'DataGx'
    for part in rel.split('/'):
        match = [p for p in cur.iterdir() if p.name.lower() == part]
        if not match:
            return None
        cur = match[0]
    return cur


def census_course(pair, root, man, pc_root, sdk, step=32.0):
    landscape = pair['landscape']
    bsp_path = (SLASH + 'TNG' + SLASH + 'DATAPSM' + SLASH + landscape + '.bsp').upper()
    entries = [e for e in man['entries'] if e['kind'] == 'file' and e['path'].upper() == bsp_path]
    if len(entries) != 1:
        return {'error': 'BSP not found ' + bsp_path}
    bsp = ps2_bsp.parse(t.read_payload(entries[0], root / 'TNG.000')[0])
    dx = find_dx(pc_root, pair['pc_landscape'])
    if dx is None:
        return {'error': 'PC DX not found'}
    pcn = gc.pc_nodes(dx)
    xml = (Path(pc_root) / pair['pc']).read_bytes()
    route = gm.markers(sdk, xml, 'RaceLine')
    if not route:
        return {'error': 'no RaceLine'}
    xs, zs = [p[0] for p in route], [p[1] for p in route]
    m = 300.0
    x0, x1, z0, z1 = min(xs) - m, max(xs) + m, min(zs) - m, max(zs) + m
    bands = [[0, 0, 0] for _ in BANDS]  # cells, solid at +3, solid at +100
    cells = 0
    x = x0
    while x <= x1:
        z = z0
        while z <= z1:
            tt = gc.pc_first_contact(pcn, (x, gm.Y_TOP, z), (x, gm.Y_BOTTOM, z))
            if tt is not None:
                ground = gm.Y_TOP + (gm.Y_BOTTOM - gm.Y_TOP) * tt
                d = min(math.dist((x, z), p) for p in route)
                b = next(i for i, (lo, hi) in enumerate(BANDS) if lo <= d < hi)
                bands[b][0] += 1
                bands[b][1] += q.ps2_is_solid(bsp, (x, ground + 3.0, z))
                bands[b][2] += q.ps2_is_solid(bsp, (x, ground + 100.0, z))
                cells += 1
            z += step
        x += step
    return {'bsp_nodes': len(bsp.nodes), 'pc_tag100_nodes': len(pcn), 'route_points': len(route), 'cells_with_pc_ground': cells,
            'bands': [{'distance': f'{int(lo)}-{int(hi) if hi < 1e8 else "inf"}', 'cells': c, 'ps2_solid_at_3_percent': round(100 * s3 / c, 1) if c else None,
                       'ps2_solid_at_100_percent': round(100 * s100 / c, 1) if c else None}
                      for (lo, hi), (c, s3, s100) in zip(BANDS, bands)]}


def main(ps2_root, pc_root, sdk_path, output):
    root = Path(ps2_root)
    man, _ = t.load_pak(root / 'TNG.PAK')
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pairs = json.loads((HERE.parent / 'cdelta1/course-pairs.json').read_text(encoding='utf-8'))
    rows = []
    for pair in pairs:
        started = time.time()
        res = census_course(pair, root, man, pc_root, sdk)
        res.update(course=pair['ps2'].replace(SLASH, '/').split('/')[-1][:-4], landscape=pair['landscape'], seconds=round(time.time() - started, 1))
        rows.append(res)
        print(res['course'], res.get('error') or [b['ps2_solid_at_3_percent'] for b in res['bands']], res['seconds'], flush=True)
    Path(output).write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main(*sys.argv[1:5])
