"""Grid contact sheet of top-down stage renders: python contact_sheet.py out.png cols label=path ..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_tracks import pc_points, ps2_points
from topdown import render

out, cols = Path(sys.argv[1]), int(sys.argv[2])
items = [a.split('=', 1) for a in sys.argv[3:]]
T = 260
rows = (len(items) + cols - 1) // cols
W = Image.new('RGB', (cols * (T + 6), rows * (T + 22)), (25, 25, 25))
d = ImageDraw.Draw(W)
for k, (label, path) in enumerate(items):
    p = Path(path)
    pts = ps2_points(p)[0] if p.suffix.upper() == '.DAT' else pc_points(p)[0]
    im = render(pts, T)
    x, y = (k % cols) * (T + 6), (k // cols) * (T + 22)
    W.paste(im, (x, y + 18)); d.text((x + 3, y + 3), label, fill=(255, 255, 255))
W.save(out)
