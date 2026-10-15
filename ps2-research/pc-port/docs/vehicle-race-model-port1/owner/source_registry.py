"""Read-only exact Xtrail CAR source registry, original SDK parser reused."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT/'ps2-research/pc-port/tools'),str(ROOT.parent/'master-rallye-re-course/src')]
from master_rallye.dx import parse_dx
from prepare_reflection_pilot import geometry_signature
SHA='e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f'
def registry(path):
 if hashlib.sha256(path.read_bytes()).hexdigest()!=SHA: raise ValueError('Original Xtrail car.dx drift')
 m=parse_dx(path); rows=[]
 for d in m.physical_draws:
  ids=m.draw_global_indices(d)
  fs=[tuple(m.vertices.positions[i] for i in ids[n:n+3]) for n in range(0,len(ids),3)]
  rows.append(dict(draw=d.draw_index,path=d.record_path,vertex_base=d.vertex_base,vertices=d.local_vertex_max+1,index_start=d.index_start,triangles=len(fs),slots=[s.value for s in d.texture_slots],hash=geometry_signature(fs)))
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT.parent/'corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/car.dx');a=p.parse_args()
 print(json.dumps(dict(source_sha=SHA,source_records=registry(a.source)),indent=2))
