"""Build an isolated configurable capacity-core experiment over SDK33.

No launcher, EXE or installed resources are written. --diagnostic-donors is
explicitly a CPU/layout experiment, never a new playable vehicle package.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.capacity_profile import SDK33,validate_profile
import sdk_capacity_native as native
import j2_frontend_reentry as j2


def digest(raw):return hashlib.sha256(raw).hexdigest()


def load_parent(source,root):
    root=Path(root)
    plan=json.loads((root/'addon-plan.json').read_text())
    rp=json.loads((root/'runtime-profile.json').read_text())
    if (plan['registry_layout']['record_count']!=33 or
            plan['selection_layout']['class_to_physical_ids']!=SDK33):
        raise ValueError('Expected the accepted SDK33 physical/class selection mapping')
    ext=rp['native_extension'];blob=(root/'native-extension.bin').read_bytes()
    ops=(root/'native-patch-ops.rvp').read_bytes()
    # These are sealed compiled inputs, not editable artwork. Exact source
    # operation preimages are also checked during reconstruction.
    if (ext['address']!=0x10000000 or ext['size']!=len(blob) or
            ext['sha256']!=digest(blob) or rp['native_patch_operations_sha256']!=digest(ops)):
        raise ValueError('Parent compiled artifact integrity/ownership mismatch')
    _,image,_=j2._parse_and_reconstruct(source,ops)
    return image,blob,rp


def diagnostic_records(profile):
    donors={'T1':('Landcruiser',9),'T2':('Navara',13),'T3':('Wildcat',22)}
    result=[]
    for c,ids in profile['classes'].items():
        if c not in donors:raise ValueError('Diagnostic native templates support only the three original classes')
        for local,i in enumerate(ids):
            if i>=33:
                family,icon=donors[c]
                result.append(replace(native.registry.ID26_DONOR_CLEANUP,slot_id=i,
                    vehicle_class=int(c[1:])-1,local_index=local,internal_name=family,
                    smallcarsheet_index=icon))
    return result


def build(source_path,parent,profile_path,out,*,records_path=None,diagnostic_donors=False,player_state=None,saved_roster=None):
    start=time.perf_counter();source_path=Path(source_path);parent=Path(parent);out=Path(out)
    profile=validate_profile(json.loads(Path(profile_path).read_text()))
    if out.exists():raise ValueError('Use a fresh output directory')
    if not out.resolve().is_relative_to((ROOT/'.research-output/vehicles/v-cap').resolve()):
        raise ValueError('Capacity experiments stay inside this worktree .research-output/vehicles/v-cap')
    source=source_path.read_bytes();before=digest(source)
    image,blob,rp=load_parent(source,parent)
    if records_path is not None:
        if diagnostic_donors:raise ValueError('Choose authored records OR diagnostic donors')
        rows=json.loads(Path(records_path).read_text());records=[native._profile(row) for row in rows]
    elif diagnostic_donors:records=diagnostic_records(profile)
    elif profile['record_count']==33:records=[]
    else:raise ValueError('Supply resolved addon records or explicitly select --diagnostic-donors')
    result,extension,report=native.extend_capacity_profile(source,image,blob,profile,records,
        parent_allocation_size=rp['native_extension']['allocation_size'])
    from master_rallye.addon_sdk.roster_identity import catalog,preflight_player_state,preserve_reservations
    historical=json.loads((ROOT/'research/r5v_a/final-vehicle-registry.json').read_text())
    names={e['registry_index']:e['internal_name'] for e in historical['canonical_registry']}
    names[25]='Trooper' # accepted SDK33 full initializer; retail record25 was unnamed
    parent_plan=json.loads((parent/'addon-plan.json').read_text())
    names.update({r['physical_id']:r['identity']['runtime_family'] for r in parent_plan['addons']})
    namespace='master-rallye-vcap-diagnostic' if diagnostic_donors else 'master-rallye-retail-sdk33'
    baseline=catalog([{'physical_id':i,'family':names[i],'vehicle_class':c,'retired':False} for c,ids in SDK33.items() for i in ids],namespace)
    names.update({r.slot_id:r.internal_name for r in records})
    identity=catalog([{'physical_id':i,'family':names[i],'vehicle_class':c,'retired':False} for c,ids in profile['classes'].items() for i in ids],namespace)
    previous=json.loads(Path(saved_roster).read_text()) if saved_roster else baseline
    preserve_reservations(previous,identity)
    if player_state:report['player_state_preflight']=preflight_player_state(Path(player_state).read_bytes(),previous,identity)
    report.update(source={'path':str(source_path.resolve()),'sha256':before,'bytes':len(source)},
        parent={'path':str(parent.resolve()),'image_sha256':digest(image),'extension_sha256':digest(blob),
                'extension_bytes':len(blob),'allocation_bytes':rp['native_extension']['allocation_size'],
                'writable_ranges_preserved':rp['native_extension'].get('writable_ranges',[])},
        reconstructed_virtual_image_sha256=digest(result),
        diagnostic_donors=diagnostic_donors,
        native_extension={'address':0x10000000,'bytes':len(extension),'sha256':digest(extension)},
        stock_network={'selectedCar_bits':8,'maximum_encodable_physical_id':255,
                       'all_profile_ids_encodable':profile['record_count']<=256,
                       'id255_sentinel_policy_requires_review':profile['record_count']>=256,'runtime_qualified':False},
        extra_options={'per_player_car_array_capacity':256,'requires_capacity_query_ABI':True},
        seconds=time.perf_counter()-start)
    # No patched PE is emitted, and this schema cannot masquerade as an
    # admitted runtime-profile.json / RVP package.
    out.mkdir(parents=True)
    (out/'capacity-extension.bin').write_bytes(extension)
    (out/'roster-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    (out/'capacity-core.json').write_text(json.dumps(report,indent=2)+'\n')
    assert source_path.read_bytes()==source
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--records',type=Path);p.add_argument('--diagnostic-donors',action='store_true')
    p.add_argument('--player-state',type=Path);p.add_argument('--saved-roster',type=Path)
    a=p.parse_args();r=build(a.source,a.parent,a.profile,a.output,records_path=a.records,diagnostic_donors=a.diagnostic_donors,player_state=a.player_state,saved_roster=a.saved_roster)
    print(json.dumps({k:r[k] for k in ('status','runtime_installable','extension_size','private_allocation_size','seconds')}))


if __name__=='__main__':main()
