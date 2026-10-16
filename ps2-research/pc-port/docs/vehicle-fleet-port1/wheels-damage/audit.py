"""Source-only exact wheel partition audit. Never grants runtime admission."""
from pathlib import Path
import collections, importlib.util, json, struct
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('fleet_source',PORT/'docs/vehicle-continuity2/fleet-car/prepare_contracts.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
spec=importlib.util.spec_from_file_location('wheel_source',PORT/'docs/vehicle-race-model-port1/wheel-port/convert_wheel.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
def audit():
 corpus=json.loads((PORT/'docs/vehicle-continuity2/fleet-car/fleet-car-contracts.json').read_text())
 p.r.w.verify_inputs(p.PS2)
 pack,_=p.t.load_pak(p.PS2/'TNG.PAK'); entries={p.t.logical_path(e['path']).upper():e for e in pack['entries'] if e['kind']=='file'}
 rows=[]
 for f in corpus['fleet']:
  if 'native_sources' not in f: continue
  wc=f['wheel_contract']; row=dict(pc_family=f['pc_family'],ps2_family=f['ps2_family'],native_wheel_records=len(wc.get('native_sources',[])),ps2_wheel_meshes=len(wc.get('source_meshes',[])),runtime='KEEP_NATIVE_IN_THIS_FLEET_PHASE',damage='WHOLE_CHASSIS_STOCK_IF_ANY_CURRENT_SOURCE_CERTIFICATE_FAILS; XTRAIL_SEPARATE_PROVEN_PATH')
  if 'source_ps2_sha256' not in wc: row['source_partition']='NO_PAIRED_WHEEL_RESOURCE';rows.append(row);continue
  row.update(source_ps2_sha256=wc['source_ps2_sha256'],source_pc_sha256=wc['source_pc_sha256'])
  raw,_=p.t.read_payload(entries[p.t.logical_path('\\TNG\\DATAPSM\\VEHICLES\\'+f['ps2_family']+'\\WHEEL.PSM').upper()],p.PS2/'TNG.000')
  if p.sha(raw)!=wc['source_ps2_sha256']:raise ValueError('PS2 wheel drift')
  scene,_=p.wheel_reader.decode_complete(raw); verts=raw[32:32+scene.vertex_count*52]; pts=[struct.unpack_from('<3f',verts,i*52+36) for i in range(scene.vertex_count)]
  source=collections.Counter(); byroot={}
  for m in scene.meshes:
   ids,_=w.c.indices_for_mesh(verts,m);c=collections.Counter(w.key([pts[i] for i in ids[k:k+3]]) for k in range(0,len(ids),3));byroot[m['path']]=c;source+=c
  path=p.PC/f['pc_family']/'wheel.dx'
  if p.sha(path.read_bytes())!=wc['source_pc_sha256']:raise ValueError('PC wheel drift')
  pc=p.parse_dx(path);native=collections.Counter();records=[]
  for d in pc.physical_draws:
   ids=pc.draw_global_indices(d);c=collections.Counter(w.key([pc.vertices.positions[i] for i in ids[k:k+3]]) for k in range(0,len(ids),3));native+=c
   records.append(dict(path=d.record_path,faces=sum(c.values()),ps2_roots_matching_faces={k:sum((c&v).values()) for k,v in byroot.items() if c&v},missing_source_faces=sum((c-source).values())))
  row.update(source_partition='EXACT_EXHAUSTIVE_FACE_MULTISET' if source==native else 'SOURCE_GEOMETRY_DIFFERS',original_ps2_faces=sum(source.values()),original_pc_faces=sum(native.values()),ps2_only_faces=sum((source-native).values()),pc_only_faces=sum((native-source).values()),records=records)
  rows.append(row)
 return dict(schema=1,grant='SOURCE_ONLY_NO_NATIVE_WHEEL_REPLACEMENT_AUTHORIZATION',families=rows)
if __name__=='__main__':
 out=audit();(HERE/'contracts.json').write_text(json.dumps(out,indent=2)+'\n');print(collections.Counter(x['source_partition'] for x in out['families']))
