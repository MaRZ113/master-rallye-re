"""Static behaviour comparison around the nine Turkey3 runtime-probe points.

For each probe point the PS2 BSP is walked outward in 16 compass directions (2-unit steps, tested at PC ground + 3) and the distance to the
first PS2 solid is reported next to the route tangent. Also counts, per outer-limit marker set, how often the wall stands inside the
limit line (PS2 would block the car before the PC OFF COURSE rule fires) and how much inside.
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
import gcoll_walls_vs_limits as gw  # noqa: E402
import ps2_bsp  # noqa: E402

POINTS = {1: (3161.5, 168.3), 2: (3182.7, 176.4), 3: (3217.6, 189.7), 4: (2592.5, 309.6), 5: (2585.9, 280.3), 6: (2574.5, 229.5),
          7: (2387.6, -686.3), 8: (2368.2, -681.4), 9: (2337.3, -673.5)}


def main(pc_root, sdk_path, bsp_path, out_path):
    pc_root = Path(pc_root)
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    pcn = gc.pc_nodes(pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pc_xml = (pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    route = gm.markers(sdk, pc_xml, 'RaceLine')
    out = {'points': {}}
    for k, (x, z) in POINTS.items():
        i = min(range(len(route)), key=lambda j: math.dist(route[j], (x, z)))
        a, b = route[max(i - 3, 0)], route[min(i + 3, len(route) - 1)]
        tangent = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
        rays = {}
        for deg in range(0, 360, 22):
            r = math.radians(deg)
            w = gw.wall_distance(bsp, pcn, (x, z), (math.sin(r), math.cos(r)), max_d=120.0)
            rays[deg] = None if w is None else round(w, 1)
        out['points'][k] = {'xz': [x, z], 'nearest_route_index': i, 'route_heading_deg_atan2_dx_dz': round(tangent, 1),
                            'wall_distance_by_heading_deg': rays}
    open(out_path, 'w').write(json.dumps(out, indent=1))
    for k, v in out['points'].items():
        print(k, v['xz'], 'route', v['route_heading_deg_atan2_dx_dz'], {d: w for d, w in v['wall_distance_by_heading_deg'].items() if w is not None and w <= 40})


if __name__ == '__main__':
    main(*sys.argv[1:5])
