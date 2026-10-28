"""Profile-driven private GT3 build using the shared MR compiler.

Profiles may be hand-written or produced by `gt_auto_profile.derive`.
Only the geometric core is required; lighting/material policy, identity,
limitations and donor pins default sensibly (pins are computed from the donor
when omitted). `mode`:

* ``standard`` - MR-native: donor MR tyres (textures and UVs), stock seated
  crew, automatic breakable glass and brake glow (native blight/screen states);
* ``full`` - every decoded source pass and GT tyre imagery, no MR additions.

Wheel envelope/assembly are authoring approximations, not recovered GT3 wheel
transforms. No runtime registration or physics edits occur.
"""
import hashlib,json,struct,zlib
from pathlib import Path
from .gt3_source import inspect_car,read_source
from .gt3_colourways import catalog,select
from .addon_sdk.gt3_scene import reconstruct,GT3_CORE_SHA256
from .addon_sdk.gt3_mr import prepare
from .addon_sdk.gt3_assembly import fit_rim,stock_tyres,place,scale_parts
from .addon_sdk.gt4_textures import TextureSet,display_rgba
from .addon_sdk.wheel_orientation import orient_parts,instance_angle
from .addon_sdk.texture_budget import texture_working_set,require_vehicle_budget
from .source_scene_compile import compile_draws
from .scene_dx_writer import write_scene_dx
from .dx import parse_dx_bytes

REQUIRED={'version','source_sha256','selections','wheel','tyre','assembly'}
OPTIONAL={'engine_sha256','model_key','source_identity','lighting_policy','material_policy','references','limitations','mode','crew','features'}
DEFAULT_LIGHTING={'lighting_fallback':'native_mr_lighting','evidence':'MR fixed-function lighting replaces GT3 VU lighting.'}

def digest(raw):return hashlib.sha256(raw).hexdigest()
def json_write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def _read_source(source):
    return read_source(source)


def _crew(donor,body,mode):
    """Stock MR seated pair placed in the GT cabin (standard mode only)."""
    from .addon_sdk.crew import fit_crew
    preset=json.loads((Path(__file__).parent/'addon_sdk/presets/navara_crew.json').read_text())
    if digest((Path(donor)/'car.dx').read_bytes())!=preset['source_sha256']:return [],[],'donor has no qualified crew preset'
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        parts,_=fit_crew(Path(donor),preset,'race',Path(td))
    points=[v.position for p in parts for v in p.geometry.vertices]
    roof_z,roof_y=_roof(body)
    # Helmet top (highest crew point) goes 8 cm under the roof skin, centred
    # under the roof panel; antennas/wings are excluded by _roof.
    top=max(points,key=lambda p:p[1])
    dy=roof_y-.08-top[1];dz=roof_z-top[2]
    for who in preset['people']:preset['placements']['race'][who]={'lateral':0,'vertical':round(dy,4),'longitudinal':round(dz,4),'yaw_degrees':0}
    return preset,{'vertical':dy,'longitudinal':dz,'roof':[roof_z,roof_y]},None


def _roof(parts):
    """(z centre, height) of the roof panel from upward-facing centre-line
    faces: the longest contiguous high run (wings are short, antennas thin)."""
    bins={}
    for p in parts:
        vs=p.geometry.vertices
        for t in p.geometry.triangles:
            a,b,c=(vs[i].position for i in t);u=[b[k]-a[k]for k in range(3)];v=[c[k]-a[k]for k in range(3)]
            n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);l=sum(x*x for x in n)**.5
            if l<1e-9 or n[1]/l<.6 or min(abs(a[0]),abs(b[0]),abs(c[0]))>.4:continue
            y=(a[1]+b[1]+c[1])/3
            for k in range(round(min(a[2],b[2],c[2])/.05),round(max(a[2],b[2],c[2])/.05)+1):bins[k]=max(bins.get(k,-9),y)
    if not bins:raise ValueError('no roof surface for crew placement')
    keys=sorted(bins);peak=max(bins.values());best=None;run=None
    for limit in (.1,.2,.3):
        run=best=None
        for k in keys:
            if bins[k]>=peak-limit:run=(run[0],k)if run and run[1]==k-1 else (k,k)
            else:run=None
            if run and (best is None or run[1]-run[0]>best[1]-best[0]):best=run
        if best[1]-best[0]>=12:break
    ys=[bins[k]for k in keys if best[0]<=k<=best[1]]
    return (best[0]+best[1])/2*.05,sorted(ys)[len(ys)//4]


def build(source,donor,profile,output,*,colour=0,colour_database=None,colour_strings=None):
    """Fresh deterministic build; immutable source, donor pins recorded."""
    if not REQUIRED<=set(profile) or set(profile)-REQUIRED-OPTIONAL or profile['version']!=1:raise ValueError('GT3 build profile schema')
    profile=dict(profile);mode=profile.get('mode','full')
    if mode not in ('standard','full'):raise ValueError('GT3 mode must be standard or full')
    raw=_read_source(source)
    if digest(raw)!=profile['source_sha256']:raise ValueError('GT3 immutable source hash mismatch')
    engine=profile.setdefault('engine_sha256',GT3_CORE_SHA256);profile.setdefault('lighting_policy',DEFAULT_LIGHTING)
    profile.setdefault('material_policy',{'qualified_environment':True,'clip_clamp_geometry':True});profile.setdefault('limitations',['Owner in-game verification pending.'])
    profile.setdefault('source_identity',{'source':Path(source).name})
    parsed=inspect_car(raw)
    colour_record={'source_index':colour,'name':'Unassociated source variant (database not supplied)'}
    if (colour_database is None)!=(colour_strings is None):raise ValueError('Both original colour tables required')
    if colour_database is not None:
        colour_record=select(catalog(Path(colour_database).read_bytes(),Path(colour_strings).read_bytes()),int(profile.get('model_key','0x0'),0),colour,parsed['body'])
    env_name=profile['assembly']['environment_reference']
    references=profile.get('references')or {}
    if not references:references={n:digest((Path(donor)/n).read_bytes())for n in ('car.dx','complete.dx','wheel.dx',env_name)}
    profile['references']=references;pinned={}
    for name,expected in references.items():
        if Path(name).name!=name or '/'in name or '\\'in name:raise ValueError('GT3 donor reference must be local basename')
        value=(Path(donor)/name).read_bytes()
        if digest(value)!=expected:raise ValueError('GT3 donor reference changed: '+name)
        pinned[name]=value
    if any(n not in pinned for n in ('car.dx','complete.dx','wheel.dx',env_name)):raise ValueError('GT3 donor models/environment not pinned')
    environment=pinned[env_name]
    decoded={};translated={};approx={}
    for component in ('body','wheel'):
        sel=profile['selections'][component]
        if set(sel)!={'model','lod','callbacks','external_texture_bindings'}:raise ValueError('GT3 selected model/LOD/branch must be explicit')
        scene=reconstruct(raw,component=component,model_index=sel['model'],lod=sel['lod'],colour=colour,callbacks=sel['callbacks'],engine_sha256=engine,external_texture_bindings=sel['external_texture_bindings'],strict_textures=bool(profile['material_policy'].get('strict',True)) if 'strict' in profile['material_policy'] else False)
        decoded[component]=scene
        translated[component],approx[component]=prepare(scene,{'source_sha256':profile['source_sha256'],**profile['lighting_policy']})
    output=Path(output)
    if output.exists():raise ValueError('GT3 build output already exists')
    assets=output/'assets';assets.mkdir(parents=True)
    body,body_audit=compile_draws(translated['body'],assets,environment_reference=environment,material_policy=profile['material_policy'])
    rim,rim_audit=compile_draws(translated['wheel'],assets,environment_reference=environment,material_policy=profile['material_policy'])
    rim=orient_parts(rim,source_outward_x=1)
    rim,fit=fit_rim(rim,{k:profile['wheel'][k]for k in ('reference_part','radius_m','outboard_x_m','source_outward_x','evidence')})
    tyre_cfg=profile['tyre']
    if tyre_cfg.get('texture',('stock'if mode=='standard'else'source'))=='stock':
        tyre,tyre_audit=stock_tyres(pinned['wheel.dx'],tyre_cfg,None)
        for p in tyre:
            stem=p.textures[0];src=Path(donor)/(stem+'.dxt')
            if src.is_file():(assets/src.name).write_bytes(src.read_bytes())
    else:
        texture=TextureSet(raw,parsed['tyre']['offset']).texture(0)
        rgba=display_rgba(texture);bgra=bytearray(rgba)
        for i in range(0,len(bgra),4):bgra[i],bgra[i+2]=bgra[i+2],bgra[i]
        tyre_data=struct.pack('<5I',0xfeed,1,zlib.crc32(bgra)&0xffffffff,texture['width'],texture['height'])+bgra
        tyre_stem='gt3-tyre-'+digest(tyre_data)[:20]+'-tga'
        (assets/(tyre_stem+'.dxt')).write_bytes(tyre_data)
        tyre,tyre_audit=stock_tyres(pinned['wheel.dx'],tyre_cfg,tyre_stem)
    wheel=tyre+rim
    assembly=profile['assembly']
    if not {'environment_reference','body_translation_m','race_body_translation_m','frontend_hubs_m','evidence'}<=set(assembly)or set(assembly)-{'environment_reference','body_translation_m','race_body_translation_m','frontend_hubs_m','evidence','body_scale'}or not assembly['evidence']:raise ValueError('Explicit GT3 compatibility assembly required')
    if len(assembly['frontend_hubs_m'])!=4:raise ValueError('Four explicit MR presentation hubs required')
    body=place(scale_parts(body,assembly.get('body_scale',1.)),assembly['body_translation_m'])
    complete=list(body);groups=[]
    for hub in assembly['frontend_hubs_m']:
        if hub[0]==0:raise ValueError('Wheel side cannot be zero')
        angle=instance_angle(-1 if hub[0]<0 else 1)
        groups.append({'draws':list(range(len(complete),len(complete)+len(wheel))),'translation':hub,'rotation_y':angle})
        complete+=place(wheel,hub,angle)
    race=place(body,assembly['race_body_translation_m'])
    crew_record=None
    if mode=='standard' and profile.get('crew',True):
        from .addon_sdk.crew import fit_crew
        preset,placement,reason=_crew(donor,race,mode)
        if preset:
            crew,records=fit_crew(Path(donor),preset,'race',assets)
            race=race+crew;back=[-v for v in assembly['race_body_translation_m']]
            complete=list(body)+place(crew,back)+complete[len(body):]
            groups=[{**g,'draws':[i+sum(1 for _ in crew)for i in g['draws']]}for g in groups]
            crew_record={'preset':'retail Navara seated pair','placement':placement,'parts':len(crew)}
        else:crew_record={'skipped':reason}
    outputs={};features=None
    for name,parts in (('car.dx',race),('complete.dx',complete),('wheel.dx',wheel)):
        data=write_scene_dx(pinned[name],parts)
        if name=='car.dx' and mode=='standard' and profile.get('features',True):
            data,features=_native_features(data,assets,donor)
        (assets/name).write_bytes(data);m=parse_dx_bytes(data)
        outputs[name]={'sha256':digest(data),'triangles':m.triangle_count,'vertices':m.vertex_count,'draws':len(m.physical_draws),'validated':m.diagnostics.validated}
    preview={'race_wheel_instances':[{'translation':[h[k]+assembly['race_body_translation_m'][k]for k in range(3)],'rotation_y':instance_angle(-1 if h[0]<0 else 1),'scale':[1.,1.,1.]}for h in assembly['frontend_hubs_m']],
             'provenance':'Authoring presentation pose; not recovered GT3 or actual MR suspension. '+assembly['evidence']}
    json_write(assets/'preview-profile.json',preview)
    budget=require_vehicle_budget(texture_working_set(assets))
    report={'schema':'gt3-mr-build/2','status':'OFFLINE_INSPECTION_CANDIDATE','mode':mode,'profile':profile,'colourway':colour_record,'source':{c:s['report']for c,s in decoded.items()},'material_approximations':approx,'conversion':{'body':body_audit,'wheel':rim_audit},'outputs':outputs,'wheel_fit':fit,'tyre':tyre_audit,'crew':crew_record,'native_features':features,'embedded_groups':groups,'texture_budget':budget,'limitations':profile['limitations'],'runtime_qualified':False}
    json_write(output/'conversion-report.json',report);json_write(output/'texture-budget.json',budget)
    return report


def _native_features(data,assets,donor):
    """Breakable glass + brake glow from the compiled car (geometric evidence)."""
    from .addon_sdk.auto_features import derive,procedural_cracks
    from .addon_sdk.native_states import author_states
    textures={p.name.casefold():p.read_bytes()for p in assets.glob('*.dxt')}
    try:
        states,extra,detail=derive(data,textures)
        if not states.get('panes')and not states.get('brake'):return data,{'status':'NO_FEATURES_FOUND',**detail}
        if states.get('panes'):
            crack=Path(donor)/'windscreenc32-tga.dxt'
            extra['mr-auto-cracked-tga.dxt']=crack.read_bytes()if crack.is_file()else procedural_cracks()
        out,audit=author_states(data,states)
    except ValueError as exc:return data,{'status':'AUTO_FEATURES_SKIPPED','reason':str(exc)}
    for name,raw in extra.items():(assets/name).write_bytes(raw)
    return out,{'status':'PASS_AUTO_FEATURES',**detail,'audit':{k:v for k,v in audit.items()if k!='states'}}
