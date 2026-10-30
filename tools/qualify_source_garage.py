"""Seven owner-local regression scenes, independent preflight and D3D9 evidence.

No native runtime/CarID is created. Existing projects are read-only comparisons.
"""
from pathlib import Path
import argparse,copy,json,struct,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye import universal_vehicle_scene as u
from master_rallye import scene_semantics as sem
from master_rallye.source_qualification import preflight

CORPUS={
 'Evo2-4Runner':('.research-output/vehicles/4runner-stable/baseline/inputs/source-scene/scene.json','evo2','Terrano','.research-output/vehicles/4runner-stable/baseline/source-baseline/assets'),
 'Michelin-RAV4':('.research-output/vehicles/michelin-assembly/final/Car25A/assembly/scene/scene.json','michelin','Forester','.research-output/vehicles/michelin-native/final-pilot/source-baseline/assets'),
 'Michelin-MeganeF2':('.research-output/vehicles/michelin-assembly/final/Car06A/assembly/scene/scene.json','michelin','Forester',None),
 'Dakar2-Pajero':('.research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json',None,None,None),
 'Dakar2-Hino':('.research-output/vehicles/dakar2-fidelity/final/HINO/scene/scene.json',None,None,None),
 'Dakar2-Nissan':('.research-output/vehicles/dakar2-fidelity/final/NISSAN/scene/scene.json',None,None,None),
 'PC-Silver':('.research-output/vehicles/paris-dakar-silver-native/silver-final/inputs/source-scene/scene.json','silver','Pajero','.research-output/vehicles/paris-dakar-silver-native/silver-final/source-baseline/assets')}


def inventory(root):
    return {p.relative_to(root).as_posix():u.sha(u.read_bounded(p,u.MAX_OUTPUT_BYTES))for p in sorted(root.rglob('*'))if p.is_file()}


def make_profile(path,kind):
    if kind=='evo2':
        from master_rallye.source_garage_pilot import pilot_profile
        return pilot_profile(path)
    if kind=='silver':
        from master_rallye.paris_dakar_silver_pilot import pilot_profile
        return pilot_profile(path)
    if kind=='michelin':
        from master_rallye.michelin_native_pilot import profile
        result=profile(path)
        if u.load_scene(path)['source']['catalog']=='Car06A.PDO':
            result['wheel_transform_evidence']='Explicit dry-run MR rest-pose only: original T0022 rim faces +X and source-X instances need proper Ypi. Same0.38 MR radius reference is an authoring experiment, not qualified Megane physics or native import.'
        return result
    return None


def rav4_semantics(path):
    """Reuse reviewed source ownership, not an automatic triangle classifier."""
    from master_rallye.michelin_native_pilot import qualified,PANES,LAMP_IDS
    scene=qualified(path);claims=[]
    def add(mesh,role,ids='all'):
        claims.append({'mesh_id':mesh['id'],'material_id':mesh['material_id'],'triangles':ids,'role':role,
                       'interpretation':'mr_authoring','evidence':'Exact v7.7 RAV4 ownership recipe and source hash; source runtime blend/motion not inferred'})
    for mesh in scene['meshes']:
        mid=mesh['id'];count=len(mesh['triangles'])
        if mid=='body-texture-000':
            glass=sorted({i for values in PANES.values()for i in values});add(mesh,'glass',glass)
            add(mesh,'opaque_body',[i for i in range(count)if i not in glass])
        elif mid=='body-texture-007':
            add(mesh,'lamp_off',LAMP_IDS);add(mesh,'opaque_body',[i for i in range(count)if i not in LAMP_IDS])
        elif mid in('body-texture-001','body-texture-002','body-texture-003'):add(mesh,'cabin_crew')
        elif mid.startswith('body-'):add(mesh,'opaque_body')
        else:add(mesh,{'wheel-texture-000':'wheel_interior','wheel-texture-001':'rim','wheel-texture-002':'wheel_interior','wheel-texture-003':'rim','wheel-texture-004':'tyre'}[mid])
    return {'schema':sem.SCHEMA,'source_scene_sha256':u.sha(path.read_bytes()),'claims':claims}


def run(output,viewer=None):
    entries={name:(ROOT/values[0],*values[1:])for name,values in CORPUS.items()}
    scenes={name:u.load_scene(values[0])for name,values in entries.items()}
    protected=[v[0].parent for v in entries.values()]+[Path(s['source']['root'])for s in scenes.values()]
    for scene in scenes.values():protected.extend(map(Path,scene['source'].get('protected_roots',[])))
    output=u.output_directory(output,protected);output.mkdir(parents=True)
    rows={};before={name:inventory(v[0].parent)for name,v in entries.items()}
    from master_rallye.universal_scene_bridge import compile_scene
    from master_rallye.scene_dx_writer import write_scene_dx
    from master_rallye.source_scene_preview import stage_source_scene,capture_views,viewer_command,preview_cull
    from qualify_michelin_pilot import sheet
    from PIL import Image
    for name,(path,kind,donor,baseline)in entries.items():
        folder=output/name;folder.mkdir();scene=scenes[name];policy=make_profile(path,kind)
        semantics=rav4_semantics(path)if name=='Michelin-RAV4'else None
        if semantics is not None:
            policy['semantics']=semantics;(folder/'semantics.json').write_bytes(u.canonical(semantics))
        row=preflight(path,profile=policy,semantics=semantics);rows[name]=row
        (folder/'preflight.json').write_bytes(u.canonical(row))
        if policy is not None:
            (folder/'native-profile.json').write_bytes(u.canonical(policy))
            compiled=compile_scene(path,policy);raws={}
            fixtures=folder/'native-fixture';fixtures.mkdir()
            for filename,parts in [('car.dx',compiled['body_parts']),('complete.dx',compiled['complete_parts']),('wheel.dx',compiled['wheel_parts'])]:
                template=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles'/donor/filename
                data=write_scene_dx(u.read_bounded(template,u.MAX_OUTPUT_BYTES),parts)
                (fixtures/filename).write_bytes(data);raws[filename]=u.sha(data)
                if baseline is not None and data!=u.read_bounded(ROOT/baseline/filename,u.MAX_OUTPUT_BYTES):
                    raise ValueError('Accepted native baseline changed: '+name+'/'+filename)
            for filename,data in compiled['textures'].items():
                (fixtures/filename).write_bytes(data)
                if baseline is not None and data!=u.read_bounded(ROOT/baseline/filename,u.MAX_OUTPUT_BYTES):
                    raise ValueError('Accepted native texture changed: '+name+'/'+filename)
            row['native_fixture_sha256']=raws;row['accepted_native_baseline_exact']=baseline is not None
            row['native_fixture_boundary']='Compiler geometry/material fixture only; no CarID, physics, controllers or new playable candidate'
        if kind is None:
            from master_rallye.source_adapters.dakar2_fidelity import expose_uv1
            derived=folder/'typed-uv1';first=expose_uv1(path,derived)
            repeated=expose_uv1(path,folder/'typed-uv1-repeat')
            if first['scene_sha256']!=repeated['scene_sha256']or first['manifest_sha256']!=repeated['manifest_sha256']:
                raise ValueError('Typed UV1 exposure is nondeterministic')
            row['typed_uv1']={k:first[k]for k in ('scene_sha256','uv1_meshes','exact_uv0_aliases','source_shader_equivalence')}
            derived_scene=u.load_scene(derived/'scene.json')
            old=folder/'original.mrpv';new=folder/'typed-uv1.mrpv'
            stage_source_scene(scene,old,scene_root=path.parent);stage_source_scene(derived_scene,new,scene_root=derived)
            if old.read_bytes()!=new.read_bytes():raise ValueError('Exposing retained UV1 unexpectedly changed preview output')
            row['typed_uv1_preview_unchanged']=True
        if viewer is not None:
            preview=folder/'source-preview.mrpv';stage_source_scene(scene,preview,scene_root=path.parent)
            repeated=folder/'repeat.mrpv';stage_source_scene(scene,repeated,scene_root=path.parent)
            if preview.read_bytes()!=repeated.read_bytes():raise ValueError('Nondeterministic preview')
            cull=preview_cull(scene);captures=folder/'views'
            capture_views(viewer,preview,captures,cull=cull,provenance=name+' original source | L2 WARN; no native/gameplay promotion')
            views=('front','rear','left','right','top','isometric')
            sheet([captures/(v+'.png')for v in views],folder/'six-views.png',[name+' '+v+' | L2 WARN'for v in views])
            isolated=copy.deepcopy(scene)
            wheel_id=next(n['id']for n in scene['nodes']if n.get('role')=='wheel')
            for node in isolated['nodes']:
                if node['id']!=wheel_id:node['mesh_ids']=[]
            wheel=folder/'wheels.mrpv';stage_source_scene(isolated,wheel,scene_root=path.parent)
            for label,preview_file,view,mode in [('wheel-closeup',wheel,'isometric','original'),('window-closeup',preview,'front','original'),('material-diagnostic',preview,'isometric','material_ids')]:
                if mode=='material_ids':stage_source_scene(scene,folder/'materials.mrpv',scene_root=path.parent,material_mode=mode);preview_file=folder/'materials.mrpv'
                bmp=folder/(label+'.bmp');command=viewer_command(viewer,preview_file,cull=cull,view=view,capture=bmp,provenance='Diagnostic; original source geometry retained')
                if label=='window-closeup':command+=['--zoom','.65']
                from master_rallye.source_scene_preview import capture_startup_info
                subprocess.run(command,check=True,timeout=45,startupinfo=capture_startup_info(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                with Image.open(bmp)as im:im.save(bmp.with_suffix('.png'))
        if inventory(path.parent)!=before[name]:raise ValueError('Protected original scene changed: '+name)
        row['source_files_unchanged']=len(before[name]);(folder/'preflight.json').write_bytes(u.canonical(row))
    result={'schema':'source-garage-corpus-qualification/1','baseline':'c557ed626722aa709384d150647dafd574c45f0a','vehicles':rows,
            'original_scene_files_checked':sum(len(x)for x in before.values()),'new_runtime_slots':0,'gameplay':'NOT TESTED',
            'owner_report_boundary':'Historical owner evidence: Evo2 4Runner playable; Silver launched with stiff suspension; RAV4 loads/drives/body damage/glass pass with wheel fringe and rear lamp defects. Full RAV4 race/Results and corrected candidates remain owner-pending. No new L4 result inferred here.'}
    (output/'qualification.json').write_bytes(u.canonical(result));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--viewer',type=Path)
    a=p.parse_args();r=run(a.output.absolute(),a.viewer.absolute()if a.viewer else None)
    print({name:row['levels']for name,row in r['vehicles'].items()})
