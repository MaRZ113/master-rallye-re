"""P0.1 coverage report: merge runtime coverage ledgers (CoverageLedger=1) into
one per-course report of what the atmosphere lights and what it does not.

    python course_coverage_report.py --logs <MRRRenderer/logs> --output <dir>
           [--reports <SDK batch reports dir>]

Every coverage-<pid>.json in --logs is merged (all sessions). Rows are keyed by
course, texture identity, FVF, verdict and reason; triangles/draws are summed.
--reports (course_lighting_batch.py output/reports) adds material names and
texture thumbnails by texture identity. Output: index.html, summary.json and
unlit.csv. Read-only on its inputs.
"""
from __future__ import annotations

import argparse
import collections
import csv
import html
import json
import shutil
from pathlib import Path

LIT = {'Lit'}
QUIET = {'Native control'}


def load_ledgers(logs: Path) -> tuple[dict, list[str]]:
    rows: dict = {}
    sources = []
    for path in sorted(logs.glob('coverage-*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if data.get('type') != 'atmosphere_coverage_ledger':
            continue
        sources.append(path.name)
        for r in data.get('rows', []):
            key = (r['course'], r['texture_sha256'], r['fvf'], r['verdict'], r['reason'])
            row = rows.setdefault(key, dict(r, draws=0, triangles=0, frames=0))
            row['draws'] += r['draws']
            row['triangles'] += r['triangles']
            row['frames'] += r['frames']
            if not row.get('material') and r.get('material'):
                row['material'] = r['material']
    return rows, sources


def load_identities(reports: Path | None) -> dict:
    """texture sha -> (material, thumbnail path, offline verdict)."""
    out = {}
    if not reports or not reports.is_dir():
        return out
    for report in reports.glob('*/report.json'):
        try:
            data = json.loads(report.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for m in data.get('materials', []):
            thumb = report.parent / m['thumbnail'] if m.get('thumbnail') else None
            for sha in m.get('texture_identities', []):
                out.setdefault(sha, (m['material'], thumb, m.get('offline_verdict', '')))
    return out


def build(logs: Path, output: Path, reports: Path | None) -> dict:
    rows, sources = load_ledgers(logs)
    ids = load_identities(reports)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'thumbs').mkdir(exist_ok=True)
    courses = collections.defaultdict(list)
    for r in rows.values():
        material, thumb, offline = ids.get(r['texture_sha256'], ('', None, ''))
        r['material'] = r.get('material') or material
        r['offline_verdict'] = offline
        r['thumbnail'] = None
        if thumb and thumb.is_file():
            name = r['texture_sha256'][:16] + thumb.suffix
            target = output / 'thumbs' / name
            if not target.exists():
                shutil.copyfile(thumb, target)
            r['thumbnail'] = 'thumbs/' + name
        courses[r['course']].append(r)

    summary = {'schema': 1, 'ledgers': sources, 'courses': {}}
    sections = []
    unlit_rows = []
    for course in sorted(courses, key=str.lower):
        items = courses[course]
        by_verdict = collections.Counter()
        for r in items:
            by_verdict[r['verdict']] += r['triangles']
        total = sum(by_verdict.values()) or 1
        summary['courses'][course] = {k: round(v * 100 / total, 2) for k, v in by_verdict.most_common()}
        open_rows = sorted((r for r in items if r['verdict'] not in LIT | QUIET),
                           key=lambda r: -r['triangles'])
        unlit_rows += open_rows
        bars = ''.join(f'<li>{html.escape(k)}: {v * 100 / total:.1f}%</li>' for k, v in by_verdict.most_common())
        table = ''.join(
            '<tr><td>' + (f'<img src="{r["thumbnail"]}">' if r['thumbnail'] else '—') + '</td>'
            f'<td>{html.escape(r["material"] or "?")}</td><td><code>{r["texture_sha256"][:12]}</code></td>'
            f'<td>0x{r["fvf"]:x}</td><td>{html.escape(r["verdict"])}</td><td>{html.escape(r["reason"])}</td>'
            f'<td>{r["triangles"]}</td><td>{r["frames"]}</td><td>{html.escape(r["offline_verdict"])}</td></tr>'
            for r in open_rows[:200])
        sections.append(f'<h2>{html.escape(course)}</h2><ul>{bars}</ul>'
                        '<table><tr><th></th><th>material</th><th>texture</th><th>FVF</th><th>verdict</th>'
                        f'<th>reason</th><th>triangles</th><th>frames</th><th>SDK</th></tr>{table}</table>')

    style = ('body{font:14px system-ui;background:#151923;color:#ddd;margin:24px}table{border-collapse:collapse;margin-bottom:24px}'
             'td,th{padding:4px 8px;border-bottom:1px solid #334;text-align:left}img{width:48px;height:48px;image-rendering:pixelated}'
             'code{color:#9cf}h2{margin-top:32px}')
    (output / 'index.html').write_text(
        f'<!doctype html><meta charset="utf-8"><title>Atmosphere coverage</title><style>{style}</style>'
        f'<h1>Atmosphere coverage</h1><p>Ledgers: {len(sources)}. Runtime verdicts from CoverageLedger=1; '
        'shares are by submitted triangles. "Not reached" = taken by another replacement before the atmosphere path.</p>'
        + ''.join(sections), encoding='utf-8')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with (output / 'unlit.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['course', 'material', 'texture_sha256', 'fvf', 'verdict', 'reason', 'triangles', 'frames', 'sdk_verdict'])
        for r in unlit_rows:
            w.writerow([r['course'], r['material'], r['texture_sha256'], hex(r['fvf']), r['verdict'], r['reason'],
                        r['triangles'], r['frames'], r['offline_verdict']])
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--logs', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--reports', type=Path)
    a = ap.parse_args()
    summary = build(a.logs, a.output, a.reports)
    for course, shares in summary['courses'].items():
        print(course, shares)
    print('ledgers:', len(summary['ledgers']), '->', a.output / 'index.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
