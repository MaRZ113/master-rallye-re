"""Find which BSP link is the front half-space and what field_0 means, using Turkey3 visual ground triangles.

For ground triangles with an upward normal, a point slightly above should be in empty space and a point slightly below
inside solid. The orientation that makes (above, below) descriptors consistent is taken as correct.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE))
import geometry_delta as g  # noqa: E402
import ps2_bsp  # noqa: E402
import bsp_query as q  # noqa: E402


def sample_faces(a, limit=3000, min_ny=0.95):
    out = []
    for f in a.faces:
        if 'shader(ground)' not in a.groups[f.group]['material'].lower():
            continue
        n = g.normal(f.points)
        if abs(n[1]) < min_ny:
            continue
        if n[1] < 0:
            n = tuple(-x for x in n)
        c = tuple(sum(p[i] for p in f.points) / 3 for i in range(3))
        out.append((c, n))
    step = max(1, len(out) // limit)
    return out[::step]


def main(ps2_root, pc_root, sdk, bsp_path, delta=0.3):
    a, _, _ = g.load_pair(Path(ps2_root), Path(pc_root), Path(sdk), 'TURKEY3')
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    faces = sample_faces(a)
    result = {'samples': len(faces), 'delta': delta}
    for child_is_front in (True, False):
        pairs = Counter()
        for c, n in faces:
            up = tuple(c[i] + delta * n[i] for i in range(3))
            dn = tuple(c[i] - delta * n[i] for i in range(3))
            pairs[(q.leaf_class(q.classify(bsp.nodes, up, child_is_front)),
                   q.leaf_class(q.classify(bsp.nodes, dn, child_is_front)))] += 1
        result['child_is_front=' + str(child_is_front)] = {f'{k[0]} -> {k[1]}': v for k, v in pairs.most_common(8)}
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:5])
