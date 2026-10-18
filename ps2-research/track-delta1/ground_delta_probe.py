"""T4c: how different are the PS2 ground (visual ground-shader triangles of the PSM) and the PC ground (tag100 first contact) around given points?

For every grid cell around each centre: PS2 height = highest PS2 ground triangle covering the cell centre (barycentric), PC height = first solid
contact of the PC tag100 from above. Reports the difference distribution and the share of cells where PS2 is above / below by more than 0.25.
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT.parent / 'src'))
sys.path.insert(0, str(HERE))
import gcoll_columns as gc  # noqa: E402
import gcoll_walls_vs_limits as gw  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402

CELL = 8.0


def ground_triangles(scene):
    tris = []
    for mesh in scene.meshes:
        if 'shader(ground)' not in mesh['material'].lower():
            continue
        for pos, _, _ in o.source_triangles(scene, mesh):
            tris.append(pos)
    return tris


def build_index(tris):
    grid = defaultdict(list)
    for t in tris:
        xs, zs = [p[0] for p in t], [p[2] for p in t]
        for cx in range(int(min(xs) // CELL), int(max(xs) // CELL) + 1):
            for cz in range(int(min(zs) // CELL), int(max(zs) // CELL) + 1):
                grid[cx, cz].append(t)
    return grid


def height_at(grid, x, z):
    best = None
    for (ax, ay, az), (bx, by, bz), (cx, cy, cz) in grid.get((int(x // CELL), int(z // CELL)), []):
        den = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        if abs(den) < 1e-9:
            continue
        w1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / den
        w2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / den
        w3 = 1 - w1 - w2
        if min(w1, w2, w3) >= -1e-6:
            y = w1 * ay + w2 * by + w3 * cy
            if best is None or y > best:
                best = y
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-dx', type=Path, required=True)
    ap.add_argument('--objects-report', type=Path, required=True, help='report.json of ps2_course_objects.py (centres)')
    ap.add_argument('--radius', type=float, default=60.0)
    ap.add_argument('--step', type=float, default=4.0)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    manifest, _ = o.t.load_pak(a.ps2_root / 'TNG.PAK')
    scene = o.w.decode_scene(o.extract(manifest, a.ps2_root, o.PSM_PATH))
    grid = build_index(ground_triangles(scene))
    pcn = gc.pc_nodes(a.pc_dx)
    report = json.loads(a.objects_report.read_text())
    out = []
    for model in report['models']:
        for inst in model['instances']:
            cx, _, cz = inst['translation']
            diffs, uncovered = [], 0
            n = int(a.radius // a.step)
            for i in range(-n, n + 1):
                for j in range(-n, n + 1):
                    x, z = cx + i * a.step, cz + j * a.step
                    p2 = height_at(grid, x, z)
                    pc = gw.ground_at(pcn, x, z)
                    if p2 is None or pc is None:
                        uncovered += 1
                        continue
                    diffs.append(p2 - pc)
            diffs.sort()
            total = len(diffs) + uncovered

            def pct(q):
                return round(diffs[int(q * (len(diffs) - 1))], 2) if diffs else None
            out.append({'egg': inst['egg'], 'center': [cx, cz], 'cells': total, 'uncovered': uncovered,
                        'ps2_above_025': round(sum(d > .25 for d in diffs) / max(1, len(diffs)), 3),
                        'ps2_below_025': round(sum(d < -.25 for d in diffs) / max(1, len(diffs)), 3),
                        'diff_percentiles': {str(q): pct(q / 100) for q in (5, 25, 50, 75, 95)}})
            print(out[-1])
    if a.out:
        a.out.write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
