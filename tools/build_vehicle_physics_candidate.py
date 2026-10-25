"""Build a fresh physics revision from a frozen visual addon project.

Uses the existing qualified collection and native-damage launcher architecture.
No source reconstruction, CarID expansion, game launch or disk EXE patch.
"""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.project import build_project,_absolute_without_links
from master_rallye.addon_sdk.manifest import read_json,canonical_json
from master_rallye.addon_sdk.physics_profile import validate_profile
import prepare_vehicle_damage_runtime as damage
import addon_collection_runtime as collection
import addon_runtime as runtime
import build_runtime_launcher as launcher

def build(project,profile_path,output,*,retail_data_sma,retail_data_root,retail_exe,base_manifests=None):
    project=_absolute_without_links(project,'baseline author project')
    profile_path=_absolute_without_links(profile_path,'physics profile') if profile_path is not None else None
    output=runtime._under_research_output(output)
    if output.exists():raise ValueError('physics candidate output already exists; choose a fresh directory')
    addon,_=read_json(project/'addon.json');spec,_=read_json(project/'vehicle-project.json')
    profile=None
    if profile_path is not None:
        profile,_=read_json(profile_path)
        validate_profile(profile,donor_family=spec['vehicle_name'],runtime_family=addon['identity']['runtime_family'])
    for p in project.rglob('*'):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('baseline project contains linked entries')
    output.mkdir(parents=True);target=output/'project';shutil.copytree(project,target)
    source=Path(spec['source_vehicle_dir'])
    if not source.is_absolute():spec['source_vehicle_dir']=str((project/source).resolve())
    for resource in spec.get('resources',{}).values():
        for key in ('scene_candidate','native_brake_scene_candidate'):
            if key in resource and not Path(resource[key]).is_absolute():resource[key]=str((project/resource[key]).resolve())
    (target/'vehicle-project.json').write_bytes(canonical_json(spec))
    if profile is not None:(target/'physics-profile.json').write_bytes(canonical_json(profile))
    author=output/'author-build'
    authored=build_project(target,collection.DEFAULT_CAPABILITIES,author,retail_data_sma=retail_data_sma,retail_data_root=retail_data_root)
    manifests=list(base_manifests or [ROOT/'research/vehicles/sdk/examples/mercedes-ml320.json'])+[target/'addon.json']
    model=addon['assets']['model_package_root'].rstrip('/')+'/car.dx'
    kwargs={'manifest_paths':manifests,'project_builds':{addon['addon_id']:author},'capabilities_path':collection.DEFAULT_CAPABILITIES,'retail_exe':retail_exe,'base_package':collection.DEFAULT_BASE_PACKAGE,'model_path':model}
    context=damage.compile_context(**kwargs);bundle=output/'runtime';packaged=damage.prepare(context,bundle)
    compiled=launcher.build_launcher(bundle=bundle,output=output/'launcher',bundle_verifier=lambda:collection._verify_tree(bundle,damage.compile_context(**kwargs)))
    checks={}
    for mode in ('--verify','--verify-launch-environment','--self-test-native-allocation'):
        r=subprocess.run([str((output/'launcher/mr-runtime-launcher.exe').resolve()),mode,str(retail_exe.resolve()),str(bundle.resolve())],capture_output=True,text=True,timeout=45)
        checks[mode]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
        if r.returncode:raise ValueError('physics runtime preflight failed: '+mode)
    # Exact current EXE path is an input selected by the caller. The launcher
    # verifies its original hash and installs only into a fresh process.
    escaped=str(retail_exe.resolve())
    (output/'Launch-Physics.cmd').write_text('@echo off\n"%~dp0launcher\\mr-runtime-launcher.exe" --integrated "'+escaped+'" "%~dp0runtime"\nif errorlevel 1 pause\n')
    report={'status':'READY_FOR_HUMAN_PHYSICS_TEST','runtime_qualified':False,'game_launched':False,'project':str(target),'model':model,'author_build':authored,'runtime':packaged,'launcher':compiled,'preflight':checks}
    (output/'physics-candidate.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--retail-data-sma',type=Path,default=ROOT.parent/'corpora/retail/Data.sma');p.add_argument('--retail-data-root',type=Path,default=ROOT.parent/'corpora/retail/Data.sma_unpacked');p.add_argument('--retail-exe',type=Path,default=ROOT.parent/'MRallye.exe');p.add_argument('--base-manifest',type=Path,action='append');a=p.parse_args()
    r=build(a.project,a.profile,a.output,retail_data_sma=a.retail_data_sma,retail_data_root=a.retail_data_root,retail_exe=a.retail_exe,base_manifests=a.base_manifest);print(r['status'])
