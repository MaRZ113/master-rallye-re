"""ATMOSPHERE6.8: convert the owner's own GT3 lamp glare texture into a lamp glint sprite.

Input : a GT3 Tex1 file from the owner's extracted disc (e.g. race/glare.img), decoded with
        the local GTPS2ModelTool (`dump -i <file>.tex1` writes <file>.png).
Output: 256x256 BGRA sprite with the 20-byte custom header (0xfeed, 1, crc32, 256, 256) read
        by Atmosphere.ini LampGlintTexture. Colour becomes grey luminance (the DLL tints white
        for headlights, red for tail lamps); alpha 255 (additive sprite).

Private use only: the sprite is derived from the owner's GT3 copy and is written to the
owner's game folder; it is never committed or redistributed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import zlib

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True, help='GT3 Tex1 file, e.g. gt3-extract/race/glare.img')
    ap.add_argument('--decoder', type=Path, required=True, help='GTPS2ModelTool.exe')
    ap.add_argument('--output', type=Path, required=True, help='sprite file, e.g. Atmosphere/glints/gt3-glare.dxt')
    ap.add_argument('--gamma', type=float, default=1.0, help='>1 thins the rays, <1 thickens them')
    a = ap.parse_args()
    raw = a.source.read_bytes()
    if raw[:4] != b'Tex1':
        raise ValueError('not a Tex1 texture')
    with tempfile.TemporaryDirectory() as tmp:
        tex = Path(tmp) / 'glare.tex1'
        shutil.copyfile(a.source, tex)
        run = subprocess.run([str(a.decoder.resolve()), 'dump', '-i', str(tex)], cwd=tmp, capture_output=True, text=True)
        if run.returncode or not tex.with_suffix('.png').is_file():
            raise ValueError('Tex1 decoder failed: ' + run.stdout[-400:] + run.stderr[-400:])
        image = Image.open(tex.with_suffix('.png')).convert('RGBA')
    rgba = np.asarray(image.resize((256, 256), Image.Resampling.LANCZOS)).astype(np.float32) / 255
    # Additive glare: brightness = max channel weighted by alpha (PS2 alpha is 0..1 here).
    value = rgba[:, :, :3].max(axis=2) * rgba[:, :, 3]
    value = np.clip(value / max(value.max(), 1e-6), 0, 1) ** a.gamma
    grey = np.rint(value * 255).astype(np.uint8)
    bgra = np.dstack([grey, grey, grey, np.full_like(grey, 255)])
    body = bgra.tobytes()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(struct.pack('<5I', 0xfeed, 1, zlib.crc32(body) & 0xffffffff, 256, 256) + body)
    report = {'tool': 'atmosphere_gt3_glare.py', 'source_sha256': hashlib.sha256(raw).hexdigest(), 'source_size': list(image.size),
              'output': str(a.output), 'output_sha256': hashlib.sha256(a.output.read_bytes()).hexdigest(), 'gamma': a.gamma,
              'policy': 'private: derived from the owner GT3 copy, never committed'}
    a.output.with_suffix('.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
