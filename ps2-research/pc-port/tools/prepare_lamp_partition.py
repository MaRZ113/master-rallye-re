"""Bounded Terrano rear lamp material control; hashes/metadata only."""
from pathlib import Path
import importlib.util,json,hashlib,collections
PORT=Path(__file__).resolve().parents[1]
def main():
 spec=importlib.util.spec_from_file_location('lamp_common',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
 part_spec=importlib.util.spec_from_file_location('existing_partition',PORT/'docs/vehicle-model-port1/race-partitions/audit.py');part=importlib.util.module_from_spec(part_spec);part_spec.loader.exec_module(part)
 model=a.parse_dx(a.PC/'Terrano/car.dx');draw=model.physical_draws[11];fs=a.faces(model,draw)
 digest=a.geometry_signature(fs)
 if digest!='7f46a206c472a37c9cb951f0f110f63bb6742ce57466d4adea1ec8896854784e':raise ValueError('Unverified Terrano lamp source')
 frozen=json.loads((PORT/'docs/xtrail-brake-followup/terrano-source.json').read_text());a.w.verify_inputs(a.PS2)
 if a.sha((a.PC/'Terrano/car.dx').read_bytes())!=frozen['pc_sha256']:raise ValueError('PC source identity drift')
 entries,_=a.t.load_pak(a.PS2/'TNG.PAK');entry=next(e for e in entries['entries'] if e['path'].upper().endswith('TERRANO\\CAR.PSM'));raw,_=a.t.read_payload(entry,a.PS2/'TNG.000')
 if a.sha(raw)!=frozen['ps2_sha256']:raise ValueError('PS2 source identity drift')
 scene=a.r.decode_vehicle(raw);mesh=next(m for m in scene.meshes if m['path']=='root.11');pfs,_=a.w.mesh_triangles(scene,mesh)
 if len(pfs)!=58 or not all(a.matches(f,a.index_faces(pfs)) for f in fs):raise ValueError('Original lamp mesh join lost')
 # Connected source components separated front/rear. Only components entirely
 # behind local Z=0 are rear controls; no screen-space silhouette or runtime ordinal.
 owners=collections.defaultdict(list)
 for i,f in enumerate(fs):
  for xyz in f:owners[xyz].append(i)
 seen=set();rear=set();components=[]
 for i in range(len(fs)):
  if i in seen:continue
  group={i};queue=[i];seen.add(i)
  while queue:
   n=queue.pop()
   for xyz in fs[n]:
    for other in owners[xyz]:
     if other not in seen:seen.add(other);group.add(other);queue.append(other)
  points=[xyz for n in group for xyz in fs[n]];bounds={'min':[min(x[k] for x in points) for k in range(3)],'max':[max(x[k] for x in points) for k in range(3)]}
  back=bounds['max'][2]<0
  if back:rear.update(group)
  components.append({'faces':sorted(group),'bounds':bounds,'policy':'NATIVE_LAMP_MATERIAL' if back else 'KEEP_ACCEPTED_MODE4'})
 if len(rear)!=22:raise ValueError('Rear lamp component inventory changed')
 mapping={}
 for i,f in enumerate(fs):
  h=part.face_hash(f);category=i not in rear
  if h in mapping and mapping[h]['shiny']!=category:raise ValueError('Contradictory shared face material')
  row=mapping.setdefault(h,{'multiplicity':0,'shiny':category});row['multiplicity']+=1
 lines=['#pragma once','#include "vehicle_partition.hpp"','namespace gfx2::ps2port {','inline constexpr PartitionFace kTerranoLampFaces[]={']
 for h,v in sorted(mapping.items()):lines.append('    {"%s",%du,%s},'%(h,v['multiplicity'],str(v['shiny']).lower()))
 lines+=['};','inline constexpr PartitionMaterial kLampPartitionMaterials[]={','    {"Terrano","%s",70u,58u,kTerranoLampFaces,58u},'%digest,'};','} // namespace gfx2::ps2port','']
 (PORT/'renderer/lamp_partition_registry.hpp').write_text('\n'.join(lines))
 report={'schema_version':1,'source_identity':frozen,'rear_faces':22,'accepted_other_faces':36,'components':components,'face_hash_policy':mapping,'coordinate_system':'MODEL_LOCAL_GAME_SOURCE','geometric_role_grade':'STATIC_INFERENCE_FROM_SOURCE_COMPONENTS','material_policy':'RETAIN_NATIVE_PC_LAMP_MATERIAL_NOT_PS2_PARITY','runtime_validation':'PENDING_USER','stock_default':'RaceModelMode=0'}
 (PORT/'docs/xtrail-brake-followup/lamp-partition.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
