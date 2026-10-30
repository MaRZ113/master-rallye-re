"""Read-only Dakar2 renderer evidence and derived UVS inspection projects.

The original L1 projects remain immutable. Static state inference is deliberately
separate from observed runtime state and full source shader parity.
"""
from copy import deepcopy
from pathlib import Path
import struct
from .. import universal_vehicle_scene as uvs
from .dakar2 import PINS
from .dakar2_disc import FileReader, xdvdfs
from .dakar2_formats import RBB, digest, sbb_entries

VERSION = 'dakar2-render-research/1'


def expose_uv1(source,output):
    """Expose an already retained source stream as typed UVS, without shader guesses."""
    source=Path(source);scene=uvs.load_scene(source)
    if scene['metadata'].get('adapter')!='dakar2-xbox-source/1':raise ValueError('Qualified Dakar2 source scene required')
    original=deepcopy(scene);manifest=uvs.load_json(uvs.read_bounded(source.parent/'manifest.json',2*1024*1024))
    assets={name:uvs.read_bounded(source.parent/name,uvs.MAX_OUTPUT_BYTES)for name in manifest['files']if name!='scene.json'}
    aliases=0;count=0
    for mesh in scene['meshes']:
        stream=mesh['source'].get('streams',{}).get('10')
        if stream is None:continue
        raw=assets[stream['path']]
        if stream['stride']!=8 or len(raw)!=8*len(mesh['positions'])or uvs.sha(raw)!=stream['sha256']:
            raise ValueError('Original UV1 stream association mismatch')
        values=[list(v)for v in struct.iter_unpack('<2f',raw)]
        mesh['uv_channels']={'1':{'values':values,'evidence':'Exact original XMD stream10 float2, original bytes/hash retained; shader use remains unknown'}}
        aliases+=values==mesh['uvs'];count+=1
    scene['metadata']['typed_uv1_research']={'source_scene_sha256':digest(source.read_bytes()),'meshes':count,
        'exact_uv0_aliases':aliases,'source_shader_equivalence':False}
    for before,after in zip(original['meshes'],scene['meshes']):
        for key in ('positions','normals','uvs','triangles','source','preview_colors_bgra'):
            if before.get(key)!=after.get(key):raise ValueError('UV1 exposure changed original source geometry/streams')
    result=uvs.save_scene(scene,output,assets)
    return {**result,'uv1_meshes':count,'exact_uv0_aliases':aliases,'source_shader_equivalence':False}


def executable_evidence(image):
    reader = FileReader(image)
    row = next(r for r in xdvdfs(reader, 0x18300000) if r['path'].lower() == 'default.xbe')
    data = reader.read(row['offset'], row['bytes'])
    if digest(data) != PINS['default.xbe']:
        raise ValueError('Unqualified Dakar2 executable')
    base = struct.unpack_from('<I', data, 0x104)[0]
    count, table = struct.unpack_from('<II', data, 0x11c)
    if count > 32: raise ValueError('XBE section budget')
    sections = [struct.unpack_from('<5I', data, table-base+i*56) for i in range(count)]
    def original(va, size):
        for flags, address, virtual_size, offset, stored in sections:
            if address <= va and va+size <= address+stored:
                return data[offset+va-address:offset+va-address+size]
        raise ValueError('Evidence VA outside original XBE section bytes')
    declarations = {}
    for va in (0x1940cc, 0x1940f4, 0x194144, 0x194158):
        key, vertex, pixel, blend, attributes = struct.unpack('<5I', original(va, 20))
        shader = original(pixel, 240)
        declarations[str(key)] = {'table_va':va, 'vertex_program_va':vertex,
            'pixel_definition_va':pixel, 'blend_mode':blend, 'attributes_va':attributes,
            'pixel_definition_sha256':digest(shader),
            'pixel_definition_words':list(struct.unpack('<60I', shader))}
    functions = {}
    for name, va, size in [('cull_emit',0xe3f50,112), ('front_face',0xe3fc0,56),
                         ('state_flush',0x87700,96), ('vehicle_draw',0x46ae0,64),
                         ('depth_write',0x86900,21), ('matrix_upload',0x88eb0,192)]:
        functions[name] = {'va':va, 'bytes':size, 'original_sha256':digest(original(va,size))}
    return {'schema':VERSION, 'xbe_sha256':digest(data), 'declarations':declarations,
        'functions':functions, 'runtime':'NOT TESTED',
        'cull_rule':'87700: enabled[3] ? requested front convention : NONE; e3f50 emits NV097 308/39c; e3fc0 emits 3a0',
        'context':'Static default scene inference from344f0/34703 disabled[3]; vehicle5ee50/46ae0 does not enable[3]. Runtime state capture still required.',
        'texture_stages':'8b590 binds all four original texture fields; pixel definitions retained, not replaced with MR materials'}


def derive_scene(source, output, evidence):
    source, output = Path(source), Path(output)
    scene = uvs.load_scene(source)
    if scene['metadata'].get('adapter') != 'dakar2-xbox-source/1':
        raise ValueError('Qualified Dakar2 L1 scene required')
    if evidence.get('xbe_sha256') != PINS['default.xbe']:
        raise ValueError('Qualified executable evidence required')
    original = deepcopy(scene)
    root = source.parent
    assets = {}
    # Retain every original sidecar exactly, with the existing immutable manifest.
    manifest = __import__('json').loads((root/'manifest.json').read_text())
    for name in manifest['files']:
        if name != 'scene.json': assets[name] = (root/name).read_bytes()
    resource = next(r for r in scene['source']['resources'] if r['member'].endswith('.LOD'))
    block = RBB(assets[resource['snapshot_path']]); lod = block.resources[0]['offset']
    node_by_mesh = {mid:n for n in scene['nodes'] for mid in n['mesh_ids']}
    for mesh in scene['meshes']:
        colors = (root/mesh['source']['streams']['3']['path']).read_bytes()
        mesh['preview_colors_bgra'] = [list(colors[i:i+4]) for i in range(0,len(colors),4)]
        node = node_by_mesh[mesh['id']]; ordinal = node['source_transform_record']['id']
        flags = block.u(lod+8+ordinal*8)
        node['source_lod_flags'] = flags
        node['render_pass'] = 1 if flags & 0x8000000 else 0
    material_by_id = {m['id']:m for m in scene['materials']}
    for mesh in scene['meshes']:
        mat = material_by_id[mesh['material_id']]; raw = mat['raw_fields'][0]
        fourth = raw['source_offset']+0x1c
        binding = block.reference(fourth)['id'] if fourth in block.external else None
        if binding is None and block.u(fourth)!=0:raise ValueError('Unknown fourth texture binding')
        raw['native_four_texture_resource_ids'] = raw['texture_resource_ids'][:3]+[binding]
        declaration = evidence['declarations'][str(raw['declaration'])]
        node = node_by_mesh[mesh['id']]
        mat['source_render_state'] = {'schema':VERSION, 'cull':'none',
            'cull_qualification':'STATIC_DEFAULT_PASS_INFERENCE; not observed runtime',
            'cull_evidence':'344f0 disables state3 at34703; 5ee50/46ae0 preserve it; 87700/e3f50 flush NONE when state3=0',
            'depth_write':True, 'depth_evidence':'5ee50 ->86900(1) at5ef7a ->87470(40,1)',
            'blend':declaration['blend_mode']==3, 'alpha_test':'UNKNOWN',
            'draw_pass':node['render_pass'], 'draw_order':node['source_transform_record']['id'],
            'pixel_definition_sha256':declaration['pixel_definition_sha256'],
            'shader_approximation':'UV0*T0*original color only; source lighting, UV1/secondary combiners remain unresolved'}
        mat['unsupported'] = ['original lighting/UV1/secondary shader stages', 'runtime alpha test and equipment selection']
    scene['metadata']['renderer_research'] = {'schema':VERSION, 'original_scene_sha256':digest(source.read_bytes()),
        'implementation_sha256':digest(Path(__file__).read_bytes()),
        'qualification':'L2 WARN: static cull/depth/order rules; original shader and runtime parity incomplete',
        'native_evidence':'inspection/native-renderer.json'}
    scene['metadata']['neutral_preview'] = {'cull':'source'}
    scene['metadata']['qualification'] = scene['metadata']['renderer_research']['qualification']
    scene['unknown_semantics'].append({'id':'renderer-state-context', 'status':'WARN',
        'meaning':'Cull NONE is a static default scene-context inference per draw, not a global polygon repair. Original runtime capture unavailable.'})
    assets['inspection/native-renderer.json'] = uvs.canonical(evidence)
    # Explicit conservation before serialization: only derived inspection fields change.
    for before, after in zip(original['meshes'], scene['meshes']):
        for name in ('positions','normals','uvs','triangles','source'):
            if before[name] != after[name]: raise ValueError('Original mesh stream changed')
    return uvs.save_scene(scene, output, assets, protected_roots=[source.parent, *map(Path,scene['source'].get('protected_roots',[]))])


def variant_inventory(image):
    reader = FileReader(image)
    row = next(r for r in xdvdfs(reader,0x18300000) if r['path'].lower().endswith('/all.sbb'))
    data = reader.read(row['offset'],row['bytes'])
    if digest(data) != PINS['ALL.SBB']: raise ValueError('Unqualified SBB revision')
    result=[]
    for member in sbb_entries(data):
        if not member['name'].startswith(('PAJERO_','HINO_','NISSAN_')): continue
        block=RBB(data[member['offset']:member['offset']+member['stored_bytes']])
        result.append({**member, 'resources':len(block.resources),
            'xmd_count':sum(r['type']=='XMD' for r in block.resources),
            'xtx_count':sum(r['type']=='XTX' for r in block.resources),
            'runtime_selection':'UNRESOLVED; filenames do not qualify active equipment/LOD'})
    return result
