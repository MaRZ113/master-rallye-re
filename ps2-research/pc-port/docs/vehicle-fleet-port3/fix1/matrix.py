from pathlib import Path
import json,re,hashlib
HERE=Path(__file__).resolve().parent
PHASE=HERE.parent;PORT=PHASE.parents[1]
def main():
 coverage=json.loads((PHASE/'coverage.json').read_text())
 profiles=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/race-profiles.json').read_text())['profiles']
 def keys(name):return set(re.findall(r'\{"([^"\n]+)","([0-9a-f]{64})"',(PORT/'renderer'/name).read_text()))
 whole=keys('reflection_pilot.hpp');mixed=keys('vehicle_partition_registry.hpp')|keys('lamp_partition_registry.hpp')
 captures=json.loads((PHASE/'runtime-qualification-11316.json').read_text())['captures']
 off={r['family']:r for r in json.loads((PHASE/'lamp-followup/contracts.json').read_text())['families']}
 for row,source in zip(coverage['vehicles'],profiles):
  assert row['family']==source['family'];name=row['family']
  observed=[{'frame':c['frame'],'proxy':c['proxy_sha256'],'evidence':s} for c in captures for s in c['families'] if s['family']==name]
  row['PORT3_runtime_sidecars']=observed
  if any(s['evidence']['healthy_body_confirmed'] for s in observed):row['CAR']['healthy_runtime']='SIDECAR_SUBMISSION_AND_COMPLETE_SUPPRESSION_CONFIRMED_VISUAL_USER_REPORT_REQUIRED'
  if name=='Ufo':row['CAR']['healthy_runtime']=row['CAR']['damaged_runtime']='USER_RUNTIME_CONFIRMED';row['CAR']['acceptance_evidence']='User report: UFO excellent, collision does not reset model; no new UFO sidecar joined in fix1'
  identities=[s for s in source['pc_sources'] if (name,s['geometry_sha256']) in whole-mixed]
  row['native_damage_reflection_fix1']={'implemented':not row['CAR']['damaged_implemented'] and bool(identities),'whole_source_record_paths':[s['record_path'] for s in identities],'runtime':'PENDING_NEW_DLL','geometry':'NATIVE_DAMAGED_NOT_PS2','mixed_records':'STOCK'}
  if name in off:
   r=off[name];row['lamps']['OFF'].update(source_ready=True,implemented=True,runtime='PRIVATE_PS2_OFF_RUNTIME_PENDING',asset=r['asset'],asset_sha256=r['sha256'],damage='COMPLETE_SOURCE_MAPPING_CURRENT_HEALTHY_OWNER_REFERENCE_REQUIRED')
 coverage['new_fleet_runtime_status']='PARTIAL_USER_AND_SIDECAR_REPORTS_NEW_FIX1_PENDING'
 coverage['fix1_limits']={'full_damage_stock_fallback_families':22,'no_global_brightness_change':True,'no_live_acceptance_claim_for_new_fix':True}
 target=HERE/'coverage.json';target.write_text(json.dumps(coverage,indent=2)+'\n')
 print(json.dumps({'output':str(target),'off_implemented':sum(r['lamps']['OFF']['implemented'] for r in coverage['vehicles']),'native_damage_reflection_families':sum(r['native_damage_reflection_fix1']['implemented'] for r in coverage['vehicles'])}))
if __name__=='__main__':main()
