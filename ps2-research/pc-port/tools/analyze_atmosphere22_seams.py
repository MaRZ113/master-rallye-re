"""Offline source evidence for draw-boundary normals, never screenshot attribution."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx_course import parse_course_dx

def normal(v):
    length=math.sqrt(sum(x*x for x in v));return tuple(x/length for x in v) if length>1e-8 else None
def analyze(path,material_rows):
    model=parse_course_dx(path);at_position=defaultdict(list);count=0
    for draw_no,draw in enumerate(model.physical_draws):
        material=material_rows.get(draw.texture_tuple[0])
        if not material or material['category'] not in (1,2,4) or material['flags']&16:continue
        indices=model.local_indices[draw.index_start:draw.index_start+draw.index_count];sums=defaultdict(lambda:[0.,0.,0.])
        for j in range(0,len(indices),3):
            a,b,c=[model.vertices.positions[draw.vertex_base+i] for i in indices[j:j+3]]
            u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)];sign=material['winding']
            n=(sign*(u[1]*v[2]-u[2]*v[1]),sign*(u[2]*v[0]-u[0]*v[2]),sign*(u[0]*v[1]-u[1]*v[0]))
            for index in indices[j:j+3]:
                for k in range(3):sums[index][k]+=n[k]
        for index,summed in sums.items():
            geometric=normal(summed);source=normal(model.vertices.normals[draw.vertex_base+index])
            if not geometric or not source:continue
            p=model.vertices.positions[draw.vertex_base+index];key=tuple(round(x*1000) for x in p)
            at_position[key].append((draw_no,draw.texture_tuple[0],geometric,source));count+=1
    seams=[];same_source=0;different_source=0
    for xyz,rows in at_position.items():
        if len(rows)>64:continue
        for i,a in enumerate(rows):
            for b in rows[i+1:]:
                if a[0]==b[0]:continue
                authored=sum(x*y for x,y in zip(a[3],b[3]));geometric=sum(x*y for x,y in zip(a[2],b[2]))
                if authored>.9999:
                    same_source+=1
                    if geometric<.95:
                        seams.append({'xyz':[x/1000 for x in xyz],'draws':[a[0],b[0]],'materials':[a[1],b[1]],'local_normal_dot':geometric,'authored_normal_dot':authored,'local_normals':[a[2],b[2]],'authored_normals':[a[3],b[3]]})
                else:different_source+=1
    return {'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices_inspected':count,'cross_draw_same_authored_normal_pairs':same_source,
            'cross_draw_different_authored_normal_pairs':different_source,'same_source_but_local_normal_dot_below_095':len(seams),'worst_examples':sorted(seams,key=lambda r:r['local_normal_dot'])[:8]}

if __name__=='__main__':
    provenance=json.loads((ROOT/'.research-output/atmosphere21/materials-validated/provenance.json').read_text());reports=[]
    for source in provenance['sources']:
        path=Path(source['source'])
        if not path.exists():path=Path(str(path).replace('DataGx\\Course\\','DataGx\\Course1\\'))
        reports.append(analyze(path,{r['material']:r for r in source['materials']}))
    report={'evidence':'OFFLINE_SOURCE_ONLY_NOT_SCREENSHOT_ATTRIBUTION','reports':reports}
    out=ROOT/'.research-output/atmosphere22/offline-seam-evidence.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print([(r['source'],r['same_source_but_local_normal_dot_below_095']) for r in reports])
