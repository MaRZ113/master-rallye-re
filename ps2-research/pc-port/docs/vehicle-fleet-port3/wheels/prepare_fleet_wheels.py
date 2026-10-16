"""Reproducible fleet wheel export using the accepted Kia lossless converter.
Output remains private; this never grants native runtime ownership.
"""
from pathlib import Path
import json, re
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def main():
 original=(PORT/'docs/vehicle-fleet-kia/wheels/convert.py').read_text()
 fleet=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/fleet-car-contracts.json').read_text())['fleet']
 manifest=[]; headers=['#pragma once','#include "race_fleet_registry.hpp"','namespace gfx2::ps2port {']
 for f in fleet:
  family=f.get('pc_family'); ps2=f['ps2_family']; wc=f.get('wheel_contract',{})
  if not family or family=='forklift':continue
  if family=='Ufo':
   manifest.append(dict(family=family,status='NO_WHEELS_AUTHORED_USER_CONFIRMED_DESIGN',native_sources=[]));continue
  target=HERE/family;target.mkdir(exist_ok=True)
  s=original.replace("HERE=Path(__file__).resolve().parent;PORT=HERE.parents[2]",'HERE=TARGET;PORT=PORT_ROOT')
  s=s.replace("=='KiaSportage'",'==FAMILY').replace("family='KiaSportage'",'family=FAMILY')
  s=s.replace("'\\\\TNG\\\\DATAPSM\\\\VEHICLES\\\\KIASPORTAGE\\\\WHEEL.PSM'", "'\\\\TNG\\\\DATAPSM\\\\VEHICLES\\\\'+PS2_FAMILY+'\\\\WHEEL.PSM'")
  s=s.replace("p.PC/'KiaSportage/wheel.dx'", "p.PC/(FAMILY+'/wheel.dx')")
  s=s.replace("PORT/'.assets/vehicles/KIASPORTAGE-WHEEL-FLEET.ps2model'", "PORT/('.assets/vehicles/port3-'+PS2_FAMILY+'-WHEEL-FLEET.ps2model')")
  s=s.replace('ALL_FOUR_CURRENT_OWNED_PC_WHEEL_SOURCES_ATOMICALLY; WHOLE_PRIVATE_WHEEL_ONCE','ALL_ACTUAL_SOURCE_RECORDS_PER_CURRENT_NATIVE_WHEEL_OWNER_ATOMICALLY; NO_ASSUMED_OWNER_COUNT')
  s=s.replace("contract=p.r.material_contract(m['material'],next((s['name'] for s in m['textures'] if s['slot']==1),''))", "contract=p.mesh_row(scene,m)['contract'];contract['mode']=p.mesh_row(scene,m)['mode']")
  s=s.replace('kKiaWheel','kPort3'+re.sub('[^A-Za-z0-9]','',family)+'Wheel')
  s=s.replace('"KiaSportage","KIASPORTAGE"','"'+family+'","'+ps2+'"')
  s=s.replace('4u,4u,',str(len(wc['native_sources']))+'u,'+str(len(wc['native_sources']))+'u,')
  s=s.replace("struct.pack('<I',4)","struct.pack('<I',len(wc['native_sources']))")
  s=s.replace("PORT/'.assets/vehicles/kia-wheel-fixtures.bin'","PORT/('.assets/vehicles/port3-'+PS2_FAMILY+'-wheel-fixtures.bin')")
  env=dict(__name__='fleet_wheel_export',TARGET=target,PORT_ROOT=PORT,FAMILY=family,PS2_FAMILY=ps2)
  try:
   exec(compile(s,str(PORT/'docs/vehicle-fleet-kia/wheels/convert.py'),'exec'),env);env['convert']()
   row=json.loads((target/'contract.json').read_text());row['status']='SOURCE_READY_NATIVE_OWNER_QUALIFICATION_REQUIRED'
   row['native_source_count']=len(row['native_sources']);row['native_wheel_owner_count']=None
   row['pivot_bounds_equal']=row['ps2_bounds']==row['pc_bounds']
   (target/'contract.json').write_text(json.dumps(row,indent=2)+'\n')
   h=(target/'kia_wheel_registry.hpp').read_text();headers+=h.splitlines()[3:-1]
   manifest.append(row)
  except Exception as e:manifest.append(dict(family=family,status='SOURCE_BLOCKED',reason=str(e)))
 headers+=['inline constexpr const FleetRaceProfile* kPort3WheelProfiles[]={']
 headers += [' &kPort3'+re.sub('[^A-Za-z0-9]','',x['family'])+'WheelProfile,' for x in manifest if x['status']=='SOURCE_READY_NATIVE_OWNER_QUALIFICATION_REQUIRED']
 headers+=['};','}'];(HERE/'fleet_wheel_registry.hpp').write_text('\n'.join(headers)+'\n')
 (HERE/'manifest.json').write_text(json.dumps(dict(schema_version=1,fleet=manifest),indent=2)+'\n')
 print([(x.get('family'),x['status'],x.get('native_source_count'),x.get('reason')) for x in manifest])
if __name__=='__main__':main()
