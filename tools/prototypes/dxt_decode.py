#!/usr/bin/env python3
"""Decode the observed 20-byte uncompressed DXT with explicit row policy."""
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

MAGIC = 0x0000FEED
ROW_POLICIES = ("preserve-stored", "flip-vertical")


def parse_dxt(path):
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("file too short")
    magic, word04, word08, width, height = struct.unpack_from("<5I", data)
    if magic != MAGIC:
        raise ValueError(f"bad magic 0x{magic:08X}")
    expected = 20 + width * height * 4
    if len(data) != expected:
        raise ValueError(f"size mismatch: expected {expected}, got {len(data)}")
    return {
        "magic": magic,
        "word_0x04": word04,
        "word_0x08": word08,
        "width": width,
        "height": height,
    }, data[20:]


def png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_png(path, width, height, pixels, order, row_policy="flip-vertical"):
    if row_policy not in ROW_POLICIES:
        raise ValueError(f"unknown row policy {row_policy!r}")
    rows = []
    row_indices = range(height)
    if row_policy == "flip-vertical":
        row_indices = reversed(range(height))
    for y in row_indices:
        row = bytearray([0])
        source = pixels[y * width * 4:(y + 1) * width * 4]
        for index in range(0, len(source), 4):
            c0, c1, c2, alpha = source[index:index + 4]
            row.extend((c2, c1, c0, alpha) if order == "bgra" else (c0, c1, c2, alpha))
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + png_chunk(b"IEND", b"")
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--order", choices=("bgra", "rgba"), default="bgra")
    parser.add_argument("--row-policy", choices=ROW_POLICIES, default="flip-vertical")
    args = parser.parse_args()
    header, pixels = parse_dxt(args.input)
    write_png(
        args.output,
        header["width"],
        header["height"],
        pixels,
        args.order,
        args.row_policy,
    )
    print(
        f"decoded {header['width']}x{header['height']} {args.order} "
        f"rows={args.row_policy} -> {args.output}"
    )


if __name__ == "__main__":
    main()
