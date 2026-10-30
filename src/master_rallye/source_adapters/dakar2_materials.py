"""Bounded NV2A combiner inspection for the qualified Dakar2 Xbox build.

This is an independently written data decoder, not Xbox GPU emulation. Shader
input V0 is a vertex-program output, never silently the original color stream.
Unqualified coordinates/constants cannot become a native diffuse-only approval.
"""
from __future__ import annotations
import math
import struct
from .. import universal_vehicle_scene as u
from .dakar2 import PINS
from .dakar2_fidelity import executable_evidence
from .dakar2_disc import FileReader, xdvdfs

SCHEMA = 'dakar2-material-qualification/1'
REGISTERS = {0:'zero',1:'c0',2:'c1',3:'fog',4:'v0',5:'v1',
             8:'t0',9:'t1',10:'t2',11:'t3',12:'r0',13:'r1',14:'sum',15:'ef'}
MODES = {0:'NONE',1:'PROJECT2D',2:'PROJECT3D',3:'CUBEMAP',4:'PASSTHRU',
         5:'CLIPPLANE',6:'BUMPENVMAP',7:'BUMPENVMAP_LUM',8:'BRDF',9:'DOT_ST',
         10:'DOT_ZW',11:'DOT_RFLCT_DIFF',12:'DOT_RFLCT_SPEC',13:'DOT_STR_3D',
         14:'DOT_STR_CUBE',15:'DEPENDENT_AR',16:'DEPENDENT_GB',17:'DOTPRODUCT',
         18:'DOT_RFLCT_SPEC_CONST'}


def _input(value):
    register=value&15
    if register not in REGISTERS:raise ValueError('Reserved combiner input register')
    return {'register':REGISTERS[register], 'alpha':bool(value&16), 'mapping':value>>5}


def _inputs(word):
    return [_input((word>>shift)&255) for shift in (24,16,8,0)]


def _outputs(word):
    if word&~0xfffff:raise ValueError('Reserved combiner output bits')
    destinations=[(word>>shift)&15 for shift in (4,0,8)]
    if any(value not in (0,4,5,8,9,10,11,12,13)for value in destinations):
        raise ValueError('Reserved combiner output register')
    return {'ab':REGISTERS[destinations[0]],'cd':REGISTERS[destinations[1]],
            'sum':REGISTERS[destinations[2]],'flags':word>>12}


def decode_pixel_definition(words):
    """Decode the 60 DWORD Xbox record; preserve every input/output and map.

    Layout is independently corroborated by original e6250 upload loops: words
    0..7 -> NV097 0x260, 10..41 ->0xa60,42 ->0x17f8,45..53 ->0x1e40.
    No raw shader payload is installed, distributed or translated implicitly.
    """
    if not isinstance(words,(list,tuple))or len(words)!=60 or any(type(x)is not int or not 0<=x<=0xffffffff for x in words):
        raise ValueError('Pixel definition requires exactly 60 uint32 words')
    count=words[53]&15
    if not 1<=count<=8 or words[53]&~0x1110f:raise ValueError('Combiner count/flags unsupported')
    if words[54]&~0xfffff:raise ValueError('Reserved texture-mode bits')
    modes=[(words[54]>>(5*i))&31 for i in range(4)]
    if any(x not in MODES for x in modes):raise ValueError('Reserved texture mode')
    stages=[]
    for i in range(count):
        stages.append({'stage':i,'rgb_inputs':_inputs(words[34+i]),'alpha_inputs':_inputs(words[i]),
                       'rgb_outputs':_outputs(words[45+i]),'alpha_outputs':_outputs(words[26+i]),
                       'constant0_argb':words[10+i],'constant1_argb':words[18+i],
                       'constant0_runtime_index':None if (words[57]>>(4*i))&15==15 else (words[57]>>(4*i))&15,
                       'constant1_runtime_index':None if (words[58]>>(4*i))&15==15 else (words[58]>>(4*i))&15})
    final_enabled=bool(words[8]or words[9])
    return {'schema':'nv2a-pixel-definition-inspection/1',
            'sha256':u.sha(struct.pack('<60I',*words)), 'combiner_count':count,
            'combiner_flags':words[53]>>8,'texture_modes':[MODES[x] for x in modes],
            'stages':stages,'final_combiner_enabled':final_enabled,
            'final_inputs_abcd':_inputs(words[8]), 'final_inputs_efg':_inputs(words[9])[:3],
            'final_settings':words[9]&255,'final_constants_argb':list(words[43:45]),
            'final_constant_mapping':words[59], 'compare_mode':words[42],
            'dot_mapping':words[55], 'input_texture':words[56]}


def _rgba(values,label):
    if not isinstance(values,(list,tuple))or len(values)!=4 or any(type(x)not in(int,float)or not math.isfinite(x)or not 0<=x<=1 for x in values):
        raise ValueError('Finite normalized RGBA required: '+label)
    return list(values)


def _constant(argb):
    return [(argb>>16&255)/255,(argb>>8&255)/255,(argb&255)/255,(argb>>24&255)/255]


def evaluate_pixel_definition(decoded, textures, shader_v0, *, runtime_constants=None):
    """Evaluate only qualified multiply/sum channels with explicit shader inputs.

    This isolates arithmetic in source-free tests. It does not derive texture
    coordinates, lighting V0, filtering, precision or runtime alpha-test state.
    Runtime-mapped constants are REQUIRED, never replaced by embedded defaults.
    """
    if decoded.get('schema')!='nv2a-pixel-definition-inspection/1' or decoded['final_combiner_enabled']:
        raise ValueError('Unsupported final combiner; no implicit approximation')
    if any(mode not in('NONE','PROJECT2D')for mode in decoded['texture_modes']):
        raise ValueError('Unsupported texture operation')
    registers={'zero':[0.]*4,'v0':_rgba(shader_v0,'vertex-program output V0'),
               'r0':[0.]*4,'r1':[0.]*4}
    for stage,mode in enumerate(decoded['texture_modes']):
        if mode!='NONE':
            key='t'+str(stage)
            if key not in textures:raise ValueError('Missing active texture input '+key)
            registers[key]=_rgba(textures[key],key)
    constants={}if runtime_constants is None else runtime_constants
    for stage in decoded['stages']:
        for name,index in [('c0',0),('c1',1)]:
            runtime_index=stage['constant'+str(index)+'_runtime_index']
            if runtime_index is None:registers[name]=_constant(stage['constant'+str(index)+'_argb'])
            elif runtime_index not in constants:raise ValueError('Unqualified runtime pixel constant '+str(runtime_index))
            else:registers[name]=_rgba(constants[runtime_index],'runtime constant')
        before={name:list(value)for name,value in registers.items()};writes=[]
        for alpha in(False,True):
            prefix='alpha'if alpha else'rgb';out=stage[prefix+'_outputs'];flags=out['flags']
            if flags:raise ValueError('Unsupported dot/mux/bias/scale combiner output')
            components=(3,)if alpha else(0,1,2)
            def value(spec,component):
                source=before.get(spec['register'])
                if source is None:raise ValueError('Unqualified shader register '+spec['register'])
                x=source[3 if spec['alpha']else(2 if alpha else component)]
                mapping=spec['mapping']
                return (max(0,x),1-max(0,x),2*max(0,x)-1,1-2*max(0,x),
                        max(0,x)-.5,.5-max(0,x),x,-x)[mapping]
            for component in components:
                a,b,c,d=[value(spec,component)for spec in stage[prefix+'_inputs']]
                for name,result in [('ab',a*b),('cd',c*d),('sum',a*b+c*d)]:
                    target=out[name]
                    if target!='zero':writes.append((target,component,max(-1.,min(1.,result))))
        # Both RGB and alpha read the previous stage, including overwritten Tn.
        for target,component,value in writes:
            registers.setdefault(target,[0.]*4)[component]=value
    return [max(0.,min(1.,x))for x in registers['r0']]


def native_evidence(image):
    """Extend existing qualified extraction with original consumer byte evidence."""
    image=__import__('pathlib').Path(image);evidence=executable_evidence(image)
    reader=FileReader(image);row=next(r for r in xdvdfs(reader,0x18300000)if r['path'].lower()=='default.xbe')
    data=reader.read(row['offset'],row['bytes'])
    if u.sha(data)!=PINS['default.xbe']:raise ValueError('Unqualified original executable')
    base=struct.unpack_from('<I',data,0x104)[0];count,table=struct.unpack_from('<II',data,0x11c)
    sections=[struct.unpack_from('<5I',data,table-base+i*56)for i in range(count)]
    functions={}
    for name,va,size in [('pixel_upload',0xe6250,0x200),('shader_dispatch',0x8b360,0x140),
                         ('texture_bind',0x8aed0,0x190),('draw_bindings',0x8b590,0x140)]:
        matches=[r for r in sections if r[1]<=va and va+size<=r[1]+r[4]]
        if len(matches)!=1:raise ValueError('Ambiguous native section mapping')
        section=matches[0];offset=section[3]+va-section[1];raw=data[offset:offset+size]
        functions[name]={'va':va,'file_offset':offset,'bytes':size,'sha256':u.sha(raw)}
    evidence['material_consumer_bytes']=functions
    evidence['decoded_pixel_definitions']={key:decode_pixel_definition(value['pixel_definition_words'])for key,value in evidence['declarations'].items()}
    return evidence


def qualify_scene(scene,evidence):
    """Per-original-draw native boundary; unresolved inputs fail closed."""
    if scene['metadata'].get('adapter')!='dakar2-xbox-source/1'or evidence.get('xbe_sha256')!=PINS['default.xbe']:
        raise ValueError('Qualified Dakar2 scene and original XBE required')
    if scene['source']['catalog']not in('PAJERO_HI_0_0.LOD','NISSAN_HI_0_0.LOD','HINO_HI_0_0.LOD'):
        raise ValueError('Qualified three-vehicle material corpus required')
    textures={t['id']:t for t in scene['textures']};materials={m['id']:m for m in scene['materials']}
    owners={mid:n for n in scene['nodes']for mid in n['mesh_ids']};rows=[]
    for mesh in scene['meshes']:
        mat=materials[mesh['material_id']];raw=mat['raw_fields'][0];node=owners[mesh['id']]
        key=str(raw['declaration']);declaration=evidence['declarations'].get(key)
        if declaration is None:raise ValueError('Unknown source shader declaration')
        decoded=decode_pixel_definition(declaration['pixel_definition_words'])
        if mat['source_render_state']['pixel_definition_sha256']!=decoded['sha256']:
            raise ValueError('Source material shader provenance mismatch')
        bindings=list(raw['texture_bindings'])
        ids=raw.get('native_four_texture_resource_ids')
        if not isinstance(ids,list)or len(ids)!=4:raise ValueError('Four original texture fields required')
        bindings+=[None]*(4-len(bindings))
        if len(bindings)!=4:raise ValueError('Texture binding budget')
        for slot,resource in enumerate(ids):
            expected=None if resource is None else 'xtx-'+str(resource).zfill(3)
            if bindings[slot]!=expected:raise ValueError('Texture stage identity mismatch')
        stages=[]
        for slot,mode in enumerate(decoded['texture_modes']):
            binding=bindings[slot]
            if mode!='NONE'and(binding is None or binding not in textures):raise ValueError('Missing active source texture stage')
            texture=textures.get(binding)
            stages.append({'stage':slot,'mode':mode,'texture_id':binding,
                           'source_resource_id':ids[slot],
                           'rgba_sha256':None if texture is None else texture['rgba_sha256'],
                           'coordinate_selection':'UNKNOWN vertex-program output T'+str(slot),
                           'native_disposition':'BLOCKED required composite'if mode!='NONE'else'UNUSED_BY_THIS_PIXEL_DEFINITION'})
        stream=mesh['source'].get('streams',{});uv1=stream.get('10');uv0=stream.get('9')
        alias=uv1 is not None and uv0 is not None and uv1['stride']==uv0['stride']==8 and uv1['sha256']==uv0['sha256']
        rows.append({'mesh_id':mesh['id'],'material_id':mat['id'],'source_node':node['name'],
                     'triangles':len(mesh['triangles']),'source_offset':raw['source_offset'],
                     'source_member_sha256':mesh['source']['member_sha256'],
                     'declaration':raw['declaration'],'pixel_definition_sha256':decoded['sha256'],
                     'vertex_program_va':declaration['vertex_program_va'],'texture_stages':stages,
                     'uv1_present':uv1 is not None,'uv1_exact_uv0_alias':alias,
                     'blend':mat['source_render_state']['blend'],'depth_write':mat['source_render_state']['depth_write'],
                     'alpha_test':mat['source_render_state']['alpha_test'],'cull':mat['source_render_state']['cull'],
                     'draw_pass':node['render_pass'],'draw_order':node['source_transform_record']['id'],
                     'material_role':'UNKNOWN; source node label retained without automatic paint/glass/lamp inference',
                     'pointwise_rule':('RGB=T0.rgb*V0.rgb; A=T0.a*V0.a'if decoded['combiner_count']==1 else
                                       'RGB=clamp(T0.rgb*V0.rgb+T1.a*clamp(T2.rgb*C0_stage1.a)); A=T0.a'),
                     'native_status':'BLOCKED','discarded_effects':[],
                     'blockers':['vertex-program V0 lighting and T0/T1/T2 coordinate selection not yet qualified',
                                 'runtime alpha-test activation and exact glass/lamp/opaque face ownership not qualified']+
                                ([]if decoded['combiner_count']==1 else['runtime-mapped C0(stage1).a has no qualified per-draw value; additive stages cannot be omitted'])})
    return {'schema':SCHEMA,'source_catalog':scene['source']['catalog'],'source_mutated':False,
            'native_material_readiness':'BLOCKED','L2':'WARN','L4':'NOT TESTED',
            'draws':rows,'draw_count':len(rows),'triangles':sum(r['triangles']for r in rows),
            'uv1_present':sum(r['uv1_present']for r in rows),'uv1_exact_aliases':sum(r['uv1_exact_uv0_alias']for r in rows),
            'native_fixture_allowed':False,'source_feature_policy':{},
            'policy_boundary':'No omit_for_mr approvals emitted for required secondary stages; no automatic L2-to-L3 promotion'}


def native_requirements(scene,evidence):
    """Typed required-effect rows for a common bridge gate; never omission consent."""
    report=qualify_scene(scene,evidence)
    return [{'material_id':row['material_id'],'source_shader_sha256':row['pixel_definition_sha256'],
             'required_texture_stages':[stage['stage']for stage in row['texture_stages']if stage['mode']!='NONE'],
             'source_uv_data_alias_is_shader_equivalence':False,
             'native_disposition':'BLOCKED','allow_omit_for_mr':False,'evidence':row['pointwise_rule'],
             'blockers':list(row['blockers'])}for row in report['draws']]
