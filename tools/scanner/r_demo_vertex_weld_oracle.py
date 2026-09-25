"""Read-only, bounded 9.3.1 Trooper post-weld hull oracle (R-DEMO2.5)."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.gxm import (parse_gxm_prefix_bytes, parse_gxm_geometry_prefix_bytes,
                               parse_gxm_triangle_prefix_bytes)
from master_rallye.gxm_hierarchy import parse_gxm_hierarchy_tail, walk_depth_first
from master_rallye.vertex_welder import (f32, loader_positions, isolation_proof,
                                         emit_triangles, compare_streams, early_hull_probe, _face)

BASELINE = "5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642"
EXE = "931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680"


def read_model(path):
    data = path.read_bytes()
    prefix = parse_gxm_prefix_bytes(data, str(path))
    geom = parse_gxm_geometry_prefix_bytes(data, prefix)
    tri = parse_gxm_triangle_prefix_bytes(data, prefix, geom)
    tree = parse_gxm_hierarchy_tail(data, tri.hierarchy_offset)
    nodes = tuple(walk_depth_first(tree.roots))
    hulls = [n for n in nodes if "$chull" in n.name]
    if len(hulls) != 1 or hulls[0].children or hulls[0] not in tree.roots:
        raise ValueError("only one root-level leaf hull supported")
    if prefix.header_words[0] != 0x20702 or prefix.header_words[1:3] != (0, 0):
        raise ValueError("unsupported loader header or auxiliary arrays")
    if len(tree.roots) != prefix.header_words[0] >> 16:
        raise ValueError("root header child count mismatch")
    forbidden = ("$sortplane", "$limits", "$raceline", "startpoint")
    if any(s in n.name.lower() for n in nodes for s in forbidden):
        raise ValueError("pre-hull node processing requires separate reconstruction")
    hull = hulls[0]
    records = tuple(struct.unpack_from("<3I", data, tri.record_offset + 52*i + 16)
                    for i in range(tri.record_count))
    if any(i >= tri.vector_c_count for face in records for i in face):
        raise ValueError("out-of-range global C index")
    ids = range(hull.mesh_start, hull.mesh_start + hull.mesh_count)
    if not hull.mesh_count or ids.stop > len(records):
        raise ValueError("invalid hull mesh range")
    selected = sorted({i for r in ids for i in records[r]})
    points = tuple(struct.unpack_from("<3f", data, tri.vector_c_offset+12*i)
                   for i in range(tri.vector_c_count))
    external = [r for r, face in enumerate(records) if r not in ids and set(face).intersection(selected)]
    usage = {i: [{"record": r, "nodes": [n.name for n in nodes
                 if n.mesh_start <= r < n.mesh_start+n.mesh_count]}
                 for r, face in enumerate(records) if i in face] for i in selected}
    return {"data": data, "tri": tri, "points": points, "selected": selected,
            "records": records, "faces": tuple(records[r] for r in ids),
            "record_ids": list(ids), "external_records": external, "usage": usage}


def translation_math(before, after, faces, translation):
    a, b = emit_triangles(before, faces), emit_triangles(after, faces)
    plane_residuals, stale_errors = [], []
    for fa, fb in zip(a, b):
        _, n = _face(fa)
        d = -sum(n[k]*fa[0][k] for k in range(3))
        expected_d = d - sum(n[k]*translation[k] for k in range(3))
        # Fixed baseline normals isolate the expected change in the plane constant.
        plane_residuals.extend(abs(sum(n[k]*p[k] for k in range(3))+expected_d) for p in fb)
        stale_errors.extend(abs(sum(n[k]*p[k] for k in range(3))+d) for p in fb)
    unique_a, unique_b = set(p for f in a for p in f), set(p for f in b for p in f)
    return {"fixed_normal_translated_plane_max_residual": max(plane_residuals),
            "stale_baseline_plane_max_residual": max(stale_errors),
            "origin_radius_baseline": max(math.dist(p,(0,0,0)) for p in unique_a),
            "origin_radius_candidate": max(math.dist(p,(0,0,0)) for p in unique_b),
            "evidence": "OFFLINE_MATHEMATICAL_DIFFERENTIAL; no stale native plane is proven"}


def build_report(baseline, candidate, exe):
    if hashlib.sha256(exe.read_bytes()).hexdigest() != EXE:
        raise ValueError("exact demo-9.3.1 EXE required")
    a, b = read_model(baseline), read_model(candidate)
    if hashlib.sha256(a["data"]).hexdigest() != BASELINE:
        raise ValueError("oracle currently pinned to evidenced Trooper baseline")
    expected = bytearray(a["data"])
    for i in a["selected"]:
        offset = a["tri"].vector_c_offset+12*i
        struct.pack_into("<f", expected, offset, f32(a["points"][i][0]+0.4))
    scope = bytes(expected) == b["data"] and not a["external_records"] and not b["external_records"]
    modes = {}
    for mode, single in (("wide_intermediates", False), ("single_intermediates", True)):
        pa, pb = loader_positions(a["points"], single_precision=single), loader_positions(b["points"], single_precision=single)
        ia, ib = isolation_proof(pa, a["selected"]), isolation_proof(pb, b["selected"])
        differential = compare_streams(pa, pb, a["faces"], b["faces"], ia, ib,
                                      pre_hull_stages_excluded=True, source_scope_validated=scope)
        ha, hb = early_hull_probe(pa, a["faces"]), early_hull_probe(pb, b["faces"])
        changed = [sa[0] for sa, sb in zip(ha["signatures"], hb["signatures"]) if sa != sb]
        ha.pop("signatures"); hb.pop("signatures")
        native_probe = {"baseline": ha, "candidate": hb, "changed_triple_classifications": changed,
                        "scope": "Configured thickness not captured; initial EXE default only. Binary64 diagnostic, not native execution."}
        modes[mode] = {"early_hull_probe": native_probe, "baseline_proof": ia, "candidate_proof": ib,
                       "differential": differential,
                       "translation_math": translation_math(pa, pb, a["faces"], (0.4,0,0))}
        for label, model, positions, proof in (("baseline", a, pa, ia), ("candidate", b, pb, ib)):
            modes[mode][label] = {
                "pre_weld_buffer_count": len(positions), "post_weld_buffer_count": len(positions),
                "effective_indices": model["faces"], "record_ids": model["record_ids"],
                "source_to_representative": proof["representatives"],
                "positions": [{"index": i, "source": model["points"][i], "pre_weld": positions[i],
                               "post_weld": positions[i] if proof["complete"] else None,
                               "usage": model["usage"][i]} for i in model["selected"]],
                "post_weld_stream": emit_triangles(positions, model["faces"]) if proof["complete"] else None,
                "external_records_using_hull_indices": model["external_records"]}
    decision = "B" if all(m["differential"]["decision"] == "B" for m in modes.values()) else "U"
    return {"schema": "r-demo2.5-isolated-weld-oracle-v1", "decision": decision,
            "evidence": "CONFIRMED_BY_EXE control flow; REPRODUCED_OFFLINE isolated hull projection",
            "scope": "Exact no-write proof for selected hull indices. Does not reconstruct non-hull weld classes or capture native FP control word.",
            "baseline_sha256": hashlib.sha256(a["data"]).hexdigest(),
            "candidate_sha256": hashlib.sha256(b["data"]).hexdigest(), "exe_sha256": EXE,
            "baseline_path": str(baseline.resolve()), "candidate_path": str(candidate.resolve()),
            "old_candidate_identity": "9.3.1 offline analogue, not byte-identical to traced 8.4.1 crash candidate",
            "source_byte_scope_validated": scope, "modes": modes}


def summary(report):
    return {k: v for k, v in report.items() if k != "modes"} | {"modes": {
        name: {"baseline_nearest_distance": m["baseline_proof"]["nearest_other_distance"],
               "candidate_nearest_distance": m["candidate_proof"]["nearest_other_distance"],
               "baseline_singleton_classes": len(m["baseline_proof"]["welded_classes"] or []),
               "candidate_singleton_classes": len(m["candidate_proof"]["welded_classes"] or []),
               "differential": m["differential"], "translation_math": m["translation_math"], "early_hull_probe": m["early_hull_probe"]}
        for name, m in report["modes"].items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("baseline", "candidate", "exe", "output"):
        p.add_argument("--"+arg, type=Path, required=True)
    args = p.parse_args()
    output = args.output.resolve()
    allowed = (ROOT/".research-output"/"r-demo2").resolve()
    if not output.is_relative_to(allowed):
        p.error("full position/triangle output must stay in ignored .research-output/r-demo2")
    if output in {args.baseline.resolve(), args.candidate.resolve(), args.exe.resolve()}:
        p.error("output cannot overwrite an input")
    report = build_report(args.baseline, args.candidate, args.exe)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(summary(report), indent=2, allow_nan=False))
    return 0 if report["decision"] == "B" else 2

if __name__ == "__main__":
    raise SystemExit(main())
