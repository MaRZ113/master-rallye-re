"""PNG <-> Master Rallye FEED texture container.

FEED layout (Retail ``*.dxt``, verified on every Retail course texture):
``u32 0xFEED, u32 1, u32 crc32(payload), u32 width, u32 height`` followed by
uncompressed BGRA32 rows stored bottom-up. Word 2 is the zlib CRC-32 of the
payload, so any new texture with the right CRC is a native texture.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

FEED_MAGIC = 0xFEED
MAX_TEXTURE_SIZE = 2048


class TextureError(ValueError):
    pass


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def decode_png(data: bytes) -> tuple[int, int, bytes]:
    """Return (width, height, RGBA8 top-down) for 8-bit grey/RGB/palette/grey-alpha/RGBA PNGs."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise TextureError("not a PNG file")
    pos, idat, palette, trns = 8, bytearray(), None, None
    width = height = depth = ctype = interlace = None
    while pos + 8 <= len(data):
        size = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + size]
        pos += 12 + size
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"PLTE":
            palette = chunk
        elif kind == b"tRNS":
            trns = chunk
        elif kind == b"IDAT":
            idat.extend(chunk)
        elif kind == b"IEND":
            break
    if width is None:
        raise TextureError("PNG has no IHDR")
    if depth != 8 or interlace:
        raise TextureError("only 8-bit non-interlaced PNG is supported (re-save the image as 8-bit PNG)")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if channels is None:
        raise TextureError(f"unsupported PNG colour type {ctype}")
    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    out = bytearray(width * height * 4)
    prev = bytearray(stride)
    src = 0
    for y in range(height):
        ftype = raw[src]
        line = bytearray(raw[src + 1:src + 1 + stride])
        src += 1 + stride
        if ftype == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up_left = prev[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(left, prev[i], up_left)) & 255
        elif ftype != 0:
            raise TextureError(f"bad PNG filter {ftype}")
        base = y * width * 4
        for x in range(width):
            s = x * channels
            if ctype == 6:
                r, g, b, a = line[s:s + 4]
            elif ctype == 2:
                r, g, b = line[s:s + 3]
                a = 255
            elif ctype == 0:
                r = g = b = line[s]
                a = 255
            elif ctype == 4:
                r = g = b = line[s]
                a = line[s + 1]
            else:
                index = line[s]
                if palette is None or 3 * index + 3 > len(palette):
                    raise TextureError("PNG palette index out of range")
                r, g, b = palette[3 * index:3 * index + 3]
                a = trns[index] if trns is not None and index < len(trns) else 255
            out[base + 4 * x:base + 4 * x + 4] = bytes((r, g, b, a))
        prev = line
    return width, height, bytes(out)


def encode_png(width: int, height: int, rgba: bytes) -> bytes:
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    rows = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def target_size(width: int, height: int, *, max_size: int = MAX_TEXTURE_SIZE) -> tuple[int, int]:
    def fit(v):
        p = 1
        while p * 2 <= v:
            p *= 2
        if p < v and (v - p) > (2 * p - v):
            p *= 2
        return max(4, min(max_size, p))
    return fit(width), fit(height)


def resize_rgba(width: int, height: int, rgba: bytes, new_w: int, new_h: int) -> bytes:
    """Area-average (down) / bilinear-free nearest (up) resample; enough for texture conforming."""
    if (width, height) == (new_w, new_h):
        return rgba
    out = bytearray(new_w * new_h * 4)
    sx, sy = width / new_w, height / new_h
    for y in range(new_h):
        y0, y1 = int(y * sy), max(int(y * sy) + 1, int((y + 1) * sy))
        for x in range(new_w):
            x0, x1 = int(x * sx), max(int(x * sx) + 1, int((x + 1) * sx))
            acc = [0, 0, 0, 0]
            n = 0
            for yy in range(y0, min(y1, height)):
                row = yy * width * 4
                for xx in range(x0, min(x1, width)):
                    p = row + 4 * xx
                    acc[0] += rgba[p]; acc[1] += rgba[p + 1]; acc[2] += rgba[p + 2]; acc[3] += rgba[p + 3]
                    n += 1
            o = (y * new_w + x) * 4
            out[o:o + 4] = bytes(v // max(n, 1) for v in acc)
    return bytes(out)


def encode_feed(width: int, height: int, rgba_top_down: bytes) -> bytes:
    if len(rgba_top_down) != width * height * 4:
        raise TextureError("RGBA size does not match the texture dimensions")
    if not (is_power_of_two(width) and is_power_of_two(height)):
        raise TextureError(f"{width}x{height} is not a power of two")
    payload = bytearray()
    stride = width * 4
    for y in reversed(range(height)):
        row = rgba_top_down[y * stride:(y + 1) * stride]
        for i in range(0, stride, 4):
            payload.extend((row[i + 2], row[i + 1], row[i], row[i + 3]))
    payload = bytes(payload)
    return struct.pack("<5I", FEED_MAGIC, 1, zlib.crc32(payload) & 0xFFFFFFFF, width, height) + payload


def decode_feed(data: bytes) -> tuple[int, int, bytes]:
    if len(data) < 20:
        raise TextureError("FEED texture is truncated")
    magic, one, crc, width, height = struct.unpack_from("<5I", data)
    if magic != FEED_MAGIC:
        raise TextureError("not a FEED texture")
    payload = data[20:]
    if len(payload) != width * height * 4:
        raise TextureError("FEED payload size mismatch")
    out = bytearray(len(payload))
    stride = width * 4
    for y in range(height):
        src = payload[(height - 1 - y) * stride:(height - y) * stride]
        for i in range(0, stride, 4):
            out[y * stride + i:y * stride + i + 4] = bytes((src[i + 2], src[i + 1], src[i], src[i + 3]))
    return width, height, bytes(out)


def feed_is_valid(data: bytes) -> bool:
    try:
        magic, one, crc, width, height = struct.unpack_from("<5I", data)
    except struct.error:
        return False
    return magic == FEED_MAGIC and len(data) == 20 + width * height * 4 and zlib.crc32(data[20:]) & 0xFFFFFFFF == crc


def has_alpha(rgba: bytes) -> bool:
    return any(a != 255 for a in rgba[3::4])


def convert_image(path: Path, *, max_size: int = MAX_TEXTURE_SIZE) -> tuple[bytes, dict]:
    """PNG (or existing FEED) file -> FEED bytes conformed to power-of-two size."""
    data = Path(path).read_bytes()
    if data[:4] == struct.pack("<I", FEED_MAGIC):
        if not feed_is_valid(data):
            raise TextureError(f"{path}: FEED texture fails its CRC/size check")
        w, h, rgba = decode_feed(data)
    else:
        w, h, rgba = decode_png(data)
    nw, nh = target_size(w, h, max_size=max_size)
    report = {"source": str(path), "source_size": [w, h], "size": [nw, nh], "resized": (nw, nh) != (w, h)}
    if (nw, nh) != (w, h):
        rgba = resize_rgba(w, h, rgba, nw, nh)
    report["has_alpha"] = has_alpha(rgba)
    return encode_feed(nw, nh, rgba), report


def solid_texture(rgba: tuple[int, int, int, int], size: int = 8) -> bytes:
    return encode_feed(size, size, bytes(rgba) * (size * size))


def noise_texture(size: int = 64, seed: int = 1) -> bytes:
    """Neutral grey detail texture for the ground noise pass of a new course."""
    state = seed & 0xFFFFFFFF
    pixels = bytearray()
    for _ in range(size * size):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        v = 112 + (state >> 16) % 32
        pixels.extend((v, v, v, 255))
    return encode_feed(size, size, bytes(pixels))
