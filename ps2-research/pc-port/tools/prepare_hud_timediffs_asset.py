"""Build PS2HudTimeDiffs.bin: the PS2 gaHudTimeDiffs2Ai opponent list art (PS2HudTimeDiffs=1).

Sources (TNG): \\TNG\\DATAPSM\\FONTS\\ARIAL\\ARIAL_16.PSB = HUD font 102 (glyph UVs match GS dump 20261018111758
exactly) and \\TNG\\DATAPSM\\FRONTEND\\NEW\\SMALLCARS\\SMALLCARSHEET.PSB (image index = PS2 car table +0x18; the PC
Frontend/RaceResults/SmallCarSheet uses the same indices). See ps2-research/hud-dump1/findings.md (TimeDiffs).

Format 'MRTD' v1 (little endian):
  u32 page_count; per page: 64*64*4 BGRA rows in D3D order (GXI rows reversed, so D3D v = PSB v; alpha as is)
  u32 glyph_count; per glyph: u8 char, u8 page, 4 f32 box (x0,y0,x1,y1; PSB local, y down), 4 f32 uv
      (u at x0, v at y0, u at x1, v at y1)
  u32 icon_count; per icon: u8 image, u8 page (0xff = no PS2 art), 4 f32 box, 4 f32 uv
  30 x 32-byte level-0 SHA-256 of PC smallcarsheet_<k>_000.dxt (runtime self-check of the car -> icon mapping)
Prints the pack SHA-256 for renderer/ps2_hud_timediffs.hpp.
"""
from pathlib import Path
import hashlib, importlib.util, math, struct, sys

PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PORT.parent / 'hud-dump1'))
from hud_bank import read_bank  # noqa: E402

PC_SMALLCARS = Path(r'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Frontend/RaceResults')
GLYPHS = '0123456789.-'
B = chr(92)


def payload(a, manifest, tail):
    entry = next(e for e in manifest['entries'] if e['kind'] == 'file' and e['path'].upper().endswith(tail))
    raw, _ = a.t.read_payload(entry, a.PS2 / 'TNG.000')
    return raw


def quad(tris):
    """One rectangle (two triangles) -> (texture, box, uv at box corners)."""
    tris = [t for t in tris if all(math.isfinite(c) for p in t[1] for c in p)]
    if not tris:
        return None
    names = {t[0] for t in tris}
    if len(tris) != 2 or len(names) != 1:
        raise ValueError('glyph/icon is not one textured rectangle')
    pts = {}
    for _, uv, xy in tris:
        for (u, v), (x, y) in zip(uv, xy):
            pts[(x, y)] = (u, v)
    xs = sorted({x for x, _ in pts}); ys = sorted({y for _, y in pts})
    if len(xs) != 2 or len(ys) != 2 or len(pts) != 4:
        raise ValueError('not an axis-aligned rectangle')
    x0, x1 = xs; y0, y1 = ys
    u0, v0 = pts[(x0, y0)]; u1, v1 = pts[(x1, y1)]
    if pts[(x1, y0)] != (u1, v0) or pts[(x0, y1)] != (u0, v1):
        raise ValueError('rotated UV')
    return names.pop(), (x0, y0, x1, y1), (u0, v0, u1, v1)


def main():
    spec = importlib.util.spec_from_file_location('asset_common', PORT / 'docs/full-coverage/vehicles/audit.py')
    a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2 / 'TNG.PAK')
    font = read_bank(payload(a, manifest, B + 'FONTS' + B + 'ARIAL' + B + 'ARIAL_16.PSB'), False)
    cars = read_bank(payload(a, manifest, B + 'SMALLCARS' + B + 'SMALLCARSHEET.PSB'), False)
    pages, index = [], {}

    def page(name):
        if name not in index:
            folder = (B + 'FONTS' + B + 'ARIAL' + B) if name.startswith('arial') else (B + 'SMALLCARS' + B)
            g = payload(a, manifest, folder + name.upper() + '.GXI')
            w, h = struct.unpack_from('<HH', g, 4)
            if struct.unpack_from('<I', g, 0)[0] != 0x13039 or (w, h) != (64, 64) or len(g) != 8 + 64 * 64 * 4:
                raise ValueError('unexpected GXI ' + name)
            rows = bytearray()
            for y in range(64):
                src = g[8 + (63 - y) * 256: 8 + (64 - y) * 256]
                for x in range(64):
                    r, gg, b, al = src[4 * x: 4 * x + 4]
                    rows += bytes((b, gg, r, al))
            index[name] = len(pages); pages.append(bytes(rows))
        return index[name]

    maps = dict(font['mappings'])
    glyphs = []
    for ch in GLYPHS:
        q = quad(font['images'][maps[ord(ch)]])
        glyphs.append((ord(ch), page(q[0]), q[1], q[2]))
    icons = []
    for k, tris in enumerate(cars['images']):
        q = quad(tris)
        if q is None:  # PS2 image 12 is a Null cell
            icons.append((k, 0xff, (0, -16, 32, 0), (0, 0, 0, 0)))
        else:
            icons.append((k, page(q[0]), q[1], q[2]))
    blob = bytearray(b'MRTD' + struct.pack('<II', 1, len(pages)))
    for p in pages:
        blob += p
    blob += struct.pack('<I', len(glyphs))
    for c, p, box, uv in glyphs:
        blob += struct.pack('<BB8f', c, p, *box, *uv)
    blob += struct.pack('<I', len(icons))
    for k, p, box, uv in icons:
        blob += struct.pack('<BB8f', k, p, *box, *uv)
    for k in range(30):
        d = (PC_SMALLCARS / ('smallcarsheet_%03d_000.dxt' % k)).read_bytes()
        w, h = struct.unpack_from('<II', d, 12)
        blob += hashlib.sha256(d[20:20 + w * h * 4]).digest()
    target = PORT / '.assets/hud/PS2HudTimeDiffs.bin'
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError('Private output link rejected')
    target.write_bytes(bytes(blob))
    print(target.name, len(blob), hashlib.sha256(blob).hexdigest(), 'pages', sorted(index, key=index.get))


if __name__ == '__main__':
    main()
