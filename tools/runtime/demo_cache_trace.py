"""Classify observed demo cache traces and compare serialized IO traversals."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

try:
    from .demo_procmon_extract import ROOT, extract_events, read_export
except ImportError:  # direct script execution
    from demo_procmon_extract import ROOT, extract_events, read_export


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ('%d.%m.%Y %H:%M:%S', '%d.%m.%Y %H:%M:%S.%f'):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


def compare_traversals(writes: list[dict], reads: list[dict]) -> dict:
    wp = [(e.get('offset'), e.get('length')) for e in writes if e.get('offset') is not None and e.get('length') is not None and e.get('result') == 'SUCCESS']
    rp = [(e.get('offset'), e.get('length')) for e in reads if e.get('offset') is not None and e.get('length') is not None and e.get('result') == 'SUCCESS']
    matching = 0
    first_divergence = None
    for index in range(max(len(wp), len(rp))):
        w, r = (wp[index] if index < len(wp) else None), (rp[index] if index < len(rp) else None)
        if w == r:
            matching += 1
        elif first_divergence is None:
            first_divergence = {'index': index, 'write': w, 'read': r}
    offsets = sorted(wp, key=lambda p: (p[0], p[1]))
    gaps, overlaps = [], []
    cursor = 0
    for offset, length in offsets:
        if offset > cursor:
            gaps.append([cursor, offset])
        elif offset < cursor:
            overlaps.append([offset, min(cursor, offset + length)])
        cursor = max(cursor, offset + length)
    return {'write_pair_count': len(wp), 'read_pair_count': len(rp), 'matching_pair_count': matching,
            'exact_match': bool(wp) and wp == rp, 'first_divergence': first_divergence,
            'gaps': gaps, 'overlaps': overlaps, 'final_serialized_size': cursor}


def analyze_events(events: list[dict]) -> dict:
    by_path: dict[str, list[dict]] = {}
    for event in events:
        by_path.setdefault(event['path'].casefold(), []).append(event)
    paths = list(by_path.values())
    source_events, cache_events = [], []
    for group in paths:
        path = group[0]['path'].casefold()
        if path.endswith(('.gxm', '.gxi')):
            source_events = group
        elif path.endswith(('.dx', '.dxt')):
            cache_events = group
    source_path = source_events[0]['path'] if source_events else None
    cache_path = cache_events[0]['path'] if cache_events else None
    def existed_at_probe(group):
        opens = [e for e in group if e['operation'] == 'CreateFile']
        if opens:
            first = opens[0]
            if first['result'] in ('NAME NOT FOUND', 'PATH NOT FOUND'):
                return False
            return first['result'] == 'SUCCESS'
        return any(e['operation'] in ('QueryAllInformationFile', 'QueryBasicInformationFile', 'ReadFile') and e['result'] not in ('NAME NOT FOUND', 'PATH NOT FOUND') for e in group)
    source_exists, cache_exists = existed_at_probe(source_events), existed_at_probe(cache_events)
    def metadata(group, before_row=None):
        info = {}
        for event in group:
            if before_row is not None and event['row'] >= before_row:
                continue
            if event['operation'] in ('QueryAllInformationFile', 'QueryBasicInformationFile'):
                for key in ('last_write_time', 'end_of_file', 'allocation_size'):
                    if key in event and key not in info:
                        info[key] = event[key]  # retain metadata seen before any rebuild write
        return info
    first_write_row = min((e['row'] for e in cache_events if e['operation'] == 'WriteFile' and e['result'] == 'SUCCESS'), default=None)
    smeta, cmeta = metadata(source_events), metadata(cache_events, before_row=first_write_row)
    source_reads = [e for e in source_events if e['operation'] == 'ReadFile' and e['result'] == 'SUCCESS']
    cache_reads = [e for e in cache_events if e['operation'] == 'ReadFile' and e['result'] == 'SUCCESS']
    cache_writes = [e for e in cache_events if e['operation'] == 'WriteFile' and e['result'] == 'SUCCESS']
    cache_creates = [e for e in cache_events if e['operation'] == 'CreateFile']
    cache_probe_result = cache_creates[0]['result'] if cache_creates else None
    source_bytes = sum(e.get('length', 0) or 0 for e in source_reads)
    cache_bytes_read = sum(e.get('length', 0) or 0 for e in cache_reads)
    cache_bytes_written = sum(e.get('length', 0) or 0 for e in cache_writes)
    source_time, cache_time = _timestamp(smeta.get('last_write_time')), _timestamp(cmeta.get('last_write_time'))
    open_results = {str(e.get('open_result', '')).casefold() for e in cache_creates}
    cache_created = 'created' in open_results
    cache_overwritten = 'overwritten' in open_results
    read_session = []
    header_probe = False
    for event in cache_events:
        if event['operation'] == 'CloseFile':
            if [(e.get('offset'), e.get('length')) for e in read_session] == [(0, 4), (4, 4)]:
                header_probe = True
            read_session = []
        elif event['operation'] == 'ReadFile' and event['result'] == 'SUCCESS':
            read_session.append(event)
    serialized_size = compare_traversals(cache_writes, [])['final_serialized_size'] if cache_writes else 0
    expected_cache_size = cmeta.get('end_of_file') or serialized_size
    cache_fully_read = bool(cache_reads and expected_cache_size and max((e.get('offset', 0) + (e.get('length') or 0) for e in cache_reads), default=0) >= expected_cache_size)
    eof_events = [e for e in cache_events if e['operation'] == 'ReadFile' and e['result'] == 'END OF FILE']
    gxi_dxt = bool(source_path and source_path.casefold().endswith('.gxi'))
    if gxi_dxt and source_exists and not cache_exists and cache_writes:
        classification = 'GXI_DXT_CACHE_MISS'
    elif not source_exists and cache_exists and cache_fully_read and not cache_writes:
        classification = 'SOURCE_MISSING_COMPILED_FALLBACK'
    elif source_exists and not cache_exists and cache_writes:
        classification = 'CACHE_MISS_BUILD'
    elif source_exists and cache_exists and source_time and cache_time and source_time > cache_time and cache_writes and cache_overwritten:
        classification = 'STALE_CACHE_REBUILD'
    elif source_exists and cache_exists and source_time and cache_time and cache_time > source_time and not source_reads and not cache_writes and cache_fully_read:
        classification = 'FRESH_CACHE_HIT'
    else:
        classification = 'UNKNOWN'
    first_write_row = min((e['row'] for e in cache_writes), default=None)
    reload_reads = [e for e in cache_reads if first_write_row is None or e['row'] > max(w['row'] for w in cache_writes)]
    traversal = compare_traversals(cache_writes, reload_reads)
    return {'source_path': source_path, 'compiled_path': cache_path, 'source_exists': source_exists,
            'cache_exists': cache_exists, 'cache_probe_result': cache_probe_result,
            'source_last_write_time': smeta.get('last_write_time'),
            'cache_last_write_time': cmeta.get('last_write_time'), 'source_body_read': bool(source_reads),
            'source_read_event_count': len(source_reads), 'source_bytes_read': source_bytes,
            'cache_created': cache_created, 'cache_overwritten': cache_overwritten,
            'cache_written': bool(cache_writes), 'cache_write_event_count': len(cache_writes),
            'cache_bytes_written': cache_bytes_written, 'cache_header_probe': header_probe,
            'cache_fully_read': cache_fully_read, 'cache_read_event_count': len(cache_reads),
            'cache_bytes_read': cache_bytes_read, 'cache_eof_size': cmeta.get('end_of_file'),
            'cache_eof_probe_count': len(eof_events),
            'cache_eof_probes': [{'offset': e.get('offset'), 'length': e.get('length'), 'result': e['result']} for e in eof_events],
            'writer_reader_traversal': traversal, 'classification': classification}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--path-fragment', required=True)
    ap.add_argument('--pid', type=int)
    args = ap.parse_args()
    source, output, root = args.input.resolve(strict=True), args.output.resolve(), ROOT.resolve()
    if root not in source.parents or root not in output.parents or source.suffix.lower() != '.csv' or output.suffix.lower() != '.json':
        ap.error('input CSV and output JSON must be under ignored .research-output/r-demo2')
    events = extract_events(read_export(source), args.path_fragment, args.pid)
    report = {'source_csv': source.relative_to(root).as_posix(), 'path_fragment': args.path_fragment,
              'pid_filter': args.pid, 'matched_event_count': len(events), **analyze_events(events)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('classification', 'source_read_event_count', 'cache_write_event_count', 'cache_read_event_count', 'writer_reader_traversal')}))


if __name__ == '__main__':
    main()
