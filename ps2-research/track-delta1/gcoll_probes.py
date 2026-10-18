"""Pick concrete probe points on straight sections of the Turkey3 RaceLine for PC and PCSX2 runtime checks of the PS2 solid wall."""
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
import gcoll_walls_vs_limits as gw  # noqa: E402
import ps2_bsp  # noqa: E402


def unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


def main(pc_root, sdk_path, bsp_path, count=6):
    pc_root = Path(pc_root)
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    pcn = gc.pc_nodes(pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pc_xml = (pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    route = gm.markers(sdk, pc_xml, 'RaceLine')
    limits = {'left': gm.markers(sdk, pc_xml, 'LeftOuterLimit'), 'right': gm.markers(sdk, pc_xml, 'RightOuterLimit')}
    n = len(route)
    candidates = []
    for i in range(6, n - 6, 3):
        t_a = unit((route[i][0] - route[i - 6][0], route[i][1] - route[i - 6][1]))
        t_b = unit((route[i + 6][0] - route[i][0], route[i + 6][1] - route[i][1]))
        turn = math.degrees(math.acos(max(-1, min(1, t_a[0] * t_b[0] + t_a[1] * t_b[1]))))
        if turn < 8.0:
            candidates.append((turn, i, unit((t_a[0] + t_b[0], t_a[1] + t_b[1]))))
    rows = []
    chosen = 0
    last = -100
    for turn, i, t in candidates:
        if chosen >= count or i - last < 40:
            continue
        normals = {'left': (-t[1], t[0]), 'right': (t[1], -t[0])}
        for side, nrm in normals.items():
            r = route[i]
            w = gw.wall_distance(bsp, pcn, r, nrm)
            lim = min((math.dist(r, p) for p in limits[side]), default=None)
            if w is None:
                continue
            wx, wz = r[0] + nrm[0] * w, r[1] + nrm[1] * w
            g_route = gw.ground_at(pcn, r[0], r[1])
            g_wall = gw.ground_at(pcn, wx, wz)
            # keep only walls on real PC ground close to the road height and reachable within 150 units
            if g_route is None or g_wall is None or g_wall > 300 or abs(g_wall - g_route) > 40 or not 15 <= w <= 150:
                continue
            rows.append({'route_index': i, 'side': side, 'route_xz': [round(r[0], 1), round(r[1], 1)], 'route_ground_y': round(g_route, 1) if g_route is not None else None,
                         'wall_distance': round(w, 1), 'wall_xz': [round(wx, 1), round(wz, 1)], 'wall_ground_y': round(g_wall, 1) if g_wall is not None else None,
                         'nearest_pc_outer_limit_distance': round(lim, 1) if lim is not None else None,
                         'direction_xz': [round(nrm[0], 3), round(nrm[1], 3)]})
        if rows and rows[-1]['route_index'] == i:
            chosen += 1
            last = i
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:4])
