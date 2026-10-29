"""Michelin PDO structural scenes; no guessed complete-car assembly or MR compiler.

The payload decoder is shared with michelin_research. Every XO is an independent
alternative; external positions are preserved, never silently mixed into it.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import struct
import math
import re
from .. import universal_vehicle_scene as u
from . import michelin_research as f

VERSION = 'michelin-neutral/1'
QUALIFIED = {
    'Car25A.PDO': ('bbbc58fe11456369231e595444d43377f94cc3f19af2e2057a4ec68a07802593', 'Toyota RAV 4'),
    'Car06A.PDO': ('f0a9400812814620832b4a3fe98a024318de72b929ba225a90c4a57e342e1a5b', 'Renault Megane F2'),
}


def ptoc(data):
    """Original 4bcf00: 54-byte records; type3 objects append via AddLOD."""
    if len(data) < 12 or data[:4] != b'PTOC': raise ValueError('PTOC header')
    count, = struct.unpack_from('<I', data, 4)
    if not 1 <= count <= 64 or len(data) != 8 + count*54 + 4: raise ValueError('PTOC record bounds')
    checksum, = struct.unpack_from('<i', data, len(data)-4)
    if checksum - sum(data[8:-4]) != -0xcc11bc: raise ValueError('PTOC original checksum')
    rows = []
    for i in range(count):
        at = 8+i*54; kind, distance = struct.unpack_from('<hf', data, at)
        if not math.isfinite(distance): raise ValueError('PTOC nonfinite distance')
        name = data[at+6:at+54].split(b'\0',1)[0].decode('ascii')
        if name: u.relative_name(name)
        rows.append({'offset': at, 'type': kind, 'distance': distance, 'name': name,
                     'raw_hex': data[at:at+54].hex()})
    if rows[0]['type'] != 0 or any(r['type'] != 3 or not r['name'] for r in rows[1:]):
        raise ValueError('Unsupported PTOC attachment branch')
    return rows


def geometry(model, member, digest):
    """Expand original indexed corners without welding or polygon correction."""
    groups = {}
    for face in model['triangles']:
        ti = face['candidate_texture_index']
        g = groups.setdefault(ti, {'positions': [], 'normals': [], 'uvs': [], 'triangles': [], 'offsets': [], 'preview_colors_bgra': [], 'face_normal_fallbacks': []})
        base = len(g['positions'])
        for corner, (vi, ni, uv) in enumerate(zip(face['vertex_indices'], face['normal_indices'], face['uv'])):
            if not 0 <= vi < len(model['positions']) or not 0 <= ni < len(model['normals']):
                raise ValueError('Michelin corner index outside source arrays')
            g['positions'].append(model['positions'][vi][:])
            normal = model['normals'][ni][:]
            if sum(v*v for v in normal) < 1e-16:
                normal = face['face_normal'][:]
                if sum(v*v for v in normal) < 1e-16:
                    raise ValueError('Zero indexed and face source normals')
                g['face_normal_fallbacks'].append({'corner':base+corner,'triangle_offset':face['source_offset'],'original_index':ni,
                                                  'policy':'Neutral fallback to original source face normal; original indexed zero retained in inspection'})
            g['normals'].append(normal); g['uvs'].append(uv[:])
            # Original 4baaa0: source triangle+0x38 bit16 selects uniform 0x5e.
            flags = face['unknown_u32_at48'][2]
            c = face['corner_color_u32_at68'][corner]
            color = [c >> 16 & 255, c >> 8 & 255, c & 255, c >> 24 & 255]
            if ti or flags & 0x10000: color = [94]*4 if flags & 0x10000 else [255]*4
            # Blend remains neutral opaque; retain exact source words in inspection.
            color[3] = 255
            g['preview_colors_bgra'].append(color)
        g['triangles'].append([base, base+1, base+2]); g['offsets'].append(face['source_offset'])
    result = []
    for ti, g in sorted(groups.items()):
        offsets = g.pop('offsets'); fallbacks = g.pop('face_normal_fallbacks'); key = 'texture-%03d' % ti
        result.append({'id': key, 'material_id': key, **g,
                       'source': {'member': member, 'member_sha256': digest,
                                  'triangle_offsets': offsets, 'face_normal_fallbacks': fallbacks,
                                  'corner_policy': 'exact original index order; no flips/welds'}})
    return result


def texture_preview(data):
    """Native-qualified coverage, not a fictitious source palette alpha channel.

    4ba190 selects alpha-capable formats for magenta palette0; 408520 ->
    407fe0 case1 emits coverage 0 for index0 and 255 otherwise. Black is never
    keyed. Exact original TGA/palette remain separate immutable sidecars.
    """
    from PIL import Image
    meta = f.indexed_tga(data)
    first = data[meta['palette_offset']:meta['palette_offset']+3]
    keyed = first[0]>=241 and first[1]<=14 and first[2]>=241
    with Image.open(BytesIO(data)) as im:
        indices = im.tobytes();rgba = bytearray(im.convert('RGB').convert('RGBA').tobytes())
    if keyed:
        rgba[3::4] = bytes(0 if i==0 else 255 for i in indices)
    return meta,bytes(rgba),keyed


def build(raw, archive, variant, source_root, *, wheel=False):
    """Pure construction, also usable with invented source-free fixtures."""
    if ((archive not in QUALIFIED and not (wheel and re.fullmatch(r'Tarmac_t0\d{3}\.pdo', archive)))
        or type(variant) is not int or not 0 <= variant < (3 if wheel else 4)):
        raise ValueError('Explicit qualified catalog and independent XO variant 0..3 required')
    tree, decoded = f.inspect_archive(raw)
    names = {name[len('decoded/'):].casefold(): name for name in decoded if name.startswith('decoded/')}
    number = archive[3:5]
    wanted = archive[:-4]+'_%d.XO'%variant if wheel else 'CAR%sA_%d.XO' % (number, variant)
    member_key = names.get(wanted.casefold())
    if member_key is None: raise ValueError('Missing selected original XO')
    member = member_key[len('decoded/'):]; model = f.xobj_structure(decoded[member_key])
    toc_key = names.get('index.toc')
    if toc_key is None: raise ValueError('Missing original PTOC')
    lods = ptoc(decoded[toc_key])
    if member.casefold() not in [r['name'].casefold() for r in lods[1:]]: raise ValueError('XO missing from source PTOC')
    assets = {}; resources = []; by_member = {}
    for name, data in sorted(decoded.items()):
        if not name.startswith('decoded/'): continue
        original = name[len('decoded/'):]; path = 'original/' + original
        assets[path] = data
        rec = {'member': original, 'snapshot_path': path, 'bytes': len(data), 'sha256': u.sha(data)}
        resources.append(rec); by_member[original.casefold()] = rec
    textures = []; texture_ids = {}
    for ordinal, name in enumerate(model['texture_names'], 1):
        key = names.get(name.casefold())
        if key is None: raise ValueError('Missing original texture reference: ' + name)
        data = decoded[key]; meta,rgba,keyed = texture_preview(data)
        width,height = meta['width'],meta['height']
        tid = 'texture-%03d' % ordinal; path = 'textures/' + tid + '.rgba'
        assets[path] = rgba; texture_ids[ordinal] = tid
        textures.append({'id': tid, 'name': name, 'width': width, 'height': height,
                         'rgba_path': path, 'rgba_sha256': u.sha(rgba),
                         'source': by_member[name.casefold()],
                         'source_channels': {'mode': 'original indexed8/BGR24 palette', 'original_tga': meta,
                                             'native_index0_coverage':keyed,
                                             'alpha': 'Native 4ba190/407fe0 index0 coverage when magenta sentinel; not palette alpha. Otherwise opaque; no black/descriptor inference'}})
    assets['textures/untextured.rgba'] = bytes([255]*4)
    textures.append({'id': 'untextured', 'width': 1, 'height': 1, 'rgba_path': 'textures/untextured.rgba',
                     'rgba_sha256': u.sha(bytes([255]*4)), 'source_channels': {'mode': 'derived white untextured diagnostic'}})
    meshes = geometry(model, member, by_member[member.casefold()]['sha256'])
    materials = []
    for mesh in meshes:
        ti = int(mesh['id'].split('-')[-1])
        if ti > len(texture_ids): raise ValueError('Invalid one-based texture dispatch')
        tid = texture_ids.get(ti, 'untextured')
        keyed = next(t for t in textures if t['id']==tid)['source_channels'].get('native_index0_coverage',False)
        materials.append({'id': mesh['id'], 'diffuse_texture_id': tid,
                          'raw_fields': [face for face in model['triangles'] if face['candidate_texture_index'] == ti],
                          'flags': {'transparent_raw': str(int(keyed)), 'evidence':'4ba190 magenta palette0 dispatch; 407fe0 case1 index0 coverage. Neutral D3D9 blend approximates original cutout'},
                          'unsupported': ['Original alpha/lighting and UV sampling orientation incomplete'],
                          'preview': {'opacity': 1.0, 'policy': 'Native 4ba6c0: 0 empty / 1..N name table; neutral opaque'}})
    external = names.get(('CAR%s_%d_VERTEX.BIN' % (number, variant)).casefold())
    differences = None
    if not wheel:
        if external is None: raise ValueError('Missing separate original vertex stream')
        data = decoded[external]
        if len(data) != len(model['positions'])*12: raise ValueError('External/XO vertex count mismatch')
        points = list(struct.iter_unpack('<3f', data))
        differences = sum(list(a) != b for a, b in zip(points, model['positions']))
    unknowns = [
        'PTOC contains LOD chain, not four assembled parts; original runtime distance selection not simulated',
        'Wheel resources and attachment transforms unresolved; NO substitute wheels',
        'Source axes/handedness/physical units unresolved: identity inspection basis only',
        'One-based texture dispatch native-qualified; complete UV sampling orientation still under inspection',
        'Native magenta/index0 coverage recovered; glass, cutout thresholds, filtering and lighting remain incomplete; black never keyed',
    ]
    root = str(Path(source_root).absolute())
    scene = {'schema': u.SCHEMA, 'source': {'root': root, 'game': 'Michelin Rally Masters', 'adapter': VERSION,
               'catalog': archive, 'archive_sha256': u.sha(raw), 'resources': resources},
             'metadata': {'display_name': (QUALIFIED[archive][1] if not wheel else archive) + ' — XO%d PARTIAL / assembly WARN' % variant,
                          'qualification': 'Independent source XO, not a qualified default complete vehicle',
                          'selected_xo': member, 'external_vertex_member': external[len('decoded/'):] if external else None,
                          'external_different_positions': differences, 'native_create': False,
                          'lods': lods, 'external_role': 'Damage target: native 4856c0; XO backup restored by 48b9b0'},
             'coordinate_system': {'source_to_normalized': [1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,-1.,0.,0.,0.,0.,1.],
                                   'interpretation_status': 'Inspection front -Z from source FRONT/BACK panel placement; physical units/game handedness unqualified',
                                   'evidence': ['Exact source geometry; +Y roof, +Z FRONT-panel geometry; reflection is reversible viewer normalization only']},
             'textures': textures, 'materials': materials, 'meshes': meshes,
             'nodes': [{'id': 'original-xo', 'name': member, 'parent_id': None,
                        'mesh_ids': [m['id'] for m in meshes], 'role': 'body',
                        'source_local_transform': None, 'local_transform': u.IDENTITY[:],
                        'visible': True, 'source_visible': True,
                        'transform_evidence': 'Derived identity inspection instance, NOT recovered source hierarchy/default selection'}],
             'selection': {'variant': variant}, 'measurements': {'source_bounds': model['source_bounds']},
             'unknown_semantics': [{'id': str(i), 'status': 'WARN', 'meaning': text} for i, text in enumerate(unknowns)]}
    assets['inspection/archive.json'] = u.canonical(tree)
    assets['inspection/xobj.json'] = u.canonical(model)
    u.validate_scene(scene)
    return scene, assets


def recover(source_root, archive, variant, output):
    root = Path(source_root).absolute()
    if archive not in QUALIFIED: raise ValueError('Unqualified Michelin catalog')
    path = root/'Data/Objects'/archive; raw = u.read_bounded(path, f.MAX_FILE)
    if u.sha(raw) != QUALIFIED[archive][0]: raise ValueError('Unqualified Michelin archive hash')
    scene, assets = build(raw, archive, variant, root)
    result = u.save_scene(scene, Path(output), assets, protected_roots=[root])
    if u.sha(u.read_bounded(path, f.MAX_FILE)) != u.sha(raw): raise ValueError('Original source changed')
    return result


CATALOG_SHA = 'bb52e07b8287e28003be86ebb4fc700277b14a6af93cea823dd6dc7535bc730b'
EXE_SHA = '71c6c36505102e75518a7f6843bbc8355f205e439086e389ec877225e3e0a8ae'
WHEEL_SHA = {
    'Tarmac_t0004.pdo': '51a4958b2a5d8b8eff55a9455b1ac439e3ed970add60606f26e49391e8d9cf33',
    'Tarmac_t0022.pdo': '649edf6cb2c989f86fd721456c9a79fdc3650946771cf31637e76900b7c5d6f8',
}


def catalog_rest(data, car_id, tyre_choice):
    """Native 405b10 catalog dispatch; 4890e0 static initial hub calculation."""
    if len(data) != 24*1608 or type(tyre_choice) is not int or not 0 <= tyre_choice < 5:
        raise ValueError('Catalog size/explicit Tarmac tyre choice 0..4')
    records = [i for i in range(0,len(data),1608) if struct.unpack_from('<I',data,i+28)[0] == car_id]
    if len(records) != 1: raise ValueError('Missing/ambiguous catalog identity')
    at = records[0]; tyre, = struct.unpack_from('<I',data,at+0x140+tyre_choice*4)
    if not 1 <= tyre <= 999: raise ValueError('Catalog wheel identifier budget')
    radius = struct.unpack('<f',struct.pack('<I',0x3e9cac08 if tyre//100 == 1 else 0x3eae147b))[0]
    hubs = []
    for i in range(4):
        offset = at+0x1d0+i*12; original = list(struct.unpack_from('<3f',data,offset))
        if not all(math.isfinite(x) and abs(x)<20 for x in original): raise ValueError('Catalog attachment bounds')
        derived = original[:]; derived[1] -= radius
        hubs.append({'offset': offset, 'original_xyz': original, 'initial_hub_xyz': derived})
    return {'record_offset': at, 'tyre_offset': at+0x140+tyre_choice*4, 'tyre_id': tyre,
            'archive': 'Tarmac_t0%03d.pdo'%tyre, 'initial_radius': radius, 'hubs': hubs,
            'evidence': '405b10-405b63 catalog+(road+16)*20+choice*4; 4890e0 +1d0 XYZ and Y-radius',
            'boundary': 'Explicit Tarmac choice; initial unsprung positions, NOT running settled suspension'}


def assemble(source_root, archive, output, *, tyre_choice=0):
    """Source body LOD0 + four authentic wheels at native initial catalog hubs.

    Zero steering/spin is a neutral inspection assumption, never runtime parity.
    """
    root = Path(source_root).absolute()
    if archive not in QUALIFIED: raise ValueError('Unqualified body archive')
    original = {}
    def read(relative, expected=None):
        raw = u.read_bounded(root/relative, f.MAX_FILE)
        if expected and u.sha(raw) != expected: raise ValueError('Unqualified original '+relative)
        original[relative] = u.sha(raw)
        return raw
    read('RallyMasters.EXE', EXE_SHA)
    catalog = read('Server/Data/Cars.BIN', CATALOG_SHA)
    rest = catalog_rest(catalog,int(archive[3:5]),tyre_choice)
    body, assets = build(read('Data/Objects/'+archive, QUALIFIED[archive][0]),archive,0,root)
    if rest['archive'] not in WHEEL_SHA: raise ValueError('Selected wheel bank not qualified in this bounded pilot')
    wheel_raw = read('Data/Objects/'+rest['archive'],WHEEL_SHA[rest['archive']])
    wheel, wheel_assets = build(wheel_raw,rest['archive'],0,root,wheel=True)
    # Each bank owns its own texture names; no cross-bank filename collision.
    from copy import deepcopy
    def prefix(scene, blobs, bank):
        scene = deepcopy(scene)
        for row in scene['source']['resources']:
            row['member'] = bank+'/'+row['member']; row['snapshot_path'] = bank+'/'+row['snapshot_path']
        for row in scene['textures']:
            row['id'] = bank+'-'+row['id']; row['rgba_path'] = bank+'/'+row['rgba_path']
            # deepcopy retains the shared resource-record reference used by textures;
            # it was prefixed once above, so do not prefix it a second time.
        for row in scene['materials']:
            row['id'] = bank+'-'+row['id'];row['diffuse_texture_id'] = bank+'-'+row['diffuse_texture_id']
        for row in scene['meshes']:
            row['id'] = bank+'-'+row['id'];row['material_id'] = bank+'-'+row['material_id'];row['source']['member'] = bank+'/'+row['source']['member']
        return scene, {bank+'/'+k:v for k,v in blobs.items()}
    body, assets = prefix(body,assets,'body');wheel,wheel_assets = prefix(wheel,wheel_assets,'wheel'); assets.update(wheel_assets)
    body['nodes'][0]['mesh_ids'] = [m['id']for m in body['meshes']]
    body['textures'].extend(wheel['textures']);body['materials'].extend(wheel['materials']);body['meshes'].extend(wheel['meshes'])
    body['source']['resources'].extend(wheel['source']['resources'])
    assets['original/Cars.BIN'] = catalog
    body['source']['resources'].append({'member':'Cars.BIN','snapshot_path':'original/Cars.BIN','bytes':len(catalog),'sha256':u.sha(catalog)})
    for i, hub in enumerate(rest['hubs']):
        matrix = u.IDENTITY[:];matrix[3],matrix[7],matrix[11] = hub['initial_hub_xyz']
        body['nodes'].append({'id':'wheel-%d'%i,'name':rest['archive']+' instance %d'%i,'parent_id':None,
                             'mesh_ids':[m['id']for m in wheel['meshes']], 'role':'wheel',
                             'local_transform':matrix,'source_local_transform':None,'visible':True,'source_visible':True,
                             'source_transform_record':hub,
                             'transform_evidence':rest['evidence']+'; identity spin/steer is neutral inspection assumption, side/runtime basis unqualified'})
    body['metadata'].update(display_name=QUALIFIED[archive][1]+' — original static assembly / L2 WARN',
                            qualification='Authentic body/wheels, native initial hub positions; neutral zero spin/steer, incomplete source renderer',
                            source_hashes=original,wheel_selection=rest)
    body['unknown_semantics'][1]['meaning'] = 'Native initial hubs and catalog wheel resource qualified; running settled/steer/spin and side matrices unqualified'
    body['measurements']['wheel_assembly'] = rest
    result = u.save_scene(body,Path(output),assets,protected_roots=[root])
    for relative, digest in original.items():
        if u.sha(u.read_bounded(root/relative,f.MAX_FILE)) != digest: raise ValueError('Source changed')
    return result
