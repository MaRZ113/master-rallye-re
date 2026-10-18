"""T4c: connected regions of the Turkey3 course where the PS2 ground (visual ground triangles) and the PC ground (tag100) differ in height."""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ground_delta_probe as g  # noqa: E402
import gcoll_columns as gc  # noqa: E402
import gcoll_walls_vs_limits as gw  # noqa: E402
import ps2_obj_to_dx as o  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-dx', type=Path, required=True)
    ap.add_argument('--step', type=float, default=6.0)
    ap.add_argument('--threshold', type=float, default=0.25)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    manifest, _ = o.t.load_pak(a.ps2_root / 'TNG.PAK')
    scene = o.w.decode_scene(o.extract(manifest, a.ps2_root, o.PSM_PATH))
    tris = g.ground_triangles(scene)
    grid = g.build_index(tris)
    xs = [p[0] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    pcn = gc.pc_nodes(a.pc_dx)
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    nx, nz = int((x1 - x0) // a.step) + 1, int((z1 - z0) // a.step) + 1
    cells = {}
    covered = 0
    for i in range(nx):
        for j in range(nz):
            x, z = x0 + i * a.step, z0 + j * a.step
            p2 = g.height_at(grid, x, z)
            if p2 is None:
                continue
            pc = gw.ground_at(pcn, x, z)
            if pc is None:
                continue
            covered += 1
            d = p2 - pc
            if abs(d) > a.threshold:
                cells[i, j] = d
    # 8-connected components
    seen, regions = set(), []
    for c in cells:
        if c in seen:
            continue
        stack, comp = [c], []
        seen.add(c)
        while stack:
            ci, cj = stack.pop()
            comp.append((ci, cj))
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    n = (ci + di, cj + dj)
                    if n in cells and n not in seen:
                        seen.add(n)
                        stack.append(n)
        ds = [cells[k] for k in comp]
        regions.append({'cells': len(comp), 'area': round(len(comp) * a.step * a.step), 'center': [round(x0 + sum(k[0] for k in comp) / len(comp) * a.step, 1),
                        round(z0 + sum(k[1] for k in comp) / len(comp) * a.step, 1)],
                        'min_dh': round(min(ds), 2), 'max_dh': round(max(ds), 2), 'mean_dh': round(sum(ds) / len(ds), 2),
                        'above': sum(d > 0 for d in ds), 'below': sum(d < 0 for d in ds)})
    regions.sort(key=lambda r: -r['cells'])
    summary = {'step': a.step, 'covered_cells': covered, 'differing_cells': len(cells), 'regions': len(regions),
               'differing_share': round(len(cells) / max(1, covered), 4),
               'above_cells': sum(d > 0 for d in cells.values()), 'below_cells': sum(d < 0 for d in cells.values())}
    print(summary)
    for r in regions[:25]:
        print(r)
    if a.out:
        a.out.write_text(json.dumps({'summary': summary, 'regions': regions}, indent=1))


if __name__ == '__main__':
    main()
