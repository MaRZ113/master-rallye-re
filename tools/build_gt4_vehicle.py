"""Build private MR inspection resources from a user-supplied qualified GT4 profile.

No GT assets are bundled, no source files modified, no runtime/CarID changes.
The packet writer is shared with other scene sources; all source selection is
explicit profile data. Unsupported source effects remain in the build report.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct,sys,zlib
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.addon_sdk.gt4_assembly import assemble
from master_rallye.addon_sdk.gt4_materials import alpha_compare
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.addon_sdk.texture_addressing import guarded_clamp
from master_rallye.addon_sdk.gt4_mr_materials import environment_pairs,qualified_environment_pairs
from master_rallye.addon_sdk.texture_budget import texture_working_set,require_vehicle_budget
from master_rallye.addon_sdk.wheel_orientation import orient_parts,instance_angle
from master_rallye.addon_sdk.gt4_brakes import source_states,source_key,native_surfaces
from master_rallye.addon_sdk.native_brakes import write_brake_scene
from master_rallye.addon_sdk.gt4_paint import prepare_paint
from master_rallye.addon_sdk.crew import fit_crew
from master_rallye.addon_sdk.visibility_keepout import apply_keepouts,append_source_housings

def rotate(v):return (-v[0],v[1],-v[2]) # RH +Y frame, source front -Z -> MR front +Z.

def compile_draws(draws,output,*,environment_reference=None,material_policy=None):
    parts=[];report=[]
    policy=material_policy or {}
    if set(policy)-{'qualified_environment','window_decal_shapes','decal_alpha_ref','paint_surfaces','paint_cutout_min_alpha','binary_cutout_surfaces'}:raise ValueError('unsupported material policy')
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
    if policy.get('paint_surfaces'):
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
            raise ValueError(f'unqualified GT4 test/variable-colour translation at packet {no}')
        if gif['blend'] and state['blend'][:4]==[0,2,0,1] and not state['depth_write']:
            report.append({'packet':no,'shape':draw['source_shape'],'component':draw.get('component','body'),
                'route':'unsupported additive colour effect retained in source diagnostics',
                'triangles':len(draw['triangles']),'state':state,
                'reason':'GS Cs*As/128+Cd requires additive blending; qualified MR base family uses source-alpha. Never converted to opaque geometry.'})
            continue
        if state['date'] or state['fbmask']&0xffffff or (gif['blend'] and state['blend'][:4]!=[0,1,0,1]):raise ValueError(f'unsupported source fragment state at packet {no}, shape {draw["source_shape"]}: {state}')
        vertices=draw['vertices'];indices=draw['triangles'];used=sorted({i for t in indices for i in t});remap={k:i for i,k in enumerate(used)}
        if state['alpha_test'] and not gif['blend'] and any((vertices[k]['rgba_ps2'] or [128]*4)[3]!=128 for k in used):
            raise ValueError('alpha-tested vertex-alpha modulation requires separate coverage qualification')
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
            if reg['tfx']!=0:raise ValueError('unqualified MR texture function')
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
            else:width,height,raw,uvs,sampler=guarded_clamp(texture['width'],texture['height'],bytes(raw),reg,uvs)
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
        parts.append(ScenePart(DrawGeometry(tuple(compiled),tuple(tuple(remap[k] for k in tri) for tri in indices)),(stem,helper,'Null'),alpha or test,test,bool(reflection)))
        report.append({'packet':no,'shape':draw['source_shape'],'route':'MR source-alpha' if alpha else 'MR cutout' if test else 'MR opaque',
            'source_packet':draw.get('packet',no),'command_offset':draw.get('command_offset'),
            'triangles':len(indices),'texture':stem,'generated_normals':missing_normals,'component':draw.get('component','body'),'sampler':sampler,
            'pose_fallback':draw.get('pose_fallback'),
            **({'qualified_tween_callbacks':draw['qualified_tween_callbacks']} if draw.get('qualified_tween_callbacks') else {}),
            'environment':reflection,
            'depth_safe_window_decal':decal,
            **({'visibility_keepout':draw['_mr_visibility_keepout']} if '_mr_visibility_keepout' in draw else {}),
            **({'source_housing':draw['_mr_source_housing']} if '_mr_source_housing' in draw else {}),
            **({'binary_cutout_approximation':{'role':binary[draw['source_shape'],draw.get('packet',no)],'boundary':'Explicit diagnostic fallback: binary source blend becomes MR cutout; filtered edges quantized, source RGB/UV/geometry unchanged.'}} if binary_cutout else {}),
            'coverage_proven_opaque':opaque_coverage,
            'fallbacks':['unadmitted DATE/generated-environment effects remain separate source records','GS destination-alpha preserve is not reproduced by MR base pass',
                         'MR alpha threshold normalized for source coverage; RGB unchanged','MR wrap sampler; source clamped axes baked into edge-extended guard texture']})
    if binary_seen!=set(binary):raise ValueError('binary cutout selector absent from selected source model/LOD')
    if not parts:raise ValueError('no qualified MR scene parts')
    return parts,report

def build_model(name,draws,template,assets,*,environment=None,policy=None,brake_source=None,profile=None,stock_glow=None,crew_root=None):
    brakes=None
    if name!='wheel.dx' and profile:
        variant='race' if name=='car.dx' else 'menu';geometry=profile.get('geometry_policy',{}).get(variant,{})
        if set(geometry)-{'visibility_keepouts','source_housings'}:raise ValueError('unsupported geometry policy')
        if geometry.get('visibility_keepouts'):
            draws,_=apply_keepouts(draws,geometry['visibility_keepouts'],profile['body_race_sha256' if variant=='race' else 'body_menu_sha256'])
        if geometry.get('source_housings'):
            draws,_=append_source_housings(draws,geometry['source_housings'],profile['body_race_sha256' if variant=='race' else 'body_menu_sha256'])
    crew,crew_records=fit_crew(crew_root,profile['crew'],'race' if name=='car.dx' else 'menu',assets) if name!='wheel.dx' and profile and profile.get('crew') and crew_root else ([],[])
    if name!='wheel.dx' and profile and profile.get('crew') and crew_root is None:raise ValueError('crew source root is required')
    if name=='car.dx' and profile and profile.get('native_brakes'):
        off,on,provenance=source_states(brake_source,profile);keys={source_key(d) for d in off}
        body=[d for d in draws if source_key(d) not in keys or d.get('component','body')!='body']
        parts,record=compile_draws(body,assets,environment_reference=environment,material_policy=policy)
        unlit,off_records=compile_draws(off,assets,environment_reference=environment,material_policy={k:v for k,v in (policy or {}).items() if not k.startswith('paint_')})
        source_on,on_records=compile_draws(on,assets)
        # Preserve opaque/cutout source cores and generate the halo only from
        # the actual blended source lens, never its shared off-state atlas.
        opaque_on=[replace(p,diffuse=False) for p in source_on if not p.alpha or p.alpha_test]
        alpha_on=[p for p in source_on if p.alpha and not p.alpha_test]
        lit,glow,lamps=native_surfaces(alpha_on,assets,stock_glow,
            alpha_ref=profile['native_brakes'].get('alpha_ref',32),offset=profile['native_brakes'].get('halo_offset',.001),halo_max_edge=profile['native_brakes'].get('halo_max_edge'))
        data=write_brake_scene(template,parts+crew,unlit,opaque_on+lit,glow)
        brakes={**provenance,**lamps,'off_conversion':off_records,'on_conversion':on_records}
    else:
        parts,record=compile_draws(draws,assets,environment_reference=environment,material_policy=policy)
        if name=='wheel.dx':parts=orient_parts(parts,source_outward_x=1)
        data=write_scene_dx(template,parts+crew)
    return data,record+crew_records,brakes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--crew-source',type=Path,help='optional independent user-supplied stock crew family');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('output exists')
    profile=json.loads(a.profile.read_text());code=profile['model_code'];menu=(a.source_root/'car/menu'/code).read_bytes();race=(a.source_root/'car/lod'/code).read_bytes();spec=a.source_root/'specdb'/profile['spec_folder']
    frontend=assemble(menu,menu,spec,profile);racing=assemble(race,menu,spec,profile,race=True)
    a.output.mkdir(parents=True);assets=a.output/'assets';assets.mkdir();report={'status':'OFFLINE_GT4_MR_CANDIDATE_NOT_RUNTIME_QUALIFIED','profile':profile,'source_reports':{'menu':frontend['report'],'race':racing['report']},'outputs':{},'conversion':{}}
    # MR assembles race wheels independently. Baking the presentation wheels
    # into car.dx would produce a duplicate set once the game attaches wheel.dx.
    race_body=[d for d in racing['draws'] if d.get('component') not in ('rim','tyre')]
    environment=None
    if reference:=profile.get('mr_environment_reference'):
        if Path(reference).name!=reference:raise ValueError('environment reference must be a local donor DXT basename')
        environment=(a.donor/reference).read_bytes();parse_dxt_bytes(environment)
        report['environment_reference']={'file':reference,'sha256':hashlib.sha256(environment).hexdigest(),'policy':'explicit MR helper approximation; only proven GS pairs admitted'}
    for name,scene,draws in [('complete.dx',frontend,frontend['draws']),('car.dx',racing,race_body),('wheel.dx',frontend,frontend['wheel_template'])]:
        policy=profile.get('material_policy',{}).get('race' if name=='car.dx' else 'menu',{}) if name!='wheel.dx' else None
        template=(a.donor/name).read_bytes()
        data,record,brakes=build_model(name,draws,template,assets,environment=environment,policy=policy,brake_source=race,profile=profile,
            stock_glow=(a.donor/'breaklightsonglow-tga.dxt').read_bytes() if profile.get('native_brakes') else None,crew_root=a.crew_source or a.donor)
        if brakes:report['native_brakes']=brakes
        (assets/name).write_bytes(data);model=parse_dx_bytes(data)
        report['outputs'][name]={'sha256':hashlib.sha256(data).hexdigest(),'vertices':model.vertex_count,'triangles':model.triangle_count,'draws':len(model.physical_draws),'validated':model.diagnostics.validated,'template_sha256':hashlib.sha256(template).hexdigest()}
        report['conversion'][name]=record
    report['texture_budget']=require_vehicle_budget(texture_working_set(assets))
    (a.output/'texture-budget.json').write_text(json.dumps(report['texture_budget'],indent=2)+'\n')
    instances=[{'translation':list(rotate(w['hub'])),'rotation_y':instance_angle(-w['side']),
                'scale':[1.,1.,1.]} for w in frontend['report']['rig']['wheels']]
    (a.output/'preview-profile.json').write_text(json.dumps({'race_wheel_instances':instances,
        'provenance':'GT4 original DBT/IDI and traced normal-four wheel constructor rest pose; no MR physics or runtime wheel positions changed'},indent=2)+'\n')
    (assets/'preview-profile.json').write_bytes((a.output/'preview-profile.json').read_bytes())
    report['wheel_orientation']={'source_template_outward_x':1,'mr_template_outward_x':-1,
        'conversion':'proper 180 degree Y rotation, determinant +1; normals follow positions; indices/UVs unchanged',
        'placements':'source and MR physics hubs unchanged; preview instance angles compensate the local basis only'}
    report['limitations']=['GT4 generated reflections/DATE use a source-qualified MR helper approximation, not PS2 renderer parity',
        'source dynamic camber/provider pose remains unresolved; source-supported static hub formula used',
        ('source tail-lamp branches use native blight; original controller CPU-qualified, gameplay confirmation pending' if profile.get('native_brakes') else 'source tail-lamp branches are decoded; selected source day branch retained'),
        'selected no-Z-write window decals use a depth-safe cutout; soft alpha edges quantized, underlying glass remains blended',
        'coverage and environment alpha share one MR channel; cutout reflective regions retain coverage after damage, with approximate reflection fading',
        'baseline donor collision retained explicitly; no physics tuning','no install/CarID allocation attempted; body materials require human MR testing','offline package is private loose research output; do not distribute GT assets']
    (a.output/'conversion-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['outputs'],indent=2))

if __name__=='__main__':main()
