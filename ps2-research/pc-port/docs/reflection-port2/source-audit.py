"""Read-only bounded source audit; outputs compact hashes and material witnesses only."""
from pathlib import Path
import sys,json,hashlib,math
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'ps2-research/tools'),str(ROOT/'ps2-research/pc-port/tools'),r'D:/Game/Master Rallye/master-rallye-re-course/src']
from master_rallye.dx import parse_dx
from prepare_reflection_pilot import geometry_signature
import reflection_runtime as r
import water_runtime as w
P=ROOT/'ps2-research/data/refl1/KIASPORTAGE-CAR.PSM'
b=P.read_bytes(); scene=r.decode_vehicle(b)
if hashlib.sha256(b).hexdigest()!='b4afabfab7437eae01ee72ca424beb90967c7b849cebdb9cf94e104560be33ce': raise ValueError('Kia PSM hash mismatch')
retail=Path(r'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles')
dx=retail/'KiaSportage/car.dx';m=parse_dx(dx)
report={'schema_version':1,'representation':'VISUAL_SOURCE_COMPILED_DRAW_NOT_LIVE_DRAW','pc_source':{'path':'DataGx/Vehicles/KiaSportage/car.dx','sha256':hashlib.sha256(dx.read_bytes()).hexdigest()},'ps2_source':json.loads((P.parent/'KIASPORTAGE-provenance.json').read_text()),'candidates':[],'negative_controls':{}}
for pth,num in [('root.5',14),('root.4',13)]:
 mesh=next(x for x in scene.meshes if x['path']==pth);pf,ctrl=w.mesh_triangles(scene,mesh)
 d=m.physical_draws[num]; ids=m.draw_global_indices(d);fs=[tuple(m.vertices.positions[i] for i in ids[n:n+3]) for n in range(0,len(ids),3)]
 signature=geometry_signature(fs)
 pcm=sum(any(w.corner_error(a,c)<=.001 for c in pf) for a in fs)
 psm=sum(any(w.corner_error(a,c)<=.001 for c in fs) for a in pf)
 bounds={'min':[min(p[i] for f in fs for p in f) for i in range(3)],'max':[max(p[i] for f in fs for p in f) for i in range(3)]}
 report['candidates'].append({'model':'KiaSportage','ps2_mesh':{'path':pth,'node_offset':mesh['node_offset'],'material_offset':mesh['material_offset'],'material':mesh['material'],'textures':mesh['textures'],'triangles':len(pf),'contract':r.material_contract(mesh['material'],mesh['textures'][1]['name'])},'pc_draw':{'record':num,'path':d.record_path,'offset':d.offset,'vertex_base':d.vertex_base,'vertex_count':d.local_vertex_max+1,'index_start':d.index_start,'index_count':d.index_count,'triangles':len(fs),'texture_slots':[s.value for s in d.texture_slots],'flags_hex':d.flags_0x20.hex(),'diffuse_alpha_values':sorted({m.vertices.colors[i*4+3] for i in ids}),'geometry_sha256':signature,'bounds':bounds},'correspondence':{'tolerance':.001,'pc_faces_matching_ps2':pcm,'ps2_faces_matching_pc':psm,'method':'unsigned corner-permutation max-distance, preserves duplicate faces'},'evidence_grade':'CONFIRMED_BY_BYTES','runtime_identity':'NOT_YET_OBSERVED','activation_constraints':['Current race/body semantic owner','Current resource generations and revisions','Exact FVF0x152/stride36 and triangle layout','Exact bitwise geometry digest','Opaque native render states and original environment stage','2D current texture generations','Known native/effective texture matrix','Stock original PC coordinate policy']})
bycount={c['pc_draw']['index_count']:c for c in report['candidates']};matches={c['pc_draw']['geometry_sha256']:[] for c in report['candidates']};checked=0;files=0;errors=[]
for f in sorted(retail.glob('*/*.dx')):
 files+=1
 try: model=parse_dx(f)
 except Exception as e:errors.append({'source':str(f.relative_to(retail)),'error':str(e)});continue
 for d in model.physical_draws:
  if d.index_count not in bycount:continue
  checked+=1;ids=model.draw_global_indices(d);fs=[tuple(model.vertices.positions[i] for i in ids[n:n+3]) for n in range(0,len(ids),3)]
  h=geometry_signature(fs)
  if h in matches:matches[h].append({'source':str(f.relative_to(retail)).replace('\\','/'),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'record':d.draw_index,'vertex_count':d.local_vertex_max+1,'texture_slots':[s.value for s in d.texture_slots]})
report['negative_controls']={'model_files_scanned':files,'matching_index_count_records_checked':checked,'signature_matches':matches,'unsupported':errors,'limitation':'Corpus uniqueness proves source shape specificity; it cannot prove current player/opponent ownership or live state'}
out=Path(__file__).with_name('vehicle-material-audit.json');out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(out),'correspondence':[c['correspondence'] for c in report['candidates']],'controls':report['negative_controls']},indent=2))
