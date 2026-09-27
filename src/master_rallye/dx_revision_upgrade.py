"""Research-only rev131 to rev135 DX draw-prefix prototype.

This implements only the byte mapping verified on paired Trooper car,
complete, and wheel outputs. It deliberately preserves local triangle/index
order and every non-prefix source byte (apart from the revision word).
"""
from __future__ import annotations

import struct

from .demo_dx import inspect_demo_dx
from .dx import MAX_TEXTURE_SLOTS, parse_dx_bytes
from .errors import BoundsError, FormatError

REVISION_131 = 131
REVISION_135 = 135
_DRAW_ENVELOPE_SIZE = 8
_SHARED_DRAW_CORE_SIZE = 20
_LEGACY_PREFIX_SIZE = 11
_REV135_PREFIX_SIZE = 24
_MAX_DRAW_RECORDS = 100_000


def _require(data: bytes, offset: int, size: int, label: str) -> None:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise BoundsError(f"truncated rev131 {label} at 0x{offset:X} (need {size} bytes)")


def _upgrade_draw_region(draw_raw: bytes) -> bytes:
    _require(draw_raw, 0, _DRAW_ENVELOPE_SIZE, "draw envelope")
    preamble, record_count = struct.unpack_from("<II", draw_raw)
    if preamble != 1:
        raise FormatError(f"unsupported rev131 draw preamble {preamble}, expected 1")
    if not 0 < record_count <= _MAX_DRAW_RECORDS:
        raise FormatError(f"unreasonable rev131 draw record count {record_count}")

    out = bytearray(draw_raw[:_DRAW_ENVELOPE_SIZE])
    cursor = _DRAW_ENVELOPE_SIZE
    for record_index in range(record_count):
        _require(draw_raw, cursor, _SHARED_DRAW_CORE_SIZE + _LEGACY_PREFIX_SIZE,
                 f"draw record {record_index}")
        core = draw_raw[cursor:cursor + _SHARED_DRAW_CORE_SIZE]
        tag = struct.unpack_from("<I", core)[0]
        if tag != 2:
            raise FormatError(
                f"unsupported rev131 draw tag {tag} in flat record {record_index}"
            )

        prefix_start = cursor + _SHARED_DRAW_CORE_SIZE
        legacy = draw_raw[prefix_start:prefix_start + _LEGACY_PREFIX_SIZE]
        flag_a, flag_b, flag_c = legacy[:3]
        value_x, texture_slot_count = struct.unpack_from("<II", legacy, 3)
        if texture_slot_count > MAX_TEXTURE_SLOTS:
            raise FormatError(
                f"draw record {record_index}: unreasonable texture slot count "
                f"{texture_slot_count}"
            )

        suffix_start = prefix_start + _LEGACY_PREFIX_SIZE
        suffix_cursor = suffix_start
        for slot_index in range(texture_slot_count):
            _require(draw_raw, suffix_cursor, 4,
                     f"draw record {record_index} texture {slot_index} length")
            string_size = struct.unpack_from("<I", draw_raw, suffix_cursor)[0]
            suffix_cursor += 4
            _require(draw_raw, suffix_cursor, string_size,
                     f"draw record {record_index} texture {slot_index} value")
            suffix_cursor += string_size

        _require(draw_raw, suffix_cursor, 4, f"draw record {record_index} terminal")
        terminal = struct.unpack_from("<I", draw_raw, suffix_cursor)[0]
        suffix_cursor += 4
        if terminal != 0:
            raise FormatError(
                f"draw record {record_index}: terminal is {terminal}, expected 0"
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
        cursor = suffix_cursor

    if cursor != len(draw_raw):
        raise FormatError(
            f"rev131 draw region has {len(draw_raw) - cursor} unexplained trailing bytes"
        )
    return bytes(out)


def upgrade_dx_131_to_135(data: bytes, source: str = "<bytes>") -> bytes:
    """Build an experimental rev135 candidate from one rev131 DX byte stream.

    Only the revision word and each observed flat tag-2 draw prefix are
    rewritten. The function refuses unsupported draw grammars, malformed
    records, non-131 inputs, and output that fails the canonical rev135 parser
    or its structural diagnostics. It never reads official rev135 bytes.
    """
    view = inspect_demo_dx(data, source)
    if view.header[1] != REVISION_131:
        raise FormatError(
            f"expected DX revision {REVISION_131}, got {view.header[1]} in {source}"
        )

    upgraded_draws = _upgrade_draw_region(view.draw_raw)
    output = bytearray(data[:view.draw_offset])
    struct.pack_into("<I", output, 4, REVISION_135)
    output += upgraded_draws
    output += data[view.global_offset:]
    result = bytes(output)

    # Parsing is validation only; no parsed or official rev135 bytes are used
    # to produce the candidate.
    parsed = parse_dx_bytes(result, f"{source} [rev131-to-135 prototype]")
    if parsed.word_0x04 != REVISION_135:
        raise FormatError("canonical parser did not retain revision 135")
    if parsed.diagnostics.errors:
        joined = "; ".join(parsed.diagnostics.errors)
        raise FormatError(f"candidate failed canonical DX validation: {joined}")
    return result
