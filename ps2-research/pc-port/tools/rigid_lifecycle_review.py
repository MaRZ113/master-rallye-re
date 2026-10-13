"""Offline bounded lifecycle evidence summary; never accesses a game process.

Observed vector membership is not destruction, a course certificate, an
admission thread, contact proof, resource ownership or pointer-generation ID.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

EXE_SHA = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"


def summarize(rows):
    if not 2 <= len(rows) <= 1201:
        raise ValueError("Expected header and at most1200 bounded samples")
    header = rows[0]
    identity = header.get("process", {})
    if (header.get("schema") != "mrr-rigid-readonly-v1"
            or header.get("event") != "header"
            or identity.get("sha256") != EXE_SHA
            or identity.get("image_base") != 0x400000
            or header.get("engine_calls") is not False
            or header.get("process_writes") is not False):
        raise ValueError("Unsupported or non-read-only capture identity")
    result = {"schema": "rigid-lifecycle-review-v1", "identity": identity,
              "samples": len(rows)-1, "status_counts": {}, "vector_membership_changes": [],
              "observed_pointer_pairs": [], "course_certificate": "UNKNOWN",
              "function_order": "UNKNOWN", "physics_thread": "UNKNOWN",
              "private_resource_ownership": "UNKNOWN", "native_destruction": "UNKNOWN",
              "vehicle_contact": "NOT_PROVED", "injected_objects": False}
    pairs = {}; last_membership = None; previous_time = -1
    for expected_sequence, row in enumerate(rows[1:]):
        seconds = row.get("monotonic_seconds")
        if (row.get("event") != "snapshot" or row.get("sequence") != expected_sequence
                or not isinstance(seconds, (float, int)) or not math.isfinite(seconds)
                or not previous_time <= seconds <= 61
                or not 0 <= row.get("read_bytes", -1) <= 65536):
            raise ValueError("Invalid sequence/time/read-budget metadata")
        previous_time = seconds
        status = row.get("status")
        if status not in ("READ_SNAPSHOT_NOT_ATOMIC", "NOT_INITIALIZED", "NO_INSTALLED_BACKEND", "FAILED_CLOSED"):
            raise ValueError("Unknown snapshot status")
        result["status_counts"][status] = result["status_counts"].get(status, 0) + 1
        if status != "READ_SNAPSHOT_NOT_ATOMIC":
            continue
        instances = row.get("instances", [])
        count = row.get("native_instance_vector_count")
        if (not isinstance(instances, list) or len(instances) > 16
                or not isinstance(count, int) or not len(instances) <= count <= 8192
                or row.get("selected_count") != len(instances)):
            raise ValueError("Inconsistent bounded native-vector count")
        membership = tuple((i.get("instance"), i.get("body"), i.get("egg_name_id")) for i in instances)
        if (count, membership) != last_membership:
            result["vector_membership_changes"].append({"sequence": expected_sequence,
                "seconds": seconds, "native_count": count,
                "selection_truncated": row.get("selection_truncated"),
                "selected_pointer_membership": [list(x) for x in membership]})
            last_membership = (count, membership)
        for i in instances:
            if i.get("status") != "READ_SNAPSHOT_NOT_ATOMIC":
                continue
            key = (i.get("instance"), i.get("body"))
            if key not in pairs:
                pairs[key] = {"instance": key[0], "body": key[1], "body_vtable": i.get("body_vtable"),
                    "category": i.get("category"), "name_id": i.get("egg_name_id"),
                    "samples": 0, "first_seconds": seconds, "last_seconds": seconds,
                    "instance_cache_zero_samples": 0, "body_cache_zero_samples": 0,
                    "positions_observed": 0, "runtime_role": "UNKNOWN",
                    "pointer_generation": "NOT_ESTABLISHED"}
            p = pairs[key]; p["samples"] += 1; p["last_seconds"] = seconds
            p["instance_cache_zero_samples"] += int(i.get("resolved_egg_cache") == 0)
            p["body_cache_zero_samples"] += int(i.get("body_resolved_egg_cache") == 0)
            position = i.get("native_nonvehicle_position")
            if position is not None:
                if len(position) != 3 or not all(isinstance(x, (float,int)) and math.isfinite(x) for x in position):
                    raise ValueError("Invalid observed XYZ")
                p["positions_observed"] += 1
                if "xyz_min" not in p:
                    p["xyz_min"] = list(position); p["xyz_max"] = list(position)
                else:
                    p["xyz_min"] = [min(a,b) for a,b in zip(p["xyz_min"],position)]
                    p["xyz_max"] = [max(a,b) for a,b in zip(p["xyz_max"],position)]
    result["duration_seconds"] = previous_time
    result["observed_pointer_pairs"] = [pairs[k] for k in sorted(pairs)]
    return result


def summarize_debugger(text, passive):
    """Capped logpoint text only; no inferred uncaptured call/return pairs."""
    records = []
    for line_number,line in enumerate(text.splitlines(),1):
        if "RIGID_PROBE event=" not in line:
            continue
        fields = dict(re.findall(r"(\w+)=([^\s]+)",line))
        if not {"event","tid","ip","ecx","hit"}.issubset(fields):
            raise ValueError("Incomplete native logpoint line")
        for key in fields:
            if key != "event":
                fields[key] = int(fields[key],10 if key == "hit" else 16)
        if not 1 <= fields['hit'] <= 16:
            raise ValueError("Logpoint exceeds declared hit cap")
        fields['line'] = line_number; records.append(fields)
    if not records or len(records) > 224:
        raise ValueError("Expected1..224 bounded logpoint observations")
    counts = {}; threads = set(); clone_links = []
    for record in records:
        event=record['event'];counts[event]=counts.get(event,0)+1;threads.add(record['tid'])
        if event != 'instance_clone_enter':continue
        later=next((r for r in records if r['line']>record['line']
                    and r['tid']==record['tid'] and r['event']=='body_bind_enter'
                    and r['ecx']==record['ecx']),None)
        if later is None:continue
        matched=[p for p in passive['observed_pointer_pairs']
                 if (p['instance'],p['body'])==(record['ecx'],later.get('arg0'))]
        clone_links.append({'clone_line':record['line'],'bind_line':later['line'],
            'instance':record['ecx'],'prototype_argument':record.get('arg0'),
            'body':later.get('arg0'),'thread':record['tid'],
            'exact_passive_pointer_pair_match':bool(matched),
            'pairing':'same thread and explicit instance pointer; not generic entry/RET pairing'})
    update_clear=[]
    for record in records:
        if record['event']!='physics_update_enter':continue
        following=next((r for r in records if r['line']>record['line']
            and r['tid']==record['tid'] and r['event'] in
            ('physics_update_enter','instance_cache_clear_enter')),None)
        if following and following['event']=='instance_cache_clear_enter':
            update_clear.append({'update_line':record['line'],'clear_line':following['line'],
                                 'thread':record['tid']})
    return {'schema':'rigid-capped-debugger-review-v1','records':len(records),
        'event_counts':dict(sorted(counts.items())),'observed_thread_ids':sorted(threads),
        'independently_capped_events':[k for k,v in sorted(counts.items()) if v==16],
        'clone_body_passive_links':clone_links,'update_followed_by_clear_observations':update_clear,
        'body_registration_observed':counts.get('body_register_enter',0)>0,
        'private_admission':'NOT_IMPLEMENTED','native_prop_admission':'NOT_PROVED',
        'target_body_destruction':'NOT_PROVED; early Egg logpoint caps are not target teardown',
        'thread_scope':'observed calls in this process/session only; not a new mutation permission',
        'instruction_order_scope':'log line order; hit counters are independent and not a call-frame ID'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--debugger-log", type=Path)
    args = parser.parse_args()
    if args.input.stat().st_size > 16*1024*1024:
        raise ValueError("Capture exceeds16MiB diagnostic limit")
    data = args.input.read_bytes()
    result = summarize([json.loads(line) for line in data.decode("utf-8-sig").splitlines()])
    result["source_sha256"] = hashlib.sha256(data).hexdigest()
    if args.debugger_log:
        if args.debugger_log.stat().st_size>16*1024*1024:
            raise ValueError("Debugger log exceeds16MiB diagnostic limit")
        log=args.debugger_log.read_bytes()
        result['debugger']=summarize_debugger(log.decode('utf-8-sig'),result)
        result['debugger']['source_sha256']=hashlib.sha256(log).hexdigest()
    with args.output.open("x", encoding="utf-8") as f:
        f.write(json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"samples": result["samples"], "statuses": result["status_counts"],
                      "membership_changes": len(result["vector_membership_changes"])}))


if __name__ == "__main__": main()
