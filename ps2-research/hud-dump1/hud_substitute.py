"""Build PS2 substitutes for PC HUD image textures (same bank, same image index, same authored geometry).

For each PC image k whose texture is one whole PC image (one texture name), every texel of the PC texture (D3D
level 0 = stored rows) is mapped PC uv -> authored xy (PC dxb triangle) -> PS2 uv (PSB triangle of image k) -> PS2
GXI texel (raw row 0 = PSB v 1; GS alpha 0x80 = 1.0). Texels outside the PS2 image stay transparent.
Images whose authored bounding box differs between PC and PS2 are not substituted.

usage: python hud_substitute.py <ps2 HUD dir (PSB+GXI)> <PC DataGx/Hud dir> <out dir> [bank...]
Writes <bank>_<k>.bgra (raw BGRA rows of the PC size), report.json and sheet_<bank>.png when Pillow is present.
"""
import sys, os, json, struct, hashlib
from hud_bank import read_bank, image_box


def bary(p, a, b, c):
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-12: return None
    l1 = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / d
    l2 = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / d
    return l1, l2, 1 - l1 - l2


def inside(l, eps=1e-6): return l is not None and min(l) >= -eps


def gxi(path):
    g = open(path, 'rb').read(); w, h = struct.unpack_from('<HH', g, 4)
    if struct.unpack_from('<I', g, 0)[0] != 0x00013039 or len(g) != 8 + w * h * 4: raise ValueError(path)
    return w, h, g[8:]


def pc_texture(path):
    d = open(path, 'rb').read(); magic, ver, _, w, h = struct.unpack_from('<5I', d, 0)
    if magic != 65261 or len(d) != 20 + w * h * 4: raise ValueError(path)
    return w, h, d[20:]


def build(ps2dir, pcdir, bank, remap=None):
    """remap: {image: (width, height)} for images whose PS2 box differs: the PC quad is remapped onto the PS2 box
    (rec['remap'] = [sx, tx, sy, ty], x' = sx*x + tx in authored units) and the PS2 art fills a texture of that size."""
    remap = remap or {}
    pc = read_bank(open(os.path.join(pcdir, bank + '.dxb'), 'rb').read(), True)
    ps = read_bank(open(os.path.join(ps2dir, bank.upper() + '.PSB'), 'rb').read(), False)
    pages = {}
    results = []
    for k, (ptris, stris) in enumerate(zip(pc['images'], ps['images'])):
        names = {t[0] for t in ptris}
        rec = {'bank': bank, 'image': k}
        if len(names) != 1: rec['skip'] = 'pc_image_spans_textures'; results.append((rec, None)); continue
        pbox, sbox = image_box(ptris), image_box(stris)
        if pbox != sbox and k not in remap: rec['skip'] = 'authored_geometry_differs'; results.append((rec, None)); continue
        name = names.pop(); pw, ph, pcpx = pc_texture(os.path.join(pcdir, name + '.dxt'))
        rec.update(pc_texture=name, pc_size=[pw, ph], pc_level0_sha256=hashlib.sha256(pcpx).hexdigest())
        w, h = remap.get(k, (pw, ph)); rec['size'] = [w, h]
        if k in remap:
            sx = (sbox[2] - sbox[0]) / (pbox[2] - pbox[0]); sy = (sbox[3] - sbox[1]) / (pbox[3] - pbox[1])
            rec['remap'] = [sx, sbox[0] - sx * pbox[0], sy, sbox[1] - sy * pbox[1]]
        out = bytearray(w * h * 4); covered = 0
        for r in range(h):
            for c in range(w):
                uv = ((c + 0.5) / w, (r + 0.5) / h); xy = None
                for _, puv, pxy in ptris:
                    l = bary(uv, *puv)
                    if inside(l, 1e-4):
                        xy = tuple(sum(l[i] * pxy[i][j] for i in range(3)) for j in range(2)); break
                if xy is None: continue
                if 'remap' in rec: xy = (rec['remap'][0] * xy[0] + rec['remap'][1], rec['remap'][2] * xy[1] + rec['remap'][3])
                for tex, suv, sxy in stris:
                    if tex == "null": continue
                    l = bary(xy, *sxy)
                    if not inside(l, 1e-4): continue
                    if tex not in pages: pages[tex] = gxi(os.path.join(ps2dir, tex.upper() + '.GXI'))
                    gw, gh, gpx = pages[tex]
                    u = sum(l[i] * suv[i][0] for i in range(3)); v = sum(l[i] * suv[i][1] for i in range(3))
                    x = min(gw - 1, max(0, int(u * gw))); y = min(gh - 1, max(0, int((1 - v) * gh)))
                    o = (y * gw + x) * 4; R, G, B, A = gpx[o:o + 4]
                    # GXI alpha is 8-bit (0x80 = half); the GS 0..0x80 scale applies only after upload.
                    q = (r * w + c) * 4; out[q:q + 4] = bytes((B, G, R, A)); covered += 1
                    break
        rec['covered'] = covered / (w * h)
        # Similarity to the PC art (same orientation check): mean abs diff of premultiplied RGB.
        if (w, h) != (pw, ph): rec['mean_abs_diff_premul'] = None; rec['ps2_sha256'] = hashlib.sha256(bytes(out)).hexdigest(); results.append((rec, bytes(out))); continue
        diff = sum(abs(out[i] * out[i - i % 4 + 3] - pcpx[i] * pcpx[i - i % 4 + 3]) for i in range(len(out)) if i % 4 != 3) / (255 * 255 * w * h * 3)
        rec['mean_abs_diff_premul'] = round(diff, 4)
        rec['ps2_sha256'] = hashlib.sha256(bytes(out)).hexdigest()
        results.append((rec, bytes(out)))
    return results


def main():
    ps2dir, pcdir, outdir = sys.argv[1:4]; banks = sys.argv[4:] or ['hud-template', 'newhud']
    os.makedirs(outdir, exist_ok=True); report = []
    for bank in banks:
        res = build(ps2dir, pcdir, bank)
        for rec, px in res:
            report.append(rec)
            if px is not None: open(os.path.join(outdir, '%s_%03d.bgra' % (bank, rec['image'])), 'wb').write(px)
            print(json.dumps(rec))
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            continue
        tiles = []
        for rec, px in res:
            if px is None: continue
            pcpx = pc_texture(os.path.join(pcdir, rec['pc_texture'] + '.dxt'))[2]
            pair = []
            for (w, h), data in ((rec['pc_size'], pcpx), (rec['size'], px)):
                s = max(1, 96 // max(rec['pc_size'] + rec['size']))
                im = Image.frombytes('RGBA', (w, h), data); b, g, r, a = im.split(); im = Image.merge('RGBA', (r, g, b, a)).transpose(Image.FLIP_TOP_BOTTOM)
                bg = Image.new('RGBA', (w, h), (90, 60, 90, 255)); bg.alpha_composite(im); pair.append(bg.convert('RGB').resize((w * s, h * s), Image.NEAREST))
            tiles.append((rec['image'], pair))
        W = sum(a.width + b.width + 12 for _, (a, b) in tiles); H = max(max(a.height, b.height) for _, (a, b) in tiles) + 14
        sheet = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(sheet); x = 0
        for k, (a, b) in tiles:
            sheet.paste(a, (x, 14)); sheet.paste(b, (x + a.width + 2, 14)); d.text((x, 0), str(k), fill=(255, 255, 0)); x += a.width + b.width + 12
        sheet.save(os.path.join(outdir, 'sheet_%s.png' % bank))
    json.dump(report, open(os.path.join(outdir, 'report.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
