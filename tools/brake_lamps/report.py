"""Penetration heat map and JSON report for fitted (or existing) lamp layers."""
from __future__ import annotations

import numpy as np

from .analysis import layer_visibility
from .geometry import Mesh, view_directions

# 0 hidden views = green, all 8 = red; buried along the lens normal = magenta outline.
def _colour(hidden, total):
    f = hidden / max(total, 1)
    return (int(255 * min(1, 2 * f)), int(255 * min(1, 2 * (1 - f))), 40)


def heat_panel(layers, occluders: Mesh, frame, *, size=300, title='', bounds=None):
    """Orthographic view along the lens normal; each sample dot coloured by how many of the 8 views hide it."""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (size, size + 16), (24, 26, 30))
    d = ImageDraw.Draw(img)
    d.text((4, 2), title, fill=(230, 230, 230))
    views = view_directions()
    pts_all = []
    data = []
    for name, mesh in layers:
        if not len(mesh.triangles):
            continue
        _, raw = layer_visibility(mesh, occluders, views=views)
        q = frame.local(raw['samples'])[:, :2]
        pts_all.append(q)
        data.append((name, mesh, q, raw['hidden_views']))
    if not data:
        return img
    allq = np.vstack(pts_all)
    lo, hi = bounds if bounds is not None else (allq.min(0), allq.max(0))
    scale = (size - 20) / max(float((hi - lo).max()), 1e-6)
    to = lambda p: (10 + (p[0] - lo[0]) * scale, 16 + size - 10 - (p[1] - lo[1]) * scale)
    for name, mesh, q, hidden in data:
        tq = frame.local(mesh.positions)[:, :2]
        for t in mesh.triangles:
            d.polygon([to(tq[i]) for i in t], outline=(70, 70, 80) if name == 'halo' else (110, 110, 120))
    for name, mesh, q, hidden in data:
        r = 1.5 if name == 'halo' else 2.5
        for p, h in zip(q, hidden):
            x, y = to(p)
            d.ellipse((x - r, y - r, x + r, y + r), fill=_colour(int(h), len(views)))
    return img


def heat_sheet(rows, path):
    """rows: list of (label, [PIL panels]) -> one PNG."""
    from PIL import Image, ImageDraw
    if not rows:
        return None
    w = max(sum(p.width for p in panels) for _, panels in rows) + 140
    h = sum(max(p.height for p in panels) for _, panels in rows)
    sheet = Image.new('RGB', (w, h + 24), (16, 16, 18))
    d = ImageDraw.Draw(sheet)
    d.text((6, 4), 'dots: green = visible from all 8 rear views, red = hidden from all 8 (buried in the body)', fill=(230, 230, 230))
    y = 24
    for label, panels in rows:
        d.text((6, y + 20), label, fill=(240, 200, 120))
        x = 140
        for p in panels:
            sheet.paste(p, (x, y)); x += p.width
        y += max(p.height for p in panels)
    sheet.save(path)
    return path
