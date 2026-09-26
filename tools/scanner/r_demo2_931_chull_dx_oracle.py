"""Compare baseline and translated 9.3.1 cooker DX outputs conservatively."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from master_rallye.demo_dx import compare_demo_dx, inspect_demo_dx  # noqa: E402

SCRATCH_ROOT = REPO_ROOT / ".research-output" / "r-demo2"
DEFAULT_TOLERANCE = 1e-5
EXPECTED_DX_DELTA = (0.10, 0.0, 0.0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def byte_diff_summary(first: bytes, second: bytes) -> dict:
    common = min(len(first), len(second))
    offsets = [index for index in range(common) if first[index] != second[index]]
    offsets.extend(range(common, max(len(first), len(second))))
    ranges: list[list[int]] = []
    for offset in offsets:
        if ranges and ranges[-1][1] == offset:
            ranges[-1][1] += 1
        else:
            ranges.append([offset, offset + 1])
    return {
        "byte_identical": first == second,
        "first_size": len(first), "second_size": len(second),
        "first_sha256": sha256(first), "second_sha256": sha256(second),
        "changed_byte_count": len(offsets),
        "changed_byte_offsets": offsets,
        "changed_byte_ranges_end_exclusive": [
            {"start": start, "end_exclusive": end,
             "hex_start": f"0x{start:X}", "hex_end_exclusive": f"0x{end:X}"}
            for start, end in ranges
        ],
    }


def _byte_field(first: bytes, second: bytes) -> dict:
    summary = byte_diff_summary(first, second)
    return {key: summary[key] for key in
            ("byte_identical", "first_size", "second_size", "changed_byte_count",
             "changed_byte_ranges_end_exclusive")}


def _sequence_diff(first: Sequence, second: Sequence) -> dict:
    common = min(len(first), len(second))
    mismatches = [index for index in range(common) if first[index] != second[index]]
    extra_count = abs(len(first) - len(second))
    positions = mismatches + list(range(common, max(len(first), len(second))))
    runs: list[dict] = []
    for index in positions:
        if runs and runs[-1]["end_exclusive"] == index:
            runs[-1]["end_exclusive"] += 1
        else:
            runs.append({"start": index, "end_exclusive": index + 1})
    for run in runs:
        start, end = run["start"], run["end_exclusive"]
        run["first_values"] = list(first[start:min(end, len(first))][:8])
        run["second_values"] = list(second[start:min(end, len(second))][:8])
    return {"first_count": len(first), "second_count": len(second),
            "equal": first == second, "changed_item_count": len(mismatches) + extra_count,
            "changed_item_runs": runs}


def vector_delta_summary(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]],
                         expected: Sequence[float] | None = None,
                         tolerance: float = DEFAULT_TOLERANCE) -> dict:
    same_shape = len(first) == len(second) and all(len(a) == len(b) for a, b in zip(first, second))
    if not same_shape:
        return {"same_shape": False, "first_count": len(first), "second_count": len(second),
                "classification": "TOPOLOGY_OR_SHAPE_DIFFERENCE"}
    deltas = [[float(y) - float(x) for x, y in zip(a, b)] for a, b in zip(first, second)]
    if not deltas:
        return {"same_shape": True, "count": 0, "changed_components": 0,
                "max_abs_delta": 0.0, "expected_translation": list(expected) if expected is not None else None,
                "max_abs_expected_residual": 0.0, "classification": "EXACT"}
    changed = sum(value != 0.0 for row in deltas for value in row)
    max_abs = max(abs(value) for row in deltas for value in row)
    result = {"same_shape": True, "count": len(deltas),
              "changed_vertices": sum(any(value != 0.0 for value in row) for row in deltas),
              "changed_components": changed,
              "delta_min_xyz": [min(row[axis] for row in deltas) for axis in range(3)],
              "delta_max_xyz": [max(row[axis] for row in deltas) for axis in range(3)],
              "max_abs_delta": max_abs,
              "expected_translation": list(expected) if expected is not None else None}
    if expected is not None:
        if len(expected) != 3 or not all(math.isfinite(float(value)) for value in expected):
            raise ValueError("expected translation must contain three finite components")
        residuals = [[row[axis] - float(expected[axis]) for axis in range(3)] for row in deltas]
        max_residual = max(abs(value) for row in residuals for value in row)
        result["max_abs_expected_residual"] = max_residual
        result["exact_expected_vertex_count"] = sum(
            all(abs(row[axis] - float(expected[axis])) <= tolerance for axis in range(3))
            for row in deltas)
        if max_residual <= tolerance:
            if any(float(value) != 0.0 for value in expected):
                result["classification"] = "INTENTIONAL_TRANSLATION"
            else:
                result["classification"] = "EXACT" if changed == 0 else "SEMANTIC_FLOAT_NOISE"
        elif max_abs <= tolerance:
            result["classification"] = "SEMANTIC_FLOAT_NOISE"
        else:
            result["classification"] = "UNEXPECTED_NUMERIC_CHANGE"
    else:
        result["classification"] = "EXACT" if changed == 0 else (
            "SEMANTIC_FLOAT_NOISE" if max_abs <= tolerance else "NUMERIC_CHANGE")
    return result


def _field_delta(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]],
                 tolerance: float) -> dict:
    result = vector_delta_summary(first, second, tolerance=tolerance)
    if result.get("same_shape") and result["classification"] == "NUMERIC_CHANGE":
        result["classification"] = "UNEXPECTED_NUMERIC_CHANGE"
    return result


def _bounds_details(first, second) -> dict | None:
    if first is None or second is None:
        return None
    return {
        "first": {"center": list(first.center), "radius": first.radius,
                  "minimum": list(first.minimum), "maximum": list(first.maximum)},
        "second": {"center": list(second.center), "radius": second.radius,
                   "minimum": list(second.minimum), "maximum": list(second.maximum)},
        "center_delta": [b - a for a, b in zip(first.center, second.center)],
        "radius_delta": second.radius - first.radius,
        "minimum_delta": [b - a for a, b in zip(first.minimum, second.minimum)],
        "maximum_delta": [b - a for a, b in zip(first.maximum, second.maximum)],
        "classification": "OBSERVED; marker-1339 derivation is not assumed to be hull-only",
    }


def categorized_byte_accounting(first: bytes, second: bytes) -> dict:
    """Assign every changed byte to a parser-proven tag101/marker field."""
    before, after = inspect_demo_dx(first, "byte-accounting first"), inspect_demo_dx(second, "byte-accounting second")
    if len(first) != len(second):
        raise ValueError("categorized accounting currently requires equal file sizes")
    fields_by_side: dict[str, list[tuple[str, int, int]]] = {"first": [], "second": []}

    def add(side: str, label: str, start: int, size: int) -> None:
        if size:
            if start < 0 or start + size > len(first):
                raise ValueError(f"parsed field outside DX: {label} at {start}+{size}")
            fields_by_side[side].append((label, start, start + size))

    def add_hull(view, prefix: str, side: str) -> None:
        hull = view.collision.convex_hull
        if hull is None:
            return
        add(side, f"{prefix}.base_geometry_positions", hull.base_geometry.vertex_data_offset,
            hull.base_geometry.vertex_count * 12)
        add(side, f"{prefix}.base_scalar", hull.base_scalar_offset, 4)
        for rep_label, rep in (("rep_a", hull.representation_a), ("rep_b", hull.representation_b)):
            add(side, f"{prefix}.{rep_label}.geometry_a_positions", rep.geometry_a.vertex_data_offset,
                rep.geometry_a.vertex_count * 12)
            add(side, f"{prefix}.{rep_label}.geometry_b_positions", rep.geometry_b.vertex_data_offset,
                rep.geometry_b.vertex_count * 12)
            add(side, f"{prefix}.{rep_label}.face_scalars", rep.face_scalar_offset,
                len(rep.face_scalars) * 4)
            for face_index, face in enumerate(rep.face_descriptors):
                add(side, f"{prefix}.{rep_label}.secondary_descriptor_face_{face_index}",
                    face.secondary_count_offset, 4 + len(face.secondary_indices) * 4)

    add_hull(before, "tag101", "first")
    add_hull(after, "tag101", "second")
    if before.collision.spatial_bounds_1339:
        add("first", "marker_1339", before.collision.spatial_bounds_1339.offset, 44)
    if after.collision.spatial_bounds_1339:
        add("second", "marker_1339", after.collision.spatial_bounds_1339.offset, 44)
    if sorted(fields_by_side["first"]) != sorted(fields_by_side["second"]):
        raise ValueError("parsed field layout differs; categorized byte accounting would be ambiguous")
    fields = fields_by_side["first"]
    # Use the first view's field map after proving both parsers locate the same
    # recognized spans; distinct overlapping categories are rejected below.
    owned: dict[int, str] = {}
    for label, start, end in fields:
        for offset in range(start, end):
            previous = owned.get(offset)
            if previous is not None and previous != label:
                raise ValueError(f"overlapping byte categories at 0x{offset:X}: {previous}, {label}")
            if previous == label:
                continue
            owned[offset] = label

    changed = [offset for offset, (a, b) in enumerate(zip(first, second)) if a != b]
    buckets: dict[str, list[int]] = {}
    unexplained = []
    for offset in changed:
        label = owned.get(offset)
        if label is None:
            unexplained.append({"offset": offset, "hex_offset": f"0x{offset:X}",
                                "first_hex": first[offset:offset + 1].hex(),
                                "second_hex": second[offset:offset + 1].hex(),
                                "first_context_hex": first[max(0, offset - 8):offset + 9].hex(),
                                "second_context_hex": second[max(0, offset - 8):offset + 9].hex()})
        else:
            buckets.setdefault(label, []).append(offset)

    categories = {}
    for label, offsets in sorted(buckets.items()):
        ranges = []
        for offset in offsets:
            if ranges and ranges[-1]["end_exclusive"] == offset:
                ranges[-1]["end_exclusive"] += 1
                ranges[-1]["changed_byte_count"] += 1
            else:
                ranges.append({"start": offset, "end_exclusive": offset + 1,
                               "changed_byte_count": 1})
        for item in ranges:
            start, end = item["start"], item["end_exclusive"]
            item["hex_start"] = f"0x{start:X}"
            item["first_hex"] = first[start:end].hex()
            item["second_hex"] = second[start:end].hex()
        categories[label] = {"changed_byte_count": len(offsets), "ranges": ranges}
    explained = sum(item["changed_byte_count"] for item in categories.values())
    return {"total_changed_bytes": len(changed), "explained_changed_bytes": explained,
            "complete": explained == len(changed) and not unexplained,
            "categories": categories, "unexplained": unexplained}


def compare_pair(first: bytes, second: bytes, *, first_source: str, second_source: str,
                 role: str, tolerance: float = DEFAULT_TOLERANCE) -> dict:
    before = inspect_demo_dx(first, first_source)
    after = inspect_demo_dx(second, second_source)
    structural = compare_demo_dx(first, second, first_source=first_source,
                                 second_source=second_source, float_tolerance=tolerance)
    byte_diff = byte_diff_summary(first, second)
    render = {
        "positions": _field_delta(before.positions, after.positions, tolerance),
        "normals": _field_delta(before.normals, after.normals, tolerance),
        "colors": _byte_field(before.colors, after.colors),
        "uv_set_count_first": len(before.uv_sets),
        "uv_set_count_second": len(after.uv_sets),
        "uv_set_count_equal": len(before.uv_sets) == len(after.uv_sets),
        "uv_sets": [_byte_field(a, b) for a, b in zip(before.uv_sets, after.uv_sets)],
        "local_indices": _sequence_diff(before.local_indices, after.local_indices),
        "draw_material_raw": _byte_field(before.draw_raw, after.draw_raw),
        "global_indices": _sequence_diff(before.global_indices, after.global_indices),
    }

    tag101 = None
    if before.collision.convex_hull is not None and after.collision.convex_hull is not None:
        hull_a, hull_b = before.collision.convex_hull, after.collision.convex_hull

        def geometry_pair(a, b, label: str, expected=None) -> dict:
            topology_equal = (a.vertex_count == b.vertex_count and
                              a.triangle_count == b.triangle_count and
                              a.triangles == b.triangles)
            result = {"name": label,
                      "first_vertex_count": a.vertex_count,
                      "second_vertex_count": b.vertex_count,
                      "first_triangle_count": a.triangle_count,
                      "second_triangle_count": b.triangle_count,
                      "triangles_equal": a.triangles == b.triangles,
                      "topology_equal": topology_equal,
                      "positions": vector_delta_summary(a.vertices, b.vertices,
                                                        expected=expected, tolerance=tolerance)}
            return result

        tag101 = {
            "first_size": len(hull_a.raw), "second_size": len(hull_b.raw),
            "raw_equal": hull_a.raw == hull_b.raw,
            "base_scalar_first": hull_a.base_scalar,
            "base_scalar_second": hull_b.base_scalar,
            "base_scalar_delta": hull_b.base_scalar - hull_a.base_scalar,
            "base_geometry": geometry_pair(hull_a.base_geometry, hull_b.base_geometry,
                                            "base_geometry"),
            "representation_a": {
                "geometry_a": geometry_pair(hull_a.representation_a.geometry_a,
                                             hull_b.representation_a.geometry_a,
                                             "representation_a.geometry_a",
                                             EXPECTED_DX_DELTA if role == "candidate" else None),
                "geometry_b": geometry_pair(hull_a.representation_a.geometry_b,
                                             hull_b.representation_a.geometry_b,
                                             "representation_a.geometry_b"),
                "metadata": structural["collision"]["tag101"]["representation_a"],
            },
            "representation_b": {
                "geometry_a": geometry_pair(hull_a.representation_b.geometry_a,
                                             hull_b.representation_b.geometry_a,
                                             "representation_b.geometry_a",
                                             EXPECTED_DX_DELTA if role == "candidate" else None),
                "geometry_b": geometry_pair(hull_a.representation_b.geometry_b,
                                             hull_b.representation_b.geometry_b,
                                             "representation_b.geometry_b"),
                "metadata": structural["collision"]["tag101"]["representation_b"],
            },
        }
    elif before.collision.convex_hull is not None or after.collision.convex_hull is not None:
        tag101 = {"classification": "TOPOLOGY_OR_TAG_PRESENCE_DIFFERENCE",
                  "first_present": before.collision.convex_hull is not None,
                  "second_present": after.collision.convex_hull is not None}

    collision = structural["collision"]
    collision_details = {
        "recognized_tag_ids_first": list(before.collision.tag_ids),
        "recognized_tag_ids_second": list(after.collision.tag_ids),
        "bsp_raw_equal": collision["bsp_raw_equal"],
        "cylinder_raw_equal": collision["cylinder_raw_equal"],
        "unparsed_raw_equal": collision["unparsed_raw_equal"],
        "other_bytes_equal_after_parsed_float_and_secondary_masks":
            collision["other_bytes_equal_after_float_and_secondary_mask"],
        "tag101": tag101,
        "marker_1339": _bounds_details(before.collision.spatial_bounds_1339,
                                        after.collision.spatial_bounds_1339),
        "parser_structured_report": collision,
    }

    unexpected = []
    unresolved_auxiliary = []
    if role == "candidate":
        if render["positions"]["classification"] not in ("EXACT", "SEMANTIC_FLOAT_NOISE"):
            unexpected.append("render vertex positions changed beyond float-noise tolerance")
        if render["normals"]["classification"] not in ("EXACT", "SEMANTIC_FLOAT_NOISE"):
            unexpected.append("render normals changed beyond float-noise tolerance")
        if not render["colors"]["byte_identical"] or any(not item["byte_identical"] for item in render["uv_sets"]):
            unexpected.append("render colors or UV bytes changed")
        if not render["uv_set_count_equal"]:
            unexpected.append("render UV set count changed")
        if not render["local_indices"]["equal"] or not render["global_indices"]["equal"]:
            unexpected.append("render index stream changed")
        if not render["draw_material_raw"]["byte_identical"]:
            unexpected.append("draw/material raw bytes changed")
        if tag101 is None or "representation_a" not in tag101 or "representation_b" not in tag101:
            unexpected.append("tag101 is absent or incomplete")
        else:
            for rep_name in ("representation_a", "representation_b"):
                geometry = tag101[rep_name]["geometry_a"]
                if not geometry["topology_equal"]:
                    unexpected.append(f"tag101 {rep_name}.geometry_a topology changed")
                if geometry["positions"]["classification"] != "INTENTIONAL_TRANSLATION":
                    unexpected.append(f"tag101 {rep_name}.geometry_a is not the expected compiled translation")
                metadata = tag101[rep_name]["metadata"]
                for field_name in ("referenced_vertex_indices_equal", "edges_equal",
                                   "primary_descriptors_equal",
                                   "edge_face_adjacency_equal", "face_loops_equal"):
                    if not metadata.get(field_name, False):
                        unexpected.append(f"tag101 {rep_name} {field_name} is false")
                secondary = metadata["secondary_descriptor_analysis"]
                if secondary["classification"] != "AUXILIARY_SECONDARY_DESCRIPTORS_EQUAL":
                    unresolved_auxiliary.append({"representation": rep_name,
                                                 "classification": secondary["classification"],
                                                 "semantics": "UNRESOLVED",
                                                 "changed_faces": secondary["changed_faces"]})
                if (not metadata["face_scalars"]["same_shape"] or
                        metadata["face_scalars"]["max_abs_delta"] > tolerance):
                    unexpected.append(f"tag101 {rep_name} face scalars changed beyond tolerance")
            if abs(tag101["base_scalar_delta"]) > tolerance:
                unexpected.append("tag101 base scalar changed beyond float-noise tolerance")
        if not collision["bsp_raw_equal"] or not collision["cylinder_raw_equal"]:
            unexpected.append("a non-tag101 recognized collision block changed")
        if not collision["other_bytes_equal_after_float_and_secondary_mask"]:
            unexpected.append("unparsed/non-float collision bytes changed")

    if tag101 is None:
        topology_class = "CORE_TOPOLOGY_DIFFERENT" if before.collision.convex_hull != after.collision.convex_hull else "NOT_PARSED"
    elif "classification" in tag101:
        topology_class = "CORE_TOPOLOGY_DIFFERENT"
    else:
        topology_equal = all(
            tag101[rep_name]["metadata"]["core_topology"]["classification"] == "CORE_TOPOLOGY_EQUAL"
            for rep_name in ("representation_a", "representation_b"))
        topology_class = "CORE_TOPOLOGY_EQUAL" if topology_equal else "CORE_TOPOLOGY_DIFFERENT"

    byte_accounting = categorized_byte_accounting(first, second)

    return {
        "role": role,
        "files": {"first": {"path": first_source, "size": len(first), "sha256": sha256(first)},
                  "second": {"path": second_source, "size": len(second), "sha256": sha256(second)}},
        "byte_diff": byte_diff,
        "semantic_verdict_from_existing_demo_dx_parser": structural["verdict"],
        "float_tolerance": tolerance,
        "render": render,
        "collision": collision_details,
        "unexpected_changes": unexpected,
        "unresolved_auxiliary_changes": unresolved_auxiliary,
        "categorized_byte_accounting": byte_accounting,
        "classification": {
            "byte_difference": "BYTE_IDENTICAL" if byte_diff["byte_identical"] else "BYTE_DIFFERENT",
            "semantic_float_noise_tolerance": tolerance,
            "topology": topology_class,
            "auxiliary_secondary_descriptors": (
                "AUXILIARY_SECONDARY_DESCRIPTORS_DIFFER" if unresolved_auxiliary
                else "AUXILIARY_SECONDARY_DESCRIPTORS_EQUAL"),
            "auxiliary_secondary_descriptor_semantics": "UNRESOLVED",
            "intentional_translation": (role == "candidate" and not unexpected and
                                        topology_class == "CORE_TOPOLOGY_EQUAL"),
            "unexpected_change": bool(unexpected),
        },
    }


def _read_audit(path: Path) -> dict:
    audit = json.loads(path.read_text(encoding="utf-8"))
    if audit.get("schema") != "r-demo2.8-931-chull-candidate-v1":
        raise ValueError("candidate audit schema does not match the 9.3.1 candidate tool")
    if audit.get("status") != "CANDIDATE_PREPARED_RUNTIME_UNTESTED":
        raise ValueError("candidate audit is not an untested 9.3.1 candidate record")
    if audit.get("translation_source_xyz") != [0.1, 0.0, 0.0]:
        raise ValueError("candidate audit does not describe the +0.10 X translation")
    return audit


def compare_oracle(baseline_a: Path, baseline_b: Path, candidate_dx: Path,
                   candidate_audit_path: Path, output: Path,
                   tolerance: float = DEFAULT_TOLERANCE) -> dict:
    audit = _read_audit(candidate_audit_path.resolve(strict=True))
    a_path, b_path = baseline_a.resolve(strict=True), baseline_b.resolve(strict=True)
    candidate_path = candidate_dx.resolve(strict=True)
    a, b, candidate = a_path.read_bytes(), b_path.read_bytes(), candidate_path.read_bytes()
    audit_candidate_path = Path(audit["candidate_path"]).resolve(strict=True)
    if SCRATCH_ROOT.resolve() not in audit_candidate_path.parents:
        raise ValueError("audited candidate GXM must stay below ignored .research-output/r-demo2")
    if audit_candidate_path.name != "trooper-931-chull-xplus010.gxm":
        raise ValueError("candidate audit refers to an unexpected candidate filename")
    if sha256(audit_candidate_path.read_bytes()) != audit["candidate_sha256"]:
        raise ValueError("candidate GXM bytes do not match the supplied audit SHA256")
    baseline_pair = compare_pair(a, b, first_source=str(a_path), second_source=str(b_path),
                                 role="baseline", tolerance=tolerance)
    a_to_candidate = compare_pair(a, candidate, first_source=str(a_path),
                                  second_source=str(candidate_path), role="candidate",
                                  tolerance=tolerance)
    b_to_candidate = compare_pair(b, candidate, first_source=str(b_path),
                                  second_source=str(candidate_path), role="candidate",
                                  tolerance=tolerance)
    if baseline_pair["byte_diff"]["byte_identical"]:
        consensus = "BYTE_IDENTICAL_BASELINE_CONSENSUS"
    elif baseline_pair["semantic_verdict_from_existing_demo_dx_parser"] == "SEMANTICALLY_EQUIVALENT_WITH_FLOAT_DRIFT":
        consensus = "SEMANTIC_BASELINE_CONSENSUS_WITH_FLOAT_DRIFT; COMPARE_CANDIDATE_TO_BOTH"
    else:
        consensus = "NO_BASELINE_CONSENSUS; COMPARE_CANDIDATE_TO_BOTH"
    result = {
        "schema": "r-demo2.8-931-chull-dx-oracle-v1",
        "corpus_id": "demo-9.3.1",
        "status": "COOKER_ORACLE_COMPARISON_COMPLETE",
        "candidate_gxm_audit": {
            "path": str(candidate_audit_path.resolve()),
            "source_gxm_sha256": audit["source_sha256"],
            "candidate_gxm_sha256": audit["candidate_sha256"],
            "translation_source_xyz": audit["translation_source_xyz"],
        },
        "coordinate_basis": {
            "source_to_dx": "(x,y,z) -> (x,z,-y)",
            "evidence": "Existing same-build 9.3.1 source-to-regenerated-tag101 map; source X maps to DX X.",
            "expected_dx_hull_translation_xyz": list(EXPECTED_DX_DELTA),
            "status": "EXPECTED_FROM_SAME_BUILD_MAPPING; must be checked against supplied DX files",
        },
        "baseline_consensus": consensus,
        "comparisons": {
            "baseline_A_vs_baseline_B": baseline_pair,
            "baseline_A_vs_chull_xplus010": a_to_candidate,
            "baseline_B_vs_chull_xplus010": b_to_candidate,
        },
        "runtime_scope": "DX byte/structure comparison only; no game runtime result is inferred by this report.",
    }
    output = output.resolve()
    if SCRATCH_ROOT.resolve() not in output.parents or output.suffix.lower() != ".json":
        raise ValueError("output must be JSON below ignored .research-output/r-demo2")
    report_path = output.with_suffix(".md")
    existing = [path for path in (output, report_path) if path.exists()]
    if existing:
        raise FileExistsError("refusing to overwrite " + ", ".join(str(path) for path in existing))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict) -> str:
    comparisons = result["comparisons"]
    lines = [
        "# Demo 9.3.1 `$chull` cooker oracle comparison",
        "",
        f"Baseline A/B: **{result['baseline_consensus']}**.",
        "",
        "| Pair | Byte result | Parser verdict | Core topology | Secondary data | Intentional translation | Unexpected change |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, pair in comparisons.items():
        classification = pair["classification"]
        lines.append(f"| `{key}` | {classification['byte_difference']} | {pair['semantic_verdict_from_existing_demo_dx_parser']} | {classification['topology']} | {classification['auxiliary_secondary_descriptors']} (semantics unresolved) | {classification['intentional_translation']} | {classification['unexpected_change']} |")
    lines.extend([
        "",
        "Every pair includes SHA256, file sizes, exact changed byte offsets/ranges, render arrays and streams, and parser-recognized collision structures. The underlying parser retains unknown draw bytes and reports unparsed collision bytes without assigning unsupported meanings.",
        "",
        "## Expected coordinate relation",
        "",
        f"The candidate source shift is `{result['candidate_gxm_audit']['translation_source_xyz']}` in GXM coordinates. Existing same-build 9.3.1 mapping `{result['coordinate_basis']['source_to_dx']}` predicts compiled tag101 geometry shift `{result['coordinate_basis']['expected_dx_hull_translation_xyz']}`. The comparison tests that prediction; it does not assume it succeeded.",
        "",
        "## Interpretation rules",
        "",
        "- Raw file bytes are classified independently from parsed semantics.",
        "- Float changes within the configured tolerance are labeled semantic float noise.",
        "- Triangle/index/face connectivity changes are reported as topology changes.",
        "- Core topology uses Rep geometry-A counts and triangles, referenced vertices, edges, primary descriptors, edge-face adjacency and face loops. Secondary descriptors are reported separately and cannot alone change the core-topology classification.",
        "- The expected tag101 position delta is labeled intentional translation only when parsed primary vertices match it within tolerance and core topology checks pass.",
        "- Exact secondary tuples and per-face multisets are both retained. Differences remain auxiliary and their semantics are unresolved.",
        "- Marker-1339 values are reported with exact before/after values and deltas; their hull-only meaning is not assumed.",
        "- `unexpected_changes` lists differences outside the expected render-stable and tag101-translation pattern.",
        "",
        "## Runtime scope",
        "",
        "This report describes generated DX bytes and parsed structures. It does not claim that the candidate loaded or that its collision behavior was safe in the game.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-a", type=Path, required=True)
    parser.add_argument("--baseline-b", type=Path, required=True)
    parser.add_argument("--candidate-dx", type=Path, required=True)
    parser.add_argument("--candidate-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="new JSON report path under ignored .research-output/r-demo2")
    parser.add_argument("--float-tolerance", type=float, default=DEFAULT_TOLERANCE)
    args = parser.parse_args()
    try:
        result = compare_oracle(args.baseline_a, args.baseline_b,
                                args.candidate_dx, args.candidate_audit,
                                args.output, args.float_tolerance)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps({"baseline_consensus": result["baseline_consensus"],
                      "output": str(args.output.resolve()),
                      "status": result["status"]}, indent=2))


if __name__ == "__main__":
    main()
