"""Four exact COMPLETE material fixes; retains prior20 profiles and rejected originals."""
from pathlib import Path
from collections import defaultdict
import importlib.util,json,struct
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('prior_fleet_converter',PORT/'docs/vehicle-crew-port1/fleet/convert_fleet_complete.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
c,source=old.c,old.source

def convert(data, row, default):
    source.validate(data)
    _, _, size, count, tex_count, source_sha = source.HEADER.unpack_from(data)
    pos = source.HEADER.size
    meta = json.loads(data[pos:pos + size]); pos += size
    original = row['models']['COMPLETE']
    if source_sha.hex() != original['sha256'] or meta['family'] != row['ps2_family']:
        raise ValueError('Pinned fleet source identity mismatch')
    if meta['extra_nodes'] or meta['unresolved_textures']:
        raise ValueError('Unsupported hierarchy/texture')
    if [m['path'] for m in meta['meshes']] != ['root.' + str(i) for i in range(len(meta['meshes']))]:
        raise ValueError('Non-flat root')
    raw = data[pos:pos + count * 52]; pos += count * 52
    textures, texture_rows = [], []
    for i in range(tex_count):
        size = struct.unpack_from('<I', data, pos)[0]; pos += 4
        gxi = data[pos:pos + size]; pos += size
        info, pixels = c.texture(gxi)
        if info['sha256'] != meta['textures'][i]['sha256']:
            raise ValueError('Original GXI mismatch')
        textures.append(struct.pack('<3I', info['width'], info['height'], len(pixels)) + pixels)
        texture_rows.append({**meta['textures'][i], 'argb_sha256': c.sha(pixels),
                             'width': info['width'], 'height': info['height']})
    indices, meshes, mesh_rows, secondary_kinds = [], [], [], []
    default_index = None
    for m in meta['meshes']:
        slots = [c.NONE] * 3
        for s in m['textures']:
            if s['private_texture_index'] is None:
                raise ValueError('Unresolved original texture')
            slots[s['slot']] = s['private_texture_index']
        authored_secondary = secondary = next((s['name'] for s in m['textures'] if s['slot'] == 1), '')
        primary_fix = (row['ps2_family'], m['node_offset']) in {('KIASPORTAGE', 379852), ('TATA', 349913)}
        if primary_fix:
            if slots[0] != c.NONE or m['material'].lower() != '$shader(carshiny)':
                raise ValueError('Pinned missing-primary source changed')
            secondary = ''
            slots[1:] = [c.NONE, c.NONE]
        contract = c.reflection_runtime.material_contract(m['material'], secondary)
        mode = contract['mode']
        if mode is None:
            if '$shader(' in m['material'].lower():
                raise ValueError('Unproved explicit shader: ' + m['material'])
            mode = 0
            slots[1:] = [c.NONE, c.NONE]
        if slots[0] == c.NONE and (mode == 0 or primary_fix):
            if default_index is None:
                if c.sha(default) != c.DEFAULT_SHA:
                    raise ValueError('Default GXI drift')
                info, pixels = c.texture(default)
                default_index = len(textures)
                textures.append(struct.pack('<3I', info['width'], info['height'], len(pixels)) + pixels)
                texture_rows.append({'path': '\\TNG\\DEFAULT.GXI', 'sha256': c.sha(default),
                                     'argb_sha256': c.sha(pixels), 'width': info['width'], 'height': info['height']})
            slots[0] = default_index
        if mode not in (0, 1, 2, 3, 20):
            raise ValueError('Unimplemented material mode ' + str(mode))
        if slots[0] == c.NONE:
            raise ValueError('Missing primary for explicit shader: node ' + str(m['node_offset']) + ' mode ' + str(mode))
        kind = ('MIXED_FRAMEBUFFER_ENVIRONMENT' if mode == 3 and
                contract.get('effective_secondary') == 'CommonTextures\\rendertarget64x64' else
                'AUTHORED_SECONDARY' if mode == 3 else 'NO_STAGE1_REFLECTION')
        secondary_kinds.append({'path': m['path'], 'mode': mode,
                                'authored_secondary': authored_secondary,
                                'primary_default_from_original_loader': primary_fix,
                                'effective_secondary': contract.get('effective_secondary'),
                                'kind': kind, 'mixed_reflection': kind == 'MIXED_FRAMEBUFFER_ENVIRONMENT'})
        ids, diag = c.indices_for_mesh(raw, m)
        meshes.append(c.MESH.pack(m['node_offset'], mode, *slots, len(indices), len(ids)))
        mesh_rows.append({**m, 'mode': mode, 'texture_indices': slots, 'first_index': len(indices),
                          'index_count': len(ids), 'faces': len(ids) // 3, **diag})
        indices.extend(ids)
    if len(indices) != original['faces_all_authored_branches'] * 3 or count != original['vertices']:
        raise ValueError('Original source count mismatch')
    manifest = {'schema_version': 2, 'source': meta, 'meshes': mesh_rows, 'texture_upload': texture_rows,
                'source_asset_sha256': c.sha(data), 'coordinates': 'ORIGINAL_MODEL_LOCAL_NATIVE_WORLD',
                'winding': 'ORDERED_SOURCE_TRIPLES_CULL_NONE', 'alpha': 'ORIGINAL_NO_REMAP',
                'primary_orientation': 'RAW_UV_RUNTIME_V_EQUALS_1_MINUS_V',
                'default_mode': 'PROVED_NO_SHADER_MODE0_ORIGINAL_PRIMARY_SECONDARY_INACTIVE'}
    text = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    binary = (c.HEADER.pack(c.MAGIC, 2, len(text), len(meshes), count, len(indices), len(textures), source_sha)
              + text + b''.join(meshes) + b''.join(c.vertex(raw, i) for i in range(count))
              + struct.pack('<%dI' % len(indices), *indices) + b''.join(textures))
    return binary, {'family': row['pc_family'], 'ps2_family': row['ps2_family'],
                    'filename': row['ps2_family'] + '-COMPLETE-FLEET-FIX1.ps2model',
                    'sha256': c.sha(binary), 'bytes': len(binary), 'vertices': count,
                    'indices': len(indices), 'textures': len(textures), 'ps2_meshes': len(meshes),
                    'mesh_secondary_kinds': secondary_kinds,
                    'source_sha256': original['sha256'], 'pc_sources': original['pc_compiled_source']['draws'],
                    'texture_dimensions': [[x['width'], x['height']] for x in texture_rows]}


def main():
    previous=json.loads((PORT/'docs/vehicle-crew-port1/fleet/frontend-profiles.json').read_text())
    rows=json.loads((PORT/'docs/vehicle-crew-port1/fleet/coverage.json').read_text())['fleet']
    default=(PORT/'.assets/vehicles/XTRAIL-default.gxi').read_bytes()
    added=[]
    for row in rows:
        if row['ps2_family'] not in {'KIASPORTAGE','TATA','MATTSERATI','SIMMBUGGHINI'}:continue
        original=PORT/'.assets/vehicles'/(row['ps2_family']+'-COMPLETE.ps2vehicle')
        binary,profile=convert(original.read_bytes(),row,default)
        out=c.private_output(PORT/'.assets/vehicles'/profile['filename'])
        if out.exists() and out.read_bytes()!=binary:raise ValueError('Existing fixed asset differs')
        out.write_bytes(binary);added.append(profile)
    profiles=previous['profiles']+added
    owners=defaultdict(set)
    for row in rows:
        for d in row['models']['COMPLETE'].get('pc_compiled_source',{}).get('draws',[]):
            owners[(d['vertices'],d['faces'],d['geometry_sha256'])].add(row['pc_family'])
    for p in profiles:
        for d in p['pc_sources']:d['unique_family_in_all_paired_complete_sources']=len(owners[(d['vertices'],d['faces'],d['geometry_sha256'])])==1
    result={'profiles':profiles,'rejected':[r for r in previous['rejected'] if r['family'] not in {p['ps2_family'] for p in added}],'new_profiles':4,'runtime':'PENDING_USER_AB','mode2_note':'GS source alpha normalization versus D3D approximation remains; no pixel parity'}
    (HERE/'frontend-profiles.json').write_text(json.dumps(result,indent=2)+'\n')
    header=['#pragma once','#include <cstddef>','namespace gfx2::ps2port {','struct FleetProfile {const char *family,*ps2Family,*filename,*sha;std::size_t size;unsigned vertices,indices,textures,ps2Meshes,pcDrawCount;const FrontendSource* source;const bool* unique;const bool* mixedReflection;};']
    for p in profiles:
        ident=p['ps2_family'];header+=['inline constexpr FrontendSource kFleetSources'+ident+'[]={']+[' {"%s",%d,%d},'%(d['geometry_sha256'],d['vertices'],d['faces']) for d in p['pc_sources']]+['};']
        header+=['inline constexpr bool kFleetUnique'+ident+'[]={'+','.join('true' if d['unique_family_in_all_paired_complete_sources'] else 'false' for d in p['pc_sources'])+'};','inline constexpr bool kFleetMixedReflection'+ident+'[]={'+','.join('true' if m['mixed_reflection'] else 'false' for m in p['mesh_secondary_kinds'])+'};']
    header+=['inline constexpr FleetProfile kFrontendFleetProfiles[]={']
    for p in profiles:
        header+=[' {"%s","%s","%s","%s",%d,%d,%d,%d,%d,%d,kFleetSources%s,kFleetUnique%s,kFleetMixedReflection%s},'%(p['family'],p['ps2_family'],p['filename'],p['sha256'],p['bytes'],p['vertices'],p['indices'],p['textures'],p['ps2_meshes'],len(p['pc_sources']),p['ps2_family'],p['ps2_family'],p['ps2_family'])]
    header+=['};','}'];(HERE/'frontend_fleet_registry.hpp').write_text('\n'.join(header)+'\n')
    print(json.dumps({'admitted':len(profiles),'added':[p['ps2_family'] for p in added],'rejected':result['rejected']}))
if __name__=='__main__':main()
