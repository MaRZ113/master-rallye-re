"""PS2-WATER1: bounded visual PSM/material diagnostics, not a game renderer.

The scene grammar is the observed landscape subset consumed by 391d38.
Spatial/collision records remain separately decoded by detail_runtime.
Full coordinate diagnostics are restricted to ignored data/water1/.
"""
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import json
import math
from pathlib import Path
import struct
import sys

import detail_runtime as d
import tngtool as t

ROOT = Path(__file__).resolve().parents[1]
MODES = {'water': 10, 'puddle': 9, 'waterfall': 19, 'waterall': 19}
CASES = {'TURKEY3': 'Turkey3', 'FRANCE1': 'France1', 'ITALY_S1': 'Italy_S1',
         'TURKEY1': 'Turkey1', 'SPAIN_S2': 'Spain_S2'}


def shader_contract(name):
    """390d98 -> interner -> 3a6c58; preserve the authored spelling."""
    start = name.find('$shader')
    left = name.find('(', start) if start >= 0 else -1
    right = name.find(')', left) if left >= 0 else -1
    authored = name[left+1:right] if right >= 0 else None
    interned = (authored.translate(str.maketrans(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ/', 'abcdefghijklmnopqrstuvwxyz\\'))
        if authored is not None else None)
    return {'authored_shader': authored, 'interned_shader': interned,
            'water_mode': MODES.get(interned),
            'fallback': None if interned in MODES else
                        'GENERIC_MAP_DEFAULTS_RETAINED_OR_OTHER_SHADER',
            'scroll_v_plus1_present': '$scroll(v,+1)' in name,
            'scroll_token_consumer': 'NOT_FOUND_IN_TRACED_WATER_PATH',
            'evidence_grade': 'CONFIRMED_BY_EXE'}


class Reader:
    def __init__(self, payload, offset):
        self.payload, self.offset = payload, offset

    def take(self, count):
        if count < 0 or self.offset + count > len(self.payload):
            raise t.FormatError('Truncated visual scene record at %d' % self.offset)
        result = self.payload[self.offset:self.offset+count]
        self.offset += count
        return result

    def unpack(self, fmt):
        values = struct.unpack('<'+fmt, self.take(struct.calcsize('<'+fmt)))
        return values[0] if len(values) == 1 else values

    def boolean(self):
        return bool(self.unpack('B'))  # 30be70 accepts any nonzero byte.

    def string(self):
        count = self.unpack('I')
        if not count:
            return '', self.offset
        if count > 65535 or count != self.unpack('H'):
            raise t.FormatError('Visual string length mismatch')
        offset = self.offset
        try:
            text = self.take(count).decode('ascii')
        except UnicodeDecodeError as error:
            raise t.FormatError('Unsupported non-ASCII material string') from error
        if '\0' in text:
            raise t.FormatError('Embedded NUL in serialized material string')
        return text, offset


@dataclass
class Scene:
    payload: bytes
    vertex_count: int
    start: int
    end: int
    meshes: list
    node_counts: dict

    def position(self, index):
        if not 0 <= index < self.vertex_count:
            raise t.FormatError('Visual vertex index outside model')
        result = struct.unpack_from('<3f', self.payload, 32+index*52+36)
        if not all(math.isfinite(x) for x in result):
            raise t.FormatError('Non-finite visual vertex')
        return result

    def control(self, index):
        return struct.unpack_from('<I', self.payload, 32+index*52+12)[0]


def decode_scene(payload):
    """Decode only tags 0/1/2/5/6; fail closed on another scene grammar.

    Tag 100 terminates this visual tree. Tag 103 is a different representation;
    it is never used here to invent visual strips or shader assignments.
    """
    if len(payload) < 32 or struct.unpack_from('<3I', payload) != (0xd00d, 2, 0x539):
        raise t.FormatError('Unsupported landscape PSM header')
    nv = struct.unpack_from('<I', payload, 28)[0]
    start = 32+52*nv
    if not 0 < nv <= 1000000 or start+8 > len(payload):
        raise t.FormatError('Invalid visual vertex span')
    reader, meshes, counts = Reader(payload, start), [], Counter()

    def node(path, depth):
        if depth > 100 or sum(counts.values()) >= 100000:
            raise t.FormatError('Visual scene recursion/node budget exceeded')
        offset = reader.offset
        tag = reader.unpack('I')
        counts[tag] += 1
        if tag == 2:
            field = reader.unpack('I')
            if reader.unpack('I') != 3:
                raise t.FormatError('Unsupported material map count')
            textures = []
            for slot in range(3):
                if reader.boolean():
                    flags = [reader.boolean() for _ in range(3)]
                    text, at = reader.string()
                    textures.append({'slot': slot, 'name': text, 'flags': flags, 'offset': at})
            material, at = reader.string()
            words = reader.unpack('2I')
            flags = [reader.boolean() for _ in range(4)]
            # mesh+70 is not a coordinate; selected original records include
            # non-finite bit patterns. Preserve it as an opaque word.
            value = reader.unpack('I')
            count = reader.unpack('I')
            if count > 100000 or count*13+4 > len(payload)-reader.offset:
                raise t.FormatError('Visual strip count exceeds payload')
            strips = []
            for _ in range(count):
                strip_at = reader.offset
                first, length = reader.unpack('2I')
                flag, scale = reader.boolean(), reader.unpack('f')
                if first >= 0x80000 or length > 65535 or first+length > nv:
                    raise t.FormatError('Unsupported/out-of-range packed visual strip')
                if not math.isfinite(scale):
                    raise t.FormatError('Non-finite strip scale')
                strips.append({'offset': strip_at, 'start': first, 'count': length,
                               'flag': flag, 'scale': scale})
            meshes.append({'node_offset': offset, 'path': path, 'field_unknown': field,
                           'textures': textures, 'material': material, 'material_offset': at,
                           'words_unknown': words, 'flags': flags, 'word70_unknown': hex(value),
                           'strips': strips, 'classification': shader_contract(material)})
        elif tag not in (0, 1, 5, 6):
            raise t.FormatError('Unsupported visual node tag %d at %d' % (tag, offset))
        children = reader.unpack('I')
        if children > 10000 or children*8 > len(payload)-reader.offset:
            raise t.FormatError('Visual child count exceeds payload')
        for i in range(children):
            node(path+'.'+str(i), depth+1)

    node('root', 0)
    end = reader.offset
    if reader.unpack('I') != 100:
        raise t.FormatError('Visual tree does not end at tag 100')
    return Scene(payload, nv, start, end, meshes, dict(sorted(counts.items())))


def area_normal(triangle):
    a, b, c = triangle
    u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
    normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    length = math.sqrt(sum(x*x for x in normal))
    return length/2, abs(normal[1])/length if length else None, abs(normal[1])/2


def mesh_triangles(scene, mesh):
    """Canonical strip triples; bit0 of the newest vertex suppresses a kick.

    Winding/back-face selection is not reconstructed. Unsigned area/footprints
    do not require it. The small area cutoff is a DIAGNOSTIC tolerance.
    """
    triangles, suppressed, degenerate = [], 0, 0
    for strip in mesh['strips']:
        for i in range(strip['start']+2, strip['start']+strip['count']):
            if scene.control(i) & 1:
                suppressed += 1
                continue
            triangle = tuple(scene.position(j) for j in (i-2, i-1, i))
            if area_normal(triangle)[0] <= 1e-7:
                degenerate += 1
            else:
                triangles.append(triangle)
    return triangles, {'suppressed_triples': suppressed, 'diagnostic_degenerate_triples': degenerate}


def geometry_metrics(triangles):
    """Coordinate-welded shared-edge connectivity, not a visible puddle count."""
    points = [p for triangle in triangles for p in triangle]
    edges, parent = {}, list(range(len(triangles)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, triangle in enumerate(triangles):
        keys = [tuple(round(v, 4) for v in p) for p in triangle]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edge = tuple(sorted((keys[a], keys[b])))
            if edge in edges:
                parent[find(i)] = find(edges[edge])
            else:
                edges[edge] = i
    components = Counter(find(i) for i in range(len(triangles)))
    areas = [area_normal(triangle) for triangle in triangles]
    slopes = [math.degrees(math.acos(min(1., n))) for _, n, _ in areas if n is not None]
    return {'triangles': len(triangles), 'coordinate_vertices': len(set(points)),
            'bounds': {'min': [min(p[i] for p in points) for i in range(3)],
                       'max': [max(p[i] for p in points) for i in range(3)]} if points else None,
            'components': len(components), 'component_sizes': sorted(components.values(), reverse=True),
            'component_method': 'Shared edges after decimal rounding to 4 places; diagnostic only',
            'surface_area': sum(a for a, _, _ in areas),
            'unsigned_xz_area': sum(a for _, _, a in areas),
            'horizontal_triangles': sum((n or 0) > .99999 for _, n, _ in areas),
            'absolute_slope_degrees': [min(slopes), max(slopes)] if slopes else None,
            'precision': 'MATHEMATICALLY_EQUIVALENT_HOST_DOUBLE_METRICS'}


def inspect_scene(scene, course, resource):
    source_hash = t.sha(scene.payload)
    groups, triangles = [], []
    for mesh in scene.meshes:
        if mesh['classification']['water_mode'] is None:
            continue
        faces, counts = mesh_triangles(scene, mesh)
        groups.append({**mesh, **counts, 'stable_id': source_hash[:16]+':mesh:%x' % mesh['node_offset'],
                       'geometry_kind': 'VISUAL_SOURCE_STRIP', 'metrics': geometry_metrics(faces),
                       'evidence_grade': 'CONFIRMED_BY_BOTH'})
        triangles.extend(faces)
    return {'course': course, 'resource': resource, 'decoded_sha256': source_hash,
            'decoded_size': len(scene.payload), 'vertex_count': scene.vertex_count,
            'visual_tree_start': scene.start, 'visual_tree_end': scene.end,
            'node_counts': scene.node_counts, 'all_visual_meshes': len(scene.meshes),
            'water_groups': groups, 'water_geometry': geometry_metrics(triangles),
            'mode_counts': dict(sorted(Counter(g['classification']['interned_shader'] for g in groups).items())),
            'geometry_source': 'AUTHORED_VISUAL_STRIPS', 'runtime_validation': 'NOT_PERFORMED',
            'unknowns': ['Runtime visibility/LOD and scene instance transform',
                         'VU upload/residency; actual runtime GS draw']}, triangles


def _cell(point, size):
    return tuple(math.floor(v/size) for v in point)


def _neighbors(key):
    return (tuple(a+b for a, b in zip(key, delta))
            for delta in itertools.product((-1, 0, 1), repeat=len(key)))


def centroid(triangle):
    return tuple(sum(p[i] for p in triangle)/3 for i in range(3))


def corner_error(a, b):
    return min(max(abs(x-y) for p, q in zip(a, order) for x, y in zip(p, q))
               for order in itertools.permutations(b))


def height_at(triangle, x, z):
    a, b, c = triangle
    den = (b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
    if abs(den) < 1e-10:
        return None
    u = ((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/den
    v = ((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/den
    w = 1-u-v
    return u*a[1]+v*b[1]+w*c[1] if min(u, v, w) >= -1e-8 else None


def match_geometry(source, pc_rows, pc_points, all_source_points=(), tolerance=.001, heights=False):
    """Compare against ALL PC draw triangles; no fitting or invented transform."""
    if not math.isfinite(tolerance) or not 0 < tolerance <= .01:
        raise t.FormatError('Unsupported comparison tolerance')
    grid, points, height_grid = defaultdict(list), defaultdict(list), defaultdict(list)
    triangle_cell, point_cell = 100*tolerance, 10*tolerance
    for p in pc_points:
        points[_cell(p, point_cell)].append(p)
    for triangle, draw in pc_rows:
        grid[_cell(centroid(triangle), triangle_cell)].append((triangle, draw))
        if heights:
            xs, zs = [p[0] for p in triangle], [p[2] for p in triangle]
            xr = range(math.floor(min(xs)/64), math.floor(max(xs)/64)+1)
            zr = range(math.floor(min(zs)/64), math.floor(max(zs)/64)+1)
            if len(xr)*len(zr) > 1000000:
                raise t.FormatError('PC height projection exceeds diagnostic cell budget')
            for x in xr:
                for z in zr:
                    height_grid[x, z].append(triangle)

    def point_match(p):
        return any(max(abs(x-y) for x, y in zip(p, q)) <= tolerance
                   for key in _neighbors(_cell(p, point_cell)) for q in points[key])

    matched, errors, draws, deltas, missing = 0, [], Counter(), [], 0
    for triangle in source:
        candidates = ((other, draw) for key in _neighbors(_cell(centroid(triangle), triangle_cell))
                      for other, draw in grid[key])
        hits = [(corner_error(triangle, other), draw) for other, draw in candidates
                if corner_error(triangle, other) <= tolerance]
        if hits:
            error, draw = min(hits)
            matched += 1
            errors.append(error)
            draws[draw] += 1
        if heights:
            x, y, z = centroid(triangle)
            hs = [h for other in height_grid[math.floor(x/64), math.floor(z/64)]
                  if (h := height_at(other, x, z)) is not None]
            if hs:
                deltas.append(min((y-h for h in hs), key=abs))
            else:
                missing += 1
    water_points = set(p for triangle in source for p in triangle)
    all_points = set(all_source_points)
    return {'tolerance': tolerance, 'triangle_matches': matched, 'triangles': len(source),
            'matched_pc_draws': dict(sorted(draws.items())), 'maximum_corner_error': max(errors, default=None),
            'water_vertices_matching_pc': sum(point_match(p) for p in water_points),
            'water_vertices': len(water_points),
            'all_source_coordinate_positions_matching_pc': sum(point_match(p) for p in all_points),
            'all_source_coordinate_positions': len(all_points),
            'coordinate_transform': 'IDENTITY; independently checked through ordinary course vertices',
            'centroid_height': {'performed': heights, 'hits': len(deltas), 'missing': missing,
                'coplanar_with_any_pc_triangle': sum(abs(v) <= tolerance for v in deltas),
                'min_signed_nearest': min(deltas, default=None), 'max_signed_nearest': max(deltas, default=None),
                'min_abs_nearest': min(map(abs, deltas), default=None),
                'max_abs_nearest': max(map(abs, deltas), default=None),
                'above_pc': sum(v > 0 for v in deltas), 'below_pc': sum(v < 0 for v in deltas)},
            'evidence_grade': 'CONFIRMED_BY_BYTES', 'runtime_visibility': 'UNKNOWN'}


def load_pc(pc_root, sdk_root, course):
    from course_delta import sdk_modules
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        _, sidecar_module = sdk_modules(sdk_root)
        from master_rallye.dx_course import parse_course_dx
        folder = pc_root/'DataGx'/'Course'/CASES[course]
        files = list(folder.iterdir())
        dx = [p for p in files if p.suffix.lower() == '.dx']
        sidecar = [p for p in files if p.suffix.lower() == '.txt']
        if len(dx) != 1 or len(sidecar) != 1:
            raise t.FormatError('Ambiguous/missing PC compiled course inputs')
        model, metadata = parse_course_dx(dx[0]), sidecar_module.parse_sidecar(sidecar[0])
        sidecar_module.apply_material_candidates(model.physical_draws, metadata)
    finally:
        sys.dont_write_bytecode = old
    if not model.course_render_validated:
        raise t.FormatError('PC Course SDK did not validate complete draw coverage')
    rows, water = [], []
    water_draws = []
    for draw in model.physical_draws:
        indices = model.draw_global_indices(draw)
        names = list(draw.texture_tuple)+[m.name for m in draw.material_candidates]
        candidate = any('water' in name.lower() or 'puddle' in name.lower() for name in names)
        faces = [tuple(model.vertices.positions[j] for j in indices[i:i+3])
                 for i in range(0, len(indices), 3)]
        rows.extend((triangle, draw.draw_index) for triangle in faces)
        if candidate:
            water.extend(faces)
            water_draws.append({'draw_index': draw.draw_index, 'textures': draw.texture_tuple,
                                'materials': [m.name for m in draw.material_candidates],
                                'metrics': geometry_metrics(faces)})
    return rows, model.vertices.positions, {'dx_sha256': t.file_hash(dx[0]),
        'sidecar_sha256': t.file_hash(sidecar[0]), 'draws': len(model.physical_draws),
        'vertices': model.vertex_count, 'triangles': model.triangle_count,
        'water_candidates': water_draws, 'water_geometry': geometry_metrics(water),
        'coverage': 'VALIDATED_PC_VISUAL_DRAW_RECORDS'}


def alpha_fields(value):
    return {'A': value & 3, 'B': value >> 2 & 3, 'C': value >> 4 & 3,
            'D': value >> 6 & 3, 'FIX': value >> 32 & 255}


def render_contract():
    return json.loads((ROOT/'water1'/'render-contract.json').read_text(encoding='utf-8'))


def waterfall_uv(counter, source_y, first_source_y, source_u, previous_phase=0., paused=False):
    """316808/321838 float32 diagnostic; inputs are explicitly supplied.

    Caller counter units and original FPU rounding mode remain UNKNOWN.
    This does not evaluate the authored $scroll(v,+1) parameter.
    """
    if not isinstance(counter, int) or not 0 <= counter <= 0xffffffff:
        raise t.FormatError('Renderer counter must be an unsigned 32-bit integer')
    values = (source_y, first_source_y, source_u, previous_phase)
    if not all(math.isfinite(v) and abs(v) < 100000 for v in values):
        raise t.FormatError('Unsupported synthetic animation input')
    phase = d.f32(previous_phase) if paused else d.div(d.f32(counter), 150.)
    doubled, quadrupled = d.add(phase, phase), d.mul(phase, 4.)
    first = d.ee_floor(d.add(d.mul(d.f32(first_source_y), .05), 6.))
    y = d.mul(d.f32(source_y), .05)
    return {'phase': phase, 'primary_uv': [d.f32(source_u),
                d.sub(d.add(y, d.sub(doubled, d.f32(d.ee_floor(doubled)))), d.f32(first))],
            'secondary_uv': [d.f32(source_u),
                d.sub(d.add(y, d.sub(quadrupled, d.f32(d.ee_floor(quadrupled)))), d.f32(first))],
            'input_provenance': 'EXPLICIT_DIAGNOSTIC_INPUT; not captured PS2 state',
            'precision': 'FLOAT32_RECONSTRUCTION', 'counter_units': 'UNKNOWN'}


def write_footprint(path, triangles, course):
    metrics = geometry_metrics(triangles)
    if not triangles:
        raise t.FormatError('No water visual source geometry for an SVG footprint')
    lo, hi = metrics['bounds']['min'], metrics['bounds']['max']
    scale = 800/max(hi[0]-lo[0], hi[2]-lo[2], 1.)
    def point(p):
        return '%.3f,%.3f' % (40+(p[0]-lo[0])*scale, 70+(hi[2]-p[2])*scale)
    height = 110+(hi[2]-lo[2])*scale
    polygons = '\n'.join('<polygon points="%s"/>' % ' '.join(map(point, tri)) for tri in triangles)
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="880" height="%g" viewBox="0 0 880 %g">'
        '<rect width="100%%" height="100%%" fill="#12202b"/><g fill="#419db0" stroke="#b3e0de" stroke-width=".35">%s</g>'
        '<g fill="white" font-family="sans-serif" font-size="15"><text x="40" y="26">%s — authored water source X/Z footprint</text>'
        '<text x="40" y="48">X right; Z up. Source geometry, not a runtime frame or renderer preview.</text></g></svg>'
        % (height, height, polygons, course), encoding='utf-8')


def verify_inputs(input_root):
    from course_delta import EXPECTED
    sizes = {'SLES_509.06': 3739852, 'SYSTEM.CNF': 56, 'TNG.PAK': 135556, 'TNG.000': 1225915283}
    for name, expected in EXPECTED.items():
        path = input_root/name
        if not path.is_file() or path.stat().st_size != sizes[name] or t.file_hash(path) != expected:
            raise t.FormatError('Canonical input identity mismatch: '+name)


def local_output(path):
    path = path.resolve()
    if not path.is_relative_to((ROOT/'data'/'water1').resolve()):
        raise t.FormatError('Diagnostics must remain in ignored data/water1/')
    if path.exists() and path.stat().st_nlink > 1:
        raise t.FormatError('Refusing to overwrite a multiply linked diagnostic file')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('inspect', 'compare', 'contract', 'waterfall-uv'))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--course', choices=tuple(CASES))
    parser.add_argument('--pc-root', type=Path)
    parser.add_argument('--sdk', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--svg', type=Path)
    parser.add_argument('--counter', type=int, default=0)
    parser.add_argument('--source-y', type=float, default=0.)
    parser.add_argument('--first-source-y', type=float, default=0.)
    parser.add_argument('--source-u', type=float, default=0.)
    args = parser.parse_args()
    output = local_output(args.output)
    svg = local_output(args.svg) if args.svg else None
    if args.mode == 'contract':
        result = render_contract()
    elif args.mode == 'waterfall-uv':
        result = waterfall_uv(args.counter, args.source_y, args.first_source_y, args.source_u)
    else:
        if args.input is None or args.course is None:
            parser.error('inspect/compare require --input and --course')
        verify_inputs(args.input)
        manifest, _ = t.load_pak(args.input/'TNG.PAK')
        resource = ('/TNG/DATAPSM/COURSE/'+args.course+'/'+args.course+'.PSM').replace('/', chr(92))
        entries = [r for r in manifest['entries'] if r['path'] == resource and r['kind'] == 'file']
        if len(entries) != 1:
            raise t.FormatError('Named canonical landscape resource is ambiguous/missing')
        payload, provenance = t.read_payload(entries[0], args.input/'TNG.000')
        scene = decode_scene(payload)
        result, triangles = inspect_scene(scene, args.course, resource)
        spatial = d.decode_landscape(payload)
        if spatial.proxy_offset != scene.end+4:
            raise t.FormatError('Independent spatial decoder disagrees with visual end')
        result['spatial_representation'] = {'offset': spatial.proxy_offset,
            'triangles': len(spatial.triangles)//3, 'geometry_kind': 'SPATIAL_SOURCE_TRIANGLE',
            'visual_triangle_equivalence': 'NOT_ASSUMED'}
        result['packfs_provenance'] = provenance
        if args.mode == 'compare':
            if args.pc_root is None or args.sdk is None:
                parser.error('compare requires --pc-root and --sdk')
            rows, points, pc = load_pc(args.pc_root, args.sdk, args.course)
            result['pc'] = pc
            result['comparison'] = match_geometry(triangles, rows, points,
                (scene.position(i) for i in range(scene.vertex_count)), heights=args.course == 'TURKEY3')
        if svg:
            svg.parent.mkdir(parents=True, exist_ok=True)
            write_footprint(svg, triangles, args.course)
    if svg and args.mode not in ('inspect', 'compare'):
        parser.error('--svg requires inspected source geometry')
    t.write_json(output, result)
    print(json.dumps({'output': str(output), 'mode': args.mode, 'runtime_validation': 'NOT_PERFORMED'}))


if __name__ == '__main__':
    main()
