"""DAMAGE2 audit: where do unresolved PS2 CAR vertices lie relative to the PC body surface?

Read-only. For every fleet family with unresolved private-damage vertices
(car/contracts.json), measure each unresolved PS2 asset vertex's distance to the
nearest healthy PC source triangle (all pinned pc_sources of that family) and
record that triangle. Vertices lying on a PC triangle are moved exactly by the
PC game's per-vertex damage displacement through their barycentric weights;
off-surface vertices are genuine authored differences.

  python surface_audit.py [Family ...]   -> surface-audit.json
"""
from pathlib import Path
import collections, hashlib, json, math, struct, sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
ROOT = PORT.parents[1]
sys.path.insert(0, str(ROOT / "src"))
BANDS = (1e-5, 1e-4, 1e-3, 5e-3, 2e-2, 5e-2)


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def closest_on_triangle(p, a, b, c):
    """Ericson, Real-Time Collision Detection 5.1.5; returns (distance, (u, v, w))."""
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0: w = (1.0, 0.0, 0.0)
    else:
        bp = sub(p, b); d3, d4 = dot(ab, bp), dot(ac, bp)
        cp = sub(p, c); d5, d6 = dot(ab, cp), dot(ac, cp)
        vc, vb, va = d1 * d4 - d3 * d2, d5 * d2 - d1 * d6, d3 * d6 - d5 * d4
        if d3 >= 0 and d4 <= d3: w = (0.0, 1.0, 0.0)
        elif d6 >= 0 and d5 <= d6: w = (0.0, 0.0, 1.0)
        elif vc <= 0 and d1 >= 0 and d3 <= 0: t = d1 / (d1 - d3); w = (1 - t, t, 0.0)
        elif vb <= 0 and d2 >= 0 and d6 <= 0: t = d2 / (d2 - d6); w = (1 - t, 0.0, t)
        elif va <= 0 and d4 - d3 >= 0 and d5 - d6 >= 0:
            t = (d4 - d3) / ((d4 - d3) + (d5 - d6)); w = (0.0, 1 - t, t)
        else:
            denom = 1.0 / (va + vb + vc); v, x = vb * denom, vc * denom; w = (1 - v - x, v, x)
    q = tuple(w[0] * a[j] + w[1] * b[j] + w[2] * c[j] for j in range(3))
    return math.dist(p, q), w


def asset_positions(blob):
    _, version, meta, meshes, vertices, indices, textures, _ = struct.unpack_from("<8s6I32s", blob)
    at = 64 + meta
    rows = [struct.unpack_from("<7I", blob, at + i * 28) for i in range(meshes)]; at += meshes * 28
    pos = [struct.unpack_from("<3f", blob, at + i * 36) for i in range(vertices)]; at += vertices * 36
    ids = struct.unpack_from("<" + "I" * indices, blob, at)
    return rows, pos, ids


def audit(profile, contract):
    from master_rallye.dx import parse_dx
    pcpath = ROOT.parent / "corpora/retail/Data.sma_unpacked/DataGx/Vehicles" / profile["family"] / "car.dx"
    blob = (PORT / ".assets/vehicles" / profile["filename"]).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == profile["sha256"]
    assert hashlib.sha256(pcpath.read_bytes()).hexdigest() == profile["original_pc_source_sha256"]
    pc = parse_dx(pcpath); bypath = {d.record_path: d for d in pc.physical_draws}
    tris = []
    for slot, s in enumerate(profile["pc_sources"]):
        d = bypath[s["record_path"]]
        pts = pc.vertices.positions[d.vertex_base:d.vertex_base + s["vertices"]]
        ids = [i - d.vertex_base for i in pc.draw_global_indices(d)]
        for k in range(0, len(ids), 3):
            a, b, c = pts[ids[k]], pts[ids[k + 1]], pts[ids[k + 2]]
            n = (lambda u, v: (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]))(sub(b, a), sub(c, a))
            if dot(n, n) <= 1e-24: continue  # degenerate triangles carry no surface
            tris.append((slot, ids[k], ids[k + 1], ids[k + 2], a, b, c))
    cell = 0.25
    grid = collections.defaultdict(list)
    for t, (_, _, _, _, a, b, c) in enumerate(tris):
        lo = [math.floor(min(a[j], b[j], c[j]) / cell) for j in range(3)]
        hi = [math.floor(max(a[j], b[j], c[j]) / cell) for j in range(3)]
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                for z in range(lo[2], hi[2] + 1): grid[(x, y, z)].append(t)
    rows, pos, ids = asset_positions(blob)
    mesh_of = {}
    for m, r in enumerate(rows):
        for v in ids[r[5]:r[5] + r[6]]: mesh_of.setdefault(v, m)
    bands = collections.Counter(); per_mesh = collections.defaultdict(collections.Counter); worst = []
    for v in contract["unresolved_vertices"]:
        p = pos[v]; c0 = [math.floor(p[j] / cell) for j in range(3)]; best = (math.inf, None, None)
        for radius in (1, 2, 4, 8):
            seen = set()
            for x in range(c0[0] - radius, c0[0] + radius + 1):
                for y in range(c0[1] - radius, c0[1] + radius + 1):
                    for z in range(c0[2] - radius, c0[2] + radius + 1):
                        for t in grid.get((x, y, z), ()):
                            if t in seen: continue
                            seen.add(t); dist, w = closest_on_triangle(p, *tris[t][4:])
                            if dist < best[0]: best = (dist, t, w)
            if best[0] <= radius * cell: break
        band = next((f"<={b:g}" for b in BANDS if best[0] <= b), ">0.05")
        bands[band] += 1; per_mesh[mesh_of.get(v, -1)][band] += 1
        worst.append((best[0], v))
    worst.sort(reverse=True)
    xs = [p[0] for p in pos]; ys = [p[1] for p in pos]; zs = [p[2] for p in pos]
    return {"family": profile["family"], "unresolved": len(contract["unresolved_vertices"]),
            "asset_extent": [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)],
            "distance_bands": dict(bands),
            "by_mesh": {str(m): dict(c) for m, c in sorted(per_mesh.items())},
            "worst": [{"vertex": v, "distance": d} for d, v in worst[:5]]}


def main():
    profiles = {p["family"]: p for p in json.loads((PORT / "docs/vehicle-continuity2/fleet-car/race-profiles.json").read_text())["profiles"]}
    contracts = {p["family"]: p for p in json.loads((HERE.parent / "car/contracts.json").read_text())["profiles"]}
    wanted = sys.argv[1:] or [f for f, c in contracts.items() if c["unresolved_vertices"]]
    results = []
    for family in wanted:
        r = audit(profiles[family], contracts[family]); results.append(r)
        print(json.dumps({k: r[k] for k in ("family", "unresolved", "distance_bands")}), flush=True)
    out = HERE / "surface-audit.json"
    previous = json.loads(out.read_text()) if out.exists() else {"schema": 1, "families": {}}
    for r in results: previous["families"][r["family"]] = r
    out.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
