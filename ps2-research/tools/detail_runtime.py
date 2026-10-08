"""PS2-GRASS1: bounded PSM spatial-surface and detail-record diagnostics.

This is an offline FLOAT32_RECONSTRUCTION, not a PC renderer or an emulator.
Geometry and instance output belong in ignored ps2-research/data/grass1/.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import struct

import tngtool as t

ROOT = Path(__file__).resolve().parents[1]
PITCH = struct.unpack('<f', bytes.fromhex('713daa3f'))[0]
LIFT = {'shrubs': struct.unpack('<f', bytes.fromhex('cdcccc3e'))[0],
        'grass': struct.unpack('<f', bytes.fromhex('c3f5a83e'))[0]}
RESOURCE = {'shrubs': r'\TNG\DATAPSM\PARTICLES\BUSH1.GXI',
            'grass': r'\TNG\DATAPSM\PARTICLES\GRASS1.GXI'}


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def add(a, b): return f32(a + b)
def sub(a, b): return f32(a - b)
def mul(a, b): return f32(a * b)
def div(a, b):
    if b == 0:
        raise t.FormatError('PS2 exceptional division is outside this float32 reconstruction')
    return f32(a / b)


def ee_floor(x):
    """356c30..356c84 integer conversion, for finite |x| < 2**31.

    Usually floor, but normalized negative powers of two below one become zero:
    the original fractional-bit check excludes the implicit mantissa bit.
    Do not replace this sequence with math.floor.
    """
    x = f32(x)
    if not math.isfinite(x) or abs(x) >= 2**31:
        raise t.FormatError('Unsupported inline-floor input')
    bits = struct.unpack('<I', struct.pack('<f', x))[0]
    exponent = ((bits & 0x7fffffff) >> 23) - 127
    sign = -1 if bits >> 31 else 0
    mantissa = bits & 0x7fffff
    magnitude = (((mantissa | 0x800000) << 8) & 0xffffffff) >> ((31-exponent) & 31)
    value = (magnitude if exponent >= 0 else 0) ^ sign
    fraction_mask = (1 << ((31-max(exponent, 0)) & 31)) - 1
    if ((mantissa << 8) & fraction_mask) == 0:
        value -= sign
    return value


def directive_contract(name):
    """2d7114/2d7148: first case-sensitive substring, through first ')'."""
    start = name.find('$detail')
    end = name.find(')', start) if start >= 0 else -1
    authored = name[start:end+1] if start >= 0 and end > start else None
    token = authored if authored is not None else '$detail(none)'
    # The interner folds ASCII capitals and '/' only AFTER the token search.
    normalized = ''.join(chr(ord(c)+32) if 'A' <= c <= 'Z' else '\\' if c == '/' else c
                         for c in token)
    value = {'$detail(shrubs)': 'shrubs', '$detail(grass)': 'grass',
             '$detail(stones)': 'stones', '$detail(none)': 'none'}.get(normalized, 'unrecognized')
    return {'authored_detail': authored, 'interned_token': normalized, 'detail_category': value,
            'point_pool_index': {'shrubs': 0, 'grass': 1}.get(value, -1),
            'default_applied': authored is None, 'grass_off_present': '$grass(off)' in name,
            'grass_off_override': 'NO_BRANCH_IN_TRACED_DETAIL_CONSUMER'}


@dataclass
class Landscape:
    payload: bytes
    vertex_count: int
    proxy_offset: int
    triangle_offset: int
    end: int
    nx: int
    nz: int
    parameters: tuple
    cells: list
    materials: list
    material_offsets: list
    triangles: tuple
    bindings: dict

    def position(self, vertex):
        result = struct.unpack_from('<3f', self.payload, 32 + vertex * 52 + 36)
        if not all(math.isfinite(x) for x in result):
            raise t.FormatError('Non-finite source position')
        return result

    def surface(self, triangle):
        if triangle not in self.bindings:
            raise t.FormatError('Triangle has no unique authored spatial binding')
        indices = self.triangles[triangle*3:triangle*3+3]
        return [self.position(i) for i in indices]


def _spatial_candidate(b, offset, nv):
    tag, reference_count, nt, nx, nz, *params = struct.unpack_from('<5I9f', b, offset)
    if not (tag == 103 and 0 < reference_count <= 2000000 and 0 < nt <= 65535
            and 0 < nx <= 4096 and 0 < nz <= 4096 and nx*nz <= 250000):
        raise t.FormatError('Invalid spatial header')
    if not all(math.isfinite(x) for x in params) or not 0 < params[0] < 100000:
        raise t.FormatError('Invalid spatial parameters')
    pos = offset + 56
    cells = []
    observed = 0
    for _ in range(nx*nz):
        count = struct.unpack_from('<I', b, pos)[0]
        pos += 4
        if count > nt or observed + count > reference_count or pos + 4*count > len(b):
            raise t.FormatError('Spatial cell exceeds declared reference budget')
        cells.append(struct.unpack_from('<%dI' % count, b, pos))
        pos += 4*count
        observed += count
    if observed != reference_count:
        raise t.FormatError('Spatial reference count mismatch')
    nm = struct.unpack_from('<I', b, pos)[0]
    pos += 4
    if not 0 < nm <= 256:
        raise t.FormatError('Unsupported spatial material count')
    materials, offsets = [], []
    for _ in range(nm):
        length, length16 = struct.unpack_from('<IH', b, pos)
        pos += 6
        if not 0 < length <= 4096 or length != length16 or pos+length > len(b):
            raise t.FormatError('Material string length mismatch')
        name = b[pos:pos+length].decode('ascii')
        # 2d5100 reads a general string here; SPAIN2 also has a material
        # consisting only of "$detail(none)". Surface type is not mandatory.
        materials.append(name)
        offsets.append(pos)
        pos += length
    triangle_offset = pos
    count = struct.unpack_from('<I', b, pos)[0]
    pos += 4
    if count != nt or pos + nt*12 > len(b):
        raise t.FormatError('Spatial and source triangle counts disagree')
    triangles = struct.unpack_from('<%dI' % (nt*3), b, pos)
    pos += nt*12
    if max(triangles) >= nv:
        raise t.FormatError('Source triangle vertex outside model')
    bindings = {}
    for cell in cells:
        for ref in cell:
            triangle, material = ref & 0xffff, ref >> 16
            if triangle >= nt or material >= nm:
                raise t.FormatError('Spatial triangle/material index outside table')
            if triangle in bindings and bindings[triangle] != material:
                raise t.FormatError('Conflicting material binding for source triangle')
            bindings[triangle] = material
    if len(bindings) != nt:
        raise t.FormatError('Not all source triangles have a spatial material binding')
    return Landscape(b, nv, offset, triangle_offset, pos, nx, nz, tuple(params),
                     cells, materials, offsets, triangles, bindings)


def decode_landscape(payload):
    """Locate exactly one validated tag-103 block; do not decode the scene tree.

    The front visual tree is deliberately opaque. Its strings cannot supply
    these bindings. The spatial block and following triangle table are checked
    independently of the printable-name survey.
    """
    if len(payload) < 32 or struct.unpack_from('<3I', payload) != (0xd00d, 2, 0x539):
        raise t.FormatError('Unsupported landscape PSM header')
    nv = struct.unpack_from('<I', payload, 28)[0]
    if not 0 < nv <= 1000000 or 32 + 52*nv >= len(payload):
        raise t.FormatError('Invalid landscape vertex span')
    matches, pos = [], 32 + 52*nv
    while True:
        pos = payload.find(b'\x67\0\0\0', pos)
        if pos < 0:
            break
        try:
            matches.append(_spatial_candidate(payload, pos, nv))
        except (t.FormatError, struct.error, UnicodeDecodeError):
            pass
        pos += 1
    if len(matches) != 1:
        raise t.FormatError('Expected one validated spatial block; found %d' % len(matches))
    return matches[0]


def eligibility(vertices, category):
    a, b, c = vertices
    ab = [sub(b[i], a[i]) for i in range(3)]
    ac = [sub(c[i], a[i]) for i in range(3)]
    cross = [sub(mul(ab[1], ac[2]), mul(ab[2], ac[1])),
             sub(mul(ab[2], ac[0]), mul(ab[0], ac[2])),
             sub(mul(ab[0], ac[1]), mul(ab[1], ac[0]))]
    length2 = add(add(mul(cross[0], cross[0]), mul(cross[1], cross[1])), mul(cross[2], cross[2]))
    normal_y = 0.0 if length2 <= 2**-23 else mul(cross[1], div(1, f32(math.sqrt(length2))))
    return {'normal_y': normal_y, 'degenerate': length2 <= 2**-23,
            'slope_pass': normal_y > f32(.975), 'category_pass': category in LIFT,
            'eligible': normal_y > f32(.975) and category in LIFT}


def spatial_query(model, x, z, half_width):
    """2d3540: inclusive cell rectangle, Z then X, first triangle occurrence."""
    if half_width <= 0 or not all(math.isfinite(v) for v in (x, z, half_width)):
        raise t.FormatError('Invalid query rectangle')
    pitch, _, _, minx, _, minz, *_ = model.parameters
    ix0, iz0 = ee_floor(div(sub(sub(x, half_width), minx), pitch)), ee_floor(div(sub(sub(z, half_width), minz), pitch))
    ix1, iz1 = ee_floor(div(sub(add(x, half_width), minx), pitch)), ee_floor(div(sub(add(z, half_width), minz), pitch))
    clamp = lambda v, n: max(0, min(v, n-1))
    seen, refs = set(), []
    for iz in range(clamp(iz0, model.nz), clamp(iz1, model.nz)+1):
        for ix in range(clamp(ix0, model.nx), clamp(ix1, model.nx)+1):
            for ref in model.cells[iz*model.nx+ix]:
                triangle = ref & 65535
                if triangle not in seen:
                    seen.add(triangle)
                    refs.append((triangle, ref >> 16))
    return refs


def jitter_table(seed=0x30ff):
    """3b7880/3f96f8: original fixed-seed LCG and rejection-sampled vectors."""
    state, calls = seed & 0xffffffff, 0
    def rng():
        nonlocal state, calls
        state = (state*0x41c64e6d+0x3039) & 0xffffffff
        calls += 1
        return state & 0x7fffffff
    for _ in range(1024):
        rng()  # uniform table 4a8810 is filled before jitter vectors
    vectors = []
    while len(vectors) < 1024:
        v = tuple(sub(mul(f32(rng()), 2**-30), 1) for _ in range(3))
        length2 = add(add(mul(v[0], v[0]), mul(v[1], v[1])), mul(v[2], v[2]))
        if f32(math.sqrt(length2)) <= 1:
            vectors.append(v)
    return vectors, {'seed': seed, 'seed_provenance': 'ELF 3b78c8 delay slot 3b78cc',
                     'rng_calls_through_jitter': calls, 'state_after_jitter': state,
                     'not_included': 'Later normalized direction table 432e88; unused by traced placement'}


def plane_coefficients(vertices):
    """359318 operation order, with input rows (X,Z,Y). Zero axes fail closed."""
    a, b, c = vertices
    dx1, dz1, dy1 = sub(b[0], a[0]), sub(b[2], a[2]), sub(b[1], a[1])
    dx2, dz2, dy2 = sub(c[0], a[0]), sub(c[2], a[2]), sub(c[1], a[1])
    inv = div(1, sub(mul(dx1, dz2), mul(dz1, dx2)))
    tx, tz = mul(a[0], inv), mul(a[2], inv)
    vz = sub(mul(mul(dy1, dx2), tz), mul(mul(dx1, tz), dy2))
    vx = sub(mul(mul(dz1, tx), dy2), mul(mul(dy1, dz2), tx))
    ix, iz = div(1, a[0]), div(1, a[2])
    cx, cz = mul(vx, -ix), mul(vz, -iz)
    constant = add(add(sub(vx, mul(mul(vx, ix), 0)), sub(vz, mul(mul(vz, iz), 0))), a[1])
    return constant, cx, cz


def scan_polygon(polygon, coefficients, category, jitter, rounding='nearest_even', limit=100000):
    """356b70: scanline grid, position hash, jitter, height plane, category lift.

    Polygon must be in the original C,B,A direction (or its clipped equivalent).
    Clipping is an input boundary here; the tool does not replace 358e98 with
    a newly invented clipping implementation.
    """
    if category not in LIFT or len(polygon) < 3:
        return []
    if len(jitter) != 1024 or limit <= 0:
        raise t.FormatError('Invalid bounded generation inputs')
    def row(z):
        return ee_floor(add(div(mul(f32(ee_floor(div(z, PITCH))), PITCH), PITCH), .1))
    first = row(min(v[2] for v in polygon))
    rows = {}
    for previous, current in zip(polygon[-1:]+polygon[:-1], polygon):
        increasing = previous[2] <= current[2]
        low, high = (previous, current) if increasing else (current, previous)
        lo, hi = row(low[2]), row(high[2])
        if lo < first or hi < first:
            raise t.FormatError('Original scanline assertion would stall')
        if lo < hi:
            increment = mul(div(sub(high[0], low[0]), sub(high[2], low[2])), PITCH)
            x = low[0]
            for iz in range(lo, hi):
                rows.setdefault(iz, {})[1 if increasing else 0] = x
                x = add(x, increment)
    result = []
    rounding_op = {'nearest_even': round, 'floor': math.floor, 'ceil': math.ceil, 'truncate': math.trunc}.get(rounding)
    if rounding_op is None:
        raise t.FormatError('Unknown CVT.W.S rounding policy')
    for iz in sorted(rows):
        bounds = rows[iz]
        if set(bounds) != {0, 1}:
            raise t.FormatError('Incomplete scanline bounds; original cached state is not available')
        x = mul(f32(ee_floor(div(bounds[0], PITCH))), PITCH)
        xmax = mul(f32(ee_floor(div(bounds[1], PITCH))), PITCH)
        z = mul(add(f32(first), f32(iz-first)), PITCH)
        zterm, minus_z = mul(z, f32(-34.923172)), -z
        while f32(.001) < sub(xmax, x):
            h = add(add(mul(x, f32(21.123102)), zterm), mul(mul(x, minus_z), f32(184.12938)))
            index = int(rounding_op(h)) & 1023
            px, pz = add(x, mul(jitter[index][0], .5)), add(z, mul(jitter[index][1], .5))
            py = add(add(add(coefficients[0], mul(px, coefficients[1])), mul(pz, coefficients[2])), LIFT[category])
            result.append({'grid_x': x, 'grid_z': z, 'jitter_index': index, 'position': [px, py, pz]})
            if len(result) > limit:
                raise t.FormatError('Diagnostic generation limit exceeded')
            x = add(x, PITCH)
    return result


def primitive_record(position, category, center, projection_scale, vertical_factor):
    """3597e0: one 64-byte input to VU1, not four CPU billboard vertices."""
    if category not in LIFT:
        return None
    if (not all(math.isfinite(v) for v in (*position, *center, projection_scale, vertical_factor))
            or projection_scale <= 0 or vertical_factor <= 0):
        raise t.FormatError('Invalid explicit primitive-record inputs')
    radius = sub(35, add(PITCH, PITCH))
    reciprocal = div(1, radius)  # Original 3597e0 computes once, then multiplies.
    dx, dz = mul(sub(position[0], center[0]), reciprocal), mul(sub(position[2], center[1]), reciprocal)
    index = ee_floor(mul(add(mul(dx, dx), mul(dz, dz)), 1024))
    if index >= 1023:
        return None
    alpha = max(0, min(128, mul(sub(1, min(1, f32(math.sqrt(mul(f32(index), 2**-10))))), 128)))
    size = mul(LIFT[category], 3)
    return {'record_bytes': 64, 'position_xyzw': [*map(f32, position), 1.0],
            'size_xy': [mul(div(64, projection_scale), size),
                        mul(div(mul(vertical_factor, 64), projection_scale), size)],
            'rgba_float': [128.0, 128.0, 128.0, alpha], 'uv_or_aux_zero': [0.0]*4,
            'resource': RESOURCE[category], 'distance_lut_index': index,
            'first_record_offset_0c': 'integer accepted-record count for this <=30-point batch',
            'vif': {'unpack_base': '0x8000', 'vectors_per_record': 4, 'mscal': '0x449'},
            'geometry_precision': 'FLOAT32_RECONSTRUCTION',
            'final_sprite_contract': 'Embedded VU1 pc449; use vu_sprite with explicit transformed inputs',
            'resident_microcode_provenance': 'UNKNOWN_UPLOAD_LINK'}


def vu_sprite(size_xy, rgba, projected_xyzw, clip_xyzw):
    """Embedded pc449's finite, positive-W, single-record output contract.

    Transformed vectors are explicit inputs, never guessed camera matrices.
    This is not a cycle-accurate VU emulator or proof of microcode residency.
    """
    if tuple(map(len, (size_xy, rgba, projected_xyzw, clip_xyzw))) != (2, 4, 4, 4):
        raise t.FormatError('Sprite inputs require size2, RGBA4, projected4 and clip4')
    if (not all(math.isfinite(v) for v in (*size_xy, *rgba, *projected_xyzw, *clip_xyzw))
            or min(size_xy) < 0 or projected_xyzw[3] <= 0 or abs(clip_xyzw[3]) < 2**-126):
        raise t.FormatError('Sprite reconstruction supports finite inputs and positive projected W')
    size_xy, rgba, projected_xyzw, clip_xyzw = [list(map(f32, v))
        for v in (size_xy, rgba, projected_xyzw, clip_xyzw)]
    q = div(1, projected_xyzw[3])
    center = [mul(v, q) for v in projected_xyzw[:3]]
    half = [min(mul(v, q), 56.0) for v in size_xy] + [0.0]
    corners = [[add(c, h) for c, h in zip(center, half)],
               [sub(c, h) for c, h in zip(center, half)]]
    clip = [mul(clip_xyzw[0], f32(.8)), mul(clip_xyzw[1], f32(.8)), sub(clip_xyzw[2], 1)]
    rejected = any(abs(v) > abs(clip_xyzw[3]) for v in clip)
    # FTOI4/FTOI0 truncate finite in-range values. Exceptional VU semantics
    # and FMAC/FDIV precision are deliberately outside this reconstruction.
    scaled = [[mul(v, 16) for v in row] for row in corners]
    if any(not -2**31 <= v < 2**31 for v in (*rgba, *(x for row in scaled for x in row))):
        raise t.FormatError('Exceptional VU integer conversion is outside the reconstruction')
    return {'input_provenance': 'EXPLICIT_TRANSFORMED_VECTORS',
            'primitive_topology': 'GS_SPRITE_TWO_CORNERS', 'vertex_count': 2,
            'q': q, 'half_size_xy': half[:2], 'corners_xyz': corners,
            'xyz_ftoi4': [[math.trunc(v) for v in row] for row in scaled],
            'stq': [[0.0, 0.0, q], [q, q, q]], 'rgba_ftoi0': [math.trunc(v) for v in rgba],
            'second_xyzf2_w_mask': 0xc000 if rejected else 0,
            'clip_test_vector': clip, 'clip_mask': '0x3f', 'gif_nloop_single_record': 2,
            'output_quadwords_excluding_tag': 6,
            'program_source': 'ELF .vudata MPG pc449, VA4443e8; single-record tail pc4ae..4c4',
            'evidence_grade': 'CONFIRMED_BY_EXE',
            'evidence_scope': 'Decoded embedded program; execution/residency link remains open',
            'numeric_precision': 'FLOAT32_RECONSTRUCTION',
            'resident_microcode_provenance': 'UNKNOWN_UPLOAD_LINK', 'runtime_validation': 'NOT_PERFORMED'}


def metadata_report(model, course, source):
    counts = Counter(model.bindings.values())
    eligible, flat = Counter(), Counter()
    first = {}
    first_flat = {}
    for triangle, material in model.bindings.items():
        category = directive_contract(model.materials[material])['detail_category']
        state = eligibility(model.surface(triangle), category)
        if state['slope_pass']:
            flat[material] += 1
            first_flat.setdefault(material, triangle)
        if state['eligible']:
            eligible[material] += 1
            first.setdefault(material, triangle)
    return {'schema': 1, 'course': course, 'landscape_resource': source,
            'source_sha256': hashlib.sha256(model.payload).hexdigest(),
            'vertex_count': model.vertex_count, 'file_vertex_stride': 52, 'runtime_vertex_stride': 48,
            'proxy_offset': model.proxy_offset, 'triangle_offset': model.triangle_offset,
            'source_triangles': len(model.triangles)//3, 'spatial_grid': [model.nx, model.nz],
            'spatial_references': sum(map(len, model.cells)),
            'materials': [{'id': i, 'name': s, 'offset': model.material_offsets[i],
                           **directive_contract(s), 'bound_triangles': counts[i],
                           'slope_passing_triangles_float32': flat[i], 'first_flat_triangle': first_flat.get(i),
                           'eligible_triangles_float32': eligible[i], 'first_eligible_triangle': first.get(i)}
                          for i, s in enumerate(model.materials)],
            'evidence_grade': 'CONFIRMED_BY_BOTH', 'numeric_precision': 'FLOAT32_RECONSTRUCTION',
            'geometry_source': 'PSM tag 103 spatial/collision triangles using shared visual gsVertex positions',
            'runtime_validation': 'NOT_PERFORMED',
            'unknowns': ['Visual scene-tree strip/draw-group equivalence', 'Live FCSR rounding state',
                         'Embedded VU1 program upload/residency and live transform inputs']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True, help='Canonical PS2 input directory')
    ap.add_argument('--course', required=True, help='Exact landscape name, e.g. FRANCE1 or TURKEY_S1')
    ap.add_argument('--triangle', type=int, help='One original source triangle; full, unclipped synthetic activation')
    ap.add_argument('--rounding', choices=['nearest_even', 'floor', 'ceil', 'truncate'], default='nearest_even')
    ap.add_argument('--record-camera', type=float, nargs=2, metavar=('X', 'Z'), help='Explicit synthetic record/fade center')
    ap.add_argument('--projection-scale', type=float, help='Explicit renderer +0x11c value, required for record mode')
    ap.add_argument('--vertical-factor', type=float, help='Explicit global 42d2c4 value, required for record mode')
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    # These diagnostics can contain original coordinates. Enforce the authorized ignored root.
    destination = a.output.resolve()
    if not destination.is_relative_to((ROOT/'data'/'grass1').resolve()):
        raise t.FormatError('Coordinate diagnostics must stay in ignored data/grass1/')
    if a.record_camera is not None and (a.triangle is None or a.projection_scale is None or a.vertical_factor is None):
        raise t.FormatError('Record mode requires --triangle, --projection-scale and --vertical-factor')
    if not a.course or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_' for c in a.course):
        raise t.FormatError('Invalid exact landscape name')
    if t.file_hash(a.input/'TNG.PAK') != t.PAK_SHA or t.file_hash(a.input/'TNG.000') != t.DATA_SHA:
        raise t.FormatError('Unsupported canonical PackFS inputs')
    manifest, _ = t.load_pak(a.input/'TNG.PAK')
    source = '\\TNG\\DATAPSM\\COURSE\\'+a.course+'\\'+a.course+'.PSM'
    matches = [entry for entry in manifest['entries'] if entry['kind'] == 'file'
               and entry['path'].upper() == source.upper()]
    if len(matches) != 1:
        raise t.FormatError('Named canonical landscape not found')
    entry = matches[0]
    payload, provenance = t.read_payload(entry, a.input/'TNG.000')
    model = decode_landscape(payload)
    report = metadata_report(model, a.course, entry['path'])
    report['packfs_provenance'] = provenance
    if a.triangle is not None:
        vertices = model.surface(a.triangle)
        material = model.bindings[a.triangle]
        category = directive_contract(model.materials[material])['detail_category']
        report['selected_surface'] = {'triangle': a.triangle, 'material': material, 'vertices': vertices,
                                      'eligibility': eligibility(vertices, category)}
        if report['selected_surface']['eligibility']['eligible']:
            table, rng = jitter_table()
            polygon = list(reversed(vertices))
            coefficients = plane_coefficients(polygon)
            report['generation'] = {'mode': 'ORIGINAL_SURFACE_WITH_SYNTHETIC_FULL_TRIANGLE_ACTIVATION',
                                    'clipping': 'Not exercised; original polygon supplied directly',
                                    'rounding': a.rounding, 'rounding_provenance': 'EXPLICIT_DIAGNOSTIC_INPUT',
                                    'rng': rng, 'instances': scan_polygon(polygon, coefficients, category, table, a.rounding),
                                    'runtime_placement_match': 'UNKNOWN'}
            report['generation']['instance_count'] = len(report['generation']['instances'])
            if a.record_camera is not None:
                report['primitive_input_records'] = [r for i in report['generation']['instances']
                    if (r := primitive_record(i['position'], category, a.record_camera,
                                              a.projection_scale, a.vertical_factor)) is not None]
                report['record_inputs'] = {'camera_xz': a.record_camera, 'projection_scale': a.projection_scale,
                                          'vertical_factor': a.vertical_factor, 'provenance': 'EXPLICIT_SYNTHETIC_INPUTS'}
        else:
            report['generation'] = {'mode': 'EXCLUDED_BY_ORIGINAL_CATEGORY_OR_SLOPE',
                                    'instance_count': 0, 'instances': [],
                                    'runtime_placement_match': 'NOT_ASSERTED'}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'output': str(destination), 'source_sha256': report['source_sha256'],
                      'source_triangles': report['source_triangles'], 'materials': len(model.materials)}))


if __name__ == '__main__':
    try:
        main()
    except (t.FormatError, OSError, struct.error) as exc:
        raise SystemExit('detail_runtime: '+str(exc))
