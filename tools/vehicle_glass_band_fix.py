"""Remove the red sun-strip band from generated broken-glass textures (owner report 2026-11-11).

The auto-generated cracked-glass textures (mr-auto-cracked-tga, heritage-cracked-tga) were composed over a windscreen
texture with the red top strip, so a smashed side/rear window showed a red band. The band is the top block of rows
whose pixels are red-dominant. Inside it the background becomes the plain glass colour of the same texture (median
of the non-crack pixels below the band) and every crack keeps its brightness above the band colour:
    out = glass + (white - glass) * clamp((lum - lum_band) / (255 - lum_band))
Alpha and everything below the band stay byte-identical in RGBA; the DXT is re-encoded with the SDK encoder.
"""
from __future__ import annotations
import argparse, hashlib, io, json, statistics, sys, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "master-rallye-re-vehicles/src"))
from master_rallye.dxt import parse_dxt_bytes, decode_rgba_pixels, encode_dxt_pixels  # noqa: E402

NAMES = ("mr-auto-cracked-tga.dxt", "heritage-cracked-tga.dxt")


def red(p):
    r, g, b = p[:3]
    return r > g + 40 and r > b + 40


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def fix_dxt(data: bytes):
    t = parse_dxt_bytes(data)
    w, h = t.width, t.height
    rgba = bytearray(decode_rgba_pixels(t))
    px = lambda x, y: rgba[(y * w + x) * 4:(y * w + x) * 4 + 4]
    def row_red(y):
        return sum(red(px(x, y)) for x in range(w)) / w
    # The texture may be stored bottom-up: find the band at either edge.
    top = [y for y in range(h)]
    for order in (top, top[::-1]):
        band = []
        for y in order:
            if row_red(y) < 0.2:
                break
            band.append(y)
        if band:
            break
    if not band or len(band) > h // 3:
        return None, {"band_rows": 0}
    rest = [y for y in range(h) if y not in band]
    lums = [lum(px(x, y)) for y in rest for x in range(w)]
    lo, hi = statistics.quantiles(lums, n=10)[0], statistics.quantiles(lums, n=10)[6]
    glass = [statistics.median(px(x, y)[c] for y in rest for x in range(w) if lo <= lum(px(x, y)) <= hi) for c in range(3)]
    band_px = [px(x, y) for y in band for x in range(w) if red(px(x, y))]
    glass_lum = lum(glass)
    lum_band = statistics.median(lum(p) for p in band_px)
    # Background per column: the clean glass right under the band (continues its gradient), cracks excluded.
    step = 1 if band[0] < h // 2 else -1
    edge = max(band) + 1 if step == 1 else min(band) - 1
    under = [edge + step * j for j in range(6) if 0 <= edge + step * j < h]
    column = []
    for x in range(w):
        clean = [px(x, y) for y in under if lum(px(x, y)) < glass_lum + 30]
        column.append([statistics.median(q[c] for q in clean) for c in range(3)] if clean else glass)
    for y in band:
        for x in range(w):
            i = (y * w + x) * 4
            k = max(0.0, min(1.0, (lum(rgba[i:i + 4]) - lum_band) / max(1.0, 255 - lum_band)))
            for c in range(3):
                base = column[x][c]
                rgba[i + c] = int(round(base + (255 - base) * k))
    return encode_dxt_pixels(t, bytes(rgba), w, h), {"band_rows": len(band), "glass_rgb": glass, "band_lum": lum_band}


def fix_tree(root: Path) -> list:
    out = []
    for p in sorted(root.rglob("*.dxt")):
        if p.name.lower() in NAMES:
            data, info = fix_dxt(p.read_bytes())
            if data:
                p.write_bytes(data)
            out.append({"path": str(p.relative_to(root)), **info})
    return out


def fix_package(path: Path) -> list:
    """Rewrite a .mrcar with fixed cracked textures (manifest hashes updated)."""
    with zipfile.ZipFile(path) as z:
        manifest = json.loads(z.read("manifest.json"))
        files = {n: z.read(n) for n in z.namelist() if n != "manifest.json"}
    report = []
    for item in manifest["files"]:
        if item["path"].rsplit("/", 1)[-1].lower() in NAMES:
            data, info = fix_dxt(files["files/" + item["path"]])
            if data:
                files["files/" + item["path"]] = data
                item["sha256"] = hashlib.sha256(data).hexdigest()
            report.append({"path": item["path"], **info})
    tmp = path.with_suffix(".mrcar.new")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in files.items():
            z.writestr(n, d)
        z.writestr("manifest.json", json.dumps(manifest, indent=1))
    tmp.replace(path)
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tree", type=Path, action="append", default=[], help="resource folder to fix in place")
    p.add_argument("--package", type=Path, action="append", default=[], help=".mrcar to fix in place")
    a = p.parse_args()
    print(json.dumps({"trees": {str(t): fix_tree(t) for t in a.tree}, "packages": {str(k): fix_package(k) for k in a.package}}, indent=1))
