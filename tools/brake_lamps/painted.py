"""Painted lenses: tail lamps drawn in the body texture (4x4 Evo imports), not modelled as glass.

The lamp is the set of body texels that match a colour rule (red by default). Candidate body triangles are
tessellated to texel scale; a sub-triangle is kept when most of its samples hit the mask. The kept patch is the
lens (its own 3D surface and atlas UVs). Its PC ON core texture is baked from the car's lit atlas
(``<family>-stop-lit``) into a small per-lamp image with planar 0..1 UVs, so the same draw also reads correctly
when BrakeGlow=1 swaps in the PS2 BREAKLIGHTSON texture.
"""
from __future__ import annotations

import numpy as np

from .geometry import Mesh

DEFAULT_MASK = {'min_red': 45, 'red_over_green': 1.4, 'red_over_blue': 1.4, 'min_alpha': 0, 'close_px': 2}


def texture_mask(rgba: np.ndarray, rule: dict | None = None) -> np.ndarray:
    """(H,W) bool: texels that belong to a painted lamp. ``rgba`` (H,W,4) uint8 in image row order."""
    r = {**DEFAULT_MASK, **(rule or {})}
    R, G, B, A = (rgba[..., k].astype(float) for k in range(4))
    m = (R >= r['min_red']) & (R >= r['red_over_green'] * G) & (R >= r['red_over_blue'] * B) & (A >= r['min_alpha'])
    # Closing (dilate, then erode) fills the dark specular/bezel texels inside a painted lamp.
    k = int(r['close_px'])
    def shift(x, op):
        out = x.copy()
        for dy in range(-k, k + 1):
            for dx in range(-k, k + 1):
                out = op(out, np.roll(np.roll(x, dy, 0), dx, 1))
        return out
    if k > 0:
        m = shift(shift(m, np.logical_or), np.logical_and)
    return m


def sample(image: np.ndarray, uv: np.ndarray, *, wrap=True):
    """Nearest texel for UVs (N,2); image (H,W,...) in the row order DxtTexture uses (v=0 at row 0)."""
    h, w = image.shape[:2]
    u, v = uv[:, 0], uv[:, 1]
    if wrap:
        u, v = u % 1.0, v % 1.0
    x = np.clip((u * w).astype(int), 0, w - 1)
    y = np.clip((v * h).astype(int), 0, h - 1)
    return image[y, x]


def _split_bary(pos, uv, max_edge, max_uv_edge):
    """Split one triangle (corner positions/UVs) by midpoints until 3D edges <= max_edge and UV edges <=
    max_uv_edge. Returns barycentric coordinates (N,3) of the points and sub-triangles (M,3)."""
    B = [np.eye(3)[k] for k in range(3)]
    tri = [(0, 1, 2)]
    for _ in range(16):
        cache, out, changed = {}, [], False
        for t in tri:
            p = [B[i] @ pos for i in t]; q = [B[i] @ uv for i in t]
            e = [max(np.linalg.norm(p[(k + 1) % 3] - p[k]) / max_edge, np.linalg.norm(q[(k + 1) % 3] - q[k]) / max_uv_edge) for k in range(3)]
            k = int(np.argmax(e))
            if e[k] <= 1:
                out.append(t); continue
            a, b, c = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
            key = (min(a, b), max(a, b))
            if key not in cache:
                cache[key] = len(B); B.append((B[a] + B[b]) / 2)
            m = cache[key]; out += [(a, m, c), (m, b, c)]; changed = True
        tri = out
        if not changed:
            break
    return np.array(B), np.array(tri, dtype=np.int64)


def painted_patch(draw_faces, geometry, textures, rule=None, *, max_edge=0.03, max_uv_texels=4, coverage=0.25, bounds=None):
    """Kept sub-triangles of the candidate faces.

    ``draw_faces`` [(draw index, [triangle ids])]; ``geometry`` the SDK source geometry per draw; ``textures``
    {draw index: (H,W,4) uint8 of that draw's base texture}. ``bounds`` ((lo xyz), (hi xyz)) keeps only
    sub-triangles whose centre lies inside (the footprint of a converter's lamp sprite, so red decals elsewhere on
    a large face stay unlit). A face whose sub-triangles are all kept is emitted whole.

    Returns a dict: positions, uvs (atlas), normals, colors (4-byte), triangles, source_draw (per triangle),
    stats - or None when no texel matches.
    """
    P, U, N, C, T, S = [], [], [], [], [], []
    stats = {'candidate_triangles': 0, 'kept_triangles': 0, 'whole_faces': 0, 'partial_faces': 0}
    w = np.array([[1 / 3, 1 / 3, 1 / 3], [2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3]])
    for index, ids in draw_faces:
        g = geometry[index]
        img = textures[index]
        mask = texture_mask(img, rule)
        texel = 1.0 / max(img.shape[:2])
        for t in ids:
            stats['candidate_triangles'] += 1
            vs = [g.vertices[i] for i in g.triangles[t]]
            pos = np.array([v.position for v in vs], float)
            uv = np.array([v.uvs[0] for v in vs], float)
            nor = np.array([v.normal for v in vs], float)
            col = np.array([list(v.color) for v in vs], float)
            bary, tri = _split_bary(pos, uv, max_edge, max_uv_texels * texel)
            sub = np.einsum('sk,tkb->tsb', w, bary[tri])            # sample barycentrics
            hit = sample(mask, (sub @ uv).reshape(-1, 2)).reshape(len(tri), len(w)).mean(axis=1) >= coverage
            if bounds is not None:
                c = (bary[tri].mean(axis=1)) @ pos
                hit &= np.all((c >= np.asarray(bounds[0])) & (c <= np.asarray(bounds[1])), axis=1)
            if not hit.any():
                continue
            if hit.all():
                bary, tri, hit = np.eye(3), np.array([[0, 1, 2]]), np.array([True])
                stats['whole_faces'] += 1
            else:
                stats['partial_faces'] += 1
            for k in np.nonzero(hit)[0]:
                base = len(P)
                for b in bary[tri[k]]:
                    P.append(b @ pos); U.append(b @ uv); N.append(b @ nor); C.append(b @ col)
                T.append((base, base + 1, base + 2)); S.append(index)
            stats['kept_triangles'] += int(hit.sum())
    if not T:
        return None
    P, U, N, C = np.array(P), np.array(U), np.array(N), np.array(C)
    key, keep, remap = {}, [], []
    for i, (p, u) in enumerate(zip(P, U)):
        k = (*np.round(p, 6), *np.round(u, 6))
        if k not in key:
            key[k] = len(keep); keep.append(i)
        remap.append(key[k])
    keep = np.array(keep)
    T = np.array([[remap[i] for i in t] for t in T], dtype=np.int64)
    N = N[keep]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return {'positions': P[keep], 'uvs': U[keep], 'normals': N, 'colors': [bytes(np.clip(np.round(c), 0, 255).astype(np.uint8)) for c in C[keep]],
            'triangles': T, 'source_draw': np.array(S), 'stats': stats}


def visible_only(patch: dict, occluders, views, *, tolerance=0.0005):
    """Drop patch triangles no rear view can see (faces inside the body, under the bed cover, behind the cab)."""
    from .geometry import ray_hits
    P, T = patch['positions'], patch['triangles']
    c = P[T].mean(axis=1)
    seen = np.zeros(len(T), bool)
    for d in views.values():
        seen |= ~np.isfinite(ray_hits(c, d, occluders, t_min=tolerance))
    if not seen.any():
        return None
    used = np.unique(T[seen]); remap = {int(v): i for i, v in enumerate(used)}
    out = {k: v for k, v in patch.items()}
    out['positions'] = P[used]; out['uvs'] = patch['uvs'][used]; out['normals'] = patch['normals'][used]
    out['colors'] = [patch['colors'][int(v)] for v in used]
    out['triangles'] = np.array([[remap[int(i)] for i in t] for t in T[seen]], dtype=np.int64)
    out['source_draw'] = patch['source_draw'][seen]
    out['stats'] = {**patch['stats'], 'hidden_triangles_dropped': int((~seen).sum())}
    return out


def components(triangles: np.ndarray, positions: np.ndarray):
    """Connected triangle groups (shared welded positions)."""
    parent = list(range(len(triangles)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    owner = {}
    for i, t in enumerate(triangles):
        for v in t:
            k = tuple(np.round(positions[v], 5))
            if k in owner:
                parent[find(i)] = find(owner[k])
            else:
                owner[k] = i
    groups = {}
    for i in range(len(triangles)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def bake(planar_uv: np.ndarray, atlas_uv: np.ndarray, triangles: np.ndarray, lit: np.ndarray, size=64, dilate=4) -> np.ndarray:
    """Per-lamp PC core image: rasterise the patch in planar UV space, each pixel sampling the lit atlas at the
    interpolated atlas UV. Empty pixels are filled from neighbours so bilinear edges stay lamp-coloured."""
    out = np.zeros((size, size, 4), np.uint8)
    have = np.zeros((size, size), bool)
    ys, xs = np.mgrid[0:size, 0:size]
    pix = np.stack([(xs.ravel() + .5) / size, (ys.ravel() + .5) / size], axis=1)
    for t in triangles:
        a, b, c = planar_uv[t]
        lo = np.floor(np.minimum(np.minimum(a, b), c) * size).astype(int) - 1
        hi = np.ceil(np.maximum(np.maximum(a, b), c) * size).astype(int) + 1
        sel = (xs.ravel() >= lo[0]) & (xs.ravel() <= hi[0]) & (ys.ravel() >= lo[1]) & (ys.ravel() <= hi[1])
        if not sel.any():
            continue
        p = pix[sel]
        v0, v1, v2 = b - a, c - a, p - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-14:
            continue
        w1 = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        w2 = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        w0 = 1 - w1 - w2
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        uv = w0[inside, None] * atlas_uv[t[0]] + w1[inside, None] * atlas_uv[t[1]] + w2[inside, None] * atlas_uv[t[2]]
        idx = np.nonzero(sel)[0][inside]
        out.reshape(-1, 4)[idx] = sample(lit, uv)
        have.reshape(-1)[idx] = True
    for _ in range(dilate):
        if have.all():
            break
        grow = out.copy(); g = have.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = np.roll(np.roll(have, dy, 0), dx, 1); col = np.roll(np.roll(out, dy, 0), dx, 1)
            fill = src & ~g
            grow[fill] = col[fill]; g |= fill
        out, have = grow, g
    if have.any():
        out[~have] = out[have].mean(axis=0).astype(np.uint8)
    out[..., 3] = 255
    return out


def hull_lens(points_2d: np.ndarray):
    """Convex hull (counter-clockwise) of 2D points: the smooth outline a halo ring is grown from."""
    pts = sorted(set(map(tuple, np.round(points_2d, 7))))
    if len(pts) < 3:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def hull_mesh(points_2d: np.ndarray, height: float, frame) -> Mesh:
    """Fan-triangulated hull polygon at ``height`` in the lens frame (world coordinates)."""
    h = hull_lens(points_2d)
    if len(h) < 3:
        raise ValueError('painted lamp too small for a halo outline')
    c = h.mean(axis=0)
    q = np.vstack([c, h])
    world = frame.world(np.column_stack([q, np.full(len(q), height)]))
    tri = [(0, i + 1, (i + 1) % len(h) + 1) for i in range(len(h))]
    return Mesh.of(world, tri)


def read_rgba(dxt: bytes) -> np.ndarray:
    """(H,W,4) RGBA in stored row order (row 0 = v 0, what the GPU samples)."""
    import struct
    _, _, _, w, h = struct.unpack_from('<5I', dxt)
    bgra = np.frombuffer(dxt[20:20 + w * h * 4], np.uint8).reshape(h, w, 4)
    return bgra[..., [2, 1, 0, 3]].copy()


def write_dxt(template: bytes, rgba: np.ndarray) -> bytes:
    """DXT with the template's header words and a new size/payload (BGRA, stored row order)."""
    import struct
    magic, w4, w8, _, _ = struct.unpack_from('<5I', template)
    h, w = rgba.shape[:2]
    return struct.pack('<5I', magic, w4, w8, w, h) + np.ascontiguousarray(rgba[..., [2, 1, 0, 3]]).tobytes()
