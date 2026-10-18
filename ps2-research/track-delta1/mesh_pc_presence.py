"""Per PS2 mesh of a course PSM: share of its vertices that exist (within 0.01) in the PC course DX; low share = candidate MISSING_ON_PC object.

Output: JSON list (mesh path, material, textures, vertex count, share, centroid, bbox) for meshes below the threshold.
"""
import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT.parent / 'src'))
import tngtool as t  # noqa: E402
import water_runtime as w  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402

BACKSLASH = chr(92)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-dx', type=Path, required=True)
    ap.add_argument('--course', default='TURKEY3')
    ap.add_argument('--threshold', type=float, default=0.5)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    pc = parse_course_dx_bytes(a.pc_dx.read_bytes(), 'pc')
    pos = {tuple(round(x, 2) for x in p) for p in pc.vertices.positions}
    manifest, _ = t.load_pak(a.ps2_root / 'TNG.PAK')
    path = BACKSLASH + 'TNG' + BACKSLASH + 'DATAPSM' + BACKSLASH + 'COURSE' + BACKSLASH + a.course + BACKSLASH + a.course + '.PSM'
    entry = [e for e in manifest['entries'] if e['kind'] == 'file' and t.logical_path(e['path']) == t.logical_path(path)][0]
    scene = w.decode_scene(t.read_payload(entry, a.ps2_root / 'TNG.000')[0])
    rows = []
    for mesh in scene.meshes:
        idx = set()
        for st in mesh['strips']:
            idx.update(range(st['start'], st['start'] + st['count']))
        if not idx:
            continue
        pts = [scene.position(i) for i in idx]
        hit = sum(1 for p in pts if tuple(round(x, 2) for x in p) in pos)
        rows.append({'path': mesh['path'], 'material': mesh['material'], 'textures': [x['name'].split(BACKSLASH)[-1] for x in mesh['textures']],
                     'vertices': len(idx), 'pc_share': round(hit / len(idx), 3),
                     'centroid': [round(sum(p[i] for p in pts) / len(pts), 2) for i in range(3)],
                     'bbox': [[round(min(p[i] for p in pts), 2) for i in range(3)], [round(max(p[i] for p in pts), 2) for i in range(3)]]})
    low = [r for r in rows if r['pc_share'] < a.threshold]
    by = collections.defaultdict(list)
    for r in low:
        by[(r['material'].split('$')[0].strip(), tuple(r['textures']))].append(r)
    print(len(rows), 'meshes,', len(low), 'below', a.threshold)
    for key, items in sorted(by.items(), key=lambda kv: -sum(r['vertices'] for r in kv[1])):
        print(key, len(items), 'meshes', sum(r['vertices'] for r in items), 'vertices', [(r['path'], r['pc_share']) for r in items][:3])
    if a.out:
        a.out.write_text(json.dumps(low, indent=1))


if __name__ == '__main__':
    main()
