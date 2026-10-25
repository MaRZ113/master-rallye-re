"""Reproducible private SCALE1 capacity canary, not a substitute Lancer import.

The extra vehicle deliberately clones a verified stock family, at a separate
resource path with explicit SDK PROBE labels. Existing Subaru assets are read
only. Uses the existing external launcher format, never emits a game EXE.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,re,shutil,struct,tempfile
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import addon_runtime as runtime
import addon_collection_runtime as legacy
import j2_frontend_reentry as j2
import sdk_capacity_native as native
from master_rallye.addon_sdk.collection import merge_resources, compose_ui_bank, reserve_roster
from master_rallye.addon_sdk.physics import clone_vehicle_family_xml
from master_rallye.addon_sdk.ui_assets import BANKS,archive_member,append_frame,parse_bank
from master_rallye.vehicle_packaging import _open_sma_archive
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes


def sha(data):return hashlib.sha256(data).hexdigest()
def dump(path,data):path.write_bytes(runtime.canonical_json(data))
def value(source):return source if isinstance(source,bytes) else Path(source).read_bytes()


def verified_base(base,source):
    legacy._safe_root(base,'base bundle')
    profile=json.loads((base/'runtime-profile.json').read_text())
    # This canary extends the frozen milestone only. Other baselines require a
    # separate reviewed profile rather than accepting a self-consistent bundle.
    pins=json.loads((ROOT/'research/vehicles/scale1/frozen-base-pins.json').read_text())
    for path,expected in pins.items():
        if sha((base/path).read_bytes())!=expected:raise ValueError('unsupported frozen base identity: '+path)
    manifest_raw=(base/'resource-manifest.json').read_bytes()
    if sha(manifest_raw)!=profile['resource_manifest_sha256']:raise ValueError('base resource manifest identity mismatch')
    if sha((base/'native-patch-manifest.json').read_bytes())!=profile['native_patch_manifest_sha256']:raise ValueError('base patch manifest mismatch')
    rvp=(base/'native-patch-ops.rvp').read_bytes()
    if sha(rvp)!=profile['native_patch_operations_sha256']:raise ValueError('base RVP identity mismatch')
    header,image,rows=j2._parse_and_reconstruct(source,rvp)
    if header['reference_sha256']!=profile['reconstructed_reference_file_sha256']:raise ValueError('base image mismatch')
    assets={};root=base/'resource-root'
    index=json.loads(manifest_raw)
    for r in index['resources']:
        p=legacy._under(root,r['path'])
        if not runtime.is_user_editable_resource(r['path']):
            if p.stat().st_size!=r['size'] or runtime.sha256_file(p)!=r['sha256']:raise ValueError('base asset changed: '+r['path'])
        else:runtime.validate_user_editable_resource(p,r['path'])
        assets[r['path']]=p
    expected={p.casefold() for p in assets}
    actual={p.relative_to(root).as_posix().casefold() for p in root.rglob('*') if p.is_file()} - runtime.RUNTIME_STATE_PATHS
    if expected!=actual:raise ValueError('base resource set differs')
    return profile,image,rows,assets


def scene_append(data,rows):
    text=data.decode('utf-8-sig');bom=data.startswith(b'\xef\xbb\xbf');g=legacy.vehicle_select.g1
    for row in rows:
        if row['vehicle_class']!='T2':raise ValueError('probe scene currently admits the qualified T2 template only')
        local=row['class_local_index'];target=f'T2_Car{local+1}'
        if f'Name="{target}"' in text:raise ValueError('scene slot collision')
        a,b=g._egg_span(text,'T2_Car8');clone=text[a:b].replace('<Egg Name="T2_Car8">',f'<Egg Name="{target}">',1)
        for key,v in [('en2d Image Bank Index',str(row['frontend']['vehicle_select_art']['frame'])),
                      ('True Value',str(row['frontend']['vehicle_select_art']['frame'])),
                      ('X ID',str(local)),('XPos*',f'Frontend/VehicleSelect/Button{local}XPos')]:clone=g._replace_value(clone,key,v)
        _,end=g._egg_span(text,f'T2_Car{local}')
        text=text[:end]+'\r\n'+clone+text[end:]
    g._parse_xml(text)
    return (b'\xef\xbb\xbf' if bom else b'')+text.encode('utf-8')


def resource_extension(assets,rows,donor='Navara'):
    """Compose explicit family clones plus banks; no arbitrary path overrides."""
    output=dict(assets);composed={};report={};added={}
    # All source research inputs remain local. The prepared archive is immutable.
    with _open_sma_archive(assets['Data.sma']) as archive:
        members=archive.namelist()
        for row in rows:
            family=row['identity']['runtime_family']
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{1,39}',family):raise ValueError('unsafe probe family')
            if any(v.casefold().startswith(f'datagx/vehicles/{family}/'.casefold()) for v in output):raise ValueError('model family already installed')
            for key in ('model_family','wheel_family'):
                if row['identity'][key]!=family:raise ValueError('native family routing mismatch')
            if row['identity']['physics_family']!='Vehicles/'+family:raise ValueError('physics routing mismatch')
            prefix=f'DataGx/Vehicles/{donor}/'
            found=[m for m in members if m.casefold().startswith(prefix.casefold()) and Path(m).suffix.lower() in ('.dx','.dxt')]
            if not found:raise ValueError('missing stock source family')
            own={f'DataGx/Vehicles/{family}/'+m[len(prefix):]:archive.read(m) for m in found}
            # Opaque, exact stock geometry/materials. No Lancer identity is used.
            if not {'car.dx','complete.dx','wheel.dx'} <= {Path(p).name.lower() for p in own}:raise ValueError('stock family incomplete')
            for p,b in own.items():
                if p.lower().endswith('.dx'):
                    if not parse_dx_bytes(b).diagnostics.validated:raise ValueError('stock DX parse failed')
                else:parse_dxt_bytes(b)
            _,inventory=merge_resources([(row['addon_id'],own)])
            for p,b in own.items():
                if p.casefold() in {k.casefold() for k in output}:raise ValueError('resource collision')
                output[p]=b
            added[row['addon_id']]=inventory
        for role,(prefix,stock_count,template,size) in BANKS.items():
            path=prefix+'.dxb';original=archive_member(archive,path)
            if parse_bank(original)['count']!=stock_count:raise ValueError('prepared archive changed stock bank base')
            one,_=append_frame(original,template)
            texture=archive_member(archive,prefix+f'_{template:03d}_000.dxt')
            base=value(assets[path]) if path in assets else original
            bank,textures,assigned=compose_ui_bank(base,role,[(r['addon_id'],one,texture) for r in rows])
            composed[path]=bank
            for r in rows:r['frontend'][role]={'policy':'project_frame','frame':assigned[r['addon_id']]}
            for p,b in textures.items():
                if p.casefold() in {k.casefold() for k in output}:raise ValueError('new UI frame collision')
                output[p]=b
            report[role]={'frames':assigned,'base_count':parse_bank(base)['count'],'new_count':parse_bank(bank)['count'],'old_records_unchanged':True}
    for path in ['DataGame/vehicles.xml','DataGame/Modifications.xml']:
        data=value(assets[path]);reports=[]
        for row in rows:
            data,r=clone_vehicle_family_xml(data,donor_family=donor,runtime_family=row['identity']['runtime_family'],source_label=path);reports.append(r)
        composed[path]=data;report[path]=reports
    path='DataScene/FrontendScreens/VehicleSelect.xml';composed[path]=scene_append(value(assets[path]),rows)
    output.update(composed)
    return output,{'shared_composed_paths':sorted(composed),'ui_and_physics':report,'family_resources':added}


def patch_artifacts(source,base_image,base_rows,image,extension,plan_sha,base_manifest,*,
                    profile_name='scale1-bounded-capacity-probe',provenance_layer='SCALE1',extension_key='scale1_extension',
                    derivation='verified frozen base plus bounded source-evidenced roster extension'):
    pe,sections=runtime._pe_sections(source);rows=[];manifest=copy.deepcopy(base_manifest);ops=[]
    changed=[i for i,(a,b) in enumerate(zip(source,image)) if a!=b];spans=[]
    for i in changed:
        if spans and spans[-1][1]==i:spans[-1]=(spans[-1][0],i+1)
        else:spans.append((i,i+1))
    for n,(start,end) in enumerate(spans):
        before=source[start:end];after=image[start:end]
        if start>=0x218 and end<=0x21c:rva,section,flags,page=0xffffffff,'PE headers',1,0
        else:
            rva,section=runtime._file_range_to_rva(sections,start,end-start);flags=0;page=1 if section=='.text' else 2
        rows.append({'file_offset':start,'rva':rva,'length':end-start,'flags':flags,'page_class':page,'before':before,'after':after})
        owners=[o for o in extension['operations'] if start<o['file_offset']+len(bytes.fromhex(o['original_bytes'])) and o['file_offset']<end]
        ops.append({'name':f'collection_delta_{n:03d}','file_offset':start,'rva':None if flags else rva,'preferred_va':None if flags else 0x400000+rva,'section':section,
                    'expected_original_bytes':before.hex(),'replacement_bytes':after.hex(),'expected_original_sha256':sha(before),'replacement_sha256':sha(after),
                    'semantic_provenance':[{'layer':provenance_layer,'name':o['name']} for o in owners] or [{'layer':'verified-parent','name':'retained-frozen-operations'}]})
    for row in base_rows:
        if row['flags']==2:
            rows.append(row);ops.append(copy.deepcopy(next(o for o in base_manifest['operations'] if o['file_offset']==row['file_offset'])))
    if len(rows)>512:raise ValueError('current external launcher operation bound exceeded')
    rvp=j2.RVP_HEADER.pack(b'MRVP',1,runtime.MACHINE_I386,runtime.IMAGE_BASE,len(source),len(source),len(rows),bytes.fromhex(sha(source)),bytes.fromhex(sha(image)),bytes.fromhex(plan_sha))+j2._serialize_rvp_rows(rows)
    _,check,_=j2._parse_and_reconstruct(source,rvp)
    if check!=image:raise ValueError('RVP reconstruction mismatch')
    manifest.update(profile=profile_name,status='STATICALLY_VERIFIED_READY_FOR_HUMAN_RUNTIME',addon_plan_sha256=plan_sha,operations=ops,
                    process_memory_operation_count=sum(r['flags']!=1 for r in rows),evidence_boundary='OFFLINE_EMULATED_NOT_RUNTIME_QUALIFIED',**{extension_key:extension})
    manifest['reference_image'].update(sha256=sha(image),written_to_disk=False,derivation=derivation)
    return runtime.canonical_json(manifest),rvp


def derive(base,extras,source,*,storage='existing_cave'):
    profile,base_image,base_rows,assets=verified_base(base,source)
    plan=json.loads((base/'addon-plan.json').read_text());rows=copy.deepcopy(extras)
    native.validate_rows(rows)
    for key in ('runtime_family','model_family','wheel_family','physics_family'):
        names=[r['identity'][key].casefold() for r in plan['addons']+rows]
        if len(set(names))!=len(names):raise ValueError('existing addon resource family collision')
    all_slots=[{'physical_id':r['physical_id'],'vehicle_class':r['vehicle_class'],'class_local_index':r['class_local_index']} for r in plan['addons']+rows]
    requests=[{'addon_id':r['addon_id'],'vehicle_class':r['vehicle_class'],'physical_id':r['physical_id']} for r in plan['addons']+rows]
    lock,_=reserve_roster(requests,slots=all_slots)
    output,resource_report=resource_extension(assets,rows)
    plan['addons']=sorted(plan['addons']+rows,key=lambda r:r['physical_id'])
    for r in rows:
        cls=r['vehicle_class'];id_=r['physical_id'];local=r['class_local_index']
        plan['class_mapping']['class_to_physical_ids'][cls].append(id_)
        plan['class_mapping']['physical_id_to_class_local'][str(id_)]={'vehicle_class':cls,'class_local_index':local}
    image,extension=native.extend_image(source,base_image,rows,storage=storage)
    layout=extension['layout'];plan['registry_layout'].update(record_count=layout['record_count'],race_test_base=layout['racetest_base'],allocation_size=layout['allocation_size'])
    plan['build_target']['profile_id']='scale1-experimental-retail-roster'
    plan['evidence_boundary'].update(resolved_addon_ids_runtime_qualified=False,experimental_addon_ids=[r['physical_id'] for r in rows])
    plan['build_target']['runtime_deployment']='EXTERNAL_SUSPENDED_PROCESS_CANDIDATE'
    plan_bytes=runtime.canonical_json(plan);plan_sha=sha(plan_bytes)
    pm,rvp=patch_artifacts(source,base_image,base_rows,image,extension,plan_sha,json.loads((base/'native-patch-manifest.json').read_text()))
    resource_rows=[{'path':p,'size':len(b) if isinstance(b,bytes) else b.stat().st_size,'sha256':sha(b) if isinstance(b,bytes) else runtime.sha256_file(b),'role':'composed-collection-resource'} for p,b in sorted(output.items())]
    index=runtime._resource_index(resource_rows)
    resource_manifest={'schema_version':1,'resources':resource_rows,'resource_count':len(resource_rows),'index_sha256':sha(index),'runtime_state_paths':sorted(runtime.RUNTIME_STATE_PATHS),'addon_plan_sha256':plan_sha}
    rm=runtime.canonical_json(resource_manifest)
    final_profile=copy.deepcopy(profile)
    final_profile.update(profile='scale1-bounded-capacity-probe',status='READY_FOR_HUMAN_RUNTIME',addon_plan_sha256=plan_sha,native_patch_manifest_sha256=sha(pm),native_patch_operations_sha256=sha(rvp),resource_manifest_sha256=sha(rm),resource_index_sha256=sha(index),resource_count=len(resource_rows),reconstructed_reference_file_sha256=sha(image),runtime_qualified=False,identity_runtime_qualified=False,
                         physical_slots_runtime_qualified=[26,27],experimental_physical_slots=[r['physical_id'] for r in rows],unresolved_runtime_gates=['Human Vehicle Select, both T2 actors, AI, Results, return and disposable-save re-entry','Capacity probe uses genuine stock donor geometry; it is not a GT4 Lancer candidate'])
    files={'addon-plan.json':plan_bytes,'native-patch-manifest.json':pm,'native-patch-ops.rvp':rvp,'runtime-profile.json':runtime.canonical_json(final_profile),
           'resource-manifest.json':rm,'resource-index.tsv':index,'roster-reservations.json':runtime.canonical_json(lock),'composition-report.json':runtime.canonical_json(resource_report)}
    if storage=='private_allocation':
        payload=bytes.fromhex(extension['private_payload_hex'])
        final_profile['native_extension']={'address':extension['payload_va'],'size':len(payload),'sha256':sha(payload),'allocation_size':65536}
        files['native-extension.bin']=payload
        files['runtime-profile.json']=runtime.canonical_json(final_profile)
    return output,files,{'extension':extension,'rows':rows,'image':image,'base_image':base_image}


def verify(bundle,base,extras,source,*,storage='existing_cave'):
    resources,files,context=derive(base,extras,source,storage=storage)
    for path,data in files.items():
        if (bundle/path).read_bytes()!=data:raise ValueError('generated metadata differs: '+path)
    root=bundle/'resource-root'
    expected={p.casefold() for p in resources}
    actual={p.relative_to(root).as_posix().casefold() for p in root.rglob('*') if p.is_file()} - runtime.RUNTIME_STATE_PATHS
    if actual!=expected:raise ValueError('resource file set differs')
    for p,data in resources.items():
        path=legacy._under(root,p)
        if runtime.is_user_editable_resource(p):runtime.validate_user_editable_resource(path,p)
        elif runtime.sha256_file(path)!=(sha(data) if isinstance(data,bytes) else runtime.sha256_file(data)):raise ValueError('resource differs: '+p)
    return {'status':'PASS_STATIC_COLLECTION_RUNTIME_BUNDLE','runtime_qualified':False,'resource_count':len(resources),'experimental_ids':[r['physical_id'] for r in extras]}


def prepare(base,extras,output,source,*,storage='existing_cave'):
    output=runtime._under_research_output(output)
    if output.exists():raise ValueError('output exists')
    resources,files,context=derive(base,extras,source,storage=storage)
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.'+output.name,dir=output.parent))
    try:
        for path,data in files.items():(stage/path).write_bytes(data)
        for path,data in resources.items():
            dest=stage/'resource-root'/path;dest.parent.mkdir(parents=True,exist_ok=True)
            if isinstance(data,bytes):dest.write_bytes(data)
            else:shutil.copyfile(data,dest)
        verify(stage,base,extras,source,storage=storage)
        os.replace(stage,output)
    except BaseException:
        shutil.rmtree(stage);raise
    return verify(output,base,extras,source,storage=storage)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--extra',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--storage',choices=['existing_cave','private_allocation'],default='existing_cave');a=p.parse_args()
    raw=json.loads(a.extra.read_text());rows=raw if isinstance(raw,list) else [raw]
    source=(ROOT.parent/'MRallye.exe').read_bytes()
    result=verify(a.output,a.base,rows,source,storage=a.storage) if a.verify else prepare(a.base,rows,a.output,source,storage=a.storage)
    print(json.dumps(result,indent=2))
