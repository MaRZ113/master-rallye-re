"""Private-input reproducible V-SDK4C.1 resource ownership audit (no game launch)."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
from master_rallye.addon_sdk.texture_budget import texture_working_set,simulate_texture_cache
from addon_runtime import RUNTIME_STATE_PATHS


def run():
    root=ROOT/'.research-output/vehicles/vsdk4c1';base=ROOT/'.research-output/vehicles/vpajero3/candidate-final/runtime';oldglass=ROOT/'.research-output/vehicles/vsdk4c/candidate-glass/runtime';reports={}
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    def index(folder):return {f.relative_to(folder).as_posix():sha(f) for f in folder.rglob('*') if f.is_file() and f.relative_to(folder).as_posix().casefold() not in RUNTIME_STATE_PATHS}
    for name,before,after,prefix in [('pajero',base,root/'candidate-pajero-final/runtime','DataGx/Vehicles/SdkPajero85/'),('subaru',oldglass,root/'candidate-subaru/runtime','DataGx/Vehicles/ImprezaProto/')]:
        a=index(before/'resource-root');b=index(after/'resource-root');changed=[p for p in sorted(set(a)|set(b)) if a.get(p)!=b.get(p)]
        assert all(p.startswith(prefix) for p in changed),changed
        if name=='subaru':assert changed==[prefix+'car.dx']
        else:
            assert a[prefix+'wheel.dx']==b[prefix+'wheel.dx']
            for p in changed:assert p in (prefix+'car.dx',prefix+'complete.dx') or p not in a,p
        for model in ['car.dx','complete.dx']:
            ar=(before/'resource-root'/prefix/model).read_bytes();br=(after/'resource-root'/prefix/model).read_bytes();x,y=map(parse_dx_bytes,(ar,br))
            assert ar[x.trailing.offset:]==br[y.trailing.offset:]
        metadata={n:(before/n).read_bytes()==(after/n).read_bytes() for n in ['addon-plan.json','native-extension.bin','native-patch-ops.rvp']}
        if name=='subaru':assert all(metadata.values())
        reports[name]={'status':'PASS_EXACT_RESOURCE_OWNERSHIP','resources':len(b),'changed_resources':changed,'outside_vehicle_identical':True,'collision_suffixes_identical':True,'metadata_byte_identity':metadata,'gameplay_qualified':False,'excluded_user_state':sorted(RUNTIME_STATE_PATHS)}
    reports['protected']={}
    for name,expected in [('MRallye.exe','bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'),('d3d8.dll','eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4')]:
        h=sha(ROOT.parent/name);assert h==expected;reports['protected'][name]=h
    reports['texture_budget']={label:texture_working_set(folder/'resource-root/DataGx/Vehicles/SdkPajero85')['cache_bytes'] for label,folder in [('before',base),('after',root/'candidate-pajero-final/runtime')]}
    sizes={};sequence=[]
    for family in ['Mercedes','ImprezaProto','LancerEvo4','SdkPajero85']:
        r=texture_working_set(root/'candidate-pajero-final/runtime/resource-root/DataGx/Vehicles'/family)
        for stem,t in r['textures'].items():sizes[family+'/'+stem]=t['cache_bytes']
        sequence += [family+'/'+s for s in r['models']['car.dx']['request_sequence']]
    sizes['synthetic-world-ui-reserve']=8*1024*1024
    reports['roster_lru_prediction']={'boundary':'synthetic 8MiB reserve; serialized bindings, not actual draw order or measured FPS','cache':simulate_texture_cache(sizes,['synthetic-world-ui-reserve']+sequence)}
    (root/'candidate-preservation.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps({'texture_budget':reports['texture_budget'],'lru':reports['roster_lru_prediction']},indent=2))


if __name__=='__main__':run()
