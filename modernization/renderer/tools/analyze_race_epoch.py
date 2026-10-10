"""Summarize bounded A3c F10 lifecycle records, without granting a race certificate."""
import argparse
import json
from pathlib import Path

MAX_FILE = 64 * 1024 * 1024
MAX_LINE = 2 * 1024 * 1024


def summarize(record):
    if record.get('type') != 'race_epoch_snapshot' or record.get('phase') != 'R-CAM1-A3c':
        raise ValueError('Not an A3c race-epoch snapshot')
    if record.get('camera_writes_authorized') is not False:
        raise ValueError('Observation pilot must not authorize camera writes')
    events, jobs = record.get('events', []), record.get('jobs', [])
    if not isinstance(events, list) or len(events) > 128 or not isinstance(jobs, list) or len(jobs) > 64:
        raise ValueError('Lifecycle capture exceeds fixed bounds')
    previous = 0
    for event in events:
        serial = event.get('serial')
        if type(serial) is not int or not previous < serial <= (1 << 64) - 1:
            raise ValueError('Invalid or out-of-order event serial')
        previous = serial
    executions = [e for e in events if e.get('event') in ('execute_begin', 'execute_return')]
    owners = []
    for event in events:
        if event.get('event') != 'owner_attach':
            continue
        lifetime = event.get('job_lifetime', 0)
        starts = [e for e in executions if e.get('event') == 'execute_begin' and
                  e.get('job_lifetime') == lifetime and e['serial'] < event['serial']]
        ends = [e for e in executions if e.get('event') == 'execute_return' and
                e.get('job_lifetime') == lifetime and e['serial'] < event['serial']]
        relation = 'inside_observed_callback' if lifetime and starts and not ends else 'outside_or_missing_callback_history'
        owners.append(dict(actor=event.get('actor'), lifetime=event.get('owner_lifetime'),
                           generation=event.get('generation'), relation=relation,
                           event_serial=event['serial']))
    return dict(
        diagnostic_only=True, camera_writes_authorized=False,
        status='BLOCKED_ON_RACE_EPOCH_CORRELATION',
        request_generation=record.get('request_generation'),
        successful_generation=record.get('successful_generation'),
        native_observer_installed=record.get('installed'),
        ownership_intact=record.get('hook_ownership_intact'),
        poisoned=record.get('poisoned'), reason=record.get('reason'),
        course_identity_verified=record.get('course_identity_verified'),
        current_owner=record.get('owner'), supporting_context=record.get('offline_context_supported'),
        requests=[dict(serial=e['serial'], generation=e.get('generation'), scene=e.get('scene'))
                  for e in events if e.get('event') == 'request'],
        jobs=jobs, owner_observations=owners,
        errors=[e for e in events if e.get('event') in ('open_error', 'read_or_decode_error', 'rejected')],
        overwritten_events=record.get('ring_overwritten', 0),
        warning='Observed ordering is evidence for review; it does not prove a complete Freecam gate.')


def read_snapshots(path):
    if path.stat().st_size > MAX_FILE:
        raise ValueError('Capture exceeds 64 MiB')
    found = []
    with path.open('rb') as stream:
        line_number = 0
        while line := stream.readline(MAX_LINE + 1):
            line_number += 1
            if len(line) > MAX_LINE:
                raise ValueError(f'Capture line {line_number} exceeds 2 MiB')
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record, dict) and record.get('type') == 'race_epoch_snapshot':
                if len(found) == 8:
                    raise ValueError('Select a single F10 file, not an aggregate session')
                found.append(summarize(record))
    if not found:
        raise ValueError('No race_epoch_snapshot; use the newly generated F10 frame file')
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    print(json.dumps(read_snapshots(args.capture), indent=2))


if __name__ == '__main__':
    main()
