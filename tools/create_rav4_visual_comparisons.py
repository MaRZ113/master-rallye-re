"""Private A/B/C/D copies of the pinned owner-tested roster; no installation.

Only owned Toyota texture/car resources may differ. Existing launcher services
reseal each derived index; all other resources and native patch bytes are exact.
"""
from pathlib import Path
import argparse,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye import universal_vehicle_scene as u
from master_rallye.michelin_visual_microfix import wheel_resources,lamp_resources
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.preview_scene import logical_cases,stage_vehicle
from collections import Counter
PIN='6789b67963c7c7b68d85de0a8aeda4174364bd19f9781843d360a200f8f8049b'
PREFIX='DataGx/Vehicles/MichelinRav4/'


def intact(raw,glass_case=1):
    model=parse_dx_bytes(raw);cases,_=logical_cases(model);geometry=source_geometry(model);out=Counter()
    for draw in model.physical_draws:
        if draw.draw_index in cases:
            switch,case=cases[draw.draw_index]
            if case!=(glass_case if switch==2 else 1):continue
        part=geometry[draw.draw_index]
        for triangle in part.triangles:
            vertices=tuple((part.vertices[i].position,part.vertices[i].normal,part.vertices[i].color,part.vertices[i].uvs)for i in triangle)
            out[(vertices,draw.texture_tuple,tuple(draw.flags_0x20),draw.unknown_0x24)]+=1
    return out


def verify(bundle, rows):
    for row in rows:
        p=bundle/'resource-root'/u.relative_name(row['path'])
        if p.stat().st_size!=row['size']or u.sha(p.read_bytes())!=row['sha256']:raise ValueError('Derived resource mismatch: '+row['path'])
    return {'status':'PASS_STATIC_COLLECTION_RUNTIME_BUNDLE','runtime_qualified':False}


def run(baseline,scene,output,viewer=None):
    from addon_runtime import _resource_index,canonical_json
    from build_runtime_launcher import build_launcher
    baseline=Path(baseline).absolute();scene=Path(scene).absolute()
    output=u.output_directory(Path(output).absolute(),[baseline,scene.parent])
    allowed=(ROOT/'.research-output/vehicles/cross-game-materials').resolve()
    if not output.is_relative_to(allowed):raise ValueError('RAV4 comparisons must stay in private ignored milestone output')
    if output.exists():raise ValueError('Fresh comparison output required')
    for path in baseline.rglob('*'):u.unlinked(path)
    bundle=baseline/'runtime';index=u.read_bounded(bundle/'resource-index.tsv',1024*1024)
    if u.sha(index)!=PIN:raise ValueError('Original accepted RAV4 index differs')
    manifest=json.loads((bundle/'resource-manifest.json').read_text());rows=manifest['resources']
    verify(bundle,rows)
    assets=bundle/'resource-root'/PREFIX
    wheel,wheel_report=wheel_resources(scene,assets);lamps,lamp_report=lamp_resources(scene,assets)
    if wheel!=wheel_resources(scene,assets)[0]or lamps!=lamp_resources(scene,assets)[0]:raise ValueError('Nondeterministic derivation')
    original=u.read_bounded(assets/'car.dx',u.MAX_OUTPUT_BYTES)
    if intact(original)!=intact(lamps['car.dx']):raise ValueError('Original OFF surface changed')
    if intact(original,2)!=intact(lamps['car.dx'],2):raise ValueError('Original broken glass states changed')
    a=parse_dx_bytes(original);b=parse_dx_bytes(lamps['car.dx'])
    if original[a.trailing.offset:]!=lamps['car.dx'][b.trailing.offset:]:raise ValueError('Collision/bounds changed')
    for name,blob in lamps.items():
        if name.endswith('.dxt'):
            texture=parse_dxt_bytes(blob);allowed=set(lamp_report['coverage']['lit_pixels'])
            if any(texture.bgra[4*i+3] for i in range(texture.width*texture.height)if i not in allowed):raise ValueError('Lamp coverage leak')
    output.mkdir(parents=True);results={}
    for label,changes in [('A',{}),('B',wheel),('C',lamps),('D',{**wheel,**lamps})]:
        folder=output/label;candidate=folder/'candidate'
        shutil.copytree(baseline,candidate)
        current=candidate/'runtime';new_rows=json.loads(json.dumps(rows));lookup={r['path']:r for r in new_rows}
        diffs=[]
        for name,blob in changes.items():
            relative=PREFIX+u.relative_name(name)
            before=lookup.get(relative,{}).get('sha256')
            (current/'resource-root'/relative).write_bytes(blob)
            row=lookup.get(relative)
            if row is None:
                row={'path':relative,'owner':'isolated-rav4-visual-microfix','role':'sdk-roster-resource'};new_rows.append(row)
            row.update(size=len(blob),sha256=u.sha(blob))
            diffs.append({'path':relative,'before':before,'after':row['sha256']})
        if changes:
            idx=_resource_index(new_rows);rm={**manifest,'resources':sorted(new_rows,key=lambda r:r['path']),'resource_count':len(new_rows),'index_sha256':u.sha(idx)}
            rm=canonical_json(rm)
            (current/'resource-index.tsv').write_bytes(idx);(current/'resource-manifest.json').write_bytes(rm)
            profile=json.loads((current/'runtime-profile.json').read_text())
            profile.update(resource_count=len(new_rows),resource_index_sha256=u.sha(idx),resource_manifest_sha256=u.sha(rm))
            (current/'runtime-profile.json').write_bytes(canonical_json(profile))
            artifact=json.loads((current/'runtime-artifact.json').read_text());artifact['resource_manifest_sha256']=u.sha(rm)
            (current/'runtime-artifact.json').write_bytes(canonical_json(artifact))
            # Build in a new folder; copied baseline launcher is never trusted
            # against a new index. Keep it separately as rollback evidence.
            candidate.joinpath('launcher').rename(candidate/'baseline-launcher')
            build_launcher(bundle=current,output=candidate/'launcher',retail_exe=ROOT.parent/'MRallye.exe',bundle_verifier=lambda:verify(current,new_rows))
        checks={}
        for mode in ('--verify','--verify-launch-environment','--self-test-native-allocation'):
            run=subprocess.run([str(candidate/'launcher/mr-runtime-launcher.exe'),mode,str(ROOT.parent/'MRallye.exe'),str(current)],capture_output=True,text=True,timeout=45)
            checks[mode]={'exit':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
            if run.returncode:raise ValueError('Launcher preflight failed: '+mode)
        # Verify exact changes to the sealed resource set, not just new outputs.
        changed_names={d['path']for d in diffs}
        for old in rows:
            if old['path']not in changed_names and u.sha((current/'resource-root'/old['path']).read_bytes())!=old['sha256']:raise ValueError('Unrelated resource changed')
        preview_assets=folder/'preview-assets';shutil.copytree(assets,preview_assets)
        for name,blob in changes.items():(preview_assets/name).write_bytes(blob)
        preview_profile=ROOT/'.research-output/vehicles/michelin-native/final-pilot/converted/assets/preview-profile.json'
        stage_vehicle(preview_assets/'car.dx',folder/'vehicle.mrpv',profile=preview_profile)
        if viewer:
            from master_rallye.source_scene_preview import capture_views
            capture_views(viewer,folder/'vehicle.mrpv',folder/'views',cull='cw',basis='source',model='race',provenance=f'RAV4 {label}: staged MR +Z front; MR authoring comparison, owner D3D8 pending')
        result={'variant':label,'source_scene_sha256':u.sha(scene.read_bytes()),'baseline_resource_index_sha256':PIN,
                'resource_index_sha256':u.sha((current/'resource-index.tsv').read_bytes()),'resource_differences':diffs,
                'preflight':checks,'off_surface_exact':True,'broken_glass_surface_exact':True,'collision_exact':True,
                'gameplay':'OWNER COMPARISON PENDING','roster_capacity':30,'new_runtime_slots':0}
        (folder/'manifest.json').write_bytes(u.canonical(result))
        (candidate/'validation.json').write_bytes(u.canonical(result));results[label]=result
    verify(bundle,rows)
    report={'schema':'rav4-visual-comparison/1','variants':results,'wheel':wheel_report,'lamps':lamp_report,
            'accepted_candidate_unchanged':True,'qualification':'OFFLINE VALIDATED; no corrected D3D8 result claimed'}
    (output/'validation.json').write_bytes(u.canonical(report));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','scene','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--viewer',type=Path);args=p.parse_args()
    print(run(args.baseline,args.scene,args.output,args.viewer)['qualification'])
