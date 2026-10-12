#!/usr/bin/env python3
"""Compare two bounded R-CAM1-A3h.1 UI ownership F10 captures.

Raw addresses are capture evidence only. A paused-only record is not a
semantic PauseMenu classification; only a validated owner-name mapping can
establish that relationship.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number}: JSONL row is not an object")
        rows.append(value)
    return rows


def _frame_capture(path: Path) -> dict[str, Any]:
    rows = read_jsonl(path)
    begin = next((r for r in rows if r.get("type") == "frame_begin"), None)
    end = next((r for r in reversed(rows) if r.get("type") == "frame_end"), None)
    race_snapshot = next((r for r in rows if r.get("type") == "race_epoch_snapshot"), None)
    if begin is None:
        return {"path": str(path), "available": False, "reason": "frame_begin_missing", "records": []}
    ui = begin.get("ui_margins")
    probe = ui.get("ui_ownership_probe") if isinstance(ui, dict) else None
    if not isinstance(probe, dict):
        return {"path": str(path), "available": False, "reason": "ownership_probe_missing", "records": [], "frame_begin": begin}
    records = probe.get("draw_records")
    if not isinstance(records, list):
        records = []
    return {
        "path": str(path), "available": True, "frame_begin": begin, "frame_end": end,
        "probe": probe, "race_snapshot": race_snapshot,
        "pause_menu": race_snapshot.get("pause_menu") if isinstance(race_snapshot, dict) else None,
        "records": [r for r in records if isinstance(r, dict)],
    }


def _identity_key(row: dict[str, Any]) -> tuple[Any, ...] | None:
    fields = ("native_entity_pointer", "native_packet_pointer", "point_storage", "content_storage", "packet_mode")
    values = tuple(row.get(field) for field in fields)
    if any(value is None for value in values):
        return None
    return values


def _capture_health(capture: dict[str, Any]) -> dict[str, Any]:
    if not capture.get("available"):
        return {"status": "missing", "complete": False, "overflow": False, "unmapped_records": 0}
    probe = capture["probe"]
    overflow = bool(probe.get("overflow")) or int(probe.get("record_drops", 0) or 0) > 0 or int(probe.get("identity_registry_overflow", 0) or 0) > 0
    frame_end = capture.get("frame_end")
    frame_complete = bool(frame_end and frame_end.get("complete") and not frame_end.get("truncated"))
    complete = bool(probe.get("complete")) and frame_complete and not overflow
    records = capture["records"]
    unmapped = sum(1 for r in records if r.get("owner_mapping_status", "unmapped") != "mapped" or not r.get("owner_name"))
    return {
        "status": "overflow" if overflow else "complete" if complete else "incomplete",
        "complete": complete, "overflow": overflow,
        "frame_file_complete": frame_complete,
        "reported_coverage_status": probe.get("coverage_status", "unknown"),
        "reported_unmapped": probe.get("unmapped"), "unmapped_records": unmapped,
        "draw_attempts": probe.get("draw_attempts"), "draw_records": len(records),
        "record_drops": probe.get("record_drops", 0),
        "identity_registry_overflow": probe.get("identity_registry_overflow", 0),
        "owner_mapping_status": probe.get("owner_mapping_status", "unknown"),
    }


def analyze(normal_path: Path, paused_path: Path, session_path: Path | None = None) -> dict[str, Any]:
    normal = _frame_capture(normal_path)
    paused = _frame_capture(paused_path)
    nkeys = {_identity_key(r) for r in normal["records"]}
    pkeys = {_identity_key(r) for r in paused["records"]}
    nkeys.discard(None)
    pkeys.discard(None)
    normal_by_entity: dict[Any, set[tuple[Any, ...]]] = {}
    paused_by_entity: dict[Any, set[tuple[Any, ...]]] = {}
    for key in nkeys:
        normal_by_entity.setdefault(key[0], set()).add(key)
    for key in pkeys:
        paused_by_entity.setdefault(key[0], set()).add(key)
    changed_entities = []
    for entity in sorted(set(normal_by_entity) & set(paused_by_entity), key=lambda value: str(value)):
        before, after = normal_by_entity[entity], paused_by_entity[entity]
        if before != after:
            changed_entities.append({
                "native_entity_pointer": entity,
                "normal_packet_identities": sorted([list(k[1:]) for k in before], key=str),
                "paused_packet_identities": sorted([list(k[1:]) for k in after], key=str),
                "interpretation": "raw_pointer_tuple_changed_or_submission_set_changed; lifetime identity is unproven",
            })

    known_names = sorted({str(r["owner_name"]) for r in normal["records"] + paused["records"]
                          if r.get("owner_mapping_status") == "mapped" and r.get("owner_name")})
    def pause_signal(capture: dict[str, Any]) -> dict[str, Any]:
        state = capture.get("pause_menu")
        if not isinstance(state, dict):
            return {"available": False, "enabled": None, "status": "snapshot_or_pause_field_missing"}
        return {"available": bool(state.get("available")), "enabled": state.get("enabled"),
                "status": state.get("status", "unknown"), "read_only": state.get("read_only") is True,
                "source": state.get("source", "unknown")}
    normal_pause = pause_signal(normal)
    paused_pause = pause_signal(paused)
    pause_signal_changed = (normal_pause["available"] and paused_pause["available"] and
                            isinstance(normal_pause["enabled"], bool) and isinstance(paused_pause["enabled"], bool) and
                            normal_pause["enabled"] != paused_pause["enabled"])
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R-CAM1-A3h.1",
        "status": "READY_FOR_A3H_ANALYSIS" if normal.get("available") and paused.get("available") else "INCOMPLETE_INPUT",
        "semantic_pause_ownership_proven": False,
        "warning": "paused-only means observed only in the manually labeled paused capture; it does not prove PauseMenu ownership",
        "capture_pair": {
            "normal": {"path": str(normal_path), "capture_id": normal.get("frame_begin", {}).get("capture_id") if normal.get("available") else None,
                       "device": normal.get("frame_begin", {}).get("device") if normal.get("available") else None,
                       "health": _capture_health(normal)},
            "paused": {"path": str(paused_path), "capture_id": paused.get("frame_begin", {}).get("capture_id") if paused.get("available") else None,
                       "device": paused.get("frame_begin", {}).get("device") if paused.get("available") else None,
                       "health": _capture_health(paused)},
        },
        "raw_identity_comparison": {
            "shared_raw_tuples": [list(k) for k in sorted(nkeys & pkeys, key=str)],
            "normal_only_raw_tuples": [list(k) for k in sorted(nkeys - pkeys, key=str)],
            "paused_only_raw_tuples": [list(k) for k in sorted(pkeys - nkeys, key=str)],
            "entities_with_changed_packet_identity_sets": changed_entities,
            "identity_basis": ["native_entity_pointer", "native_packet_pointer", "point_storage", "content_storage", "packet_mode"],
            "pointer_lifetime_caveat": "raw addresses are compared for this pair only; reuse across scene lifetimes is not excluded",
        },
        "owner_mapping": {
            "known_owner_names": known_names,
            "unknown_draw_records": sum(1 for r in normal["records"] + paused["records"]
                                         if r.get("owner_mapping_status", "unmapped") != "mapped" or not r.get("owner_name")),
            "status": "mapped" if known_names else "unmapped",
        },
        "pause_state_signal": {
            "normal_capture": normal_pause, "paused_capture": paused_pause,
            "typed_values_differ": pause_signal_changed if normal_pause["available"] and paused_pause["available"] else None,
            "semantic_interpretation": "typed Broker state is corroboration only; capture labels and visible menu remain the operator's normal/paused ground truth",
        },
        "classification": {
            "shared": "raw identity tuple present in both manually labeled captures",
            "paused_only": "raw identity tuple present only in paused capture; owner remains unproven",
            "normal_only": "raw identity tuple present only in normal capture",
        },
    }
    if session_path is not None:
        session_rows = read_jsonl(session_path)
        session = next((r for r in session_rows if r.get("type") == "session"), {})
        ends = {r.get("capture_id"): r for r in session_rows if r.get("type") == "ui_ownership_capture_end"}
        frames = [normal, paused]
        session_matches = []
        for capture in frames:
            if not capture.get("available"):
                session_matches.append(False)
                continue
            capture_id = capture["probe"].get("capture_id")
            session_matches.append(capture_id in ends)
        headers_match = bool(session) and all(
            capture.get("available") and
            capture["frame_begin"].get("exe_sha256") == session.get("exe_sha256") and
            capture["frame_begin"].get("proxy_sha256") == session.get("proxy_sha256")
            for capture in frames
        )
        same_device = bool(normal.get("available") and paused.get("available") and
                           normal["frame_begin"].get("device") == paused["frame_begin"].get("device"))
        report["session_validation"] = {
            "session_path": str(session_path), "session_header_found": bool(session),
            "frame_hashes_match_session": headers_match,
            "same_device_id": same_device,
            "normal_capture_end_found": session_matches[0],
            "paused_capture_end_found": session_matches[1],
            "same_session_supported": headers_match and same_device and all(session_matches),
            "capture_end_records": {k: ends.get(k) for k in [normal.get("probe", {}).get("capture_id"), paused.get("probe", {}).get("capture_id")] if k},
        }
    if not normal.get("available") or not paused.get("available"):
        report["status"] = "INCOMPLETE_INPUT"
    elif not _capture_health(normal)["complete"] or not _capture_health(paused)["complete"]:
        report["status"] = "INCOMPLETE_CAPTURE"
    elif session_path is not None and not report["session_validation"]["same_session_supported"]:
        report["status"] = "SESSION_OR_BUILD_MISMATCH"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path)
    parser.add_argument("--normal-frame", required=True, type=Path)
    parser.add_argument("--paused-frame", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.normal_frame, args.paused_frame, args.session)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result["status"] == "READY_FOR_A3H_ANALYSIS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
