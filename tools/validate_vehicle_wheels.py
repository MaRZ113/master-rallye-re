"""Qualify wheel template winding and four explicit visual rest instances.

The caller identifies source-qualified face draws. No texture names, physics
parameters, fitted hubs or vehicle-specific draw numbers are inferred here.
"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes


def geometry(model):
    rows=[]
    for d in model.physical_draws:
        ids=model.draw_global_indices(d);area=[0.,0.,0.];degenerate=[];opposed=[]
        for i in range(0,len(ids),3):
            tri=ids[i:i+3];p,q,r=(model.vertices.positions[k] for k in tri)
            a=[q[k]-p[k] for k in range(3)];b=[r[k]-p[k] for k in range(3)]
            cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
            if sum(v*v for v in cross)<1e-20:degenerate.append(i//3);continue
            if sum(cross[k]*sum(model.vertices.normals[j][k] for j in tri) for k in range(3))<=0:opposed.append(i//3)
            area=[area[k]+cross[k] for k in range(3)]
        rows.append({'draw':d.draw_index,'triangles':len(ids)//3,'degenerate_triangles':degenerate,
                     'normal_winding_disagreements':opposed,'oriented_area':area})
    return rows


def qualify(data,profile,face_draws,*,before_data=None,before_profile=None):
    m=parse_dx_bytes(data)
    if not m.diagnostics.validated:raise ValueError('invalid wheel DX')
    if not face_draws or not set(face_draws)<=set(range(len(m.physical_draws))):raise ValueError('invalid qualified face draws')
    if not all(math.isfinite(v) for p in (*m.vertices.positions,*m.vertices.normals) for v in p):raise ValueError('nonfinite wheel attributes')
    rows=geometry(m)
    if any(r['normal_winding_disagreements'] for r in rows):raise ValueError('wheel normals oppose canonical triangle winding')
    if any(r['triangles']==len(r['degenerate_triangles']) for r in rows):raise ValueError('entire wheel draw is degenerate')
    face=sum(rows[i]['oriented_area'][0] for i in face_draws)
    if face>=-1e-8:raise ValueError('qualified face does not point to native stock local -X')
    transforms=profile['race_wheel_instances']
    if len(transforms)!=4:raise ValueError('require four independently qualified rest instances')
    if len({tuple(t['translation']) for t in transforms})!=4:raise ValueError('duplicate wheel hubs')
    checks=[]
    for i,t in enumerate(transforms):
        scale=t.get('scale',[1.,1.,1.]);det=math.prod(scale);angle=t['rotation_y'];hub=t['translation']
        if len(scale)!=3 or len(hub)!=3 or not all(math.isfinite(v) for v in [*scale,*hub,angle]):raise ValueError('invalid instance transform')
        if det<=0:raise ValueError('mirrored wheel transform requires an independently qualified winding policy')
        side=t.get('outward_x',1 if hub[0]>0 else -1)
        outward=[-math.cos(angle)*scale[0],0.,math.sin(angle)*scale[0]]
        if side not in (-1,1) or outward[0]*side<=0 or abs(outward[2])>1e-6:raise ValueError('wheel face points inward')
        checks.append({'instance':i,'hub':hub,'determinant':det,'outward_x':side,'face_axis':outward,'status':'PASS'})
    report={'status':'PASS_FOUR_VISUAL_REST_INSTANCES','draws':rows,'instances':checks,
            'source_degenerate_triangles_retained':sum(len(r['degenerate_triangles']) for r in rows),
            'boundary':'explicit visual source-rest transforms; native physics hub/spin/steering require runtime inspection',
            'runtime_qualified':False}
    if before_data is not None:
        old=parse_dx_bytes(before_data);oldrows=geometry(old)
        if old.vertex_count!=m.vertex_count or old.local_indices!=m.local_indices or old.global_index_table.indices!=m.global_index_table.indices:raise ValueError('orientation repair changed topology')
        for p,q,n,z in zip(old.vertices.positions,m.vertices.positions,old.vertices.normals,m.vertices.normals):
            if q!=(-p[0],p[1],-p[2]) or z!=(-n[0],n[1],-n[2]):raise ValueError('repair is not the declared proper Y half-turn')
        if old.vertices.colors!=m.vertices.colors or old.uv_sets!=m.uv_sets:raise ValueError('wheel colours/UVs changed')
        if [r['degenerate_triangles'] for r in rows]!=[r['degenerate_triangles'] for r in oldrows]:raise ValueError('introduced wheel degeneracy')
        if before_profile and [t['translation'] for t in transforms]!=[t['translation'] for t in before_profile['race_wheel_instances']]:raise ValueError('wheel hubs moved')
        report.update(proper_rotation_determinant=1,topology_uv_colour_preserved=True,no_new_degenerate_triangles=True,hubs_unchanged=bool(before_profile))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--wheel',type=Path,required=True);p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--face-draws',required=True,help='comma-separated source-qualified face draw indices')
    p.add_argument('--before-wheel',type=Path);p.add_argument('--before-profile',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=qualify(a.wheel.read_bytes(),json.loads(a.profile.read_text()),[int(v) for v in a.face_draws.split(',')],
        before_data=a.before_wheel.read_bytes() if a.before_wheel else None,before_profile=json.loads(a.before_profile.read_text()) if a.before_profile else None)
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
