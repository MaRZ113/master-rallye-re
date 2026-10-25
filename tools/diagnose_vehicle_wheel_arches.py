"""Fit explicitly selected arch-edge samples; never guess or edit wheel hubs.

An arch is not necessarily circular or concentric with its physical axle.
Reported centres are geometric diagnostics, not recovered GT4 transforms.
No NumPy or retail/GT assets are bundled.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes

def solve(a,b):
    m=[list(row)+[value] for row,value in zip(a,b)]
    for col in range(3):
        pivot=max(range(col,3),key=lambda i:abs(m[i][col]));m[col],m[pivot]=m[pivot],m[col]
        d=m[col][col]
        if abs(d)<1e-12:raise ValueError('arch samples do not define a stable circle')
        m[col]=[x/d for x in m[col]]
        for i in range(3):
            if i!=col:
                d=m[i][col];m[i]=[x-d*y for x,y in zip(m[i],m[col])]
    return [row[3] for row in m]

def diagnose(raw,selection):
    if hashlib.sha256(raw).hexdigest()!=selection['model_sha256']:raise ValueError('arch sample source hash differs')
    m=parse_dx_bytes(raw)
    if not m.diagnostics.validated:raise ValueError('invalid arch model')
    rows={}
    for axle,ids in selection['arch_vertex_indices'].items():
        if axle not in ('Front','Rear') or not 4<=len(ids)<=128 or len(set(ids))!=len(ids) or any(type(i) is not int or not 0<=i<m.vertex_count for i in ids):raise ValueError('invalid explicit arch vertex selection')
        points=[m.vertices.positions[i] for i in ids];cz=sum(p[2] for p in points)/len(points);cy=sum(p[1] for p in points)/len(points)
        a=[[2*(p[2]-cz),2*(p[1]-cy),1] for p in points];b=[(p[2]-cz)**2+(p[1]-cy)**2 for p in points]
        z,y,c=solve([[sum(row[i]*row[j] for row in a) for j in range(3)] for i in range(3)],[sum(row[i]*v for row,v in zip(a,b)) for i in range(3)])
        radius=math.sqrt(z*z+y*y+c);z+=cz;y+=cy
        residual=max(abs(math.hypot(p[2]-z,p[1]-y)-radius) for p in points)
        rows[axle]={'sample_indices':ids,'centre_zy_m':[z,y],'circle_radius_m':radius,'max_radial_residual_m':residual}
    f=rows['Front']['centre_zy_m'][0];r=rows['Rear']['centre_zy_m'][0]
    return {'status':'GEOMETRIC_ARCH_DIAGNOSTIC_NOT_SOURCE_AXLES','model_sha256':selection['model_sha256'],'arches':rows,
        'arch_centre_spacing_m':f-r,'common_longitudinal_centre_m':(f+r)/2,
        'boundary':'explicit upper-edge samples; circular approximation only; neither automatic hub fitting nor proof of original GT4 wheelbase. A symmetric MR WheelBase cannot exactly satisfy an asymmetric body opening pair.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=diagnose(a.model.read_bytes(),json.loads(a.selection.read_text()));a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('status','arch_centre_spacing_m','common_longitudinal_centre_m')}))
