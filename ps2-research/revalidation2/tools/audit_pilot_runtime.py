#!/usr/bin/env python3
"""Summarize supplied PILOT1.3 sessions, screenshots and optional F10 frames.

The report stores hashes and selected fields only. It never copies screenshots,
logs, or original game data. Screenshot-to-mode pairing is ordinal and must be
treated as correlation unless a separate capture manifest exists.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

TARGET_ARGS = [4, 11940, 28, 22944, 48]
STATE_IDS = {
    "ZENABLE": 7,
    "ZWRITEENABLE": 14,
    "ALPHATESTENABLE": 15,
    "ZFUNC": 23,
    "ALPHAREF": 24,
    "ALPHAFUNC": 25,
    "ALPHABLENDENABLE": 27,
    "SRCBLEND": 19,
    "DESTBLEND": 20,
}
STATE_NAMES = {value: key for key, value in STATE_IDS.items()}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Read dimensions from a JPEG SOF marker without external libraries."""
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("not a JPEG stream")
    pos = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while pos < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            break
        marker = data[pos]
        pos += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if pos + 2 > len(data):
            break
        length = int.from_bytes(data[pos:pos + 2], "big")
        if length < 2 or pos + length > len(data):
            raise ValueError("invalid JPEG segment length")
        if marker in sof:
            if length < 7:
                raise ValueError("truncated JPEG SOF segment")
            height = int.from_bytes(data[pos + 3:pos + 5], "big")
            width = int.from_bytes(data[pos + 5:pos + 7], "big")
            if width <= 0 or height <= 0:
                raise ValueError("invalid JPEG dimensions")
            return width, height
        pos += length
    raise ValueError("JPEG dimensions not found")


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    malformed = 0
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(value, dict):
                rows.append(value)
            else:
                malformed += 1
    return rows, malformed


def selected_state_values(draw: dict[str, Any]) -> dict[str, Any]:
    state = draw.get("state")
    render = state.get("render_states") if isinstance(state, dict) else None
    if not isinstance(render, dict):
        return {}
    return {name: render.get(str(index)) for name, index in STATE_IDS.items() if str(index) in render}


def capture_frame_number(path_or_name: str) -> int | None:
    match = re.search(r"-(\d+)\.jsonl$", Path(path_or_name).name)
    return int(match.group(1)) if match else None


def audit_frame(path: Path) -> dict[str, Any]:
    rows, malformed = read_jsonl(path)
    matching = [
        row for row in rows
        if row.get("type") == "draw"
        and row.get("method") == "DrawIndexedPrimitive"
        and isinstance(row.get("arguments"), list)
        and row["arguments"][:5] == TARGET_ARGS
    ]
    summaries = [row for row in rows if row.get("type") == "frame_summary"]
    endings = [row for row in rows if row.get("type") == "frame_end"]
    draw = matching[0] if len(matching) == 1 else None
    ending = endings[-1] if endings else {}
    summary = summaries[-1] if summaries else {}
    begin = next((row for row in rows if row.get("type") == "frame_begin"), {})
    draw_sequence = draw.get("sequence") if draw else None
    local_native_events = [
        row for row in rows
        if row.get("type") == "native_override"
        and row.get("method") == "SetRenderState"
        and isinstance(row.get("sequence"), int)
        and isinstance(draw_sequence, int)
        and draw_sequence - 4 <= row["sequence"] <= draw_sequence + 4
        and row.get("feature_mask") == 128
    ]
    before = [row for row in local_native_events if row["sequence"] < draw_sequence]
    after = [row for row in local_native_events if row["sequence"] > draw_sequence]
    before_state_ids = {
        row["arguments"][0] for row in before
        if isinstance(row.get("arguments"), list) and len(row["arguments"]) >= 2
        and isinstance(row["arguments"][0], int)
    }
    after_values = {
        row["arguments"][0]: row["arguments"][1] for row in after
        if isinstance(row.get("arguments"), list) and len(row["arguments"]) >= 2
        and isinstance(row["arguments"][0], int)
    }
    snapshot = selected_state_values(draw) if draw else {}
    restoration_matches = bool(before_state_ids) and before_state_ids == set(after_values) and all(
        after_values[state_id] == snapshot.get(STATE_NAMES.get(state_id, ""))
        for state_id in before_state_ids
    )

    def native_event_summary(row: dict[str, Any]) -> dict[str, Any]:
        args = row.get("arguments", [])
        state_id = args[0] if len(args) > 0 and isinstance(args[0], int) else None
        return {
            "sequence": row.get("sequence"),
            "state_id": state_id,
            "state_name": STATE_NAMES.get(state_id),
            "value": args[1] if len(args) > 1 else None,
            "hresult": row.get("result"),
            "native_only": row.get("native_only"),
            "forwarded": row.get("forwarded"),
        }
    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "malformed_lines": malformed,
        "frame_summary_count": len(summaries),
        "frame_draw_count": ending.get("draw_records"),
        "frame_primitive_total": summary.get("primitive_total"),
        "frame_complete": ending.get("complete"),
        "frame_truncated": ending.get("truncated"),
        "frame_dropped_records": ending.get("dropped_records"),
        "frame": draw.get("frame") if draw else begin.get("frame"),
        "capture_id": begin.get("capture_id"),
        "target_draw_matches": len(matching),
        "target_draw": ({
            "frame": draw.get("frame"),
            "sequence": draw.get("sequence"),
            "draw_index_zero_based": draw.get("draw_index"),
            "arguments": draw.get("arguments"),
            "result": draw.get("result"),
            "native_override_applied_field": draw.get("native_override_applied"),
            "state_snapshot": snapshot,
            "native_state_events_before": [native_event_summary(row) for row in before],
            "native_state_events_after": [native_event_summary(row) for row in after],
            "restoration_matches_pre_draw_snapshot": restoration_matches,
        } if draw else None),
        "evidence_note": "Frame-record state is the state snapshot stored by this trace schema; it is not assumed to be the temporary native state during an override.",
    }


def audit_session(path: Path, logs_dir: Path, supplied_frames: dict[int, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    rows, malformed = read_jsonl(path)
    types: dict[str, int] = {}
    for row in rows:
        kind = row.get("type")
        if isinstance(kind, str):
            types[kind] = types.get(kind, 0) + 1
    headers = [row for row in rows if row.get("type") == "session"]
    modes = [row for row in rows if row.get("type") == "ps2_port_mode_selected"]
    identities = [row for row in rows if row.get("type") == "ps2_port_draw_identity"]
    capture_rows = [row for row in rows if row.get("type") == "capture_written"]
    header = headers[0] if len(headers) == 1 else {}
    mode = modes[0] if len(modes) == 1 else None
    target = identities[0] if len(identities) == 1 else None
    captures = []
    for row in capture_rows:
        raw = row.get("path")
        name = Path(raw).name if isinstance(raw, str) else None
        captures.append({
            "basename": name,
            "reported_complete_file": row.get("complete_file"),
            "exists_in_supplied_logs_dir": bool(name and (logs_dir / name).is_file()),
            "capture_frame_number": capture_frame_number(name) if name else None,
        })
        frame_number = captures[-1]["capture_frame_number"]
        candidates = (supplied_frames or {}).get(frame_number, [])
        captures[-1]["matched_supplied_capture"] = (
            {"file": candidates[0]["file"], "capture_id": candidates[0].get("capture_id")}
            if len(candidates) == 1 else None
        )
    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "malformed_lines": malformed,
        "event_type_counts": dict(sorted(types.items())),
        "executable_sha256": header.get("exe_sha256"),
        "proxy_sha256": header.get("proxy_sha256"),
        "mode_event_count": len(modes),
        "selected_mode": ({
            "mode": mode.get("mode"),
            "mode_name": mode.get("mode_name"),
            "requested_mask": mode.get("requested_mask"),
            "applied_mask_at_selection": mode.get("applied_mask"),
            "override_applied_at_selection": mode.get("override_applied"),
        } if mode else None),
        "identity_event_count": len(identities),
        "target_identity": ({
            "frame": target.get("frame"),
            "identity": target.get("identity"),
            "geometry_sha256": target.get("geometry_sha256"),
            "vertex_generation": target.get("vertex_generation"),
            "index_generation": target.get("index_generation"),
            "vertex_revision": target.get("vertex_revision"),
            "index_revision": target.get("index_revision"),
            "mode": target.get("mode"),
            "mode_name": target.get("mode_name"),
            "requested_mask": target.get("requested_mask"),
            "applied_mask": target.get("applied_mask"),
            "override_applied": target.get("override_applied"),
            "pre_draw_restore_ok": target.get("pre_draw_restore_ok"),
        } if target else None),
        "capture_references": captures,
    }


def audit_screenshot(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    width, height = jpeg_dimensions(data)
    return {
        "file": path.name,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "width": width,
        "height": height,
        "filesystem_mtime_local": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="milliseconds"),
    }


def build_report(logs_dir: Path, screenshots_dir: Path, sessions: Iterable[str], screenshots: Iterable[str], reference_frames: Iterable[Path]) -> dict[str, Any]:
    session_names = list(sessions)
    screenshot_names = list(screenshots)
    if len(session_names) != len(screenshot_names):
        raise ValueError("session and screenshot lists must have equal length for ordinal correlation")
    frame_reports = [audit_frame(path) for path in reference_frames]
    frame_index: dict[int, list[dict[str, Any]]] = {}
    for frame in frame_reports:
        if isinstance(frame.get("frame"), int):
            frame_index.setdefault(frame["frame"], []).append(frame)
    session_reports = [audit_session(logs_dir / name, logs_dir, frame_index) for name in session_names]
    screenshot_reports = [audit_screenshot(screenshots_dir / name) for name in screenshot_names]
    pairs = []
    for index, (session, shot) in enumerate(zip(session_reports, screenshot_reports)):
        selected = session.get("selected_mode") or {}
        pairs.append({
            "session": session["file"],
            "selected_mode": selected.get("mode"),
            "mode_name": selected.get("mode_name"),
            "screenshot": shot["file"],
            "association": "ordinal capture sequence supplied by user; supported by file times, not embedded screenshot metadata",
            "sequence_index": index,
        })
    return {
        "schema": "ps2-pilot13-runtime-audit-v1",
        "target_draw_arguments_prefix": TARGET_ARGS,
        "source_roots": {"logs_directory_name": logs_dir.name, "screenshots_directory_name": screenshots_dir.name},
        "session_reports": session_reports,
        "screenshot_reports": screenshot_reports,
        "ordinal_correlations": pairs,
        "reference_frames": frame_reports,
        "limitations": [
            "Malformed/truncated JSONL lines are counted but their contents are not retained.",
            "Screenshots do not embed the selected mode; pairing relies on ordinal sequence and filesystem times.",
            "No claim is made that frame snapshots show temporary override states.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", type=Path, required=True)
    parser.add_argument("--screenshots-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sessions", nargs="+", default=[f"session-{i}.jsonl" for i in range(1, 5)])
    parser.add_argument("--screenshots", nargs="+", default=[f"{i}.jpg" for i in range(4)])
    parser.add_argument("--reference-frame", action="append", type=Path, default=[])
    args = parser.parse_args()
    report = build_report(args.logs_dir, args.screenshots_dir, args.sessions, args.screenshots, args.reference_frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "sessions": len(report["session_reports"]),
        "screenshots": len(report["screenshot_reports"]),
        "reference_frames": len(report["reference_frames"]),
        "target_override_modes": [r["selected_mode"]["mode"] for r in report["session_reports"] if r.get("selected_mode") and r.get("target_identity")],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"runtime audit failed: {exc}")
