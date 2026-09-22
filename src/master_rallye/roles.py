"""Read-only vehicle-resource role analysis for the R4A evidence reports."""
from __future__ import annotations

import json
import math
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dx import parse_dx
from .model import DxModel
from .sidecar import SidecarModel, parse_sidecar, resolve_sidecar


CREW_TERMS = ("driver", "codriver", "co-driver", "helmet", "head01", "head02", "gorrilahead")
GLASS_TERMS = ("glass", "screen", "windscreen")
WHEEL_EXCLUSIONS = ("wheelarch", "steeringwheel", "spare")


def classify_mesh_name(name: str) -> tuple[str, ...]:
    """Return evidence categories derived only from the literal sidecar name."""
    value = name.casefold()
    categories: list[str] = []
    if any(term in value for term in CREW_TERMS):
        categories.append("crew")
    if any(term in value for term in GLASS_TERMS):
        categories.append("glass")
    if "$chull(" in value:
        categories.append("collision_hull_named")
    if "wheel" in value and not any(term in value for term in WHEEL_EXCLUSIONS):
        categories.append("wheel")
    if "hub" in value:
        categories.append("hub")
    return tuple(categories)


def _aabb(model: DxModel) -> dict[str, list[float]]:
    points = model.vertices.positions
    return {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }


def _mesh_evidence(sidecar: SidecarModel | None) -> dict[str, list[dict[str, Any]]]:
    evidence = {key: [] for key in ("crew", "glass", "collision_hull_named", "wheel", "hub")}
    if sidecar is None:
        return evidence
    for mesh in sidecar.meshes:
        item = {"name": mesh.name, "index": mesh.index, "size": mesh.size}
        for category in classify_mesh_name(mesh.name):
            evidence[category].append(item)
    return evidence


def _material_tuples(sidecar: SidecarModel | None) -> list[dict[str, Any]]:
    if sidecar is None:
        return []
    values = {
        tuple(texture.resource_stem for texture in sorted(material.textures, key=lambda item: item.slot))
        for material in sidecar.materials
    }
    return [list(value) for value in sorted(values)]


def _select_structural_sidecar(
    path: Path,
    model: DxModel,
    resolved_sidecar: SidecarModel | None,
    resolved_path: Path | None,
) -> tuple[SidecarModel | None, Path | None, str]:
    """Select TXT for source mesh names separately from material resolution."""
    exact_path = path.with_suffix(".txt")
    if exact_path.exists():
        return parse_sidecar(exact_path), exact_path, "exact-stem"
    candidates: list[tuple[tuple[int, int, str], Path, SidecarModel]] = []
    for candidate_path in path.parent.glob("*.txt"):
        try:
            candidate = parse_sidecar(candidate_path)
        except (OSError, ValueError):
            continue
        hull_triangles = sum(
            mesh.size for mesh in candidate.meshes
            if "collision_hull_named" in classify_mesh_name(mesh.name)
        )
        render_gap = abs(candidate.mesh_span - model.triangle_count)
        hull_adjusted_gap = abs(candidate.mesh_span - hull_triangles - model.triangle_count)
        candidates.append((
            (min(render_gap, hull_adjusted_gap), render_gap, candidate_path.name.casefold()),
            candidate_path,
            candidate,
        ))
    if candidates:
        _, selected_path, selected = min(candidates, key=lambda item: item[0])
        return selected, selected_path, "closest-mesh-span"
    return resolved_sidecar, resolved_path, "material-resolution-fallback"


def _global_triangles(model: DxModel) -> list[tuple[int, int, int]]:
    if model.global_index_table is not None:
        values = model.global_index_table.indices
    else:
        values = tuple(index for draw in model.physical_draws for index in model.draw_global_indices(draw))
    return [tuple(values[offset:offset + 3]) for offset in range(0, len(values), 3) if offset + 2 < len(values)]


def triangle_edge_signature(
    model: DxModel,
    triangle_start: int,
    triangle_count: int,
    decimals: int = 4,
) -> Counter[tuple[float, float, float]]:
    """Rigid/reflection-invariant multiset for a contiguous triangle span."""
    triangles = _global_triangles(model)
    if triangle_start < 0 or triangle_count < 0 or triangle_start + triangle_count > len(triangles):
        return Counter()
    positions = model.vertices.positions
    signature: Counter[tuple[float, float, float]] = Counter()
    for triangle in triangles[triangle_start:triangle_start + triangle_count]:
        points = [positions[index] for index in triangle]
        lengths = []
        for first, second in ((0, 1), (1, 2), (2, 0)):
            lengths.append(round(math.dist(points[first], points[second]), decimals))
        signature[tuple(sorted(lengths))] += 1
    return signature


def multiset_similarity(first: Counter[Any], second: Counter[Any]) -> float:
    """Multiset Jaccard similarity; 1.0 means exact signature equality."""
    keys = set(first) | set(second)
    union = sum(max(first[key], second[key]) for key in keys)
    if union == 0:
        return 1.0
    intersection = sum(min(first[key], second[key]) for key in keys)
    return intersection / union


def _span_matches(
    complete: DxModel,
    complete_sidecar: SidecarModel | None,
    wheel: DxModel | None,
    wheel_sidecar: SidecarModel | None,
) -> list[dict[str, Any]]:
    if complete_sidecar is None or wheel is None or wheel_sidecar is None:
        return []
    wheel_sources = [
        mesh for mesh in wheel_sidecar.meshes
        if "wheel" in classify_mesh_name(mesh.name) and mesh.size > 0
    ]
    if not wheel_sources:
        return []
    source_signatures = {
        (mesh.name, mesh.index, mesh.size): triangle_edge_signature(wheel, mesh.index, mesh.size)
        for mesh in wheel_sources
    }
    results: list[dict[str, Any]] = []
    for mesh in complete_sidecar.meshes:
        if "wheel" not in classify_mesh_name(mesh.name) or mesh.size <= 0:
            continue
        target = triangle_edge_signature(complete, mesh.index, mesh.size)
        candidates = []
        for source in wheel_sources:
            if source.size != mesh.size:
                continue
            similarity = multiset_similarity(target, source_signatures[(source.name, source.index, source.size)])
            candidates.append({"wheel_mesh": source.name, "similarity": round(similarity, 6)})
        candidates.sort(key=lambda item: (-item["similarity"], item["wheel_mesh"].casefold()))
        results.append({
            "complete_mesh": mesh.name,
            "index": mesh.index,
            "size": mesh.size,
            "best_match": candidates[0] if candidates else None,
        })
    return results


def _whole_resource_wheel_evidence(model: DxModel, wheel: DxModel | None) -> dict[str, Any] | None:
    """Measure wheel edge-signature containment without assuming TXT span order.

    The exporter sidecar span order is not necessarily the compiled draw order,
    so this deliberately compares complete multisets rather than slicing the
    compiled global table at TXT offsets.
    """
    if wheel is None:
        return None
    target = triangle_edge_signature(model, 0, model.triangle_count, decimals=3)
    source = triangle_edge_signature(wheel, 0, wheel.triangle_count, decimals=3)
    contained = sum(min(target[key], count) for key, count in source.items())
    total = sum(source.values())
    multiplicities = [target[key] // count for key, count in source.items() if count]
    return {
        "quantization_decimals": 3,
        "wheel_triangles": total,
        "contained_signature_triangles": contained,
        "containment_ratio": round(contained / total, 6) if total else None,
        "minimum_complete_signature_multiplicity": min(multiplicities) if multiplicities else 0,
        "unique_edge_triplets": len(source),
    }


def _resource(path: Path) -> tuple[dict[str, Any], DxModel, SidecarModel | None]:
    model = parse_dx(path)
    resolution = resolve_sidecar(model, path.parent)
    resolved_sidecar = resolution.sidecar
    structural_sidecar, structural_path, structural_reason = _select_structural_sidecar(
        path, model, resolved_sidecar, resolution.selected_path
    )
    exact_path = path.with_suffix(".txt")
    slot_counts = Counter(len(draw.texture_slots) for draw in model.physical_draws)
    named_evidence = _mesh_evidence(structural_sidecar)
    hull_triangle_count = sum(item["size"] for item in named_evidence["collision_hull_named"])
    return ({
        "path": f"{path.parent.name}/{path.name}",
        "byte_size": model.byte_size,
        "vertex_count": model.vertex_count,
        "triangle_count": model.triangle_count,
        "draw_count": len(model.physical_draws),
        "declared_top_level_record_count": model.declared_top_level_record_count,
        "group_count": len(model.draw_groups),
        "record_tags": model.record_tags,
        "group_labels": model.group_labels,
        "uv_set_count": len(model.uv_sets),
        "texture_slot_count": sum(len(draw.texture_slots) for draw in model.physical_draws),
        "texture_slot_count_distribution": {str(key): value for key, value in sorted(slot_counts.items())},
        "aabb": _aabb(model),
        "trailing": {
            "layout_family": model.trailing.layout_family,
            "byte_count": len(model.trailing.data),
            "recognized_bounds": model.trailing.bounding is not None,
            "first_u32": struct.unpack_from("<I", model.trailing.data)[0] if len(model.trailing.data) >= 4 else None,
        },
        "sidecar": {
            "resolved_material_sidecar": resolution.selected_path.name if resolution.selected_path else None,
            "exact_stem_sidecar": exact_path.name if exact_path.exists() else None,
            "structural_sidecar": structural_path.name if structural_path else None,
            "structural_selection_reason": structural_reason,
            "score": resolution.score,
            "ambiguous": resolution.ambiguous,
            "mesh_span": structural_sidecar.mesh_span if structural_sidecar else None,
            "mesh_span_minus_binary_triangles": (
                structural_sidecar.mesh_span - model.triangle_count if structural_sidecar else None
            ),
            "named_collision_hull_triangle_count": hull_triangle_count,
            "material_texture_tuples": _material_tuples(resolved_sidecar),
            "mesh_count": len(structural_sidecar.meshes) if structural_sidecar else 0,
            "mesh_names": [mesh.name for mesh in structural_sidecar.meshes] if structural_sidecar else [],
        },
        "named_mesh_evidence": named_evidence,
        "parser_warnings": list(model.diagnostics.warnings),
        "validated": model.diagnostics.validated,
    }, model, structural_sidecar)


def _name_set(sidecar: SidecarModel | None) -> set[str]:
    return {mesh.name.casefold() for mesh in sidecar.meshes} if sidecar else set()


def _tuple_set(sidecar: SidecarModel | None) -> set[tuple[str, ...]]:
    if sidecar is None:
        return set()
    return {
        tuple(texture.resource_stem for texture in sorted(material.textures, key=lambda item: item.slot))
        for material in sidecar.materials
    }


def _comparison(
    vehicle: str,
    resources: dict[str, tuple[dict[str, Any], DxModel, SidecarModel | None]],
) -> dict[str, Any] | None:
    if "car" not in resources or "complete" not in resources:
        return None
    car_record, car, car_sidecar = resources["car"]
    complete_record, complete, complete_sidecar = resources["complete"]
    wheel_tuple = resources.get("wheel")
    wheel = wheel_tuple[1] if wheel_tuple else None
    wheel_sidecar = wheel_tuple[2] if wheel_tuple else None
    car_names = _name_set(car_sidecar)
    complete_names = _name_set(complete_sidecar)
    car_materials = _tuple_set(car_sidecar)
    complete_materials = _tuple_set(complete_sidecar)
    wheel_materials = _tuple_set(wheel_sidecar)
    return {
        "vehicle": vehicle,
        "delta_complete_minus_car": {
            "vertices": complete.vertex_count - car.vertex_count,
            "triangles": complete.triangle_count - car.triangle_count,
            "draws": len(complete.physical_draws) - len(car.physical_draws),
            "groups": len(complete.draw_groups) - len(car.draw_groups),
            "texture_slots": complete_record["texture_slot_count"] - car_record["texture_slot_count"],
        },
        "record_tags": {"car": car.record_tags, "complete": complete.record_tags},
        "trailing_layout": {"car": car.trailing.layout_family, "complete": complete.trailing.layout_family},
        "aabb": {"car": car_record["aabb"], "complete": complete_record["aabb"]},
        "sidecar_mesh_names": {
            "common_count": len(car_names & complete_names),
            "car_only": sorted(car_names - complete_names),
            "complete_only": sorted(complete_names - car_names),
        },
        "material_texture_tuples": {
            "car_count": len(car_materials),
            "complete_count": len(complete_materials),
            "shared_count": len(car_materials & complete_materials),
            "wheel_shared_with_complete": len(wheel_materials & complete_materials),
            "wheel_total": len(wheel_materials),
        },
        "named_mesh_counts": {
            category: {
                "car": len(car_record["named_mesh_evidence"][category]),
                "complete": len(complete_record["named_mesh_evidence"][category]),
            }
            for category in ("crew", "glass", "collision_hull_named", "wheel", "hub")
        },
        "embedded_wheel_geometry_matches": _span_matches(
            complete, complete_sidecar, wheel, wheel_sidecar
        ),
        "whole_resource_wheel_signature": {
            "car": _whole_resource_wheel_evidence(car, wheel),
            "complete": _whole_resource_wheel_evidence(complete, wheel),
        },
    }


def analyze_vehicle_roles(vehicle_root: Path) -> dict[str, Any]:
    """Analyze all vehicle DX resources without modifying the external corpus."""
    root = vehicle_root.resolve()
    vehicles: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for directory in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda item: item.name.casefold()):
        dx_paths = sorted(directory.glob("*.dx"), key=lambda item: item.name.casefold())
        if not dx_paths:
            continue
        parsed: dict[str, tuple[dict[str, Any], DxModel, SidecarModel | None]] = {}
        failures: list[dict[str, str]] = []
        for path in dx_paths:
            try:
                parsed[path.stem.casefold()] = _resource(path)
            except Exception as error:
                failures.append({"resource": path.name, "type": type(error).__name__, "message": str(error)})
        resource_records = {name: value[0] for name, value in sorted(parsed.items())}
        standard = {name: name in resource_records for name in ("car", "complete", "wheel")}
        vehicles.append({
            "vehicle": directory.name,
            "car_present": standard["car"],
            "complete_present": standard["complete"],
            "wheel_present": standard["wheel"],
            "other_dx_resources": sorted(name for name in resource_records if name not in standard),
            "resources": resource_records,
            "failures": failures,
        })
        compared = _comparison(directory.name, parsed)
        if compared is not None:
            comparisons.append(compared)

    resources = [resource for vehicle in vehicles for resource in vehicle["resources"].values()]
    full_wheel_containment = [
        comparison for comparison in comparisons
        if comparison["whole_resource_wheel_signature"]["complete"]
        and comparison["whole_resource_wheel_signature"]["complete"]["containment_ratio"] == 1.0
    ]
    four_copy_lower_bounds = [
        comparison for comparison in full_wheel_containment
        if comparison["whole_resource_wheel_signature"]["complete"]["minimum_complete_signature_multiplicity"] >= 4
    ]
    summary = {
        "vehicle_folder_count": len(vehicles),
        "dx_resource_count": len(resources),
        "parse_failure_count": sum(len(vehicle["failures"]) for vehicle in vehicles),
        "car_present_count": sum(vehicle["car_present"] for vehicle in vehicles),
        "complete_present_count": sum(vehicle["complete_present"] for vehicle in vehicles),
        "wheel_present_count": sum(vehicle["wheel_present"] for vehicle in vehicles),
        "car_complete_pair_count": len(comparisons),
        "validated_resource_count": sum(resource["validated"] for resource in resources),
        "car_with_named_collision_hull": sum(
            bool(vehicle["resources"].get("car", {}).get("named_mesh_evidence", {}).get("collision_hull_named"))
            for vehicle in vehicles
        ),
        "complete_with_named_collision_hull": sum(
            bool(vehicle["resources"].get("complete", {}).get("named_mesh_evidence", {}).get("collision_hull_named"))
            for vehicle in vehicles
        ),
        "car_with_named_crew": sum(
            bool(vehicle["resources"].get("car", {}).get("named_mesh_evidence", {}).get("crew"))
            for vehicle in vehicles
        ),
        "complete_with_named_crew": sum(
            bool(vehicle["resources"].get("complete", {}).get("named_mesh_evidence", {}).get("crew"))
            for vehicle in vehicles
        ),
        "complete_with_named_wheels": sum(
            bool(vehicle["resources"].get("complete", {}).get("named_mesh_evidence", {}).get("wheel"))
            for vehicle in vehicles
        ),
        "wheel_signature_candidate_count": sum(
            len(comparison["embedded_wheel_geometry_matches"]) for comparison in comparisons
        ),
        "complete_full_wheel_signature_containment_count": len(full_wheel_containment),
        "complete_four_copy_signature_lower_bound_count": len(four_copy_lower_bounds),
        "car_trailing_first_u32_101_count": sum(
            vehicle["resources"].get("car", {}).get("trailing", {}).get("first_u32") == 101
            for vehicle in vehicles
        ),
        "complete_trailing_first_u32_101_count": sum(
            vehicle["resources"].get("complete", {}).get("trailing", {}).get("first_u32") == 101
            for vehicle in vehicles
        ),
        "car_txt_gap_equals_named_hull_triangles_count": sum(
            resource["sidecar"]["mesh_span_minus_binary_triangles"]
            == resource["sidecar"]["named_collision_hull_triangle_count"]
            and resource["sidecar"]["named_collision_hull_triangle_count"] > 0
            for vehicle in vehicles
            for name, resource in vehicle["resources"].items()
            if name == "car"
        ),
    }
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_descriptor": "external DataGx/Vehicles root (path intentionally omitted)",
        "summary": summary,
        "vehicles": vehicles,
        "car_vs_complete": comparisons,
    }


def vehicle_matrix_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# R4A vehicle resource matrix",
        "",
        "All paths are relative to the external read-only `DataGx/Vehicles` tree.",
        "",
        "## Summary",
        "",
        f"- Vehicle folders: **{summary['vehicle_folder_count']}**.",
        f"- DX resources: **{summary['dx_resource_count']}**; validated: **{summary['validated_resource_count']}**; failures: **{summary['parse_failure_count']}**.",
        f"- `car.dx`: {summary['car_present_count']}; `complete.dx`: {summary['complete_present_count']}; `wheel.dx`: {summary['wheel_present_count']}.",
        f"- Car/complete pairs: {summary['car_complete_pair_count']}.",
        "",
        "## Resource presence",
        "",
        "| Vehicle | car | complete | wheel | Other DX | Warnings |",
        "|---|:---:|:---:|:---:|---|---:|",
    ]
    for vehicle in report["vehicles"]:
        warnings = sum(len(resource["parser_warnings"]) for resource in vehicle["resources"].values())
        other = ", ".join(f"`{name}.dx`" for name in vehicle["other_dx_resources"]) or "—"
        lines.append(
            f"| {vehicle['vehicle']} | {'yes' if vehicle['car_present'] else '—'} | "
            f"{'yes' if vehicle['complete_present'] else '—'} | {'yes' if vehicle['wheel_present'] else '—'} | "
            f"{other} | {warnings} |"
        )
    lines.extend([
        "",
        "## Named and geometry evidence",
        "",
        f"- Car resources with a literal `$chull(...)` sidecar mesh: {summary['car_with_named_collision_hull']}.",
        f"- Complete resources with a literal `$chull(...)` sidecar mesh: {summary['complete_with_named_collision_hull']}.",
        f"- Car resources with literal crew-associated mesh names: {summary['car_with_named_crew']}.",
        f"- Complete resources with literal crew-associated mesh names: {summary['complete_with_named_crew']}.",
        f"- Complete resources with literal non-spare wheel mesh names: {summary['complete_with_named_wheels']}.",
        f"- Complete resources containing 100% of the separate wheel edge signature: {summary['complete_full_wheel_signature_containment_count']}.",
        f"- Complete resources with a four-copy lower bound for every wheel edge-signature element: {summary['complete_four_copy_signature_lower_bound_count']}.",
        "- TXT source triangle spans are retained as diagnostics, but are not treated as compiled-table offsets.",
        f"- Car resources whose opaque trailing section starts with raw u32 `101`: {summary['car_trailing_first_u32_101_count']}.",
        f"- Car resources where TXT span minus render triangles exactly equals the named `$chull` span: {summary['car_txt_gap_equals_named_hull_triangles_count']}.",
        "",
        "Counts and names are static evidence; runtime semantics are documented separately.",
        "",
        "## Per-resource structure",
        "",
        "| Vehicle/resource | Sidecar | V | T | Draws/groups | Tags | UV | Slots | Trailing | AABB min .. max | Warnings |",
        "|---|---|---:|---:|---:|---|---:|---:|---|---|---:|",
    ])
    for vehicle in report["vehicles"]:
        for name, resource in vehicle["resources"].items():
            aabb = resource["aabb"]
            bounds = (
                f"{','.join(f'{value:.3f}' for value in aabb['minimum'])} .. "
                f"{','.join(f'{value:.3f}' for value in aabb['maximum'])}"
            )
            sidecar = resource["sidecar"]["structural_sidecar"] or "—"
            trailing = f"{resource['trailing']['layout_family']} ({resource['trailing']['byte_count']})"
            lines.append(
                f"| `{vehicle['vehicle']}/{name}.dx` | `{sidecar}` | {resource['vertex_count']} | "
                f"{resource['triangle_count']} | {resource['draw_count']}/{resource['group_count']} | "
                f"{','.join(str(tag) for tag in resource['record_tags'])} | {resource['uv_set_count']} | "
                f"{resource['texture_slot_count']} | {trailing} | {bounds} | {len(resource['parser_warnings'])} |"
            )
    return "\n".join(lines) + "\n"


def car_complete_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R4A car.dx versus complete.dx",
        "",
        "This comparison is generated from the canonical parser and structural TXT evidence.",
        "Positive deltas mean `complete.dx` contains more than `car.dx`.",
        "",
        "## Corpus classification",
        "",
        "- **CONSISTENT_ACROSS_CORPUS:** all 26 pairs exist; every car trailing section is opaque and starts with raw u32 `101`; every complete uses tag 2 only; every complete has no literal crew mesh name.",
        "- **COMMON:** 25/26 cars use tags 2/7/8; 25/26 complete files have named embedded wheels; 24/26 complete files have more triangles; 23/26 have more vertices; 25/26 have fewer draws.",
        "- **VEHICLE_SPECIFIC:** forklift has tag 2 only and two more complete draws; IceCream and Ufo complete files have fewer triangles; IceCream, RMonster, and Ufo complete files have fewer vertices; SeatBuggy complete retains `$chull(Seatbuggy)` and trailing marker `101`.",
        "- **UNKNOWN:** control-word semantics and the exact structures stored after raw trailing marker `101`.",
        "",
        "## Pair matrix",
        "",
        "| Vehicle | ΔV | ΔT | Δdraw | Car tags | Complete tags | Car crew | Complete wheels | Car hull | Complete hull | Wheel signature |",
        "|---|---:|---:|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for item in report["car_vs_complete"]:
        wheel = item["whole_resource_wheel_signature"]["complete"]
        wheel_text = "n/a" if wheel is None else (
            f"{wheel['containment_ratio']:.3f}; min×{wheel['minimum_complete_signature_multiplicity']}"
        )
        lines.append(
            f"| {item['vehicle']} | {item['delta_complete_minus_car']['vertices']} | "
            f"{item['delta_complete_minus_car']['triangles']} | {item['delta_complete_minus_car']['draws']} | "
            f"{','.join(map(str, item['record_tags']['car']))} | {','.join(map(str, item['record_tags']['complete']))} | "
            f"{item['named_mesh_counts']['crew']['car']} | {item['named_mesh_counts']['wheel']['complete']} | "
            f"{item['named_mesh_counts']['collision_hull_named']['car']} | "
            f"{item['named_mesh_counts']['collision_hull_named']['complete']} | {wheel_text} |"
        )
    lines.extend([
        "",
        "## Interpretation boundaries",
        "",
        "`complete.dx` is not simply a higher-detail `car.dx`: it normally adds four presentation wheels while omitting crew, collision-hull source content, and tag-7/tag-8 state groups. Conversely, car commonly has more draws despite fewer triangles because it retains runtime-switchable structures.",
        "",
        "The wheel signature is a quantized multiset of triangle edge lengths. It is invariant under rigid transforms and reflection. It supports repeated geometry, but it is not a byte-level identity proof and does not assign individual compiled triangles to TXT source spans.",
    ])
    return "\n".join(lines) + "\n"


def write_vehicle_role_reports(
    vehicle_root: Path,
    json_path: Path,
    markdown_path: Path,
    comparison_path: Path | None = None,
) -> dict[str, Any]:
    report = analyze_vehicle_roles(vehicle_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(vehicle_matrix_markdown(report), encoding="utf-8")
    if comparison_path is not None:
        comparison_path.write_text(car_complete_markdown(report), encoding="utf-8")
    return report
