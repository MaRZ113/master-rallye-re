"""Fit the opt-in PS2Color tone curve from PC/PS2 screenshot pairs.

Curve (per channel, x and y in 0..1):  y = (1 - k) * x + k * x^2
k = 0 is the identity, k > 0 darkens mid-tones (k = 1 is x^2, roughly gamma 2).
The renderer draws it with fixed-function stages only (renderer/ps2_color.*).

Screenshots of the two versions never share exact framing (PS2 has grass, a different FOV and HUD), so
pixels are not compared one to one. Each pair lists matched regions (normalized boxes over the same
surface: sky, rock, road, car body ...). For every region and channel the tool compares quantiles
(5..95 %) of the PC region with the PS2 region and fits one k per channel by least squares over all
regions of all pairs:  k = sum((y - x)(x^2 - x)) / sum((x^2 - x)^2).

Usage:  python fit_tone_curve.py pairs.json [--image-root DIR] [--crops OUT_DIR]
Requires Pillow. Prints the fit, per-region residuals and the INI lines.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

QUANTILES = [q / 100 for q in range(5, 96, 5)]


def region_pixels(image: Image.Image, box: list[float]) -> list[tuple[int, int, int]]:
    w, h = image.size
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError(f"box {box} must be normalized 0..1 with x0<x1, y0<y1")
    crop = image.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    return list(crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata())


def quantiles(values: list[float]) -> list[float]:
    ordered = sorted(values)
    n = len(ordered)
    return [ordered[min(n - 1, int(q * n))] for q in QUANTILES]


def curve(x: float, k: float) -> float:
    return (1 - k) * x + k * x * x


def saturation(pixels: list[tuple[float, float, float]]) -> float:
    total = 0.0
    for r, g, b in pixels:
        hi, lo = max(r, g, b), min(r, g, b)
        total += 0 if hi <= 0 else (hi - lo) / hi
    return total / max(1, len(pixels))


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pairs", type=Path)
    parser.add_argument("--image-root", type=Path, default=None)
    parser.add_argument("--crops", type=Path, default=None, help="write region crops for visual checking")
    args = parser.parse_args()

    manifest = json.loads(args.pairs.read_text(encoding="utf-8"))
    root = args.image_root or args.pairs.parent
    samples: list[list[tuple[float, float]]] = [[], [], []]  # per channel (x, y)
    regions = []
    for pair in manifest["pairs"]:
        pc = load(root / pair["pc"])
        ps2 = load(root / pair["ps2"])
        for region in pair["regions"]:
            a = region_pixels(pc, region["pc"])
            b = region_pixels(ps2, region["ps2"])
            if args.crops:
                args.crops.mkdir(parents=True, exist_ok=True)
                stem = f"{pair['name']}-{region['name']}"
                pc.crop(tuple(int(v * s) for v, s in zip(region["pc"], pc.size * 2))).save(args.crops / f"{stem}-pc.png")
                ps2.crop(tuple(int(v * s) for v, s in zip(region["ps2"], ps2.size * 2))).save(args.crops / f"{stem}-ps2.png")
            weight = float(region.get("weight", 1.0))
            entry = {"pair": pair["name"], "region": region["name"], "weight": weight, "x": [], "y": [],
                     "pc_pixels": [tuple(c / 255 for c in p) for p in a[::5]],
                     "ps2_pixels": [tuple(c / 255 for c in p) for p in b[::5]]}
            for c in range(3):
                xs = quantiles([p[c] / 255 for p in a])
                ys = quantiles([p[c] / 255 for p in b])
                entry["x"].append(xs)
                entry["y"].append(ys)
                samples[c].extend((x, y, weight) for x, y in zip(xs, ys))
            regions.append(entry)

    ks = []
    for c in range(3):
        num = sum(w * (y - x) * (x * x - x) for x, y, w in samples[c])
        den = sum(w * (x * x - x) ** 2 for x, y, w in samples[c])
        ks.append(0.0 if den == 0 else max(-1.0, min(1.0, num / den)))

    names = "RGB"
    print(f"pairs={len(manifest['pairs'])} regions={len(regions)}")
    print("fit: " + "  ".join(f"k_{n}={k:+.3f}" for n, k in zip(names, ks)))
    print("\nregion                       mean PC -> PS2 (fitted)             rmse before / after   sat PC / PS2 / fitted")
    total_before = total_after = 0.0
    count = 0
    for entry in regions:
        before = after = 0.0
        means = []
        for c in range(3):
            xs, ys = entry["x"][c], entry["y"][c]
            before += sum((y - x) ** 2 for x, y in zip(xs, ys))
            after += sum((y - curve(x, ks[c])) ** 2 for x, y in zip(xs, ys))
            means.append((sum(xs) / len(xs), sum(ys) / len(ys), sum(curve(x, ks[c]) for x in xs) / len(xs)))
        n = 3 * len(QUANTILES)
        total_before += before
        total_after += after
        count += n
        fitted = [tuple(curve(v, ks[c]) for c, v in enumerate(p)) for p in entry["pc_pixels"]]
        mean_text = " ".join(f"{n}:{m[0]*255:3.0f}->{m[1]*255:3.0f}({m[2]*255:3.0f})" for n, m in zip(names, means))
        print(f"{entry['pair'] + '/' + entry['region']:28} {mean_text}  {(before/n)**.5*255:5.1f} / {(after/n)**.5*255:5.1f}"
              f"   {saturation(entry['pc_pixels']):.3f} / {saturation(entry['ps2_pixels']):.3f} / {saturation(fitted):.3f}")
    print(f"\noverall rmse (0..255): before {(total_before/count)**.5*255:.1f}, after {(total_after/count)**.5*255:.1f}")
    print("\nPS2Port.ini:")
    print("PS2Color=1")
    print("PS2ColorCurve=" + ",".join(f"{k:.3f}" for k in ks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
