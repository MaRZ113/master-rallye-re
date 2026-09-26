"""Build a source-only GXM chull prediction, then optionally compare to DX."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.native_hull_reconstruction import (  # noqa: E402
    HullPolicy,
    build_rep_b_core_from_gxm_chull,
)


def _prediction_json(prediction) -> dict:
    report = prediction.summary()
    report["vertices"] = [
        {"source_c_index": source_id, "dx_xyz": list(point)}
        for source_id, point in zip(prediction.vertex_source_c_indices, prediction.vertices)
    ]
    report["polygon_faces"] = [
        {"face_index": index,
         "source_c_loop": list(face.source_c_indices),
         "coplanar_source_c_indices": list(face.coplanar_source_c_indices),
         "outward_normal": list(face.normal),
         "plane_distance": face.distance,
         "first_supporting_triple": list(face.first_supporting_triple)}
        for index, face in enumerate(prediction.polygon_faces)
    ]
    report["triangles_source_c_indices"] = [list(item)
                                             for item in prediction.triangles_source_c_indices]
    report["edges_source_c_indices"] = [list(item)
                                         for item in prediction.edges_source_c_indices]
    report["edge_face_adjacency"] = [list(item) for item in prediction.edge_face_adjacency]
    report["plane_trace"] = [
        {"combination_index": item.combination_index,
         "source_c_indices": list(item.source_c_indices),
         "disposition": item.disposition,
         "normal": list(item.normal) if item.normal is not None else None,
         "distance": item.distance,
         "cross_magnitude": item.cross_magnitude,
         "coplanar_source_c_indices": list(item.coplanar_source_c_indices),
         "face_index": item.face_index}
        for item in prediction.plane_trace
    ]
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gxm", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--directive", required=True)
    parser.add_argument("--native-dx", type=Path,
                        help="optional comparison oracle; never passed to the source-only builder")
    parser.add_argument("--support-tolerance", type=float, default=1e-6)
    parser.add_argument("--output", type=Path,
                        help="optional JSON destination beneath ignored .research-output")
    args = parser.parse_args()
    gxm_path = args.gxm.resolve(strict=True)
    sidecar_path = args.sidecar.resolve(strict=True)
    gxm_data = gxm_path.read_bytes()
    policy = HullPolicy(support_tolerance=args.support_tolerance)

    # Complete construction before opening the optional native DX comparison input.
    prediction = build_rep_b_core_from_gxm_chull(
        gxm_data, sidecar_path, args.directive, policy=policy)
    report = {
        "schema": "r-demo2.10-native-hull-source-prediction-v1",
        "source_inputs": {
            "gxm_path": str(gxm_path),
            "gxm_size": len(gxm_data),
            "gxm_sha256": hashlib.sha256(gxm_data).hexdigest(),
            "sidecar_path": str(sidecar_path),
            "sidecar_sha256": hashlib.sha256(sidecar_path.read_bytes()).hexdigest(),
        },
        "prediction": _prediction_json(prediction),
    }
    if args.native_dx is not None:
        from master_rallye.demo_dx import inspect_demo_dx
        from master_rallye.hull_oracle_compare import (
            analyze_native_rep_b_loop_fan,
            analyze_native_rep_b_loop_order_hypotheses,
            compare_prediction_to_native_rep_b,
        )

        native_path = args.native_dx.resolve(strict=True)
        native_dx_data = native_path.read_bytes()
        native_dx = inspect_demo_dx(native_dx_data, str(native_path))
        native_rep_b = native_dx.collision.convex_hull.representation_b
        report["native_oracle_input"] = {
            "path": str(native_path),
            "size": len(native_dx_data),
            "sha256": hashlib.sha256(native_dx_data).hexdigest(),
            "role": "comparison_only_opened_after_source_prediction",
        }
        report["oracle_comparison"] = compare_prediction_to_native_rep_b(
            prediction, native_rep_b)
        report["native_loop_fan_hypothesis"] = analyze_native_rep_b_loop_fan(native_rep_b)
        report["native_loop_order_hypotheses"] = analyze_native_rep_b_loop_order_hypotheses(
            prediction, native_rep_b)

    output = None
    if args.output is not None:
        output = args.output.resolve()
        research_output = (ROOT / ".research-output").resolve()
        if output == research_output or research_output not in output.parents:
            parser.error("--output must be beneath this repository's ignored .research-output directory")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    comparison = report.get("oracle_comparison")
    comparison_summary = None
    if comparison is not None:
        ordering = comparison["native_ordering"]
        comparison_summary = {
            "status": comparison["status"],
            "vertex_membership_exact": comparison["vertex_membership"]["exact_source_id_set_match"],
            "max_position_error": comparison["vertex_membership"]["max_position_error"],
            "polygon_face_sets_equal": comparison["polygon_faces"]["same_per_face_vertex_sets"],
            "edge_sets_equal": comparison["edges"]["same_undirected_edge_set"],
            "edge_face_adjacency_equal": comparison["edge_face_adjacency"]["same_after_face_identity_mapping"],
            "triangulation": comparison["triangulation"]["classification"],
            "native_ordering": {
                "vertex_order_matches_prediction": ordering["vertex_order_matches_prediction"],
                "face_order_matches_prediction": ordering["face_order_matches_prediction"],
                "edge_order_matches_prediction": ordering["edge_order_matches_prediction"],
                "triangle_order_and_winding_match_prediction": ordering[
                    "triangle_list_order_and_winding_match_prediction"],
            },
            "native_loop_fan_second_vertex_matches_all_faces": report[
                "native_loop_fan_hypothesis"]["fan_from_loop_vertex_1_matches_all_faces"],
            "native_loop_fan_second_vertex_match_count": report[
                "native_loop_fan_hypothesis"]["fan_from_loop_vertex_1_match_count"],
            "native_loop_start_matches_first_occurrence_count": report[
                "native_loop_order_hypotheses"]["native_start_matches_first_occurrence_count"],
        }
    prediction_summary = prediction.summary()
    summary = {"prediction": {
                   "status": prediction_summary["status"],
                   "directive": prediction_summary["directive"],
                   "source_record_range": prediction_summary["source_record_range"],
                   "source_triangle_record_count": prediction_summary[
                       "source_triangle_record_count"],
                   "source_c_count": prediction_summary["source_c_count"],
                   "predicted_vertex_count": prediction_summary["predicted_vertex_count"],
                   "polygon_face_count": prediction_summary["polygon_face_count"],
                   "edge_count": prediction_summary["edge_count"],
                   "triangle_count": prediction_summary["triangle_count"],
                   "plane_decision_count": prediction_summary["plane_decision_count"],
                   "plane_disposition_counts": prediction_summary[
                       "plane_disposition_counts"],
                   "support_tolerance": prediction_summary["policy"][
                       "support_tolerance"],
               },
               "oracle_comparison": comparison_summary,
               "output": str(output) if output else None}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
