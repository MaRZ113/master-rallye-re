"""TREEBLEND1: authored foliage/material/GS diagnostics, never a renderer.

Reuse PackFS, WATER1 visual strips, DRESSING1 ancestry and GEOM1 matching.
Complete source vertices are read locally; outputs are compact summaries.
Inherited GS words remain unknown unless the caller supplies synthetic words.
"""
import argparse
from collections import Counter
import json
import itertools
import math
from pathlib import Path
import struct

import detail_runtime as d
import dressing_runtime as dr
import geometry_delta as g
import psbtool as p
import tngtool as t
import water_runtime as w

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'ps2-foliage-contract-v1'
SHADERS = {
    'treeblend': dict(mode=2, handler='0x003ae618', registration='0x003a7468',
                      vtable='0x00487d68', queue_bucket=1, texture_lookup_flag=1,
                      mip_factor_word=0x3e19999a),
    'tree': dict(mode=6, handler='0x003ae710', registration='0x003a75b8',
                 vtable='0x00487d08', queue_bucket=0, texture_lookup_flag=0,
                 mip_factor_word=0x3e4ccccd),
    'object': dict(mode=15, handler='0x003ae760', registration='0x003a7628',
                   vtable='0x00487ce8', queue_bucket=0, texture_lookup_flag=0,
                   mip_factor_word=0x3f000000),
}
CASES = (
    ('A', 'TURKEY3', 3620664, 'treeblend'),
    ('B', 'ITALY_S1', 3706566, 'tree'),
    ('C', 'FRANCE1', 3550808, 'tree'),
    ('D', 'TURKEY3', 3429766, 'object'),
    ('E', 'FRANCE1', 3509209, 'treeblend'),
)
FIELDS = {
    'PRIM': dict(PRIM=(0, 3), IIP=(3, 1), TME=(4, 1), FGE=(5, 1),
                 ABE=(6, 1), AA1=(7, 1), FST=(8, 1), CTXT=(9, 1)),
    'TEST': dict(ATE=(0, 1), ATST=(1, 3), AREF=(4, 8), AFAIL=(12, 2),
                 DATE=(14, 1), DATM=(15, 1), ZTE=(16, 1), ZTST=(17, 2)),
    'ALPHA': dict(A=(0, 2), B=(2, 2), C=(4, 2), D=(6, 2), FIX=(32, 8)),
    'ZBUF': dict(ZBP=(0, 9), PSM=(24, 4), ZMSK=(32, 1)),
    'TEX0': dict(TBP0=(0, 14), PSM=(20, 6), TCC=(34, 1), TFX=(35, 2)),
    'TEX1': dict(LCM=(0, 1), MXL=(2, 3), MMAG=(5, 1), MMIN=(6, 3),
                 MTBA=(9, 1), L=(19, 2), K=(32, 12)),
    'FBA': dict(FBA=(0, 1)),
}
MASK64 = (1 << 64)-1


def material_contract(name):
    parsed = w.shader_contract(name)
    shader = parsed['interned_shader']
    info = SHADERS.get(shader)
    return {'authored_shader': parsed['authored_shader'], 'interned_shader': shader,
            'classification': info, 'alphatest_marker_present': '$alphatest' in name,
            'marker_is_final_gs_state': False,
            'geometry_source': 'AUTHORED_VISUAL_STRIPS' if info else 'UNKNOWN',
            'texture_name_override': False if info else 'UNKNOWN',
            'precision': 'EXACT_ELF_OPERATION' if info else 'UNKNOWN',
            'evidence_grade': 'CONFIRMED_BY_EXE' if info else 'UNKNOWN',
            'unknown_token_policy': 'PRESERVED; NO SPELLING OR WHITESPACE REPAIR'}


def state_operations(shader):
    """312610 mode2/mode6(+31679c)/mode15 integer mask operations."""
    if shader not in SHADERS:
        raise t.FormatError('Untraced foliage/control shader')
    blend = shader == 'treeblend'
    test = 0x41000 if blend else 0x4040d if shader == 'tree' else 0x4040c
    return {
        'GIF_TAG': (0xffc07fffffffffff, 0x003e000000000000 if blend else 0x001e000000000000),
        'TEST': (0xfffffffffff9c000, test),
        'ALPHA': (0xffffff00ffffff00, 0x44),
        'ZBUF': (MASK64 ^ (1 << 32), (1 << 32) if blend else 0),
        'TEX0': (0xffffffe3ffffffff, 0x400000000),
        'TEX1': (0xfffff000ffe7fe1e, 0x160),
        'FBA': (MASK64 ^ 1, 0),
    }


def decoded_fields(register, value, known_mask=MASK64):
    result = {}
    for name, (shift, width) in FIELDS[register].items():
        mask = ((1 << width)-1) << shift
        result[name] = (value & mask) >> shift if known_mask & mask == mask else 'INHERITED'
    return result


def state_contract(shader, inherited=None):
    """No guessed initial state. Explicit inherited words are synthetic inputs."""
    if inherited is not None:
        if any(k not in state_operations(shader) or isinstance(v, bool) or
               not isinstance(v, int) or not 0 <= v <= MASK64 for k, v in inherited.items()):
            raise t.FormatError('Expected named unsigned 64-bit inherited GS words')
    rows = {}
    for register, (keep, bits) in state_operations(shader).items():
        supplied = inherited is not None and register in inherited
        value = ((inherited[register] if supplied else 0) & keep) | bits
        known = MASK64 if supplied else MASK64 ^ keep
        name = 'PRIM' if register == 'GIF_TAG' else register
        decoded = decoded_fields(name, value >> 47, known >> 47) if name == 'PRIM' else decoded_fields(name, value, known)
        rows[register] = {'keep_mask': f'0x{keep:016x}', 'set_bits': f'0x{bits:016x}',
                          'known_mask': f'0x{known:016x}', 'decoded': decoded,
                          'result_word': f'0x{value:016x}' if supplied else None}
    return {'shader': shader, 'mode': SHADERS[shader]['mode'], 'registers': rows,
            'blend_equation': '(Cs-Cd)*As/128+Cd' if shader == 'treeblend' else 'ABE=0; ALPHA inactive',
            'alpha_test': 'DISABLED' if shader != 'tree' else 'A > 64; AFAIL=KEEP',
            'effective_geometry_streams': 1,
            'primary_gif_registers': '0x412: ST, RGBAQ, XYZF2',
            'secondary_gif_registers': '0xfff: NOP, NOP, NOP',
            'precision': 'EXACT_ELF_OPERATION',
            'input_provenance': 'EXPLICIT_SYNTHETIC_INHERITED_WORDS' if inherited is not None else 'INHERITED_STATE_NOT_SUPPLIED',
            'inherited_scope': ['ZTE', 'DATE/DATM', 'FRAME', 'PABE', 'TEXA', 'dynamic TEX0 address/format',
                                'higher PRIM bits until template initialization', 'global AD helper state'],
            'runtime_validation': 'NOT_PERFORMED', 'evidence_grade': 'CONFIRMED_BY_EXE'}


def vertex_color(word):
    """3a7f10 ->3401f0/230/270/2b0 ->31f4e0 ->VU FTOI0.

    Original normalized-byte round trips recover integer channels; clamp2..254
    is explicitly proved. This is not a generalized FCSR conversion emulator.
    """
    if isinstance(word, bool) or not isinstance(word, int) or not 0 <= word < 2**32:
        raise t.FormatError('Expected original unsigned source color word')
    channels = tuple(word >> shift & 255 for shift in (24, 16, 8, 0))
    loaded = tuple(min(254, max(2, c)) for c in channels)
    cache = tuple(d.mul(float(c), .5) for c in loaded)
    return {'source_rgba': channels, 'runtime_rgba_bytes': loaded, 'cached_rgba_f32': cache,
            'vu_rgba_integers': tuple(math.trunc(c) for c in cache),
            'precision': 'FLOAT32_RECONSTRUCTION', 'fcsr_scope': 'NORMALIZED_ORIGINAL_BYTES_ONLY'}


def source_vertex(scene, index):
    scene.position(index)  # Existing bounded finite coordinate validation.
    base = 32+52*index
    normal = struct.unpack_from('<3f', scene.payload, base)
    uv = struct.unpack_from('<4f', scene.payload, base+20)
    if not all(math.isfinite(x) for x in normal+uv):
        raise t.FormatError('Non-finite foliage normal or UV')
    return {'source_index': index, 'source_offset': base, 'normal': normal,
            'control': scene.control(index), 'position': scene.position(index), 'uv4': uv,
            'color': vertex_color(struct.unpack_from('<I', scene.payload, base+16)[0])}


def attribute_summary(scene, mesh):
    indices = sorted({i for s in mesh['strips'] for i in range(s['start'], s['start']+s['count'])})
    vertices = [source_vertex(scene, i) for i in indices]
    ranges = lambda key: [[min(v[key][j] for v in vertices), max(v[key][j] for v in vertices)]
                         for j in range(len(vertices[0][key]))] if vertices else []
    hist = lambda key: dict(sorted(Counter(str(v['color'][key]) for v in vertices).items()))
    return {'referenced_source_vertices': len(indices), 'normal_ranges': ranges('normal'),
            'uv4_ranges': ranges('uv4'), 'source_rgba_histogram': hist('source_rgba'),
            'runtime_rgba_histogram': hist('runtime_rgba_bytes'),
            'vu_rgba_histogram': hist('vu_rgba_integers'),
            'source_vertex_bytes_sha256': t.sha(b''.join(scene.payload[32+i*52:32+(i+1)*52] for i in indices)),
            'normal_consumption': 'CACHED; UNUSED_BY_SELECTOR_0_COORDINATE_AND_COLOR_PATH',
            'position_consumption': 'ORDINARY_MATRIX_AND_PROJECTION; NO FOLIAGE PIVOT RECONSTRUCTION',
            'color_consumption': 'AUTHOR_RGBA -> CLAMP2..254 -> SCALE0.5 -> FTOI0',
            'uv_consumption': 'PRIMARY_UV_XY -> STQ; SECONDARY_STREAM_NOP',
            'control_consumption': 'FIRST_VERTEX_STRIP_LENGTH; THEN ORIGINAL_BIT0_ADC',
            'winding': 'ORIGINAL_STRIP_ORDER_RETAINED; LIVE_CULLING_NOT_CAPTURED'}


def exact_comparison(faces, pc):
    """GEOM1's matcher supplies the oracle; no new triangle matcher here."""
    summary = []
    baseline = None
    for profile_name in ('strict', 'baseline', 'relaxed'):
        rows, stats = g.direction_match(faces, pc.faces, g.PROFILES[profile_name], 'PS2_EXTRA_VISUAL_SOURCE')
        if profile_name == 'baseline': baseline = rows
        summary.append({'profile': profile_name, 'tolerance': g.PROFILES[profile_name],
                        'relations': dict(sorted(Counter(r['geometry_relation'] for r in rows).items())),
                        'maximum_exact_corner_error': max((r['maximum_corner_error'] for r in rows
                                                          if r['maximum_corner_error'] is not None), default=None),
                        'candidate_counts': stats})
    groups = sorted({gid for row in baseline for gid in row['other_groups']})
    return {'source_frame': 'GAME_SOURCE; IDENTITY_ANCHORED_BY_GEOM1_ROUTE_AND_GROUND',
            'profiles': summary, 'matched_pc_groups': [pc.groups[k] for k in groups],
            'classification_scope': 'COMPILED_PAIRED_DX; NO INSTANCE_OR_POPULATION CLAIM',
            'evidence_grade': 'CONFIRMED_BY_BYTES for exact correspondence; STATIC_INFERENCE otherwise'}


def inspect_mesh(scene, course, resource, mesh, case_id=None, pc=None):
    faces, exclusions = w.mesh_triangles(scene, mesh)
    group = [g.Face(f'{mesh["node_offset"]}:{i}', str(mesh['node_offset']), tri)
             for i, tri in enumerate(faces)]
    ancestors = [node for node in scene.nodes if node['path'] == mesh['path'] or mesh['path'].startswith(node['path']+'.')]
    contract = material_contract(mesh['material'])
    result = {'case_id': case_id, 'course': course, 'landscape_resource': resource,
              'source_hash': t.sha(scene.payload), 'representation': 'PS2_VISUAL_SOURCE_MESH',
              'node_offset': mesh['node_offset'], 'node_path': mesh['path'],
              'material_offset': mesh['material_offset'], 'material': mesh['material'],
              'source_textures': mesh['textures'], 'material_contract': contract,
              'source_strips': mesh['strips'], 'source_faces': len(faces), 'excluded_triples': exclusions,
              'geometry': w.geometry_metrics(faces), 'attributes': attribute_summary(scene, mesh),
              'ancestors': ancestors, 'source_mesh_flags': mesh['flags'],
              'geometry_instance_count': 'UNKNOWN', 'live_visibility': 'UNKNOWN',
              'transform': 'NO LOCAL MATRIX IN SELECTED TAG1/6/5/2 SOURCE PATH',
              'shader_billboard': 'NOT_FOUND_IN_TRACED_HANDLER_CACHE_SELECTOR0_PATH',
              'shader_lod_fade': 'NOT_FOUND_IN_TRACED_HANDLER_PATH',
              'wind': 'NOT_FOUND_IN_TRACED_HANDLER_CACHE_SELECTOR0_PATH',
              'evidence_grade': 'CONFIRMED_BY_BOTH', 'runtime_validation': 'NOT_PERFORMED'}
    if contract['classification']:
        result['render_contract'] = state_contract(contract['interned_shader'])
    if pc:
        result['pc'] = exact_comparison(group, pc)
        texture = g.texture_key(mesh['textures'][0]['name'])
        result['pc']['same_texture_family_groups'] = [v for _, v in sorted(pc.groups.items())
                                                   if any(g.texture_key(x) == texture for x in v['textures'])]
        result['pc']['source'] = pc.source
    return result


def texture_inspection(manifest, input_root, name):
    resource = '\\TNG\\DATAPSM\\'+name.upper().replace('/', '\\')+'.GXI'
    payload, provenance = dr.payload_for(manifest, input_root, resource)
    metadata = p.parse_gxi(payload)  # Fail closed on unsupported variants.
    return {'resource': resource, 'provenance': provenance, 'metadata': metadata,
            'loader_chain': '3714e0 ->2fd7d0 ->2f84f0/2f9c80 -> mesh+dc/+e0 ->311c50',
            'file_channels': 'RGBA32; STORED_ALPHA_0..255',
            'runtime_storage_format': 'UNKNOWN_WITHOUT_SELECTED_DESCRIPTOR',
            'runtime_palette_and_alpha_conversion': 'NOT_FULLY_RECOVERED',
            'evidence_grade': 'CONFIRMED_BY_BYTES; NAME_TO_HANDLER_BINDING_CONFIRMED_BY_BOTH',
            'runtime_validation': 'NOT_PERFORMED'}


def pc_texture_inspection(pc_root, sdk, name, ps2_payload):
    """Compare stored pixels with explicit row policies using the read-only SDK."""
    g.c.sdk_modules(sdk)
    from master_rallye.dxt import parse_dxt, decode_rgba_pixels
    relative = Path('DataGx')/Path(name.replace('\\', '/')+'.dxt')
    path = pc_root/relative
    if not path.is_file():
        return {'path': relative.as_posix(), 'status': 'NOT_FOUND_AT_PAIRED_MATERIAL_PATH',
                'scope': 'EXPLICIT_PAIRED_PATH; NOT A GLOBAL ASSET ABSENCE CLAIM'}
    texture = parse_dxt(path)
    alpha = texture.bgra[3::4]
    metadata = p.parse_gxi(ps2_payload)
    comparisons = {}
    for policy in ('preserve-stored', 'flip-vertical'):
        pixels = decode_rgba_pixels(texture, row_policy=policy)
        comparisons[policy] = {'rgba_sha256': t.sha(pixels),
            'identical_ps2_stored_rgba': pixels == ps2_payload[8:],
            'equal_channel_bytes': sum(a == b for a, b in zip(pixels, ps2_payload[8:]))
                if len(pixels) == len(ps2_payload)-8 else None}
    return {'path': relative.as_posix(), 'size': path.stat().st_size,
            'sha256': t.file_hash(path), 'dimensions': [texture.width, texture.height],
            'stored_channels': 'BGRA; SDK CONVERTS TO RGBA',
            'alpha': {'min': min(alpha), 'max': max(alpha), 'distinct': len(set(alpha))},
            'same_dimensions': [texture.width, texture.height] == [metadata['width'], metadata['height']],
            'row_policy_comparisons': comparisons, 'runtime_alpha_consumption': 'UNKNOWN',
            'evidence_grade': 'CONFIRMED_BY_BYTES'}


def pc_draw_inspection(pc_root, sdk, course, matched_groups):
    """Selected compiled records; source flags do not claim a live PC shader."""
    g.c.sdk_modules(sdk)
    from master_rallye.dx_course import parse_course_dx
    folder = pc_root/'DataGx'/'Course'/w.CASES[course]
    paths = sorted(folder.glob('*.dx'))
    if len(paths) != 1:
        raise t.FormatError('Expected one explicitly paired PC DX')
    model = parse_course_dx(paths[0])
    selected = {row['draw_index'] for row in matched_groups}
    result = []
    for draw in model.physical_draws:
        if draw.draw_index not in selected:
            continue
        ordered_ids = model.draw_global_indices(draw)
        ids = sorted(set(ordered_ids))
        duplicate_faces = Counter()
        winding = {}
        for offset in range(0, len(ordered_ids), 3):
            points = tuple(model.vertices.positions[i] for i in ordered_ids[offset:offset+3])
            key = tuple(sorted(points))
            duplicate_faces[key] += 1
            order = min(itertools.permutations(range(3)), key=lambda perm: tuple(points[i] for i in perm))
            parity = sum(order[a] > order[b] for a in range(3) for b in range(a+1, 3)) % 2
            winding.setdefault(key, set()).add(parity)
        colors = [tuple(model.vertices.colors[4*i:4*i+4]) for i in ids]
        ranges = lambda values: [[min(v[j] for v in values), max(v[j] for v in values)]
                                for j in range(len(values[0]))] if values else []
        flags = list(draw.flags_0x20)
        suffix = ('NO_ALPHA_SUFFIX' if flags[0] == 0 else '_alpha' if flags[1] == 0 else '_alphatest') if len(flags) == 4 else 'UNKNOWN_LAYOUT'
        result.append({'draw_index': draw.draw_index, 'record_offset': draw.offset,
            'core_offset': draw.core_offset, 'tag': draw.tag,
            'raw_flags_0x20': flags, 'raw_feature_mask_0x24': draw.unknown_0x24,
            'generic_pc_selector_prediction': suffix,
            'prediction_scope': 'R4D_1 SHARED TAG2 LOADER/SELECTOR; COURSE LIVE HANDLER NOT CAPTURED',
            'referenced_vertices': len(ids), 'triangles': draw.triangle_count,
            'exact_unsigned_unique_triangles': len(duplicate_faces),
            'triangle_multiplicity_histogram': dict(sorted(Counter(duplicate_faces.values()).items())),
            'unsigned_triangles_with_both_windings': sum(len(v) == 2 for v in winding.values()),
            'winding_scope': 'COMPILED SOURCE REDUNDANCY; LIVE CULLING UNKNOWN',
            'normal_ranges': ranges([model.vertices.normals[i] for i in ids]),
            'stored_color_bgra_histogram': dict(sorted(Counter(str(v) for v in colors).items())),
            'uv_ranges': [ranges([uv.values[i] for i in ids]) for uv in model.uv_sets],
            'evidence_grade': 'CONFIRMED_BY_BYTES; SELECTOR APPLICATION STATIC_PC_INFERENCE'})
    return sorted(result, key=lambda row: row['draw_index'])


def inspect_cases(input_root, pc_root=None, sdk=None):
    from course_delta import EXPECTED
    w.verify_inputs(input_root)
    identity = {name: {'size': (input_root/name).stat().st_size, 'sha256': digest,
                       'verification': 'FRESH_SHA256_VERIFIED'}
                for name, digest in sorted(EXPECTED.items())}
    if bool(pc_root) != bool(sdk):
        raise t.FormatError('PC comparison requires both PC retail root and read-only SDK')
    manifest = t.load_pak(input_root/'TNG.PAK')[0]
    cases, sources, textures, pc_textures = [], {}, {}, {}
    for course in sorted({case[1] for case in CASES}):
        logical = f'\\TNG\\DATAPSM\\COURSE\\{course}\\{course}.PSM'
        payload, provenance = dr.payload_for(manifest, input_root, logical)
        scene = w.decode_scene(payload)
        pc = g.pc_adapter(pc_root, sdk, course) if pc_root else None
        sources[course] = {'resource': logical, 'provenance': provenance, 'decoded_sha256': t.sha(payload)}
        for case_id, _, offset, shader in (row for row in CASES if row[1] == course):
            matches = [mesh for mesh in scene.meshes if mesh['node_offset'] == offset]
            if len(matches) != 1 or material_contract(matches[0]['material'])['interned_shader'] != shader:
                raise t.FormatError('Selected canonical foliage node/material mismatch')
            row = inspect_mesh(scene, course, logical, matches[0], case_id, pc)
            if pc:
                row['pc']['selected_draw_attributes'] = pc_draw_inspection(pc_root, sdk, course,
                    row['pc']['matched_pc_groups'])
            cases.append(row)
            for tex in matches[0]['textures']:
                if tex['slot'] == 0 and tex['name'] != 'Null' and tex['name'] not in textures:
                    textures[tex['name']] = texture_inspection(manifest, input_root, tex['name'])
                    if pc:
                        payload, _ = dr.payload_for(manifest, input_root, textures[tex['name']]['resource'])
                        pc_textures[tex['name']] = pc_texture_inspection(pc_root, sdk, tex['name'], payload)
    return {'schema': SCHEMA, 'phase': 'PS2-TREEBLEND1', 'canonical_identity': identity,
            'sources': sources, 'cases': sorted(cases, key=lambda x: x['case_id']),
            'textures': [textures[k] for k in sorted(textures)],
            'pc_texture_evidence': [pc_textures[k] for k in sorted(pc_textures)],
            'runtime_validation': 'NOT_PERFORMED', 'geometry_output': 'COMPACT_SUMMARY_ONLY',
            'live_vu_residency': 'UNKNOWN', 'original_assets': 'READ_ONLY'}


def local_output(path):
    path = path.resolve()
    root = (ROOT/'data/treeblend1').resolve()
    if not path.is_relative_to(root) or path == root:
        raise t.FormatError('TREEBLEND1 diagnostics must stay under ignored data/treeblend1')
    if path.exists():
        raise t.FormatError('Existing diagnostic output preserved')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['states', 'cases'])
    ap.add_argument('--input-root', type=Path)
    ap.add_argument('--pc-root', type=Path)
    ap.add_argument('--sdk', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    if args.mode == 'states':
        result = {'schema': SCHEMA, 'states': [state_contract(s) for s in SHADERS]}
    else:
        if not args.input_root: ap.error('cases requires --input-root')
        result = inspect_cases(args.input_root, args.pc_root, args.sdk)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n'
    if args.output: local_output(args.output).write_text(text, encoding='utf-8', newline='\n')
    else: print(text, end='')


if __name__ == '__main__': main()
