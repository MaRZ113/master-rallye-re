"""Compose independently validated author projects into the qualified 29/30 roster.

Author-slot IDs are explicit inputs, never edited in frozen projects. Runtime
rebinding changes CarID metadata only; resources retain their own namespaces.
No game launch, executable disk patch, implicit probe/save migration or assets.
"""
from __future__ import annotations
import argparse,copy,json,re,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import prepare_sdk_capacity_probe as probe
import addon_collection_runtime as legacy
import addon_runtime as runtime
import sdk_capacity_native as capacity
import vehicle_damage_native as damage
import vehicle_physics_native as physics
import vehicle_audio_native as audio
import vehicle_shadow_native as shadow
import vehicle_whine_native as supplemental
import vehicle_mechanics_native as mechanics
import build_runtime_launcher as launcher
from master_rallye.addon_sdk.collection import reserve_roster,compose_ui_bank
from master_rallye.addon_sdk.ui_assets import BANKS
from master_rallye.addon_sdk.manifest import canonical_json

PROFILE='sdk-multi-addon-roster'
ALLOCATION=262144

def append_owned_family(base,source,family):
    """Append only a validated author's family; preserve all existing bytes."""
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{1,39}',family):raise ValueError('unsafe physics family')
    prefix='Vehicles/'+family+'/'
    a=ET.fromstring(base.decode('utf-8-sig'));b=ET.fromstring(source.decode('utf-8-sig'))
    if any(n.get('Name','').casefold().startswith(prefix.casefold()) for n in a.iter('Value')):raise ValueError('physics family collision')
    wanted=[dict(n.attrib) for n in b.iter('Value') if n.get('Name','').startswith(prefix)]
    pattern=rb'<Value\s+Name="'+re.escape(prefix.encode())+rb'[^\"]+"[^>]*/>'
    lines=[line for line in source.splitlines() if re.search(pattern,line)]
    if any(not re.fullmatch(rb'\s*'+pattern+rb'\s*',line) for line in lines):raise ValueError('physics family values must occupy separate lines')
    if not wanted or len(lines)!=len(wanted) or base.count(b'</Broker>')!=1:raise ValueError('unsupported physics family serialization')
    newline=b'\r\n' if b'\r\n' in base else b'\n';block=newline+newline.join(lines)+newline
    result=base.replace(b'</Broker>',block+b'</Broker>',1)
    tree=ET.fromstring(result.decode('utf-8-sig'));names=[n.get('Name') for n in tree.iter('Value')]
    if len(names)!=len(set(names)):raise ValueError('duplicate composed physics value')
    actual=[dict(n.attrib) for n in tree.iter('Value') if n.get('Name','').startswith(prefix)]
    if actual!=wanted or result.replace(block,b'',1)!=base:raise ValueError('physics family composition changed other values')
    return result

def load_author(project,build):
    project=legacy._safe_root(project,'author project');build=legacy._safe_root(build,'author build')
    manifest_raw=(project/'addon.json').read_bytes();manifest=json.loads(manifest_raw)
    plan=json.loads((build/'addon-plan.json').read_text());rows=plan.get('addons',[])
    if len(rows)!=1 or rows[0]['addon_id']!=manifest['addon_id']:raise ValueError('exactly one standalone author addon required')
    original=rows[0]
    _,resources,report=legacy._load_project_build(manifest['addon_id'],manifest,manifest_raw,original,build)
    return original,resources,report

def derive(config):
    if not isinstance(config,dict) or not {'sdk_roster_version','base_runtime','projects'}<=set(config) or set(config)-{'sdk_roster_version','base_runtime','projects','reservations','retail_exe','frontend_profiler','frontend_bulk_read','stock_resource_projects','camera_profiles'} or type(config.get('sdk_roster_version')) is not int or config['sdk_roster_version']!=1:raise ValueError('unsupported SDK roster declaration')
    if type(config.get('frontend_profiler',False)) is not bool:raise ValueError('frontend_profiler must be an explicit boolean')
    if type(config.get('frontend_bulk_read',False)) is not bool:raise ValueError('frontend_bulk_read must be an explicit boolean')
    inputs=config.get('projects')
    if not isinstance(inputs,list) or len(inputs) not in (1,2):raise ValueError('only previously demonstrated 29/30 layouts admitted')
    base=Path(config['base_runtime']);source=Path(config.get('retail_exe',ROOT.parent/'MRallye.exe')).read_bytes()
    profile,image,base_rows,assets=probe.verified_base(base,source)
    plan=json.loads((base/'addon-plan.json').read_text());base_plan=copy.deepcopy(plan)
    rows=[];authors=[]
    for entry in sorted(inputs,key=lambda x:x['physical_id']):
        if set(entry)!={'project','build','physical_id'}:raise ValueError('invalid roster project input')
        original,resources,report=load_author(Path(entry['project']),Path(entry['build']))
        row=copy.deepcopy(original);row.update(physical_id=entry['physical_id'],class_local_index=8+len(rows))
        if row['vehicle_class']!='T2' or row['physical_id']!=28+len(rows):raise ValueError('new runtime projects must append ID28/29 T2 local8/9')
        if report.get('audio_profile'):
            report=copy.deepcopy(report);report['audio_profile']['physical_car_id']=row['physical_id']
        rows.append(row);authors.append({'input':entry,'original':original,'resources':resources,'report':report})
    all_rows=plan['addons']+rows
    for key in ('runtime_family','model_family','wheel_family','physics_family'):
        names=[r['identity'][key].casefold() for r in all_rows]
        if len(names)!=len(set(names)):raise ValueError('addon family conflict: '+key)
    slots=[{k:r[k] for k in ('physical_id','vehicle_class','class_local_index')} for r in all_rows]
    requests=[{k:r[k] for k in ('addon_id','vehicle_class','physical_id')} for r in all_rows]
    previous=json.loads(Path(config['reservations']).read_text()) if config.get('reservations') else None
    lock,active=reserve_roster(requests,slots=slots,previous=previous)
    if [r['physical_id'] for r in active]!=list(range(26,28+len(rows))):raise ValueError('reserved roster differs from selected layout')
    output=dict(assets);owned={p.casefold():p for p in output};ownership={};ui_report={}
    for row,author in zip(rows,authors):
        for path,location,role in author['resources']:
            key=path.casefold()
            if key in owned:raise ValueError('resource ownership collision: '+path)
            output[path]=location;owned[key]=path;ownership[path]=row['addon_id']
    for path in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
        value=probe.value(output[path])
        for row,author in zip(rows,authors):
            value=append_owned_family(value,(Path(author['input']['build'])/path).read_bytes(),row['identity']['runtime_family'])
        output[path]=value
    for role,(prefix,count,template,size) in BANKS.items():
        contributions=[]
        for row,author in zip(rows,authors):
            root=Path(author['input']['build'])
            if row['frontend'][role]['policy']!='project_frame':raise ValueError('roster import needs its own UI frame')
            contributions.append((row['addon_id'],(root/(prefix+'.dxb')).read_bytes(),(root/(prefix+f'_{count:03d}_000.dxt')).read_bytes()))
        bank,textures,assigned=compose_ui_bank(probe.value(output[prefix+'.dxb']),role,contributions)
        output[prefix+'.dxb']=bank
        for p,b in textures.items():
            if p.casefold() in owned:raise ValueError('UI frame collision')
            output[p]=b;owned[p.casefold()]=p
        for row in rows:row['frontend'][role]={'policy':'project_frame','frame':assigned[row['addon_id']]}
        ui_report[role]=assigned
    scene='DataScene/FrontendScreens/VehicleSelect.xml';output[scene]=probe.scene_append(probe.value(output[scene]),rows)
    stock_projects=config.get('stock_resource_projects',[])
    if not isinstance(stock_projects,list) or any(not isinstance(p,str) or not p for p in stock_projects):raise ValueError('stock_resource_projects must contain explicit project paths')
    if stock_projects:
        from master_rallye.addon_sdk.stock_project import validated_overrides
        for project in stock_projects:
            for path,data in validated_overrides(Path(project)).items():
                if path.casefold() in owned:raise ValueError('stock resource ownership collision: '+path)
                output[path]=data;owned[path.casefold()]=path;ownership[path]='stock-project:'+str(Path(project).resolve())
    # A single native damage dispatcher, a single set of each hook and one
    # sealed allocation. Capacity payload is appended at its own aligned VA.
    models=[probe.value(output[r['assets']['model_package_root']+'/car.dx']) for r in rows]
    image,ext=damage.extend_models(source,image,models);blob=bytes.fromhex(ext.pop('private_payload_hex'));ops=list(ext['operations']);bindings={'damage':{k:v for k,v in ext.items() if k!='operations'}}
    reports=[a['report'] for a in authors]
    native_profiles=[('physics',physics.append_reference,[r['physics_profile'] for r in reports if r.get('physics_profile')]),
        ('engine_audio',audio.append_audio,[r['audio_profile'] for r in reports if r.get('audio_profile')]),
        ('shadow',shadow.append_shadow,[r['shadow_bounds'] for r in reports if r.get('shadow_bounds')]),
        ('supplemental_audio',supplemental.append_whine,[r['audio_profile'] for r in reports if r.get('audio_profile')]),
        ('mechanics',mechanics.append_mechanics,[r['mechanical_attachments']['native_profile'] for r in reports if r.get('mechanical_attachments')])]
    writable=[]
    for name,append,profiles in native_profiles:
        image,blob,report=append(source,image,blob,damage.PAYLOAD_VA,profiles,ALLOCATION)
        if report:
            ops+=report['operations'];bindings[name]={k:v for k,v in report.items() if k!='operations'}
            writable+=report.get('writable_ranges',[])
    blob+=b'\x90'*((-len(blob))%16);capacity_offset=len(blob)
    image,cap=capacity.extend_image(source,image,rows,storage='private_allocation',payload_va=damage.PAYLOAD_VA+capacity_offset)
    blob+=bytes.fromhex(cap.pop('private_payload_hex'));ops+=cap['operations'];bindings['capacity']=cap
    if config.get('frontend_profiler',False):
        from vehicle_frontend_perf_native import append_frontend_perf
        state=bindings.get('supplemental_audio')
        if len(writable)!=1 or state is None:raise ValueError('frontend profiler requires the qualified shared audio RW page')
        # The audio appender owns its map/slots at the front of one RW/NX page.
        # Reserve the last512B only after checking its actual emitted layout.
        state_va=damage.PAYLOAD_VA+writable[0]['offset']+3584
        image,blob,perf=append_frontend_perf(source,image,blob,damage.PAYLOAD_VA,ALLOCATION,state_va=state_va,state_size=512,audio_state=state)
        ops+=perf['operations'];bindings['frontend_profiler']={k:v for k,v in perf.items() if k!='operations'}
    if config.get('frontend_bulk_read',False):
        from vehicle_dxt_bulk_native import append_dxt_bulk
        image,blob,bulk=append_dxt_bulk(source,image,blob,damage.PAYLOAD_VA,ALLOCATION)
        ops+=bulk['operations'];bindings['frontend_bulk_read']={k:v for k,v in bulk.items() if k!='operations'}
    camera_inputs=config.get('camera_profiles',[])
    if not isinstance(camera_inputs,list) or any(not isinstance(p,str) or not p for p in camera_inputs):raise ValueError('camera_profiles must contain explicit profile paths')
    if camera_inputs:
        from master_rallye.addon_sdk.camera_profile import bind_camera_profile
        from master_rallye.addon_sdk.stock_project import QUALIFIED_STOCK,safe
        from vehicle_camera_native import append_camera
        camera_bindings=[]
        identities={r['physical_id']:r['identity']['runtime_family'] for r in all_rows}
        identities.update(QUALIFIED_STOCK)
        for camera_path in camera_inputs:
            cp=json.loads(Path(camera_path).read_text());family=cp.get('runtime_family')
            if identities.get(cp.get('car_id'))!=family:raise ValueError('camera CarID/family is not a qualified roster identity')
            rel='DataGx/Vehicles/'+family+'/car.dx'
            if rel in output:model=probe.value(output[rel])
            else:
                matching=[]
                for stock_project in stock_projects:
                    sp=Path(stock_project);metadata=json.loads((sp/'stock-project.json').read_text())
                    if metadata['car_id']==cp['car_id'] and metadata['family']==family:matching.append(safe(sp/'resources',rel).read_bytes())
                if len(matching)!=1:raise ValueError('stock camera needs exactly one validated zero-edit/resource project')
                model=matching[0]
            camera_bindings.append(bind_camera_profile(cp,model))
        image,blob,camera=append_camera(source,image,blob,damage.PAYLOAD_VA,camera_bindings,ALLOCATION)
        ops+=camera['operations'];bindings['camera']={k:v for k,v in camera.items() if k!='operations'}
    if len(blob)>ALLOCATION or len(writable)>1:raise ValueError('bounded combined native allocation exhausted')
    for i,a in enumerate(ops):
        span=(a['file_offset'],a['file_offset']+len(bytes.fromhex(a['original_bytes'])))
        for b in ops[:i]:
            other=(b['file_offset'],b['file_offset']+len(bytes.fromhex(b['original_bytes'])))
            if max(span[0],other[0])<min(span[1],other[1]):raise ValueError('native hook ownership collision')
    plan['addons']=sorted(all_rows,key=lambda x:x['physical_id'])
    for row in rows:
        plan['class_mapping']['class_to_physical_ids']['T2'].append(row['physical_id'])
        plan['class_mapping']['physical_id_to_class_local'][str(row['physical_id'])]={'vehicle_class':'T2','class_local_index':row['class_local_index']}
    plan['registry_layout'].update(record_count=cap['layout']['record_count'],race_test_base=cap['layout']['racetest_base'],allocation_size=cap['layout']['allocation_size'])
    plan['build_target'].update(profile_id=PROFILE,runtime_deployment='EXTERNAL_SUSPENDED_PROCESS_CANDIDATE')
    plan['evidence_boundary'].update(resolved_addon_ids_runtime_qualified=False,experimental_addon_ids=[r['physical_id'] for r in rows])
    plan_raw=canonical_json(plan);plan_sha=probe.sha(plan_raw)
    extension={'operations':ops,'bindings':bindings,'allocation_size':ALLOCATION,'payload_va':damage.PAYLOAD_VA,'payload_size':len(blob),'runtime_qualified':False}
    pm,rvp=probe.patch_artifacts(source,image,base_rows,image,extension,plan_sha,json.loads((base/'native-patch-manifest.json').read_text()),profile_name=PROFILE,provenance_layer='V-SDK1',extension_key='sdk_roster_extension',derivation='verified frozen Subaru plus source-validated independent projects and composed native hooks')
    resource_rows=[{'path':p,'size':len(v) if isinstance(v,bytes) else v.stat().st_size,'sha256':probe.sha(v) if isinstance(v,bytes) else runtime.sha256_file(v),'role':'sdk-roster-resource','owner':ownership.get(p,'frozen-base-or-explicit-shared-composition')} for p,v in sorted(output.items())]
    index=runtime._resource_index(resource_rows);rm=canonical_json({'schema_version':1,'resources':resource_rows,'resource_count':len(resource_rows),'index_sha256':probe.sha(index),'runtime_state_paths':sorted(runtime.RUNTIME_STATE_PATHS),'addon_plan_sha256':plan_sha})
    profile.update(profile=PROFILE,status='READY_FOR_HUMAN_RUNTIME',addon_plan_sha256=plan_sha,native_patch_manifest_sha256=probe.sha(pm),native_patch_operations_sha256=probe.sha(rvp),resource_manifest_sha256=probe.sha(rm),resource_index_sha256=probe.sha(index),resource_count=len(resource_rows),reconstructed_reference_file_sha256=probe.sha(image),runtime_qualified=False,identity_runtime_qualified=False,
        native_extension={'address':damage.PAYLOAD_VA,'size':len(blob),'sha256':probe.sha(blob),'allocation_size':ALLOCATION,**({'writable_ranges':writable} if writable else {})},
        sdk_roster_layout={'record_count':28+len(rows),'addon_ids':list(range(26,28+len(rows)))},
        physical_slots_runtime_qualified=[26,27],experimental_physical_slots=[r['physical_id'] for r in rows],unresolved_runtime_gates=['Exact combined imported roster player/AI, finishing, Results and re-entry','Simultaneous independent physics/audio/damage/light behavior','No migration of experimental probe saves or other candidate state'])
    audit={'runtime_qualified':False,'capacity_mechanism':'SCALE1 29/30 user gameplay confirmed; this combined candidate not gameplay tested','author_slot_rebindings':[{'addon_id':r['addon_id'],'author_id':a['original']['physical_id'],'runtime_id':r['physical_id']} for r,a in zip(rows,authors)],'bindings':bindings,'native_hook_count':len(ops),'resource_ownership':ownership,'ui_frames':ui_report,'source_reports':reports,'base_plan_sha256':probe.sha(canonical_json(base_plan))}
    files={'addon-plan.json':plan_raw,'native-patch-manifest.json':pm,'native-patch-ops.rvp':rvp,'native-extension.bin':blob,'runtime-profile.json':canonical_json(profile),'resource-manifest.json':rm,'resource-index.tsv':index,'roster-reservations.json':canonical_json(lock),'sdk-roster-audit.json':canonical_json(audit),'runtime-artifact.json':canonical_json({'profile':PROFILE,'runtime_qualified':False,'resource_manifest_sha256':probe.sha(rm)})}
    return {'resources':output,'files':files,'profile':profile,'image':image,'capacity':cap,'rows':rows,'audit':audit}

def verify(bundle,context):
    for p,b in context['files'].items():
        if (bundle/p).read_bytes()!=b:raise ValueError('generated metadata changed: '+p)
    rows=json.loads(context['files']['resource-manifest.json'])['resources'];root=bundle/'resource-root'
    expected={r['path'].casefold() for r in rows};actual={p.relative_to(root).as_posix().casefold() for p in root.rglob('*') if p.is_file()}-runtime.RUNTIME_STATE_PATHS
    if expected!=actual:raise ValueError('resource set changed')
    for r in rows:
        p=legacy._under(root,r['path'])
        if runtime.is_user_editable_resource(r['path']):runtime.validate_user_editable_resource(p,r['path'])
        elif p.stat().st_size!=r['size'] or runtime.sha256_file(p)!=r['sha256']:raise ValueError('resource changed: '+r['path'])
    return {'status':'PASS_STATIC_COLLECTION_RUNTIME_BUNDLE','scope':'sdk-multi-addon-roster','resource_count':len(rows),'runtime_qualified':False}

def build(config,output):
    output=runtime._under_research_output(output)
    if output.exists():raise ValueError('candidate output already exists')
    ctx=derive(config);bundle=output/'runtime';bundle.mkdir(parents=True)
    for p,b in ctx['files'].items():(bundle/p).write_bytes(b)
    for p,v in ctx['resources'].items():
        target=bundle/'resource-root'/p;target.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(v,bytes):target.write_bytes(v)
        else:shutil.copyfile(v,target)
    exe=Path(config.get('retail_exe',ROOT.parent/'MRallye.exe')).resolve()
    result=verify(bundle,ctx);result['launcher']=launcher.build_launcher(bundle=bundle,output=output/'launcher',retail_exe=exe,bundle_verifier=lambda:verify(bundle,ctx));result['preflight']={}
    for mode in ('--verify','--verify-launch-environment','--self-test-native-allocation'):
        r=subprocess.run([str((output/'launcher/mr-runtime-launcher.exe').resolve()),mode,str(exe),str(bundle.resolve())],capture_output=True,text=True,timeout=45)
        result['preflight'][mode]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
        if r.returncode:raise ValueError('launcher preflight failed: '+mode)
    (output/'Launch-SDK-Roster.cmd').write_text('@echo off\n"%~dp0launcher\\mr-runtime-launcher.exe" --integrated "'+str(exe)+'" "%~dp0runtime"\nif errorlevel 1 pause\n')
    if config.get('frontend_profiler',False):
        (output/'Capture-Frontend.cmd').write_text('@echo off\nsetlocal\ncd /d "'+str(ROOT)+'"\n"'+sys.executable+'" "'+str(ROOT/'tools/capture_frontend_performance.py')+'" --candidate "%~dp0."\npause\n')
    (output/'roster-config.json').write_bytes(canonical_json(config));(output/'validation.json').write_bytes(canonical_json(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(json.loads(a.config.read_text()),a.output),indent=2))
