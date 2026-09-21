#!/usr/bin/env python3
"""Tiny dependency-free textured preview renderer for R0.5 validation."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from dx_mesh_probe import parse_dx
from dxt_decode import parse_dxt, write_png
from dx_export_obj import resolve_texture


def render(source: Path, output: Path, texture_directory: Path, flip_v: bool, size: int) -> None:
    result, arrays = parse_dx(source)
    positions = arrays["positions"]
    uvs = arrays["uv_sets"][0]
    records = result["sections"]["draw_table"]["records"]
    indices = arrays["global_indices"]
    textures = {}
    for record in records:
        primary = next((s["text"] for s in record["texture_slots"] if s["text"].lower() != "null"), None)
        if primary is None:
            record["_preview_texture"] = None
            continue
        path = resolve_texture(texture_directory, primary)
        if path is None:
            raise FileNotFoundError(primary)
        if primary.lower() not in textures:
            header, pixels = parse_dxt(path)
            textures[primary.lower()] = (header["width"], header["height"], pixels)
        record["_preview_texture"] = textures[primary.lower()]

    # Orthographic view predominantly along +X, slightly oblique to reveal depth.
    ca, sa = math.cos(math.radians(18.0)), math.sin(math.radians(18.0))
    projected = [(z * ca - x * sa, y, x * ca + z * sa) for x, y, z in positions]
    min_x = min(p[0] for p in projected); max_x = max(p[0] for p in projected)
    min_y = min(p[1] for p in projected); max_y = max(p[1] for p in projected)
    margin = 28
    scale = min((size - 2 * margin) / (max_x - min_x), (size - 2 * margin) / (max_y - min_y))
    screen = [((p[0] - min_x) * scale + margin, (max_y - p[1]) * scale + margin, p[2]) for p in projected]
    pixels = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            checker = 36 if ((x // 24) + (y // 24)) % 2 else 48
            i = (y * size + x) * 4
            pixels[i:i+4] = bytes((checker, checker, checker, 255))
    depth = [-float("inf")] * (size * size)

    for record in records:
        texture = record["_preview_texture"]
        start = record["index_start"]
        end = start + record["index_count"]
        for index_offset in range(start, end, 3):
            ia, ib, ic = indices[index_offset:index_offset + 3]
            a, b, c = screen[ia], screen[ib], screen[ic]
            denom = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(denom) < 1e-10:
                continue
            x0 = max(0, int(math.floor(min(a[0], b[0], c[0])))); x1 = min(size - 1, int(math.ceil(max(a[0], b[0], c[0]))))
            y0 = max(0, int(math.floor(min(a[1], b[1], c[1])))); y1 = min(size - 1, int(math.ceil(max(a[1], b[1], c[1]))))
            pa, pb, pc = positions[ia], positions[ib], positions[ic]
            e1 = tuple(pb[i] - pa[i] for i in range(3)); e2 = tuple(pc[i] - pa[i] for i in range(3))
            normal = (e1[1]*e2[2]-e1[2]*e2[1], e1[2]*e2[0]-e1[0]*e2[2], e1[0]*e2[1]-e1[1]*e2[0])
            length = math.sqrt(sum(value*value for value in normal)) or 1.0
            lighting = 0.30 + 0.70 * abs((normal[0]*0.7 + normal[1]*0.4 + normal[2]*0.6) / length)
            for py in range(y0, y1 + 1):
                for px in range(x0, x1 + 1):
                    sx, sy = px + 0.5, py + 0.5
                    wa = ((b[1]-c[1])*(sx-c[0]) + (c[0]-b[0])*(sy-c[1])) / denom
                    wb = ((c[1]-a[1])*(sx-c[0]) + (a[0]-c[0])*(sy-c[1])) / denom
                    wc = 1.0 - wa - wb
                    if wa < -1e-6 or wb < -1e-6 or wc < -1e-6:
                        continue
                    z = wa*a[2] + wb*b[2] + wc*c[2]
                    at = py * size + px
                    if z <= depth[at]:
                        continue
                    depth[at] = z
                    if texture:
                        tw, th, texels = texture
                        u = (wa*uvs[ia][0] + wb*uvs[ib][0] + wc*uvs[ic][0]) % 1.0
                        v = (wa*uvs[ia][1] + wb*uvs[ib][1] + wc*uvs[ic][1]) % 1.0
                        if flip_v:
                            v = (1.0 - v) % 1.0
                        tx = min(tw - 1, int(u * tw))
                        # Match the reusable PNG encoder: output row 0 is stored row H-1.
                        png_y = min(th - 1, int(v * th))
                        ty = th - 1 - png_y
                        ti = (ty * tw + tx) * 4
                        blue, green, red, alpha = texels[ti:ti+4]
                    else:
                        red, green, blue, alpha = 210, 210, 210, 255
                    oi = at * 4
                    pixels[oi:oi+4] = bytes((int(red*lighting), int(green*lighting), int(blue*lighting), alpha))
    output.parent.mkdir(parents=True, exist_ok=True)
    write_png(output, size, size, bytes(pixels), "rgba", "preserve-stored")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--texture-directory", type=Path)
    parser.add_argument("--flip-v", action="store_true")
    parser.add_argument("--size", type=int, default=640)
    args = parser.parse_args()
    render(args.input.resolve(), args.output.resolve(), (args.texture_directory or args.input.parent).resolve(), args.flip_v, args.size)
    print(f"rendered {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
