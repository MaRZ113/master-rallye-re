"""Where does PS2 report solid space above matching PC ground? Distance to the RaceLine and extent of the solid column."""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import course_delta as cd  # noqa: E402
import geometry_delta as g  # noqa: E402
import ps2_bsp  # noqa: E402
import bsp_query as q  # noqa: E402
import gcoll_columns as gc  # noqa: E402


def main(ps2_root, pc_root, sdk, bsp_path, limit=2000):
    a, b, _ = g.load_pair(Path(ps2_root), Path(pc_root), Path(sdk), 'TURKEY3')
    _, forward, _ = g.compare(a, b)
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    sdkmod, _ = cd.sdk_modules(Path(sdk))
    scene, _ = cd.parse_scene((Path(pc_root) / 'DataScene/RaceTest/Turkey3.xml').read_bytes(), 'pc', sdkmod)
    route = scene['_route_points']
    exact, _extra = gc.columns(a, forward, limit)
    rows = []
    for c in exact:
        top = (c[0], c[1] + 3.0, c[2])
        bot = (c[0], c[1] - 6.0, c[2])
        t = q.ps2_first_solid_t(bsp, top, bot)
        if t is None:
            continue
        starts_solid = t <= 1e-9
        d = min(math.dist((c[0], c[2]), (p[0], p[2])) for p in route)
        height = None
        if starts_solid:
            # extent: march up in 1 unit steps while the PS2 tree says solid
            h = 3.0
            while h < 200 and q.ps2_is_solid(bsp, (c[0], c[1] + h, c[2])):
                h += 1.0
            height = h
        rows.append((starts_solid, d, height))
    solid = [r for r in rows if r[0]]
    other = [r for r in rows if not r[0]]
    def pct(v, p):
        v = sorted(v)
        return round(v[int(p * (len(v) - 1))], 1) if v else None
    print(json.dumps({
        'columns_with_ps2_contact': len(rows), 'start_in_solid': len(solid),
        'route_distance_start_in_solid': {p: pct([r[1] for r in solid], p / 100) for p in (10, 50, 90)},
        'route_distance_other': {p: pct([r[1] for r in other], p / 100) for p in (10, 50, 90)},
        'solid_column_height_above_ground': {p: pct([r[2] for r in solid], p / 100) for p in (10, 50, 90, 99)},
        'solid_within_30_of_route': sum(r[1] <= 30 for r in solid), 'other_within_30_of_route': sum(r[1] <= 30 for r in other),
    }, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:5])
