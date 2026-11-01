"""Manifest-driven native Demo restoration using Heritage and Workshop services.

No vehicle names, source addresses, face IDs, source physics or artwork mappings
live here. Original resources and accepted projects are read-only inputs.
"""
from pathlib import Path,PurePosixPath
import copy,hashlib,json,re,struct,sys,xml.etree.ElementTree as ET
from . import heritage_source as heritage
from .project import read_sma_member
from .physics_profile import MEMBERS
from .historical_physics import source_family_profile
from .demo_identity import selected_identity
from .ui_assets import parse_bank,fit_rgba
from ..dxt import parse_dxt_bytes,decode_rgba_pixels
from ..dx import parse_dx_bytes
from ..dx_revision_upgrade import validate_existing_rev135
from ..demo_vehicle_audit import dx_evidence
from ..frontend_presentation import align_complete_rest_frame
from ..universal_vehicle_scene import output_directory

sha=lambda b:hashlib.sha256(b).hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def localized_records(raw,pointer):
    rows=[]
    for hit in re.finditer(re.escape(struct.pack('<I',pointer)),raw):
        offset=hit.start()
        if offset>=8 and offset%4==0:
            cat,index=struct.unpack_from('<2I',raw,offset-8)
            if cat<256 and index<256:rows.append({'file_offset':offset-8,'category':cat,'index':index,'pointer':pointer})
    return rows


def off_geometry(raw):
    """Stable original-surface fingerprints, excluding native ON/broken cases."""
    from ..topology_writer import source_geometry
    from ..preview_scene import logical_cases
    from ..demo_vehicle_audit import surfaces
    model=parse_dx_bytes(raw);geometries=source_geometry(model);cases,_=logical_cases(model)
    points=[];normals=[];colors=b'';uv=[];triangles=[];materials=[]
    for d in model.physical_draws:
        if d.draw_index in cases and cases[d.draw_index][1]!=1:continue
        g=geometries[d.draw_index];base=len(points)
        points.extend(v.position for v in g.vertices);normals.extend(v.normal for v in g.vertices);colors+=b''.join(v.color for v in g.vertices);uv.extend(v.uvs[0]for v in g.vertices)
        triangles.extend(tuple(base+i for i in t)for t in g.triangles)
        materials.extend([repr((d.texture_tuple,list(d.flags_0x20),d.unknown_0x24)).encode()]*len(g.triangles))
    return {k:v for k,v in surfaces(points,normals,colors,[uv],triangles,materials).items()if not k.startswith('_')}


def resolve(roots,root,path):
    p=PurePosixPath(path)
    if p.is_absolute()or any(x in('..',)or ':'in x or '\\'in x for x in p.parts):raise ValueError('Unsafe restoration source path')
    base=Path(roots[root]).absolute();candidate=base.joinpath(*p.parts)
    if not candidate.resolve().is_relative_to(base.resolve()):raise ValueError('Restoration source escaped root')
    # Heritage reads also reject links/junctions; reject the directory chain now.
    for part in (candidate,*candidate.parents):
        if part.is_symlink()or getattr(part,'is_junction',lambda:False)():raise ValueError('Linked restoration input')
    return candidate


def validate_manifest(m):
    keys={'version','id','name','source_family','runtime_family','vehicle_class','source','inputs','original_geometry','identity','physics','features','references','frontend_reference','runtime','notes'}
    if not isinstance(m,dict)or set(m)!=keys or type(m['version'])is not int or m['version']!=1:raise ValueError('Unsupported Demo restoration manifest')
    if not re.fullmatch('[a-z0-9][a-z0-9.-]{1,63}',m['id']):raise ValueError('Invalid restoration identity')
    for k in ('source_family','runtime_family'):
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,39}',m[k]):raise ValueError('Invalid native restoration family')
    if (m['vehicle_class'],m['runtime']['physical_id'])not in (('T2',30),('T2',31),('T3',32))or type(m['runtime']['physical_id'])is not int:raise ValueError('Restoration needs an explicitly bounded independent slot')
    if not isinstance(m['source']['files'],dict)or not 3<=len(m['source']['files'])<=512 or not 1<=len(m['inputs'])<=128:raise ValueError('Restoration input budget')
    if set(m['original_geometry'])!={'car.gxm','complete.gxm','wheel.gxm'}or not set(heritage.ROLES)<=set(m['source']['files']):raise ValueError('All original and rebaked model roles are required')
    aliases=m['features']['texture_aliases']
    if not isinstance(aliases,dict)or not aliases or any(not isinstance(v,str)or not re.fullmatch('[A-Za-z0-9_-]{1,96}',v)or v.casefold()=='null'for v in aliases.values())or len({v.casefold()for v in aliases.values()})!=len(aliases):raise ValueError('Unsafe or colliding restoration texture aliases')
    if set(m['identity']['artwork'])!={'vehicle_select_art','smallcarsheet'}:raise ValueError('Exactly two known artwork roles are required')
    evidence=m['identity'].get('frontend_stats')
    if evidence and evidence.get('status')=='PROVEN':
        value=evidence.get('value')
        if (not isinstance(value,list)or len(value)!=4 or any(type(v)is not int or not 0<=v<=10 for v in value)
                or value!=m['identity']['frontend']['stats']or evidence.get('record',{}).get('stats')!=value
                or not re.fullmatch('[0-9a-f]{64}',evidence.get('source_sha256',''))):raise ValueError('Historical frontend stats differ from qualified source evidence')
    for role,item in m['identity']['artwork'].items():
        if item['policy']not in('exact','bounded-resample','workshop-generated')or item['native_size']!=([128,128]if role=='vehicle_select_art'else[32,16]):raise ValueError('Unsupported artwork role dimensions or policy')
    for name,digest in m['source']['files'].items():
        if Path(name).name!=name or not re.fullmatch('[a-zA-Z0-9_. -]+',name)or not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('Unsafe source file pin')
    return m


def verify_inputs(m,roots):
    validate_manifest(m);pins={};inputs={}
    source=resolve(roots,m['source']['root'],m['source']['directory'])
    actual={p.name for p in source.iterdir()if p.is_file()}
    if actual!=set(m['source']['files']):raise ValueError('Canonical source file set changed')
    def read(path,digest):
        raw=heritage.read(path)
        if sha(raw)!=digest:raise ValueError('Restoration source hash differs: '+str(path))
        pins[str(path)]=digest;return raw
    for name,digest in m['source']['files'].items():read(source/name,digest)
    for key,item in m['inputs'].items():
        if set(item)!={'root','path','sha256'}:raise ValueError('Invalid restoration input declaration')
        inputs[key]=read(resolve(roots,item['root'],item['path']),item['sha256'])
    for name,key in m['original_geometry'].items():
        if inputs[key]!=(source/name).read_bytes():raise ValueError('Rebaked geometry differs from shipped source: '+name)
    evidence=[]
    for item in m['identity']['bindings']:
        raw=inputs[item['input']]
        if item['kind']=='xml':
            eggs=[n for n in ET.fromstring(raw).iter('Egg')if n.get('Name')==item['egg']]
            if len(eggs)!=1:raise ValueError('Ambiguous original identity widget')
            values={n.get('Name'):n.get('Value')for n in eggs[0].iter('Value')}
            if any(values.get(k)!=v for k,v in item['values'].items()):raise ValueError('Original UI identity binding differs')
            evidence.append(item)
        elif item['kind']=='localized':
            rows=localized_records(raw,item['pointer']);wanted=[r for r in rows if r['category']==item['category']and r['index']==item['index']]
            if len(wanted)!=item['count']:raise ValueError('Original localized association differs')
            offset=item['string_offset'];text=item['text'].encode('ascii')+b'\0'
            if raw[offset:offset+len(text)]!=text:raise ValueError('Original localized string differs')
            evidence.append({**item,'records':wanted})
        else:raise ValueError('Unknown identity evidence kind')
    return source,inputs,pins,evidence


def restoration_physics(policy,profile,inputs,members,*,runtime_family):
    """Keep inactive historical records separate from the active retail clone."""
    donor=policy['donor_family']
    if policy['mode']=='historical-compatible':
        return source_family_profile(inputs[policy['input']],members,source_family=policy['source_family'],donor_family=donor,runtime_family=runtime_family,source_only=policy['source_only'])
    if policy['mode']!='retail':raise ValueError('Unknown restoration physics policy')
    required={'profile_version','donor_family','runtime_family','source_sha256','overrides','notes'}
    if policy.get('require_exact_clone') and (any(profile['overrides'].values())or set(profile)-required):
        raise ValueError('Exact retail clone cannot contain physics or tyre overrides')
    report={'policy':'Independent unmodified retail clone','overrides':profile['overrides'],'notes':policy['reason']}
    if 'input'in policy:
        raw=inputs[policy['input']];prefix='Vehicles/'+policy['source_family']+'/'
        rows=[dict(v.attrib)for v in ET.fromstring(raw).iter('Value')if v.get('Name','').startswith(prefix)]
        if not rows:raise ValueError('Historical physics evidence family is absent')
        report['inactive_historical_evidence']={'sha256':sha(raw),'family':policy['source_family'],'row_count':len(rows),'rows':rows,'applied':False}
    return profile,report


def verify_retail_clone(original,compiled,*,donor_family,runtime_family):
    """Compare every original attribute after only the owned family rename."""
    def rows(raw,family):
        prefix='Vehicles/'+family+'/'
        values=[v for v in ET.fromstring(raw).iter('Value')if v.get('Name','').startswith(prefix)]
        result={v.get('Name')[len(prefix):]:{k:value for k,value in v.attrib.items()if k!='Name'}for v in values}
        if not result or len(result)!=len(values):raise ValueError('Missing or duplicate retail clone rows')
        return result
    report={}
    for member in MEMBERS:
        source=rows(original[member],donor_family);target=rows(compiled[member],runtime_family)
        if source!=target:raise ValueError('Compiled retail clone differs: '+member)
        if rows(compiled[member],donor_family)!=source:raise ValueError('Original retail donor changed: '+member)
        report[member]={'identical_family_rows':len(source),'differences':[]}
    return report


def qualify_rebaked_model(raw,name,rule=None):
    """Exact optional cache repair; all local render/collision streams conserved."""
    if rule is None:
        validation=validate_existing_rev135(raw,name);fixed,count=heritage.repair_global_indices(raw,require_order_equivalence=True)
    else:
        # An explicit, exact-source cache repair is different from weakening
        # the generic writer's oriented-triangle validation. Local draw
        # indices/attributes/collision must remain unchanged below.
        if set(rule)!={'source_sha256','authoring_sha256','reason'}or sha(raw)!=rule['source_sha256']or not rule['reason']:raise ValueError('Unqualified source cache repair')
        fixed,count=heritage.repair_global_indices(raw)
        if sha(fixed)!=rule['authoring_sha256']:raise ValueError('Unexpected cache repair output')
        validation={'status':'EXPLICIT_SOURCE_PINNED_CACHE_REPAIR','reason':rule['reason'],'output_validation':validate_existing_rev135(fixed,name)}
    a,b=dx_evidence(raw,name),dx_evidence(fixed,name);keys=('surface_sha256','uv_surface_sha256','normal_color_surface_sha256','material_surface_sha256','draw_state_sha256','collision_sha256')
    if any(a[k]!=b[k]for k in keys):raise ValueError('Cache repair changed authentic source streams')
    return fixed,{'source_sha256':sha(raw),'authoring_sha256':sha(fixed),'cache_positions_changed':count,'input_validation':validation,'fingerprints':{k:a[k]for k in keys}}


def prepare(manifest,roots,roster_config,output,*,sdk_root,build=True):
    from ..workshop.service import WorkshopProject
    m=validate_manifest(copy.deepcopy(manifest));source,inputs,pins,evidence=verify_inputs(m,roots)
    config=json.loads(Path(roster_config).read_text());previous_projects=copy.deepcopy(config['projects']);slot=m['runtime']['physical_id'];expected=list(range(28,slot))
    replacement=m['runtime'].get('replace_addon_id')
    if replacement:
        if [r['physical_id']for r in config['projects']]!=expected+[slot]:raise ValueError('Replacement must preserve every earlier physical ID')
        target=config['projects'][-1]
        previous=json.loads((Path(target['project'])/'addon.json').read_text())
        if previous['addon_id']!=replacement:raise ValueError('Explicit replacement addon identity differs')
        config['projects']=config['projects'][:-1]
    elif [r['physical_id']for r in config['projects']]!=expected:raise ValueError('Preserve the exact previous independent roster before append')
    protected=[source,Path(roster_config),*[Path(p)for p in pins],*[Path(p)for p in roots.values()]]
    protected.extend(Path(entry[key])for entry in previous_projects for key in('project','build'))
    output=output_directory(Path(output),protected)
    if not output.is_relative_to((Path(sdk_root)/'.research-output').absolute()):raise ValueError('Restoration outputs must remain private')
    output.mkdir(parents=True);write(output/'restoration-manifest.json',m)
    qualification={}
    for name in heritage.ROLES:
        raw=(source/name).read_bytes()
        _,qualification[name]=qualify_rebaked_model(raw,name,m['source'].get('cache_repairs',{}).get(name))
    write(output/'source-authoring-qualification.json',qualification)
    sma=resolve(roots,'retail','Data.sma');donor=m['physics']['donor_family'];project=output/'author'
    heritage.create_author(Path(roots['demo']),m['source_family'],project,name=m['name'],runtime_family=m['runtime_family'],physics_donor=donor,
        stock_audio_profile_id=m['runtime']['audio_profile'],vehicle_class='T2'if m['vehicle_class']=='T3'else m['vehicle_class'],retail_sma=sma,features=None,family_folder=source)
    members={n:read_sma_member(sma,n)for n in MEMBERS};pp=m['physics'];profile=json.loads((project/'physics-profile.json').read_text())
    profile,physics=restoration_physics(pp,profile,inputs,members,runtime_family=m['runtime_family'])
    write(project/'physics-profile.json',profile);write(output/'physics-preservation.json',physics)
    assets=project/'assets/source'/donor;car=(assets/'car.dx').read_bytes();model=parse_dx_bytes(car);features=copy.deepcopy(m['features'])
    if features['states']['source_sha256']!=sha(car):raise ValueError('Feature selection belongs to a different source')
    for selector in features['selectors']:
        draw=model.physical_draws[selector['draw']]
        if list(draw.texture_tuple)!=selector['textures']or draw.triangle_count!=selector['triangle_count']:raise ValueError('Original material/face ownership differs')
    refs={}
    for name,item in m['references'].items():
        raw=read_sma_member(sma,item['member'])
        if sha(raw)!=item['sha256']:raise ValueError('Retail technical reference differs: '+name)
        refs[name]=raw
    feature=project/'native-features';feature.mkdir();(feature/'technical-donor.dx').write_bytes(refs['brake_model'])
    extra={};aliases={}
    for stem,key in features['texture_references'].items():
        raw=refs[key];alias=features['texture_aliases'][stem];aliases[stem]=alias;extra[alias+'.dxt']=raw
    for pane in features['states'].get('panes',[]):pane['broken_texture']=aliases[features['cracked_stem']]
    lamp=features['states']['brake'];lamp['lit_texture']=aliases[features['on_stem']];lamp['glow_texture']=aliases[features['glow_stem']]
    additions={}
    for name,raw in extra.items():
        path=feature/name;path.write_bytes(raw);additions[name]={'path':str(path.absolute()),'sha256':sha(raw)}
    recipe={'version':1,'additional_textures':additions,'states':features['states'],'evidence':features['evidence'],
        'brake_glow_reference':{'path':str((feature/'technical-donor.dx').absolute()),'sha256':sha(refs['brake_model']),'texture_aliases':aliases,'include_on_core':True}}
    write(feature/'recipe.json',recipe);audit=heritage.apply_features(project,feature/'recipe.json');write(output/'native-features.json',audit)
    reference={n:refs[k]for n,k in m['frontend_reference'].items()}
    aligned,framing=align_complete_rest_frame({n:(assets/n).read_bytes()for n in heritage.ROLES},reference)
    (assets/'complete.dx').write_bytes(aligned);write(output/'frontend-frame.json',framing)
    heritage_meta=json.loads((project/'heritage-import.json').read_text());heritage_meta['frontend_frame']=framing;heritage_meta['restoration_manifest_sha256']=sha(json.dumps(m,sort_keys=True).encode());heritage_meta['resource_pins']={p.name:sha(p.read_bytes())for p in assets.iterdir()if p.is_file()};write(project/'heritage-import.json',heritage_meta)
    from PIL import Image
    ui=json.loads((project/'ui-assets.json').read_text());art=[]
    generated={}
    from generate_vehicle_ui_previews import render_sources
    for role,item in m['identity']['artwork'].items():
        if item['policy']=='workshop-generated':
            settings=item.get('rendering',{})
            if set(settings)-{'azimuth','elevation','padding'}:raise ValueError('Unsupported artwork rendering setting')
            folder=project/'ui-generated'/role
            generated[role]=render_sources(assets,folder,roles=[role],style=item.get('presentation','mr-native-v2'),**settings)[role]
    for role,item in m['identity']['artwork'].items():
        if item['policy']=='workshop-generated':
            path=project/'ui'/(role+'.png');path.write_bytes((project/'ui-generated'/role/path.name).read_bytes())
            ui['icons'][role]={'png':'ui/'+path.name,'sha256':sha(path.read_bytes()),'presentation':item.get('presentation','mr-native-v1')}
            art.append({'role':role,**item,'png_sha256':sha(path.read_bytes()),'render':generated[role],
                        'source_resources':{p.name:sha(p.read_bytes())for p in assets.iterdir()if p.suffix.casefold()in('.dx','.dxt')}})
            continue
        bank=parse_bank(inputs[item['bank']]);name=bank['names'][item['frame']]
        expected=Path(m['inputs'][item['texture']]['path']).stem
        if name!=expected:raise ValueError('Original artwork bank ownership differs')
        tex=parse_dxt_bytes(inputs[item['texture']]);pixels=decode_rgba_pixels(tex);size=tuple(item['native_size']);policy=item['policy']
        if policy=='exact':
            if (tex.width,tex.height)!=size:raise ValueError('Original artwork dimensions differ')
        elif policy=='bounded-resample':pixels=fit_rgba((tex.width,tex.height,pixels),*size,padding=0)
        else:raise ValueError('Unknown artwork policy')
        path=project/'ui'/(role+'.png');Image.frombytes('RGBA',size,pixels).save(path);ui['icons'][role]={'png':'ui/'+path.name,'sha256':sha(path.read_bytes()),'presentation':item['presentation']}
        art.append({'role':role,'original_texture_sha256':sha(inputs[item['texture']]),'bank_sha256':sha(inputs[item['bank']]),**item})
    write(project/'ui-assets.json',ui)
    identity=m['identity'];addon=json.loads((project/'addon.json').read_text());selected=selected_identity(identity,addon['race_colour_rgba'])
    addon['addon_id']=m['id'];addon['frontend'].update(identity['frontend']);addon['results']['display_name']=selected['driver']['value'];addon['race_colour_rgba']=selected['race_marker']['value'];addon['description']=m['notes'];write(project/'addon.json',addon)
    ai_policy=m['runtime'].get('ai_policy')
    if isinstance(ai_policy,dict):
        from sdk_addon_ai import validate_eligibility
        validate_eligibility(m['vehicle_class'],ai_policy);addon['ai_eligibility']=copy.deepcopy(ai_policy)
    elif m['vehicle_class']!='T2':
        if ai_policy!='disabled':raise ValueError('Non-T2 restoration requires an explicit qualified AI policy')
        addon['ai_eligibility']={mode:{'enabled':False,'reason':'Explicit disabled restoration AI policy.'}for mode in addon['ai_eligibility']}
    policy=identity.get('race_marker_policy')
    if policy:
        write(project/'race-marker.json',{'version':1,'historical':identity.get('race_marker'),'policy':policy,'selected_rgba':addon['race_colour_rgba']})
    if m['vehicle_class']=='T3'and addon['vehicle_class']!='T3'and addon['ai_eligibility']['invitation']['enabled']:
        write(project/'native-ai.json',{'version':1,'eligibility':copy.deepcopy(addon['ai_eligibility'])})
        addon['ai_eligibility']['invitation']={'enabled':False,'reason':'Explicit runtime T3-only policy; technical author slot unchanged.'}
    write(project/'addon.json',addon)
    identity_report={'runtime_class':m['vehicle_class'],'bindings':evidence,'artwork':art,'driver':identity['driver'],'frontend':identity['frontend'],'selected':selected}
    if 'frontend_stats'in identity:identity_report['frontend_stats']=identity['frontend_stats']
    write(output/'identity-evidence.json',identity_report);write(project/'historical-identity.json',identity_report)
    config['experimental_record_count']=slot+1;config['projects'].append({'project':str(project.absolute()),'build':str(output/'not-built'),'physical_id':slot,**({'vehicle_class':m['vehicle_class']}if m['vehicle_class']!='T2'else{})})
    plan=output/'runtime-plan';plan.mkdir();write(plan/'roster-config.json',config)
    workshop=WorkshopProject.create(project,output/'workshop',kind='addon');workshop.configure_build({'roster_candidate':str(plan.absolute()),'retail_sma':str(sma),'retail_root':str(resolve(roots,'retail','Data.sma_unpacked'))})
    if policy:workshop.marker_select(policy['mode'],contrast=policy.get('contrast',False))
    result=workshop.build(output/'workshop/builds/first',sdk_root=Path(sdk_root),log=lambda s:print(s,flush=True))if build else None
    if any(sha(heritage.read(Path(p)))!=d for p,d in pins.items()):raise ValueError('Original source changed during restoration')
    write(output/'restoration-result.json',{'status':'READY_FOR_OWNER_TEST'if build else'AUTHORING_ONLY','runtime_qualified':False,'manifest_id':m['id'],'source_pins':pins,'physics':physics,'identity':identity,'build':result,'native_reference_sha256':{k:sha(v)for k,v in refs.items()},'candidate':str(output/'workshop/builds/first/candidate'),'unverified':m['runtime']['owner_gates']})
    (output/'Open-Restoration-Workshop.cmd').write_text('@echo off\n"'+sys.executable+'" "'+str(Path(sdk_root)/'tools/rally_workshop.py')+'" --project "%~dp0workshop" --workspace "%~dp0workspace"\nif errorlevel 1 pause\n')
    return workshop
