"""PS2-REFL1: vehicle material, normal-coordinate and GS diagnostics.

No PC renderer, reflection shader or capture simulator. Coordinates use explicit
inputs; live VU residency and numerical parity are separate, unperformed checks.
Reuse PackFS, GXI and WATER1's visual mesh grammar without a second parser.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct

import detail_runtime as d
import psbtool as p
import tngtool as t
import water_runtime as w

ROOT = Path(__file__).resolve().parents[1]
CASES = ('TATA', 'KIASPORTAGE')
MODES = {'carshiny': 3, 'carflat': 1, 'caralpha': 2,
         'carglass': 20, 'carsglass': 20, 'carglow': 21}
TARGET = 'CommonTextures\\rendertarget64x64'
WINDSCREEN = 'CommonTextures/windscreen-reflect'


def material_contract(name, second_texture=''):
    parsed = w.shader_contract(name)
    shader = parsed['interned_shader']
    mode = MODES.get(shader)
    secondary = second_texture or None
    retained = shader == 'carshiny' and 'rubber' in second_texture
    if shader in ('carshiny', 'carglow') and not retained:
        secondary = TARGET
    elif shader in ('carglass', 'carsglass'):
        secondary = WINDSCREEN
    return {'authored_shader': parsed['authored_shader'], 'interned_shader': shader,
            'mode': mode, 'authored_secondary': second_texture or None,
            'effective_secondary': secondary, 'rubber_substring_preserved': retained,
            'reflection_contract_known': shader in MODES,
            'environment_selector': 1 if mode in (3, 20, 21) else None,
            'handler': {'carshiny': '0x3ade58', 'carflat': '0x3ae250',
                        'caralpha': '0x3adfe8', 'carglass': '0x3ae040',
                        'carsglass': '0x3ae0c8', 'carglow': '0x3ae150'}.get(shader),
            'fallback': None if mode is not None else 'UNTRACED_SHADER_OR_GENERIC_DEFAULT',
            'evidence_grade': 'CONFIRMED_BY_EXE' if mode is not None else 'UNKNOWN'}


def _named_node(reader):
    count = reader.unpack('I')
    if count > 65535:
        raise t.FormatError('Vehicle node name exceeds diagnostic budget')
    try:
        name = reader.take(count).decode('ascii')
    except UnicodeDecodeError as error:
        raise t.FormatError('Unsupported vehicle node name encoding') from error
    if '\0' in name:
        raise t.FormatError('Embedded NUL in vehicle node name')
    return {'name': name, 'name_index': reader.unpack('I') if count else None,
            'role': 'NAMED_CHILD_WRAPPER_NOT_A_MATRIX'}


def _indexed_node(reader):
    return {'selector': reader.unpack('I'), 'role': 'INDEXED_CHILD_WRAPPER'}


def decode_vehicle(payload):
    return w.decode_scene(payload, {7: _named_node, 8: _indexed_node}, terminator=101)


def inspect_vehicle(payload, model, resource):
    scene = decode_vehicle(payload)
    groups = []
    for mesh in scene.meshes:
        second = next((x['name'] for x in mesh['textures'] if x['slot'] == 1), '')
        contract = material_contract(mesh['material'], second)
        faces, counts = w.mesh_triangles(scene, mesh)
        indices = sorted({i for strip in mesh['strips']
                          for i in range(strip['start'], strip['start']+strip['count'])})
        normals = [struct.unpack_from('<3f', payload, 32+i*52) for i in indices]
        if not all(math.isfinite(x) for normal in normals for x in normal):
            raise t.FormatError('Non-finite source normal')
        groups.append({'stable_id': t.sha(payload)[:16]+':mesh:%x' % mesh['node_offset'],
            'path': mesh['path'], 'node_offset': mesh['node_offset'],
            'material': mesh['material'], 'material_offset': mesh['material_offset'],
            'textures': mesh['textures'], 'contract': contract,
            'strip_count': len(mesh['strips']), 'strip_record_offsets': [x['offset'] for x in mesh['strips']],
            'source_vertices_referenced': len(indices), 'metrics': w.geometry_metrics(faces),
            **counts, 'geometry_kind': 'VISUAL_SOURCE_STRIP',
            'normal_source': 'file vertex +0, three float32; runtime vertex +0',
            'normal_length_range': [min(math.sqrt(sum(x*x for x in n)) for n in normals),
                                    max(math.sqrt(sum(x*x for x in n)) for n in normals)] if normals else None,
            'evidence_grade': 'CONFIRMED_BY_BOTH'})
    return {'model': model, 'resource': resource, 'decoded_sha256': t.sha(payload),
            'decoded_size': len(payload), 'source_vertex_count': scene.vertex_count,
            'visual_tree_start': scene.start, 'visual_tree_end': scene.end,
            'terminal': 101, 'node_counts': scene.node_counts, 'named_nodes': scene.extra_nodes,
            'mesh_count': len(groups), 'groups': groups,
            'shader_counts': dict(sorted(Counter(g['contract']['interned_shader'] or '<untagged>'
                                                 for g in groups).items())),
            'coordinates': 'MODEL_LOCAL; final scene transform is runtime input',
            'runtime_validation': 'NOT_PERFORMED',
            'unknowns': ['Live named-child/LOD selection', 'Vehicle trailer after tag 101',
                         'Captured world/camera matrices and live VU code', 'Pixel parity']}


def _finite_vector(value, length):
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise ValueError('Expected %d components' % length)
    result = [d.f32(float(x)) for x in value]
    if not all(math.isfinite(x) for x in result):
        raise ValueError('Non-finite diagnostic input')
    return result


def _matrix(value):
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError('Expected four stored matrix rows')
    return [_finite_vector(row, 4) for row in value]


def _lerp(a, b, weight):
    left = d.sub(1., weight)  # VU 41c..42f: (1-w)*a + w*b.
    return [[d.add(d.mul(left, x), d.mul(weight, y)) for x, y in zip(ar, br)]
            for ar, br in zip(a, b)]


def _product(a, b):
    result = []
    for row in a:  # VU 430..448: ordered x, y, z, w multiply-add.
        out = []
        for col in range(4):
            x = d.mul(row[0], b[0][col])
            for i in range(1, 4):
                x = d.add(x, d.mul(row[i], b[i][col]))
            out.append(x)
        result.append(out)
    return result


def coordinates(normal, object0, object1, view0, view1, weight, base_uv=(0., 0.),
                provenance='SYNTHETIC_INPUT'):
    """Explicit-state reconstruction, not a guess at a live interpolation weight.

    No reflection-vector, normalization, inverse transpose or vertex-position
    operation appears in selector 1. VU ACC/FPU special cases are not emulated.
    """
    n = _finite_vector(normal, 3)
    uv = _finite_vector(base_uv, 2)
    weight = _finite_vector([weight], 1)[0]
    if not 0. <= weight <= 1.:
        raise ValueError('Weight outside the observed VU writer clamp range')
    obj = _lerp(_matrix(object0), _matrix(object1), weight)
    view = _lerp(_matrix(view0), _matrix(view1), weight)
    combined = _product(obj, view)
    coefficients = [[d.mul(row[0], .5), d.mul(row[1], -.5)] for row in combined[:3]]
    environment = []
    for col in range(2):
        acc = d.mul(coefficients[0][col], n[0])
        acc = d.add(acc, d.mul(coefficients[1][col], n[1]))
        acc = d.add(acc, d.mul(coefficients[2][col], n[2]))
        environment.append(d.add(acc, .5))
    if not all(math.isfinite(x) for x in environment):
        raise ValueError('Non-finite reconstructed coordinates')
    return {'base_uv': uv, 'environment_uv': environment, 'uv_qword': uv+environment,
            'coefficients': coefficients, 'weight': weight,
            'input_provenance': provenance, 'precision': 'FLOAT32_RECONSTRUCTION',
            'operation_order': 'LERP -> row matrix product -> column scale -> normal dot -> bias',
            'original_vu': ['0x2cf', '0x30e', '0x408', '0x41c', '0x430'],
            'runtime_validation': 'NOT_PERFORMED',
            'limitations': ['Host float32 rounds each op; VU ACC/denormal behavior not emulated',
                            'Live weight/input matrices must be captured separately']}


def body_color(normal, rounding):
    n = _finite_vector(normal, 3)
    value = d.add(d.mul(0., n[0]), d.mul(1., n[1]))
    value = d.add(value, d.mul(0., n[2]))
    value = d.mul(d.add(d.mul(value, d.f32(.225)), d.f32(.4)), 255.)
    if rounding == 'nearest_even':
        integer = round(value)
    elif rounding == 'toward_zero':
        integer = math.trunc(value)
    else:
        raise ValueError('CVT.W.S FCSR mode must be explicit')
    return {'source_rgba8': [max(2, min(254, integer))]*3+[254],
            'unrounded_gray': value, 'rounding': rounding,
            'precision': 'FLOAT32_RECONSTRUCTION', 'input_provenance': 'SYNTHETIC_INPUT',
            'original_function': '0x322220', 'runtime_fcsr': 'NOT_CAPTURED'}


def blend_contract(word):
    fields = w.alpha_fields(word)
    colors = ('Cs', 'Cd', '0', 'RESERVED')
    coefficients = ('As', 'Ad', 'FIX', 'RESERVED')
    fields['equation'] = '(%s - %s) * %s / 128 + %s' % (
        colors[fields['A']], colors[fields['B']], coefficients[fields['C']], colors[fields['D']])
    fields['word'] = '0x%016x' % word
    return fields


def render_contract():
    return json.loads((ROOT/'refl1'/'render-contract.json').read_text(encoding='utf-8'))


def resource_inventory():
    return json.loads((ROOT/'refl1'/'resource-evidence.json').read_text(encoding='utf-8'))


def inspect_resources(input_root):
    w.verify_inputs(input_root)
    manifest, _ = t.load_pak(input_root/'TNG.PAK')
    rows = []
    for expected in resource_inventory()['resources']:
        entries = [x for x in manifest['entries'] if x['path'] == expected['path'] and x['kind'] == 'file']
        if len(entries) != 1:
            raise t.FormatError('Missing/ambiguous reflection resource')
        payload, provenance = t.read_payload(entries[0], input_root/'TNG.000')
        image = p.parse_gxi(payload)
        if image['sha256'] != expected['gxi']['sha256']:
            raise t.FormatError('Reflection texture identity changed')
        rows.append({'path': expected['path'], 'provenance': provenance, 'gxi': image})
    return {'resources': rows, 'runtime_validation': 'NOT_PERFORMED'}


def local_output(path):
    result = path.resolve()
    if not result.is_relative_to((ROOT/'data'/'refl1').resolve()):
        raise t.FormatError('Diagnostics must remain in ignored data/refl1/')
    if result.exists() and result.stat().st_nlink > 1:
        raise t.FormatError('Refusing to overwrite a multiply linked diagnostic file')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('inspect', 'resources', 'coordinates', 'contract'))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--model', choices=CASES)
    parser.add_argument('--inputs-json', type=Path,
                        help='Explicit normal/object0/object1/view0/view1/weight/base_uv values')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = local_output(args.output)
    if args.mode == 'contract':
        result = render_contract()
    elif args.mode == 'coordinates':
        if args.inputs_json is None:
            parser.error('coordinates requires --inputs-json; no inferred live defaults')
        result = coordinates(**json.loads(args.inputs_json.read_text(encoding='utf-8')))
    elif args.mode == 'resources':
        if args.input is None:
            parser.error('resources requires --input')
        result = inspect_resources(args.input)
    else:
        if args.input is None or args.model is None:
            parser.error('inspect requires --input and --model')
        w.verify_inputs(args.input)
        manifest, _ = t.load_pak(args.input/'TNG.PAK')
        resource = ('/TNG/DATAPSM/VEHICLES/'+args.model+'/CAR.PSM').replace('/', '\\')
        entries = [x for x in manifest['entries'] if x['path'] == resource and x['kind'] == 'file']
        if len(entries) != 1:
            raise t.FormatError('Missing/ambiguous canonical vehicle resource')
        payload, provenance = t.read_payload(entries[0], args.input/'TNG.000')
        result = inspect_vehicle(payload, args.model, resource)
        result['packfs_provenance'] = provenance
    t.write_json(output, result)
    print(json.dumps({'output': str(output), 'mode': args.mode, 'runtime_validation': 'NOT_PERFORMED'}))


if __name__ == '__main__':
    main()
