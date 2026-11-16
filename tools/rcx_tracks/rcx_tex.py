"""RCX TEX v1 decoder (magic 0x0DA7ADDE; A8R8G8B8, X8R8G8B8, DXT1, DXT3), top mip only."""
from __future__ import annotations
import struct
from PIL import Image

FORMATS = {21: 'A8R8G8B8', 22: 'X8R8G8B8', 0x31545844: 'DXT1', 0x33545844: 'DXT3'}


def decode_tex(data: bytes) -> dict:
    magic, version, w, h, fmt, levels = struct.unpack_from('<6I', data)
    if magic != 0x0DA7ADDE or version != 1 or fmt not in FORMATS:
        raise ValueError('unsupported TEX')
    if fmt in (21, 22):
        rgba = bytearray(Image.frombytes('RGBA', (w, h), data[24:24 + w * h * 4], 'raw', 'BGRA').tobytes())
        if fmt == 22:
            rgba[3::4] = b'\xff' * (w * h)
        rgba = bytes(rgba)
    else:
        size = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * (8 if fmt == 0x31545844 else 16)
        rgba = Image.frombytes('RGBA', (w, h), data[24:24 + size], 'bcn', (1, 'DXT1') if fmt == 0x31545844 else (2, 'DXT3')).tobytes()
    return {'width': w, 'height': h, 'format': FORMATS[fmt], 'rgba': rgba}
