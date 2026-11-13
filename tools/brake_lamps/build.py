"""Brake Glow-ON authoring: resolve sources, auto-fit onto the OFF lens, compile car.dx + registry rows.

Requires the Vehicle SDK (``master_rallye``) on sys.path for reading/writing car.dx.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace as dc_replace
import hashlib
import math

import numpy as np

from . import analysis
from .carmodel import face_ids, ON_CORE_TEXTURE, ON_GLOW_TEXTURE
from .geometry import Mesh, closest_on_mesh, merge, ray_hits, rotation_matrix
from .spec import normalise, SpecError

WHITE = b'\xff\xff\xff\xff'
BLAZER_HALO_WIDTH = 0.45   # Blazer ring width / lens extent (retail ChevyBlazer: ~6 cm ring on a ~13 cm lens)
POLICY = {'ANY': 'ANY_MODEL', 'PC': 'PC_BODY_ONLY', 'PS2': 'PS2_BODY_ONLY'}


@dataclass
class Layer:
    """Lamp layer mesh with per-vertex attributes (model space)."""
    positions: np.ndarray
    uvs: np.ndarray
    triangles: np.ndarray
    normals: np.ndarray | None = None
    colors: list | None = None

    def mesh(self) -> Mesh:
        return Mesh(self.positions, self.triangles)

    def copy(self) -> 'Layer':
        return Layer(self.positions.copy(), self.uvs.copy(), self.triangles.copy(),
                     None if self.normals is None else self.normals.copy(), None if self.colors is None else list(self.colors))

    @staticmethod
    def from_geometry(g) -> 'Layer':
        return Layer(np.array([v.position for v in g.vertices], float), np.array([v.uvs[0] if v.uvs else (0, 0) for v in g.vertices], float),
                     np.array(g.triangles, dtype=np.int64).reshape(-1, 3), np.array([v.normal for v in g.vertices], float),
                     [bytes(v.color) for v in g.vertices])

    def geometry(self):
        from master_rallye.topology_writer import CompiledVertex, DrawGeometry
        n = self.normals if self.normals is not None else np.tile([0.0, 0.0, -1.0], (len(self.positions), 1))
        c = self.colors or [WHITE] * len(self.positions)
        verts = tuple(CompiledVertex(tuple(float(x) for x in p), tuple(float(x) for x in nn), cc, ((float(u[0]), float(u[1])),))
                      for p, nn, cc, u in zip(self.positions, n, c, self.uvs))
        return DrawGeometry(verts, tuple(tuple(int(i) for i in t) for t in self.triangles))


def join(layers) -> Layer:
    layers = [l for l in layers if len(l.triangles)]
    pos, uv, tri, nor, col = [], [], [], [], []
    at = 0
    for l in layers:
        pos.append(l.positions); uv.append(l.uvs); tri.append(l.triangles + at)
        nor.append(l.normals if l.normals is not None else np.tile([0.0, 0.0, -1.0], (len(l.positions), 1)))
        col += l.colors or [WHITE] * len(l.positions); at += len(l.positions)
    return Layer(np.vstack(pos), np.vstack(uv), np.vstack(tri), np.vstack(nor), col)


# ---------------------------------------------------------------- lens frame

@dataclass
class Frame:
    origin: np.ndarray
    normal: np.ndarray   # outward
    u: np.ndarray        # horizontal in-plane axis (follows +X)
    v: np.ndarray        # vertical in-plane axis (follows +Y)

    @staticmethod
    def of(mesh: Mesh, rear=(0.0, 0.0, -1.0)) -> 'Frame':
        n = analysis.outward(mesh, rear)
        a = mesh.areas()
        centroid = (mesh.corners().mean(axis=1) * a[:, None]).sum(0) / max(a.sum(), 1e-12)
        x = np.array([1.0, 0.0, 0.0]) - n * n[0]
        if np.linalg.norm(x) < 1e-6:
            x = np.array([0.0, 0.0, 1.0]) - n * n[2]
        x /= np.linalg.norm(x)
        y = np.cross(n, x)
        if y[1] < 0:
            y = -y
        return Frame(centroid, n, x, y)

    def local(self, p):
        d = np.asarray(p) - self.origin
        return np.stack([d @ self.u, d @ self.v, d @ self.normal], axis=-1)

    def world(self, q):
        q = np.asarray(q)
        return self.origin + q[..., :1] * self.u + q[..., 1:2] * self.v + q[..., 2:3] * self.normal


def oriented_vertex_normals(mesh: Mesh, outward: np.ndarray) -> np.ndarray:
    fn = analysis.oriented_face_normals(mesh, outward) * mesh.areas()[:, None]
    out = np.zeros_like(mesh.positions)
    for k in range(3):
        np.add.at(out, mesh.triangles[:, k], fn)
    length = np.linalg.norm(out, axis=1, keepdims=True)
    out = np.where(length > 1e-12, out / np.maximum(length, 1e-12), outward)
    return out


# ---------------------------------------------------------------- sources

def boundary_loops(mesh: Mesh):
    """Ordered outline loops (vertex index lists) of a triangle patch; vertices welded by position."""
    key = {}
    weld = np.array([key.setdefault(tuple(np.round(p, 6)), len(key)) for p in mesh.positions])
    first = {}
    for i, w in enumerate(weld):
        first.setdefault(w, i)
    edges = {}
    for t in mesh.triangles:
        a, b, c = weld[t]
        for e in ((a, b), (b, c), (c, a)):
            k = tuple(sorted(e))
            edges.setdefault(k, []).append(e)
    nxt = {}
    for k, uses in edges.items():
        if len(uses) == 1:
            a, b = uses[0]
            nxt.setdefault(a, []).append(b)
    loops, seen = [], set()
    for start in list(nxt):
        if start in seen:
            continue
        loop, cur = [], start
        while cur not in seen and cur in nxt:
            seen.add(cur); loop.append(cur); cur = nxt[cur][0]
        if len(loop) >= 3:
            loops.append([first[w] for w in loop])
    return loops


def planar_uv(points, frame: Frame, lo=None, hi=None, mirror=False):
    q = frame.local(points)[:, :2]
    lo = q.min(0) if lo is None else lo
    hi = q.max(0) if hi is None else hi
    span = np.maximum(hi - lo, 1e-9)
    u = (q[:, 0] - lo[0]) / span[0]
    v = (hi[1] - q[:, 1]) / span[1]
    if mirror:
        u = 1 - u
    return np.stack([u, v], axis=1)


def from_glass(lens: Mesh, frame: Frame, halo_size: float):
    """Core = lens faces (planar 0..1 UV like the Blazer core); halo = ring grown from the outline."""
    mirror = frame.origin[0] < 0
    core = Layer(lens.positions.copy(), planar_uv(lens.positions, frame, mirror=mirror), lens.triangles.copy())
    q = frame.local(lens.positions)
    extent = float(np.ptp(q[:, :2], axis=0).max())
    width = BLAZER_HALO_WIDTH * extent * halo_size
    pos, tri = [], []
    for loop in boundary_loops(lens):
        n = len(loop)
        inner = q[loop, :2]
        # Orientation: positive signed area = counter-clockwise in (u, v).
        area = .5 * sum(inner[i, 0] * inner[(i + 1) % n, 1] - inner[(i + 1) % n, 0] * inner[i, 1] for i in range(n))
        sign = 1 if area > 0 else -1
        outward = []
        for i in range(n):
            ds = []
            for a, b in ((inner[i - 1], inner[i]), (inner[i], inner[(i + 1) % n])):
                e = b - a
                ln = np.linalg.norm(e)
                if ln > 1e-9:
                    ds.append(sign * np.array([e[1], -e[0]]) / ln)
            d = np.sum(ds, axis=0)
            d = d / max(np.linalg.norm(d), 1e-9)
            outward.append(d)
        base = len(pos)
        for i in range(n):
            pos.append(np.array([*inner[i], q[loop[i], 2]]))
        for i in range(n):
            pos.append(np.array([*(inner[i] + outward[i] * width), q[loop[i], 2]]))
        for i in range(n):
            j = (i + 1) % n
            a, b, c, d = base + i, base + j, base + n + j, base + n + i
            tri += [(a, b, c), (c, d, a)]
    if not pos:
        raise SpecError('lens selection has no outline for the halo')
    world = frame.world(np.array(pos))
    halo = Layer(world, planar_uv(world, frame, mirror=mirror), np.array(tri, dtype=np.int64))
    return core, halo


def donor_layers(kind: str, source: dict, side: str, donor_dx: bytes | None, ps2_loader=None):
    """(core, glow) Layers of a donor source in its own model space."""
    if kind == 'blazer':
        from master_rallye.dx import parse_dx_bytes
        from master_rallye.topology_writer import source_geometry
        from master_rallye.preview_scene import logical_cases
        from master_rallye.addon_sdk.native_effect_reference import _components
        m = parse_dx_bytes(donor_dx)
        geom = source_geometry(m)
        cases, _ = logical_cases(m)
        pick = {}
        for d in m.physical_draws:
            if cases.get(d.draw_index) == (1, 2) and d.texture_tuple[0] in (ON_CORE_TEXTURE, ON_GLOW_TEXTURE):
                parts = sorted(_components(geom[d.draw_index]), key=lambda g: sum(v.position[0] for v in g.vertices))
                if len(parts) != 2:
                    raise SpecError('Blazer donor must have two lamp components per layer')
                pick[d.texture_tuple[0]] = parts[0 if side == 'left' else 1]
        if set(pick) != {ON_CORE_TEXTURE, ON_GLOW_TEXTURE}:
            raise SpecError('Blazer donor ON core/halo not found')
        return Layer.from_geometry(pick[ON_CORE_TEXTURE]), Layer.from_geometry(pick[ON_GLOW_TEXTURE])
    if kind == 'custom':
        def layer(m):
            return Layer(np.array(m['positions'], float), np.array(m['uvs'], float), np.array(m['triangles'], dtype=np.int64).reshape(-1, 3))
        return layer(source['core']), layer(source['glow'])
    if kind == 'ps2':
        if ps2_loader is None:
            raise SpecError('ps2 source needs a PS2 mesh loader')
        return ps2_loader(source['asset'], source['core']), ps2_loader(source['asset'], source['glow'])
    raise SpecError(kind)


def place_donor(core: Layer, glow: Layer, lens: Mesh, frame: Frame, halo_size: float):
    """Map a donor layer pair onto the lens: donor frame -> lens frame, uniform scale fitting the lens extent."""
    dframe = Frame.of(core.mesh())
    dq = dframe.local(core.positions)
    lq = frame.local(lens.positions)
    dspan = np.ptp(dq[:, :2], axis=0)
    lspan = np.ptp(lq[:, :2], axis=0)
    scale = float(min(lspan / np.maximum(dspan, 1e-9)))
    if not .05 <= scale <= 4:
        raise SpecError(f'donor/lens scale {scale:.3f} outside 0.05..4')
    dcen = (dq[:, :2].min(0) + dq[:, :2].max(0)) / 2
    lcen = (lq[:, :2].min(0) + lq[:, :2].max(0)) / 2

    def move(layer):
        q = dframe.local(layer.positions)
        q[:, :2] = (q[:, :2] - dcen) * scale + lcen
        q[:, 2] = q[:, 2] * scale
        out = layer.copy(); out.positions = frame.world(q); out.normals = None
        return out
    c, g = move(core), move(glow)
    if halo_size != 1.0:
        # Each halo vertex keeps its direction from the nearest core vertex; the distance scales.
        for i, p in enumerate(g.positions):
            k = np.argmin(np.linalg.norm(c.positions - p, axis=1))
            g.positions[i] = c.positions[k] + halo_size * (p - c.positions[k])
    return c, g


def apply_transform(layers, frame: Frame, t: dict):
    """User transform about the lens centre in lens-frame axes (offset metres, rotation degrees, scale)."""
    R = rotation_matrix(t['rotation'])
    S = np.diag(t['scale'])
    M = np.stack([frame.u, frame.v, frame.normal], axis=1)  # lens frame -> world
    for layer in layers:
        q = (layer.positions - frame.origin) @ M
        q = (q @ S.T) @ R.T
        layer.positions = frame.origin + q @ M.T + np.asarray(t['offset']) + frame.normal * (t['normal_offset_mm'] / 1000)


def subdivide(layer: Layer, max_edge: float, limit=6) -> Layer:
    """Split triangles whose longest edge exceeds ``max_edge`` (midpoint split, UV interpolated)."""
    pos, uv, tri = [*layer.positions], [*layer.uvs], [tuple(t) for t in layer.triangles]
    for _ in range(limit):
        cache, out, changed = {}, [], False
        for t in tri:
            p = [pos[i] for i in t]
            e = [np.linalg.norm(p[(k + 1) % 3] - p[k]) for k in range(3)]
            k = int(np.argmax(e))
            if e[k] <= max_edge:
                out.append(t); continue
            a, b = t[k], t[(k + 1) % 3]; c = t[(k + 2) % 3]
            key = (min(a, b), max(a, b))
            if key not in cache:
                cache[key] = len(pos); pos.append((pos[a] + pos[b]) / 2); uv.append((uv[a] + uv[b]) / 2)
            m = cache[key]
            out += [(a, m, c), (m, b, c)]; changed = True
        tri = out
        if not changed:
            break
    return Layer(np.array(pos), np.array(uv), np.array(tri, dtype=np.int64))


def lift(points, normals, surface: Mesh, offset: float, *, snap=False, reach=0.5, spread=0.0, axes=None):
    """Move points onto/over ``surface`` along their normals.

    A ray is cast from ``p + n*reach`` back along ``-n``; the first hit is the outermost surface there. ``snap``
    places the point exactly ``offset`` above it; otherwise a point is only raised when it lies below that.
    ``spread`` (with in-plane ``axes`` (u, v)) also probes p +/- spread*u, p +/- spread*v and keeps the highest
    surface: an envelope, so a triangle between lifted vertices does not sag under a convex crease.
    Returns new points and a hit mask.
    """
    starts = points + normals * reach
    t = ray_hits(starts, -normals, surface)
    if spread > 0 and axes is not None:
        for a in axes:
            for sgn in (1, -1):
                tt = ray_hits(starts + sgn * spread * np.asarray(a), -normals, surface)
                t = np.fmin(t, tt)
    hit = np.isfinite(t)
    target = starts - normals * np.where(hit, t, 0)[:, None] + normals * offset
    height = ((points - target) * normals).sum(1)
    move = hit & (snap | (height < 0))
    return np.where(move[:, None], target, points), hit


def fit_layers(core: Layer, glow: Layer, lens: Mesh, occluders: Mesh, frame: Frame, fit: dict, offset: float, *, exact_core=False):
    """Place core/halo per fit mode. ``exact_core``: core vertices are the lens vertices (from_glass)."""
    mode = fit['mode']
    if mode == 'none':
        return core, glow
    ln = oriented_vertex_normals(lens, frame.normal)
    surface = merge([lens, occluders])
    if mode != 'plane':
        # An exact lens copy already follows the lens; only donor/ring layers need tessellation.
        if not exact_core:
            core = subdivide(core, fit['max_edge_m'])
        glow = subdivide(glow, fit.get('halo_max_edge_m', fit['max_edge_m']))
    core_before, glow_before = core.positions.copy(), glow.positions.copy()
    if mode == 'plane':
        top = float(frame.local(lens.positions)[:, 2].max())
        for layer in (core, glow):
            q = frame.local(layer.positions); q[:, 2] = top + offset
            layer.positions = frame.world(q)
    elif mode == 'project' or exact_core:
        n = np.tile(frame.normal, (len(core.positions), 1))
        if exact_core:
            # Lens copy: push each vertex along its smoothed lens normal (shared edges stay closed).
            _, tri, _ = closest_on_mesh(core.positions, lens)
            core.positions = core.positions + offset * smooth_normals_at(core.positions, lens, ln)
        else:
            core.positions, _ = lift(core.positions, n, lens, offset, snap=True)
    else:  # shrinkwrap
        closest, tri, _ = closest_on_mesh(core.positions, lens)
        core.positions = closest + offset * smooth_normals_at(closest, lens, ln)
    # Never leave any layer vertex under the lens or the body (seen along the lens normal).
    n = np.tile(frame.normal, (len(core.positions), 1))
    core.positions, _ = lift(core.positions, n, lens, offset)
    # The whole halo, inner ring included, rides the envelope of lens + body: in a recessed lamp it sits at the
    # housing rim, in front of the housing walls, like the floating retail Blazer halo.
    glow.positions = lift_halo(glow.positions, core.positions, frame, surface, offset,
                               step=fit['max_edge_m'] / 2, radius=fit.get('halo_max_edge_m', fit['max_edge_m']), triangles=glow.triangles,
                               core_triangles=core.triangles)
    core.normals = np.tile(frame.normal, (len(core.positions), 1)); glow.normals = np.tile(frame.normal, (len(glow.positions), 1))
    return core, glow


def weld_map(points, targets, tol=1e-6):
    """{point index: target index} for points coincident with a target point."""
    if not len(points) or not len(targets):
        return {}
    d = np.linalg.norm(points[:, None] - targets[None], axis=2)
    k = d.argmin(axis=1)
    return {i: int(k[i]) for i in range(len(points)) if d[i, k[i]] < tol}


def inside_2d(points, verts, triangles):
    """Points (N,2) inside any 2D triangle of (verts, triangles); all False without triangles."""
    out = np.zeros(len(points), dtype=bool)
    if triangles is None or not len(triangles):
        return out
    a, b, c = (verts[triangles[:, k]] for k in range(3))
    def cross(o, p, r):
        return (p[None, :, 0] - o[None, :, 0]) * (r[:, None, 1] - o[None, :, 1]) - (p[None, :, 1] - o[None, :, 1]) * (r[:, None, 0] - o[None, :, 0])
    P = points
    for at in range(0, len(P), 4096):
        pp = P[at:at + 4096]
        d1, d2, d3 = cross(a, b, pp), cross(b, c, pp), cross(c, a, pp)
        neg = (d1 < 0) | (d2 < 0) | (d3 < 0); pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
        out[at:at + 4096] = (~(neg & pos)).any(axis=1)
    return out


def lift_halo(points, core_points, frame: 'Frame', surface: Mesh, offset: float, *, step=0.01, radius=0.03,
              max_rise=0.012, reach=0.5, samples=48, triangles=None, smooth=4, core_triangles=None):
    """Lift halo vertices onto a smooth conservative envelope of ``surface`` (seen along the lens normal).

    Surface heights are probed on a ``step`` grid; the envelope at a point is the highest probe within
    ``radius``, so a triangle (edges <= radius) never sags under a crease between its vertices. Where the
    envelope climbs more than ``max_rise`` above the lens top (a bumper shelf, a panel seen edge-on, the
    silhouette), the halo is shortened radially from the lens centre - smoothly, so its outline stays soft.
    """
    n = frame.normal
    q = frame.local(points)
    top = float(frame.local(core_points)[:, 2].max())
    lo, hi = q[:, :2].min(0) - radius, q[:, :2].max(0) + radius
    gu = np.arange(lo[0], hi[0] + step, step); gv = np.arange(lo[1], hi[1] + step, step)
    G = np.array([(u, v) for u in gu for v in gv])
    t = ray_hits(frame.world(np.column_stack([G, np.full(len(G), top + reach)])), -n, surface)
    h = np.where(np.isfinite(t), top + reach - t, -np.inf)

    def envelope(P):
        d = np.linalg.norm(P[:, None, :] - G[None], axis=2)
        return np.where(d <= radius, h[None], -np.inf).max(axis=1)
    # Radial shortening: largest fraction of the centre->vertex segment whose envelope stays under the limit.
    c = frame.local(core_points)[:, :2].mean(0)
    frac = np.linspace(0, 1, samples + 1)[1:]
    path = c[None, None] + frac[None, :, None] * (q[:, None, :2] - c[None, None])
    env = envelope(path.reshape(-1, 2)).reshape(len(q), samples)
    # Points over the lens/core itself never shorten the halo (the core is fitted separately).
    inside = inside_2d(path.reshape(-1, 2), frame.local(core_points)[:, :2], core_triangles).reshape(len(q), samples)
    ok = (env <= top + max_rise) | inside
    # Where the centre->vertex line leaves the core: shortening never pulls a vertex inside the core outline.
    last_in = np.where(inside.any(axis=1), samples - 1 - np.argmax(inside[:, ::-1], axis=1), -1)
    floor = np.where(last_in >= 0, frac[np.maximum(last_in, 0)], 0.0)
    first_bad = np.where(ok.all(axis=1), samples, np.argmin(ok, axis=1))
    s = np.where(first_bad == samples, 1.0, np.concatenate([[0.0], frac])[first_bad])
    if triangles is not None and len(triangles) and smooth:
        # Neighbour minimum then averaging: never lengthens into a violation much, keeps the outline soft.
        nb = [set() for _ in range(len(q))]
        for a, b, cc in triangles:
            nb[a] |= {b, cc}; nb[b] |= {a, cc}; nb[cc] |= {a, b}
        nb = [sorted(x) for x in nb]
        s = np.array([min([s[i]] + [s[j] for j in nb[i]]) for i in range(len(q))])
        for _ in range(smooth):
            s = np.array([(s[i] + sum(s[j] for j in nb[i])) / (1 + len(nb[i])) for i in range(len(q))])
    s = np.maximum(s, floor)
    q[:, :2] = c + s[:, None] * (q[:, :2] - c)
    need = envelope(q[:, :2]) + offset
    q[:, 2] = np.maximum(q[:, 2], np.where(np.isfinite(need), need, q[:, 2]))
    return frame.world(q)


def smooth_normals_at(points, lens: Mesh, vertex_normals):
    """Interpolated (barycentric) smoothed lens normal at points on or near the lens."""
    closest, tri, _ = closest_on_mesh(points, lens)
    c = lens.corners()[tri]
    v0, v1, v2 = c[:, 0], c[:, 1], c[:, 2]
    e0, e1, e2 = v1 - v0, v2 - v0, closest - v0
    d00, d01, d11 = (e0 * e0).sum(1), (e0 * e1).sum(1), (e1 * e1).sum(1)
    d20, d21 = (e2 * e0).sum(1), (e2 * e1).sum(1)
    den = np.where(np.abs(d00 * d11 - d01 * d01) > 1e-18, d00 * d11 - d01 * d01, 1)
    b1 = (d11 * d20 - d01 * d21) / den
    b2 = (d00 * d21 - d01 * d20) / den
    b0 = 1 - b1 - b2
    idx = lens.triangles[tri]
    n = b0[:, None] * vertex_normals[idx[:, 0]] + b1[:, None] * vertex_normals[idx[:, 1]] + b2[:, None] * vertex_normals[idx[:, 2]]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def mirror_layer(layer: Layer) -> Layer:
    out = layer.copy()
    out.positions[:, 0] *= -1
    out.triangles = out.triangles[:, [0, 2, 1]]
    if out.normals is not None:
        out.normals[:, 0] *= -1
    return out


# ---------------------------------------------------------------- per-car authoring

@dataclass
class FittedLamp:
    id: str
    body: str
    core: Layer
    glow: Layer
    lens: Mesh
    frame: Frame
    offset_mm: float
    checks: dict = field(default_factory=dict)


def lens_mesh(car_geometry, draw_faces):
    """Mesh of the lens faces. ``draw_faces``: list of (draw index, triangle indices)."""
    pos, tri = [], []
    for index, ids in draw_faces:
        g = car_geometry[index]
        for t in ids:
            base = len(pos)
            pos += [g.vertices[i].position for i in g.triangles[t]]
            tri.append((base, base + 1, base + 2))
    # Weld duplicates so outlines/normals are shared.
    key, out, remap = {}, [], []
    for p in pos:
        k = tuple(np.round(p, 7))
        if k not in key:
            key[k] = len(out); out.append(p)
        remap.append(key[k])
    tri = [tuple(remap[i] for i in t) for t in tri]
    return Mesh.of(out, tri)


def resolve_faces(model, geometry, cases, lamp):
    """[(draw index, [triangle indices])] for the lens face IDs of one lamp."""
    want = set(lamp['lens']['faces'])
    if lamp['lens']['draw'] == 'blight':
        draws = [d for d in model.physical_draws if cases.get(d.draw_index) and cases[d.draw_index] == (1, 1)]
    elif lamp['lens']['draw'] == 'any':
        draws = [d for d in model.physical_draws if cases.get(d.draw_index) is None or cases[d.draw_index][1] == 1]
    else:
        draws = [d for d in model.physical_draws if d.draw_index == lamp['lens']['draw']]
    found = []
    seen = set()
    for d in draws:
        g = geometry[d.draw_index]
        ids = face_ids([v.position for v in g.vertices], g.triangles)
        hit = [i for i, f in enumerate(ids) if f in want]
        seen |= {ids[i] for i in hit}
        if hit:
            found.append((d.draw_index, hit))
    missing = want - seen
    if missing:
        raise SpecError(f'lamp {lamp["id"]}: {len(missing)} lens face IDs not found in the model (re-pick the lens)')
    return found


def fit_lamp(lamp, lens: Mesh, occluders: Mesh, *, donor_dx=None, ps2_loader=None, views=None):
    frame = Frame.of(lens)
    src = lamp['source']
    halo = float(lamp['halo']['size'])
    if src['kind'] == 'from_glass':
        core, glow = from_glass(lens, frame, halo)
    else:
        side = src.get('side') or ('left' if frame.origin[0] < 0 else 'right')
        core, glow = donor_layers(src['kind'], src, side, donor_dx, ps2_loader)
        if lamp['fit']['mode'] != 'none':
            core, glow = place_donor(core, glow, lens, frame, halo)
    apply_transform((core, glow), frame, lamp['transform'])
    offset = float(lamp['fit']['offset_mm']) if lamp['fit']['mode'] != 'none' else 0.0
    base = (core.copy(), glow.copy())
    while True:
        c, g = fit_layers(base[0].copy(), base[1].copy(), lens, occluders, frame, lamp['fit'], offset / 1000,
                          exact_core=src['kind'] == 'from_glass' and lamp['transform']['scale'] == [1.0, 1.0, 1.0] and lamp['transform']['rotation'] == [0.0, 0.0, 0.0])
        checks = check_layers(c, g, lens, occluders, frame, views=views)
        if checks['buried'] == 0 or offset + .5 > float(lamp['fit']['max_offset_mm']) + 1e-9 or lamp['fit']['mode'] == 'none':
            break
        offset += .5
    if lamp['fit']['mode'] == 'none' and lamp['body'] == 'PS2':
        # Original PS2 geometry sits on the PS2 body, which is not part of car.dx: checks against the PC body
        # occluders say nothing about it.
        checks['evaluated'] = False
        checks['buried'] = 0
    return FittedLamp(lamp['id'], lamp['body'], c, g, lens, frame, offset, checks)


def check_layers(core: Layer, glow: Layer, lens: Mesh, occluders: Mesh, frame: Frame, *, views=None):
    """Visibility of each layer from the lens normal (``normal``) and the 8 standard rear views.

    The lens itself is the baseline: a layer is *buried* when, seen along the lens normal, more of it is hidden
    than of the OFF lens it covers (a bezel that hides part of the lens hides the lit lamp equally).
    """
    from .geometry import view_directions
    views = dict(views or view_directions())
    views['normal'] = frame.normal
    base, _ = analysis.layer_visibility(lens, occluders, views={'normal': frame.normal})
    baseline = base['normal']['hidden_fraction']
    out = {'buried': 0, 'lens_normal_hidden': baseline}
    for name, layer in (('core', core), ('halo', glow)):
        vis, raw = analysis.layer_visibility(layer.mesh(), occluders, views=views)
        entry = {'views': vis, 'normal_hidden': vis['normal']['hidden_fraction'], 'rear_hidden': vis['rear']['hidden_fraction'],
                 'max_buried_mm': round(float(raw['rear_depth'].max()) * 1000, 2), '_raw': raw}
        if name == 'core':
            fn = analysis.oriented_face_normals(lens, frame.normal)
            closest, tri, _ = closest_on_mesh(layer.positions, lens)
            s = ((layer.positions - closest) * fn[tri]).sum(1)
            entry['lens_offset_mm'] = {'min': round(float(s.min()) * 1000, 2), 'max': round(float(s.max()) * 1000, 2)}
        out[name] = entry
        if vis['normal']['hidden_fraction'] > baseline + .01:
            out['buried'] += 1
    return out


def tinted_glow(dxt: bytes, color, brightness) -> bytes:
    """Per-car PC halo texture with an RGB tint and brightness multiplier (BrakeGlow=0 only)."""
    if list(color) == [255, 255, 255] and float(brightness) == 1.0:
        return dxt
    from master_rallye.dxt import parse_dxt_bytes, decode_rgba_pixels, replace_dxt_pixels
    t = parse_dxt_bytes(dxt)
    rgba = bytearray(decode_rgba_pixels(t))
    for i in range(0, len(rgba), 4):
        for k in range(3):
            rgba[i + k] = min(255, int(round(rgba[i + k] * color[k] / 255 * brightness)))
    return replace_dxt_pixels(dxt, bytes(rgba))
