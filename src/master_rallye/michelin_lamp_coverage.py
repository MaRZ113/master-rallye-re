"""Versioned RAV4 rear-lens authoring, separate from source runtime semantics.

The contours follow the red portions of the original rear atlas. Amber upper
lamps, the pale inset (reverse/highlight identity unqualified), black inner
housing, Toyota emblem and bumper reflectors are deliberately excluded.
No RGB threshold can promote an unrelated red source texel to a brake light.
"""
from __future__ import annotations
import math
from .material_derivation import polygon_pixels

SCENE_SHA256 = '7ab8b1525fb078aee8fcd524a3d8b3816670668708102e9a4a36ec257074f27c'
ATLAS_RGBA_SHA256 = '45d472d949f4b8936d9a915c0b530628f5ac6dc6ae67bff697dffc9ab89444f4'
MESH_ID = 'body-texture-007'
# Pixel-edge coordinates, not normalized UVs. The concave notch preserves the
# original pale inset; it is not proven to be an original brake-emitting area.
LEFT_CONTOUR = ((45, 63), (60, 63), (60, 65), (53, 65),
                (53, 71), (60, 71), (60, 77), (45, 77))
CONTOURS = (LEFT_CONTOUR, tuple((256-x, y) for x, y in LEFT_CONTOUR))


def _inside_triangle(points, x, y):
    a, b, c = points
    denominator = ((b[1]-c[1])*(a[0]-c[0]) +
                   (c[0]-b[0])*(a[1]-c[1]))
    if abs(denominator) < 1e-12:
        return False
    first = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denominator
    second = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denominator
    return min(first, second, 1-first-second) >= -1e-9


def uv_coverage(mesh, pixels, width, height, *, filter_radius=1):
    """Bound exact lit texels to original faces, including sampling neighbours.

    The one-texel support includes original triangles sampling across a contour
    boundary under bilinear filtering. Their non-lens texels remain alpha zero
    in the separate ON overlay; their ordinary diffuse body stays untouched.
    Missing coverage fails instead of silently dropping part of a lens.
    """
    if any(type(v) is not int or v <= 0 for v in (width, height)) or width*height > 1024*1024:
        raise ValueError('lamp atlas budget')
    if type(filter_radius) is not int or not 0 <= filter_radius <= 2:
        raise ValueError('lamp filter support budget')
    if not isinstance(pixels,(set,list,tuple)) or len(pixels) > 65536:
        raise ValueError('lamp coverage allocation budget')
    pixels = set(pixels)
    if not pixels or any(type(i) is not int or not 0 <= i < width*height for i in pixels):
        raise ValueError('invalid lamp coverage pixels')
    triangles, uvs = mesh['triangles'], mesh['uvs']
    if len(triangles) > 4096 or len(uvs) > 16384:
        raise ValueError('lamp mesh budget')
    if any(len(v) != 2 or any(not math.isfinite(x) for x in v) for v in uvs):
        raise ValueError('invalid lamp UV values')
    if any(len(t) != 3 or any(type(i) is not int or not 0 <= i < len(uvs) for i in t) for t in triangles):
        raise ValueError('invalid lamp UV index')
    support = {yy*width+xx for i in pixels
               for yy in range(max(0,i//width-filter_radius), min(height,i//width+filter_radius+1))
               for xx in range(max(0,i%width-filter_radius), min(width,i%width+filter_radius+1))}
    if len(triangles)*(len(pixels)+len(support)) > 8_000_000:
        raise ValueError('lamp coverage work budget')
    covered = set()
    faces = []
    direct_counts = {}
    for face_id, ids in enumerate(triangles):
        points = [(uvs[i][0]*width, uvs[i][1]*height) for i in ids]
        direct = {i for i in pixels if _inside_triangle(points, i%width+.5, i//width+.5)}
        covered.update(direct)
        if direct or any(_inside_triangle(points,i%width+.5,i//width+.5) for i in support):
            faces.append(face_id)
            direct_counts[str(face_id)] = len(direct)
    missing = pixels-covered
    if missing:
        raise ValueError('lamp contour has texels outside original source faces')
    return {'source_face_ids':faces, 'lit_pixel_count':len(pixels),
            'direct_pixel_counts_by_face':direct_counts,
            'uncovered_lit_pixels':0, 'filter_support_radius':filter_radius}


def rav4_coverage(scene, source_scene_sha256):
    """Admit only the qualified Toyota topology and exact original rear atlas."""
    if source_scene_sha256 != SCENE_SHA256 or scene['source'].get('catalog') != 'Car25A.PDO':
        raise ValueError('RAV4 lamp recipe requires exact accepted source scene')
    mesh = next(m for m in scene['meshes'] if m['id'] == MESH_ID)
    material = next(m for m in scene['materials'] if m['id'] == mesh['material_id'])
    texture = next(t for t in scene['textures'] if t['id'] == material['diffuse_texture_id'])
    if len(mesh['triangles']) != 90 or (texture['width'],texture['height']) != (256,128) or texture['rgba_sha256'] != ATLAS_RGBA_SHA256:
        raise ValueError('RAV4 original rear topology or atlas mismatch')
    pixels = polygon_pixels(CONTOURS,256,128)
    report = uv_coverage(mesh,pixels,256,128)
    return {'schema':'michelin-rav4-lamp-coverage/1', 'interpretation':'mr_authoring',
            'source_scene_sha256':source_scene_sha256, 'mesh_id':MESH_ID,
            'source_atlas_rgba_sha256':ATLAS_RGBA_SHA256, 'atlas_size':[256,128],
            'contours':CONTOURS, 'lit_pixels':sorted(pixels), **report,
            'source_runtime_brake_ownership':'WARN_NOT_RECOVERED',
            'pale_inset_identity':'UNRESOLVED_REVERSE_OR_HIGHLIGHT_EXCLUDED',
            'evidence':'Original rear texture and UV inspection. Explicit conservative red-lens contours; amber upper area and pale inset excluded. This is reversible MR authoring, not recovered Michelin brake shader behavior.',
            'required_native_mode':'masked_overlay',
            'opaque_body_must_remain_diffuse':True,
            'original_off_texture_geometry_uv_must_remain_unchanged':True}
