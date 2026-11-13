"""Evo 2 paints of an installed MR car as Vehicle Manager paint input (docs/vehicle-manager/VEHICLE_OPTIONS_DESIGN.md).

The installed body texture of a converted Evo 2 truck is one colorList record of the source catalog (for the 4Runner:
record 1, HSV delta 0,0,0). Every other record is recomputed with the original recolouring replayed from the owner's
4x42.exe (evo2_color.reconstruct, exact pre-gloss CPU RGB) and written as a replacement of that texture: same file
name, same 20-byte DXT header, same stored row order. Output: <out>/<n>/<texture>.dxt and <out>/paints.json for
`vehicle_manager.py make-paint --spec <out>/paints.json`. Paint 0 = the installed record (no files).

Nothing in the game or the source scene is modified.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from master_rallye import universal_vehicle_scene as u          # noqa: E402
from master_rallye.source_adapters import evo2_color as c        # noqa: E402


def stored_bgra(rgba: bytes) -> bytes:
    out = bytearray(len(rgba))
    out[0::4], out[1::4], out[2::4], out[3::4] = rgba[2::4], rgba[1::4], rgba[0::4], rgba[3::4]
    return bytes(out)


def run(scene_path: Path, member: str, installed: Path, executable: Path, base: str, out: Path) -> dict:
    scene = u.load_scene(scene_path)
    tex = next(t for t in scene['textures'] if t['source']['member'].casefold() == member.casefold())
    ch = tex['source_channels']
    raw = (scene_path.parent / ch['raw_samples_path']).read_bytes()
    pal = (scene_path.parent / ch['palette_path']).read_bytes()
    size = tex['width']
    exe = executable.read_bytes()
    inst = installed.read_bytes()
    header, payload = inst[:20], inst[20:]
    if len(payload) != size * size * 4:
        raise ValueError('installed texture is not the source texture size')
    records = scene['source']['catalog_original']['color_records']
    rgba = {}
    for i, r in enumerate(records):
        rgba[i] = c.reconstruct(exe, raw, pal, size, [float(v) for v in r['value'].split(',')[:3]])['rgba']
    own = [i for i in rgba if stored_bgra(rgba[i]) == payload]
    if len(own) != 1:
        raise ValueError(f'installed texture matches {len(own)} catalog records exactly (need one)')
    order = own + [i for i in range(len(records)) if i != own[0]]
    out.mkdir(parents=True, exist_ok=False)
    paints = []
    for n, i in enumerate(order):
        fields = records[i]['value'].split(',')
        entry = {'rgb': [int(fields[3]), int(fields[4]), int(fields[5])], 'source_record': i}
        if n:
            d = out / str(n)
            d.mkdir()
            (d / installed.name).write_bytes(header + stored_bgra(rgba[i]))
            entry['dir'] = str(n)
        paints.append(entry)
    spec = {'base': base, 'default': 0, 'name': f'{base} paints (Evo 2 catalog)', 'texture': installed.name, 'paints': paints}
    (out / 'paints.json').write_text(json.dumps(spec, indent=1) + '\n')
    return spec


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--scene', type=Path, required=True, help='Evo 2 source scene.json of the truck')
    p.add_argument('--member', default='art/4runnersr5.tif', help='paintable source texture member')
    p.add_argument('--installed', type=Path, required=True, help='installed DXT of that texture (MR car folder)')
    p.add_argument('--exe', type=Path, required=True, help="owner's 4x42.exe")
    p.add_argument('--base', required=True, help='MR family folder, e.g. Evo2FourRunner')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(run(a.scene, a.member, a.installed, a.exe, a.base, a.out), indent=1))
