"""T4c: triangle-level ground delta of Turkey3 and its spatial clusters.

PS2 ground triangle = triangle of a PSM mesh whose material has shader(ground); PC ground triangle = triangle of a course-DX draw whose third texture
slot is noise-tga (the PC ground family). A triangle is 'exact' when the other side has a triangle with the same three vertices (0.001).
Clusters: non-exact triangles of both sides merged when their XZ bounding boxes are within `gap` units.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT.parent / 'src'))
sys.path.insert(0, str(HERE))
import ps2_obj_to_dx as o  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402


def key(points):
    return tuple(sorted(tuple(round(c, 3) for c in p) for p in points))


def load(ps2_root, pc_dx):
    manifest, _ = o.t.load_pak(ps2_root / 'TNG.PAK')
    scene = o.w.decode_scene(o.extract(manifest, ps2_root, o.PSM_PATH))
    ps2 = []  # (points, uv, colors, texture, mesh path, is_ground)
    for mesh in scene.meshes:
        ground = 'shader(ground)' in mesh['material'].lower()
        tex = mesh['textures'][0]['name'] if mesh['textures'] else ''
        for pos, uv, col in o.source_triangles(scene, mesh):
            ps2.append({'p': pos, 'uv': uv, 'col': col, 'tex': tex, 'mesh': mesh['path'], 'ground': ground})
    model = parse_course_dx_bytes(pc_dx.read_bytes(), 'pc')
    pc = []  # triangles with the file offset of their three local indices
    for draw in model.physical_draws:
        ground = len(draw.texture_tuple) > 2 and draw.texture_tuple[2] == 'noise-tga'
        for k in range(draw.triangle_count):
            first = draw.index_start + 3 * k
            idx = [model.local_indices[first + j] + draw.vertex_base for j in range(3)]
            pts = [model.vertices.positions[i] for i in idx]
            pc.append({'p': tuple(pts), 'ground': ground, 'draw': draw.draw_index, 'first_index': first})
    return scene, ps2, model, pc


def cluster(items, gap):
    boxes = []
    for it in items:
        xs, zs = [p[0] for p in it['p']], [p[2] for p in it['p']]
        boxes.append([min(xs), min(zs), max(xs), max(zs)])
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    cell = max(gap, 1.0) * 2
    grid = defaultdict(list)
    for i, b in enumerate(boxes):
        for cx in range(int((b[0] - gap) // cell), int((b[2] + gap) // cell) + 1):
            for cz in range(int((b[1] - gap) // cell), int((b[3] + gap) // cell) + 1):
                for j in grid[cx, cz]:
                    bj = boxes[j]
                    if b[0] - gap <= bj[2] and bj[0] - gap <= b[2] and b[1] - gap <= bj[3] and bj[1] - gap <= b[3]:
                        parent[find(i)] = find(j)
                grid[cx, cz].append(i)
    groups = defaultdict(list)
    for i in range(len(items)):
        groups[find(i)].append(i)
    return list(groups.values()), boxes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-dx', type=Path, required=True)
    ap.add_argument('--gap', type=float, default=4.0)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    _, ps2, _, pc = load(a.ps2_root, a.pc_dx)
    ps2_keys = {key(t['p']) for t in ps2}
    pc_keys = {key(t['p']) for t in pc}
    ps2_non = [t for t in ps2 if t['ground'] and key(t['p']) not in pc_keys]
    pc_non = [t for t in pc if t['ground'] and key(t['p']) not in ps2_keys]
    print('PS2 ground triangles', sum(t['ground'] for t in ps2), 'non-exact', len(ps2_non), '| PC ground triangles', sum(t['ground'] for t in pc), 'non-exact', len(pc_non))
    items = [dict(t, side='ps2') for t in ps2_non] + [dict(t, side='pc') for t in pc_non]
    groups, boxes = cluster(items, a.gap)
    out = []
    for g in groups:
        b = [min(boxes[i][0] for i in g), min(boxes[i][1] for i in g), max(boxes[i][2] for i in g), max(boxes[i][3] for i in g)]
        ys = [p[1] for i in g for p in items[i]['p']]
        out.append({'bbox_xz': [round(x, 1) for x in b], 'y_range': [round(min(ys), 1), round(max(ys), 1)],
                    'ps2_triangles': sum(items[i]['side'] == 'ps2' for i in g), 'pc_triangles': sum(items[i]['side'] == 'pc' for i in g)})
    out.sort(key=lambda r: -(r['ps2_triangles'] + r['pc_triangles']))
    print(len(out), 'clusters; largest:')
    for r in out[:12]:
        print(r)
    if a.out:
        a.out.write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
