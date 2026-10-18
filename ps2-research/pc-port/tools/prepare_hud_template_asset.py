"""Build the PS2 HUD-TEMPLATE substitutes for the PC hud-template images (PS2HudTemplate=1).

PC Hud0.xml and PS2 HUD0.XML both draw the race HUD from the image bank hud\\hud-template (same 11 images, same
authored geometry for every image used here except image 3). The PC re-authored the art and stores one texture per
image; the PS2 packs the images into 64x64 GXI pages. For each image below, every texel of the substitute is mapped
PC uv -> authored xy (PC dxb triangle) -> PS2 uv (PSB triangle) -> PS2 GXI texel (raw row 0 = PSB v 1). GXI alpha is
8-bit (0x80 = half) and is kept as is. See ps2-research/hud-dump1/hud_substitute.py and findings.md (HUD-PORT4).

Image 3 (progress car) has another PS2 box (arrow 13x16 vs PC car 16x8): the PC quad is remapped onto the PS2 box at
draw time (x' = sx*x + tx, y' = sy*y + ty in authored units) and the PS2 arrow fills a 16x16 texture.

Writes .assets/hud/PS2HudTemplate.bin:
  'MRHT', u32 version 2, u32 count, then per image: u32 image, u32 PC width, u32 PC height, 32-byte PC level-0
  SHA-256, u32 width, u32 height, 4 f32 remap (sx, tx, sy, ty; identity when the boxes match), width*height*4 BGRA
  rows (D3D level-0 order).
Prints the C++ identity table for renderer/ps2_hud_template.hpp.
"""
from pathlib import Path
import hashlib, importlib.util, struct, sys

PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PORT.parent / 'hud-dump1'))
import hud_substitute as hs  # noqa: E402

PC_HUD = Path(r'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Hud')
IMAGES = (0, 2, 3, 4, 5, 6, 8, 9, 10)  # dial, needle, progress car, split marker, tick, finish flag, bar caps, middle
REMAP = {3: (16, 16)}
PS2_FILES = ['HUD-TEMPLATE.PSB'] + ['HUD-TEMPLATE_%03d.GXI' % i for i in range(8)]


def main():
    spec = importlib.util.spec_from_file_location('asset_common', PORT / 'docs/full-coverage/vehicles/audit.py')
    a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2 / 'TNG.PAK')
    staging = PORT / '.assets/hud/.ps2-hud-template'
    staging.mkdir(parents=True, exist_ok=True)
    for name in PS2_FILES:
        suffix = chr(92) + 'HUD' + chr(92) + name
        entry = next(e for e in manifest['entries'] if e['kind'] == 'file' and e['path'].upper().endswith(suffix))
        raw, _ = a.t.read_payload(entry, a.PS2 / 'TNG.000')
        (staging / name).write_bytes(raw)
    results = {rec['image']: (rec, px) for rec, px in hs.build(str(staging), str(PC_HUD), 'hud-template', REMAP)}
    blob = bytearray(b'MRHT' + struct.pack('<II', 2, len(IMAGES)))
    table = []
    for k in IMAGES:
        rec, px = results[k]
        if px is None or rec['covered'] < 0.5:
            raise ValueError('image %d not substitutable: %s' % (k, rec.get('skip')))
        w, h = rec['size']; pw, ph = rec['pc_size']; m = rec.get('remap', [1.0, 0.0, 1.0, 0.0])
        blob += struct.pack('<III', k, pw, ph) + bytes.fromhex(rec['pc_level0_sha256']) + struct.pack('<II4f', w, h, *m) + px
        table.append('    {%2d,%3d,%3d,"%s",\n        %3d,%3d,"%s",{%gf,%gf,%gf,%gf}},'
                     % (k, pw, ph, rec['pc_level0_sha256'], w, h, rec['ps2_sha256'], *m))
    target = PORT / '.assets/hud/PS2HudTemplate.bin'
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError('Private output link rejected')
    target.write_bytes(bytes(blob))
    print(target.name, len(blob), hashlib.sha256(blob).hexdigest())
    print('\n'.join(table))


if __name__ == '__main__':
    main()
