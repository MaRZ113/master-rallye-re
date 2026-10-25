"""V-MESH4.1: content-driven classification of a GT3 body LOD (LOD0 as primary source) - no LOD-specific names.

GT3 material/texture indices (``MatN_TexM``) are numbered per LOD, so ``Mat6_Tex10`` in LOD1 and ``Mat6_Tex37`` in
LOD0 are the same window pane.  The classifier therefore decides from what the data *is*:

* object names written by the GT3 dumper that are structural, not per-car: ``*reflection*`` (env-map shell),
  ``*_tail_lamp_on`` (lit duplicate), ``*tail_lamp_off`` (the lamp body);
* GT material class prefix (``Mat-1`` shell, ``Mat1`` paint, ``Mat6`` trim, ``Mat4`` glass, ``Mat2`` lit lamp);
* measured texture content: alpha plane statistics and mean luminance;
* measured geometry: front-corner objects (single side, inside the front 15 % of the body length).

It also provides the *support test* that separates decal overlays (mostly-transparent textures lying on another
surface, dropped) from mostly-transparent materials that are the only surface there (kept, e.g. the LOD0 bonnet).
No GT data is stored here.
"""
from __future__ import annotations

import collections
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from master_rallye.texture_authoring import decode_rgba_png  # noqa: E402
from vmesh_geometry import ALPHA_OPAQUE, AlphaTexture, find_glazing_materials  # noqa: E402

FRONT_FRACTION = 0.15          # lamp objects must lie within this fraction of the body length from the front end
LAMP_X_ABS = (0.25, 1.0)       # GT-frame |x| band of a front-corner lamp object


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


class Lod0Classifier:
    """Callable ``(obj, material) -> role`` plus a record of why each (object, material) went where it did."""

    def __init__(self, faces, textures: dict):
        self.textures = textures
        self.tex_cache: dict[str, AlphaTexture] = {}
        self.glazing = find_glazing_materials(faces, textures)
        body = [c[0] for o, m, t in faces if not self._structural_exclude(o) for c in t]
        self.z_front = min(p[2] for p in body)         # GT front is -Z
        self.length = max(p[2] for p in body) - self.z_front
        self.lamp_objects = self._find_lamp_objects(faces)
        self.reasons: dict[tuple, str] = {}

    # ---------------------------------------------------------------- structure
    @staticmethod
    def _structural_exclude(obj: str) -> bool:
        return "reflection" in obj or "_tail_lamp_on" in obj

    def texture(self, material: str):
        if material not in self.textures:
            return None
        if material not in self.tex_cache:
            self.tex_cache[material] = AlphaTexture(self.textures[material].read_bytes())
        return self.tex_cache[material]

    def _find_lamp_objects(self, faces) -> set:
        """Objects entirely inside a front corner on one side only (the pair of head-lamp units)."""
        per = collections.defaultdict(list)
        for o, m, t in faces:
            if not self._structural_exclude(o):
                per[o] += [c[0] for c in t]
        out = set()
        for o, pts in per.items():
            xs = [p[0] for p in pts]
            if (min(p[2] for p in pts) < self.z_front - 1e-6 or max(p[2] for p in pts) > self.z_front + FRONT_FRACTION * self.length
                    or not (min(xs) * max(xs) > 0) or not (LAMP_X_ABS[0] <= min(abs(x) for x in xs) and max(abs(x) for x in xs) <= LAMP_X_ABS[1])):
                continue
            out.add(o)
        return out if len(out) >= 2 else set()

    # ------------------------------------------------------------------- roles
    def __call__(self, obj: str, material: str) -> str:
        role, why = self._decide(obj, material)
        self.reasons[(obj, material)] = why
        return role

    def _decide(self, obj: str, material: str):
        if "reflection" in obj:
            return "exclude", "env-map reflection shell (object name)"
        if "_tail_lamp_on" in obj:
            return "exclude", "lit tail-lamp duplicate (object name)"
        tex = self.texture(material)
        if material.startswith("Mat-1"):
            if tex is None:
                return "exclude", "untextured Mat-1 duplicate shell"
            return "interior", "textured Mat-1 cabin shell"
        if "tail_lamp_off" in obj:
            return "tail_lamp", "tail-lamp body (object name)"
        if material in self.glazing:
            return "glass", "translucent dark Mat6 pane (texture alpha/luminance)"
        if obj in self.lamp_objects and material.startswith("Mat6") and tex is not None and 0.01 < tex.transparent_fraction < 0.95:
            return "head_lamp", "cut-out lens material of a front-corner lamp object"
        if material.startswith("Mat4"):
            return ("black", "Mat4 strip next to translucent panes (seal/overlay)") if self.glazing else ("glass", "Mat4 glass class")
        if material.startswith("Mat6"):
            return "black", "Mat6 trim"
        return "paint", "paint class (Mat1/other)"

    # ------------------------------------------------------------------ report
    def describe(self, faces) -> list[dict]:
        """Per (object, material): role, reason, triangle count, area, texture statistics."""
        rows = collections.OrderedDict()
        for o, m, t in faces:
            r = rows.setdefault((o, m), {"object": o, "material": m, "triangles": 0, "area_m2": 0.0})
            r["triangles"] += 1
            a, b, c = (p[0] for p in t)
            n = _cross(_sub(b, a), _sub(c, a))
            r["area_m2"] += 0.5 * math.sqrt(_dot(n, n))
        out = []
        for (o, m), r in rows.items():
            role, why = self._decide(o, m)
            tex = self.texture(m)
            w, h = ((tex.w, tex.h) if tex else (0, 0))
            out.append({**r, "area_m2": round(r["area_m2"], 4), "role": role, "reason": why,
                        "texture": None if tex is None else {"size": [w, h], "alpha_policy": tex.policy,
                                                             "transparent_fraction": round(tex.transparent_fraction, 3)}})
        return out


class SupportIndex:
    """Which triangles of a mostly-transparent overlay lie on another (solid) surface.

    ``solid`` is a list of GT-position triangles.  A triangle counts as supported when its centroid projects inside a
    solid triangle within ``tol`` metres along that triangle's normal.
    """

    CELL = 0.1

    def __init__(self, solid, tol: float = 0.03):
        self.solid, self.tol = solid, tol
        self.grid = collections.defaultdict(list)
        for i, t in enumerate(solid):
            lo = [min(p[k] for p in t) for k in range(3)]
            hi = [max(p[k] for p in t) for k in range(3)]
            for ix in range(math.floor(lo[0] / self.CELL), math.floor(hi[0] / self.CELL) + 1):
                for iy in range(math.floor(lo[1] / self.CELL), math.floor(hi[1] / self.CELL) + 1):
                    for iz in range(math.floor(lo[2] / self.CELL), math.floor(hi[2] / self.CELL) + 1):
                        self.grid[(ix, iy, iz)].append(i)

    def supported(self, tri_positions) -> bool:
        c = tuple(sum(p[k] for p in tri_positions) / 3 for k in range(3))
        for i in self.grid.get(tuple(math.floor(x / self.CELL) for x in c), ()):
            s = self.solid[i]
            n = _cross(_sub(s[1], s[0]), _sub(s[2], s[0]))
            ln = math.sqrt(_dot(n, n))
            if ln < 1e-12:
                continue
            n = tuple(x / ln for x in n)
            d = _dot(_sub(c, s[0]), n)
            if abs(d) > self.tol:
                continue
            q = tuple(c[k] - d * n[k] for k in range(3))
            v0, v1, v2 = _sub(s[1], s[0]), _sub(s[2], s[0]), _sub(q, s[0])
            d00, d01, d11, d20, d21 = _dot(v0, v0), _dot(v0, v1), _dot(v1, v1), _dot(v2, v0), _dot(v2, v1)
            den = d00 * d11 - d01 * d01
            if abs(den) < 1e-18:
                continue
            b = (d11 * d20 - d01 * d21) / den
            cc = (d00 * d21 - d01 * d20) / den
            if b >= -0.05 and cc >= -0.05 and b + cc <= 1.05:
                return True
        return False


def make_overlay_keep(faces, classifier: Lod0Classifier):
    """Return ``keep(tri)``: True when an overlay triangle is the only surface there (must not be dropped)."""
    solid = []
    for o, m, t in faces:
        role = classifier._decide(o, m)[0]
        if role in ("exclude", "interior"):          # support must be a visible body surface
            continue
        tex = classifier.texture(m)
        if tex is not None and tex.policy == "drop":
            continue
        solid.append(tuple(c[0] for c in t))
    index = SupportIndex(solid)

    def keep(tri) -> bool:
        return not index.supported(tuple(c[0] for c in tri))
    keep.index = index
    return keep


# --------------------------------------------------------------------------- source identity (material importer input)
def source_materials_table(faces, textures: dict, classifier: Lod0Classifier) -> list[dict]:
    """Per GT material: texture file, size, hash, alpha statistics and the donor role(s) it was mapped to.

    This is the identity record the later material importer needs; the first game candidate does not use it.
    """
    import hashlib
    roles = collections.defaultdict(collections.Counter)
    tris = collections.Counter()
    for o, m, t in faces:
        roles[m][classifier._decide(o, m)[0]] += 1
        tris[m] += 1
    out = []
    for m in sorted(tris):
        p = textures.get(m)
        tex = classifier.texture(m)
        out.append({"material": m, "triangles": tris[m], "roles": dict(roles[m]),
                    "texture_file": None if p is None else Path(p).name,
                    "texture_sha256": None if p is None else hashlib.sha256(Path(p).read_bytes()).hexdigest(),
                    "texture_size": None if tex is None else [tex.w, tex.h],
                    "alpha_policy": None if tex is None else tex.policy,
                    "transparent_fraction": None if tex is None else round(tex.transparent_fraction, 4),
                    "alpha_min": None if tex is None else min(tex.alpha), "alpha_mean": None if tex is None else round(sum(tex.alpha) / len(tex.alpha), 1)})
    return out


def verify_source_map(dx_bytes: bytes, smap: list, faces, tp, skip_roles=("interior",), tol: float = 2e-4) -> dict:
    """Check that every source-map record still points at the same triangle after ``rebuild_topology``.

    Compares the DX draw triangle ``tri`` of ``draw`` against the transformed source face corners (positions in the
    target frame).  Roles in ``skip_roles`` (the cabin shell is shrunk after transformation) are only range-checked.
    """
    from master_rallye.dx import parse_dx_bytes
    from vmesh_diagnose import draw_triangles
    model = parse_dx_bytes(dx_bytes)
    cache, ok, bad, skipped, no_uv = {}, 0, [], 0, 0
    for e in smap:
        tris = cache.setdefault(e["draw"], draw_triangles(model, e["draw"]))
        if e["tri"] >= len(tris):
            bad.append(e)
            continue
        if any(c["uv"] is None for c in e["corners"]):
            no_uv += 1
        if e["role"] in skip_roles or e.get("source_role") in skip_roles:
            skipped += 1
            continue
        want = [tp(faces[e["face"]][2][i][0]) for i in range(3)]
        got = tris[e["tri"]]
        if all(math.dist(a, b) <= tol for a, b in zip(want, got)):
            ok += 1
        else:
            bad.append(e)
    return {"records": len(smap), "verified_exact": ok, "range_checked_only": skipped, "mismatches": len(bad),
            "records_without_uv": no_uv, "first_mismatch": bad[0] if bad else None}
