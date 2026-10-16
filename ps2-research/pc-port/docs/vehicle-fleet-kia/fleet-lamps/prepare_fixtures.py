"""Original native source fixtures, local ignored only; never ship proprietary bytes."""
from pathlib import Path
import importlib.util,json,struct,hashlib
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def main():
 s=importlib.util.spec_from_file_location('native_off_fleet',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
 data=json.loads((HERE/'source-registry.json').read_text());cases=[];manifest=[]
 for f in data['families']:
  path=a.PC/f['family']/'car.dx';assert a.sha(path.read_bytes())==f['pc_sha256'];pc=a.parse_dx(path)
  for n,d in enumerate(pc.physical_draws):
   ids=pc.draw_global_indices(d);first=min(ids);count=max(ids)-first+1
   vb=b''.join(struct.pack('<3f3fI2f',*pc.vertices.positions[i],*pc.vertices.normals[i],0xffffffff,*pc.uv_sets[0].values[i]) for i in range(first,first+count));ib=struct.pack('<%dI'%len(ids),*(i-first for i in ids))
   positive=f.get('profile',{}).get('record')==n;kind=0 if positive else 3
   cases.append(struct.pack('<4I',kind,count,len(ids)//3,36)+vb+ib);manifest.append({'family':f['family'],'record':n,'expected_off':positive})
 binary=b'PS2LMP01'+struct.pack('<I',len(cases))+b''.join(cases);out=PORT/'.assets/vehicles/fleet-off-lamp-native.bin';out.write_bytes(binary)
 doc={'sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'cases':manifest,'positive':sum(x['expected_off'] for x in manifest),'negative':sum(not x['expected_off'] for x in manifest),'path':str(out),'format':'PS2LMP01 kind0=OFFpositive kind3=negative; FVF152/36 IDX32','live_upload':False};(HERE/'fixture-manifest.json').write_text(json.dumps(doc,indent=2)+'\n');print({k:v for k,v in doc.items() if k!='cases'})
if __name__=='__main__':main()
