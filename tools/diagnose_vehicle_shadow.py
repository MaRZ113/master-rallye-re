"""Generate a source-bound shadow profile and top-view footprint comparison."""
import argparse
import base64
import html
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools')]
from master_rallye.addon_sdk.vehicle_shadow import generate_profile, bind_profile
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes, encode_png, PNG_ROWS_FLIP_VERTICAL


def hull(points):
    points = sorted(set(points))
    if len(points) < 3:
        return points
    cross = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    def side(ps):
        result = []
        for p in ps:
            while len(result) >= 2 and cross(result[-2], result[-1], p) <= 0:
                result.pop()
            result.append(p)
        return result
    return side(points)[:-1] + side(reversed(points))[:-1]


def render_topview(model_data, texture_data, bound):
    """Render static flat-ground blob mapping, never a live GPU observation."""
    outline = hull([(p[0], p[2]) for p in parse_dx_bytes(model_data).vertices.positions])
    # Native V grows with +Z; +Z is up in this plot, hence stored rows flip.
    raster = base64.b64encode(encode_png(parse_dxt_bytes(texture_data), row_policy=PNG_ROWS_FLIP_VERTICAL)).decode()
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="840" viewBox="0 0 1080 840">',
           '<rect width="1080" height="840" fill="#eef1f5"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#1b2634}.small{font-size:14px}</style>',
           '<text x="35" y="34" font-size="22">'+html.escape(bound['profile']['runtime_family'])+' body and native projected blob: top view</text>',
           '<text x="35" y="60" class="small">Static mapping on flat ground, full shadow strength. Front is up. Cyan = render convex outline.</text>']
    scale = 76
    for index, (title, key) in enumerate((('Original shared blob and native bounds', 'native'), ('Generated shadow-only bounds', 'generated'))):
        cx, cz = bound[key + '_quad_center_xz_m']; w, length = bound[key + '_quad_size_xz_m']
        tx = 280 + index * 520
        out += [f'<text x="{tx - 230}" y="94" font-size="18">{html.escape(title)}</text>',
            f'<g transform="translate({tx},450) scale({scale})">']
        for k in range(-4, 5):
            out += [f'<path d="M -2.8 {k} H 2.8 M {k} -4.2 V 4.2" stroke="#d2d9e1" stroke-width=".008"/>']
        out += [f'<image href="data:image/png;base64,{raster}" x="{cx - w / 2}" y="{-cz - length / 2}" width="{w}" height="{length}"/>',
            '<polygon points="' + ' '.join(f'{x},{-z}' for x, z in outline) + '" fill="#1bafc8" fill-opacity=".15" stroke="#008ca6" stroke-width=".025"/>',
            '<path d="M -.15 0 H .15 M 0 -.15 V .15" stroke="#d44847" stroke-width=".018"/>', '</g>',
            f'<text x="{tx - 220}" y="795" class="small">Quad: {w:.3f} m wide, {length:.3f} m long; center Z {cz:+.3f} m</text>']
    out += ['<text x="35" y="826" class="small">Actual alpha also depends on terrain height and vehicle transform. Antenna/decorations may affect the body outline.</text>', '</svg>']
    return '\n'.join(out) + '\n'


def diagnose(model, texture, family, output, *, profile=None, **controls):
    model_data = model.read_bytes(); texture_data = texture.read_bytes()
    p = json.loads(profile.read_text()) if profile else generate_profile(model_data, texture_data, family, **controls)
    if p['runtime_family'] != family:
        raise ValueError('shadow diagnostic family mismatch')
    bound = bind_profile(p, model_data, texture_data)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'shadow-profile.json').write_text(json.dumps(p, indent=2) + '\n')
    (output / 'shadow-diagnostic.json').write_text(json.dumps(bound, indent=2) + '\n')
    (output / 'shadow-topview.svg').write_text(render_topview(model_data, texture_data, bound), encoding='utf-8')
    return bound


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, required=True); p.add_argument('--texture', type=Path, required=True)
    p.add_argument('--family', required=True); p.add_argument('--output', type=Path, required=True); p.add_argument('--profile', type=Path)
    for axis in ('x', 'z'):
        p.add_argument('--scale-' + axis, type=float, default=1.)
        p.add_argument('--offset-' + axis + '-m', type=float, default=0.)
        p.add_argument('--margin-' + axis + '-m', type=float, default=.05 if axis == 'x' else .10)
    p.add_argument('--alpha-threshold', type=int, default=32)
    a = vars(p.parse_args()); model = a.pop('model'); texture = a.pop('texture'); family = a.pop('family'); output = a.pop('output')
    result = diagnose(model, texture, family, output, **a)
    print(json.dumps({k: result[k] for k in ('native_alpha_support_xz_m', 'generated_alpha_support_xz_m', 'runtime_qualified')}))
