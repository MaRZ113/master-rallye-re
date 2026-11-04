"""Convert an image into an ATMOSPHERE sun starburst sprite (SunRaysTexture=).

The sprite is drawn ADDITIVELY around the sun, centred on the image centre:
black = no light. Output is the 20-byte header used by the custom sky layers
(0xfeed, 0, 0, 256, 256) followed by 256x256 BGRA pixels. The proxy multiplies
it by the sun colour and the current-frame depth visibility, exactly like the
procedural spokes. Requires ffmpeg on PATH.

    python atmosphere_sun_sprite.py rays.png Atmosphere25/sun_rays.dxt [--gray]
"""
from __future__ import annotations
import argparse
import struct
import subprocess
from pathlib import Path

SIZE = 256


def convert(source: Path, output: Path, gray: bool = False) -> bytes:
    filters = f'scale={SIZE}:{SIZE}:flags=lanczos' + (',format=gray,format=bgra' if gray else ',format=bgra')
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(source), '-vf', filters, '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'bgra', '-'], capture_output=True, check=True).stdout
    if len(raw) != SIZE * SIZE * 4:
        raise ValueError(f'unexpected decoded size {len(raw)}')
    pixels = bytearray(raw)
    pixels[3::4] = bytes([255]) * (SIZE * SIZE)  # additive sprite: alpha unused
    data = struct.pack('<5I', 0xfeed, 0, 0, SIZE, SIZE) + bytes(pixels)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--gray', action='store_true', help='use luminance only (sun colour comes from Sun* keys)')
    args = parser.parse_args()
    data = convert(args.source, args.output, args.gray)
    print(f'{args.output}: {len(data)} bytes')


if __name__ == '__main__':
    main()
