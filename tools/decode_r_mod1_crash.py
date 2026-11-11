#!/usr/bin/env python3
"""Decode the optional fixed-size R-MOD1 first-chance AV diagnostic log."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


MAGIC = b"RMCRASH1"
RECORD = struct.Struct("<8s9I15I10I2I3i2I2i32I32I")
PHASES = {
    0: "idle",
    1: "start_guard_entered",
    2: "start_blocked",
    3: "start_allowed",
    4: "native_setup_call_armed",
    5: "native_setup_returned",
    6: "prepared_validation_entered",
    7: "prepared_validation_accepted",
    8: "prepared_validation_rejected",
}
KINDS = {1: "session", 2: "access_violation_first_chance", 3: "access_violation_unhandled"}


def decode_bytes(data: bytes) -> list[dict[str, object]]:
    if len(data) % RECORD.size:
        raise ValueError(f"truncated record stream: {len(data)} bytes is not a multiple of {RECORD.size}")
    rows = []
    for offset in range(0, len(data), RECORD.size):
        values = RECORD.unpack_from(data, offset)
        if values[0] != MAGIC or values[1] != RECORD.size:
            raise ValueError(f"invalid record signature/size at offset {offset:#x}")
        cursor = 2
        row: dict[str, object] = {
            "sequence": values[cursor], "process_id": values[cursor + 1],
            "thread_id": values[cursor + 2], "kind": KINDS.get(values[cursor + 3], "unknown"),
            "exception_code": values[cursor + 4], "exception_flags": values[cursor + 5],
            "exception_address": values[cursor + 6], "parameter_count": values[cursor + 7],
        }
        cursor += 8
        information = list(values[cursor:cursor + 15])
        row["exception_information"] = information[:min(int(row["parameter_count"]), 15)]
        cursor += 15
        context_names = ("eip", "esp", "ebp", "eax", "ebx", "ecx", "edx", "esi", "edi", "eflags")
        row.update(zip(context_names, values[cursor:cursor + 10]))
        cursor += 10
        row["start_phase"] = values[cursor]
        row["start_phase_name"] = PHASES.get(values[cursor], "unknown")
        row["config_flags"] = values[cursor + 1]
        row["opponent_count"] = values[cursor + 2]
        row["track"] = values[cursor + 3]
        row["mode"] = values[cursor + 4]
        row["ghost"] = values[cursor + 5]
        row["split_screen"] = values[cursor + 6]
        row["player_id"] = values[cursor + 7]
        row["player_class"] = values[cursor + 8]
        cursor += 9
        row["stack_words"] = list(values[cursor:cursor + 32])
        cursor += 32
        frame_words = values[cursor:cursor + 32]
        row["frames"] = [
            {"ebp": frame_words[index], "return_address": frame_words[index + 1]}
            for index in range(0, len(frame_words), 2)
            if frame_words[index] or frame_words[index + 1]
        ]
        row["offset"] = offset
        rows.append(row)
    return rows


def decode(path: Path) -> list[dict[str, object]]:
    return decode_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = decode(args.record)
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        else:
            print(rendered, end="")
        return 0
    except (OSError, ValueError) as error:
        parser.error(str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
