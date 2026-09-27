"""Same-source Demo DX revision comparison using the existing DX readers.

The 9.3.1 demo draw record is intentionally kept as raw bytes by
``demo_dx``. This module aligns those raw records against parsed 9.10.0
records only when shared core fields and the trailing texture-reference bytes
prove the boundary. Unknown legacy draw-prefix bytes remain opaque.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
import hashlib
import struct
from typing import Any

from .demo_dx import DemoDxView, inspect_demo_dx
from .dx import parse_dx_bytes
from .errors import FormatError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _byte_ranges(first: bytes, second: bytes, start: int = 0) -> list[list[int]]:
    """Coalesce byte positions that differ; inputs must have equal lengths."""
    if len(first) != len(second):
        raise ValueError("byte range comparison requires equal-sized sections")
    ranges: list[list[int]] = []
    range_start: int | None = None
    for offset, (left, right) in enumerate(zip(first, second)):
        if left != right and range_start is None:
            range_start = offset
        elif left == right and range_start is not None:
            ranges.append([start + range_start, start + offset])
            range_start = None
    if range_start is not None:
        ranges.append([start + range_start, start + len(first)])
    return ranges


def _prefix_suffix(first: bytes, second: bytes) -> tuple[int, int]:
    limit = min(len(first), len(second))
    prefix = 0
    while prefix < limit and first[prefix] == second[prefix]:
        prefix += 1
    suffix = 0
    while suffix < limit - prefix and first[-1 - suffix] == second[-1 - suffix]:
        suffix += 1
    return prefix, suffix


def _file_section_ranges(view: DemoDxView) -> dict[str, tuple[int, int]]:
    count = view.header[3]
    position_start = 16
    position_end = position_start + count * 12
    normal_end = position_end + count * 12
    color_end = normal_end + count * 4
    uv_count = struct.unpack_from("<I", view.data, color_end)[0]
    uv_end = color_end + 4 + uv_count * count * 8
    local_count = struct.unpack_from("<I", view.data, uv_end)[0]
    local_end = uv_end + 4 + local_count * 2
    if local_end != view.draw_offset:
        raise FormatError(
            f"DX local-index boundary 0x{local_end:X} disagrees with "
            f"parsed draw boundary 0x{view.draw_offset:X} in {view.source}"
        )
    return {
        "header": (0, 16),
        "positions": (position_start, position_end),
        "normals": (position_end, normal_end),
        "colors": (normal_end, color_end),
        "uv_count_and_sets": (color_end, uv_end),
        "local_count_and_indices": (uv_end, local_end),
        "local_indices": (uv_end + 4, local_end),
    }


def _triangles(indices: tuple[int, ...], start: int, count: int, base: int) -> list[tuple[int, int, int]]:
    values = indices[start:start + count]
    if len(values) != count or count % 3:
        raise FormatError(f"draw index range {start}+{count} is incomplete")
    return [
        (values[i] + base, values[i + 1] + base, values[i + 2] + base)
        for i in range(0, len(values), 3)
    ]


def _draw_alignment(first: DemoDxView, second: DemoDxView) -> dict[str, Any]:
    """Validate old/new flat draw alignment without decoding rev131 fields."""
    if len(first.draw_raw) < 8 or len(second.draw_raw) < 8:
        return {"status": "UNRESOLVED", "reason": "draw envelope is truncated"}
    first_count = struct.unpack_from("<I", first.draw_raw, 4)[0]
    second_count = struct.unpack_from("<I", second.draw_raw, 4)[0]
    delta_total = len(second.draw_raw) - len(first.draw_raw)
    if (first.draw_raw[:8] != second.draw_raw[:8] or first_count != second_count
            or second_count == 0 or delta_total % second_count):
        return {
            "status": "UNRESOLVED",
            "first_declared_count": first_count,
            "second_declared_count": second_count,
            "draw_size_delta": delta_total,
            "reason": "draw envelopes/counts do not support equal per-record alignment",
        }

    per_record_delta = delta_total // second_count
    try:
        newer = parse_dx_bytes(second.data, second.source)
    except (FormatError, ValueError, struct.error) as exc:
        return {"status": "UNRESOLVED", "reason": f"rev135 structured parse failed: {exc}"}
    draws = newer.physical_draws
    if len(draws) != second_count or any(draw.tag != 2 or draw.children for draw in draws):
        return {
            "status": "UNRESOLVED",
            "new_parsed_record_count": len(draws),
            "first_declared_count": first_count,
            "reason": "the observed flat tag-2 record alignment is not applicable",
            "rev135_parser_errors": list(newer.diagnostics.errors),
        }

    records: list[dict[str, Any]] = []
    metadata_substitutions = 0
    topology_equal = True
    material_refs_equal = True
    triangle_count = 0
    mapped_triangle_count = 0
    order_preserved_count = 0

    for draw_index, draw in enumerate(draws):
        new_start = draw.offset - second.draw_offset
        old_start = new_start - draw_index * per_record_delta
        old_size = draw.own_size - per_record_delta
        if old_start < 8 or old_size < 24 or new_start + draw.own_size > len(second.draw_raw):
            return {"status": "UNRESOLVED", "reason": f"draw {draw_index} record boundary is invalid"}
        old_record = first.draw_raw[old_start:old_start + old_size]
        new_record = second.draw_raw[new_start:new_start + draw.own_size]
        if len(old_record) != old_size or len(new_record) != draw.own_size:
            return {"status": "UNRESOLVED", "reason": f"draw {draw_index} record is truncated"}

        old_core = struct.unpack_from("<5I", old_record, 0)
        new_core = (draw.tag, draw.vertex_base, draw.local_vertex_max,
                    draw.index_start, draw.index_count)
        if old_core != new_core:
            return {
                "status": "UNRESOLVED",
                "reason": f"draw {draw_index} shared 20-byte core differs",
                "draw_index": draw_index,
            }

        if not draw.texture_slots:
            return {"status": "UNRESOLVED", "reason": f"draw {draw_index} has no parsed texture slots"}
        first_name = draw.texture_slots[0].raw
        new_name_offset = draw.texture_slots[0].data_offset - draw.offset
        old_name_offset = old_record.find(first_name, 20)
        if new_name_offset < 4 or old_name_offset < 4:
            return {"status": "UNRESOLVED", "reason": f"draw {draw_index} texture string boundary is unknown"}
        old_strings_start = old_name_offset - 4
        new_strings_start = new_name_offset - 4
        old_prefix = old_record[20:old_strings_start]
        new_prefix = new_record[20:new_strings_start]
        old_string_block = old_record[old_strings_start:]
        new_string_block = new_record[new_strings_start:]
        strings_identical = old_string_block == new_string_block
        material_refs_equal &= strings_identical
        if len(new_prefix) - len(old_prefix) != per_record_delta:
            return {
                "status": "UNRESOLVED",
                "reason": f"draw {draw_index} prefix/string alignment does not explain record growth",
            }
        prefix_differences = sum(a != b for a, b in zip(old_prefix, new_prefix))
        metadata_substitutions += prefix_differences
        prefix_byte_differences = [
            {"relative_offset": i, "old": old_prefix[i], "new": new_prefix[i]}
            for i in range(min(len(old_prefix), len(new_prefix)))
            if old_prefix[i] != new_prefix[i]
        ]

        old_triangles = _triangles(first.local_indices, draw.index_start,
                                   draw.index_count, draw.vertex_base)
        new_triangles = _triangles(second.local_indices, draw.index_start,
                                   draw.index_count, draw.vertex_base)
        same_triangle_multiset = Counter(old_triangles) == Counter(new_triangles)
        topology_equal &= same_triangle_multiset
        triangle_count += len(old_triangles)
        queues: dict[tuple[int, int, int], deque[int]] = defaultdict(deque)
        for new_triangle_index, triangle in enumerate(new_triangles):
            queues[triangle].append(new_triangle_index)
        order_map: list[int] = []
        if same_triangle_multiset:
            for triangle in old_triangles:
                order_map.append(queues[triangle].popleft())
            mapped_triangle_count += len(order_map)
            order_preserved_count += sum(i == value for i, value in enumerate(order_map))

        records.append({
            "draw_index": draw_index,
            "old_record_range": [first.draw_offset + old_start,
                                 first.draw_offset + old_start + old_size],
            "new_record_range": [second.draw_offset + new_start,
                                 second.draw_offset + new_start + draw.own_size],
            "old_record_size": old_size,
            "new_record_size": draw.own_size,
            "record_size_delta": draw.own_size - old_size,
            "first_20_bytes_equal": True,
            "legacy_opaque_prefix": old_prefix.hex(),
            "legacy_opaque_prefix_size": len(old_prefix),
            "legacy_opaque_prefix_byte_differences": prefix_byte_differences,
            "rev135_parsed_prefix": new_prefix.hex(),
            "rev135_parsed_prefix_size": len(new_prefix),
            "rev135_fields": {
                "unknown_0x14": draw.unknown_0x14,
                "unknown_0x18": draw.unknown_0x18,
                "unknown_0x1c_float": draw.unknown_0x1c_float,
                "flags_0x20_hex": draw.flags_0x20.hex(),
                "unknown_0x24": draw.unknown_0x24,
                "texture_slot_count": len(draw.texture_slots),
            },
            "aligned_prefix_byte_substitutions": prefix_differences,
            "texture_references": list(draw.texture_tuple),
            "texture_reference_suffix_byte_identical": strings_identical,
            "triangle_count": len(old_triangles),
            "triangle_multiset_equal_with_winding": same_triangle_multiset,
            "old_triangle_index_to_new_triangle_index": order_map,
        })

    return {
        "status": "VERIFIED" if topology_equal and material_refs_equal else "DIFFERENT_OR_UNRESOLVED",
        "record_alignment_status": "VERIFIED",
        "topology_status": "EQUAL" if topology_equal else "DIFFERENT",
        "material_reference_status": "EQUAL" if material_refs_equal else "DIFFERENT",
        "declared_record_count": first_count,
        "parsed_rev135_record_count": len(draws),
        "draw_size_delta": delta_total,
        "per_record_size_delta": per_record_delta,
        "legacy_prefix_size": records[0]["legacy_opaque_prefix_size"] if records else None,
        "rev135_prefix_size": records[0]["rev135_parsed_prefix_size"] if records else None,
        "legacy_prefix_byte_substitutions": metadata_substitutions,
        "inserted_bytes": max(per_record_delta, 0) * first_count,
        "all_record_sizes_expand_equally": all(r["record_size_delta"] == per_record_delta for r in records),
        "all_first_20_bytes_equal": all(r["first_20_bytes_equal"] for r in records),
        "all_texture_reference_suffixes_identical": material_refs_equal,
        "all_per_draw_oriented_triangle_multisets_equal": topology_equal,
        "triangle_count": triangle_count,
        "triangles_mapped": mapped_triangle_count,
        "triangle_order_preserved": order_preserved_count == triangle_count,
        "triangle_order_identity_count": order_preserved_count,
        "rev135_parser_validation": {
            "validated": newer.diagnostics.validated,
            "errors": list(newer.diagnostics.errors),
            "warnings": list(newer.diagnostics.warnings),
        },
        "records": records,
    }


def _collision_summary(view: DemoDxView) -> dict[str, Any]:
    collision = view.collision
    hull = collision.convex_hull
    cylinder = collision.cylinder
    bounds = collision.spatial_bounds_1339
    return {
        "tags": list(collision.tag_ids),
        "bsp_sha256": collision.bsp.sha256 if collision.bsp else None,
        "tag101": ({
            "sha256": hull.sha256,
            "size": len(hull.raw),
            "base_geometry_counts": [hull.base_geometry.vertex_count,
                                     hull.base_geometry.triangle_count],
            "base_scalar": hull.base_scalar,
            "representation_a_counts": [hull.representation_a.geometry_a.vertex_count,
                                         hull.representation_a.geometry_a.triangle_count],
            "representation_b_counts": [hull.representation_b.geometry_a.vertex_count,
                                         hull.representation_b.geometry_a.triangle_count],
        } if hull else None),
        "tag102": ({
            "sha256": cylinder.sha256,
            "size": len(cylinder.raw),
            "values": [cylinder.value_0, cylinder.value_1],
        } if cylinder else None),
        "marker1339": ({
            "sha256": _sha256(bounds.raw),
            "size": len(bounds.raw),
            "center": list(bounds.center),
            "radius": bounds.radius,
            "minimum": list(bounds.minimum),
            "maximum": list(bounds.maximum),
        } if bounds else None),
        "unparsed_tail_size": len(collision.unparsed_data),
        "warnings": list(collision.warnings),
        "errors": list(collision.errors),
    }


def compare_cooker_dx(
    first: bytes,
    second: bytes,
    *,
    first_source: str = "rev131",
    second_source: str = "rev135",
    source_hashes: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """Compare a 9.3.1 rev131 DX against 9.10.0 rev135.

    Source hashes are optional for generic byte analysis. When supplied, they
    are surfaced explicitly so a same-source conclusion is never inferred
    from output similarity alone.
    """
    left = inspect_demo_dx(first, first_source)
    right = inspect_demo_dx(second, second_source)
    if left.header[1] != 131 or right.header[1] != 135:
        raise ValueError(
            f"expected revision 131 then 135, received {left.header[1]} then {right.header[1]}"
        )
    if len(first) > len(second):
        raise ValueError("revision-135 output is shorter than revision-131 output in this experiment")

    left_ranges = _file_section_ranges(left)
    right_ranges = _file_section_ranges(right)
    section_comparisons: dict[str, Any] = {}
    for section in ("header", "positions", "normals", "colors", "uv_count_and_sets"):
        a, b = left_ranges[section], right_ranges[section]
        if a[1] - a[0] != b[1] - b[0]:
            section_comparisons[section] = {"equal": False, "reason": "section sizes differ"}
        else:
            raw_a, raw_b = first[a[0]:a[1]], second[b[0]:b[1]]
            section_comparisons[section] = {
                "equal": raw_a == raw_b,
                "first_range": list(a),
                "second_range": list(b),
                "size": len(raw_a),
                "different_byte_count": sum(x != y for x, y in zip(raw_a, raw_b)),
                "different_ranges": _byte_ranges(raw_a, raw_b, a[0]) if len(raw_a) == len(raw_b) else [],
            }

    local_a_range = left_ranges["local_indices"]
    local_b_range = right_ranges["local_indices"]
    local_a = first[local_a_range[0]:local_a_range[1]]
    local_b = second[local_b_range[0]:local_b_range[1]]
    if len(local_a) != len(local_b):
        raise FormatError("local-index buffers have different lengths")
    local_count_offset_a = local_a_range[0] - 4
    local_count_offset_b = local_b_range[0] - 4
    local_count_header_equal = (
        first[local_count_offset_a:local_count_offset_a + 4]
        == second[local_count_offset_b:local_count_offset_b + 4]
    )
    draw = _draw_alignment(left, right)
    common_prefix, common_suffix = _prefix_suffix(first, second)
    offset_range_count = len(_byte_ranges(first[:min(len(first), len(second))],
                                          second[:min(len(first), len(second))]))
    source_identity: dict[str, Any] = {"status": "NOT_SUPPLIED"}
    if source_hashes is not None:
        first_source_hash, second_source_hash = source_hashes
        source_identity = {
            "first_sha256": first_source_hash,
            "second_sha256": second_source_hash,
            "equal": first_source_hash.lower() == second_source_hash.lower(),
            "status": "CONFIRMED_BY_BYTES" if first_source_hash.lower() == second_source_hash.lower()
            else "DIFFERENT_SOURCE_CONTENT",
        }

    header_revision_only = (
        section_comparisons["header"].get("different_ranges") == [[4, 5]]
    )
    shifted_global_equal = (
        first[left.global_offset:left.collision.offset]
        == second[right.global_offset:right.collision.offset]
    )
    shifted_collision_equal = first[left.collision.offset:] == second[right.collision.offset:]
    normalized_accounting_complete = (
        header_revision_only
        and all(section_comparisons[name]["equal"] for name in
                ("positions", "normals", "colors", "uv_count_and_sets"))
        and local_count_header_equal
        and draw.get("status") == "VERIFIED"
        and shifted_global_equal
        and shifted_collision_equal
        and len(second) - len(first) == draw.get("inserted_bytes")
    )
    normalized_edit_bytes = (
        section_comparisons["header"].get("different_byte_count", 0)
        + sum(a != b for a, b in zip(local_a, local_b))
        + draw.get("legacy_prefix_byte_substitutions", 0)
        + draw.get("inserted_bytes", 0)
    )

    geometry_attrs_equal = all(
        section_comparisons[name]["equal"] for name in
        ("positions", "normals", "colors", "uv_count_and_sets")
    )
    if not geometry_attrs_equal:
        geometry_verdict = "DIFFERENT"
    elif draw.get("record_alignment_status") == "VERIFIED":
        geometry_verdict = (
            "EQUIVALENT_AFTER_REMAP"
            if draw.get("topology_status") == "EQUAL"
            else "DIFFERENT"
        )
    elif geometry_attrs_equal and left.global_indices == right.global_indices:
        geometry_verdict = "TOPOLOGY_UNRESOLVED"
    else:
        geometry_verdict = "TOPOLOGY_UNRESOLVED"

    return {
        "schema_version": 1,
        "evidence": "CONFIRMED_BY_BYTES",
        "first": {"label": first_source, "size": len(first), "sha256": left.sha256,
                  "header": list(left.header)},
        "second": {"label": second_source, "size": len(second), "sha256": right.sha256,
                   "header": list(right.header)},
        "source_identity": source_identity,
        "byte_diff": {
            "same_absolute_offset_hamming_count": sum(a != b for a, b in zip(first, second)),
            "same_absolute_offset_hamming_range_count": offset_range_count,
            "length_delta": len(second) - len(first),
            "common_prefix_length": common_prefix,
            "common_suffix_length": common_suffix,
            "note": "Same-offset mismatches include bytes shifted by draw-record growth; use the section-aligned map below for semantic accounting.",
        },
        "sections": section_comparisons,
        "normalized_byte_accounting": {
            "header_revision_field_only": header_revision_only,
            "position_normal_uv_color_sections_identical": all(
                section_comparisons[name]["equal"] for name in
                ("positions", "normals", "colors", "uv_count_and_sets")
            ),
            "local_index_count_field_identical": local_count_header_equal,
            "local_index_differing_byte_count": sum(a != b for a, b in zip(local_a, local_b)),
            "draw_prefix_substitution_byte_count": draw.get("legacy_prefix_byte_substitutions", 0),
            "draw_record_inserted_byte_count": draw.get("inserted_bytes", 0),
            "global_index_section_equal_after_relocation": shifted_global_equal,
            "collision_and_tail_equal_after_relocation": shifted_collision_equal,
            "length_delta_explained_by_draw_growth": len(second) - len(first) == draw.get("inserted_bytes"),
            "explained_edit_bytes": normalized_edit_bytes,
            "all_changed_content_accounted": normalized_accounting_complete,
        },
        "local_indices": {
            "first_count": len(left.local_indices),
            "second_count": len(right.local_indices),
            "equal": left.local_indices == right.local_indices,
            "changed_values": sum(a != b for a, b in zip(left.local_indices, right.local_indices)),
            "changed_value_indices": [
                {"index": i, "rev131": a, "rev135": b}
                for i, (a, b) in enumerate(zip(left.local_indices, right.local_indices))
                if a != b
            ],
            "different_byte_count": sum(a != b for a, b in zip(local_a, local_b)),
            "different_byte_ranges": _byte_ranges(local_a, local_b, local_a_range[0]),
            "global_index_sequences_equal": left.global_indices == right.global_indices,
        },
        "draws": draw,
        "global_index_sections": {
            "first_range": [left.global_offset, left.collision.offset],
            "second_range": [right.global_offset, right.collision.offset],
            "equal_after_relocation": shifted_global_equal,
        },
        "collision_and_tail": {
            "first_range": [left.collision.offset, len(first)],
            "second_range": [right.collision.offset, len(second)],
            "equal_after_relocation": shifted_collision_equal,
            "first": _collision_summary(left),
            "second": _collision_summary(right),
        },
        "geometry_equivalence": {
            "classification": geometry_verdict,
            "positions_exact": section_comparisons["positions"]["equal"],
            "normals_exact": section_comparisons["normals"]["equal"],
            "colors_exact": section_comparisons["colors"]["equal"],
            "uv_exact": section_comparisons["uv_count_and_sets"]["equal"],
            "per_draw_triangle_order_permutation_only": draw.get(
                "all_per_draw_oriented_triangle_multisets_equal", False
            ) and not draw.get("triangle_order_preserved", False),
        },
    }
