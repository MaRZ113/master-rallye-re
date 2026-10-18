"""Where is the PS2 solid wall relative to the outer limit lists? Marching from the RaceLine toward each limit marker.

For a limit marker L the nearest RaceLine point R defines the direction R->L. Starting at R, the walk advances in 2-unit steps until the
PS2 BSP is solid at (PC ground height + 3). Reported: wall distance minus limit distance (negative = the wall stands inside the limit).
"""
import json
import math
import sys
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


def ground_at(pcn, x, z):
    t = gc.pc_first_contact(pcn, (x, gm.Y_TOP, z), (x, gm.Y_BOTTOM, z))
    return None if t is None else gm.Y_TOP + (gm.Y_BOTTOM - gm.Y_TOP) * t


def wall_distance(bsp, pcn, r, direction, max_d=400.0, step=2.0):
    d = 0.0
    while d <= max_d:
        x, z = r[0] + direction[0] * d, r[1] + direction[1] * d
        g = ground_at(pcn, x, z)
        if g is not None and q.ps2_is_solid(bsp, (x, g + 3.0, z)):
            return d
        d += step
    return None


def main(pc_root, sdk_path, bsp_path):
    pc_root = Path(pc_root)
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    pcn = gc.pc_nodes(pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pc_xml = (pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    ps2_xml = (HERE.parent / 'data/cdelta1/cache/TNG/DATASCENE/RACETEST/TURKEY3.XML').read_bytes()
    route = gm.markers(sdk, pc_xml, 'RaceLine')
    sets = {'PC LeftOuterLimit': gm.markers(sdk, pc_xml, 'LeftOuterLimit'), 'PC RightOuterLimit': gm.markers(sdk, pc_xml, 'RightOuterLimit'),
            'PS2 LeftOuterLimit2': gm.markers(sdk, ps2_xml, 'LeftOuterLimit2'), 'PS2 RightOuterLimit2': gm.markers(sdk, ps2_xml, 'RightOuterLimit2')}
    out = {}
    for name, pts in sets.items():
        diffs, no_wall, start_solid = [], 0, 0
        for lim in pts:
            r = min(route, key=lambda p: math.dist(p, lim))
            dist = math.dist(r, lim)
            if dist < 1e-6:
                continue
            direction = ((lim[0] - r[0]) / dist, (lim[1] - r[1]) / dist)
            w = wall_distance(bsp, pcn, r, direction)
            if w is None:
                no_wall += 1
                continue
            if w == 0.0:
                start_solid += 1
            diffs.append(w - dist)
        diffs.sort()
        def pct(p):
            return round(diffs[int(p * (len(diffs) - 1))], 1) if diffs else None
        out[name] = {'markers': len(pts), 'wall_found': len(diffs), 'no_wall_within_400': no_wall, 'route_point_already_solid': start_solid,
                     'wall_minus_limit_percentiles': {p: pct(p / 100) for p in (5, 25, 50, 75, 95)},
                     'wall_within_10_of_limit': sum(abs(x) <= 10 for x in diffs), 'wall_inside_limit_by_more_than_10': sum(x < -10 for x in diffs),
                     'wall_beyond_limit_by_more_than_10': sum(x > 10 for x in diffs)}
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:4])
