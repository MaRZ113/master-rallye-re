"""Compose an SDK33 parent and authored additions into one native runtime.

Every physical ID is supplied by the manifest; no per-slot patch code is used.
The output is private and unqualified until the owner completes game tests.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import struct
import stat
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import addon_runtime as runtime
import build_sdk_roster as roster
import build_sdk_capacity_profile as experiment
import j2_frontend_reentry as j2
import sdk_capacity_native as native
from master_rallye.addon_sdk.capacity_profile import SDK33,validate_profile
from master_rallye.addon_sdk.collection import compose_ui_bank
from master_rallye.addon_sdk.manifest import canonical_json
from master_rallye.addon_sdk.roster_identity import catalog,preserve_reservations,preflight_player_state
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank

PROFILE='sdk-configurable-vehicle-registry'


def verify_bundle(bundle,context):
    """Check each directory/file once, never follow a reparse point.

    The legacy verifier stats every ancestor for each of thousands of files.
    Walking verified directory entries avoids that repeated IO while retaining
    the same full content hashes and mutable-state exceptions.
    """
    for name,raw in context['files'].items():
        if (bundle/name).read_bytes()!=raw:raise ValueError('Generated metadata changed: '+name)
    expected={r['path'].casefold():r for r in json.loads(context['files']['resource-manifest.json'])['resources']}
    root=roster.legacy._safe_root(bundle/'resource-root','registry resource root')
    seen=set();pending=[root]
    while pending:
        directory=pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                info=entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:raise ValueError('Linked registry resource: '+entry.path)
                if stat.S_ISDIR(info.st_mode):pending.append(Path(entry.path));continue
                if not stat.S_ISREG(info.st_mode):raise ValueError('Nonregular registry resource: '+entry.path)
                path=Path(entry.path);relative=path.relative_to(root).as_posix();key=relative.casefold()
                if key in seen:raise ValueError('Case-colliding registry resource: '+relative)
                if key in runtime.RUNTIME_STATE_PATHS:continue
                seen.add(key)
                if key not in expected:raise ValueError('Unlisted registry resource: '+relative)
                row=expected[key]
                if runtime.is_user_editable_resource(relative):runtime.validate_user_editable_resource(path,relative)
                elif info.st_size!=row['size'] or runtime.sha256_file(path)!=row['sha256']:raise ValueError('Resource changed: '+relative)
    if seen!=set(expected):raise ValueError('Registry resource set changed')
    return {'status':'PASS_STATIC_COLLECTION_RUNTIME_BUNDLE','scope':'sdk-configurable-vehicle-registry','resource_count':len(seen),'runtime_qualified':False}


def read_parent(source,base):
    roster.legacy._safe_root(base,'SDK33 parent')
    image,blob,rp=experiment.load_parent(source,base)
    manifest=(base/'resource-manifest.json').read_bytes()
    for name,key in [('resource-manifest.json','resource_manifest_sha256'),('native-patch-manifest.json','native_patch_manifest_sha256')]:
        if roster.probe.sha((base/name).read_bytes())!=rp[key]:raise ValueError('Parent compiled metadata changed: '+name)
    assets={}
    for r in json.loads(manifest)['resources']:
        p=roster.legacy._under(base/'resource-root',r['path'])
        if runtime.is_user_editable_resource(r['path']):runtime.validate_user_editable_resource(p,r['path'])
        elif p.stat().st_size!=r['size'] or runtime.sha256_file(p)!=r['sha256']:raise ValueError('Parent sealed resource changed: '+r['path'])
        assets[r['path']]=p
    _,check,ops=j2._parse_and_reconstruct(source,(base/'native-patch-ops.rvp').read_bytes())
    if check!=image:raise ValueError('Parent reconstruction differs')
    return image,blob,rp,assets,ops,{r['path']:r for r in json.loads(manifest)['resources']}


def identity(plan,classes):
    historical=json.loads((ROOT/'research/r5v_a/final-vehicle-registry.json').read_text())
    names={r['registry_index']:r['internal_name'] for r in historical['canonical_registry']}
    names[25]='Trooper'
    names.update({r['physical_id']:r['identity']['runtime_family'] for r in plan['addons']})
    return catalog([{'physical_id':i,'family':names[i],'vehicle_class':c,'retired':False} for c,ids in classes.items() for i in ids])


def derive(config):
    if (not isinstance(config,dict) or config.get('schema')!='mr-vehicle-registry-build/1'
        or not {'base_runtime','retail_exe','capacity_profile','projects'}<=set(config)
        or set(config)-{'schema','base_runtime','retail_exe','capacity_profile','projects','previous_roster','reactivation_migration','wheel_profiles'}):
        raise ValueError('Unsupported vehicle registry build manifest')
    p=validate_profile(config['capacity_profile']);base=Path(config['base_runtime'])
    source=Path(config['retail_exe']).read_bytes()
    image,blob,rp,assets,base_ops,parent_resource_rows=read_parent(source,base)
    plan=json.loads((base/'addon-plan.json').read_text());before=identity(plan,SDK33)
    rows=[];authors=[];canonical=copy.deepcopy(SDK33)
    inputs=config['projects']
    if not isinstance(inputs,list) or len(inputs)!=p['record_count']-33:raise ValueError('Supply one authored project for each new physical ID')
    for entry in sorted(inputs,key=lambda e:e['physical_id']):
        if not isinstance(entry,dict) or set(entry)!={'project','build','physical_id'}:raise ValueError('Project requires project/build/physical_id')
        original,resources,report=roster.load_author(Path(entry['project']),Path(entry['build']))
        row=copy.deepcopy(original);i=entry['physical_id']
        if type(i)is not int or i!=33+len(rows):raise ValueError('New IDs must append without deleting reservations')
        cls=row['vehicle_class']
        if cls not in canonical or i not in p['classes'][cls]:raise ValueError('Profile and authored class differ')
        row.update(physical_id=i,class_local_index=len(canonical[cls]))
        canonical[cls].append(i);rows.append(row)
        authored={path:location for path,location,role in resources}
        for path in ('DataGame/vehicles.xml','DataGame/Modifications.xml',*[prefix+suffix for prefix,stock,_,_ in BANKS.values() for suffix in ('.dxb',f'_{stock:03d}_000.dxt')]):
            authored[path]=Path(entry['build'])/path
        authors.append({'row':row,'resources':authored,'report':report,'entry':entry})
    native.validate_rows(rows)
    all_rows=plan['addons']+rows
    for key in ('runtime_family','model_family','wheel_family','physics_family'):
        names=[r['identity'][key].casefold() for r in all_rows]
        if len(names)!=len(set(names)):raise ValueError('Resource family collision: '+key)
    if len({r['addon_id'] for r in all_rows})!=len(all_rows):raise ValueError('Addon identity collision')
    plan['addons']=all_rows
    current=identity(plan,p['classes'])
    previous=json.loads(Path(config['previous_roster']).read_text()) if config.get('previous_roster') else before
    preserve_reservations(previous,current,migration=config.get('reactivation_migration'))
    output=dict(assets);ownership={};ui={}
    for path in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
        data=roster.probe.value(output[path])
        for a in authors:
            data=roster.append_owned_family(data,roster.probe.value(a['resources'][path]),a['row']['identity']['runtime_family'])
            if path=='DataGame/vehicles.xml' and a['report'].get('physics_profile',{}).get('owned_tyres'):
                from master_rallye.addon_sdk.physics_profile import publish_owned_tyres
                data=publish_owned_tyres(data,roster.probe.value(a['resources'][path]),a['report']['physics_profile'])
        output[path]=data
    for role,(prefix,stock_count,template,size) in BANKS.items():
        contributors=[]
        for a in authors:
            if a['row']['frontend'][role]['policy']!='project_frame':raise ValueError('New vehicles require explicitly authored artwork for '+role)
            bank=roster.probe.value(a['resources'][prefix+'.dxb'])
            name=parse_bank(bank)['names'][stock_count]
            tex=roster.probe.value(a['resources'][prefix.rsplit('/',1)[0]+'/'+name+'.dxt'])
            contributors.append((a['row']['addon_id'],bank,tex))
        bank,textures,assigned=compose_ui_bank(roster.probe.value(output[prefix+'.dxb']),role,contributors)
        output[prefix+'.dxb']=bank;output.update(textures)
        ui[role]={'frames':assigned,'count':parse_bank(bank)['count'],'original_frames_preserved':True}
        for r in rows:r['frontend'][role]['frame']=assigned[r['addon_id']]
    for a in authors:
        root=a['row']['assets']['model_package_root']+'/'
        for path,value in a['resources'].items():
            if path.casefold().startswith(root.casefold()):
                if path.casefold() in {k.casefold() for k in output}:raise ValueError('Owned resource collision: '+path)
                output[path]=value;ownership[path]=a['row']['addon_id']
    scene='DataScene/FrontendScreens/VehicleSelect.xml'
    output[scene]=roster.probe.scene_append(roster.probe.value(output[scene]),rows)
    from roster_scene_layout import reorder_scene
    selection={'canonical':canonical,'class_to_physical_ids':p['classes']}
    output[scene]=reorder_scene(output[scene],selection)
    image,blob,core=native.extend_capacity_profile(source,image,blob,p,[native._profile(r) for r in rows],parent_allocation_size=rp['native_extension']['allocation_size'])
    budget=(p['memory_budget_bytes']-p['layout']['allocation_size'])//65536*65536
    if budget<len(blob):raise ValueError('Insufficient native extension budget')
    operations=core['operations'][:];bindings={'capacity':core}
    if rows:
        from sdk_registry_routes import append_routes
        image,blob,routes=append_routes(source,image,blob,json.loads((base/'addon-plan.json').read_text()),rows,allocation_size=budget)
        operations+=routes['operations'];bindings['routes']=routes
        import vehicle_damage_native as damage
        pe=native.registry.parse_pe(source)
        delegate=native.branch_target(image,pe,damage.DAMAGE_CALL_VA,0xe8)
        if not 0x10000000<=delegate<0x10000000+len(blob):raise ValueError('Parent damage hook ownership differs')
        prefix=blob+b'\x90'*((-len(blob))%16)
        model_data=[roster.probe.value(output[r['assets']['model_package_root']+'/car.dx']) for r in rows]
        tail,report=damage.payload_models(model_data,payload_va=0x10000000+len(prefix),max_payload=budget-len(prefix),delegate_va=delegate)
        at=native.registry.va_to_file_offset(pe,damage.DAMAGE_CALL_VA,5)
        op=native.i0._operation('additional_models_after_parent_damage','v-cap2',at,image[at:at+5],native.i0._rel32(damage.DAMAGE_CALL_VA,0x10000000+len(prefix),0xe8),'one native deformation, preserved parent coverage then additional source identity',va=damage.DAMAGE_CALL_VA)
        image=native.i0._apply_layer(image,[op]);blob=prefix+tail;operations.append(op);bindings['damage']=report
        # Reference wrappers adjust only their own newly authored families and
        # tail-call the verified parent's publisher once.
        import vehicle_physics_native as physics
        profiles=[a['report']['physics_profile'] for a in authors if a['report'].get('physics_profile')]
        delegate=native.branch_target(image,pe,physics.CALL,0xe8)
        image,blob,report=physics.append_reference(source,image,blob,0x10000000,profiles,budget,parent_delegate_va=delegate)
        if report:operations+=report['operations'];bindings['physics']=report
        unsupported={key for a in authors for key in ('audio_profile','shadow_bounds','mechanical_attachments') if a['report'].get(key)}
        if unsupported:raise ValueError('Authored native contributors require explicit parent composition: '+', '.join(sorted(unsupported)))
    if config.get('wheel_profiles'):
        import vehicle_wheels_native as wheels
        qualified=roster.qualified_wheel_profiles(config['wheel_profiles'],output,all_rows)
        parent_audit=json.loads((base/'sdk-roster-audit.json').read_text())
        image,blob,report=wheels.append_wheels(source,image,blob,0x10000000,qualified,budget,mechanics_report=parent_audit['bindings'].get('mechanics'))
        if report:operations+=report['operations'];bindings['wheels']=report
    from sdk_registry_network import append_network_guard
    image,blob,network=append_network_guard(source,image,blob,allocation_size=budget)
    operations+=network['operations'];bindings['network']=network
    writable=copy.deepcopy(rp['native_extension'].get('writable_ranges',[]))+network['writable_ranges']
    allocation=max(rp['native_extension']['allocation_size'],(len(blob)+65535)//65536*65536)
    if allocation>budget:raise ValueError('Combined extension exceeds configured memory budget')
    plan['registry_layout'].update(record_count=p['record_count'],race_test_base=p['layout']['racetest_base'],allocation_size=p['layout']['allocation_size'])
    mapping={'class_to_physical_ids':p['classes'],'physical_id_to_class_local':{str(i):{'vehicle_class':c,'class_local_index':n} for c,ids in p['classes'].items() for n,i in enumerate(ids)}}
    plan['class_mapping'].update(mapping,ordering_policy='STABLE_SDK33_APPEND_CONFIGURED')
    plan['selection_layout']={**selection,**mapping}
    plan['build_target'].update(profile_id=PROFILE,runtime_deployment='EXTERNAL_SUSPENDED_PROCESS_CANDIDATE')
    plan['evidence_boundary'].update(resolved_addon_ids_runtime_qualified=False,experimental_addon_ids=[r['physical_id'] for r in rows])
    plan_raw=canonical_json(plan);plan_sha=roster.probe.sha(plan_raw)
    extension={'operations':operations,'bindings':bindings,'allocation_size':allocation,'payload_va':0x10000000,'payload_size':len(blob),'runtime_qualified':False}
    pm,rvp=roster.probe.patch_artifacts(source,image,base_ops,image,extension,plan_sha,json.loads((base/'native-patch-manifest.json').read_text()),profile_name=PROFILE,provenance_layer='V-CAP2',extension_key='vehicle_registry_extension',derivation='accepted SDK33 plus manifest-generated registry, native routes and authored resources')
    # Reuse the digest from the source verification for inherited files. The
    # final copied output is independently hashed once below, so a source edit
    # during composition is still detected without rereading unchanged input.
    resources=[]
    for path,v in sorted(output.items()):
        inherited=not isinstance(v,bytes) and path in assets and v==assets[path] and not runtime.is_user_editable_resource(path)
        resources.append({'path':path,'size':parent_resource_rows[path]['size'] if inherited else len(v) if isinstance(v,bytes) else v.stat().st_size,'sha256':parent_resource_rows[path]['sha256'] if inherited else roster.probe.sha(v) if isinstance(v,bytes) else runtime.sha256_file(v),'role':'vehicle-registry-resource'})
    index=runtime._resource_index(resources)
    rm=canonical_json({'schema_version':1,'resources':resources,'resource_count':len(resources),'index_sha256':roster.probe.sha(index),'runtime_state_paths':sorted(runtime.RUNTIME_STATE_PATHS),'addon_plan_sha256':plan_sha})
    profile=copy.deepcopy(rp)
    profile.update(profile=PROFILE,status='READY_FOR_HUMAN_RUNTIME',capacity_profile=p,vehicle_registry_descriptor=core['entries']['descriptor'],addon_plan_sha256=plan_sha,native_patch_manifest_sha256=roster.probe.sha(pm),native_patch_operations_sha256=roster.probe.sha(rvp),resource_manifest_sha256=roster.probe.sha(rm),resource_index_sha256=roster.probe.sha(index),resource_count=len(resources),reconstructed_reference_file_sha256=roster.probe.sha(image),native_extension={'address':0x10000000,'size':len(blob),'sha256':roster.probe.sha(blob),'allocation_size':allocation,**({'writable_ranges':writable} if writable else {})},sdk_roster_layout={'record_count':p['record_count'],'addon_ids':list(range(26,p['record_count']))},runtime_qualified=False,identity_runtime_qualified=False,experimental_physical_slots=[r['physical_id'] for r in rows],unresolved_runtime_gates=['Owner game checks for this exact composite: expanded native selection, AI/physics, artwork, Results, new competition save/restart; native high-ID network UI admission remains unqualified'])
    artwork={'schema':'mr-registry-artwork/1','entries':[{'physical_id':r['physical_id'],'family':r['identity']['runtime_family'],'model_variant':'PC','roles':{role:{'frame':r['frontend'][role]['frame'],'bank':BANKS[role][0]+'.dxb','provenance':'authored-project-preserved'} for role in BANKS}} for r in all_rows]}
    parent_model_hashes={runtime.sha256_file(value) for name,value in assets.items() if name.lower().endswith('/car.dx')}
    new_models=[{'physical_id':r['physical_id'],'family':r['identity']['runtime_family'],'car_dx_sha256':roster.probe.sha(roster.probe.value(output[r['assets']['model_package_root']+'/car.dx']))} for r in rows]
    for model in new_models:model['different_bytes_from_parent_models']=model['car_dx_sha256'] not in parent_model_hashes
    audit={'schema':'mr-vehicle-registry-build/1','runtime_qualified':False,'record_count':p['record_count'],'authored_additions':new_models,'ui':ui,'bindings':bindings,'parent_extension_prefix_preserved':blob[:len((base/'native-extension.bin').read_bytes())]==(base/'native-extension.bin').read_bytes(),'native_hook_count':len(json.loads(pm)['operations']),'mode_boundaries':{'network':'stock unsigned byte, high IDs require native protocol gate; no >254 runtime qualification','active_championship':'identity preflight only; disposable candidate state','challenge':'authored restrictions unchanged'},'owner_checks_required':['native frontend all class slots and return/reentry','AI/player distinct resources, physics and damage','CarSheet/SIDE and Results','fresh competition save/restart']}
    files={'addon-plan.json':plan_raw,'native-patch-manifest.json':pm,'native-patch-ops.rvp':rvp,'native-extension.bin':blob,'runtime-profile.json':canonical_json(profile),'resource-manifest.json':rm,'resource-index.tsv':index,'roster-identity.json':canonical_json(current),'artwork-bindings.json':canonical_json(artwork),'registry-build-audit.json':canonical_json(audit)}
    return {'resources':output,'files':files,'profile':profile,'image':image,'audit':audit,'previous_identity':previous,'identity':current}


def build(config,out,*,compile_launcher=True):
    started=time.perf_counter();out=runtime._under_research_output(Path(out))
    if out.exists():raise ValueError('Use a fresh candidate output directory')
    print('V-CAP2: validating SDK33 inputs and composing native registry/resources',file=sys.stderr,flush=True)
    ctx=derive(config);bundle=out/'runtime';bundle.mkdir(parents=True)
    composed=time.perf_counter()
    print(f'V-CAP2: writing {len(ctx["resources"])} resource files ({composed-started:.2f}s composition)',file=sys.stderr,flush=True)
    for name,raw in ctx['files'].items():(bundle/name).write_bytes(raw)
    for name,value in ctx['resources'].items():
        dest=bundle/'resource-root'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(value,bytes):dest.write_bytes(value)
        else:shutil.copyfile(value,dest)
    from master_rallye.addon_sdk.player_state import seed_player_state
    seed=seed_player_state(Path(config['retail_exe']).parent,bundle/'resource-root')
    state=bundle/'resource-root/DataGame/PlayerState.xml'
    if state.exists():
        check=preflight_player_state(state.read_bytes(),ctx['previous_identity'],ctx['identity'],migration=config.get('reactivation_migration'))
        if check['status'].startswith('BLOCKED_'):raise ValueError('Use a separate input game with no active competition for candidate seeding')
    copied=time.perf_counter()
    print('V-CAP2: verifying the generated resource set',file=sys.stderr,flush=True)
    verified=verify_bundle(bundle,ctx);checked=time.perf_counter()
    result={'status':'PRIVATE_OWNER_TEST_CANDIDATE','runtime_qualified':False,'verification':verified,'player_state':seed,'stage_seconds':{'compose':composed-started,'copy':copied-composed,'verify':checked-copied}}
    if compile_launcher:
        import build_runtime_launcher as launcher
        # This exact fresh bundle was verified immediately above; compiling
        # the launcher does not mutate resources. Avoid hashing the archive a
        # third time merely to pass the already completed gate to the builder.
        result['launcher']=launcher.build_launcher(bundle=bundle,output=out/'launcher',retail_exe=Path(config['retail_exe']),bundle_verifier=lambda:verified,sdk_binding_input=True)
    (out/'registry-build.json').write_bytes(canonical_json(config))
    result['seconds']=time.perf_counter()-started
    (out/'validation.json').write_bytes(canonical_json(result))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--no-launcher',action='store_true')
    a=p.parse_args();print(json.dumps(build(json.loads(a.manifest.read_text()),a.output,compile_launcher=not a.no_launcher),indent=2))


if __name__=='__main__':main()
