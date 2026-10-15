from pathlib import Path
import struct,json,collections,hashlib
H=Path(__file__).resolve().parent; P=H.parents[2]
b=(P/'.assets/vehicles/XTRAIL-CAR.ps2model').read_bytes();magic,ver,jl,nm,nv,ni,nt,sha=struct.unpack_from('<8s6I32s',b);at=64+jl
meta=json.loads(b[64:at]); meshes=[struct.unpack_from('<7I',b,at+i*28) for i in range(nm)];at+=nm*28
v=[struct.unpack_from('<3f3fI2f',b,at+i*36) for i in range(nv)];at+=nv*36
ix=struct.unpack_from('<%dI'%ni,b,at)
out={}
for root in (0,7,8):
 m=meshes[root]; faces=[ix[m[5]+i:m[5]+i+3] for i in range(0,m[6],3)]
 # Coincident XYZ seams joined exactly; no spatial threshold.
 pointfaces=collections.defaultdict(list)
 for i,f in enumerate(faces):
  for j in f:pointfaces[v[j][:3]].append(i)
 todo=set(range(len(faces)));cs=[]
 while todo:
  seed=min(todo);q=[seed];todo.remove(seed);c=[]
  while q:
   i=q.pop();c.append(i)
   for j in faces[i]:
    for k in pointfaces[v[j][:3]]:
     if k in todo:todo.remove(k);q.append(k)
  ids=sorted(set(j for i in c for j in faces[i]));positions=[v[j][:3] for j in ids];uvs=[v[j][7:] for j in ids]
  cs.append({'seed_face':seed,'faces':sorted(c),'face_count':len(c),'vertices':len(ids),'bounds':[[min(p[a] for p in positions) for a in range(3)],[max(p[a] for p in positions) for a in range(3)]],'uv_bounds':[[min(p[a] for p in uvs) for a in range(2)],[max(p[a] for p in uvs) for a in range(2)]],'index_sha256':hashlib.sha256(struct.pack('<%dI'%(len(c)*3),*(j for i in sorted(c) for j in faces[i]))).hexdigest()})
 out[str(root)]={'material':meta['meshes'][root]['material'],'components':cs}
H.joinpath('components.json').write_text(json.dumps(out,indent=2)+'\n')
for r,row in out.items():
 print(r,row['material'])
 for c in row['components']:print(c['seed_face'],c['face_count'],c['bounds'],c['uv_bounds'])
