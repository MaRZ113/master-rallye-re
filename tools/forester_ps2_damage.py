"""ForesterSTI PS2 race body deformation: bind the PS2 chassis to the PC (Demo) surface through the body scale.

Owner test 2026-11-12 (renderer a92a055a): the damaged PS2 Forester opened holes instead of denting. The PORT3
generator (docs/vehicle-fleet-port3/car/prepare_contracts.py, run by tools/ps2_fleet_damage_new.py) binds a PS2-only
component to the nearest healthy PC triangle only when every vertex is within 5 cm, otherwise the whole component is
rigid. The PC (Demo) Forester is the PS2 body rescaled per axis (fix 05: about x1.048 y1.031 z1.020), so the rear and
the large side/roof components sit 5-6 cm inside the PC surface: 1596 vertices (root.4 body 621+298+182, rear lamp
and bumper pieces) stayed rigid next to panels that followed the PC damage, and the seams opened.

This tool keeps the generator's rules (same surface index, same 5 cm limit, PS2-only components wholly transferred or
wholly rigid, Kia-verified static crew templates untouched) and changes only the query point: the PS2 vertex is first
mapped into PC body space with a per-axis scale fitted by iterative closest point over the whole chassis. The runtime
delta (wa*d(a)+wb*d(b)+wc*d(c)) is unchanged. `--apply` rewrites FORESTER_static, FORESTER_transfers and the FORESTER
profile row of renderer/fleet_damage_registry.hpp.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, struct, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PORT = BASE / "ps2-research/pc-port"
GEN = PORT / "docs/vehicle-fleet-port3/car/prepare_contracts.py"
REGISTRY = PORT / "renderer/fleet_damage_registry.hpp"
REPORT = BASE / ".research-output/roster-v4/fleet/race-profiles.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("port3_contracts", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(sdk: Path):
    g = load_generator()
    sys.path.insert(0, str(sdk.resolve() / "src"))
    from master_rallye.dx import parse_dx
    report = json.loads(REPORT.read_text())
    fam = next(f for f in report["families"] if f["profile"]["family"] == "ForesterSTI")
    p, pcpath = fam["profile"], BASE / fam["pc_car"]
    blob = (PORT / ".assets/vehicles" / p["filename"]).read_bytes()
    assert g.digest(blob) == p["sha256"] and g.digest(pcpath.read_bytes()) == p["original_pc_source_sha256"]
    # Kia-verified static crew templates (same rule as the generator).
    old = json.loads((PORT / "docs/vehicle-continuity2/fleet-car/race-profiles.json").read_text())["profiles"]
    kia = next(q for q in old if q["family"] == "KiaSportage")
    kr, kv, ki = g.asset_data((PORT / ".assets/vehicles" / kia["filename"]).read_bytes())
    templates = {g.component_signature(kv, f) for m in (17, 18, 19) for f in g.components(kv, ki[kr[m][5]:kr[m][5] + kr[m][6]])}
    # Healthy PC chassis sources, pinned by the profile certificate.
    pc = parse_dx(pcpath); bypath = {d.record_path: d for d in pc.physical_draws}; originals = []; slot_tris = []
    for s in p["pc_sources"]:
        d = bypath[s["record_path"]]; pts = pc.vertices.positions[d.vertex_base:d.vertex_base + s["vertices"]]
        assert g.digest(b"".join(struct.pack("<3f", *v) for v in pts)) == s["ordered_position_sha256"]
        originals.append(pts); ids = [i - d.vertex_base for i in pc.draw_global_indices(d)]
        slot_tris.append([tuple(ids[k:k + 3]) for k in range(0, len(ids), 3)])
    surface = g.SurfaceIndex(slot_tris, originals)
    rows, raw, ids = g.asset_data(blob)
    meta = json.loads(blob[64:64 + struct.unpack_from("<8s6I32s", blob)[2]])
    positions = [struct.unpack_from("<3f", r) for r in raw]
    exact = {tuple(round(x / 1e-5) for x in v) for o in originals for v in o}
    static, comps = set(), []
    for mesh, r in enumerate(rows):
        for faces in g.components(raw, ids[r[5]:r[5] + r[6]]):
            verts = sorted({i for t in faces for i in t})
            assert not any(tuple(round(x / 1e-5) for x in positions[v]) in exact for v in verts)  # PS2-only body
            if g.component_signature(raw, faces) in templates: static.update(verts)
            else: comps.append((mesh, verts))
    body = sorted({v for _, vs in comps for v in vs} - static)
    # Per-axis body scale, iterative closest point (no translation, like the fix 05 lamp fit).
    scale = [1.0, 1.0, 1.0]
    for it in range(8):
        pairs = []
        for v in body:
            q = tuple(positions[v][k] * scale[k] for k in range(3)); d, slot, a, b, c, w = surface.nearest(q)
            if it == 0 or d <= 0.02:
                A, B, C = originals[slot][a], originals[slot][b], originals[slot][c]
                pairs.append((positions[v], tuple(w[0] * A[k] + w[1] * B[k] + w[2] * C[k] for k in range(3))))
        scale = [sum(a[k] * b[k] for a, b in pairs) / sum(a[k] * a[k] for a, _ in pairs) for k in range(3)]
    transfer, rigid, rigid_report = {}, set(), []
    for mesh, verts in comps:
        todo = [v for v in verts if v not in static]
        if not todo: continue
        near = {v: surface.nearest(tuple(positions[v][k] * scale[k] for k in range(3))) for v in todo}
        if all(near[v][0] <= g.TRANSFER_LIMIT for v in todo): transfer.update(near)
        else:
            rigid.update(todo)
            rigid_report.append(dict(mesh=meta["meshes"][mesh]["path"], vertices=len(todo), max_distance=max(n[0] for n in near.values()),
                                     center=[sum(positions[v][k] for v in todo) / len(todo) for k in range(3)]))
    referenced = set(ids)
    assert referenced <= static | rigid | set(transfer)
    evidence = dict(asset_sha256=p["sha256"], pc_source_sha256=p["original_pc_source_sha256"], body_scale=scale,
                    referenced=len(referenced), static_template=len(static), transfer=len(transfer), rigid=len(rigid),
                    max_transfer_distance=max(t[0] for t in transfer.values()), transfer_limit=g.TRANSFER_LIMIT,
                    rigid_components=rigid_report)
    return transfer, sorted(static | rigid), evidence


def apply(transfer, static):
    text = REGISTRY.read_text()
    st = "inline constexpr uint32_t FORESTER_static[]={" + ",".join(f"{v}u" for v in static) + "};"
    tr = "inline constexpr Transfer FORESTER_transfers[]={" + ",".join(
        "{%du,%du,%du,%du,%du,%sf,%sf,%sf}" % (v, t[1], t[2], t[3], t[4], repr(float(t[5][0])), repr(float(t[5][1])), repr(float(t[5][2])))
        for v, t in sorted(transfer.items())) + "};"
    mx = max(t[0] for t in transfer.values())
    row = '{"ForesterSTI","FORESTER",3306u,14u,FORESTER_candidates,0u,FORESTER_mapping,3306u,FORESTER_static,%du,true,FORESTER_transfers,%du,%sf},' % (len(static), len(transfer), repr(float(mx)))
    for pattern, new in ((r"^inline constexpr uint32_t FORESTER_static\[\]=\{.*\};$", st),
                         (r"^inline constexpr Transfer FORESTER_transfers\[\]=\{.*\};$", tr),
                         (r'^\{"ForesterSTI","FORESTER",.*\},$', row)):
        text, n = re.subn(pattern, lambda _m: new, text, flags=re.M)
        if n != 1: raise ValueError("registry layout changed: " + pattern[:40])
    REGISTRY.write_text(text)
    return hashlib.sha256(REGISTRY.read_bytes()).hexdigest()


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--sdk", type=Path, required=True); a.add_argument("--evidence", type=Path); a.add_argument("--apply", action="store_true")
    o = a.parse_args()
    transfer, static, ev = build(o.sdk)
    print(json.dumps({k: v for k, v in ev.items() if k != "rigid_components"}, indent=1))
    for r in ev["rigid_components"]: print("rigid", r["mesh"], r["vertices"], round(r["max_distance"], 3), [round(x, 2) for x in r["center"]])
    if o.evidence: o.evidence.parent.mkdir(parents=True, exist_ok=True); o.evidence.write_text(json.dumps(ev, indent=1))
    if o.apply: print("registry", apply(transfer, static))
