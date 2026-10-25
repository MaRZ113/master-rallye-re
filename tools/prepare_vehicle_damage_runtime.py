"""Optional source-bound native coverage-alpha adapter over a verified SDK build.

Reuses collection compilation, strict resource/tree verification, exact native
RVP serialization and the existing sealed process-allocation launcher. No game
is launched. No capacity expansion or physics values are introduced.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import addon_collection_runtime as collection
import addon_runtime as runtime
import build_runtime_launcher as launcher
import prepare_sdk_capacity_probe as layers
import j2_frontend_reentry as j2
import vehicle_damage_native as native
import vehicle_physics_native as physics_native
import vehicle_audio_native as audio_native
import vehicle_shadow_native as shadow_native
import vehicle_whine_native as whine_native
import vehicle_mechanics_native as mechanics_native

def sha(data):return hashlib.sha256(data).hexdigest()


def compile_context(*,model_path,**kwargs):
    context=collection._compile_context(**kwargs);files=dict(context['expected_files'])
    profile=copy.deepcopy(context['profile'])
    if profile.get('native_extension'):raise ValueError('do not combine an existing experimental native extension with damage adaptation')
    path=PurePosixPath(model_path)
    if path.is_absolute() or '..' in path.parts or path.suffix.lower()!='.dx':raise ValueError('model must be a local runtime resource path')
    key=path.as_posix().casefold()
    if key not in context['resource_sources']:raise ValueError('damage model is not owned by this verified collection')
    row,source=context['resource_sources'][key];data=source if isinstance(source,bytes) else source.read_bytes()
    if sha(data)!=row['sha256']:raise ValueError('damage source identity changed')
    retail=context['retail_exe'].read_bytes();_,parent,parent_rows=j2._parse_and_reconstruct(retail,files['native-patch-ops.rvp'])
    image,extension=native.extend_image(retail,parent,data)
    # Payload bytes are a separately sealed file, not duplicated in JSON.
    blob=bytes.fromhex(extension.pop('private_payload_hex'))
    source_report=json.loads(files['collection-inputs.json'])['id27_resource_source']
    physics_profiles=[source_report['physics_profile']] if source_report.get('physics_profile') else []
    image,blob,reference=physics_native.append_reference(retail,image,blob,native.PAYLOAD_VA,physics_profiles,extension.get('allocation_size',65536))
    if reference:
        extension['operations']+=reference['operations']
        extension['ride_height_reference']={k:v for k,v in reference.items() if k!='operations'}
    audio_profiles=[source_report['audio_profile']] if source_report.get('audio_profile') else []
    image,blob,audio=audio_native.append_audio(retail,image,blob,native.PAYLOAD_VA,audio_profiles,extension.get('allocation_size',65536))
    if audio:
        extension['operations']+=audio['operations']
        extension['independent_engine_audio']={k:v for k,v in audio.items() if k!='operations'}
    shadow_profiles=[source_report['shadow_bounds']] if source_report.get('shadow_bounds') else []
    image,blob,shadow=shadow_native.append_shadow(retail,image,blob,native.PAYLOAD_VA,shadow_profiles,extension.get('allocation_size',65536))
    if shadow:
        extension['operations']+=shadow['operations']
        extension['vehicle_shadow']={k:v for k,v in shadow.items() if k!='operations'}
    image,blob,whine=whine_native.append_whine(retail,image,blob,native.PAYLOAD_VA,audio_profiles,extension.get('allocation_size',65536))
    if whine:
        extension['operations']+=whine['operations']
        extension['transmission_whine']={k:v for k,v in whine.items() if k!='operations'}
    mechanics_profiles=[source_report['mechanical_attachments']['native_profile']] if source_report.get('mechanical_attachments') else []
    image,blob,mechanics=mechanics_native.append_mechanics(retail,image,blob,native.PAYLOAD_VA,mechanics_profiles,extension.get('allocation_size',65536))
    if mechanics:
        extension['operations']+=mechanics['operations']
        extension['mechanical_attachments']={k:v for k,v in mechanics.items() if k!='operations'}
    pm,rvp=layers.patch_artifacts(retail,parent,parent_rows,image,extension,profile['addon_plan_sha256'],
        json.loads(files['native-patch-manifest.json']),profile_name='sdk-native-damage-coverage-alpha',
        provenance_layer='SDK-DAMAGE-ALPHA',extension_key='damage_alpha_extension',
        derivation='verified collection plus source-bound coverage-alpha ownership after unchanged native deformation')
    profile.update(profile='sdk-native-damage-coverage-alpha',native_patch_manifest_sha256=sha(pm),
        native_patch_operations_sha256=sha(rvp),reconstructed_reference_file_sha256=sha(image),
        native_extension={'address':native.PAYLOAD_VA,'size':len(blob),'sha256':sha(blob),'allocation_size':extension.get('allocation_size',65536)},
        runtime_qualified=False,status='READY_FOR_HUMAN_RUNTIME')
    if whine and whine.get('writable_ranges'):
        profile['native_extension']['writable_ranges']=whine['writable_ranges']
    profile['unresolved_runtime_gates']=list(profile.get('unresolved_runtime_gates',[]))+[
        'Human race-wheel orientation and post-impact geometry/coverage; source-bound native alpha bridge is offline qualified only']
    policy={k:v for k,v in extension.items() if k!='operations'};policy['resource_path']=path.as_posix()
    artifact=copy.deepcopy(context['runtime_artifact'])
    artifact.update(profile=profile['profile'],artifact_kind='sdk-native-damage-coverage-candidate',
        native_patch_manifest_sha256=sha(pm),native_patch_operations_sha256=sha(rvp),
        reconstructed_reference_image_sha256=sha(image),native_damage_policy_sha256=sha(runtime.canonical_json(policy)),
        runtime_qualified=False)
    files.update({'native-patch-manifest.json':pm,'native-patch-ops.rvp':rvp,
        'runtime-profile.json':runtime.canonical_json(profile),'runtime-artifact.json':runtime.canonical_json(artifact),
        'native-extension.bin':blob,'damage-alpha-policy.json':runtime.canonical_json(policy)})
    return {**context,'expected_files':files,'profile':profile,'runtime_artifact':artifact,
        'patch_operation_count':len(json.loads(pm)['operations']),
        'process_memory_operation_count':json.loads(pm)['process_memory_operation_count']}


def prepare(context,output):
    output=runtime._under_research_output(output)
    if output.exists():raise ValueError('output exists')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.'+output.name,dir=output.parent))
    try:
        for name,data in context['expected_files'].items():(stage/name).write_bytes(data)
        for row in context['resource_inventory']['resources']:
            source_row,source=context['resource_sources'][row['path'].casefold()]
            if source_row!=row:raise ValueError('resource source row changed')
            dest=stage/'resource-root'/row['path'];dest.parent.mkdir(parents=True,exist_ok=True)
            if isinstance(source,bytes):dest.write_bytes(source)
            else:shutil.copyfile(source,dest)
        report=collection._verify_tree(stage,context);os.replace(stage,output);return report
    except BaseException:
        shutil.rmtree(stage);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,action='append',required=True)
    p.add_argument('--project-build',action='append',default=[]);p.add_argument('--model',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--launcher-output',type=Path)
    a=p.parse_args();kwargs={'manifest_paths':a.manifest,'project_builds':collection._parse_project_builds(a.project_build),
        'capabilities_path':collection.DEFAULT_CAPABILITIES,'retail_exe':collection.DEFAULT_RETAIL_EXE,'base_package':collection.DEFAULT_BASE_PACKAGE}
    ctx=compile_context(model_path=a.model,**kwargs);report=prepare(ctx,a.output)
    def verify():return collection._verify_tree(a.output,compile_context(model_path=a.model,**kwargs))
    if a.launcher_output:
        report['launcher']=launcher.build_launcher(bundle=a.output,output=a.launcher_output,bundle_verifier=verify)
        report['preflight']={}
        for mode in ('--verify','--verify-launch-environment','--self-test-native-allocation'):
            r=subprocess.run([str((a.launcher_output/'mr-runtime-launcher.exe').resolve()),mode,str(collection.DEFAULT_RETAIL_EXE),str(a.output.resolve())],capture_output=True,text=True)
            report['preflight'][mode]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
            if r.returncode:raise ValueError('launcher preflight failed: '+mode)
    (a.output.parent/'damage-runtime-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
