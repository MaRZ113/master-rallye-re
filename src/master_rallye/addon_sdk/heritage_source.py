"""Read-only native MR edition inventory and source-pinned Heritage staging.

Reuses the qualified DX Upgrader and reviewed R-DEMO GXI readers. No original
cooker execution, GT conversion, slot allocation or installation is implicit.
"""
from pathlib import Path
import hashlib,json,re,struct
from ..dx import parse_dx_bytes
from ..dx_revision_upgrade import upgrade_dx_131_to_135_with_report,validate_existing_rev135
from ..dxt import parse_dxt_bytes
from ..gxi import parse_gxi_bytes,encode_gxi_as_observed_dxt
from .project import _absolute_without_links,initialize_project
from .manifest import canonical_json
from ..errors import MasterRallyeError

EDITIONS={
 # Owner confirmed 2026-10-27: current corpora hold original EXEs; older
 # research fingerprints below can identify restriction-patched snapshots.
 '2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a':'demo-8.4.1',
 '611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728':'demo-9.3.1',
 'bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be':'demo-8.4.1',
 '931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680':'demo-9.3.1',
 '13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78':'demo-9.10.0',
 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4':'retail',
}
ROLES=('car.dx','complete.dx','wheel.dx')
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def read(path,limit=64*1024*1024,*,allow_empty=False):
    path=_absolute_without_links(Path(path),'Heritage source')
    if not path.is_file()or not (0 if allow_empty else 1)<=path.stat().st_size<=limit:raise ValueError('Missing/oversize Heritage source: '+str(path))
    with path.open('rb')as f:raw=f.read(limit+1)
    if not (0 if allow_empty else 1)<=len(raw)<=limit:raise ValueError('Heritage input changed size')
    return raw


def edition(root, *, family=None):
    root=_absolute_without_links(Path(root),'edition root');raw=read(root/'MRallye.exe',16*1024*1024);digest=sha(raw)
    identity={'edition':EDITIONS.get(digest,'UNQUALIFIED_EXECUTABLE'),'exe_sha256':digest,'exe_bytes':len(raw),'root':str(root),'executable_qualified':digest in EDITIONS,'identity_evidence':('Owner confirmed original corpora EXE on 2026-10-27' if digest in ('2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a','611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728') else 'Historical exact-build fingerprint; original EXE never executed by this adapter')}
    if family is not None and digest not in EDITIONS:
        # Fingerprints are source-only qualification data, independent of current EXE.
        fixtures=json.loads(Path(__file__).with_name('heritage_qualified_sources.json').read_text())
        matches=[]
        for fixture in fixtures['families']:
            folder=root/'DataGx/Vehicles'/family
            if fixture['family'].casefold()==family.casefold() and all(sha(read(folder/name))==value for name,value in fixture['files'].items()):matches.append(fixture)
        if len(matches)!=1:raise ValueError('Unqualified source edition/assets; original source fingerprint required')
        identity.update(edition=matches[0]['edition'],asset_qualification=matches[0],warning='EXE differs from original; never executed. Model/source bytes independently match historical shipped source fingerprints. Texture files recorded locally; not authenticated by EXE hash.')
    return identity


def compatible_model(raw,name):
    if len(raw)<8:raise ValueError('Truncated DX')
    revision=struct.unpack_from('<I',raw,4)[0]
    if revision==131:return upgrade_dx_131_to_135_with_report(raw,name)
    if revision==135:return raw,{'status':'EXISTING_REV135_PASSTHROUGH','source_sha256':sha(raw),'output_sha256':sha(raw),'validation':validate_existing_rev135(raw,name)}
    raise ValueError(f'Unsupported vehicle DX revision {revision}; no guessed conversion')


def inspect_family(folder):
    folder=_absolute_without_links(Path(folder),'vehicle family')
    if not folder.is_dir():raise ValueError('Native vehicle family missing')
    files={}
    for f in sorted(folder.iterdir()):
        if f.is_file()and f.suffix.casefold()in ('.dx','.dxt','.gxi','.gxm','.txt'):
            key=f.name.casefold()
            if key in files:raise ValueError('Case-colliding Heritage source resource')
            raw=read(f,allow_empty=f.suffix.casefold()=='.txt');files[key]={'path':str(f),'bytes':len(raw),'sha256':sha(raw)}
    meshes={}
    for key,item in files.items():
        if key.endswith('.txt'):
            names=re.findall(r'moMesh\(Name\s+\[([^\]]+)\]',read(item['path'],allow_empty=True).decode('utf-8',errors='replace'))
            if names:meshes[key]=names
    models={};references=set();problems=[]
    for role in ROLES:
        if role not in files:problems.append(role+': missing');continue
        raw=read(files[role]['path'])
        try:
            converted,report=compatible_model(raw,str(folder/role));m=parse_dx_bytes(converted)
            refs=sorted({n for d in m.physical_draws for n in d.texture_tuple if n.casefold()!='null'});references.update(refs)
            models[role]={'revision':struct.unpack_from('<I',raw,4)[0],'triangles':m.triangle_count,'draws':len(m.physical_draws),'vertices':m.vertex_count,'textures':refs,'materials':[{'draw':d.draw_index,'flags':list(d.flags_0x20),'state_0x24':d.unknown_0x24,'slots':list(d.texture_tuple),'tag':d.tag,'group':d.group_label,'control_words':list(d.control_words)}for d in m.physical_draws],'position_bounds':[[min(p[k]for p in m.vertices.positions)for k in range(3)],[max(p[k]for p in m.vertices.positions)for k in range(3)]],'native_convex_hull':m.collision.convex_hull is not None,'groups':[d.group_label for d in m.physical_draws if d.group_label],'converted_sha256':sha(converted),'conversion':report}
        except (ValueError,MasterRallyeError,struct.error)as exc:problems.append(role+': '+str(exc))
    textures={}
    for stem in sorted(references):
        name=stem.casefold();dxt=files.get(name+'.dxt');gxi=files.get(name+'.gxi')
        if dxt:
            raw=read(dxt['path']);t=parse_dxt_bytes(raw);mode='UNCHANGED_DXT';pair=None
            if gxi:pair=encode_gxi_as_observed_dxt(parse_gxi_bytes(read(gxi['path'])))==raw
            textures[stem]={'source':dxt,'dimensions':[t.width,t.height],'policy':mode,'gxi_pair_byte_identical':pair}
        elif gxi:
            raw=encode_gxi_as_observed_dxt(parse_gxi_bytes(read(gxi['path'])));t=parse_dxt_bytes(raw)
            textures[stem]={'source':gxi,'dimensions':[t.width,t.height],'policy':'OBSERVED_GXI_TO_DXT','output_sha256':sha(raw)}
        else:problems.append('Missing exact local texture '+stem)
    return {'family':folder.name,'folder':str(folder),'source_mesh_names':meshes,'files':files,'models':models,'textures':textures,'problems':problems,'qualified_for_staging':not problems and set(models)==set(ROLES),'features':{'crew':'Inspect source sidecars and crew material/geometry; no automatic character inference','glass':[g for m in models.values()for g in m['groups']if g.startswith('screen')],'brake_switch':any('blight'in m['groups']for m in models.values()),'audio':'Executable per-CarID association not inferred from folder name','physics':'Named XML references inventoried separately; not silently copied from Demo'}}


def inventory(root,*,retail=False):
    root=_absolute_without_links(Path(root),'edition root')
    identity={'edition':'retail-unpacked','root':str(root),'exe_sha256':None}if retail else edition(root)
    vehicles=root/'DataGx/Vehicles'
    if not vehicles.is_dir():raise ValueError('Expected user-local DataGx/Vehicles')
    identity['vehicles']=[inspect_family(f)for f in sorted(vehicles.iterdir())if f.is_dir()]
    extras={}
    for area,pattern in [('DataGame','*.xml'),('DataGx/Frontend','*'),('DataScene/FrontendScreens','VehicleSelect*'),('DataAudio/Vehicles','*')]:
        base=root/area
        if not base.is_dir():continue
        for f in sorted(base.rglob(pattern)):
            if f.is_file():
                raw=read(f,allow_empty=True);extras[f.relative_to(root).as_posix()]={'sha256':sha(raw),'bytes':len(raw)}
    import xml.etree.ElementTree as ET
    for vehicle in identity['vehicles']:
        family=vehicle['family'];refs={}
        for member in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
            f=root/member
            if not f.is_file():continue
            try:tree=ET.fromstring(read(f).decode('utf-8-sig'))
            except (ET.ParseError,UnicodeError)as exc:refs[member]={'status':'UNQUALIFIED_XML','error':str(exc)};continue
            prefix='Vehicles/'+family+'/'
            rows=[dict(n.attrib)for n in tree.iter('Value')if n.get('Name','').casefold().startswith(prefix.casefold())]
            if rows:refs[member]={'sha256':sha(read(f)),'exact_named_family_values':rows,'note':'Named family reference, not proof of the Demo executable class/CarID/audio registration'}
        vehicle['physics_references']=refs
        vehicle['audio_and_ui_association']='Shared source banks/screens inventoried by exact hash below; per-CarID original association unqualified unless an explicit native mapping is separately supplied.'
    identity['edition_references']=extras
    return identity


def compare_editions(catalogs,retail):
    reference={v['family'].casefold():v for v in retail['vehicles']};result=[]
    for catalog in catalogs:
        for vehicle in catalog['vehicles']:
            other=reference.get(vehicle['family'].casefold())
            if other is None:status='DEMO_MODEL_ABSENT_FROM_RETAIL'
            elif set(vehicle['models'])!=set(ROLES)or set(other['models'])!=set(ROLES):status='UNQUALIFIED'
            else:status='SAME_MODEL_BYTES'if all(vehicle['models'][n]['converted_sha256']==other['models'][n]['converted_sha256']for n in ROLES)else'DIFFERENT_NATIVE_MODELS'
            if other is not None and status=='SAME_MODEL_BYTES':
                at={n.casefold():t['source']['sha256']for n,t in vehicle['textures'].items()};bt={n.casefold():t['source']['sha256']for n,t in other['textures'].items()}
                status='SHARED_MODELS_AND_TEXTURES'if at==bt else'SHARED_MODELS_DIFFERENT_TEXTURES'
            result.append({'edition':catalog['edition'],'family':vehicle['family'],'classification':status,'qualified_for_staging':vehicle['qualified_for_staging']})
    return result


def _stage_resources(report,baseline,converted):
    baseline.mkdir(parents=True);converted.mkdir(parents=True,exist_ok=True);pins={};conversions={}
    for key,item in report['files'].items():
        raw=read(item['path'],allow_empty=key.endswith('.txt'))
        if len(raw)!=item['bytes']or sha(raw)!=item['sha256']:raise ValueError('Heritage source changed during staging: '+key)
        (baseline/key).write_bytes(raw);pins[key]=sha(raw)
    for role in ROLES:
        raw,detail=compatible_model((baseline/role).read_bytes(),str(Path(report['folder'])/role));(converted/role).write_bytes(raw);conversions[role]=detail
    for stem,item in report['textures'].items():
        raw=(baseline/Path(item['source']['path']).name.casefold()).read_bytes()
        if item['policy']=='OBSERVED_GXI_TO_DXT':raw=encode_gxi_as_observed_dxt(parse_gxi_bytes(raw))
        (converted/(stem+'.dxt')).write_bytes(raw)
    return pins,conversions


def stage_family(root,family,output):
    identity=edition(root,family=family)
    if not isinstance(family,str)or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,39}',family):raise ValueError('Unsafe native family')
    report=inspect_family(Path(root)/'DataGx/Vehicles'/family)
    if not report['qualified_for_staging']:raise ValueError('Unqualified source family: '+str(report['problems']))
    output=_absolute_without_links(Path(output),'Heritage preview')
    if output.exists():raise ValueError('Heritage preview output exists')
    pins,conversions=_stage_resources(report,output/'native-import',output/family)
    result={'source':identity,'family':family,'immutable_source_sha256':pins,'conversions':conversions,'package':str(output/family)}
    (output/'native-source.json').write_bytes(canonical_json(result));return result


def create_author(root,family,output,*,name,runtime_family,physics_donor,stock_audio_profile_id,vehicle_class='T2',retail_sma=None):
    """Immutable edition snapshot + compatible native source + normal SDK project.

    Class/audio/donor are EXPLICIT inputs. No source slot or audio association is
    invented. This does not change any installed/previously reserved roster.
    """
    identity=edition(root,family=family)
    for value in (family,physics_donor):
        if not isinstance(value,str)or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,39}',value):raise ValueError('Unsafe native family')
    if type(stock_audio_profile_id)is not int or not 0<=stock_audio_profile_id<=24:raise ValueError('Explicit tuned retail audio profile0..24 required')
    source=Path(root)/'DataGx/Vehicles'/family;report=inspect_family(source)
    if not report['qualified_for_staging']:raise ValueError('Unqualified native source: '+str(report['problems']))
    physics=None
    if retail_sma is not None:
        from .project import read_sma_member
        from .physics_profile import MEMBERS,compile_family,validate_player_defaults
        members={n:read_sma_member(Path(retail_sma),n)for n in MEMBERS}
        physics={'profile_version':1,'donor_family':physics_donor,'runtime_family':runtime_family,'source_sha256':{n:sha(b)for n,b in members.items()},'overrides':{},'notes':'Exact independent retail '+physics_donor+' donor defaults; no Demo tuning inference or visual fitment offsets.'}
        compiled={n:compile_family(b,physics,donor_family=physics_donor,runtime_family=runtime_family,source_label=n)[0]for n,b in members.items()}
        validate_player_defaults(compiled[MEMBERS[0]],compiled[MEMBERS[1]],runtime_family)
    output=_absolute_without_links(Path(output),'Heritage project')
    initialize_project(name=name,vehicle_class=vehicle_class,donor=physics_donor,family=runtime_family,output=output)
    baseline=output/'native-import';converted=output/'assets/source'/physics_donor
    pins,conversions=_stage_resources(report,baseline,converted)
    from generate_vehicle_ui_previews import render_sources
    render_sources(converted,output/'ui')
    icons={role:{'png':'ui/'+role+'.png','sha256':sha((output/'ui'/(role+'.png')).read_bytes()),'presentation':'mr-native-v1'}for role in ('vehicle_select_art','smallcarsheet')}
    (output/'ui-assets.json').write_bytes(canonical_json({'version':1,'icons':icons}))
    addon=json.loads((output/'addon.json').read_text());addon['audio']['stock_audio_profile_id']=stock_audio_profile_id
    addon['frontend'].update(manufacturer='MR DEMO',model=name.upper(),combined='MR DEMO '+name.upper())
    addon['results']['display_name']=family.upper()
    from .ui_assets import BANKS
    for role,(_,count,_,_)in BANKS.items():addon['frontend'][role]={'policy':'project_frame','frame':count}
    addon['description']=identity['edition']+' native '+family+'; independent retail '+physics_donor+' physics; explicit tuned retail audio profile '+str(stock_audio_profile_id)+'. Demo engine mapping unqualified; no authentic source audio claim.'
    from .manifest import _validate_one
    _validate_one(addon)
    (output/'addon.json').write_bytes(canonical_json(addon))
    if physics is not None:(output/'physics-profile.json').write_bytes(canonical_json(physics))
    provenance={'version':1,'adapter':'native-mr-heritage','source':identity,'family':family,'immutable_source_sha256':pins,'conversions':conversions,'texture_plan':report['textures'],'physics_donor':physics_donor,'audio':addon['audio'],'resource_pins':{f.name:sha(f.read_bytes())for f in converted.iterdir()if f.is_file()},'class_policy':'Explicit isolated test class; not inferred from historical Demo slot','baseline_policy':'native-import source bytes unchanged; native resources in assets/source; no GT/Classic conversion'}
    (output/'heritage-import.json').write_bytes(canonical_json(provenance))
    (output/'README.md').write_text('# MR Heritage Garage — '+name+'\n\nPrivate user-local native MR source snapshot. Do not distribute this project.\n'
        'native-import is immutable; heritage-import.json pins original and compatible resources.\n'
        'No GT Classic conversion or original Demo executable execution.\n'
        'Open this author project in Rally Workshop, select a matching isolated roster in Configure, Validate, then Build.\n'
        'Author-plan IDs26/27 are independently rebound by the qualified roster builder to runtime IDs28/29.\n'
        'The current owner-qualified roster limit is30; no31+ gameplay support is claimed.\n'
        'Use editable physics-profile.json and reversible Workshop overlays. Audio is an explicit retail donor fallback.\n'
        'Native feature recipes, intact attribute conservation and source hashes are recorded separately.\n'
        'See docs/sdk/help/en/heritage.md for reproduction and owner gameplay checks.\n',encoding='utf-8')
    return provenance


def verify_author(root):
    root=Path(root);metadata=root/'heritage-import.json'
    if not metadata.exists():return None
    report=json.loads(read(metadata,4*1024*1024))
    if report.get('version')!=1 or report.get('adapter')!='native-mr-heritage':raise ValueError('Unknown Heritage provenance')
    if {p.name for p in (root/'native-import').iterdir()}!=set(report['immutable_source_sha256']):raise ValueError('Immutable Heritage source file set changed')
    for name,digest in report['immutable_source_sha256'].items():
        if Path(name).name!=name or '/'in name or '\\'in name or ':'in name:raise ValueError('Unsafe Heritage snapshot name')
        if sha(read(root/'native-import'/name,allow_empty=name.endswith('.txt')))!=digest:raise ValueError('Immutable Heritage source changed: '+name)
    donor=report['physics_donor']
    if not isinstance(donor,str)or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,39}',donor):raise ValueError('Invalid Heritage donor identity')
    if {p.name for p in (root/'assets/source'/donor).iterdir()if p.suffix.lower()in('.dx','.dxt')}!=set(report['resource_pins']):raise ValueError('Immutable compatible Heritage resource set changed')
    for name,digest in report['resource_pins'].items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.(?:dx|dxt)',name):raise ValueError('Unsafe Heritage resource name')
        if sha(read(root/'assets/source'/donor/name))!=digest:raise ValueError('Immutable compatible Heritage baseline changed: '+name)
    if 'native_features'in report and sha(read(root/'native-feature-profile.json'))!=report['native_features']['profile_sha256']:raise ValueError('Native feature recipe changed; rebuild from the immutable source')
    return {'status':'PASS_IMMUTABLE_HERITAGE_SOURCE','edition':report['source']['edition'],'family':report['family'],'files':len(report['immutable_source_sha256'])}


def apply_features(root,profile_path):
    """Explicit native feature overlay, using a pinned Core state recipe."""
    root=Path(root);verify_author(root);report=json.loads(read(root/'heritage-import.json'));profile_raw=read(profile_path,1024*1024);profile=json.loads(profile_raw)
    if set(profile)!={'version','additional_textures','states','evidence'}or profile['version']!=1 or not isinstance(profile['evidence'],str)or not profile['evidence'].strip():raise ValueError('Invalid Heritage native feature recipe')
    target=root/'assets/source'/report['physics_donor'];extra={}
    for name,item in profile['additional_textures'].items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.dxt',name)or set(item)!={'path','sha256'}:raise ValueError('Unsafe native feature texture')
        raw=read(item['path']);parse_dxt_bytes(raw)
        if sha(raw)!=item['sha256']:raise ValueError('Feature texture SHA256 mismatch')
        if (target/name).exists():raise ValueError('Native feature must not replace source textures')
        extra[name]=raw
    from .native_states import author_states
    data,detail=author_states((target/'car.dx').read_bytes(),profile['states'])
    references={n.casefold()+'.dxt' for d in parse_dx_bytes(data).physical_draws for n in d.texture_tuple if n.casefold()!='null'}
    available={f.name.casefold() for f in target.iterdir() if f.is_file()}|{n.casefold() for n in extra}
    if references-available:raise ValueError('Missing native feature textures: '+str(sorted(references-available)))
    # All parsing/qualification happens before changing the new project's copy.
    for name,raw in extra.items():(target/name).write_bytes(raw)
    (target/'car.dx').write_bytes(data);(root/'native-feature-profile.json').write_bytes(profile_raw)
    report['native_features']={'profile_sha256':sha(profile_raw),'evidence':profile['evidence'],'audit':detail}
    report['resource_pins']={f.name:sha(f.read_bytes())for f in target.iterdir()if f.is_file()}
    (root/'heritage-import.json').write_bytes(canonical_json(report));return detail
