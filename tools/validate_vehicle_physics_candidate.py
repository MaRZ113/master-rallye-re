"""Prove a physics revision changes only its explicit independent XML fields.

This comparison complements, and does not replace, the sealed launcher checks.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.physics_profile import apply_profile,validate_player_defaults
from master_rallye.addon_sdk.manifest import read_json

MUTABLE={'datagame/options.xml','datagame/options.xml#','datagame/playerstate.xml','datagame/playerstate.xml#'}
def validate(baseline,candidate,profile,exe=None):
    before=baseline/'resource-root';after=candidate/'resource-root'
    def tree(root):return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix().casefold() not in MUTABLE}
    a,b=tree(before),tree(after)
    if set(a)!=set(b):raise ValueError('physics revision changed the immutable resource set')
    checked=[];deltas={};xmls={}
    for name in sorted(a):
        old,new=a[name].read_bytes(),b[name].read_bytes()
        if name in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
            expected,detail=apply_profile(old,profile,donor_family=profile['donor_family'],runtime_family=profile['runtime_family'],source_label=name)
            if new!=expected:raise ValueError('physics XML differs outside declared typed edits: '+name)
            deltas[name]=detail;xmls[name]=new
        elif name.endswith('/'+profile['runtime_family']+'/car.dx') and profile.get('collision_fit'):
            from master_rallye.addon_sdk.physics_collision import fit_collision
            expected,collision=fit_collision(old,profile['collision_fit'])
            if new!=expected:raise ValueError('collision differs outside declared source-pinned affine fit')
        elif old!=new:raise ValueError('visual/stock/UI resource changed: '+name)
        checked.append({'path':name,'sha256':hashlib.sha256(new).hexdigest(),'identical_bytes':old==new})
    validate_player_defaults(xmls['DataGame/vehicles.xml'],xmls['DataGame/Modifications.xml'],profile['runtime_family'],profile.get('ride_height_reference_m'))
    # No capacity, identity, native algorithm or alpha-ownership changes.
    for name in ('addon-plan.json','frontend-overlay.plan.json'):
        if (baseline/name).read_bytes()!=(candidate/name).read_bytes():raise ValueError('native/runtime behavior changed: '+name)
    reference=None
    if profile.get('ride_height_reference_m'):
        import j2_frontend_reentry as j2
        from vehicle_physics_native import append_reference
        exe=exe or ROOT.parent/'MRallye.exe';retail=exe.read_bytes()
        oldimage=j2._parse_and_reconstruct(retail,(baseline/'native-patch-ops.rvp').read_bytes())[1]
        newimage=j2._parse_and_reconstruct(retail,(candidate/'native-patch-ops.rvp').read_bytes())[1]
        rp=json.loads((baseline/'runtime-profile.json').read_text());ext=rp['native_extension']
        expected,blob,reference=append_reference(retail,oldimage,(baseline/'native-extension.bin').read_bytes(),ext['address'],[profile],ext['allocation_size'])
        if newimage!=expected or blob!=(candidate/'native-extension.bin').read_bytes():raise ValueError('native change differs from exact family ride-reference adapter')
        expected_policy=json.loads((baseline/'damage-alpha-policy.json').read_text())
        expected_policy['ride_height_reference']={k:v for k,v in reference.items() if k!='operations'}
        path=expected_policy['resource_path'];expected_policy['model_sha256']=hashlib.sha256((after/path).read_bytes()).hexdigest()
        if expected_policy!=json.loads((candidate/'damage-alpha-policy.json').read_text()):raise ValueError('native damage policy changed outside reference metadata/model hash')
    else:
        for name in ('native-patch-ops.rvp','native-extension.bin','damage-alpha-policy.json'):
            if (baseline/name).read_bytes()!=(candidate/name).read_bytes():raise ValueError('native/runtime behavior changed: '+name)
    return {'status':'PASS_DECLARED_PHYSICS_REVISION','runtime_qualified':False,'immutable_resource_count':len(checked),'byte_identical_resources':sum(x['identical_bytes'] for x in checked),'resources':checked,'physics_edits':deltas,'native_change':reference,'existing_native_code_unchanged':True,'boundary':'offline resource and exact code comparison; no gameplay qualification'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();profile,_=read_json(a.profile)
    r=validate(a.baseline,a.candidate,profile);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('status','immutable_resource_count','byte_identical_resources')}))
