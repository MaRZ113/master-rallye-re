from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
def generate():
 d=json.loads((HERE/'source-registry.json').read_text());rows=[]
 for f in d['families']:
  if f['status']!='SOURCE_ADMITTED':continue
  p=f['profile'];assert not any(p['geometry']==n['geometry'] and p['positionUv']==n['positionUv'] for n in f['negative_sources'])
  rows.append((f['family'],p['vertices'],p['faces'],p['geometry'],p['positionUv']))
 assert len(rows)==21 and len({r[3:] for r in rows})==21
 text='#pragma once\nnamespace gfx2::ps2port {\nstruct FleetOffLampProfile { const char* family; unsigned vertices,triangles; const char* geometry; const char* positionUv; };\ninline constexpr FleetOffLampProfile kFleetOffLampProfiles[]={\n'+''.join(' {"%s",%du,%du,"%s","%s"},\n'%r for r in rows)+'};\n}\n'
 (HERE/'fleet_off_lamp_registry_draft.hpp').write_text(text);print('21exactOFFprofiles;18newplusKia/Xtrail/Terrano; noON/glowidentitycollisions')
 return text
if __name__=='__main__':generate()
