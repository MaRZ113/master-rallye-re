"""Source-bound controls for the retail projected blob shadow.

Only the shadow consumer receives generated bounds. Spatial/collision bounds,
render geometry and the shared original texture remain authoritative assets.
"""
from __future__ import annotations
import hashlib
import math
import re
import struct
from ..bounds import parse_bounds1339
from ..dx import parse_dx_bytes
from ..dxt import parse_dxt_bytes

NATIVE_WIDTH_FACTOR = 1.75
NATIVE_LENGTH_FACTOR = 1.5
POLICY = 'body_alpha_support'


def _number(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be finite in [{minimum}, {maximum}]')
    return float(value)


def validate_profile(profile, *, runtime_family=None):
    allowed = {'profile_version', 'policy', 'runtime_family', 'source_model_sha256', 'source_texture_sha256', 'alpha_threshold', 'scale_x', 'scale_z', 'offset_x_m', 'offset_z_m', 'margin_x_m', 'margin_z_m', 'notes'}
    required = allowed - {'notes'}
    if not isinstance(profile, dict) or set(profile) - allowed or required - set(profile):
        raise ValueError('shadow profile has unknown or missing fields')
    if type(profile['profile_version']) is not int or profile['profile_version'] != 1 or profile['policy'] != POLICY:
        raise ValueError('unsupported shadow profile version/policy')
    family = profile['runtime_family']
    if not isinstance(family, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', family) or (runtime_family is not None and family != runtime_family):
        raise ValueError('shadow runtime family mismatch or invalid name')
    for key in ('source_model_sha256', 'source_texture_sha256'):
        if not isinstance(profile[key], str) or not re.fullmatch('[0-9a-f]{64}', profile[key]):
            raise ValueError('shadow source SHA256 must be lowercase hex')
    if type(profile['alpha_threshold']) is not int or not 1 <= profile['alpha_threshold'] <= 255:
        raise ValueError('shadow alpha threshold must be 1..255')
    for axis in ('x', 'z'):
        _number(profile['scale_' + axis], 'shadow scale', .1, 2.)
        _number(profile['offset_' + axis + '_m'], 'shadow offset', -2., 2.)
        _number(profile['margin_' + axis + '_m'], 'shadow margin', 0., 1.)
    return profile


def generate_profile(model_data, texture_data, runtime_family, *, alpha_threshold=32, scale_x=1., scale_z=1., offset_x_m=0., offset_z_m=0., margin_x_m=.05, margin_z_m=.10):
    profile = {'profile_version': 1, 'policy': POLICY, 'runtime_family': runtime_family,
        'source_model_sha256': hashlib.sha256(model_data).hexdigest(), 'source_texture_sha256': hashlib.sha256(texture_data).hexdigest(),
        'alpha_threshold': alpha_threshold, 'scale_x': scale_x, 'scale_z': scale_z,
        'offset_x_m': offset_x_m, 'offset_z_m': offset_z_m, 'margin_x_m': margin_x_m, 'margin_z_m': margin_z_m}
    bind_profile(profile, model_data, texture_data)
    return profile


def _xz_bounds(positions):
    if not positions:
        raise ValueError('shadow body has no render vertices')
    return [[float(f(p[k] for p in positions)) for k in (0, 2)] for f in (min, max)]


def alpha_support(texture_data, threshold):
    texture = parse_dxt_bytes(texture_data)
    points = [(i % texture.width, i // texture.width) for i, a in enumerate(texture.bgra[3::4]) if a >= threshold]
    if not points:
        raise ValueError('shadow texture has no selected alpha support')
    # Pixel cell boundaries in stored/native texture coordinates, never PNG row flips.
    return [[min(p[k] for p in points) / size for k, size in enumerate((texture.width, texture.height))],
            [(max(p[k] for p in points) + 1) / size for k, size in enumerate((texture.width, texture.height))]]


def runtime_bounds(serialized):
    """Retail 00553C80: marker is not stored; radius squared is inserted."""
    if len(serialized) != 44 or struct.unpack_from('<I', serialized)[0] != 1339:
        raise ValueError('invalid serialized bounds')
    radius = struct.unpack_from('<f', serialized, 16)[0]
    return serialized[4:20] + struct.pack('<f', radius * radius) + serialized[20:]


def bind_profile(profile, model_data, texture_data):
    """Validate sealed source identities and derive the shadow-only native record."""
    validate_profile(profile)
    for data, key in ((model_data, 'source_model_sha256'), (texture_data, 'source_texture_sha256')):
        if hashlib.sha256(data).hexdigest() != profile[key]:
            raise ValueError('shadow source identity mismatch: ' + key)
    model = parse_dx_bytes(model_data)
    if not model.diagnostics.validated:
        raise ValueError('invalid shadow source DX')
    native = parse_bounds1339(model.collision.unparsed_data, model.collision.unparsed_offset)
    if native is None:
        raise ValueError('shadow requires qualified marker1339 model bounds')
    body = _xz_bounds(model.vertices.positions)
    support = alpha_support(texture_data, profile['alpha_threshold'])
    generated = bytearray(native.raw)
    desired = [[], []]
    centers, quads = [], []
    for axis, index, factor in (('x', 0, NATIVE_WIDTH_FACTOR), ('z', 1, NATIVE_LENGTH_FACTOR)):
        span = (body[1][index] - body[0][index] + 2 * profile['margin_' + axis + '_m']) * profile['scale_' + axis]
        center = (body[0][index] + body[1][index]) / 2 + profile['offset_' + axis + '_m']
        if not .05 <= span <= 20:
            raise ValueError('shadow footprint exceeds supported size')
        uvspan = support[1][index] - support[0][index]
        quad = span / uvspan
        quadcenter = center - ((support[0][index] + support[1][index]) / 2 - .5) * quad
        native_span = quad / factor
        # 00588200 reads min X/Z at +14/+1C and max X/Z at +20/+28.
        k = 0 if axis == 'x' else 2
        struct.pack_into('<f', generated, 20 + k * 4, quadcenter - native_span / 2)
        struct.pack_into('<f', generated, 32 + k * 4, quadcenter + native_span / 2)
        struct.pack_into('<f', generated, 4 + k * 4, quadcenter)
        centers.append(quadcenter); quads.append(quad)
        desired[0].append(center - span / 2); desired[1].append(center + span / 2)
    native_quad = [(native.maximum[k] - native.minimum[k]) * factor for k, factor in ((0, NATIVE_WIDTH_FACTOR), (2, NATIVE_LENGTH_FACTOR))]
    native_center = [(native.maximum[k] + native.minimum[k]) / 2 for k in (0, 2)]
    original_support = [[native_center[k] + (support[side][k] - .5) * native_quad[k] for k in range(2)] for side in range(2)]
    return {'profile': dict(profile), 'model_resource': f'vehicles/{profile["runtime_family"].lower()}/car',
        'native_bounds_values_hex': runtime_bounds(native.raw).hex(), 'shadow_bounds_hex': runtime_bounds(bytes(generated)).hex(),
        'bounds_layout': 'retail_00553c80_center_radius_radius_squared_min_max',
        'body_bounds_xz_m': body, 'texture_alpha_support_uv': support,
        'native_quad_size_xz_m': native_quad, 'native_quad_center_xz_m': native_center,
        'native_alpha_support_xz_m': original_support, 'generated_quad_size_xz_m': quads,
        'generated_quad_center_xz_m': centers, 'generated_alpha_support_xz_m': desired,
        'runtime_qualified': False, 'scope': 'shadow bounds return only; source DX, collision, body and shared DXT unchanged'}


def matches_binding(bound, resource_name, native_values):
    """Portable reference for the exact native wrapper admission checks."""
    return (resource_name.replace('\\', '/').lower() == bound['model_resource'] and
            bytes(native_values) == bytes.fromhex(bound['native_bounds_values_hex']))


def rebase_unchanged_footprint(before,after,profile):
    """Re-pin unrelated appearance edits without changing shadow behaviour."""
    validate_profile(profile)
    if hashlib.sha256(before).hexdigest()!=profile['source_model_sha256']:raise ValueError('Shadow baseline model mismatch')
    a,b=parse_dx_bytes(before),parse_dx_bytes(after)
    if not a.diagnostics.validated or not b.diagnostics.validated or _xz_bounds(a.vertices.positions)!=_xz_bounds(b.vertices.positions):raise ValueError('Shadow rebase changes body footprint')
    if a.collision.spatial_bounds_1339.raw!=b.collision.spatial_bounds_1339.raw:raise ValueError('Shadow rebase changes native bounds')
    return {**profile,'source_model_sha256':hashlib.sha256(after).hexdigest()}
