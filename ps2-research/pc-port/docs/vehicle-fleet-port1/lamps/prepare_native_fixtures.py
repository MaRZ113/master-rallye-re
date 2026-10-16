"""Ignored original-PC all-record positives/negatives for25 glow identities."""
from pathlib import Path
import struct,json,hashlib,importlib.util
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def main():
 s=importlib.util.spec_from_file_location('fleet_glow_original',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
 old=json.loads((PORT/'docs/vehicle-crew-port1/lamps/source-registry.json').read_text())
 chosen={f['pc_family']:(f['pc_sha256'],m['pc_candidates'][0]['record']) for f in old['families'] for m in f['meshes'] if m['mode']==14 and len(m['pc_candidates'])==1}
 new=json.loads((HERE/'admission-decisions.json').read_text())
 evidence={f['family']:f for f in json.loads((HERE/'missing-source-comparison.json').read_text())['families']}
 names={'FRONTERA':'Frontera','JUMP':'Jump','MATTSERATI':'Mattserati','RMONSTER':'RMonster','TATA':'Tata'}
 for r in new['added_profiles']:chosen[names[r['family']]]=(evidence[r['family']]['pc_sha256'],r['record'])
 assert len(chosen)==25
 cases=[];manifest=[]
 for family,(sha,record) in sorted(chosen.items()):
  path=a.PC/family/'car.dx';assert a.sha(path.read_bytes())==sha
  pc=a.parse_dx(path)
  for n,d in enumerate(pc.physical_draws):
   ids=pc.draw_global_indices(d);first=min(ids);count=max(ids)-first+1
   vb=b''.join(struct.pack('<3f3f2f',*pc.vertices.positions[i],*pc.vertices.normals[i],*pc.uv_sets[0].values[i]) for i in range(first,first+count))
   ib=struct.pack('<%dI'%len(ids),*(i-first for i in ids))
   kind=2 if n==record else 3
   cases.append(struct.pack('<4I',kind,count,len(ids)//3,32)+vb+ib)
   manifest.append({'family':family,'record':n,'glow_expected':kind==2})
 binary=b'PS2LMP01'+struct.pack('<I',len(cases))+b''.join(cases)
 out=PORT/'.assets/vehicles/fleet-port1-native-glow.bin';out.write_bytes(binary)
 summary={'schema':1,'fixture_path':str(out),'bytes':len(binary),'sha256':hashlib.sha256(binary).hexdigest(),'positive_glow':sum(x['glow_expected'] for x in manifest),'negative_original_body_off_on_other':sum(not x['glow_expected'] for x in manifest),'format':'PS2LMP01; kind2=positiveglow, kind3=mustreject; FVF112/stride32; IDX32','runtime_evidence':False,'cases':manifest}
 (HERE/'native-fixture-manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k!='cases'}))
if __name__=='__main__':main()
