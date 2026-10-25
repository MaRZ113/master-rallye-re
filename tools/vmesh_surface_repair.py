"""Bounded source-linked cavity backs and small boundary-gap bridges.

Only generated black interior geometry is appended. Original imported vertices,
UVs, normals and triangles are retained, with a separate provenance report.
"""
from __future__ import annotations
import math
import collections
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry,CompiledVertex,DrawGeometry,rebuild_topology


def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def unit(a):
    ln=math.sqrt(dot(a,a))
    return tuple(x/ln for x in a) if ln>1e-12 else (0,0,0)
def normal(p,q,r):
    a,b=sub(q,p),sub(r,p)
    return unit((a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]))
def key(p): return tuple(round(x,5) for x in p)
def closest(p,a,b):
    v=sub(b,a);den=dot(v,v)
    t=max(0,min(1,dot(sub(p,a),v)/den)) if den else 0
    return tuple(a[k]+v[k]*t for k in range(3))


def on_surface(p, tri, tolerance=.001):
    a,b,c=tri;u,v,w=sub(b,a),sub(c,a),sub(p,a)
    n=normal(a,b,c)
    if n==(0,0,0) or abs(dot(w,n))>tolerance:return False
    uu,uv,vv,wu,wv=dot(u,u),dot(u,v),dot(v,v),dot(w,u),dot(w,v)
    den=uu*vv-uv*uv
    if den<1e-18:return False
    s,t=(vv*wu-uv*wv)/den,(uu*wv-uv*wu)/den
    return s>=-1e-6 and t>=-1e-6 and s+t<=1.000001


def repair(data, source_faces, classifier, material_plan, transform, source_map, *,
           black_draw=9, backing_depth=.004, max_gap=.020, front_fraction=.20,
           glass_draw=None, lens_offset=.001, weld_lenses=False, close_recesses=False,
           source_caps_only=False, recess_padding=.025):
    if not 0<backing_depth<=.02 or not 0<max_gap<=.03 or not 0<front_fraction<=.3:
        raise ValueError('surface repair bounds outside supported range')
    model=parse_dx_bytes(data);geoms=source_geometry(model);base=geoms[black_draw]
    verts,tris=list(base.vertices),list(base.triangles)
    backs,bridges=[],[]
    top_backs=[]
    def emit(points):
        n=normal(*points)
        if n==(0,0,0): return
        off=len(verts)
        verts.extend(CompiledVertex(tuple(p),n,bytes((255,255,255,255)),((.5,.5),)) for p in points)
        # Explicitly two-sided generated interior closures; existing culling state stays fixed.
        tris.extend(((off,off+1,off+2),(off,off+2,off+1)))
    limit=classifier.z_front+front_fraction*classifier.length
    for fi,(o,m,t) in enumerate(source_faces):
        role=classifier._decide(o,m)[0]
        cls=material_plan._cls.get(fi,(None,None))[1]
        front=sum(c[0][2] for c in t)/3<=limit
        if not source_caps_only and (role=='head_lamp' or role=='black' and cls=='cutout' and front):
            ps=[transform(c[0]) for c in t]
            n=normal(*ps)
            # In the converted frame the front points toward +Z. Use that
            # direction to orient the cavity depth even for reversed source winding.
            if n[2]<0:n=tuple(-v for v in n)
            emit([tuple(p[k]-backing_depth*n[k] for k in range(3)) for p in ps])
            backs.append(fi)
        if close_recesses and not source_caps_only and role=='paint' and cls=='cutout' and m not in material_plan.decal_materials:
            ps=[transform(c[0]) for c in t];n=normal(*ps)
            top=sum(c[0][1] for c in t)/3
            if abs(n[1])>.75 and top>.55 and sum(c[0][2] for c in t)/3<classifier.z_front+.4*classifier.length:
                if n[1]<0:n=tuple(-v for v in n)
                centre=tuple(sum(p[k] for p in ps)/3 for k in range(3))
                emit([tuple(p[k]-backing_depth*n[k]+.003*unit(sub(p,centre))[k] for k in range(3)) for p in ps])
                top_backs.append(fi)
    collars=[]
    if close_recesses:
        if not 0 < recess_padding <= .025:raise ValueError('recess padding out of bounds')
        collars=_recess_collars(source_faces,classifier,material_plan,transform,emit,padding=recess_padding)
    edges=collections.defaultdict(list)
    solid=[]
    seen=set()
    for r in source_map:
        fi=r['face'];o,m,t=source_faces[fi]
        if classifier._decide(o,m)[0] not in ('paint','black','head_lamp'):continue
        if sum(c[0][2] for c in t)/3>limit:continue
        g=geoms[r['draw']];ps=[g.vertices[i].position for i in g.triangles[r['tri']]]
        if not model.physical_draws[r['draw']].flags_0x20[0]:solid.append(ps)
        tk=tuple(sorted(key(p) for p in ps))
        if tk in seen:continue
        seen.add(tk)
        for a,b in zip(ps,ps[1:]+ps[:1]):
            ek=tuple(sorted((key(a),key(b))))
            if ek[0]!=ek[1]:edges[ek].append((a,b,fi))
    boundary=[v[0] for v in edges.values() if len(v)==1]
    used=set()
    supported_skipped=0
    for i,(a,b,fi) in enumerate(boundary):
        if i in used or math.dist(a,b)<.005:continue
        best=None
        for j,(c,d,fj) in enumerate(boundary):
            if i==j or j in used or fi==fj:continue
            if abs(dot(unit(sub(b,a)),unit(sub(d,c))))<.98:continue
            q0,q1=closest(a,c,d),closest(b,c,d)
            if math.dist(q0,q1)<.75*math.dist(a,b):continue
            gaps=[math.dist(a,q0),math.dist(b,q1)]
            if max(gaps)<.0005 or max(gaps)>max_gap:continue
            score=sum(gaps)
            if best is None or score<best[0]:best=(score,j,q0,q1,gaps,fj)
        if best:
            _,j,q0,q1,gaps,fj=best
            samples=[tuple(((1-t)*a[k]+t*b[k]+(1-t)*q0[k]+t*q1[k])/2 for k in range(3)) for t in (.2,.5,.8)]
            if all(any(on_surface(p,tri) for tri in solid) for p in samples):
                supported_skipped+=1
                continue
            emit([a,b,q0]);emit([b,q1,q0]);used.update((i,j))
            bridges.append({'source_faces':[fi,fj],'gap_m':gaps,'edges':[list(a),list(b),list(q0),list(q1)]})
    edits={black_draw:DrawGeometry(tuple(verts),tuple(tris))}
    lens_sources=[]
    uv=getattr(material_plan,'lamp_glass_uv',None)
    if glass_draw is not None and uv is not None:
        glass=geoms[glass_draw];gv,gt=list(glass.vertices),list(glass.triangles)
        lamp_points={key(c[0]) for o,m,t in source_faces if o in classifier.lamp_objects for c in t}
        already=set();origin=transform((0,0,0));selected=[]
        for fi,(o,m,t) in enumerate(source_faces):
            if 'reflection' not in o or not all(key(c[0]) in lamp_points for c in t):continue
            identity=tuple(sorted(key(c[0]) for c in t))
            if identity in already:continue
            already.add(identity)
            selected.append((fi,t))
        normal_sums=collections.defaultdict(lambda:[0.,0.,0.]);normal_first={}
        if weld_lenses:
            for fi,t in selected:
                fn=normal(*(transform(c[0]) for c in t))
                for c in t:
                    n=unit(sub(transform(c[1]),origin)) if c[1] is not None else fn
                    normal_first.setdefault(key(c[0]),n)
                    for k in range(3):normal_sums[key(c[0])][k]+=n[k]
        welded={}
        for fi,t in selected:
            points=[transform(c[0]) for c in t]
            fn=normal(*points)
            ns=[unit(sub(transform(c[1]),origin)) if c[1] is not None else fn for c in t]
            out=unit(tuple(sum(n[k] for n in ns) for k in range(3)))
            local=[]
            for c,p,n in zip(t,points,ns):
                pk=key(c[0])
                if weld_lenses:
                    n=unit(normal_sums[pk])
                    if n==(0,0,0):n=normal_first[pk]
                    out=n
                    if pk in welded:local.append(welded[pk]);continue
                idx=len(gv)
                gv.append(CompiledVertex(tuple(p[k]+lens_offset*out[k] for k in range(3)),n,
                                         bytes((255,255,255,255)),(tuple(uv),)))
                local.append(idx)
                if weld_lenses:welded[pk]=idx
            gt.append(tuple(local));lens_sources.append(fi)
        if lens_sources:edits[glass_draw]=DrawGeometry(tuple(gv),tuple(gt))
    rebuilt=rebuild_topology(data,edits,bounds_mode='recompute')
    return rebuilt.data,{'method':'source-linked lamp/front technical-mask backs and paired boundary edges',
                         'backing_depth_m':backing_depth,'maximum_allowed_gap_m':max_gap,
                         'front_fraction':front_fraction,'backing_source_faces':backs,'bridges':bridges,
                         'source_caps_only':source_caps_only,
                         'supported_edge_pairs_skipped':supported_skipped,
                         'top_mask_backing_source_faces':top_backs,'recess_collars':collars,
                         'lamp_glass':{'native_glass_draw':glass_draw,'uv':uv,'offset_m':lens_offset,
                                       'shared_vertices':weld_lenses,
                                       'reflection_shell_source_faces':lens_sources,
                                       'generated_triangles':len(lens_sources),'opaque_cavity_retained':True},
                         'generated_triangles':len(tris)-len(base.triangles),'original_vertices_moved':0,
                         'rebuild':rebuilt.to_dict()}


def _recess_collars(faces,classifier,plan,transform,emit,padding=.025,depth=.010):
    """Connect small dark planar terminal panels to a bounded expanded back rim.

    Components and their plane come from source geometry. This catches grille
    and plate recesses even when nearby frame edges have different tessellation.
    """
    groups=collections.defaultdict(list);result=[]
    body_points=[transform(c[0]) for o,m,t in faces if classifier._decide(o,m)[0] in ('paint','black') for c in t]
    body_width=max(p[0] for p in body_points)-min(p[0] for p in body_points) if body_points else 0
    for fi,(o,m,t) in enumerate(faces):
        role=classifier._decide(o,m)[0]
        if role not in ('paint','black') or o in classifier.lamp_objects or m in plan.decal_materials:continue
        if plan._cls.get(fi,(None,None))[1] not in ('opaque','cutout'):continue
        tex=plan.textures.get(m)
        if tex is None or max(tex.mean_color()[0])>75:continue
        groups[o,m].append((fi,t))
    for (obj,material),items in groups.items():
        adjacent=collections.defaultdict(set)
        for j,(fi,t) in enumerate(items):
            for c in t:adjacent[key(c[0])].add(j)
        todo=set(range(len(items)))
        while todo:
            seed=todo.pop();stack=[seed];component=[]
            seed_points=[c[0] for c in items[seed][1]];seed_n=normal(*seed_points)
            while stack:
                j=stack.pop();component.append(items[j])
                for c in items[j][1]:
                    for q in adjacent[key(c[0])]&todo:
                        qp=[v[0] for v in items[q][1]];qn=normal(*qp)
                        if abs(dot(seed_n,qn))<.995 or max(abs(dot(sub(p,seed_points[0]),seed_n)) for p in qp)>.004:continue
                        todo.remove(q);stack.append(q)
            src=[c[0] for fi,t in component for c in t]
            centre_z=sum(p[2] for p in src)/len(src)
            front=centre_z<classifier.z_front+.18*classifier.length
            rear=centre_z>classifier.z_front+.82*classifier.length
            if not (front or rear):continue
            if classifier._decide(obj,material)[0]=='paint' and abs(sum(p[0] for p in src)/len(src))>.15:continue
            ps=[transform(p) for p in src];n=normal(*ps[:3])
            if abs(n[2])<.8 or max(abs(dot(sub(p,ps[0]),n)) for p in ps)>.006:continue
            if n[2]*(1 if front else -1)<0:n=tuple(-v for v in n)
            u=unit((n[2],0,-n[0]));v=(n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0])
            origin=tuple(sum(p[k] for p in ps)/len(ps) for k in range(3))
            pts=sorted(set((dot(sub(p,origin),u),dot(sub(p,origin),v)) for p in ps))
            def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            def half(points):
                out=[]
                for p in points:
                    while len(out)>1 and cross(out[-2],out[-1],p)<=1e-10:out.pop()
                    out.append(p)
                return out
            hull=half(pts)[:-1]+half(reversed(pts))[:-1]
            if not 3<=len(hull)<=8:continue
            area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(hull,hull[1:]+hull[:1])))/2
            sx=max(p[0] for p in hull)-min(p[0] for p in hull);sy=max(p[1] for p in hull)-min(p[1] for p in hull)
            if area<.012 or area>.5 or min(sx,sy)<.035 or max(sx,sy)/min(sx,sy)<1.5 or area/(sx*sy)<.85:continue
            if max(p[0] for p in ps)-min(p[0] for p in ps)>.65*body_width:continue
            inner=[tuple(origin[k]+u[k]*x+v[k]*y for k in range(3)) for x,y in hull]
            outer=[tuple(origin[k]+u[k]*x*(1+2*padding/sx)+v[k]*y*(1+2*padding/sy)-depth*n[k] for k in range(3)) for x,y in hull]
            for i in range(len(hull)):
                j=(i+1)%len(hull);emit([inner[i],inner[j],outer[i]]);emit([inner[j],outer[j],outer[i]])
            result.append({'object':obj,'material':material,'source_faces':[fi for fi,t in component],
                           'padding_m':padding,'depth_m':depth,'area_m2':area,'front':front,'rear':rear})
    return result
