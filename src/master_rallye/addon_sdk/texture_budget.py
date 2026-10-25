"""Offline texture residency checks for the qualified retail MR build.

0053CDF0 initializes a 32 MiB texture-manager budget at +0x38. 0053D2F0
charges original width*height*4 at +0x30 (not compressed size, GPU format or
TextureQuality), then evicts least-recently-used resources. These checks do
not emulate the whole renderer or establish a frame-rate guarantee.
"""
from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes

RETAIL_TEXTURE_CACHE_BYTES = 32 * 1024 * 1024
RETAIL_EXE_SHA256 = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
# Authoring policy, NOT a separate native limit. Reserve half for UI/world/AI.
DEFAULT_VEHICLE_TEXTURE_BUDGET = RETAIL_TEXTURE_CACHE_BYTES // 2


def texture_working_set(root: Path) -> dict:
    textures = {}
    models = {}
    for name in ('car.dx', 'complete.dx', 'wheel.dx'):
        model = parse_dx_bytes((root / name).read_bytes())
        sequence = [s for d in model.physical_draws for s in d.texture_tuple if s != 'Null']
        for stem in sequence:
            if Path(stem).name != stem or '/' in stem or '\\' in stem:
                raise ValueError('texture budget requires local texture stems: ' + stem)
            if stem not in textures:
                t = parse_dxt_bytes((root / (stem + '.dxt')).read_bytes())
                if t.width & (t.width - 1) or t.height & (t.height - 1):
                    raise ValueError('native texture dimensions must be powers of two: ' + stem)
                textures[stem] = {'width': t.width, 'height': t.height,
                                  'cache_bytes': t.width * t.height * 4}
        models[name] = {'unique_textures': len(set(sequence)),
                        'cache_bytes': sum(textures[s]['cache_bytes'] for s in set(sequence)),
                        'request_sequence': sequence}
    return {'native_cache_bytes': RETAIL_TEXTURE_CACHE_BYTES,
            'native_evidence_build_sha256': RETAIL_EXE_SHA256,
            'accounting': 'original DXT width*height*4, independent of TextureQuality and GPU format',
            'unique_textures': len(textures),
            'cache_bytes': sum(t['cache_bytes'] for t in textures.values()),
            'models': models, 'textures': textures,
            'runtime_fps_confirmed': False}


def require_vehicle_budget(report: dict, limit: int = DEFAULT_VEHICLE_TEXTURE_BUDGET) -> dict:
    if not 0 < limit < RETAIL_TEXTURE_CACHE_BYTES:
        raise ValueError('vehicle texture budget must leave native cache headroom')
    if report['cache_bytes'] > limit:
        raise ValueError(f"vehicle texture working set {report['cache_bytes']} exceeds authoring budget {limit}; "
                         'native cache eviction can cause per-frame texture reloads')
    return {**report, 'authoring_budget_bytes': limit,
            'native_cache_headroom_bytes': RETAIL_TEXTURE_CACHE_BYTES - report['cache_bytes'],
            'status': 'PASS_OFFLINE_TEXTURE_BUDGET',
            'scope': 'vehicle-family union; shared UI/world/other cars still need runtime qualification'}


def simulate_texture_cache(sizes: dict[str, int], sequence: list[str], *,
                           capacity: int = RETAIL_TEXTURE_CACHE_BYTES, frames: int = 3) -> list[dict]:
    """Resident-resource LRU model derived from 0053D2F0; not live profiling."""
    if capacity <= 0 or frames <= 0 or any(size <= 0 for size in sizes.values()):
        raise ValueError('invalid cache simulation parameters')
    resident = OrderedDict()
    total = 0
    result = []
    for _ in range(frames):
        misses = uploaded = evictions = 0
        for name in sequence:
            size = sizes[name]
            if name in resident:
                resident.move_to_end(name)
                continue
            resident[name] = size
            total += size
            misses += 1
            uploaded += size
            # Native code stops at the just-requested texture if it alone is
            # oversized; never spin or silently pretend it fits the budget.
            while total > capacity and len(resident) > 1:
                _, old_size = resident.popitem(last=False)
                total -= old_size
                evictions += 1
        result.append({'misses': misses, 'uploaded_source_bytes': uploaded,
                       'evictions': evictions, 'resident_bytes': total})
    return result
