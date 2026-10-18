"""Hypothesis: a BSP plane `code` is the index of a tag103 triangle of the same course PSM (so it carries the material / $surfacetype)."""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE))
import detail_runtime as dr  # noqa: E402
import ps2_bsp  # noqa: E402
import tngtool as t  # noqa: E402


def tri_plane(p):
    a, b, c = p
    u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    ln = math.sqrt(sum(x * x for x in n))
    if ln < 1e-12:
        return None
    n = tuple(x / ln for x in n)
    return n, -sum(n[i] * a[i] for i in range(3))


def load_psm(root, course):
    """The single .PSM inside the course folder of the PackFS (folder names keep their underscores)."""
    man, _ = t.load_pak(root / 'TNG.PAK')
    folder = chr(92).join(['', 'TNG', 'DATAPSM', 'COURSE', course.upper()]) + chr(92)
    entries = [e for e in man['entries'] if e['kind'] == 'file' and e['path'].upper().startswith(folder)
               and e['path'].upper().endswith('.PSM')]
    if len(entries) != 1:
        raise SystemExit('expected one PSM in ' + folder + ', found %d' % len(entries))
    return t.read_payload(entries[0], root / 'TNG.000')[0]


def main(root, course, bsp_path):
    root = Path(root)
    land = dr.decode_landscape(load_psm(root, course))
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    nt = len(land.triangles) // 3
    stat = Counter()
    mismatch_examples = []
    for n, d, code in ((p[:3], p[3], p[4]) for p in bsp.plane_table):
        if code >= nt:
            stat['code_ge_triangle_count'] += 1
            continue
        pl = tri_plane(land.surface(code))
        if pl is None:
            stat['degenerate_triangle'] += 1
            continue
        pn, pd = pl
        dot = sum(n[i] * pn[i] for i in range(3))
        same = abs(abs(dot) - 1) < 1e-3 and abs((d - pd) if dot > 0 else (d + pd)) < 0.05
        stat['plane_equals_tag103_triangle' if same else 'plane_differs'] += 1
        if not same and len(mismatch_examples) < 3:
            mismatch_examples.append({'code': code, 'dot': round(dot, 4)})
    print(json.dumps({'course': course, 'tag103_triangles': nt, 'plane_table': len(bsp.plane_table), **stat,
                      'examples_of_mismatch': mismatch_examples}, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:4])
