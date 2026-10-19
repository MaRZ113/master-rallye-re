"""TRACK-GROUND1: what are the unexplained PS2 PSM vertex floats (+28, +32)? Test them against the PC noise UV (course DX UV set 1) and UV set 0.

PS2 vertex (52 bytes): +0 normal xyz, +12 0.0, +16 colour word, +20 UV, +28/+32 unknown pair, +36 position, +48 1.0.
For PS2 ground triangles with a PC ground triangle of the same footprint and height, vertices are paired by position and the pair (f28, f32) is compared
with the PC noise UV and with the PC base UV (modulo integer offsets).
"""
import argparse
import collections
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TD1 = HERE.parent / 'track-delta1'
sys.path.insert(0, str(TD1))
sys.path.insert(0, str(TD1.parent / 'tools'))
sys.path.insert(0, str(TD1.parent.parent / 'src'))
import ps2_obj_to_dx as o  # noqa: E402
import ps2_terrain as terrain  # noqa: E402
import ground_clusters as gcl  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402


def frac(v):
    return v - round(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ps2-root', type=Path, default=Path('D:/Game/Master Rallye PS2'))
    ap.add_argument('--pc-dx', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    model = parse_course_dx_bytes(a.pc_dx.read_bytes(), 'pc')
    U0, U1, P = model.uv_sets[0].values, model.uv_sets[1].values, model.vertices.positions
    pos = collections.defaultdict(list)
    for i, p in enumerate(P):
        pos[tuple(round(c, 2) for c in p)].append(i)
    noise_draw = set()
    for d in model.physical_draws:
        if len(d.texture_tuple) > 2 and d.texture_tuple[2] == 'noise-tga':
            for k in range(d.triangle_count):
                for j in range(3):
                    noise_draw.add(model.local_indices[d.index_start + 3 * k + j] + d.vertex_base)
    manifest, _ = o.t.load_pak(a.ps2_root / 'TNG.PAK')
    scene = o.w.decode_scene(o.extract(manifest, a.ps2_root, o.PSM_PATH))
    pairs = []
    for mesh in scene.meshes:
        if not ('shader(ground)' in mesh['material'].lower() or any('noise' in x['name'].lower() for x in mesh['textures'])):
            continue
        for strip in mesh['strips']:
            for newest in range(strip['start'] + 2, strip['start'] + strip['count']):
                for vi in (newest - 2, newest - 1, newest):
                    pos3 = tuple(round(c, 2) for c in scene.position(vi))
                    ids = [i for i in pos.get(pos3, []) if i in noise_draw]
                    if len(ids) == 1:
                        f = struct.unpack_from('<13f', scene.payload, 32 + vi * 52)
                        pairs.append((f, ids[0]))
    n = len(pairs)
    out = {'pairs': n}
    for label, idx in (('f28_f32 vs PC noise UV (exact)', U1), ('f28_f32 vs PC base UV (exact)', U0)):
        out[label] = sum(1 for f, i in pairs if abs(f[7] - idx[i][0]) < 1e-3 and abs(f[8] - idx[i][1]) < 1e-3)
        out[label + ' modulo 1'] = sum(1 for f, i in pairs if abs(frac(f[7] - idx[i][0])) < 2e-3 and abs(frac(f[8] - idx[i][1])) < 2e-3)
    out['f28_f32 inside 0..1.1 (share)'] = round(sum(1 for f, i in pairs if -0.05 <= f[7] <= 1.1 and -0.05 <= f[8] <= 1.1) / max(1, n), 3)
    out['f28_f32 min/max'] = [round(min(min(f[7], f[8]) for f, _ in pairs), 3), round(max(max(f[7], f[8]) for f, _ in pairs), 3)]
    print(json.dumps(out, indent=1))
    if a.out:
        a.out.write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
