#!/usr/bin/env python3
"""COURSE-RENDER-FIX1 offline evidence for the black SpainS2 reflection (no game needed).

1. env-target arithmetic: the ReflectionDebug=2 screenshot shows the 64x64 environment target (4x, top centre). The target is
   0.625 x static term + 0.375 x flipped frame buffer, so (target - static term) is the frame buffer the capture saw.
2. draw order: F10 captures (frame-*.jsonl / named captures of the session log folder) list every draw of one frame in call
   order. The vertex format tells the classes apart: 0x102 sky, 0x142 world, 0x242/0x252 terrain with the second (noise) UV
   set, 0x152/0x112 car body/wheels (both 36/32 byte vertex formats of the PS2 car).

  python reflection_evidence.py --screenshot spains2-env-view.png --env-gxi PS2EnvSource64x64.gxi \
        --capture converted=frame-18300-d1-00051123.jsonl --capture stock=A-start-stationary.jsonl --json evidence.json
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

CAR_FVF = {338, 274}           # 0x152 body, 0x112 wheel
GROUND_FVF = {578, 594}        # 0x242 / 0x252
SKY_FVF = {258}                # 0x102


# ---- minimal PNG reader (8-bit RGB/RGBA, no interlace) -------------------------------------------------------------------

def read_png(path: Path):
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    at, idat, width = 8, b'', 0
    while at < len(data):
        length, kind = struct.unpack('>I4s', data[at:at + 8])
        body = data[at + 8:at + 8 + length]
        if kind == b'IHDR':
            width, height, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', body)
            if depth != 8 or color not in (2, 6) or interlace:
                raise ValueError('only 8-bit RGB/RGBA without interlace is supported')
        elif kind == b'IDAT':
            idat += body
        at += 12 + length
    channels = 3 if color == 2 else 4
    raw = zlib.decompress(idat)
    stride = width * channels
    rows, previous = [], bytearray(stride)
    pos = 0
    for _ in range(height):
        ftype = raw[pos]; line = bytearray(raw[pos + 1:pos + 1 + stride]); pos += 1 + stride
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = previous[i]
            c = previous[i - channels] if i >= channels else 0
            if ftype == 1:
                line[i] = (line[i] + a) & 255
            elif ftype == 2:
                line[i] = (line[i] + b) & 255
            elif ftype == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line); previous = line
    return width, height, channels, rows


def env_arithmetic(screenshot: Path, gxi: Path, x0=192, y0=16, scale=4):
    w, h, ch, rows = read_png(screenshot)
    # target texel (tx, ty) = mean of the scale x scale block
    target = [[[0.0] * 3 for _ in range(64)] for _ in range(64)]
    for ty in range(64):
        for tx in range(64):
            acc = [0, 0, 0]
            for dy in range(scale):
                row = rows[y0 + ty * scale + dy]
                for dx in range(scale):
                    p = (x0 + tx * scale + dx) * ch
                    acc[0] += row[p]; acc[1] += row[p + 1]; acc[2] += row[p + 2]
            target[ty][tx] = [v / (scale * scale) for v in acc]
    gx = gxi.read_bytes()
    pix = gx[8:8 + 64 * 64 * 4]
    static = [[[0.0] * 3 for _ in range(64)] for _ in range(64)]
    for ty in range(64):
        src_row = 63 - ty                    # rows reversed as uploaded (ReflectionPilot convert_static_env)
        for tx in range(64):
            p = (src_row * 64 + tx) * 4
            static[ty][tx] = [float((pix[p + c] * 80) // 128) for c in range(3)]
    bands = []
    for r0 in range(0, 64, 4):
        diff = [0.0, 0.0, 0.0]
        tmean = [0.0, 0.0, 0.0]
        for ty in range(r0, r0 + 4):
            for tx in range(64):
                for c in range(3):
                    diff[c] += target[ty][tx][c] - static[ty][tx][c]
                    tmean[c] += target[ty][tx][c]
        n = 4 * 64
        bands.append({'rows': [r0, r0 + 3], 'target_mean': [round(v / n, 1) for v in tmean], 'framebuffer_term_mean': [round(v / n, 1) for v in diff]})
    empty = [b for b in bands if max(abs(v) for v in b['framebuffer_term_mean']) < 2.0]
    lit = [b for b in bands if min(b['framebuffer_term_mean']) > 40.0]
    first_lit = lit[0]['rows'][0] if lit else None
    return {
        'screenshot': screenshot.name,
        'bands': bands,
        'empty_framebuffer_term_rows': [empty[0]['rows'][0], empty[-1]['rows'][1]] if empty else None,
        'first_lit_row': first_lit,
        'reading': ('The framebuffer term is exactly zero (target == static term) from the top of the target (screen bottom, the '
                    'ground) down to the horizon and bright from the horizon on: the frame buffer seen by the capture held the sky '
                    'and nothing else.') if empty and lit else 'inconclusive',
    }


# ---- draw order -------------------------------------------------------------------------------------------------------------

def load_draws(path: Path):
    draws = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get('type') == 'draw':
            draws.append(record)
    return draws


def draw_order(path: Path):
    draws = load_draws(path)
    triangles = [d.get('primitive_count') or 0 for d in draws]
    fvf = [d['state'].get('vertex_shader') for d in draws]
    total = sum(triangles)
    first_car = next((i for i, f in enumerate(fvf) if f in CAR_FVF), None)
    ground_total = sum(t for t, f in zip(triangles, fvf) if f in GROUND_FVF)
    before = triangles[:first_car] if first_car is not None else triangles
    fvf_before = fvf[:first_car] if first_car is not None else fvf
    ground_before = sum(t for t, f in zip(before, fvf_before) if f in GROUND_FVF)
    return {
        'capture': path.name, 'draws': len(draws), 'triangles': total,
        'first_car_draw_index': first_car,
        'triangles_before_first_car_draw': sum(before),
        'ground_class_triangles_total': ground_total,
        'ground_class_triangles_before_first_car_draw': ground_before,
        'ground_class_fraction_before_first_car_draw': round(ground_before / ground_total, 3) if ground_total else None,
        'ground_class_draws_after_first_car_draw': sum(1 for f in fvf[first_car:] if f in GROUND_FVF) if first_car is not None else 0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--screenshot', type=Path)
    parser.add_argument('--env-gxi', type=Path)
    parser.add_argument('--capture', action='append', default=[], metavar='LABEL=FILE')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args(argv)
    result = {}
    if args.screenshot and args.env_gxi:
        result['env_arithmetic'] = env_arithmetic(args.screenshot, args.env_gxi)
    result['draw_order'] = {}
    for item in args.capture:
        label, _, name = item.partition('=')
        result['draw_order'][label] = draw_order(Path(name))
    text = json.dumps(result, indent=1)
    if args.json:
        args.json.write_text(text, encoding='utf-8')
    else:
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
