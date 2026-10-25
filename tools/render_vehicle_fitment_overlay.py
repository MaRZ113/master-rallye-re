"""Draw source/native hub overlays from a sealed offline fitment diagnostic.

Position-only orthographic diagnostic: triangles ignore material alpha, and
native hubs are unloaded attachment frames, not a settled gameplay capture.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes


def render(model_raw, report):
    if hashlib.sha256(model_raw).hexdigest()!=report['model_sha256']:
        raise ValueError('fitment model differs from diagnostic')
    model=parse_dx_bytes(model_raw)
    if not model.diagnostics.validated:raise ValueError('invalid fitment model')
    rows=report['rows']
    if len(rows)!=4:raise ValueError('four matched source/native hubs required')
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="660" viewBox="0 0 1000 660">',
           '<rect width="1000" height="660" fill="#f5f7fa"/>',
           '<g font-family="Segoe UI, sans-serif" fill="#243142">',
           f'<text x="24" y="30" font-size="20">{html.escape(report["family"])} — source/native fitment</text>',
           '<text x="24" y="52" font-size="13">Green: qualified source hubs. Red: native attachments. Dashed: retained collision AABB.</text>']
    positions=model.vertices.positions
    bbox=report['collision_aabb_m']
    for top in (False,True):
        cy=225 if not top else 505
        scale=105
        def point(v):return (500+v[2]*scale,cy-v[0 if top else 1]*scale)
        parts.append(f'<text x="24" y="{90 if not top else 360}" font-size="16">{"Top X/Z" if top else "Side Y/Z"} — metres, body frame</text>')
        for draw in model.physical_draws:
            indices=model.draw_global_indices(draw)
            for i in range(0,len(indices)-2,3):
                ps=[point(positions[j]) for j in indices[i:i+3]]
                parts.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in ps)+'" fill="#c5ccd5" fill-opacity=".45"/>')
        if bbox:
            corners=[point(v) for v in ((bbox[0][0],bbox[0][1],bbox[0][2]),(bbox[1][0],bbox[1][1],bbox[1][2]))]
            x=min(p[0] for p in corners);y=min(p[1] for p in corners)
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{abs(corners[1][0]-corners[0][0]):.2f}" height="{abs(corners[1][1]-corners[0][1]):.2f}" fill="none" stroke="#64748b" stroke-dasharray="7 4"/>')
        for row in rows:
            if not top and not row['positive_x']:continue
            native=point(row['native_attachment']);source=point(row['source_reference_hub'])
            parts.append(f'<line x1="{native[0]:.2f}" y1="{native[1]:.2f}" x2="{source[0]:.2f}" y2="{source[1]:.2f}" stroke="#475569"/>')
            for p,color,key in ((source,'#168047','visual_radial_envelope_m'),(native,'#c83535','physical_radius_m')):
                radius=4 if top else row[key]*scale
                parts.append(f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="{radius:.2f}" fill="none" stroke="{color}" stroke-width="2"/>')
                parts.append(f'<path d="M{p[0]-5:.2f},{p[1]:.2f}h10 M{p[0]:.2f},{p[1]-5:.2f}v10" stroke="{color}"/>')
    parts+=['<text x="24" y="624" font-size="13">Unloaded native/reference comparison only; no tyre contact, spring equilibrium, camber, steering or alpha simulation.</text>',
            '<text x="24" y="646" font-size="12">Body triangles are a position-only backdrop. This diagnostic does not change model, collision or physics.</text></g></svg>']
    return '\n'.join(parts)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',type=Path,required=True);p.add_argument('--diagnostic',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    svg=render(a.model.read_bytes(),json.loads(a.diagnostic.read_text()))
    if a.output.exists():raise ValueError('new overlay path required')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(svg,encoding='utf-8');print(a.output)
