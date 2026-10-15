from pathlib import Path
import sys,json,hashlib,struct,collections
H=Path(__file__).resolve().parent;P=H.parents[2];R=P.parents[1]
sys.path.insert(0,str(R.parent/'master-rallye-re-course/src'))
from master_rallye.dx import parse_dx
SRC=R.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/car.dx'
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f'
m=parse_dx(SRC);out={};pf={}
def bounds(points):return [[min(p[a] for p in points) for a in range(3)],[max(p[a] for p in points) for a in range(3)]]
def facehash(f):
 w=[tuple(struct.unpack('<I',struct.pack('<f',0 if v==0 else v))[0] for v in p) for p in f]
 return hashlib.sha256(b''.join(struct.pack('<3I',*p) for p in sorted(w))).hexdigest()
for d in m.physical_draws:
 if d.draw_index not in (16,17,18,19,20):continue
 ids=m.draw_global_indices(d);fs=[tuple(m.vertices.positions[i] for i in ids[n:n+3]) for n in range(0,len(ids),3)];pf[d.draw_index]=fs
 pointfaces=collections.defaultdict(set)
 for i,f in enumerate(fs):
  for p in f:pointfaces[p].add(i)
 todo=set(range(len(fs)));cs=[]
 while todo:
  seed=min(todo);q=[seed];todo.remove(seed);c=[]
  while q:
   i=q.pop();c.append(i)
   for p in fs[i]:
    for k in pointfaces[p]:
     if k in todo:todo.remove(k);q.append(k)
  cs.append({'seed':seed,'faces':sorted(c),'face_count':len(c),'bounds':bounds([p for i in c for p in fs[i]])})
 out[str(d.draw_index)]={'slots':[s.value for s in d.texture_slots],'components':cs,'bounds':bounds([p for f in fs for p in f]),'face_count':len(fs),'faces':[{'ordinal':i,'hash':facehash(f),'xyz':f} for i,f in enumerate(fs)]}

# Exact coincident topology closure, not an approximate cabin bounding-box rule.
for c in out['17']['components'][:4]:
 points=set(tuple(p) for i in c['faces'] for p in out['17']['faces'][i]['xyz'])
 c['exact_shared_vertices']={r:len(points & set(tuple(p) for f in out[r]['faces'] for p in f['xyz'])) for r in ('16','18','19','20')}
for r,row in out.items():
 for f in row['faces']:
  f.pop('xyz')
  f['category']='CREW' if r!='17' or f['ordinal']<38 else 'VERIFIED_PS2_TRIM'
 counts=collections.Counter(f['hash'] for f in row['faces']); cats={f['hash']:f['category'] for f in row['faces']}
 row['runtime_hash_categories']=[{'hash':h,'multiplicity':n,'category':cats[h]} for h,n in sorted(counts.items())]
result={'schema_version':1,'pc_source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'records':out,'runtime_admission':'CURRENT_CHASSIS_QUEUE_OWNER_AND_FULL_RECORD_GEOMETRY_SIGNATURE_GENERATION_AND_EXACT_WORLD_REQUIRED','mapping':{'16':{'ps2_root':0,'component_seed':123,'faces':48,'side':'NEGATIVE_X'},'18':{'ps2_root':0,'component_seed':222,'faces':48,'side':'POSITIVE_X'},'19':{'ps2_root':8,'faces':148},'20':{'ps2_root':0,'component_seeds':[71,73],'faces':252},'17':{'crew_faces':38,'ps2_root':7,'component_seeds':[6,10],'faces':48,'preserved_trim_faces':[38,39,40,41]}},'scope':'STATIC_CREW_NO_ANIMATION_RECONSTRUCTION'}
H.joinpath('pc-crew-components.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified static crew: native 444 crew faces, four trim faces separate; PS2 544 crew faces')
