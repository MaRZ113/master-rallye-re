"""Shared conservative source-scene to MR packet/material compiler.

GT adapters supply the same geometry/GS-state contract. Existing GT4 defaults,
resource names and rejection rules are preserved for deterministic regressions.
"""
import hashlib,math,struct,zlib
from dataclasses import replace
from .scene_dx_writer import ScenePart
from .topology_writer import CompiledVertex,DrawGeometry
from .dxt import parse_dxt_bytes
from .addon_sdk.texture_addressing import guarded_clamp
from .addon_sdk.gt4_mr_materials import environment_pairs,qualified_environment_pairs
from .addon_sdk.gt4_materials import alpha_compare
from .addon_sdk.gt4_paint import prepare_paint
from .addon_sdk.gt4_layered import opaque_layered_surfaces
from .addon_sdk.uv_clamp_geometry import refine as refine_clamp

def rotate(v):return (-v[0],v[1],-v[2]) # RH +Y frame, source front -Z -> MR front +Z.

def compile_draws(draws,output,*,environment_reference=None,material_policy=None):
    parts=[];report=[]
    policy=material_policy or {}
    if set(policy)-{'qualified_environment','window_decal_shapes','decal_alpha_ref','paint_surfaces','paint_cutout_min_alpha','binary_cutout_surfaces','layered_opaque_surfaces','source_backfaces','clip_clamp_geometry','strict','max_texture_dim'}:raise ValueError('unsupported material policy')
    cap=policy.get('max_texture_dim')
    if cap is not None and (type(cap) is not int or cap not in (64,128,256,512,1024)):raise ValueError('max_texture_dim must be a power of two 64..1024')
    strict=policy.get('strict',True)
    if type(strict) is not bool:raise ValueError('strict must be boolean')
    def unsupported(no,draw,reason):
        # Non-strict imports keep going: the pass is recorded, not converted.
        if strict:raise ValueError(reason)
        report.append({'packet':no,'shape':draw['source_shape'],'component':draw.get('component','body'),'route':'skipped unsupported source pass (non-strict)','reason':reason,'triangles':len(draw['triangles'])})
    if type(policy.get('clip_clamp_geometry',False)) is not bool:raise ValueError('clip_clamp_geometry must be boolean')
    if type(policy.get('source_backfaces',False)) is not bool:raise ValueError('source_backfaces must be boolean')
    if policy.get('layered_opaque_surfaces'):draws=opaque_layered_surfaces(draws,policy['layered_opaque_surfaces'])
    if type(policy.get('qualified_environment',False)) is not bool:raise ValueError('qualified_environment must be boolean')
    selected=policy.get('window_decal_shapes',[])
    if not isinstance(selected,list) or any(type(i) is not int or i<0 for i in selected) or len(set(selected))!=len(selected):raise ValueError('invalid window decal shape selection')
    if type(policy.get('decal_alpha_ref',32)) is not int or not 0<=policy.get('decal_alpha_ref',32)<128:raise ValueError('invalid source decal alpha threshold')
    binary={};binary_seen=set()
    for item in policy.get('binary_cutout_surfaces',[]):
        if not isinstance(item,dict) or set(item)!={'shape','packets','role'} or type(item['shape']) is not int or item['shape']<0 or not isinstance(item['packets'],list) or not isinstance(item['role'],str) or not item['role']:raise ValueError('binary cutout requires explicit source selection and provenance role')
        for packet in item['packets']:
            if type(packet)is not int or packet<0 or (item['shape'],packet) in binary:raise ValueError('invalid or duplicate binary cutout selector')
            binary[item['shape'],packet]=item['role']
    if policy.get('paint_surfaces') and any(d.get('component','body')=='body'for d in draws):
        if not environment_reference:raise ValueError('paint coverage needs an explicit environment reference')
        draws=prepare_paint(draws,policy['paint_surfaces'],cutout_floor=policy.get('paint_cutout_min_alpha',129))
    pairer=qualified_environment_pairs if policy.get('qualified_environment') else environment_pairs
    reflections,consumed=pairer(draws) if environment_reference else ({},{})
    for no,draw in enumerate(draws):
        if no in consumed or '_mr_paint_consumed' in draw:
            report.append({'packet':no,'shape':draw['source_shape'],'route':'paired into MR environment helper','base_packet':consumed.get(no,draw.get('_mr_paint_consumed'))});continue
        if draw['issues']:
            report.append({'packet':no,'shape':draw['source_shape'],'route':'retained unsupported source effect','issues':draw['issues']});continue
        state=draw['state'];texture=draw['texture'];gif=draw['gif']
        # A GS alpha-only preparation pass cannot contribute visible RGB and
        # does not establish depth. MR has no equivalent destination-alpha
        # buffer operation; retain its provenance without inventing colour.
        if state['fbmask']&0xffffff==0xffffff and not state['depth_write']:
            report.append({'packet':no,'shape':draw['source_shape'],'component':draw.get('component','body'),
                'route':'unsupported alpha-only effect retained in source diagnostics',
                'triangles':len(draw['triangles']),'state':state,
                'reason':'GS masks all RGB writes and disables depth writes; destination-alpha preparation is not a visible MR colour surface.'})
            continue
        if (state['alpha_fail'] or not state['depth_test'] or state['depth_func']!=2 or
                state['variable_scale']!=[1.,1.,1.,1.] or state['variable_offset']!=[0.,0.,0.,0.]):
            unsupported(no,draw,f'unqualified GT4 test/variable-colour translation at packet {no}');continue
        if gif['blend'] and state['blend'][:4]==[0,2,0,1] and not state['depth_write']:
            report.append({'packet':no,'shape':draw['source_shape'],'component':draw.get('component','body'),
                'route':'unsupported additive colour effect retained in source diagnostics',
                'triangles':len(draw['triangles']),'state':state,
                'reason':'GS Cs*As/128+Cd requires additive blending; qualified MR base family uses source-alpha. Never converted to opaque geometry.'})
            continue
        if state['date'] or state['fbmask']&0xffffff or (gif['blend'] and state['blend'][:4]!=[0,1,0,1]):
            unsupported(no,draw,f'unsupported source fragment state at packet {no}, shape {draw["source_shape"]}: {state}');continue
        clamp_geometry=None
        if policy.get('clip_clamp_geometry'):
            partition_uv=False
            if '_mr_uv_vertices'in draw and '_mr_paint_reflection'in draw and '_mr_source_draw'in draw:
                # The exact source-triangle paint proof has already run. With
                # subdivision enabled each partition owns its derived UVs and
                # guard texture; parent vertex IDs no longer address that mesh.
                draw=dict(draw);draw.pop('_mr_uv_vertices');partition_uv=True
            draw,clamp_geometry=refine_clamp(draw)
            if partition_uv:clamp_geometry['partition_uv_ownership']='Independent derived paint partition; source proof precedes subdivision; no parent vertex indexing'
        vertices=draw['vertices'];indices=draw['triangles'];used=sorted({i for t in indices for i in t});remap={k:i for i,k in enumerate(used)}
        if state['alpha_test'] and not gif['blend'] and any((vertices[k]['rgba_ps2'] or [128]*4)[3]!=128 for k in used):
            unsupported(no,draw,'alpha-tested vertex-alpha modulation requires separate coverage qualification');continue
        reflection=draw.get('_mr_paint_reflection',reflections.get(no));alpha=bool(gif['blend']);test=bool(state['alpha_test'] and not alpha)
        binary_cutout=draw.get('component','body')=='body' and (draw['source_shape'],draw.get('packet',no)) in binary
        if binary_cutout:
            if not alpha or not state['depth_write'] or state['alpha_test'] or reflection or not texture or texture['registers']['tfx']!=0 or not texture['registers']['tcc']:raise ValueError('binary cutout selector is not a qualified depth-writing source-alpha surface')
            if set(texture['rgba_ps2'][3::4])!={0,128} or any((vertices[k]['rgba_ps2'] or [128]*4)[3]!=128 for k in used):raise ValueError('binary cutout requires source alpha exactly zero/unity and unity vertex alpha')
            alpha=False;test=True;binary_seen.add((draw['source_shape'],draw.get('packet',no)))
        if reflection:alpha=test=False # Every source texel is proven covered.
        if reflection and reflection.get('coverage') in ('exact_GREATER128_cutout','paint_cutout_floor'):test=True
        decal=draw.get('component','body')=='body' and draw['source_shape'] in policy.get('window_decal_shapes',[])
        if decal:
            if not alpha or state['depth_write'] or reflection or not texture:raise ValueError('window decal is not the qualified no-Z-write source overlay')
            alpha=False;test=True
        stem='untextured-tga';uvs=[tuple(vertices[k]['uv']) if vertices[k]['uv'] else (0.,0.) for k in used];sampler=None
        if texture:
            reg=texture['registers']
            if reg['tfx']!=0:
                unsupported(no,draw,'unqualified MR texture function');continue
            raw=bytearray(texture['rgba_ps2']);source_alpha=raw[3::4]
            for i,a in enumerate(source_alpha):
                effective=a if reg['tcc'] else 128
                passed=not state['alpha_test'] or alpha_compare(effective,state['alpha_func'],state['alpha_ref'])
                if binary_cutout:passed=effective==128
                raw[4*i+3]=min(255,effective*255//128) if (alpha or reflection) and passed else (255 if passed else 0)
                if reflection and 'date' in reflection and reflection['date'] and int(effective>=128)!=reflection['datm']:raw[4*i+3]=0
                if reflection and reflection.get('alpha_floor') and passed:raw[4*i+3]=max(raw[4*i+3],reflection['alpha_floor'])
                if decal:raw[4*i+3]=255 if passed and effective>policy.get('decal_alpha_ref',32) else 0
            if '_mr_uv_vertices' in draw:
                parent=draw['_mr_uv_vertices'];parent_uvs=[tuple(vertices[k]['uv']) for k in parent]
                width,height,raw,parent_uvs,sampler=guarded_clamp(texture['width'],texture['height'],bytes(raw),reg,parent_uvs)
                mapped=dict(zip(parent,parent_uvs));uvs=[mapped[k] for k in used]
            else:width,height,raw,uvs,sampler=guarded_clamp(texture['width'],texture['height'],bytes(raw),reg,uvs,compact=bool(policy.get('clip_clamp_geometry')))
            if cap and max(width,height)>cap:
                # MR-native budget: box-reduce oversized atlases. UVs are
                # normalized, so geometry is untouched; source is unchanged.
                from PIL import Image
                factor=max(width,height)/cap;nw,nh=max(1,round(width/factor)),max(1,round(height/factor))
                img=Image.frombytes('RGBA',(width,height),bytes(raw)).resize((nw,nh),Image.BOX)
                raw=img.tobytes();width,height=nw,nh
                if sampler is not None:sampler={**sampler,'mr_budget_downscale':[nw,nh]}
            raw=bytearray(raw)
            # Preserve RGB and row order; texture alpha maps PS2 unity128.
            for i in range(0,len(raw),4):raw[i],raw[i+2]=raw[i+2],raw[i]
            key=hashlib.sha256(bytes(raw)+struct.pack('<II',width,height)).hexdigest()[:20];stem='gt4-'+key+'-tga'
            data=struct.pack('<5I',0xfeed,1,zlib.crc32(raw)&0xffffffff,width,height)+raw
            path=output/(stem+'.dxt')
            if path.exists() and path.read_bytes()!=data:raise ValueError('texture hash collision')
            path.write_bytes(data);parse_dxt_bytes(data)
        else:
            raw=bytes((255,255,255,255));(output/(stem+'.dxt')).write_bytes(struct.pack('<5I',0xfeed,1,zlib.crc32(raw),1,1)+raw)
        # GT4 often enables an alpha test even for a wholly covered image.
        # MR damage treats vertex alpha as reflection weight. Keep a redundant
        # source test from turning that weight into body coverage after impact.
        opaque_coverage=all(a==255 for a in raw[3::4]) and all((vertices[k]['rgba_ps2'] or [128]*4)[3]==128 for k in used)
        if test and opaque_coverage:test=False
        if alpha and opaque_coverage and state['depth_write']:alpha=False
        compiled=[];missing_normals=0
        normals={}
        for tri in indices:
            a,b,c=[vertices[i]['position'] for i in tri];u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)];n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);length=math.sqrt(sum(t*t for t in n))
            if length>1e-12:
                for i in tri:normals.setdefault(i,tuple(t/length for t in n))
        for k,uv in zip(used,uvs):
            v=vertices[k];normal=v['normal']
            if normal is None:normal=normals.get(k,(0.,1.,0.));missing_normals+=1
            colour=v['rgba_ps2'] or (128,128,128,128)
            # D3DCOLOR memory order BGRA; source RGB neutral128 -> MR255.
            r,g,b,a=(min(255,int(c)*255//128) for c in colour)
            compiled.append(CompiledVertex(rotate(v['position']),rotate(normal),bytes((b,g,r,a)),(uv,)))
        helper='Null'
        if reflection:
            ref=parse_dxt_bytes(environment_reference);raw=bytearray(ref.bgra);gain=reflection['gain_rgb']
            for i in range(0,len(raw),4):
                for k in range(3):raw[i+k]=min(255,round(raw[i+k]*gain[2-k]))
                raw[i+3]=255
            helper='gt4-env-'+hashlib.sha256(bytes(raw)).hexdigest()[:20]+'-tga'
            (output/(helper+'.dxt')).write_bytes(struct.pack('<5I',0xfeed,1,zlib.crc32(raw)&0xffffffff,ref.width,ref.height)+raw)
        triangles=tuple(tuple(remap[k] for k in tri) for tri in indices)
        backfaces=policy.get('source_backfaces') and not state['cull']
        if backfaces:
            # MR has global culling. Honor source cull-disable with explicit
            # reverse faces and independent normals, not a global render hook.
            def cyclic(t):
                positions=tuple(compiled[i].position for i in t)
                return min(positions,positions[1:]+positions[:1],positions[2:]+positions[:2])
            present={cyclic(t) for t in triangles};missing=[t for t in triangles if cyclic(tuple(reversed(t))) not in present]
            count=len(compiled);used_back=sorted({i for t in missing for i in t});reverse_ids={i:count+n for n,i in enumerate(used_back)}
            compiled.extend(replace(compiled[i],normal=tuple(-n for n in compiled[i].normal)) for i in used_back)
            triangles+=tuple(tuple(reverse_ids[i] for i in reversed(t)) for t in missing)
        parts.append(ScenePart(DrawGeometry(tuple(compiled),triangles),(stem,helper,'Null'),alpha or test,test,bool(reflection)))
        report.append({'packet':no,'shape':draw['source_shape'],'route':'MR source-alpha' if alpha else 'MR cutout' if test else 'MR opaque',
            'source_packet':draw.get('packet',no),'command_offset':draw.get('command_offset'),
            'triangles':len(indices),'texture':stem,'generated_normals':missing_normals,'component':draw.get('component','body'),'sampler':sampler,
            'pose_fallback':draw.get('pose_fallback'),
            **({'qualified_tween_callbacks':draw['qualified_tween_callbacks']} if draw.get('qualified_tween_callbacks') else {}),
            'environment':reflection,
            'depth_safe_window_decal':decal,
            'source_cull_backfaces':bool(backfaces),
            **({'clamp_geometry':clamp_geometry} if clamp_geometry is not None else {}),
            **({'visibility_keepout':draw['_mr_visibility_keepout']} if '_mr_visibility_keepout' in draw else {}),
            **({'source_housing':draw['_mr_source_housing']} if '_mr_source_housing' in draw else {}),
            **({'binary_cutout_approximation':{'role':binary[draw['source_shape'],draw.get('packet',no)],'boundary':'Explicit diagnostic fallback: binary source blend becomes MR cutout; filtered edges quantized, source RGB/UV/geometry unchanged.'}} if binary_cutout else {}),
            'coverage_proven_opaque':opaque_coverage,
            'fallbacks':['unadmitted DATE/generated-environment effects remain separate source records','GS destination-alpha preserve is not reproduced by MR base pass',
                         'MR alpha threshold normalized for source coverage; RGB unchanged','MR wrap sampler; source clamped axes baked into edge-extended guard texture']})
    if binary_seen!=set(binary):raise ValueError('binary cutout selector absent from selected source model/LOD')
    if not parts:raise ValueError('no qualified MR scene parts')
    return parts,report

