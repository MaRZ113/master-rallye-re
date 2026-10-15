"""Bounded read-only wheel source/F10 join; ordinals are evidence only."""
from pathlib import Path
import sys,json,hashlib,math,importlib.util
ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT.parent/'master-rallye-re-course/src'),str(ROOT/'ps2-research/pc-port/tools'),str(ROOT/'ps2-research/tools')]
from master_rallye.dx import parse_dx
from prepare_reflection_pilot import geometry_signature
import tngtool as t,reflection_runtime as r

def run():
 p=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/wheel.dx';raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 assert sha=='f05ac990b6ea2312f2a2d552ec886aded4c68a8d8fac027f99e1fc7b0826779c'
 m=parse_dx(p);source=[];pcfaces={}
 for d in m.physical_draws:
  ids=m.draw_global_indices(d);fs=[tuple(m.vertices.positions[i] for i in ids[n:n+3]) for n in range(0,len(ids),3)]
  pcfaces[d.draw_index]=fs;source.append(dict(record=d.draw_index,path=d.record_path,vertex_base=d.vertex_base,vertices=d.local_vertex_max+1,index_start=d.index_start,triangles=len(fs),slots=[s.value for s in d.texture_slots],signature=geometry_signature(fs)))
 frame=Path(r'D:/Game/Master Rallye Pristine/MRRRenderer/logs/frame-44168-d1-00006057.jsonl');rs=[json.loads(s) for s in frame.read_text().splitlines()];obs=[]
 for q in rs:
  if q.get('type')!='draw' or q.get('object_class')!='VEHICLE_WHEEL':continue
  a=q['arguments'];matches=[s for s in source if s['vertices']==a[2] and s['triangles']==a[4]]
  if len(matches)!=1:continue
  s=matches[0];st=q['state'];world=st['matrices']['256']['values']
  obs.append(dict(draw=q['draw_index'],sequence=q['sequence'],source_record=s['record'],arguments=a,vertex_relocation=a[1]-s['vertex_base'],index_relocation=a[3]-s['index_start'],world=world,axis_lengths=[math.sqrt(sum(world[k+j]*world[k+j] for j in range(3))) for k in (0,4,8)],transform_track=q['transform_track_id'],stream=st['streams'][0],indices=st['indices'],fvf=st['vertex_shader'],caller_rva=q['caller']['return_rva'],identity_status='LAYOUT_AND_TEMPORAL_OBSERVATION_NOT_UPLOAD_HASH_OR_QUEUE_OWNER_PROOF'))
 root=Path('D:/Game/Master Rallye PS2');pack,_=t.load_pak(root/'TNG.PAK');entries={t.logical_path(e['path']).upper():e for e in pack['entries'] if e['kind']=='file'};raw,_=t.read_payload(entries['\\TNG\\DATAPSM\\VEHICLES\\XTRAIL\\WHEEL.PSM'],root/'TNG.000');spec=importlib.util.spec_from_file_location('reader',ROOT/'ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights/complete_reader.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader);scene,trailer=reader.decode_complete(raw)
 import struct
 spec2=importlib.util.spec_from_file_location('conv',ROOT/'ps2-research/pc-port/docs/vehicle-model-port2/assets/convert_complete.py');conv=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(conv)
 ps=[struct.unpack_from('<3f',raw,32+i*52+36) for i in range(scene.vertex_count)]
 psmesh=[]
 for mesh in scene.meshes:
  ids,diag=conv.indices_for_mesh(raw[32:32+scene.vertex_count*52],mesh);fs=[tuple(ps[i] for i in ids[n:n+3]) for n in range(0,len(ids),3)];psmesh.append(dict(path=mesh['path'],faces=len(fs),signature=geometry_signature(fs)))
 def bounds(v):return [list(map(min,zip(*v))),list(map(max,zip(*v)))]
 out=dict(frame=6057,pid=44168,frame_sha256=t.sha(frame.read_bytes()),pc_source_sha256=sha,pc_source_records=source,pc_bounds=bounds(m.vertices.positions),ps2_source_sha256=t.sha(raw),ps2_bounds=bounds(ps),ps2_vertices=scene.vertex_count,ps2_meshes=psmesh,pc_records_0_plus_2_signature=geometry_signature(pcfaces[0]+pcfaces[2]),observations=obs,unique_worlds=len({tuple(o['world']) for o in obs}))
 Path(__file__).with_name('evidence.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('pc_bounds','ps2_bounds','unique_worlds')}));print('observations',len(obs))
if __name__=='__main__':run()
