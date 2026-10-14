"""Bounded offline frontend session audit; no process memory access."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGS = Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')


def audit():
    session = LOGS / 'session-20261014-082055-35860.jsonl'
    rows, malformed = [], []
    for ordinal, line in enumerate(session.read_text().splitlines(), 1):
        try:
            rows.append(json.loads(line))
        except ValueError:
            malformed.append(ordinal)
    records = [r for r in rows if r.get('type') == 'ps2_frontend_upload_identity']
    frames = []
    for frame in sorted({r['frame'] for r in records}):
        subset = sorted((r for r in records if r['frame'] == frame),
                        key=lambda r: r['source_record_metadata_index'])
        worlds = sorted({tuple(r['world_view_projection'][0]) for r in subset})
        views = sorted({tuple(r['world_view_projection'][1]) for r in subset})
        projections = sorted({tuple(r['world_view_projection'][2]) for r in subset})
        frames.append(dict(frame=frame, records=subset, record_count=len(subset),
                           indices=[r['source_record_metadata_index'] for r in subset],
                           triangles=sum(r['triangles'] for r in subset),
                           world_matrices=worlds, view_matrices=views,
                           projection_matrices=projections))
    inputs = []
    for p in sorted(LOGS.glob('*35860*')):
        inputs.append(dict(name=p.name, size=p.stat().st_size,
                           sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    return dict(schema_version=1, inputs=inputs, malformed_session_lines=malformed,
                grade='CONFIRMED_BY_RUNTIME', runtime_scope='proxy source-upload diagnostics',
                executable=next(r for r in rows if r.get('type') == 'session'),
                frames=frames, owner_cache_join='UNKNOWN', replacement_enabled=False)


if __name__ == '__main__':
    report = audit()
    (ROOT / 'runtime-evidence.json').write_text(json.dumps(report, indent=2) + '\n')
    for f in report['frames']:
        print(f['frame'], f['record_count'], f['indices'], f['triangles'],
              'world classes', len(f['world_matrices']))
