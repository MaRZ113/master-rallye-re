"""Ignored original Kia conditional material fixtures, never shipped evidence bytes."""
from pathlib import Path
import json,struct,importlib.util,hashlib
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
def main():
 s=importlib.util.spec_from_file_location('kia_native_lamp',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
 evidence=json.loads((HERE/'source-runtime.json').read_text());path=a.PC/'KiaSportage/car.dx';assert a.sha(path.read_bytes())==evidence['pc_sha256'];pc=a.parse_dx(path)
 cases=[]
 for kind,record,stride in ((0,30,36),(1,31,20),(2,32,20)):
  d=pc.physical_draws[record];ids=pc.draw_global_indices(d);first=min(ids);count=max(ids)-first+1
  vb=b''.join(struct.pack('<3f',*pc.vertices.positions[i])+(struct.pack('<3fI',*pc.vertices.normals[i],0xffffffff) if stride==36 else b'')+struct.pack('<2f',*pc.uv_sets[0].values[i]) for i in range(first,first+count))
  ib=struct.pack('<%dI'%len(ids),*(i-first for i in ids));cases.append(struct.pack('<4I',kind,count,len(ids)//3,stride)+vb+ib)
 binary=b'PS2LMP01'+struct.pack('<I',3)+b''.join(cases);out=PORT/'.assets/vehicles/kia-off-on-glow-native.bin';out.write_bytes(binary)
 manifest={'path':str(out),'bytes':len(binary),'sha256':hashlib.sha256(binary).hexdigest(),'cases':['OFF FVF152/36 mustreflect','ON FVF102/20 mustnotreflect','glow FVF102/20 mustnotreflect'],'live_uploaded_bytes':False}
 (HERE/'fixture-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(manifest)
if __name__=='__main__':main()
