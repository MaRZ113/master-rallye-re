"""Bounded Forester COMPLETE draw-to-WOOLDAND COMPLETE root-mesh join.

No source geometry export or runtime state changes. Both exact-triangle and
coplanar overlap controls remain separate from current runtime suppression.
"""
from pathlib import Path
import collections
import importlib.util
import itertools
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "ps2-research/tools"))
SPEC = importlib.util.spec_from_file_location("old_frontend_audit",
    ROOT / "ps2-research/pc-port/docs/coverage-followup/frontend/audit.py")
old = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(old)
spec2 = importlib.util.spec_from_file_location("vehicle_audit",
    ROOT / "ps2-research/pc-port/docs/full-coverage/vehicles/audit.py")
a = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(a)
import geometry_delta as g


def index_faces(faces, tolerance):
    index = collections.defaultdict(list)
    for i, face in enumerate(faces):
        for point in face:
            index[tuple(int(x // tolerance) for x in point)].append(i)
    return index


def corner_matches(faces, target, tolerance):
    index = index_faces(target, tolerance)
    rows = []
    for face in faces:
        key = tuple(int(x // tolerance) for x in face[0])
        candidates = sorted({i for delta in itertools.product((-1, 0, 1), repeat=3)
            for i in index.get(tuple(key[j] + delta[j] for j in range(3)), [])})
        best = min(((a.w.corner_error(face, target[i]), i) for i in candidates), default=(1e20, None))
        rows.append({"matched": best[0] <= tolerance, "maximum_corner_error": best[0] if best[1] is not None else None,
                     "target_face": best[1]})
    return rows


def main():
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2 / "TNG.PAK")
    path = r"\TNG\DATAPSM\VEHICLES\WOOLDAND\COMPLETE.PSM"
    entry = old.unique_resource(manifest["entries"], path)
    payload, provenance = a.t.read_payload(entry, a.PS2 / "TNG.000")
    scene = old.decode_menu(payload)
    pcfile = a.PC / "Forester/complete.dx"
    model = a.parse_dx(pcfile)
    pcfaces = {d.draw_index: a.faces(model, d) for d in model.physical_draws}
    psfaces = {m["path"]: a.w.mesh_triangles(scene, m)[0] for m in scene.meshes}
    cases = []
    for pcid, meshpath in ((5, "root.4"), (1, "root.2")):
        source = psfaces[meshpath]
        selected = pcfaces[pcid]
        matched = corner_matches(selected, source, .005)
        strict = corner_matches(selected, source, .001)
        mesh = next(m for m in scene.meshes if m["path"] == meshpath)
        relations = []
        allcomplete = []
        othercomplete = []
        for otherid, fs in pcfaces.items():
            allcomplete.extend(g.Face(f"pc:{otherid}:{i}", str(otherid), f) for i, f in enumerate(fs))
            if otherid != pcid:
                othercomplete.extend(g.Face(f"pc:{otherid}:{i}", str(otherid), f) for i, f in enumerate(fs))
        for tolerance in (.001, .005):
            negatives = []
            for otherid, fs in sorted(pcfaces.items()):
                if otherid == pcid:
                    continue
                match = corner_matches(source, fs, tolerance)
                count = sum(r["matched"] for r in match)
                if count:
                    negatives.append({"pc_draw": otherid, "matching_ps2_faces": count})
            profile = dict(vertex=tolerance, plane=tolerance, normal=.99999,
                           coverage=.99999, near=tolerance)
            clipped, stats = g.direction_match(
                [g.Face(f"ps2:{meshpath}:{i}", meshpath, f) for i, f in enumerate(source)],
                othercomplete, profile, "NO_PC_OTHER_GROUP_SURFACE")
            overlapping = [row for row in clipped if row["coverage"] > 1e-8]
            relations.append({"tolerance": tolerance, "exact_other_group_matches": negatives,
                "coplanar_other_group_overlap_faces": len(overlapping),
                "coplanar_other_groups": sorted({x for r in overlapping for x in r["other_groups"]}),
                "maximum_other_group_coverage": max((r["coverage"] for r in overlapping), default=0.),
                "overlap_statistics": stats,
                "boundary": "No whole-mesh exclusivity is inferred from triangle hashes alone."})
        source_fullmatch = corner_matches(source, selected, .005)
        extra = [f for i, f in enumerate(source) if not source_fullmatch[i]["matched"]]
        extra_clipped, extra_stats = g.direction_match(
            [g.Face(f"extra:{i}", meshpath, f) for i, f in enumerate(extra)],
            othercomplete, dict(vertex=.005, plane=.005, normal=.99999, coverage=.99999, near=.005),
            "NO_PC_OTHER_GROUP_SURFACE")
        extra_overlap = [r for r in extra_clipped if r["coverage"] > 1e-8]
        cases.append({"pc_draw": pcid, "pc_record_path": model.physical_draws[pcid].record_path,
            "pc_faces": len(selected), "pc_geometry_sha256": a.geometry_signature(selected),
            "pc_slots": [s.value for s in model.physical_draws[pcid].texture_slots],
            "ps2_mesh": meshpath, "ps2_node": mesh["node_offset"], "ps2_material": mesh["material"],
            "ps2_slots": a.slot(mesh), "ps2_faces": len(source),
            "source_bounds": g.bounds(p for f in source for p in f),
            "pc_bounds": g.bounds(p for f in selected for p in f),
            "pc_to_ps2_exact_matches": sum(r["matched"] for r in strict),
            "pc_to_ps2_modified_matches": sum(r["matched"] for r in matched),
            "maximum_corner_error_among_matches": max((r["maximum_corner_error"] for r in matched if r["matched"]), default=None),
            "maximum_nearest_candidate_error_including_unmatched": max((r["maximum_corner_error"] for r in matched if r["maximum_corner_error"] is not None), default=None),
            "ps2_to_pc_selected_matches": sum(r["matched"] for r in source_fullmatch),
            "other_group_controls": relations,
            "ps2_extra_faces_relative_to_selected_pc_draw": len(extra),
            "extra_faces_coplanar_overlap_other_pc_groups": len(extra_overlap),
            "extra_face_other_pc_groups": sorted({x for r in extra_overlap for x in r["other_groups"]}),
            "extra_overlap_statistics": extra_stats,
            "evidence_grade": "CONFIRMED_BY_BYTES_FOR_TRIANGLES_STATIC_INFERENCE_FOR_COPLANAR_OVERLAP",
            "runtime_visibility": "UNKNOWN_NOT_A_LIVE_DRAW_CAPTURE"})
    report = {"schema_version": 1, "ps2_source": {"resource": path, "sha256": a.sha(payload), "provenance": provenance},
              "pc_source": {"path": "Forester/complete.dx", "sha256": a.sha(pcfile.read_bytes())},
              "model_kind": "COMPLETE_ONLY_NOT_CAR", "cases": cases,
              "coordinate_frame": "ORIGINAL_MODEL_LOCAL_IDENTITY_NO_FITTED_TRANSFORM",
              "limitations": [".005 source units is an explicitly relaxed material/shape join, not exact .001 geometry parity.",
                "Angularly different intersecting surfaces are not covered by the coplanar duplicate test.",
                "The unknown crashiny and untyped PS2 materials are not normalized or included in carshiny body transfer."]}
    (Path(__file__).parent / "mesh-joins.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps(cases, indent=2))


if __name__ == "__main__":
    main()
