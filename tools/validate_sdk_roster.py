"""Reproduce a roster and prove immutable family/UI/physics resource ownership."""
import argparse,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from build_sdk_roster import derive,verify
import prepare_sdk_capacity_probe as probe
import addon_runtime as runtime
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank
from master_rallye.addon_sdk.texture_budget import texture_working_set,simulate_texture_cache,RETAIL_TEXTURE_CACHE_BYTES

SHARED={'DataGame/vehicles.xml','DataGame/Modifications.xml','DataScene/FrontendScreens/VehicleSelect.xml',*(p+'.dxb' for p,_,_,_ in BANKS.values())}

def validate(config,candidate):
    ctx=derive(config);result=verify(candidate/'runtime',ctx);base=Path(config['base_runtime'])/'resource-root';target=candidate/'runtime/resource-root'
    preserved=[]
    for p in base.rglob('*'):
        if not p.is_file():continue
        name=p.relative_to(base).as_posix()
        if name in SHARED or name.casefold() in runtime.RUNTIME_STATE_PATHS or runtime.is_user_editable_resource(name):continue
        if p.read_bytes()!=(target/name).read_bytes():raise ValueError('frozen base resource changed: '+name)
        preserved.append(name)
    bank_checks={}
    for role,(prefix,_,_,_) in BANKS.items():
        before=parse_bank((base/(prefix+'.dxb')).read_bytes());after=parse_bank((target/(prefix+'.dxb')).read_bytes())
        if after['records'][:before['count']]!=before['records']:raise ValueError('existing UI record changed')
        bank_checks[role]={'preserved_records':before['count'],'new_count':after['count']}
    xml_checks={}
    for name in ('DataGame/vehicles.xml','DataGame/Modifications.xml'):
        def values(p):return {n.get('Name'):dict(n.attrib) for n in ET.fromstring(p.read_bytes().decode('utf-8-sig')).iter('Value')}
        before=values(base/name);after=values(target/name)
        if any(after.get(k)!=v for k,v in before.items()):raise ValueError('existing physics value changed')
        xml_checks[name]={'unchanged_values':len(before),'added_values':len(after)-len(before)}
    budgets={};sizes={};sequence=['<world-ui-reserve>'];reserve=8*1024*1024;sizes[sequence[0]]=reserve
    for row in json.loads(ctx['files']['addon-plan.json'])['addons']:
        family=row['assets']['model_package_root'];report=texture_working_set(target/family);budgets[row['addon_id']]={k:report[k] for k in ('cache_bytes','unique_textures')}
        for stem,detail in report['textures'].items():sizes[family+'/'+stem]=detail['cache_bytes']
        sequence += [family+'/'+s for m in ('car.dx','wheel.dx') for s in report['models'][m]['request_sequence']]
    lru=simulate_texture_cache(sizes,sequence)
    return {**result,'preserved_base_resources':len(preserved),'existing_ui':bank_checks,'physics_values':xml_checks,
        'family_texture_budgets':budgets,'combined_vehicle_race_prediction':{'native_cache_bytes':RETAIL_TEXTURE_CACHE_BYTES,'synthetic_world_ui_reserve_bytes':reserve,'frames':lru,'boundary':'one of each addon family, serialized binding order and an explicit synthetic 8 MiB reserve; not live MR ordering or measured FPS'},
        'boundary':'source-reproduced resource/native package validation, no actual player/AI gameplay or device mixing proof'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('new evidence path required')
    r=validate(json.loads(a.config.read_text()),a.candidate);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
