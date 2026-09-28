"""Fail-closed revision-131 vehicle DX conversion to revision 135.

The supported transformation is limited to the observed flat vehicle draw
grammar. It expands each 11-byte legacy prefix into the evidenced 24-byte
revision-135 prefix and preserves local triangle order and all other source
payloads. It does not reproduce the 9.10.0 triangle optimizer.
"""
from __future__ import annotations

import hashlib
import math
import struct
from collections import Counter
from typing import Any

from . import __version__
from .demo_dx import DemoDxView, inspect_demo_dx
from .dx import MAX_STRING_BYTES, MAX_TEXTURE_SLOTS, parse_dx_bytes
from .errors import BoundsError, FormatError, MasterRallyeError

REVISION_131 = 131
REVISION_135 = 135
_DRAW_ENVELOPE_SIZE = 8
_SHARED_DRAW_CORE_SIZE = 20
_LEGACY_PREFIX_SIZE = 11
_REV135_PREFIX_SIZE = 24
_MAX_DRAW_RECORDS = 100_000


class DxRevisionUpgradeError(FormatError):
    """A source DX or conversion candidate failed an explicit safety gate."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require(data: bytes, offset: int, size: int, label: str) -> None:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise DxRevisionUpgradeError(
            "truncated_draw_record",
            f"truncated rev131 {label} at 0x{offset:X} (need {size} bytes)",
        )


def _inspect_source(data: bytes, source: str) -> DemoDxView:
    if len(data) < 8:
        raise DxRevisionUpgradeError("truncated_header", f"DX header is truncated in {source}")
    magic, revision = struct.unpack_from("<2I", data)
    if magic != 0xD00D:
        raise DxRevisionUpgradeError(
            "invalid_magic", f"unsupported DX magic 0x{magic:08X} in {source}"
        )
    if revision == REVISION_135:
        raise DxRevisionUpgradeError(
            "already_revision_135",
            f"{source} is already revision 135; single-file conversion accepts revision 131 only",
        )
    if revision != REVISION_131:
        raise DxRevisionUpgradeError(
            "unsupported_revision",
            f"unsupported DX revision {revision} in {source}; expected 131",
        )
    try:
        return inspect_demo_dx(data, source)
    except (BoundsError, FormatError) as exc:
        raise DxRevisionUpgradeError(
            "invalid_source_structure", f"cannot establish supported rev131 vehicle structure: {exc}"
        ) from exc


def _upgrade_draw_region(draw_raw: bytes, view: DemoDxView) -> tuple[bytes, list[dict[str, Any]]]:
    _require(draw_raw, 0, _DRAW_ENVELOPE_SIZE, "draw envelope")
    preamble, record_count = struct.unpack_from("<II", draw_raw)
    if preamble != 1:
        raise DxRevisionUpgradeError(
            "unsupported_draw_preamble",
            f"unsupported rev131 draw preamble {preamble}, expected 1",
        )
    if not 0 < record_count <= _MAX_DRAW_RECORDS:
        raise DxRevisionUpgradeError(
            "invalid_draw_count", f"unreasonable rev131 draw record count {record_count}"
        )

    out = bytearray(draw_raw[:_DRAW_ENVELOPE_SIZE])
    records: list[dict[str, Any]] = []
    cursor = _DRAW_ENVELOPE_SIZE
    for record_index in range(record_count):
        old_start = cursor
        _require(draw_raw, cursor, _SHARED_DRAW_CORE_SIZE + _LEGACY_PREFIX_SIZE,
                 f"draw record {record_index}")
        core = draw_raw[cursor:cursor + _SHARED_DRAW_CORE_SIZE]
        tag, vertex_base, local_vertex_max, index_start, index_count = struct.unpack("<5I", core)
        if tag != 2:
            raise DxRevisionUpgradeError(
                "unsupported_draw_record",
                f"unsupported rev131 draw tag {tag} in flat record {record_index}; expected tag 2",
            )
        if index_count % 3:
            raise DxRevisionUpgradeError(
                "invalid_draw_index_count",
                f"draw record {record_index}: index count {index_count} is not divisible by 3",
            )
        if index_start > len(view.local_indices) or index_count > len(view.local_indices) - index_start:
            raise DxRevisionUpgradeError(
                "draw_index_range_out_of_bounds",
                f"draw record {record_index}: index range {index_start}+{index_count} exceeds "
                f"{len(view.local_indices)} local indices",
            )
        vertex_end = vertex_base + local_vertex_max
        if vertex_base >= len(view.positions) or vertex_end >= len(view.positions):
            raise DxRevisionUpgradeError(
                "draw_vertex_range_out_of_bounds",
                f"draw record {record_index}: vertex range {vertex_base}..{vertex_end} exceeds "
                f"{len(view.positions)} vertices",
            )
        local_values = view.local_indices[index_start:index_start + index_count]
        if local_values and max(local_values) > local_vertex_max:
            raise DxRevisionUpgradeError(
                "draw_local_index_out_of_range",
                f"draw record {record_index}: local index {max(local_values)} exceeds declared "
                f"maximum {local_vertex_max}",
            )

        prefix_start = cursor + _SHARED_DRAW_CORE_SIZE
        legacy = draw_raw[prefix_start:prefix_start + _LEGACY_PREFIX_SIZE]
        flag_a, flag_b, flag_c = legacy[:3]
        value_x, texture_slot_count = struct.unpack_from("<II", legacy, 3)
        if texture_slot_count > MAX_TEXTURE_SLOTS:
            raise DxRevisionUpgradeError(
                "invalid_texture_slot_count",
                f"draw record {record_index}: impossible texture-slot count {texture_slot_count}",
            )

        suffix_start = prefix_start + _LEGACY_PREFIX_SIZE
        suffix_cursor = suffix_start
        texture_values: list[bytes] = []
        for slot_index in range(texture_slot_count):
            _require(draw_raw, suffix_cursor, 4,
                     f"draw record {record_index} texture {slot_index} length")
            string_size = struct.unpack_from("<I", draw_raw, suffix_cursor)[0]
            suffix_cursor += 4
            if string_size > MAX_STRING_BYTES:
                raise DxRevisionUpgradeError(
                    "invalid_texture_reference_length",
                    f"draw record {record_index} texture {slot_index}: length {string_size} "
                    f"exceeds {MAX_STRING_BYTES}",
                )
            _require(draw_raw, suffix_cursor, string_size,
                     f"draw record {record_index} texture {slot_index} value")
            value = draw_raw[suffix_cursor:suffix_cursor + string_size]
            try:
                value.decode("ascii")
            except UnicodeDecodeError as exc:
                raise DxRevisionUpgradeError(
                    "invalid_texture_reference_encoding",
                    f"draw record {record_index} texture {slot_index}: reference is not ASCII",
                ) from exc
            texture_values.append(value)
            suffix_cursor += string_size

        _require(draw_raw, suffix_cursor, 4, f"draw record {record_index} terminal")
        terminal = struct.unpack_from("<I", draw_raw, suffix_cursor)[0]
        suffix_cursor += 4
        if terminal != 0:
            raise DxRevisionUpgradeError(
                "invalid_draw_terminal",
                f"draw record {record_index}: terminal is {terminal}, expected 0",
            )

        expanded_flags = bytes((flag_a, 0, flag_b, flag_c))
        new_prefix = struct.pack(
            "<IIf4sII", 1, 0, 1.0, expanded_flags, value_x, texture_slot_count
        )
        if len(new_prefix) != _REV135_PREFIX_SIZE:
            raise AssertionError("internal rev135 prefix size mismatch")

        out += core
        out += new_prefix
        out += draw_raw[suffix_start:suffix_cursor]
        records.append({
            "record_index": record_index,
            "source_relative_offset": old_start,
            "source_size": suffix_cursor - old_start,
            "output_relative_offset": len(out) - (suffix_cursor - old_start) - 13,
            "output_size": suffix_cursor - old_start + 13,
            "flags_before": [flag_a, flag_b, flag_c],
            "flags_after": list(expanded_flags),
            "preserved_x": value_x,
            "texture_slot_count": texture_slot_count,
            "texture_references": [value.decode("ascii") for value in texture_values],
        })
        cursor = suffix_cursor

    if cursor != len(draw_raw):
        raise DxRevisionUpgradeError(
            "unparsed_draw_region_bytes",
            f"rev131 draw region has {len(draw_raw) - cursor} unexplained trailing bytes",
        )
    return bytes(out), records


def _parse_revision135(data: bytes, source: str):
    if len(data) < 8:
        raise DxRevisionUpgradeError("truncated_header", f"DX header is truncated in {source}")
    magic, revision = struct.unpack_from("<2I", data)
    if magic != 0xD00D:
        raise DxRevisionUpgradeError(
            "invalid_magic", f"unsupported DX magic 0x{magic:08X} in {source}"
        )
    if revision != REVISION_135:
        raise DxRevisionUpgradeError(
            "unsupported_revision", f"expected revision 135, got {revision} in {source}"
        )
    try:
        return parse_dx_bytes(data, source)
    except (MasterRallyeError, struct.error, ValueError, OverflowError) as exc:
        raise DxRevisionUpgradeError(
            "canonical_parser_rejected_rev135",
            f"canonical parser rejected rev135 DX: {exc}",
        ) from exc


def _validate_rev135_structure(parsed, source: str) -> dict[str, Any]:
    """Validate the shared rev135 structure without imposing index order."""
    if parsed.word_0x04 != REVISION_135:
        raise DxRevisionUpgradeError(
            "output_revision_mismatch",
            f"canonical parser read revision {parsed.word_0x04}, expected 135",
        )
    if parsed.draw_table_preamble != 1:
        raise DxRevisionUpgradeError(
            "invalid_draw_preamble",
            f"rev135 draw table preamble is {parsed.draw_table_preamble}, expected 1 in {source}",
        )
    if not parsed.physical_draws:
        raise DxRevisionUpgradeError("empty_draw_table", f"rev135 DX has no physical draws in {source}")
    if parsed.global_index_table is None:
        raise DxRevisionUpgradeError("missing_global_index_table", f"rev135 DX has no global index table in {source}")
    if parsed.global_index_table.preamble != 1:
        raise DxRevisionUpgradeError(
            "invalid_global_index_preamble",
            f"rev135 global-index preamble is {parsed.global_index_table.preamble}, expected 1 in {source}",
        )
    if parsed.global_index_table.count != len(parsed.local_indices):
        raise DxRevisionUpgradeError(
            "global_index_count_mismatch",
            f"rev135 global-index count {parsed.global_index_table.count} does not match local index count "
            f"{len(parsed.local_indices)} in {source}",
        )
    if len(parsed.local_indices) % 3:
        raise DxRevisionUpgradeError("invalid_index_count", f"rev135 local index count is not triangular in {source}")

    finite_arrays = [
        ("position", parsed.vertices.positions),
        ("normal", parsed.vertices.normals),
        ("UV", tuple(value for uv_set in parsed.uv_sets for value in uv_set.values)),
    ]
    for label, rows in finite_arrays:
        if any(not math.isfinite(value) for row in rows for value in row):
            raise DxRevisionUpgradeError("nonfinite_geometry", f"rev135 {label} data contain a non-finite value in {source}")

    collision = parsed.collision
    if collision.errors or collision.warnings:
        details = list(collision.errors) + list(collision.warnings)
        raise DxRevisionUpgradeError(
            "collision_parser_diagnostics",
            "rev135 DX has collision diagnostics: " + "; ".join(details),
        )
    if collision.bsp is not None:
        raise DxRevisionUpgradeError(
            "unresolved_bsp_tail",
            f"rev135 DX contains raw tag-100 BSP bytes whose remaining tail boundary is unresolved in {source}",
        )
    if collision.unparsed_data:
        bounds = collision.spatial_bounds_1339
        if bounds is None or bounds.raw != collision.unparsed_data:
            raise DxRevisionUpgradeError(
                "unresolved_collision_tail",
                f"rev135 DX has trailing collision bytes that are not a validated marker-1339 block in {source}",
            )

    if parsed.diagnostics.warnings:
        raise DxRevisionUpgradeError(
            "parser_warnings",
            "rev135 DX has structural parser warnings: " + "; ".join(parsed.diagnostics.warnings),
        )

    return {
        "revision": parsed.word_0x04,
        "draw_count": len(parsed.physical_draws),
        "vertex_count": parsed.vertex_count,
        "triangle_count": parsed.triangle_count,
        "collision_tags": list(collision.tag_ids),
        "collision_tail": (
            "marker-1339-validated" if collision.unparsed_data else "none"
        ),
        "parser_warnings": [],
        "collision_errors": [],
        "collision_warnings": [],
    }


def _oriented_triangle_key(triangle: tuple[int, int, int]) -> tuple[int, int, int]:
    """Canonicalize cyclic corner rotation while retaining triangle winding."""
    a, b, c = triangle
    return min((a, b, c), (b, c, a), (c, a, b))


def _analyze_global_index_order(parsed, source: str) -> dict[str, Any]:
    table = parsed.global_index_table
    if table is None:  # Defensive; common structural validation checks this first.
        raise DxRevisionUpgradeError("missing_global_index_table", f"rev135 DX has no global table in {source}")
    index_count = len(parsed.local_indices)
    owners = [0] * index_count
    expected_positions: list[int | None] = [None] * index_count
    per_draw: list[dict[str, Any]] = []
    for draw in parsed.physical_draws:
        start, count = draw.index_start, draw.index_count
        if count % 3:
            raise DxRevisionUpgradeError(
                "invalid_draw_index_count", f"draw {draw.record_path} count {count} is not divisible by 3 in {source}"
            )
        if start > index_count or count > index_count - start:
            raise DxRevisionUpgradeError(
                "draw_index_range_out_of_bounds", f"draw {draw.record_path} index range exceeds local array in {source}"
            )
        if draw.vertex_base >= parsed.vertex_count or draw.vertex_base + draw.local_vertex_max >= parsed.vertex_count:
            raise DxRevisionUpgradeError(
                "draw_vertex_range_out_of_bounds", f"draw {draw.record_path} vertex range exceeds geometry in {source}"
            )
        local = parsed.local_indices[start:start + count]
        if local and max(local) > draw.local_vertex_max:
            raise DxRevisionUpgradeError(
                "draw_local_index_out_of_range", f"draw {draw.record_path} local index exceeds its vertex range in {source}"
            )
        expected = parsed.draw_global_indices(draw)
        if len(expected) != count:
            raise DxRevisionUpgradeError(
                "invalid_reconstructed_draw_count", f"draw {draw.record_path} reconstruction is incomplete in {source}"
            )
        for relative, value in enumerate(expected):
            position = start + relative
            owners[position] += 1
            if expected_positions[position] is None:
                expected_positions[position] = value
            elif expected_positions[position] != value:
                raise DxRevisionUpgradeError(
                    "conflicting_draw_ownership", f"overlapping draws disagree at global index {position} in {source}"
                )

        actual = table.indices[start:start + count]
        expected_triangles = [tuple(expected[i:i + 3]) for i in range(0, count, 3)]
        actual_triangles = [tuple(actual[i:i + 3]) for i in range(0, len(actual), 3)]
        if len(actual) != count:
            raise DxRevisionUpgradeError(
                "truncated_global_index_range", f"draw {draw.record_path} global-index range is truncated in {source}"
            )
        topology_equal = Counter(map(_oriented_triangle_key, expected_triangles)) == Counter(
            map(_oriented_triangle_key, actual_triangles)
        )
        per_draw.append({
            "draw_index": draw.draw_index,
            "index_start": start,
            "index_count": count,
            "triangle_count": count // 3,
            "oriented_triangle_multiset_equal": topology_equal,
        })
        if not topology_equal:
            raise DxRevisionUpgradeError(
                "global_index_topology_mismatch",
                f"rev135 draw {draw.record_path} local/global oriented triangle sets differ in {source}",
            )

    if any(owner != 1 for owner in owners):
        raise DxRevisionUpgradeError(
            "draw_index_coverage_invalid",
            f"rev135 draws do not cover every local index exactly once in {source}",
        )
    if any(value is None for value in expected_positions):
        raise DxRevisionUpgradeError("draw_index_coverage_invalid", f"rev135 draw coverage has gaps in {source}")

    expected_indices = tuple(int(value) for value in expected_positions)
    mismatches = [
        index for index, (expected, stored) in enumerate(zip(expected_indices, table.indices))
        if expected != stored
    ]
    sequence_equal = not mismatches
    expected_parser_error = None
    if mismatches:
        expected_parser_error = (
            f"stored global indices differ at {len(mismatches)} covered positions; first 0x{mismatches[0]:X}"
        )
    if bool(parsed.diagnostics.reconstructed_global_match) != sequence_equal:
        raise DxRevisionUpgradeError(
            "parser_global_validation_disagreement",
            f"canonical parser and independent global-index check disagree in {source}",
        )
    return {
        "sequence_equal": sequence_equal,
        "ordering_divergence": not sequence_equal,
        "oriented_triangle_sets_equal_per_draw": True,
        "mismatched_index_positions": len(mismatches),
        "first_mismatch_position": mismatches[0] if mismatches else None,
        "expected_parser_order_error": expected_parser_error,
        "per_draw": per_draw,
    }


def _validate_generated_model(parsed, source: str) -> dict[str, Any]:
    structure = _validate_rev135_structure(parsed, source)
    index_analysis = _analyze_global_index_order(parsed, source)
    if parsed.diagnostics.errors or not parsed.diagnostics.reconstructed_global_match:
        raise DxRevisionUpgradeError(
            "generated_global_index_mismatch",
            "generated rev135 output must have exact local/global index ordering consistency",
        )
    return {
        "status": "PASS",
        "policy": "GENERATED_REV135_STRICT",
        **structure,
        "global_index_validation": index_analysis,
        "parser_errors": [],
    }


def validate_generated_rev135(data: bytes, source: str = "<bytes>") -> dict[str, Any]:
    """Apply strict validation to output freshly generated by this upgrader.

    Generated bytes must retain the exact rev131 local/global sequence. The
    stricter rule is guaranteed by the converter's own preservation contract.
    """
    parsed = _parse_revision135(data, source)
    return _validate_generated_model(parsed, source)


def validate_existing_rev135(data: bytes, source: str = "<bytes>") -> dict[str, Any]:
    """Validate external rev135 input, allowing only proven order divergence.

    An official 9.10.0 vehicle may reorder local triangles while retaining the
    prior global-index order. That is accepted only when each draw's oriented
    triangle multiset still matches and all other parser/geometry/collision
    checks are clean.
    """
    parsed = _parse_revision135(data, source)
    structure = _validate_rev135_structure(parsed, source)
    index_analysis = _analyze_global_index_order(parsed, source)
    errors = parsed.diagnostics.errors
    if index_analysis["sequence_equal"]:
        if errors:
            raise DxRevisionUpgradeError(
                "unexpected_parser_errors", "rev135 DX has parser errors: " + "; ".join(errors)
            )
    elif errors != [index_analysis["expected_parser_order_error"]]:
        raise DxRevisionUpgradeError(
            "unexpected_parser_errors",
            "rev135 DX has parser errors beyond the recognized local/global ordering divergence: "
            + "; ".join(errors),
        )
    return {
        "status": "VALID_WITH_ORDERING_DIVERGENCE" if index_analysis["ordering_divergence"] else "VALID",
        "policy": "EXISTING_REV135_STRUCTURAL",
        **structure,
        "global_index_validation": index_analysis,
        "parser_errors": list(errors),
    }


def _verify_preservation(source_view: DemoDxView, output_view: DemoDxView,
                         source: bytes, output: bytes,
                         records: list[dict[str, Any]]) -> dict[str, bool]:
    source_collision = source[source_view.collision.offset:]
    output_collision = output[output_view.collision.offset:]
    source_global = source[source_view.global_offset:source_view.collision.offset]
    output_global = output[output_view.global_offset:output_view.collision.offset]
    source_header = struct.unpack_from("<4I", source)
    output_header = struct.unpack_from("<4I", output)
    prefix_matches = True
    core_and_suffixes_match = True
    for record in records:
        source_start = source_view.draw_offset + record["source_relative_offset"]
        output_start = output_view.draw_offset + record["output_relative_offset"]
        source_prefix = source[source_start + _SHARED_DRAW_CORE_SIZE:
                               source_start + _SHARED_DRAW_CORE_SIZE + _LEGACY_PREFIX_SIZE]
        output_prefix = output[output_start + _SHARED_DRAW_CORE_SIZE:
                               output_start + _SHARED_DRAW_CORE_SIZE + _REV135_PREFIX_SIZE]
        if len(source_prefix) != _LEGACY_PREFIX_SIZE or len(output_prefix) != _REV135_PREFIX_SIZE:
            prefix_matches = False
        else:
            a, b, c = source_prefix[:3]
            x, slots = struct.unpack_from("<II", source_prefix, 3)
            expected = struct.pack("<IIf4sII", 1, 0, 1.0, bytes((a, 0, b, c)), x, slots)
            prefix_matches &= output_prefix == expected
        suffix_size = record["source_size"] - _SHARED_DRAW_CORE_SIZE - _LEGACY_PREFIX_SIZE
        core_and_suffixes_match &= (
            source[source_start:source_start + _SHARED_DRAW_CORE_SIZE]
            == output[output_start:output_start + _SHARED_DRAW_CORE_SIZE]
            and source[source_start + _SHARED_DRAW_CORE_SIZE + _LEGACY_PREFIX_SIZE:
                       source_start + _SHARED_DRAW_CORE_SIZE + _LEGACY_PREFIX_SIZE + suffix_size]
            == output[output_start + _SHARED_DRAW_CORE_SIZE + _REV135_PREFIX_SIZE:
                      output_start + _SHARED_DRAW_CORE_SIZE + _REV135_PREFIX_SIZE + suffix_size]
        )
    source_pre_draw = bytearray(source[:source_view.draw_offset])
    source_pre_draw[4:8] = output[4:8]
    checks = {
        "header_except_revision_preserved": (
            source_header[0] == output_header[0]
            and source_header[2:] == output_header[2:]
            and output_header[1] == REVISION_135
        ),
        "all_pre_draw_bytes_except_revision_preserved": bytes(source_pre_draw) == output[:output_view.draw_offset],
        "draw_prefix_formula_verified": prefix_matches,
        "draw_cores_and_texture_suffixes_preserved": core_and_suffixes_match,
        "positions_preserved": source_view.positions == output_view.positions,
        "normals_preserved": source_view.normals == output_view.normals,
        "colors_preserved": source_view.colors == output_view.colors,
        "uv_sets_preserved": source_view.uv_sets == output_view.uv_sets,
        "local_index_order_preserved": source_view.local_indices == output_view.local_indices,
        "global_index_bytes_preserved": source_global == output_global,
        "collision_bytes_preserved": source_collision == output_collision,
        "collision_tags_preserved": source_view.collision.tag_ids == output_view.collision.tag_ids,
        "output_size_matches_prefix_growth": len(output) == len(source) + len(records) * 13,
        "global_table_reconstructs": True,
    }
    return checks


def upgrade_dx_131_to_135_with_report(
    data: bytes,
    source: str = "<bytes>",
) -> tuple[bytes, dict[str, Any]]:
    """Convert a supported revision-131 vehicle DX and return evidence report.

    The output is produced only from ``data``. Official revision-135 assets are
    never read or consulted. Unsupported or ambiguous layouts fail closed.
    """
    source_view = _inspect_source(data, source)
    upgraded_draws, records = _upgrade_draw_region(source_view.draw_raw, source_view)
    output = bytearray(data[:source_view.draw_offset])
    struct.pack_into("<I", output, 4, REVISION_135)
    output += upgraded_draws
    output += data[source_view.global_offset:]
    result = bytes(output)

    output_source = f"{source} [rev131-to-135]"
    parsed = _parse_revision135(result, output_source)
    output_validation = _validate_generated_model(parsed, output_source)
    try:
        output_view = inspect_demo_dx(result, f"{source} [rev131-to-135]")
    except (BoundsError, FormatError) as exc:
        raise DxRevisionUpgradeError(
            "output_structural_validation_failed",
            f"generated output failed demo DX structural validation: {exc}",
        ) from exc
    if len(parsed.physical_draws) != len(records):
        raise DxRevisionUpgradeError(
            "output_draw_count_mismatch",
            f"output parser found {len(parsed.physical_draws)} draws; transformed {len(records)}",
        )
    checks = _verify_preservation(source_view, output_view, data, result, records)
    checks["global_table_reconstructs"] = parsed.diagnostics.reconstructed_global_match
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise DxRevisionUpgradeError(
            "preservation_check_failed",
            "conversion failed preservation checks: " + ", ".join(failed),
        )

    report: dict[str, Any] = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "PASS",
        "source_path": source,
        "source_sha256": _sha256(data),
        "source_size": len(data),
        "source_revision": REVISION_131,
        "output_sha256": _sha256(result),
        "output_size": len(result),
        "output_revision": REVISION_135,
        "draw_records_transformed": len(records),
        "draw_record_size_growth_bytes": len(result) - len(data),
        "draw_prefix_transform": "A B C + u32 X + u32 slot_count -> "
        "u32(1) + u32(0) + float32(1.0) + A 00 B C + u32 X + u32 slot_count",
        "geometry_preserved": all(checks[name] for name in (
            "positions_preserved", "normals_preserved", "colors_preserved", "uv_sets_preserved"
        )),
        "local_index_order_preserved": checks["local_index_order_preserved"],
        "collision_preserved": checks["collision_bytes_preserved"],
        "global_index_table_preserved": checks["global_index_bytes_preserved"],
        "trailing_data_preserved": (
            checks["global_index_bytes_preserved"] and checks["collision_bytes_preserved"]
        ),
        "preservation_checks": checks,
        "parser_validation": {
            **output_validation,
            "global_index_reconstruction_match": parsed.diagnostics.reconstructed_global_match,
        },
        "evidence_profile": "STATICALLY_SUPPORTED",
        "runtime_evidence": {
            "validated_families": ["Trooper", "Forester"],
            "individual_output_runtime_status": "NOT_ASSESSED_BY_CONVERTER",
            "triangle_optimizer_reproduced": False,
        },
        "records": records,
    }
    return result, report


def upgrade_dx_131_to_135(data: bytes, source: str = "<bytes>") -> bytes:
    """Compatibility API returning only converted bytes."""
    result, _report = upgrade_dx_131_to_135_with_report(data, source)
    return result
