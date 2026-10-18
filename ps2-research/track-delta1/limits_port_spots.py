"""Pick test spots between the PC outer border and the PS2 Limit2 border on Turkey3 (PC would say OFF COURSE, PS2 border still inside)."""
import math
import re
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
import limits_port as lp  # noqa: E402


def crossing(o, d, pts, max_d=300.0):
    best = None
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ex, ez = b[0] - a[0], b[1] - a[1]
        den = d[0] * ez - d[1] * ex
        if abs(den) < 1e-9:
            continue
        t = ((a[0] - o[0]) * ez - (a[1] - o[1]) * ex) / den
        u = ((a[0] - o[0]) * d[1] - (a[1] - o[1]) * d[0]) / den
        if 0 <= u <= 1 and 0 < t <= max_d and (best is None or t < best):
            best = t
    return best


def main(pc_root, sdk_path, ps2_scene):
    pc_root = Path(pc_root)
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pc = (pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    ps2 = Path(ps2_scene).read_bytes()
    pcn = gc.pc_nodes(pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
    route = gm.markers(sdk, pc, 'RaceLine')

    def pts(d, n):
        s, e = lp.list_span(d, n)
        return [(float(m.split()[0]), float(m.split()[2])) for m in re.findall(rb'Marker Pos" Type="Vector3" Value="([^"]+)"', d[s:e])]
    sets = {'left': (pts(pc, 'LeftOuterLimit'), pts(ps2, 'LeftOuterLimit2')), 'right': (pts(pc, 'RightOuterLimit'), pts(ps2, 'RightOuterLimit2'))}
    rows = []
    for i in range(6, len(route) - 6, 2):
        a, b = route[i - 6], route[i + 6]
        t = (b[0] - a[0], b[1] - a[1]); n = math.hypot(*t); t = (t[0] / n, t[1] / n)
        for side, nrm in (('left', (-t[1], t[0])), ('right', (t[1], -t[0]))):
            pc_d, ps_d = (crossing(route[i], nrm, p) for p in sets[side])
            if pc_d is None or ps_d is None or ps_d - pc_d < 15:
                continue
            mid = pc_d + (ps_d - pc_d) * 0.5
            x, z = route[i][0] + nrm[0] * mid, route[i][1] + nrm[1] * mid
            g = gw.ground_at(pcn, x, z)
            g0 = gw.ground_at(pcn, *route[i])
            if g is None or g0 is None or abs(g - g0) > 25:
                continue
            rows.append((ps_d - pc_d, i, side, pc_d, ps_d, x, g, z, math.degrees(math.atan2(nrm[0], nrm[1]))))
    rows.sort(reverse=True)
    chosen = []
    for r in rows:
        if all(abs(r[1] - c[1]) > 60 for c in chosen):
            chosen.append(r)
        if len(chosen) == 3:
            break
    for k, r in enumerate(chosen, 1):
        print(f'; spot {k}: route idx {r[1]}, {r[2]} side, PC border at {r[3]:.0f}, PS2 border at {r[4]:.0f} from the road; heading to the border {r[8]:.0f} deg')
        print(f'Point{k}={r[5]:.1f},{r[6] + 1.5:.1f},{r[7]:.1f},0')


if __name__ == '__main__':
    main(*sys.argv[1:4])
