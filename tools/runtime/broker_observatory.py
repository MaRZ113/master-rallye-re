"""Read-only capture, parse, and diff for Master Rallye's Broker Debug→Dump.

The live capture path reads only the retail process's existing Debug text
buffer with PROCESS_QUERY_INFORMATION | PROCESS_VM_READ. It never sends game
input, suspends the process, or writes process memory.
"""

from __future__ import annotations

import argparse
import hashlib
import csv
import math
import json
import os
import re
import struct
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from observatory_version import VERSION
from observatory_build_profiles import RETAIL_PRISTINE, ObservatoryBuildProfile, match_profile
import observatory_compatibility as compatibility


RETAIL_SHA256 = RETAIL_PRISTINE.sha256  # compatibility aliases; not selection gates
RETAIL_SIZE = RETAIL_PRISTINE.file_size
RETAIL_IMAGE_BASE = 0x00400000
ACTIVE_LOG_SINK_RVA = RETAIL_PRISTINE.active_log_sink_rva
DEBUG_SINK_VTABLE_RVA = RETAIL_PRISTINE.debug_sink_vtable_rva
DEBUG_SINK_OBJECT_SIZE = 0x30
DEBUG_BUFFER_MAX_BYTES = 128 * 1024 * 1024
CAPTURE_RETRIES = 5
SNAPSHOT_SCHEMA_VERSION = 1

ENTRY_TYPES = (
    "MarkerListName",
    "XmlFilename",
    "StringList",
    "nuVector4",
    "nuVector3",
    "nuVector2",
    "xmlData",
    "Matrix",
    "Bool",
    "Float",
    "Int",
    "String",
)
ENTRY_TYPES = tuple(sorted(ENTRY_TYPES, key=len, reverse=True))

HEADER_RE = re.compile(r"^enBroker\(Size\s+(\d+)\s+Capacity\s+(\d+)\)$")
ENTRY_RE = re.compile(
    r"^\[Rev=(-?\d+)\]\s+\[ID=(.*?)\]\s+\[Save:\s*S=([TF])\s*,\s*O=([TF])\s*,\s*PS=([TF])\]\s+"
    r"\[SaveFile=(.*?)\]\s+(.*)$"
)
FILENAME_HEADER_RE = re.compile(r"^enBroker FilenamesList Num entries\s*=\s*(\d+)$")
SUMMARY_RE = {
    "global": re.compile(r"^NUM BROKER ENTRIES:\s*GLOBAL\s*\[(\d+)\]$"),
    "scene": re.compile(r"^NUM BROKER ENTRIES:\s*SCENE\s*\[(\d+)\]$"),
    "user": re.compile(r"^NUM BROKER ENTRIES:\s*USER\s*\[(\d+)\]$"),
    "total": re.compile(r"^NUM BROKER ENTRIES:\s*TOTAL\s*\[(\d+)\]$"),
}
FLOAT_RE = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")


class ObservatoryError(RuntimeError):
    """Input or safety validation failed; no game memory was written."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decode(raw: bytes) -> str:
    # The retail logger uses ANSI strings. cp1252 plus surrogateescape keeps
    # otherwise undefined bytes reversible; the raw sidecar remains canonical.
    return raw.decode("cp1252", errors="surrogateescape")


def _raw_lines(raw: bytes) -> tuple[list[str], list[int], list[bytes]]:
    chunks = raw.split(b"\n")
    offsets: list[int] = []
    lines: list[str] = []
    starts: list[int] = []
    cursor = 0
    for chunk in chunks:
        starts.append(cursor)
        offsets.append(cursor + len(chunk))
        line = chunk[:-1] if chunk.endswith(b"\r") else chunk
        lines.append(_decode(line))
        cursor += len(chunk) + 1
    return lines, starts, chunks


def _trim_control(line: str) -> str:
    return line.strip()


def _typed_tail(tail: str) -> tuple[str, str, str, str | None]:
    for type_name in ENTRY_TYPES:
        marker = f"({type_name})"
        index = tail.rfind(marker)
        if index > 0 and tail[index - 1].isspace():
            path = tail[:index].rstrip()
            remainder = tail[index + len(marker) :]
            if "=" in remainder:
                _formatting, value = remainder.split("=", 1)
                value_display = value.strip()
            else:
                value_display = ""
            return path, type_name, remainder, value_display

    # Retain future/unknown types as diagnostics rather than dropping their row.
    match = re.match(r"^(.*?\S)\s+\(([^()]+)\)(.*)$", tail)
    if match:
        remainder = match.group(3)
        value = remainder.split("=", 1)[1].strip() if "=" in remainder else ""
        return match.group(1), f"UNKNOWN:{match.group(2)}", remainder, value
    return tail.rstrip(), "UNKNOWN_FORMAT", "", None


def _typed_value(type_name: str, raw_value: str, continuation: Sequence[str]) -> Any:
    """Decode only representations whose text form is unambiguous enough."""
    if type_name == "Bool":
        lowered = raw_value.strip().casefold()
        if lowered in {"true", "false"}:
            return lowered == "true"
    elif type_name == "Int":
        try:
            return int(raw_value.strip(), 10)
        except ValueError:
            pass
    elif type_name == "Float":
        try:
            number = float(raw_value.strip())
            if math.isfinite(number):
                return number
        except ValueError:
            pass
    elif type_name in {"nuVector2", "nuVector3", "nuVector4"}:
        expected = {"nuVector2": 2, "nuVector3": 3, "nuVector4": 4}[type_name]
        numbers = [float(match.group(0)) for match in FLOAT_RE.finditer(raw_value)]
        if len(numbers) == expected and all(math.isfinite(number) for number in numbers):
            return numbers
    elif type_name == "Matrix":
        numbers = [float(match.group(0)) for line in continuation for match in FLOAT_RE.finditer(line)]
        if len(numbers) == 16 and all(math.isfinite(number) for number in numbers):
            return numbers
    elif type_name in {"String", "MarkerListName", "XmlFilename"}:
        if len(raw_value) >= 2 and raw_value.startswith('"') and raw_value.endswith('"'):
            return raw_value[1:-1]
        return raw_value
    elif type_name == "StringList":
        return [line.strip() for line in continuation if line.strip() not in {"{", "}"}]
    elif type_name == "xmlData":
        return raw_value if raw_value else None
    return raw_value


def _parse_entry(line: str, ordinal: int) -> dict[str, Any] | None:
    visible = line.lstrip()
    match = ENTRY_RE.match(visible)
    if not match:
        return None
    revision, broker_id, save_s, save_o, save_ps, save_file, tail = match.groups()
    broker_id = broker_id.strip()
    path, type_name, remainder, value = _typed_tail(tail)
    if broker_id == "GLOBAL":
        scope_label = "GLOBAL"
    elif broker_id == "SCENE":
        scope_label = "SCENE"
    else:
        # 00601D00 sends all remaining scope-tag values through its USER branch.
        scope_label = "USER"
    return {
        "ordinal": ordinal,
        "occurrence": None,
        "revision": int(revision),
        # Exact display text after ID=. It is not the interned string-table ID
        # for this broker path, which the dump does not print separately.
        "broker_id": broker_id,
        "scope_label": scope_label,
        "path": path,
        "type": type_name,
        "value": value,
        "value_raw": value if value is not None else "",
        "value_raw_remainder": remainder,
        "save_flags": {"S": save_s == "T", "O": save_o == "T", "PS": save_ps == "T"},
        "save_game": save_s == "T",
        "save_options": save_o == "T",
        "save_player_state": save_ps == "T",
        "save_file": save_file,
        "raw_first_line": line,
        "continuation_lines": [],
    }


def _find_summary(lines: list[str], start: int, limit: int) -> tuple[dict[str, int], dict[str, int]]:
    values: dict[str, int] = {}
    indices: dict[str, int] = {}
    for name, pattern in SUMMARY_RE.items():
        for i in range(start, limit):
            match = pattern.match(_trim_control(lines[i]))
            if match:
                values[name] = int(match.group(1))
                indices[name] = i
                break
    return values, indices


def _attempt_block(
    raw: bytes,
    lines: list[str],
    starts: list[int],
    chunks: list[bytes],
    header_index: int,
    limit: int,
) -> tuple[dict[str, Any] | None, str]:
    header_match = HEADER_RE.match(_trim_control(lines[header_index]))
    if not header_match:
        return None, "unrecognized broker header"
    reported_size, reported_capacity = map(int, header_match.groups())
    body_open = next(
        (i for i in range(header_index + 1, min(header_index + 4, limit)) if _trim_control(lines[i]) == "{"),
        None,
    )
    if body_open is None:
        return None, "broker body opening brace is absent"
    summary, summary_indices = _find_summary(lines, header_index + 1, limit)
    if set(summary) != set(SUMMARY_RE):
        return None, "one or more broker scope totals are absent"
    summary_start = min(summary_indices.values())
    if summary_indices["total"] < max(summary_indices[k] for k in ("global", "scene", "user")):
        return None, "TOTAL line precedes a scope subtotal"

    entry_lines: list[tuple[int, dict[str, Any]]] = []
    malformed: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for i in range(body_open + 1, summary_start):
        parsed = _parse_entry(lines[i], len(entry_lines))
        if parsed is not None:
            if parsed["type"] in {"UNKNOWN_FORMAT"}:
                malformed.append({"line": i + 1, "text": lines[i], "reason": "entry type/path parse failed"})
            if parsed["type"].startswith("UNKNOWN:"):
                malformed.append({"line": i + 1, "text": lines[i], "reason": "unrecognized entry type"})
            current = parsed
            entry_lines.append((i, parsed))
        elif lines[i].lstrip().startswith("[Rev="):
            malformed.append({"line": i + 1, "text": lines[i], "reason": "entry-like row failed header parse"})
            if current is not None:
                current["continuation_lines"].append(lines[i])
        elif current is not None and lines[i] != "":
            current["continuation_lines"].append(lines[i])

    if malformed:
        samples = "; ".join(
            f"line {item['line']}: {item['reason']}: {item['text'][:160]!r}" for item in malformed[:3]
        )
        return None, f"{len(malformed)} malformed/unknown entry row(s): {samples}"
    if len(entry_lines) != summary["total"]:
        return None, f"parsed {len(entry_lines)} rows but Dump reports {summary['total']}"
    if summary["global"] + summary["scene"] + summary["user"] != summary["total"]:
        return None, "scope subtotals do not sum to TOTAL"

    # The broker body has a close brace after TOTAL, followed by a second
    # filename-list block. Match its stated item count before accepting it.
    body_close = next(
        (i for i in range(summary_indices["total"] + 1, limit) if _trim_control(lines[i]) == "}"),
        None,
    )
    if body_close is None:
        return None, "broker body closing brace is absent"
    filename_index = next(
        (
            i
            for i in range(body_close + 1, limit)
            if FILENAME_HEADER_RE.match(_trim_control(lines[i]))
        ),
        None,
    )
    if filename_index is None:
        return None, "filename-list section is absent"
    filename_match = FILENAME_HEADER_RE.match(_trim_control(lines[filename_index]))
    assert filename_match is not None
    reported_filename_count = int(filename_match.group(1))
    open_index = next(
        (i for i in range(filename_index + 1, min(filename_index + 4, limit)) if _trim_control(lines[i]) == "{"),
        None,
    )
    if open_index is None:
        return None, "filename-list opening brace is absent"
    filename_close = next(
        (i for i in range(open_index + 1, limit) if _trim_control(lines[i]) == "}"),
        None,
    )
    if filename_close is None:
        return None, "filename-list closing brace is absent"
    filename_lines = [line for line in lines[open_index + 1 : filename_close] if line.strip()]
    if len(filename_lines) != reported_filename_count:
        return None, (
            f"filename section has {len(filename_lines)} non-empty lines but reports "
            f"{reported_filename_count}"
        )

    occurrences: Counter[tuple[str, str]] = Counter()
    for _i, entry in entry_lines:
        entry["value"] = _typed_value(entry["type"], str(entry.get("value_raw", "")), entry["continuation_lines"])
        key = (entry["broker_id"], entry["path"])
        entry["occurrence"] = occurrences[key]
        occurrences[key] += 1

    end_index = filename_close
    block_start = starts[header_index]
    # split(b'\n') has one synthetic trailing chunk when the source ends in LF.
    if end_index + 1 < len(starts):
        block_end = starts[end_index + 1]
    else:
        block_end = starts[end_index] + len(chunks[end_index])
    if block_end > len(raw):
        block_end = len(raw)
    section_raw = raw[block_start:block_end]
    return {
        "dump": {
            "reported_size": reported_size,
            "reported_capacity": reported_capacity,
            "reported_scope_counts": {
                "GLOBAL": summary["global"],
                "SCENE": summary["scene"],
                "USER": summary["user"],
                "TOTAL": summary["total"],
            },
            "parsed_entry_count": len(entry_lines),
            "reported_filename_count": reported_filename_count,
            "filenames": [line.strip() for line in filename_lines],
            "special_labels_observed": [
                label
                for label in ("__NO_SAVE", "__NO_CHANGE", "__IGNORE")
                if label in {line.strip() for line in filename_lines}
                or any(entry["save_file"] == label for _index, entry in entry_lines)
            ],
        },
        "entries": [entry for _i, entry in entry_lines],
        "block": {
            "start_offset": block_start,
            "end_offset": block_end,
            "byte_length": len(section_raw),
            "sha256": sha256_bytes(section_raw),
            "first_line": header_index + 1,
            "last_line": end_index + 1,
        },
    }, "complete"


def parse_dump_bytes(raw: bytes, source: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parse the latest complete Dump block while preserving source-byte facts."""
    parse_raw = raw.rstrip(b"\x00")
    lines, starts, chunks = _raw_lines(parse_raw)
    candidates: list[tuple[int, dict[str, Any]]] = []
    failures: list[dict[str, Any]] = []
    headers = [i for i, line in enumerate(lines) if HEADER_RE.match(_trim_control(line))]
    for position, i in enumerate(headers):
        limit = headers[position + 1] if position + 1 < len(headers) else len(lines)
        result, reason = _attempt_block(parse_raw, lines, starts, chunks, i, limit)
        if result is None:
            failures.append({"line": i + 1, "reason": reason})
        else:
            candidates.append((i, result))
    if not candidates:
        detail = "; ".join(f"line {x['line']}: {x['reason']}" for x in failures[-3:])
        raise ObservatoryError("No complete Broker Dump block was found" + (f" ({detail})" if detail else "."))

    _header_index, parsed = candidates[-1]
    complete_ranges = [
        (candidate["block"]["first_line"] - 1, candidate["block"]["last_line"] - 1)
        for _index, candidate in candidates
    ]
    malformed_lines: list[dict[str, Any]] = []
    for line_index, line in enumerate(lines):
        if not line.lstrip().startswith("[Rev="):
            continue
        entry = _parse_entry(line, -1)
        if entry is None or entry["type"].startswith("UNKNOWN"):
            malformed_lines.append({"line": line_index + 1, "text": line[:240]})
    ignored_samples = [
        {"line": line_index + 1, "text": line[:240]}
        for line_index, line in enumerate(lines)
        if line.strip()
        and not line.lstrip().startswith("[Rev=")
        and not any(start <= line_index <= end for start, end in complete_ranges)
    ][:20]
    ignored_count = sum(
        bool(line.strip())
        and not line.lstrip().startswith("[Rev=")
        and not any(start <= line_index <= end for start, end in complete_ranges)
        for line_index, line in enumerate(lines)
    )
    src = dict(source or {})
    src.setdefault("capture_kind", "offline-parse")
    src.update(
        {
            "raw_sha256": sha256_bytes(raw),
            "raw_byte_length": len(raw),
            "raw_nul_suffix_bytes": len(raw) - len(parse_raw),
            "selected_block_offset": parsed["block"]["start_offset"],
            "selected_block_length": parsed["block"]["byte_length"],
            "selected_block_sha256": parsed["block"]["sha256"],
            "selected_block_first_line": parsed["block"]["first_line"],
            "selected_block_last_line": parsed["block"]["last_line"],
        }
    )
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "tool_version": VERSION,
        "kind": "master-rallye-broker-dump-snapshot",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "source": src,
        "dump": parsed["dump"],
        "entries": parsed["entries"],
        "diagnostics": {
            "complete_dump_candidates": len(candidates),
            "selected_candidate_index": len(candidates) - 1,
            "incomplete_candidates": failures,
            "parsed_entry_count": len(parsed["entries"]),
            "ignored_non_entry_line_count": ignored_count,
            "ignored_non_entry_line_samples": ignored_samples,
            "malformed_lines": malformed_lines,
            "value_precision_note": (
                "Float, vector, and matrix values retain the game-emitted text; the executable formats "
                "these fields to two decimal places, so the snapshot is lossless relative to Debug→Dump output, "
                "not the underlying full-precision broker storage."
            ),
            "type_12_records": (
                "The executable Dump routine skips broker type tag 0x0C; the parsed entry set is complete "
                "relative to what this diagnostic emits, not a raw enumeration of every manager slot."
            ),
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ObservatoryError(f"Cannot read snapshot {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ObservatoryError(f"Snapshot root must be an object: {path}")
    if value.get("kind") != "master-rallye-broker-dump-snapshot":
        raise ObservatoryError(f"Unsupported snapshot kind in {path}")
    if value.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ObservatoryError(f"Unsupported snapshot schema version in {path}")
    if not isinstance(value.get("entries"), list) or not isinstance(value.get("dump"), dict):
        raise ObservatoryError(f"Snapshot structure is incomplete: {path}")
    return value


def _numeric_value(entry: dict[str, Any]) -> list[int | float] | None:
    kind = entry.get("type")
    if kind == "Bool":
        return [1 if entry.get("value") is True else 0] if isinstance(entry.get("value"), bool) else None
    if kind == "Int":
        value = entry.get("value")
        return [value] if isinstance(value, int) and not isinstance(value, bool) else None
    if kind == "Float":
        value = entry.get("value")
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            return [float(value)]
        return None
    if kind not in {"nuVector2", "nuVector3", "nuVector4", "Matrix"}:
        return None
    value = entry.get("value")
    if isinstance(value, list) and all(isinstance(item, (int, float)) and math.isfinite(item) for item in value):
        return [float(item) for item in value]
    return None


def _values_equal(left: dict[str, Any], right: dict[str, Any], tolerance: float) -> bool:
    if left.get("type") != right.get("type"):
        return False
    if tolerance == 0:
        return (left.get("value_raw"), left.get("continuation_lines", [])) == (
            right.get("value_raw"),
            right.get("continuation_lines", []),
        )
    left_numbers, right_numbers = _numeric_value(left), _numeric_value(right)
    if left_numbers is not None or right_numbers is not None:
        if left_numbers is None or right_numbers is None or len(left_numbers) != len(right_numbers):
            return False
        if left.get("type") in {"Bool", "Int"}:
            return left_numbers == right_numbers
        return all(abs(a - b) <= tolerance for a, b in zip(left_numbers, right_numbers))
    return (left.get("value"), left.get("value_raw"), left.get("continuation_lines", [])) == (
        right.get("value"),
        right.get("value_raw"),
        right.get("continuation_lines", []),
    )


def _entry_identity(entry: dict[str, Any]) -> tuple[str, str, int]:
    return str(entry.get("broker_id", "")), str(entry.get("path", "")), int(entry.get("occurrence", 0))


def _path_occurrence(entry: dict[str, Any]) -> tuple[str, int]:
    return str(entry.get("path", "")), int(entry.get("occurrence", 0))


def _changes(left: dict[str, Any], right: dict[str, Any], tolerance: float) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    if left.get("broker_id") != right.get("broker_id"):
        changes["BROKER_ID_CHANGED"] = {"before": left.get("broker_id"), "after": right.get("broker_id")}
    if left.get("scope_label") != right.get("scope_label"):
        changes["SCOPE_CHANGED"] = {"before": left.get("scope_label"), "after": right.get("scope_label")}
    if left.get("type") != right.get("type"):
        changes["TYPE_CHANGED"] = {"before": left.get("type"), "after": right.get("type")}
        if (left.get("value_raw"), left.get("continuation_lines", [])) != (
            right.get("value_raw"), right.get("continuation_lines", [])
        ):
            changes["VALUE_CHANGED"] = {
                "before": {"value": left.get("value"), "value_raw": left.get("value_raw"), "continuation_lines": left.get("continuation_lines", [])},
                "after": {"value": right.get("value"), "value_raw": right.get("value_raw"), "continuation_lines": right.get("continuation_lines", [])},
            }
    elif not _values_equal(left, right, tolerance):
        changes["VALUE_CHANGED"] = {
            "before": {"value": left.get("value"), "value_raw": left.get("value_raw"), "continuation_lines": left.get("continuation_lines", [])},
            "after": {"value": right.get("value"), "value_raw": right.get("value_raw"), "continuation_lines": right.get("continuation_lines", [])},
        }
    if left.get("revision") != right.get("revision"):
        changes["REVISION_CHANGED"] = {"before": left.get("revision"), "after": right.get("revision")}
    if left.get("save_flags") != right.get("save_flags"):
        changes["SAVE_MASK_CHANGED"] = {"before": left.get("save_flags"), "after": right.get("save_flags")}
    if left.get("save_file") != right.get("save_file"):
        changes["SAVE_FILE_CHANGED"] = {"before": left.get("save_file"), "after": right.get("save_file")}
    return changes


def diff_snapshots(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    prefixes: Sequence[str] = (),
    float_tolerance: float = 0.0,
    ignore_revision_only: bool = False,
) -> dict[str, Any]:
    if float_tolerance < 0 or not math.isfinite(float_tolerance):
        raise ObservatoryError("float tolerance must be a finite non-negative number")

    def selected(entry: dict[str, Any]) -> bool:
        path = str(entry.get("path", ""))
        return not prefixes or any(path.startswith(prefix) for prefix in prefixes)

    old_entries = [entry for entry in before["entries"] if selected(entry)]
    new_entries = [entry for entry in after["entries"] if selected(entry)]
    old_by_id: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    new_by_id: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for entry in old_entries:
        old_by_id[_entry_identity(entry)].append(entry)
    for entry in new_entries:
        new_by_id[_entry_identity(entry)].append(entry)

    paired: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    old_unmatched: list[dict[str, Any]] = []
    new_unmatched: list[dict[str, Any]] = []
    all_ids = set(old_by_id) | set(new_by_id)
    for key in all_ids:
        old_group = old_by_id.get(key, [])
        new_group = new_by_id.get(key, [])
        paired.extend((a, b, "broker-id-path-occurrence") for a, b in zip(old_group, new_group))
        old_unmatched.extend(old_group[len(new_group) :])
        new_unmatched.extend(new_group[len(old_group) :])

    # A displayed broker-ID change breaks exact identity. Pair it only where path and
    # occurrence identify one remaining record on both sides; ambiguous
    # cross-scope duplicates stay as explicit remove/add events.
    old_fallback: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    new_fallback: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for entry in old_unmatched:
        old_fallback[_path_occurrence(entry)].append(entry)
    for entry in new_unmatched:
        new_fallback[_path_occurrence(entry)].append(entry)
    consumed_old: set[int] = set()
    consumed_new: set[int] = set()
    for key, left_group in old_fallback.items():
        right_group = new_fallback.get(key, [])
        if len(left_group) == 1 and len(right_group) == 1:
            paired.append((left_group[0], right_group[0], "unique-path-occurrence-fallback"))
            consumed_old.add(id(left_group[0]))
            consumed_new.add(id(right_group[0]))
    old_unmatched = [entry for entry in old_unmatched if id(entry) not in consumed_old]
    new_unmatched = [entry for entry in new_unmatched if id(entry) not in consumed_new]

    events: list[dict[str, Any]] = []
    for left, right, pairing in paired:
        changes = _changes(left, right, float_tolerance)
        if changes and not (ignore_revision_only and set(changes) == {"REVISION_CHANGED"}):
            events.append(
                {
                    "kind": "CHANGED",
                    "path": left.get("path"),
                    "before_scope": left.get("scope_label"),
                    "after_scope": right.get("scope_label"),
                    "occurrence": left.get("occurrence"),
                    "pairing": pairing,
                    "changes": changes,
                }
            )
    events.extend(
        {"kind": "REMOVED", "path": entry.get("path"), "scope": entry.get("scope_label"), "entry": entry}
        for entry in old_unmatched
    )
    events.extend(
        {"kind": "ADDED", "path": entry.get("path"), "scope": entry.get("scope_label"), "entry": entry}
        for entry in new_unmatched
    )
    events.sort(key=lambda item: (str(item.get("path", "")), item["kind"], str(item.get("scope", item.get("after_scope", "")))))
    counts = Counter()
    for event in events:
        if event["kind"] == "CHANGED":
            counts["CHANGED"] += 1
            counts.update(event["changes"].keys())
        else:
            counts[event["kind"]] += 1
    return {
        "schema_version": 1,
        "kind": "master-rallye-broker-snapshot-diff",
        "before_sha256": before.get("source", {}).get("raw_sha256"),
        "after_sha256": after.get("source", {}).get("raw_sha256"),
        "before_label": before.get("source", {}).get("label"),
        "after_label": after.get("source", {}).get("label"),
        "before_entry_count": len(old_entries),
        "after_entry_count": len(new_entries),
        "filters": {"path_prefixes": list(prefixes), "float_tolerance": float_tolerance,
                    "ignore_revision_only": ignore_revision_only},
        "summary": dict(sorted(counts.items())),
        "events": events,
    }


SAVE_MODE_FIELDS = {"game": "save_game", "options": "save_options", "playerstate": "save_player_state"}


def persistence_report(snapshot: dict[str, Any], *, save_file: str | None = None,
                       save_mode: str | None = None, scope: str | None = None) -> dict[str, Any]:
    """Group emitted diagnostic rows; this is metadata coverage, not a save preview."""
    if save_mode is not None and save_mode not in SAVE_MODE_FIELDS:
        raise ObservatoryError(f"Unknown save mode: {save_mode}")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in snapshot["entries"]:
        if save_file is not None and entry["save_file"] != save_file:
            continue
        if scope is not None and entry["scope_label"] != scope:
            continue
        if save_mode is not None and not entry[SAVE_MODE_FIELDS[save_mode]]:
            continue
        groups[entry["save_file"]].append(entry)
    result = []
    for name, entries in sorted(groups.items()):
        revisions = [entry["revision"] for entry in entries]
        result.append({
            "save_file": name, "entries": len(entries),
            "scopes": dict(sorted(Counter(e["scope_label"] for e in entries).items())),
            "save_enabled": {mode: sum(bool(e[field]) for e in entries) for mode, field in SAVE_MODE_FIELDS.items()},
            "types": dict(sorted(Counter(e["type"] for e in entries).items())),
            "revisions": {"min": min(revisions), "max": max(revisions),
                          "histogram": dict(sorted(Counter(str(r) for r in revisions).items()))},
            "representative_paths": sorted(set(e["path"] for e in entries))[:8],
        })
    return {"kind": "master-rallye-broker-persistence-report", "schema_version": 1,
            "entry_count": sum(g["entries"] for g in result), "groups": result,
            "filters": {"save_file": save_file, "save_mode": save_mode, "scope": scope},
            "limitation": "Emitted Dump rows only; type 0x0C is omitted. Save bits alone are not the entire serializer filter."}


def print_persistence_report(report: dict[str, Any]) -> None:
    print(f"Emitted entries: {report['entry_count']}")
    for group in report["groups"]:
        print(f"SaveFile {group['save_file']}: {group['entries']} entries")
        print(f"  scopes={group['scopes']} save-enabled={group['save_enabled']}")
        print(f"  types={group['types']} revision={group['revisions']['min']}..{group['revisions']['max']}")
        print("  paths: " + ", ".join(group["representative_paths"]))
    print(report["limitation"])


def _configure_win32(kernel32: Any, ctypes: Any) -> None:
    from ctypes import wintypes

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Module32FirstW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel32.Module32FirstW.restype = wintypes.BOOL
    kernel32.Module32NextW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel32.Module32NextW.restype = wintypes.BOOL
    kernel32.ReadProcessMemory.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.ReadProcessMemory.restype = wintypes.BOOL


def _process_image_path(kernel32: Any, pid: int, ctypes: Any) -> tuple[Any, Path]:
    from ctypes import byref, create_unicode_buffer
    from ctypes import wintypes

    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        raise ObservatoryError(f"OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ) failed for PID {pid}")
    length = wintypes.DWORD(32768)
    buffer = create_unicode_buffer(length.value)
    if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, byref(length)):
        kernel32.CloseHandle(handle)
        raise ObservatoryError(f"Could not resolve the image path for PID {pid}")
    return handle, Path(buffer.value)


def _module_info(kernel32: Any, pid: int, ctypes: Any) -> tuple[int, int, Path]:
    from ctypes import wintypes

    class MODULEENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("th32ModuleID", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("GlblcntUsage", wintypes.DWORD),
            ("ProccntUsage", wintypes.DWORD),
            ("modBaseAddr", ctypes.c_void_p),
            ("modBaseSize", wintypes.DWORD),
            ("hModule", wintypes.HMODULE),
            ("szModule", wintypes.WCHAR * 256),
            ("szExePath", wintypes.WCHAR * 260),
        ]

    TH32CS_SNAPMODULE = 0x00000008
    TH32CS_SNAPMODULE32 = 0x00000010
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    invalid = ctypes.c_void_p(-1).value
    if not snapshot or snapshot == invalid:
        raise ObservatoryError(f"Could not enumerate modules for PID {pid}")
    try:
        entry = MODULEENTRY32W()
        entry.dwSize = ctypes.sizeof(MODULEENTRY32W)
        entry_pointer = ctypes.cast(ctypes.byref(entry), ctypes.c_void_p)
        if not kernel32.Module32FirstW(snapshot, entry_pointer):
            raise ObservatoryError(f"Module enumeration returned no entries for PID {pid}")
        while True:
            if entry.th32ProcessID == pid and entry.szModule.casefold() == "mrallye.exe":
                base = int(entry.modBaseAddr or 0)
                if base == 0:
                    break
                return base, int(entry.modBaseSize), Path(entry.szExePath)
            if not kernel32.Module32NextW(snapshot, entry_pointer):
                break
    finally:
        kernel32.CloseHandle(snapshot)
    raise ObservatoryError("Verified process has no MRallye.exe main module")


def _module_base(kernel32: Any, pid: int, ctypes: Any) -> int:
    """Compatibility wrapper for older internal callers."""
    return _module_info(kernel32, pid, ctypes)[0]


def _read_remote(kernel32: Any, process: Any, address: int, size: int, ctypes: Any) -> bytes:
    if address <= 0 or size < 0 or size > DEBUG_BUFFER_MAX_BYTES or address + size > 0x80000000:
        raise ObservatoryError(f"Refusing invalid remote range address=0x{address:X} size={size}")
    if size == 0:
        return b""
    data = (ctypes.c_ubyte * size)()
    received = ctypes.c_size_t()
    ok = kernel32.ReadProcessMemory(
        process,
        ctypes.c_void_p(address),
        ctypes.cast(data, ctypes.c_void_p),
        size,
        ctypes.byref(received),
    )
    if not ok or received.value != size:
        raise ObservatoryError(
            f"ReadProcessMemory failed/short at 0x{address:X}: requested {size}, got {received.value}"
        )
    return bytes(data)


def _u32(raw: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def _valid_x86_user_pointer(pointer: int) -> bool:
    return 0x10000 <= pointer <= 0x7FFFFFFF


def _read_sink_state(kernel32: Any, user32: Any, process: Any, module_base: int, ctypes: Any,
                     profile: ObservatoryBuildProfile = RETAIL_PRISTINE) -> dict[str, int]:
    global_address = module_base + profile.active_log_sink_rva
    sink_pointer = _u32(_read_remote(kernel32, process, global_address, 4, ctypes))
    if not _valid_x86_user_pointer(sink_pointer):
        raise ObservatoryError(f"Active logger sink pointer is invalid: 0x{sink_pointer:08X}")
    obj = _read_remote(kernel32, process, sink_pointer, DEBUG_SINK_OBJECT_SIZE, ctypes)
    vtable = _u32(obj, 0)
    expected_vtable = module_base + profile.debug_sink_vtable_rva
    if vtable != expected_vtable:
        raise ObservatoryError(
            f"Active logger is not the expected Debug sink (vtable 0x{vtable:08X}, expected 0x{expected_vtable:08X}); "
            "open the Debug window first."
        )
    helper = _u32(obj, 0x0C)
    if not _valid_x86_user_pointer(helper):
        raise ObservatoryError(f"Debug sink window helper pointer is invalid: 0x{helper:08X}")
    hwnd = _u32(_read_remote(kernel32, process, helper + 4, 4, ctypes))
    if hwnd == 0 or not user32.IsWindow(ctypes.c_void_p(hwnd)):
        raise ObservatoryError("Debug sink has no live Debug window handle")
    visible_start = _u32(obj, 0x20)
    capacity_end = _u32(obj, 0x24)
    buffer_base = _u32(obj, 0x28)
    write_end = _u32(obj, 0x2C)
    for label, pointer in (
        ("visible-text start", visible_start),
        ("allocation end", capacity_end),
        ("buffer base", buffer_base),
        ("write end", write_end),
    ):
        if not _valid_x86_user_pointer(pointer):
            raise ObservatoryError(f"Debug {label} pointer is invalid: 0x{pointer:08X}")
    if not (buffer_base <= visible_start <= write_end <= capacity_end):
        raise ObservatoryError("Debug buffer pointers are out of order or outside the allocation")
    capacity = capacity_end - buffer_base
    used = write_end - buffer_base
    if capacity > DEBUG_BUFFER_MAX_BYTES or used > capacity:
        raise ObservatoryError(f"Debug buffer size is outside safety limit ({capacity} bytes allocated)")
    return {
        "sink_pointer": sink_pointer,
        "vtable": vtable,
        "helper_pointer": helper,
        "hwnd": hwnd,
        "visible_start": visible_start,
        "capacity_end": capacity_end,
        "buffer_base": buffer_base,
        "write_end": write_end,
        "capacity_bytes": capacity,
        "used_bytes": used,
    }


def _anchors_for_capability(profile: ObservatoryBuildProfile, capability: str) -> tuple[dict[str, Any], ...]:
    names = {
        "broker_read": {"debug_logger", "debug_sink_vtable"},
        "native_dump": {"debug_logger", "debug_sink_vtable", "broker_editor_dump_route",
                        "broker_singleton_accessor", "native_dump_walker"},
        "open_broker_editor": {"broker_editor_dump_route"},
    }.get(capability, set())
    by_name = {item["name"]: item for item in profile.runtime_anchors}
    if not names or not names.issubset(by_name):
        return ()
    return tuple(by_name[name] for name in sorted(names))


def _verify_remote_anchors(kernel32: Any, process: Any, module_base: int, ctypes: Any,
                           profile: ObservatoryBuildProfile, capability: str,
                           pe: dict[str, Any] | None = None,
                           runtime_details: dict[str, Any] | None = None,
                           disk_sha256: str | None = None,
                           disk_size: int | None = None) -> list[str]:
    if not profile.supports(capability):
        raise ObservatoryError(f"Capability {capability} is not statically audited for this build")
    anchors = _anchors_for_capability(profile, capability)
    if not anchors:
        # The public exact-profile executable set predates family anchor
        # metadata. Its exact file identity remains the frozen compatibility
        # gate; newly locally-audited profiles must always carry live anchors.
        if capability != "native_dump" and profile.profile_origin == "committed_exact" and not profile.audit_version:
            return []
        raise ObservatoryError(f"No runtime code fingerprints are available for {capability}")
    identity = profile.pe_identity
    preferred_base = identity.get("image_base")
    image_size = identity.get("size_of_image")
    if (type(preferred_base) is not int or type(image_size) is not int
            or module_base != preferred_base or module_base + image_size > 0x80000000):
        raise ObservatoryError("Live x86 module base/extent differs from the audited PE identity")
    def read_rva(rva: int, length: int) -> bytes:
        if rva + length > image_size:
            raise ObservatoryError("Runtime fingerprint is outside the verified module image")
        return _read_remote(kernel32, process, module_base + rva, length, ctypes)

    skip_names = ("native_dump_walker",) if capability == "native_dump" else ()
    try:
        verified = compatibility.verify_runtime_anchor_fingerprints(
            read_rva, anchors, skip_names=skip_names
        )
    except Exception as exc:
        raise ObservatoryError(f"Live {capability} anchor verification failed: {exc}") from exc
    if capability == "native_dump":
        if pe is None:
            raise ObservatoryError("Native Dump verification is missing the verified PE layout")
        canonical = compatibility.definitions()
        walker = next((item for item in canonical["anchors"]
                       if item.get("name") == "native_dump_walker"), None)
        profile_walker = next((item for item in anchors
                               if item.get("name") == "native_dump_walker"), None)
        image_base = pe.get("image_base") if isinstance(pe, dict) else None
        walker_va = walker.get("va") if isinstance(walker, dict) else None
        if (type(image_base) is not int or type(walker_va) is not int
                or walker_va < image_base):
            raise ObservatoryError("Native Dump walker reference has an invalid VA/image base")
        expected_rva = walker_va - image_base
        if (walker is None or profile_walker is None
                or profile_walker.get("rva") != expected_rva
                or any(profile_walker.get(key) != walker.get(key)
                       for key in ("length", "sha256", "section"))):
            raise ObservatoryError("Native Dump walker reference differs from the audited retail family")

        def read_va(va: int, size: int) -> bytes:
            rva = va - pe["image_base"]
            if rva < 0 or rva + size > identity["size_of_image"]:
                raise ObservatoryError("Native Dump read is outside the verified module image")
            return _read_remote(kernel32, process, module_base + rva, size, ctypes)

        try:
            walker_result = compatibility.classify_native_dump_walker(
                read_va, pe,
                profile_sha256=profile.sha256,
                profile_size=profile.file_size,
                disk_sha256=disk_sha256,
                disk_size=disk_size,
            )
        except Exception as exc:
            raise ObservatoryError(str(exc)) from exc
        variant = walker_result["variant"]
        if variant not in ("native_stock", "native-hardened-null-safe-stubs-v1"):
            raise ObservatoryError("Live native Dump walker variant is not explicitly approved")
        if variant == "native-hardened-null-safe-stubs-v1":
            if profile.sha256 != RETAIL_SHA256 or profile.file_size != RETAIL_SIZE:
                raise ObservatoryError("J.1 hardened walker requires the exact pristine retail executable identity")
            if len(walker_result.get("verified_trampolines", ())) != 2:
                raise ObservatoryError("J.1 hardened walker did not verify both required trampolines")
        if runtime_details is not None:
            runtime_details.update(walker_result)
        verified.append(f"native_dump_walker:{variant}")
    return verified


def _mapped_header_size(data: bytes) -> int:
    try:
        return compatibility.mapped_header_size(data)
    except ValueError as exc:
        raise ObservatoryError(f"Verified executable PE headers are invalid: {exc}") from exc


def _verify_mapped_image(kernel32: Any, process: Any, ctypes: Any, image_path: Path,
                         module_path: Path, module_base: int, module_size: int,
                         disk_bytes: bytes, pe: dict[str, Any]) -> None:
    try:
        expected_path = os.path.normcase(str(image_path.resolve())).casefold()
        mapped_path = os.path.normcase(str(module_path.resolve())).casefold()
    except OSError as exc:
        raise ObservatoryError("Could not resolve the executable module paths") from exc
    if expected_path != mapped_path:
        raise ObservatoryError("Mapped MRallye.exe path differs from the verified process image")
    if (module_base != pe.get("image_base") or module_size != pe.get("size_of_image")
            or module_base < 0x10000 or module_base + module_size > 0x80000000):
        raise ObservatoryError("Mapped module base/size differs from the exact audited PE image")
    header_size = _mapped_header_size(disk_bytes)
    mapped_headers = _read_remote(kernel32, process, module_base, header_size, ctypes)
    try:
        compatibility.validate_mapped_image_identity(
            disk_bytes, mapped_headers, pe, module_base, module_size
        )
    except ValueError as exc:
        raise ObservatoryError(f"Mapped PE identity differs from the verified on-disk executable: {exc}") from exc


def _verify_live_capability_open(kernel32: Any, process: Any, pid: int,
                                 image_path: Path, profile: ObservatoryBuildProfile,
                                 capability: str, ctypes: Any, *,
                                 disk_bytes: bytes | None = None) -> dict[str, Any]:
    if not profile.supports(capability):
        raise ObservatoryError(f"Capability {capability} is not statically audited for this build")
    if image_path.name.casefold() != "mrallye.exe" or not image_path.is_file():
        raise ObservatoryError(f"PID {pid} image is not a readable MRallye.exe")
    disk_bytes = image_path.read_bytes() if disk_bytes is None else disk_bytes
    image_hash = hashlib.sha256(disk_bytes).hexdigest()
    if image_hash != profile.sha256 or len(disk_bytes) != profile.file_size:
        raise ObservatoryError("Live process executable changed after profile resolution")
    if capability == "native_dump":
        try:
            compatibility.validate_pristine_runtime_identity(
                profile.sha256, profile.file_size, image_hash, len(disk_bytes)
            )
        except ValueError as exc:
            raise ObservatoryError(str(exc)) from exc
    try:
        pe = compatibility.pe_layout(disk_bytes)
    except ValueError as exc:
        raise ObservatoryError(f"Verified executable PE layout is invalid: {exc}") from exc
    expected_identity = profile.pe_identity
    for key in ("machine", "image_base", "size_of_image", "entry_rva"):
        expected_value = expected_identity.get(key)
        if expected_value is not None and pe.get(key) != expected_value:
            raise ObservatoryError(f"On-disk PE identity differs from profile at {key}")
    module_base, module_size, module_path = _module_info(kernel32, pid, ctypes)
    _verify_mapped_image(kernel32, process, ctypes, image_path, module_path,
                          module_base, module_size, disk_bytes, pe)
    runtime_details: dict[str, Any] = {}
    verified = _verify_remote_anchors(kernel32, process, module_base, ctypes,
                                      profile, capability, pe=pe,
                                      runtime_details=runtime_details,
                                      disk_sha256=image_hash,
                                      disk_size=len(disk_bytes))
    report: dict[str, Any] = {
        "capability": capability,
        "verified_anchors": verified,
        "module_base": module_base,
        "module_size": module_size,
        "disk_sha256": image_hash,
        "disk_size": len(disk_bytes),
    }
    if capability == "native_dump":
        variant = runtime_details.get("variant", "unknown")
        hardened = variant == "native-hardened-null-safe-stubs-v1"
        report.update({
            "effective_broker_dump_variant": "native_hardened" if hardened else "native_stock" if variant == "native_stock" else "unknown",
            "native_dump_post_results_safe": compatibility.native_dump_post_results_safe(variant),
            "native_dump_verification": "verified" if variant in ("native_stock", "native-hardened-null-safe-stubs-v1") else "unverified",
            "native_dump_walker_variant": variant,
            "native_dump_walker_sha256": runtime_details.get("walker_sha256"),
            "verified_trampolines": runtime_details.get("verified_trampolines", []),
        })
    return report


def verify_live_capability_report(pid: int, profile: ObservatoryBuildProfile,
                                  capability: str) -> dict[str, Any]:
    """Return process-scoped capability evidence after file and mapping checks."""
    if not os.name == "nt":
        raise ObservatoryError("Live capability verification is Windows-only")
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _configure_win32(kernel32, ctypes)
    process, image_path = _process_image_path(kernel32, pid, ctypes)
    try:
        return _verify_live_capability_open(kernel32, process, pid, image_path,
                                            profile, capability, ctypes)
    finally:
        kernel32.CloseHandle(process)


def verify_live_capability(pid: int, profile: ObservatoryBuildProfile, capability: str) -> list[str]:
    """Compatibility wrapper returning the independently verified anchor names."""
    return verify_live_capability_report(pid, profile, capability)["verified_anchors"]


def capture_debug_buffer(pid: int, profile: ObservatoryBuildProfile | None = None) -> tuple[bytes, dict[str, Any]]:
    """Read a consistent snapshot of the active retail Debug sink buffer."""
    if os.name != "nt":
        raise ObservatoryError("Live process capture is Windows-only; use parse for offline dump files.")
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    _configure_win32(kernel32, ctypes)
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL

    process, image_path = _process_image_path(kernel32, pid, ctypes)
    try:
        if image_path.name.casefold() != "mrallye.exe":
            raise ObservatoryError(f"PID {pid} image is not MRallye.exe: {image_path}")
        if not image_path.is_file():
            raise ObservatoryError(f"Process image path is no longer readable: {image_path}")
        disk_bytes = image_path.read_bytes()
        image_hash = hashlib.sha256(disk_bytes).hexdigest()
        image_size = len(disk_bytes)
        if profile is None:
            try:
                profile = match_profile(image_hash, image_size)
            except ValueError as exc:
                raise ObservatoryError(f"PID {pid}: {exc}") from exc
        elif image_hash != profile.sha256 or image_size != profile.file_size:
            raise ObservatoryError("PID executable identity changed after profile resolution")
        if not profile.supports("broker_read"):
            raise ObservatoryError("Passive Broker read is disabled for this build profile")
        broker_report = _verify_live_capability_open(
            kernel32, process, pid, image_path, profile, "broker_read", ctypes,
            disk_bytes=disk_bytes,
        )
        module_base = broker_report["module_base"]
        verified_anchors = broker_report["verified_anchors"]

        last_problem = "buffer changed during read"
        captured: bytes | None = None
        final_state: dict[str, int] | None = None
        for _attempt in range(CAPTURE_RETRIES):
            try:
                state_a = _read_sink_state(kernel32, user32, process, module_base, ctypes, profile)
                first = _read_remote(
                    kernel32, process, state_a["buffer_base"], state_a["used_bytes"], ctypes
                )
                state_b = _read_sink_state(kernel32, user32, process, module_base, ctypes, profile)
                second = _read_remote(
                    kernel32, process, state_b["buffer_base"], state_b["used_bytes"], ctypes
                )
                state_c = _read_sink_state(kernel32, user32, process, module_base, ctypes, profile)
                if state_a == state_b == state_c and first == second:
                    captured = first
                    final_state = state_c
                    break
                last_problem = "logger metadata or bytes changed between repeated reads"
            except ObservatoryError as exc:
                last_problem = str(exc)
        if captured is None or final_state is None:
            raise ObservatoryError(f"Could not obtain a stable Debug-buffer snapshot after {CAPTURE_RETRIES} attempts: {last_problem}")

        native_dump_report: dict[str, Any] | None = None
        native_dump_error: str | None = None
        if profile.supports("native_dump"):
            try:
                native_dump_report = _verify_live_capability_open(
                    kernel32, process, pid, image_path, profile, "native_dump", ctypes,
                    disk_bytes=disk_bytes,
                )
            except (OSError, ObservatoryError) as exc:
                # Passive Broker reading is independent. A failed native Dump
                # attestation is recorded but does not suppress this read-only capture.
                native_dump_error = str(exc)

        metadata = {
            "capture_kind": "live-debug-buffer-read-only",
            "build": "retail",
            "build_profile_id": profile.id,
            "image_path": str(image_path),
            "image_sha256": image_hash,
            "image_size": image_size,
            "process_id": pid,
            "module_base": f"0x{module_base:08X}",
            "active_sink_pointer": f"0x{final_state['sink_pointer']:08X}",
            "sink_vtable": f"0x{final_state['vtable']:08X}",
            "debug_window_handle": f"0x{final_state['hwnd']:08X}",
            "debug_buffer_base": f"0x{final_state['buffer_base']:08X}",
            "debug_buffer_capacity_bytes": final_state["capacity_bytes"],
            "debug_buffer_used_bytes": final_state["used_bytes"],
            "capture_consistency": "three equal metadata reads and two equal byte reads; process was not suspended",
            "access_rights": ["PROCESS_QUERY_INFORMATION", "PROCESS_VM_READ"],
            "runtime_verified_anchors": verified_anchors,
            "runtime_verified_capabilities": {"broker_read": verified_anchors},
        }
        if native_dump_report is not None:
            metadata["runtime_verified_capabilities"]["native_dump"] = native_dump_report["verified_anchors"]
        metadata.update({
            "build_profile": profile.id,
            "build_classification": ("hardened" if native_dump_report and
                                     native_dump_report.get("effective_broker_dump_variant") == "native_hardened"
                                     else profile.build_classification),
            "disk_build_classification": profile.build_classification,
            "exact_profile_id": profile.exact_profile_id,
            "profile_origin": profile.profile_origin,
            "compatibility_family": profile.compatibility_family,
            "audit_version": profile.audit_version,
            "audit_fingerprint": profile.audit_fingerprint,
            "vehicle_registry_profile": profile.vehicle_registry_profile,
            "disk_capabilities": dict(profile.capabilities),
            "capabilities": dict(profile.capabilities),
            "effective_capabilities": {
                "broker_read": True,
                "native_dump": True if native_dump_report else None,
                "post_results_native_dump_safe": (native_dump_report or {}).get("native_dump_post_results_safe"),
                "broker_dump_variant": (native_dump_report or {}).get("effective_broker_dump_variant", "unknown"),
            },
            "disk_broker_dump_variant": profile.capabilities.get("broker_dump_variant", "unknown"),
            "disk_native_dump_post_results_safe": profile.capabilities.get("post_results_native_dump_safe"),
            "broker_dump_variant": (native_dump_report or {}).get("effective_broker_dump_variant", "unknown"),
            "effective_broker_dump_variant": (native_dump_report or {}).get("effective_broker_dump_variant", "unknown"),
            "native_dump_post_results_safe": (native_dump_report or {}).get("native_dump_post_results_safe"),
            "native_dump_verification": (native_dump_report or {}).get("native_dump_verification", "unverified"),
            "native_dump_walker_variant": (native_dump_report or {}).get("native_dump_walker_variant", "unknown"),
            "native_dump_walker_sha256": (native_dump_report or {}).get("native_dump_walker_sha256"),
            "verified_trampolines": (native_dump_report or {}).get("verified_trampolines", []),
            "runtime_native_dump_verified_anchors": (native_dump_report or {}).get("verified_anchors", []),
            "native_dump_verification_error": native_dump_error,
            "legacy_loading_attract_present": profile.capabilities.get("legacy_loading_attract_present"),
        })
        return captured, metadata
    finally:
        kernel32.CloseHandle(process)


def _snapshot_summary(snapshot: dict[str, Any], prefixes: Sequence[str] = ()) -> dict[str, Any]:
    entries = snapshot["entries"]
    if prefixes:
        entries = [entry for entry in entries if any(str(entry.get("path", "")).startswith(p) for p in prefixes)]
    by_scope = Counter(str(entry.get("scope_label", "")) for entry in entries)
    by_type = Counter(str(entry.get("type", "")) for entry in entries)
    return {
        "label": snapshot.get("source", {}).get("label"),
        "entries": len(entries),
        "by_scope": dict(sorted(by_scope.items())),
        "by_type": dict(sorted(by_type.items())),
        "path_prefixes": list(prefixes),
        "paths": [entry.get("path", "") for entry in entries],
        "filenames": snapshot.get("dump", {}).get("filenames", []),
        "reported_scope_counts": snapshot.get("dump", {}).get("reported_scope_counts", {}),
    }


def _print_diff_text(result: dict[str, Any]) -> None:
    before_name = result.get("before_label") or str(result.get("before_sha256") or "snapshot A")[:12]
    after_name = result.get("after_label") or str(result.get("after_sha256") or "snapshot B")[:12]
    print(f"Snapshot A: {before_name}")
    print(f"Snapshot B: {after_name}")
    print(f"Entries: A={result.get('before_entry_count')} B={result.get('after_entry_count')}")
    summary = result["summary"]
    print("Diff summary: " + (", ".join(f"{key}={value}" for key, value in summary.items()) or "no changes"))
    for event in result["events"]:
        if event["kind"] in {"ADDED", "REMOVED"}:
            print(f"{event['kind']} [{event.get('scope')}] {event.get('path')}")
            continue
        before_scope = event.get("before_scope")
        after_scope = event.get("after_scope")
        print(f"CHANGED [{before_scope}->{after_scope}] {event.get('path')} occurrence={event.get('occurrence')}")
        for name, values in event["changes"].items():
            print(f"  {name}: {values.get('before')!r} -> {values.get('after')!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Broker Debug Dump snapshot and diff tool")
    sub = parser.add_subparsers(dest="command", required=True)

    capture = sub.add_parser("capture", help="read the live retail Debug text buffer (read-only)")
    capture.add_argument("--pid", required=True, type=int, help="PID of the verified retail MRallye.exe")
    capture.add_argument("--output", required=True, type=Path, help="snapshot JSON destination; raw .dump.bin is written beside it")
    capture.add_argument("--label", help="optional experiment label; metadata only")

    parse_cmd = sub.add_parser("parse", help="parse an existing raw Debug text capture offline")
    parse_cmd.add_argument("input", type=Path, help="raw text/binary Debug buffer capture")
    parse_cmd.add_argument("--output", required=True, type=Path, help="snapshot JSON destination")
    parse_cmd.add_argument("--label", help="optional experiment label; metadata only")

    summarize = sub.add_parser("summarize", help="print entry/type/scope summary without values")
    summarize.add_argument("snapshot", type=Path)
    summarize.add_argument("--prefix", action="append", default=[], help="case-sensitive path prefix filter; repeatable")
    summarize.add_argument("--json", action="store_true", help="emit JSON summary")

    diff = sub.add_parser("diff", help="compare two snapshots while preserving duplicate rows")
    diff.add_argument("before", type=Path)
    diff.add_argument("after", type=Path)
    diff.add_argument("--prefix", action="append", default=[], help="case-sensitive path prefix filter; repeatable")
    diff.add_argument("--float-tolerance", type=float, default=0.0, help="absolute tolerance for parsed numeric values; default 0")
    diff.add_argument("--ignore-revision-only", action="store_true", help="hide rows whose only change is revision")
    diff.add_argument("--format", choices=("text", "json", "csv"), default="text")
    diff.add_argument("--output", type=Path, help="optional output file for JSON or CSV")
    report = sub.add_parser("persistence-report", help="group emitted rows by SaveFile, scope, types and save bits")
    report.add_argument("snapshot", type=Path)
    report.add_argument("--save-file", help="exact case-sensitive SaveFile identity")
    report.add_argument("--save-mode", choices=tuple(SAVE_MODE_FIELDS))
    report.add_argument("--scope", choices=("GLOBAL", "SCENE", "USER"))
    report.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capture":
            raw, source = capture_debug_buffer(args.pid)
            if args.label:
                source["label"] = args.label
            raw_path = args.output.with_suffix(".dump.bin")
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(raw)
            try:
                snapshot = parse_dump_bytes(raw, source)
            except ObservatoryError as exc:
                raise ObservatoryError(f"{exc}; raw buffer was preserved at {raw_path}") from exc
            snapshot["source"]["raw_sidecar"] = raw_path.name
            write_json(args.output, snapshot)
            print(f"Captured {snapshot['dump']['parsed_entry_count']} entries from verified retail PID {args.pid}.")
            print(f"Snapshot: {args.output}; raw source: {raw_path}")
            print(f"Raw SHA256: {snapshot['source']['raw_sha256']}; selected Dump SHA256: {snapshot['source']['selected_block_sha256']}")
            return 0
        if args.command == "parse":
            raw = args.input.read_bytes()
            source = {"capture_kind": "offline-parse", "input_name": args.input.name}
            if args.label:
                source["label"] = args.label
            snapshot = parse_dump_bytes(raw, source)
            snapshot["source"]["raw_sidecar"] = args.input.name
            write_json(args.output, snapshot)
            print(f"Parsed {snapshot['dump']['parsed_entry_count']} entries from {args.input} -> {args.output}")
            return 0
        if args.command == "summarize":
            summary = _snapshot_summary(load_snapshot(args.snapshot), args.prefix)
            if args.json:
                print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
            else:
                print(f"Entries: {summary['entries']}")
                print("Scopes: " + ", ".join(f"{key}={value}" for key, value in summary["by_scope"].items()))
                print("Types: " + ", ".join(f"{key}={value}" for key, value in summary["by_type"].items()))
                print("Save files: " + ", ".join(summary["filenames"]))
                for path in summary["paths"]:
                    print(path)
            return 0
        if args.command == "diff":
            result = diff_snapshots(
                load_snapshot(args.before),
                load_snapshot(args.after),
                prefixes=args.prefix,
                float_tolerance=args.float_tolerance,
                ignore_revision_only=args.ignore_revision_only,
            )
            if args.format == "text":
                _print_diff_text(result)
            elif args.format == "json":
                payload = json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
                if args.output:
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(payload, encoding="utf-8")
                else:
                    print(payload, end="")
            else:
                rows: list[dict[str, Any]] = []
                for event in result["events"]:
                    if event["kind"] == "CHANGED":
                        for change, values in event["changes"].items():
                            rows.append(
                                {
                                    "kind": change,
                                    "path": event.get("path"),
                                    "before_scope": event.get("before_scope"),
                                    "after_scope": event.get("after_scope"),
                                    "before": json.dumps(values.get("before"), ensure_ascii=True),
                                    "after": json.dumps(values.get("after"), ensure_ascii=True),
                                }
                            )
                    else:
                        rows.append(
                            {
                                "kind": event["kind"],
                                "path": event.get("path"),
                                "before_scope": event.get("scope") if event["kind"] == "REMOVED" else "",
                                "after_scope": event.get("scope") if event["kind"] == "ADDED" else "",
                                "before": "" if event["kind"] == "ADDED" else json.dumps(event.get("entry"), ensure_ascii=True),
                                "after": "" if event["kind"] == "REMOVED" else json.dumps(event.get("entry"), ensure_ascii=True),
                            }
                        )
                from io import StringIO

                buffer = StringIO()
                writer = csv.DictWriter(buffer, fieldnames=("kind", "path", "before_scope", "after_scope", "before", "after"))
                writer.writeheader()
                writer.writerows(rows)
                if args.output:
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(buffer.getvalue(), encoding="utf-8", newline="")
                else:
                    sys.stdout.write(buffer.getvalue())
            return 0
        if args.command == "persistence-report":
            report = persistence_report(load_snapshot(args.snapshot), save_file=args.save_file,
                                        save_mode=args.save_mode, scope=args.scope)
            if args.json:
                print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
            else:
                print_persistence_report(report)
            return 0
    except (OSError, ObservatoryError) as exc:
        print(f"broker_observatory: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
