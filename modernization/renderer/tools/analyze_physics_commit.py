"""Read-only native Reset capture audit; never certifies a teleport contract."""
import argparse
import json
from pathlib import Path


def analyze_session(records):
    setups = [r for r in records if r.get("type") == "physics_probe_setup"]
    summaries = [r for r in records if r.get("type") == "physics_probe_summary"]
    setup = setups[-1] if setups else {}
    summary = summaries[-1] if summaries else {}
    capture = summary.get("clear_writer_capture", {})
    counts = summary.get("counts", {})
    clears = []
    for row in records:
        if row.get("type") != "physics_probe_clear_writer_event":
            continue
        if row.get("apply_flag_before") != 1 or row.get("native_store_value") != 0:
            continue
        # A pre-store sample alone does not prove the native store completed.
        # Require a later consumer observation of the cleared flag on the same
        # current human candidate, same backing and same thread for correlation.
        subsequent = []
        for event in records:
            if event.get("type") != "physics_probe_event":
                continue
            if event.get("event") != "controller_transform_consumer":
                continue
            before = event.get("before", {})
            if (before.get("controller") == row.get("controller")
                    and before.get("backing") == row.get("backing")
                    and before.get("thread_id") == row.get("thread_id")
                    and before.get("apply_flag_P_plus_0x33") == 0
                    and before.get("qpc", 0) > row.get("qpc", 0)):
                subsequent.append(before["qpc"])
        current_human = (row.get("owner_known") is True
                         and row.get("owner_links_current") is True
                         and row.get("player_type") == 1)
        consumer_thread = row.get("last_flagged_consumer_thread", 0)
        consumer_qpc = row.get("last_flagged_consumer_qpc", 0)
        ordered = (consumer_thread == row.get("thread_id")
                   and 0 < consumer_qpc < row.get("qpc", 0))
        clears.append({
            "writer": row.get("writer"), "store_va": row.get("store_va"),
            "flag_address": row.get("flag_address"),
            "current_human_candidate": current_human,
            "flagged_consumer_calls": row.get("interval_flagged_consumer_calls"),
            "consumer_precedes_store_same_thread": ordered,
            "later_zero_consumer_same_thread": bool(subsequent),
            "consumer_in_progress": row.get("consumer_in_progress"),
            "pause_state": row.get("pause_state"),
            "store_completion_observed": row.get("store_completion_observed", False),
            "evidence": "pre_store_native_clear_with_later_zero" if subsequent else "pre_store_only",
        })
    losses = bool(counts.get("dropped_events", 0) or counts.get("dropped_tracks", 0)
                  or (not capture and counts.get("clear_writer_events_dropped", 0))
                  or capture.get("transition_overflow", 0)
                  or counts.get("same_controller_overlap_calls", 0)
                  or counts.get("identity_changes", 0)
                  or counts.get("invalid_native_snapshots", 0))
    attributed = any(c["current_human_candidate"]
                     and c["consumer_precedes_store_same_thread"]
                     and c["later_zero_consumer_same_thread"]
                     and c["consumer_in_progress"] is False for c in clears)
    adequate = (setup.get("installed") is True
                and setup.get("exact_retail_build") is True
                and summary.get("patch_restored") is True
                and capture.get("policy") == "transition_priority_v1"
                and capture.get("all_sampled_store_transitions_retained") is True
                and not losses and attributed)
    return {
        "status": "STOCK_CLEAR_ATTRIBUTION_CAPTURED" if adequate else "NEEDS_CLEAR_ATTRIBUTION_CAPTURE",
        "flag_rises_observed": counts.get("flag_rises_observed"),
        "flag_clears_observed": counts.get("flag_clears_observed"),
        "flag_set_consumer_calls": counts.get("flag_set_consumer_calls"),
        "clear_writer_capture": capture,
        "clear_candidates": clears,
        "capture_loss_or_overlap": losses,
        "legacy_capture": not bool(capture),
        "one_shot_guaranteed": False,
        "teleport_authorized_by_this_report": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.session.read_text(encoding="utf-8-sig").splitlines()
               if line.strip()]
    result = json.dumps(analyze_session(records), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
