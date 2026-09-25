"""Parse bounded ProcMon CSV exports, including the real extended column set."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / '.research-output' / 'r-demo2'
OPERATIONS = {'CreateFile', 'ReadFile', 'WriteFile', 'CloseFile', 'QueryOpen',
              'QueryAllInformationFile', 'QueryInformationVolume', 'QueryBasicInformationFile',
              'FileSystemControl', 'SetEndOfFile'}
REQUIRED = ('Time of Day', 'Process Name', 'PID', 'Operation', 'Path', 'Result', 'Detail')
NUMBER = r'([\d\s\u00a0\u202f]+)'
OFFSET_LENGTH = re.compile(r'Offset\s*:\s*' + NUMBER + r'\s*,\s*Length\s*:\s*' + NUMBER, re.I)
FIELD_PATTERNS = {
    'last_write_time': re.compile(r'LastWriteTime\s*:\s*([^,]+)', re.I),
    'end_of_file': re.compile(r'EndOfFile\s*:\s*' + NUMBER, re.I),
    'allocation_size': re.compile(r'AllocationSize\s*:\s*' + NUMBER, re.I),
    'desired_access': re.compile(r'Desired Access\s*:\s*([^,]+)', re.I),
    'disposition': re.compile(r'Disposition\s*:\s*([^,]+)', re.I),
    'open_result': re.compile(r'OpenResult\s*:\s*([^,]+)', re.I),
}


def parse_procmon_number(value: str) -> int | None:
    compact = re.sub(r'[\s\u00a0\u202f]', '', value)
    return int(compact) if compact.isdigit() else None


def parse_detail(detail: str) -> dict:
    parsed = {}
    pair = OFFSET_LENGTH.search(detail)
    if pair:
        parsed['offset'] = parse_procmon_number(pair.group(1))
        parsed['length'] = parse_procmon_number(pair.group(2))
    for name, pattern in FIELD_PATTERNS.items():
        match = pattern.search(detail)
        if match:
            value = match.group(1).strip()
            parsed[name] = parse_procmon_number(value) if name in ('end_of_file', 'allocation_size') else value
    return parsed


def extract_events(csv_text: str, path_fragment: str, pid: int | None = None) -> list[dict]:
    reader = csv.DictReader(csv_text.splitlines())
    if not reader.fieldnames or any(name not in reader.fieldnames for name in REQUIRED):
        raise ValueError(f'ProcMon CSV requires columns: {", ".join(REQUIRED)}')
    needle = path_fragment.replace('/', '\\').casefold()
    if not needle or len(needle) < 3:
        raise ValueError('path fragment must identify a resource')
    events = []
    for row_index, row in enumerate(reader):
        if (row.get('Process Name') or '').casefold() != 'mrallye.exe':
            continue
        try:
            actual_pid = int(row['PID'])
        except (ValueError, TypeError):
            continue
        if pid is not None and actual_pid != pid:
            continue
        operation = row.get('Operation', '')
        if operation not in OPERATIONS:
            continue
        path = row.get('Path') or ''
        if needle not in path.replace('/', '\\').casefold():
            continue
        event = {'time': row.get('Time of Day', ''), 'pid': actual_pid,
                 'operation': operation, 'path': path, 'result': row.get('Result', ''),
                 'detail': row.get('Detail', ''), 'row': row_index}
        if row.get('Sequence'):
            event['sequence'] = row['Sequence']
        event.update(parse_detail(event['detail']))
        events.append(event)
    return events


def read_export(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    return raw.decode('utf-8-sig', errors='replace')


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
              'pid_filter': args.pid, 'matched_count': len(events), 'events': events}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'matched_count': len(events), 'output': str(output)}))


if __name__ == '__main__':
    main()
