"""Fail-closed revision-131 vehicle DX conversion to revision 135.

The supported transformation is limited to the observed flat vehicle draw
grammar. It expands each 11-byte legacy prefix into the evidenced 24-byte
revision-135 prefix and preserves local triangle order and all other source
payloads. It does not reproduce the 9.10.0 triangle optimizer.
"""
from __future__ import annotations

import hashlib
import struct
from typing import Any

from . import __version__
from .demo_dx import DemoDxView, inspect_demo_dx
from .dx import MAX_STRING_BYTES, MAX_TEXTURE_SLOTS, parse_dx_bytes
from .errors import BoundsError, FormatError

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


def _parser_result(result: bytes, source: str):
    try:
        parsed = parse_dx_bytes(result, source)
    except (BoundsError, FormatError) as exc:
        raise DxRevisionUpgradeError(
            "canonical_parser_rejected_output",
            f"canonical parser rejected generated rev135 DX: {exc}",
        ) from exc
    if parsed.word_0x04 != REVISION_135:
        raise DxRevisionUpgradeError(
            "output_revision_mismatch",
            f"canonical parser read revision {parsed.word_0x04}, expected 135",
        )
    if parsed.diagnostics.errors or parsed.diagnostics.warnings:
        details = parsed.diagnostics.errors + parsed.diagnostics.warnings
        raise DxRevisionUpgradeError(
            "output_parser_diagnostics",
            "generated rev135 DX has parser diagnostics: " + "; ".join(details),
        )
    if parsed.collision.errors or parsed.collision.warnings:
        details = list(parsed.collision.errors) + list(parsed.collision.warnings)
        raise DxRevisionUpgradeError(
            "output_collision_diagnostics",
            "generated rev135 DX has collision diagnostics: " + "; ".join(details),
        )
    if parsed.global_index_table is None or not parsed.diagnostics.reconstructed_global_match:
        raise DxRevisionUpgradeError(
            "output_global_index_validation_failed",
            "generated rev135 DX has no validated matching global index table",
        )
    return parsed


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

    parsed = _parser_result(result, f"{source} [rev131-to-135]")
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
            "status": "PASS",
            "revision": parsed.word_0x04,
            "draw_count": len(parsed.physical_draws),
            "vertex_count": parsed.vertex_count,
            "triangle_count": parsed.triangle_count,
            "collision_tags": list(parsed.collision.tag_ids),
            "global_index_reconstruction_match": parsed.diagnostics.reconstructed_global_match,
            "errors": list(parsed.diagnostics.errors),
            "warnings": list(parsed.diagnostics.warnings),
            "collision_errors": list(parsed.collision.errors),
            "collision_warnings": list(parsed.collision.warnings),
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


def validate_revision_135(data: bytes, source: str = "<bytes>") -> dict[str, Any]:
    """Validate a revision-135 file for unchanged directory-mode copying."""
    if len(data) < 8:
        raise DxRevisionUpgradeError("truncated_header", f"DX header is truncated in {source}")
    magic, revision = struct.unpack_from("<2I", data)
    if magic != 0xD00D:
        raise DxRevisionUpgradeError("invalid_magic", f"unsupported DX magic in {source}")
    if revision != REVISION_135:
        raise DxRevisionUpgradeError(
            "unsupported_revision", f"expected revision 135 for unchanged copy, got {revision} in {source}"
        )
    parsed = _parser_result(data, source)
    return {
        "status": "COPIED_UNCHANGED",
        "source_revision": REVISION_135,
        "output_revision": REVISION_135,
        "draw_records_transformed": 0,
        "source_sha256": _sha256(data),
        "output_sha256": _sha256(data),
        "source_size": len(data),
        "output_size": len(data),
        "parser_validation": {
            "status": "PASS",
            "revision": parsed.word_0x04,
            "draw_count": len(parsed.physical_draws),
            "vertex_count": parsed.vertex_count,
            "triangle_count": parsed.triangle_count,
            "collision_tags": list(parsed.collision.tag_ids),
            "global_index_reconstruction_match": parsed.diagnostics.reconstructed_global_match,
            "errors": list(parsed.diagnostics.errors),
            "warnings": list(parsed.diagnostics.warnings),
            "collision_errors": list(parsed.collision.errors),
            "collision_warnings": list(parsed.collision.warnings),
        },
        "individual_output_runtime_status": "NOT_ASSESSED_BY_CONVERTER",
    }
