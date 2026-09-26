"""Conservative DEMO-to-retail DX comparison and candidate checks.

This module reuses the project parsers. It reports parser-level evidence and
does not treat that evidence as proof of game-runtime acceptance.
"""
from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .demo_dx import DemoDxView, compare_demo_dx, inspect_demo_dx
from .dx import parse_dx_bytes
from .model import DxModel

RETAIL_CACHE_MAGIC = 0x0000D00D
RETAIL_CACHE_REVISION = 0x87


def _fingerprint(data: bytes, source: str) -> dict[str, Any]:
    header = list(struct.unpack_from("<4I", data)) if len(data) >= 16 else None
    return {"source": source, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "header_u32_le": header}


def _try_demo(data: bytes, source: str) -> tuple[DemoDxView | None, dict[str, Any]]:
    try:
        view = inspect_demo_dx(data, source)
    except Exception as exc:  # parser errors are evidence in a comparison report
        return None, {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
    return view, {"status": "ACCEPTED", "header": list(view.header),
                  "vertex_count": len(view.positions), "local_index_count": len(view.local_indices),
                  "draw_raw_size": len(view.draw_raw), "global_index_count": len(view.global_indices),
                  "collision_tags": list(view.collision.tag_ids)}


def _try_retail(data: bytes, source: str) -> tuple[DxModel | None, dict[str, Any]]:
    try:
        model = parse_dx_bytes(data, source)
    except Exception as exc:  # parser errors are evidence in a comparison report
        return None, {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"}
    return model, {"status": "ACCEPTED", "summary": model.to_summary()}


def _float_rows(left: Sequence[Sequence[float]], right: Sequence[Sequence[float]]) -> dict[str, Any]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return {"same_shape": False, "left_count": len(left), "right_count": len(right),
                "exact_equal": False}
    deltas = [abs(float(a) - float(b)) for row_a, row_b in zip(left, right)
              for a, b in zip(row_a, row_b)]
    return {"same_shape": True, "count": len(left), "component_count": len(deltas),
            "exact_equal": all(delta == 0.0 for delta in deltas),
            "changed_components": sum(delta != 0.0 for delta in deltas),
            "max_abs_delta": max(deltas, default=0.0),
            "all_finite": all(math.isfinite(value) for row in left + right for value in row)}


def _byte_array(left: bytes, right: bytes) -> dict[str, Any]:
    return {"left_size": len(left), "right_size": len(right), "exact_equal": left == right,
            "left_sha256": hashlib.sha256(left).hexdigest(),
            "right_sha256": hashlib.sha256(right).hexdigest(),
            "changed_bytes": (sum(a != b for a, b in zip(left, right)) + abs(len(left) - len(right))
                              if left != right else 0)}


def _tag101(view: DemoDxView) -> dict[str, Any] | None:
    hull = view.collision.convex_hull
    if hull is None:
        return None
    return {"payload_size": len(hull.raw), "sha256": hull.sha256,
            "base_geometry": {"vertices": hull.base_geometry.vertex_count,
                              "triangles": hull.base_geometry.triangle_count},
            "base_scalar": hull.base_scalar,
            "representation_a": {
                "geometry_a": {"vertices": hull.representation_a.geometry_a.vertex_count,
                               "triangles": hull.representation_a.geometry_a.triangle_count},
                "geometry_b": {"vertices": hull.representation_a.geometry_b.vertex_count,
                               "triangles": hull.representation_a.geometry_b.triangle_count},
                "face_count": hull.representation_a.face_count,
                "edge_count": len(hull.representation_a.edges),
            },
            "representation_b": {
                "geometry_a": {"vertices": hull.representation_b.geometry_a.vertex_count,
                               "triangles": hull.representation_b.geometry_a.triangle_count},
                "geometry_b": {"vertices": hull.representation_b.geometry_b.vertex_count,
                               "triangles": hull.representation_b.geometry_b.triangle_count},
                "face_count": hull.representation_b.face_count,
                "edge_count": len(hull.representation_b.edges),
            }}


def _collision(view: DemoDxView) -> dict[str, Any]:
    collision = view.collision
    bounds = collision.spatial_bounds_1339
    return {"tags": list(collision.tag_ids), "errors": list(collision.errors),
            "warnings": list(collision.warnings), "tag101": _tag101(view),
            "tag100_sha256": collision.bsp.sha256 if collision.bsp else None,
            "tag102_sha256": collision.cylinder.sha256 if collision.cylinder else None,
            "marker1339": bounds.to_dict() if bounds else None,
            "unparsed_size": len(collision.unparsed_data),
            "unparsed_sha256": hashlib.sha256(collision.unparsed_data).hexdigest()}


def _cache_header_gate(data: bytes) -> dict[str, Any]:
    if len(data) < 8:
        return {"status": "FAIL_SHORT_HEADER", "magic": None, "revision": None,
                "magic_pass": False, "revision_pass": False}
    magic, revision = struct.unpack_from("<2I", data)
    magic_pass = magic == RETAIL_CACHE_MAGIC
    revision_pass = revision == RETAIL_CACHE_REVISION
    return {"status": "PASS" if magic_pass and revision_pass else "FAIL",
            "magic": magic, "expected_magic": RETAIL_CACHE_MAGIC, "magic_pass": magic_pass,
            "revision": revision, "expected_revision": RETAIL_CACHE_REVISION,
            "revision_pass": revision_pass,
            "evidence": "Retail MRallye.exe FUN_00551970 reads the first two DWORDs and compares them with 0xD00D and 0x87."}


def compare_dx_generations(demo_data: bytes, retail_data: bytes, *,
                           demo_source: str = "demo DX", retail_source: str = "retail DX") -> dict[str, Any]:
    """Compare observed shared sections while keeping format and content separate."""
    demo_view, demo_result = _try_demo(demo_data, demo_source)
    retail_view, retail_view_result = _try_demo(retail_data, retail_source)
    demo_as_retail, demo_retail_result = _try_retail(demo_data, demo_source)
    retail_as_retail, retail_retail_result = _try_retail(retail_data, retail_source)
    report: dict[str, Any] = {
        "schema_version": 1,
        "inputs": {"demo": _fingerprint(demo_data, demo_source),
                   "retail": _fingerprint(retail_data, retail_source)},
        "parser_coverage": {"demo_structural_parser": demo_result,
                            "retail_structural_parser_on_demo": demo_retail_result,
                            "demo_structural_parser_on_retail": retail_view_result,
                            "retail_structural_parser": retail_retail_result},
        "retail_cache_header_gate": {"demo": _cache_header_gate(demo_data),
                                      "retail": _cache_header_gate(retail_data)},
        "format_assessment": {
            "retail_parser_accepts_demo": demo_as_retail is not None,
            "retail_parser_accepts_control": retail_as_retail is not None,
            "classification": ("RETAIL_PARSER_REJECTS_DEMO_LAYOUT" if demo_as_retail is None and
                               retail_as_retail is not None else
                               "BOTH_ACCEPTED_BY_RETAIL_PARSER" if demo_as_retail is not None and
                               retail_as_retail is not None else "PARSER_EVIDENCE_INCOMPLETE"),
            "runtime_acceptance_proven": False,
        },
    }
    if demo_view is None or retail_view is None:
        report["comparison_status"] = "INCOMPLETE_DEMO_STRUCTURAL_PARSE"
        return report

    report["comparison_status"] = "COMPARED"
    report["header"] = {"demo": list(demo_view.header), "retail": list(retail_view.header),
                        "magic_equal": demo_view.header[0] == retail_view.header[0],
                        "word_0x04_equal": demo_view.header[1] == retail_view.header[1],
                        "word_0x08_equal": demo_view.header[2] == retail_view.header[2],
                        "vertex_count_equal": demo_view.header[3] == retail_view.header[3]}
    report["render"] = {
        "positions": _float_rows(demo_view.positions, retail_view.positions),
        "normals": _float_rows(demo_view.normals, retail_view.normals),
        "colors": _byte_array(demo_view.colors, retail_view.colors),
        "uv_set_count": {"demo": len(demo_view.uv_sets), "retail": len(retail_view.uv_sets),
                         "equal": len(demo_view.uv_sets) == len(retail_view.uv_sets)},
        "uv_sets": [_byte_array(a, b) for a, b in zip(demo_view.uv_sets, retail_view.uv_sets)],
        "local_indices": {"demo_count": len(demo_view.local_indices),
                          "retail_count": len(retail_view.local_indices),
                          "exact_equal": demo_view.local_indices == retail_view.local_indices},
        "draw_region": {"demo_offset": demo_view.draw_offset, "retail_offset": retail_view.draw_offset,
                        "demo_size": len(demo_view.draw_raw), "retail_size": len(retail_view.draw_raw),
                        "exact_equal": demo_view.draw_raw == retail_view.draw_raw,
                        "demo_sha256": hashlib.sha256(demo_view.draw_raw).hexdigest(),
                        "retail_sha256": hashlib.sha256(retail_view.draw_raw).hexdigest()},
        "global_indices": {"demo_count": len(demo_view.global_indices),
                           "retail_count": len(retail_view.global_indices),
                           "exact_equal": demo_view.global_indices == retail_view.global_indices},
    }
    collision_diff = compare_demo_dx(demo_data, retail_data, first_source=demo_source,
                                     second_source=retail_source)["collision"]
    report["collision"] = {"demo": _collision(demo_view), "retail": _collision(retail_view),
                           "tag_sequence_equal": demo_view.collision.tag_ids == retail_view.collision.tag_ids,
                           "semantic_diff": collision_diff}
    if retail_as_retail is not None:
        report["retail_typed_draw_tree"] = {
            "top_level_records": retail_as_retail.declared_top_level_record_count,
            "reconstructed_roots": len(retail_as_retail.draw_groups),
            "physical_draws": len(retail_as_retail.physical_draws),
            "record_tags": retail_as_retail.record_tags,
            "texture_strings": sorted({slot.value for draw in retail_as_retail.physical_draws
                                        for slot in draw.texture_slots}, key=str.lower),
            "diagnostics": retail_as_retail.diagnostics.errors + retail_as_retail.diagnostics.warnings,
        }
    return report


def validate_bridge_candidate(data: bytes, *, source: str = "bridge candidate") -> dict[str, Any]:
    """Run local retail-format checks without claiming a game runtime result."""
    gate = _cache_header_gate(data)
    try:
        model = parse_dx_bytes(data, source)
    except Exception as exc:
        return {"source": source, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "outer_format_valid": len(data) >= 4 and struct.unpack_from("<I", data)[0] == RETAIL_CACHE_MAGIC,
                "retail_required_revision_valid": gate["revision_pass"],
                "retail_cache_header_gate": gate, "recognized_tags_valid": False,
                "section_bounds_valid": False, "index_ranges_valid": False,
                "render_topology_valid": False, "collision_structures_valid": False,
                "marker_bounds_valid": False, "unknown_or_unparsed_data_bytes": None,
                "retail_parser": {"status": "REJECTED", "error": f"{type(exc).__name__}: {exc}"},
                "runtime_acceptance": "NOT_TESTED", "retail_ready": False,
                "status": "REJECTED_BY_LOCAL_RETAIL_PARSER"}

    local_indices_valid = all(index < model.vertex_count for index in model.local_indices)
    global_indices = model.global_index_table.indices if model.global_index_table else ()
    global_indices_valid = all(index < model.vertex_count for index in global_indices)
    collision = model.collision
    bounds = collision.spatial_bounds_1339
    topology_valid = model.diagnostics.validated and not model.diagnostics.errors
    collision_valid = not collision.errors
    gates_pass = gate["magic_pass"] and gate["revision_pass"]
    structural_pass = (topology_valid and local_indices_valid and global_indices_valid and collision_valid)
    return {"source": source, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "outer_format_valid": True,
            "retail_required_revision_valid": gate["revision_pass"],
            "retail_cache_header_gate": gate,
            "recognized_tags_valid": collision_valid,
            "section_bounds_valid": True,
            "index_ranges_valid": local_indices_valid and global_indices_valid,
            "render_topology_valid": topology_valid,
            "collision_structures_valid": collision_valid,
            "marker_bounds_valid": bounds is not None,
            "unknown_or_unparsed_data_bytes": len(collision.unparsed_data),
            "parser_diagnostics": {"errors": list(model.diagnostics.errors) + list(collision.errors),
                                   "warnings": list(model.diagnostics.warnings) + list(collision.warnings)},
            "retail_parser": {"status": "ACCEPTED", "summary": model.to_summary()},
            "structural_checks_pass": structural_pass and gates_pass,
            "runtime_acceptance": "NOT_TESTED", "retail_ready": False,
            "status": "STRUCTURALLY_VALIDATED_RUNTIME_UNCONFIRMED" if structural_pass and gates_pass
                     else "BLOCKED_BY_KNOWN_STRUCTURAL_OR_HEADER_CHECK"}


def audit_bridge_provenance(source: bytes, candidate: bytes,
                            ledger: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Prove every changed candidate byte is covered by exact ledger evidence."""
    changes: list[int] = []
    for offset in range(max(len(source), len(candidate))):
        before = source[offset] if offset < len(source) else None
        after = candidate[offset] if offset < len(candidate) else None
        if before != after:
            changes.append(offset)
    entries: list[dict[str, Any]] = []
    covered: set[int] = set()
    invalid: list[str] = []
    for index, raw in enumerate(ledger):
        entry = dict(raw)
        try:
            start, end = int(entry["start"]), int(entry["end"])
            if start < 0 or end <= start or end > max(len(source), len(candidate)):
                raise ValueError("invalid exclusive range")
            old = bytes.fromhex(str(entry["old_hex"]))
            new = bytes.fromhex(str(entry["new_hex"]))
            if len(old) != end - start or len(new) != end - start:
                raise ValueError("hex length does not match range")
            if source[start:end] != old or candidate[start:end] != new:
                raise ValueError("old/new bytes do not match source/candidate")
            if not str(entry.get("reason", "")).strip() or not str(entry.get("evidence", "")).strip():
                raise ValueError("reason and evidence are required")
            covered.update(range(start, end))
            entries.append({"start": start, "end": end, "old_hex": old.hex(), "new_hex": new.hex(),
                            "reason": str(entry["reason"]), "evidence": str(entry["evidence"])})
        except (KeyError, TypeError, ValueError) as exc:
            invalid.append(f"ledger entry {index}: {exc}")
    changed = set(changes)
    return {"source_sha256": hashlib.sha256(source).hexdigest(),
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
            "source_size": len(source), "candidate_size": len(candidate),
            "changed_byte_count": len(changes),
            "unchanged_source_byte_percent": (100.0 * (min(len(source), len(candidate)) -
                                                sum(i in changed for i in range(min(len(source), len(candidate))))) /
                                               len(source) if source else 100.0),
            "ledger_entries": entries,
            "uncovered_changed_offsets": sorted(changed - covered),
            "ledger_entries_outside_diff": sorted(covered - changed),
            "invalid_ledger_entries": invalid,
            "complete": not invalid and changed == covered}
