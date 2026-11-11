"""SIDE / small icon of a vehicle model: orthographic side render of complete.dx + the SDK smallcarsheet composition.

The SDK generates SIDE artwork with its live D3D9 previewer (azimuth -90, elevation 0, orthographic, key .55,
ambient .70) and then `ui_preview.compose_preview(..., 'smallcarsheet')`. This tool renders the same view offline
(textured, alpha-tested, lambert key + ambient) so a SIDE icon can be made for a model without opening Workshop,
then uses the unchanged SDK composition. `--reference` compares against an SDK-made icon of the same model.
"""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "master-rallye-re-v-cap/src")]
from master_rallye.dx import parse_dx_bytes                     # noqa: E402
from master_rallye.dxt import parse_dxt_bytes, decode_rgba_pixels  # noqa: E402
from master_rallye.addon_sdk.ui_preview import compose_preview, PROFILES  # noqa: E402
from PIL import Image                                            # noqa: E402

SKIP = ("crack", "breaklightson", "brakeon", "shadow")


GAME = None   # game folder for textures the overlay folder does not carry (set by --game)


def load_texture(folder: Path, name: str, cache: dict):
    key = name.lower()
    if key not in cache:
        data = None
        p = folder / (key + ".dxt")
        if p.is_file():
            data = p.read_bytes()
        elif GAME is not None:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from vehicle_manager import game_file
            try:
                data = game_file(folder, GAME, f"DataGx/Vehicles/{folder.name}/{key}.dxt")
            except KeyError:
                data = None
        if data is None:
            cache[key] = None
        else:
            t = parse_dxt_bytes(data)
            cache[key] = (t.width, t.height, decode_rgba_pixels(t))
    return cache[key]


def render(folder: Path, width=512, height=256, facing=1, flip_v=True):
    m = parse_dx_bytes((folder / "complete.dx").read_bytes(), source="complete.dx")
    pos, uv = m.vertices.positions, m.uv_sets[0].values
    xs = [p[2] for p in pos]; ys = [p[1] for p in pos]
    zmin, zmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    scale = min((width - 8) / (zmax - zmin), (height - 8) / (ymax - ymin))
    ox, oy = (width - (zmax - zmin) * scale) / 2, (height - (ymax - ymin) * scale) / 2
    proj = lambda p: (ox + ((p[2] - zmin) if facing > 0 else (zmax - p[2])) * scale, height - oy - (p[1] - ymin) * scale)
    depth = [float("inf")] * (width * height)
    color = bytearray(width * height * 4)
    light = (facing * -0.4, 0.6, 0.2)          # from the camera side, a little above
    ln = math.sqrt(sum(c * c for c in light)); light = tuple(c / ln for c in light)
    cache = {}
    for d in m.physical_draws:
        if d.group_label is None and "." in d.record_path:
            continue                                  # state alternatives (broken glass, brake ON)
        names = [s.value for s in d.texture_slots if s.value and s.value != "Null"]
        if names and any(k in names[0].lower() for k in SKIP):
            continue
        tex = load_texture(folder, names[0], cache) if names else None
        ids = m.draw_global_indices(d)
        for k in range(0, len(ids), 3):
            a, b, c = ids[k:k + 3]
            A, B, C = pos[a], pos[b], pos[c]
            u = (B[0] - A[0], B[1] - A[1], B[2] - A[2]); v = (C[0] - A[0], C[1] - A[1], C[2] - A[2])
            n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            nl = math.sqrt(sum(x * x for x in n)) or 1
            shade = 0.70 + 0.55 * abs(sum(n[i] * light[i] for i in range(3)) / nl)
            pa, pb, pc = proj(A), proj(B), proj(C)
            x0, x1 = int(max(0, min(pa[0], pb[0], pc[0]))), int(min(width - 1, max(pa[0], pb[0], pc[0])))
            y0, y1 = int(max(0, min(pa[1], pb[1], pc[1]))), int(min(height - 1, max(pa[1], pb[1], pc[1])))
            den = (pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1])
            if abs(den) < 1e-9:
                continue
            for py in range(y0, y1 + 1):
                for px in range(x0, x1 + 1):
                    sx, sy = px + 0.5, py + 0.5
                    w0 = ((pb[1] - pc[1]) * (sx - pc[0]) + (pc[0] - pb[0]) * (sy - pc[1])) / den
                    w1 = ((pc[1] - pa[1]) * (sx - pc[0]) + (pa[0] - pc[0]) * (sy - pc[1])) / den
                    w2 = 1 - w0 - w1
                    if w0 < 0 or w1 < 0 or w2 < 0:
                        continue
                    # depth: distance from the camera along X (camera on the `facing` side)
                    z = facing * (w0 * A[0] + w1 * B[0] + w2 * C[0])
                    i = py * width + px
                    if z >= depth[i]:
                        continue
                    r, g, bl, al = 200, 200, 200, 255
                    if tex:
                        tu = w0 * uv[a][0] + w1 * uv[b][0] + w2 * uv[c][0]
                        tv = w0 * uv[a][1] + w1 * uv[b][1] + w2 * uv[c][1]
                        tw, th, px_ = tex
                        ix = int((tu % 1.0) * tw) % tw
                        iy = int(((1 - tv) if flip_v else tv) % 1.0 * th) % th
                        o = (iy * tw + ix) * 4
                        r, g, bl, al = px_[o], px_[o + 1], px_[o + 2], px_[o + 3]
                        if al < 100:
                            continue
                    depth[i] = z
                    color[i * 4:i * 4 + 4] = bytes((min(255, int(r * shade)), min(255, int(g * shade)), min(255, int(bl * shade)), 255))
    return width, height, bytes(color)


def side_icon(folder: Path, facing=1, flip_v=True):
    image = render(folder, facing=facing, flip_v=flip_v)
    rgba, _report = compose_preview(image, "smallcarsheet", style="mr-native-v1")
    w, h = PROFILES["smallcarsheet"]["size"]
    return Image.frombytes("RGBA", (w, h), rgba), Image.frombytes("RGBA", image[:2], image[2])


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--folder", type=Path, required=True, help="vehicle folder with complete.dx and its .dxt textures")
    p.add_argument("--output", type=Path, required=True, help="PNG (32x16 smallcarsheet)")
    p.add_argument("--facing", type=int, default=1)
    p.add_argument("--game", type=Path, help="game folder: loose files and Data.sma for textures not in --folder")
    p.add_argument("--no-flip-v", action="store_true")
    a = p.parse_args()
    GAME = a.game
    icon, source = side_icon(a.folder, a.facing, not a.no_flip_v)
    icon.save(a.output); source.save(a.output.with_suffix(".source.png"))
    print(a.output)
