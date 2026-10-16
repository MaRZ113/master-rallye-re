"""Extend exact native identities without relaxing the legacy PS2 geometry join."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def generate():
 old=(PORT/'renderer/brake_glow_registry.hpp').read_text()
 # This phase always derives the first20 from their original source generator.
 import importlib.util
 s=importlib.util.spec_from_file_location('legacy_glow_registry',PORT/'docs/vehicle-crew-port1/lamps/generate_runtime_registry.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 old=m.generate()
 evidence=json.loads((HERE/'missing-source-comparison.json').read_text())
 rows=[]
 for family in evidence['families']:
  glow=[x for x in family['meshes'] if x['mode']==14]
  if len(glow)!=1:raise ValueError('Ambiguous authored glow')
  mesh=glow[0]
  candidates=[c for c in mesh['pc_candidates'] if c['exact_uv_triangle_multiset'] and c['max_uv_error']==0 and c['ordered_texture_slots'] in (['breaklightsonglow-tga','Null','Null'],['breaklightsonglow-tga','perspex-tga','Null'])]
  if len(candidates)!=1:raise ValueError('Ambiguous original native glow source')
  c=candidates[0]
  # Deliberately not using PS2 XYZ as a tolerance-based runtime match.
  # The native profile hashes exact PC XYZ+UV. The authored shape difference is reported.
  rows.append({'family':family['family'],'record':c['record'],'vertices':c['vertices'],'triangles':mesh['faces'],'geometry':c['geometry_sha256'],'positionUv':c['position_uv_corner_sha256'],'ps2_path':mesh['path'],'ps2_mode':14,'original_pc_geometry_retained':True,'max_original_xyz_difference':c['max_position_error'],'runtime_validation':'PENDING_USER_BRAKE_OFF_ON'})
 assert len(rows)==5 and len({r['positionUv'] for r in rows})==5
 names={'FRONTERA':'Frontera','JUMP':'Jump','MATTSERATI':'Mattserati','RMONSTER':'RMonster','TATA':'Tata'}
 extra=''.join(' {"%s",%du,%du,"%s","%s"},\n'%(names[r['family']],r['vertices'],r['triangles'],r['geometry'],r['positionUv']) for r in rows)
 result=old.replace('};\n}\n',extra+'};\n}\n')
 assert result.count(' {"')==25
 (HERE/'brake_glow_registry_draft.hpp').write_text(result)
 (HERE/'admission-decisions.json').write_text(json.dumps({'schema':1,'legacy_profiles':20,'added_profiles':rows,'runtime_geometry_policy':'EXACT_NATIVE_PC_GEOMETRY_AND_UV_HASHES; NO_POSITION_TOLERANCE','new_ps2_geometry_replacement':False},indent=2)+'\n')
 print('Generated25 exact native identities; old20 preserved; five native-shape revisions explicit.')
 return result
if __name__=='__main__':generate()
