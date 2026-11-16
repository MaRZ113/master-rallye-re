"""Top-down point renders of PC .map and PS2 MAPxx.DAT vertex clouds (height-coloured)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_tracks import pc_points, ps2_points

def render(p, size=360):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    s = max(x.max() - x.min(), z.max() - z.min())
    u = ((x - x.min()) / s * (size - 1)).astype(int)
    v = ((z - z.min()) / s * (size - 1)).astype(int)
    h = ((y - y.min()) / max(1e-3, y.max() - y.min()) * 255).astype(np.uint8)
    img = np.zeros((size, size, 3), np.uint8)
    img[size - 1 - v, u] = np.stack([h, 255 - h, np.full_like(h, 90)], 1)
    return Image.fromarray(img)

def main():
    out = Path(sys.argv[1]); tiles = []
    for a in sys.argv[2:]:
        p = Path(a)
        pts = ps2_points(p)[0] if p.suffix.upper() == '.DAT' else pc_points(p)[0]
        im = render(pts); tiles.append((p.stem, im))
    W = Image.new('RGB', (370 * len(tiles), 380), (30, 30, 30))
    from PIL import ImageDraw
    d = ImageDraw.Draw(W)
    for i, (n, im) in enumerate(tiles):
        W.paste(im, (i * 370, 20)); d.text((i * 370 + 4, 4), n, fill=(255, 255, 255))
    W.save(out)

if __name__ == '__main__':
    main()
