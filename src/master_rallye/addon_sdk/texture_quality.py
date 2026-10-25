"""Conservative, explicit authoring policy for native MR texture budgets.

Image statistics are protection hints, never recognition of text or materials.
The source-fidelity preset is byte preserving. Other presets are opt-in lossy
authoring choices; capacity pressure is reported rather than silently erasing
important artwork. No proprietary inputs or image-library dependency required.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes

PRESETS = ('source-fidelity', 'balanced', 'performance')
ROLES = ('auto', 'livery', 'text', 'alpha-critical', 'secondary', 'effect')


def image_metrics(texture):
    """Bounded deterministic pixel sampling; high frequency is not text evidence."""
    w, h, pixels = texture.width, texture.height, texture.bgra
    step = max(1, math.ceil(math.sqrt(w * h / 16384)))
    edges = alpha_edges = samples = partial = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            at = (y*w+x)*4
            alpha = pixels[at+3]
            partial += 0 < alpha < 255
            samples += 1
            for xx, yy in ((x+1, y), (x, y+1)):
                if xx >= w or yy >= h:
                    continue
                other = (yy*w+xx)*4
                # Invisible RGB must not masquerade as important artwork.
                if alpha and pixels[other+3]:
                    edges += max(abs(pixels[at+c]-pixels[other+c]) for c in range(3)) >= 40
                alpha_edges += abs(alpha-pixels[other+3]) >= 40
    divisor = max(samples*2, 1)
    return {'sample_count': samples, 'rgb_edge_fraction': edges/divisor,
            'alpha_edge_fraction': alpha_edges/divisor,
            'partial_alpha_fraction': partial/max(samples, 1),
            'interpretation': 'sampled detail/alpha risk only; no text or semantic identification'}


def texture_usage(root: Path):
    """Selected DX UV/area evidence; draw sums may include layered passes."""
    result = {}
    for name in ('car.dx', 'complete.dx', 'wheel.dx'):
        path = root/name
        if not path.exists():
            continue
        model = parse_dx_bytes(path.read_bytes())
        if not model.diagnostics.validated:
            raise ValueError('quality policy requires a validated DX: '+name)
        for draw in model.physical_draws:
            if not draw.index_count:
                continue
            ids = model.draw_global_indices(draw)
            area = uv_area = 0.
            for i in range(0, len(ids), 3):
                a,b,c = (model.vertices.positions[k] for k in ids[i:i+3])
                if not all(math.isfinite(v) for p in (a,b,c) for v in p):
                    raise ValueError('nonfinite texture-usage geometry')
                ab = [b[k]-a[k] for k in range(3)]; ac = [c[k]-a[k] for k in range(3)]
                cross = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]]
                area += math.sqrt(sum(v*v for v in cross))*.5
                if model.uv_sets and draw.flags_0x20[3]:
                    u,v,t = (model.uv_sets[0].values[k] for k in ids[i:i+3])
                    if not all(math.isfinite(n) for uv in (u,v,t) for n in uv):
                        raise ValueError('nonfinite texture-usage UV')
                    uv_area += abs((v[0]-u[0])*(t[1]-u[1])-(v[1]-u[1])*(t[0]-u[0]))*.5
            for slot, stem in enumerate(draw.texture_tuple):
                if stem == 'Null':
                    continue
                if Path(stem).name != stem or '/' in stem or '\\' in stem:
                    raise ValueError('requires local texture references')
                row = result.setdefault(stem, {})
                use = row.setdefault(name, {'base_draws': 0, 'environment_draws': 0, 'surface_area_m2': 0., 'uv_triangle_area': 0.})
                if slot == 0:
                    use['base_draws'] += 1; use['surface_area_m2'] += area; use['uv_triangle_area'] += uv_area
                else:
                    use['environment_draws'] += 1
    return result


def choose_limit(preset, metrics, usage, role='auto', importance=1.):
    if preset not in PRESETS or role not in ROLES:
        raise ValueError('unknown texture preset or role')
    if isinstance(importance, bool) or not isinstance(importance, (int,float)) or not math.isfinite(importance) or not 0 <= importance <= 4:
        raise ValueError('importance must be finite 0..4')
    if preset == 'source-fidelity':
        return None, ['source-fidelity preserves input bytes']
    reasons = []
    limit = 256 if preset == 'balanced' else 128
    area = max((v['surface_area_m2'] for v in usage.values()), default=0.)
    if role in ('livery','text','alpha-critical'):
        return None, ['explicit protected role: '+role]
    if role == 'auto':
        if metrics['alpha_edge_fraction'] > .005:
            return None, ['alpha-edge risk: preserve original']
        if metrics['rgb_edge_fraction'] > .04:
            limit = max(limit, 512 if preset == 'balanced' else 256)
            reasons.append('sampled high-frequency detail')
        if area*importance >= 1.:
            limit = max(limit, 512 if preset == 'balanced' else 256)
            reasons.append('large base-textured surface area')
    reasons.append('explicit opt-in '+preset+' resolution ceiling')
    return limit, reasons


def plan_textures(root: Path, *, preset='source-fidelity', profile=None):
    if preset not in PRESETS:
        raise ValueError('unknown texture preset')
    if profile is None:profile = {'version': 1, 'textures': {}}
    if not isinstance(profile,dict) or set(profile)-{'version','textures'} or type(profile.get('version')) is not int or profile.get('version') != 1 or not isinstance(profile.get('textures'),dict):
        raise ValueError('invalid texture-quality profile')
    usage = texture_usage(root)
    paths = {p.stem:p for p in root.glob('*.dxt')}
    if set(profile['textures'])-set(paths):
        raise ValueError('profile references absent textures')
    rows=[]
    for stem,path in sorted(paths.items()):
        raw=path.read_bytes(); tex=parse_dxt_bytes(raw); metrics=image_metrics(tex)
        settings=profile['textures'].get(stem, {})
        if not isinstance(settings,dict) or set(settings)-{'role','importance','source_sha256','reason'}:
            raise ValueError('unsupported texture quality settings')
        digest=hashlib.sha256(raw).hexdigest()
        if settings.get('source_sha256',digest) != digest:
            raise ValueError('texture quality provenance mismatch: '+stem)
        limit,reasons=choose_limit(preset,metrics,usage.get(stem,{}),settings.get('role','auto'),settings.get('importance',1.))
        factor=1
        while limit and max(tex.width//factor,tex.height//factor)>limit:
            factor*=2
        if min(tex.width//factor,tex.height//factor)<1 or tex.width%factor or tex.height%factor:
            raise ValueError('cannot preserve texture aspect with integer reduction')
        uses=usage.get(stem,{})
        density={name:{**item,'source_texels_per_metre_estimate':math.sqrt(item['uv_triangle_area']*tex.width*tex.height/item['surface_area_m2']) if item['surface_area_m2']>0 else None}
                 for name,item in uses.items()}
        rows.append({'file':path.name,'source_sha256':digest,'source_size':[tex.width,tex.height],
            'output_size':[tex.width//factor,tex.height//factor], 'factor':factor,
            'role':settings.get('role','auto'),'reasons':reasons,'metrics':metrics,'usage':density,
            'referenced':stem in usage,'source_cache_bytes':tex.width*tex.height*4,
            'output_cache_bytes':tex.width*tex.height*4//factor**2})
    return {'version':1,'preset':preset,'textures':rows,
        'source_cache_bytes':sum(x['source_cache_bytes'] for x in rows if x['referenced']),
        'output_cache_bytes':sum(x['output_cache_bytes'] for x in rows if x['referenced']),
        'boundary':'offline image/UV/area policy, not measured screen visibility, OCR, GPU timing or gameplay performance; layered area sums may overlap'}
