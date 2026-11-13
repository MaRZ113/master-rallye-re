"""Total Drivin' (PS1) car textures: level VRAM file + per-car material table -> OBJ/MTL/PNG.

VRAM file (2nd LZW chunk of a LEVELS.DAT entry): records `u16 x, y, w, h` + w*h u16 words;
h bits 14-15 = kind (2 = CLUT row, 0/1 = 4-bit pixel rect). Records tile VRAM exactly.

Car material table: right after the `<CLASS><n>` node name (16 bytes): u32 ?, 3 x u32, u32 count at
+0x20, 12 bytes, then `count` entries of 28 bytes:
  u16 page_code, u16 clut, u32 E2 texture window | same 8 bytes (second buffer) | u32 type (byte 3:
  8 = textured 4-bit, 1/2/0x0a = flat) | 8 bytes.
clut = standard PS1 CLUT word ((y << 6) | (x >> 4)); it matches the CLUT records exactly.
page_code >> 3 = 4-bit texture page x index (64 VRAM words) on the y = 256 row (evidence: side
liveries of the 8 DAKAR cars sit on pages 8-11 and the UV outlines land on them only with this rule).
The E2 window selects the livery copy inside the page: texel = (uv & ~mask) | (offset & mask).
Face record u32 at +12 = material entry index; corner u32 = vertex | shade index << 8 | u << 16 | v << 24.
"""
import struct, sys, os
import numpy as np
from PIL import Image


def vram(buf):
    V = np.zeros((512, 1024), np.uint16); o = 0
    while o < len(buf):
        x, y, w, h = struct.unpack_from('<4H', buf, o); hh = h & 0x3fff
        V[y:y + hh, x:x + w] = np.frombuffer(buf, np.uint16, w * hh, o + 8).reshape(hh, w)
        o += 8 + w * hh * 2
    return V


def materials(d, car):
    a = d.find(car.encode() + b'\x00'); n = struct.unpack_from('<I', d, a + 32)[0]
    out = []
    for k in range(n):
        p, c, w = struct.unpack_from('<HHI', d, a + 44 + 28 * k)
        out.append({'page_code': p, 'clut': c, 'window': w, 'type': d[a + 44 + 28 * k + 19]})
    return out


def window(w):
    return ((w & 31) * 8, ((w >> 5) & 31) * 8, ((w >> 10) & 31) * 8, ((w >> 15) & 31) * 8)


def rgba(words):
    w = words.astype(np.uint32)
    r = (w & 31) << 3; g = ((w >> 5) & 31) << 3; b = ((w >> 10) & 31) << 3
    a = np.where(w == 0, 0, 255)
    return np.dstack([r, g, b, a]).astype(np.uint8)


def texture(V, m):
    """Window crop of the entry's 4-bit page, coloured by its CLUT -> (RGBA image, (u0, v0, w, h))."""
    px = m['page_code'] >> 3; py = 1
    page = V[py * 256:py * 256 + 256, px * 64:px * 64 + 64]
    idx = np.zeros((256, 256), np.uint16)
    for k in range(4): idx[:, k::4] = (page >> (4 * k)) & 15
    cx = (m['clut'] & 63) * 16; cy = m['clut'] >> 6
    img = rgba(V[cy, cx:cx + 16][idx])
    mx, my, ox, oy = window(m['window'])
    u0, uw = (ox & mx, 256 - mx) if mx else (0, 256)
    v0, vh = (oy & my, 256 - my) if my else (0, 256)
    return Image.fromarray(img[v0:v0 + vh, u0:u0 + uw]), (u0, v0, uw, vh)


def export(obj_path, vram_path, car, outdir):
    from . import td_model
    d = open(obj_path, 'rb').read(); V = vram(open(vram_path, 'rb').read())
    mats = materials(d, car); parts = td_model.find_car(d, car)
    a = d.find(car.encode() + b'\x00'); j = d.find(b'BODY\x00', a)
    os.makedirs(outdir, exist_ok=True)
    body = parts['BODY']; h = j + 0x20; p = h + 49
    nv = struct.unpack_from('<HHhHH', d, p)[3]; f = p + 10 + 4 * nv + 20
    recs = [struct.unpack_from('<4hHHII', d, f + 20 * k) for k in range(len(body['polys']))]
    tex = {}
    for k, m in enumerate(mats):
        if m['type'] == 8:
            im, box = texture(V, m); im.save(os.path.join(outdir, '%s_m%02d.png' % (car, k))); tex[k] = box
    Vt = []; lines = []
    with open(os.path.join(outdir, car + '.mtl'), 'w') as fm:
        for k in range(len(mats)):
            fm.write('newmtl m%02d\nKd 1 1 1\n' % k)
            if k in tex: fm.write('map_Kd %s_m%02d.png\n' % (car, k))
    with open(os.path.join(outdir, car + '.obj'), 'w') as fo:
        fo.write('mtllib %s.mtl\n' % car)
        for x, y, z in body['V']: fo.write('v %.4f %.4f %.4f\n' % (x / 100., y / 100., z / 100.))
        cur = None
        for (idx, uv, shade, mat), r in zip(body['polys'], recs):
            e = r[6]
            if e != cur: fo.write('usemtl m%02d\n' % e); cur = e
            box = tex.get(e)
            ids = []
            for (u, v) in uv:
                if box: Vt.append(((u - box[0]) / box[2], 1 - (v - box[1]) / box[3]))
                else: Vt.append((0, 0))
                fo.write('vt %.5f %.5f\n' % Vt[-1]); ids.append(len(Vt))
            for k in range(1, len(idx) - 1):
                fo.write('f %d/%d %d/%d %d/%d\n' % (idx[0] + 1, ids[0], idx[k + 1] + 1, ids[k + 1], idx[k] + 1, ids[k]))
    return {'materials': len(mats), 'textured': sorted(tex)}


if __name__ == '__main__':
    print(export(*sys.argv[1:5]))
