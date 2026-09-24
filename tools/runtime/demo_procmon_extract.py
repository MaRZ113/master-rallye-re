"""Extract bounded Master Rallye resource events from a ProcMon CSV export."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / '.research-output' / 'r-demo2'
OPERATIONS = {'CreateFile', 'ReadFile', 'WriteFile', 'QueryOpen',
              'SetEndOfFile', 'CloseFile'}
REQUIRED = ('Time of Day', 'Process Name', 'PID', 'Operation', 'Path', 'Result', 'Detail')


def extract_events(csv_text: str, path_fragment: str, pid: int | None = None) -> list[dict]:
    reader = csv.DictReader(csv_text.splitlines())
    if not reader.fieldnames or any(name not in reader.fieldnames for name in REQUIRED):
        raise ValueError(f'ProcMon CSV requires columns: {", ".join(REQUIRED)}')
    needle = path_fragment.replace('/', '\\').casefold()
    if not needle or len(needle) < 3:
        raise ValueError('path fragment must identify a resource')
    events = []
    for row in reader:
        if row['Process Name'].casefold() != 'mrallye.exe':
            continue
        try:
            actual_pid = int(row['PID'])
        except (ValueError, TypeError):
            continue
        if pid is not None and actual_pid != pid:
            continue
        if row['Operation'] not in OPERATIONS:
            continue
        if needle not in row['Path'].replace('/', '\\').casefold():
            continue
        events.append({'time': row['Time of Day'], 'pid': actual_pid,
                       'operation': row['Operation'], 'path': row['Path'],
                       'result': row['Result'], 'detail': row['Detail']})
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
    source = args.input.resolve(strict=True)
    output = args.output.resolve()
    root = ROOT.resolve()
    if root not in source.parents or root not in output.parents or source.suffix.lower() != '.csv' or output.suffix.lower() != '.json':
        ap.error('input CSV and output JSON must be under ignored .research-output/r-demo2')
    events = extract_events(read_export(source), args.path_fragment, args.pid)
    report = {'source_csv': source.relative_to(root).as_posix(),
              'path_fragment': args.path_fragment, 'pid_filter': args.pid,
              'matched_count': len(events), 'events': events}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'matched_count': len(events), 'output': str(output)}))


if __name__ == '__main__':
    main()
