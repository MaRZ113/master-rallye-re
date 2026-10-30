"""Bounded, opt-in native texture derivations; source buffers stay immutable.

These operations describe MR authoring, never donor renderer equivalence.
"""
from collections import deque
import math

MAX_PIXELS = 4 * 1024 * 1024


def dimensions(raw, width, height):
    if any(type(v) is not int or v <= 0 for v in (width, height)) or width * height > MAX_PIXELS:
        raise ValueError('texture pixel budget')
    if len(raw) != width * height * 4:
        raise ValueError('texture channel count')


def transparent_edge_padding(bgra, width, height, *, radius=8):
    """Nearest opaque RGB into zero-alpha texels, stable row-major tie breaks.

    A bounded four-neighbour wavefront never crosses a partially opaque pixel.
    Every nonzero-alpha pixel and every alpha byte are bit-identical. No alpha
    dilation, palette editing, UV change or global atlas substitution occurs.
    """
    dimensions(bgra, width, height)
    if type(radius) is not int or not 1 <= radius <= 32:
        raise ValueError('padding radius budget')
    out = bytearray(bgra)
    distance = bytearray([255]) * (width * height)
    queue = deque()
    for i in range(width * height):
        if bgra[4*i+3] == 255:
            distance[i] = 0
            queue.append(i)
    if not queue:
        raise ValueError('padding requires opaque seed pixels')
    changed = 0
    while queue:
        i = queue.popleft()
        if distance[i] >= radius:
            continue
        x, y = i % width, i // width
        for j in ((i-1 if x else -1), (i+1 if x+1 < width else -1),
                  (i-width if y else -1), (i+width if y+1 < height else -1)):
            if j < 0 or distance[j] != 255 or bgra[4*j+3] != 0:
                continue
            distance[j] = distance[i] + 1
            out[4*j:4*j+3] = out[4*i:4*i+3]
            changed += out[4*j:4*j+3] != bgra[4*j:4*j+3]
            queue.append(j)
    return bytes(out), {'operation':'transparent-edge-padding/1','radius':radius,
                        'changed_zero_alpha_rgb_pixels':changed,'alpha_preserved':True,
                        'nonzero_alpha_pixels_preserved':True}


def polygon_pixels(polygons, width, height):
    """Pixel-centre coverage of explicit atlas contours (no color heuristics)."""
    if any(type(v) is not int or v <= 0 for v in (width, height)) or width*height > MAX_PIXELS:
        raise ValueError('coverage pixel budget')
    if not isinstance(polygons, (list, tuple)) or not 1 <= len(polygons) <= 512:
        raise ValueError('coverage polygon budget')
    covered = set(); work=0
    for points in polygons:
        if not 3 <= len(points) <= 32 or any(len(p)!=2 or any(not math.isfinite(v) for v in p) for p in points):
            raise ValueError('invalid coverage contour')
        if any(not (0 <= x <= width and 0 <= y <= height) for x,y in points):
            raise ValueError('coverage outside atlas')
        work+=(math.ceil(max(p[0]for p in points))-math.floor(min(p[0]for p in points)))*(math.ceil(max(p[1]for p in points))-math.floor(min(p[1]for p in points)))
        if work>16*1024*1024:raise ValueError('coverage work budget')
    for points in polygons:
        for y in range(max(0, math.floor(min(p[1] for p in points))), min(height, math.ceil(max(p[1] for p in points)))):
            for x in range(max(0, math.floor(min(p[0] for p in points))), min(width, math.ceil(max(p[0] for p in points)))):
                inside = False
                for (ax,ay),(bx,by) in zip(points, points[1:]+points[:1]):
                    if (ay > y+.5) != (by > y+.5) and x+.5 < (bx-ax)*(y+.5-ay)/(by-ay)+ax:
                        inside = not inside
                if inside:
                    covered.add(y*width+x)
    return covered


def lens_textures(bgra, width, height, contours):
    """Explicit authored red-lens contours, including highlights, not all red.

    OFF remains untouched. ON and glow cover the same complete contour; original
    alpha is retained. Contours must be qualified by source faces/UV ownership.
    """
    dimensions(bgra, width, height)
    pixels = polygon_pixels(contours, width, height)
    lit = bytearray(bgra); glow = bytearray(len(bgra))
    for i in sorted(pixels):
        b,g,r,a = bgra[4*i:4*i+4]
        lit[4*i:4*i+4] = bytes((min(90, b), min(100, g), max(r, min(255, 100+r)), a))
        glow[4*i:4*i+4] = bytes((10,20,255, min(100, a)))
    return bytes(lit), bytes(glow), sorted(pixels)
