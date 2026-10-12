"""Audit exact native publication/consumer/store intervals; never authorizes writes."""
import argparse
import json
from pathlib import Path

PUBLISH = "0x004CCFF1"
COMPLETE = "0x004CD131"
CLEAR_SITES = {"0x004CCC70", "0x004CD1A1", "0x004CD1DE", "0x00591345", "0x004CB62A"}

def audit(records):
    setups = [r for r in records if r.get("type") == "physics_probe_setup"]
    summaries = [r for r in records if r.get("type") == "physics_probe_summary"]
    captures = [r for r in records if r.get("type") == "physics_probe_transaction_summary"]
    setup = setups[-1] if setups else {}
    summary = summaries[-1] if summaries else {}
    capture = captures[-1] if captures else {}
    events = [r for r in records if r.get("type") == "physics_probe_transaction_event"]
    loss = (not capture or any(capture.get(k, 0) for k in
        ("important_overflow", "diagnostic_overflow", "pairing_failures", "unknown_transitions", "in_flight_store_observations"))
        or any(summary.get("counts", {}).get(k, 0) for k in
        ("dropped_tracks", "same_controller_overlap_calls", "identity_changes", "invalid_native_snapshots")))
    healthy = (setup.get("installed") is True and setup.get("exact_retail_build") is True
        and summary.get("patch_restored") is True and not loss)
    groups = {}
    unknown = []
    for event in events:
        candidate = event.get("reset_transaction_candidate_id", 0)
        if candidate:
            # IDs are invocation labels, not proof: all native ownership/content gates below remain necessary.
            groups.setdefault(candidate, []).append(event)
        else:
            unknown.append(event.get("event_sequence"))
    results = []
    for candidate, rows in sorted(groups.items()):
        rows.sort(key=lambda r: (r.get("qpc_timestamp", 0), r.get("event_sequence", 0)))
        errors = []
        pubs = [r for r in rows if r.get("native_callsite") == PUBLISH]
        matrices = [r for r in rows if r.get("native_callsite") == COMPLETE]
        consumers = [r for r in rows if r.get("event_kind") == "controller_consumption" and r.get("flag_value_before") == 1]
        clears = [r for r in rows if r.get("native_callsite") in CLEAR_SITES
            and r.get("flag_value_before") == 1 and r.get("flag_value_after") == 0]
        zero = [r for r in rows if r.get("event_kind") == "controller_consumption" and r.get("flag_value_before") == 0]
        if len(pubs) != 1: errors.append("missing_or_ambiguous_publication")
        if len(matrices) != 1: errors.append("missing_or_ambiguous_matrix_completion")
        if not consumers: errors.append("no_active_consumer")
        if len(clears) != 1: errors.append("missing_or_ambiguous_actual_clear")
        if not zero: errors.append("no_subsequent_zero_consumer")
        if any(r.get("event_kind")=="flag_store" and
            (not r.get("store_completion_observed") or not r.get("store_result_matches_operand")
             or r.get("native_store_value") != r.get("flag_value_after")) for r in rows):
            errors.append("native_store_result_not_verified")
        identity_keys = ("race_generation", "owner_lifetime", "controller_identity", "controller_identity_generation", "controller_backing_pointer")
        if any(len({r.get(k) for r in rows}) != 1 for k in identity_keys): errors.append("identity_changed")
        if (any(not r.get("race_context_valid") or not r.get("current_human_candidate")
            or not r.get("observation_readable") or r.get("unknown_transition_before") for r in rows)
            or any(not rows[0].get(k) or rows[0].get(k) == "0x00000000" for k in identity_keys)):
            errors.append("invalid_current_native_identity_or_unknown_transition")
        if len({r.get("thread_id") for r in rows}) != 1 or not rows[0].get("thread_id"):
            errors.append("cross_thread_happens_before_unproved")
        seq = [r.get("event_sequence", 0) for r in rows]
        if len(set(seq)) != len(seq) or any(a >= b for a, b in zip(seq, seq[1:])):
            errors.append("event_sequence_order_conflict")
        if any(not r.get("qpc_timestamp") or r.get("qpc_after",0) < r.get("qpc_timestamp",0) for r in rows):
            errors.append("invalid_native_timestamps")
        if any(a.get("qpc_after",0) >= b.get("qpc_timestamp",0) for a,b in zip(rows,rows[1:])):
            errors.append("overlapping_native_observations")
        if pubs and matrices:
            pub, matrix = pubs[0], matrices[0]
            if (pub.get("flag_value_after") != 1 or matrix.get("flag_value_before") != 1 or matrix.get("flag_value_after") != 1
                or not pub.get("reset_manager_identity") or pub.get("reset_manager_identity") == "0x00000000"
                or pub.get("reset_manager_identity") != matrix.get("reset_manager_identity")
                or pub.get("participant_index") is None or pub.get("participant_index") != matrix.get("participant_index")
                or not 0 <= pub.get("participant_index", -1) < 8): errors.append("recovery_owner_or_phase_mismatch")
            target = matrix.get("transform_bits")
            if not isinstance(target, list) or len(target) != 16 or matrix.get("transform_bits_before") != target:
                errors.append("matrix_completion_unreadable_or_unstable")
            for row in consumers + clears + zero:
                if (row.get("transform_bits_before") != target or row.get("transform_bits") != target
                    or row.get("transform_digest") != matrix.get("transform_digest")):
                    errors.append("transform_content_mismatch"); break
            for clear in clears:
                if clear.get("native_callsite") in {"0x004CCC70","0x004CD1A1","0x004CD1DE"} and clear.get("reset_manager_identity") != pub.get("reset_manager_identity"):
                    errors.append("clear_reset_manager_mismatch")
            if clears and consumers and zero:
                ordered = [pub,matrix,*consumers,clears[0],zero[0]]
                if any(a.get("qpc_after",0) >= b.get("qpc_timestamp",0) for a,b in zip(ordered,ordered[1:])):
                    errors.append("publication_consume_clear_zero_order_not_proved")
        if not healthy: errors.append("capture_not_lossless_or_hooks_not_restored")
        results.append({"candidate_id":candidate,"status":"OBSERVED_STOCK_TRANSACTION" if not errors else "INCOMPLETE_TRANSACTION",
            "active_consumer_calls":len(consumers),"repeated_application_observed":len(consumers)>1,
            "clear_writer":clears[0].get("native_callsite") if len(clears)==1 else None,
            "event_sequences":seq,"failures":sorted(set(errors))})
    return {"status":"STOCK_TRANSACTION_CORRELATED" if any(r["status"] == "OBSERVED_STOCK_TRANSACTION" for r in results) else "NEEDS_TRANSACTION_CAPTURE",
        "transactions":results,"unattributed_event_sequences":unknown,"capture_loss_or_unknown_transition":loss,
        "writer_coverage_exhaustive":False,"one_shot_guaranteed":False,"teleport_authorized_by_this_report":False,
        "decisive_invariant":"exclusive single-use ownership of backing flag across native recovery and input/restore writers is unproved"}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    records=[json.loads(line) for line in args.session.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    text=json.dumps(audit(records),indent=2)+"\n"
    if args.output: args.output.write_text(text,encoding="utf-8")
    else: print(text,end="")
if __name__=="__main__": main()
