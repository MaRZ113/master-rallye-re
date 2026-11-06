"""ATMOSPHERE6 (P1): procedural night sky set for CustomSet (no game or GT3 assets).

Writes <output>/clouds.dxt and <output>/layer.dxt in the custom sky format read by
renderer/atmosphere.hpp decode_sky: 20-byte header (0xfeed, 1, crc32, 256, 256) +
256x256 BGRA. Row 0 is the horizon (v=0), row 255 the zenith cap (v>=.97 uniform),
v ~ height/radius on the native sky cylinder (CustomSkyProjection=1).

clouds.dxt: opaque night gradient (moonlit horizon glow -> deep zenith).
layer.dxt : thin moonlit cloud wisps; alpha is the cloud cover (the renderer scales it
            by CustomSkyHaze). Both tile seamlessly in u. Stars are NOT baked: one texel
            spans ~0.7 degrees, so stars are drawn as depth-tested sprites (Stars=1).
"""
from pathlib import Path
import argparse
import json
import struct
import zlib

import numpy as np
from PIL import Image

SIZE = 256


def periodic_noise(rng, octaves, base, persistence=.55):
    """Fractal value noise, periodic in x (u wraps), smooth in y."""
    out = np.zeros((SIZE, SIZE), np.float32)
    amplitude, total = 1.0, 0.0
    x = np.arange(SIZE, dtype=np.float32)
    for o in range(octaves):
        cells_x = base * (2 ** o)
        cells_y = max(2, int(cells_x * .6))
        grid = rng.random((cells_y + 2, cells_x), dtype=np.float32)
        gx = x / SIZE * cells_x
        gy = np.arange(SIZE, dtype=np.float32) / SIZE * cells_y
        x0 = np.floor(gx).astype(int)
        y0 = np.floor(gy).astype(int)
        fx = gx - x0
        fy = gy - y0
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        x1 = (x0 + 1) % cells_x
        x0 = x0 % cells_x
        a = grid[y0][:, x0]
        b = grid[y0][:, x1]
        c = grid[y0 + 1][:, x0]
        d = grid[y0 + 1][:, x1]
        top = a + (b - a) * fx[None, :]
        bottom = c + (d - c) * fx[None, :]
        out += amplitude * (top + (bottom - top) * fy[:, None])
        total += amplitude
        amplitude *= persistence
    return out / total


def srgb(hex_color):
    return np.array([(hex_color >> 16) & 255, (hex_color >> 8) & 255, hex_color & 255], np.float32)


def build(seed, horizon, zenith, cloud, cover):
    rng = np.random.default_rng(seed)
    v = (np.arange(SIZE, dtype=np.float32) + .5) / SIZE
    # Sky gradient: most of the change in the first ~15 degrees above the horizon.
    t = 1 - np.exp(-v * 5.5)
    t = t / t.max()
    gradient = horizon[None, :] * (1 - t[:, None]) + zenith[None, :] * t[:, None]
    base = np.repeat(gradient[:, None, :], SIZE, axis=1)
    # Very faint large-scale variation so the dome does not look flat.
    variation = periodic_noise(rng, 3, 3) - .5
    base *= (1 + .08 * variation)[:, :, None]

    def stretch(x):  # averaged octaves cluster at .5; use the full 0..1 range
        lo, hi = np.percentile(x, 2), np.percentile(x, 98)
        return np.clip((x - lo) / max(hi - lo, 1e-6), 0, 1)
    shapes = stretch(periodic_noise(rng, 5, 4))
    wisps = stretch(periodic_noise(rng, 4, 10, .5))
    density = np.clip((shapes * .75 + wisps * .25 - (1 - cover)) / max(cover, 1e-3), 0, 1) ** 1.6
    band = np.clip(v / .05, 0, 1) * np.clip((.85 - v) / .35, 0, 1)  # clear zenith cap, soft horizon
    alpha = density * band[:, None]
    # Moonlit tops: brighter where dense, darker rims.
    light = .55 + .45 * np.clip(wisps * 1.4 - .2, 0, 1)
    layer_rgb = cloud[None, None, :] * light[:, :, None]
    # Layer RGB over gradient where clear (alpha 0), so filtering never bleeds black.
    layer_rgb = layer_rgb * alpha[:, :, None] + base * (1 - alpha[:, :, None])
    return base, layer_rgb, alpha


def payload(rgb, alpha):
    bgra = np.empty((SIZE, SIZE, 4), np.uint8)
    bgra[:, :, 0] = np.clip(np.rint(rgb[:, :, 2]), 0, 255)
    bgra[:, :, 1] = np.clip(np.rint(rgb[:, :, 1]), 0, 255)
    bgra[:, :, 2] = np.clip(np.rint(rgb[:, :, 0]), 0, 255)
    bgra[:, :, 3] = np.clip(np.rint(alpha * 255), 0, 255)
    body = bgra.tobytes()
    return struct.pack('<5I', 0xfeed, 1, zlib.crc32(body) & 0xffffffff, SIZE, SIZE) + body, bgra


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True, help='set folder, e.g. Atmosphere/sky/night')
    ap.add_argument('--seed', type=int, default=6)
    ap.add_argument('--horizon', type=lambda s: int(s, 0), default=0x24344a)
    ap.add_argument('--zenith', type=lambda s: int(s, 0), default=0x05080f)
    ap.add_argument('--cloud', type=lambda s: int(s, 0), default=0x3b4559)
    ap.add_argument('--cover', type=float, default=.55, help='0 clear .. 1 overcast')
    ap.add_argument('--preview', action='store_true', help='also write PNG previews')
    a = ap.parse_args()
    base, layer_rgb, alpha = build(a.seed, srgb(a.horizon), srgb(a.zenith), srgb(a.cloud), float(np.clip(a.cover, .05, 1)))
    a.output.mkdir(parents=True, exist_ok=True)
    report = {'tool': 'atmosphere_night_sky.py', 'seed': a.seed, 'horizon': hex(a.horizon), 'zenith': hex(a.zenith),
              'cloud': hex(a.cloud), 'cover': a.cover, 'assets': 'procedural only', 'files': {}}
    for name, rgb, al in (('clouds', base, np.ones((SIZE, SIZE), np.float32)), ('layer', layer_rgb, alpha)):
        data, bgra = payload(rgb, al)
        (a.output / f'{name}.dxt').write_bytes(data)
        import hashlib
        report['files'][name + '.dxt'] = hashlib.sha256(data).hexdigest()
        if a.preview:
            Image.fromarray(bgra[:, :, [2, 1, 0, 3]]).save(a.output / f'{name}.png')
    (a.output / 'night-sky.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
