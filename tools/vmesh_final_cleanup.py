"""Opt-in visual finishing operations on existing SDK geometry/material slots.

No controller, wheel fitment, physics or original source vertices are changed.
Model selectors belong in the caller's editable profile, not in these helpers.
"""
from __future__ import annotations
import dataclasses
import math
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, source_geometry, rebuild_topology


def tyre_only_sidewall(original, *, old_ratio, new_ratio, guard_texels=2):
    """Extend donor rubber underneath the entire bead's bilinear footprint.

    The rim has its own opaque draw/texture. Never copy rim imagery into this
    texture, including texels that nominally lie inside the unused disc region.
    """
    w,h,px=original
    if not 0 < old_ratio < new_ratio < 1 or not 0 <= guard_texels <= 3:
        raise ValueError('invalid tyre annulus/guard')
    guard=min((1-old_ratio)*.25,2*guard_texels/min(w,h))
    out=bytearray(len(px))
    for y in range(h):
        for x in range(w):
            u,v=(x+.5)/w,(y+.5)/h
            r=math.hypot(2*u-1,2*v-1)
            sr=old_ratio+guard+max(0,r-new_ratio)*(1-old_ratio-guard)/(1-new_ratio)
            # At the centre choose a harmless rubber sample, not the donor hub.
            dx,dy=((u-.5)/r,(v-.5)/r) if r>1e-8 else (.5,0)
            xx=min(w-1,max(0,int((.5+dx*sr)*w)))
            yy=min(h-1,max(0,int((.5+dy*sr)*h)))
            i,j=4*(y*w+x),4*(yy*w+xx)
            out[i:i+4]=px[j:j+3]+bytes([0])  # opaque draw: alpha controls reflection
    return w,h,bytes(out)


def rim_interior(image):
    """Bake a restrained disc/barrel appearance into nonreflective spoke gaps.

    Geometry remains opaque, including these pixels. Source metal RGB/alpha is
    retained exactly. A radial disc, hub and subtle machining bands give depth
    cues without inventing an independently visible wheel or brake assembly.
    """
    w,h,px=image;out=bytearray(px);changed=0
    for y in range(h):
        for x in range(w):
            i=4*(y*w+x)
            if px[i+3]:continue
            u,v=2*(x+.5)/w-1,2*(y+.5)/h-1;r=math.hypot(u,v)
            if r>.92:shade=10
            elif r<.22:shade=15
            else:
                shade=round(27+9*max(0,1-abs(r-.61)/.37)+2*math.cos(95*r)+3*u)
                if .30<r<.79 and u>.45 and abs(v)<.23:shade=20
            out[i:i+3]=bytes((shade,shade+1,shade+3));changed+=1
    return (w,h,bytes(out)),{'edited_nonreflective_texels':changed,'opaque_face':True,
        'method':'baked dark brake-disc, hub and barrel cues; original metallic pixels untouched'}


def hull_xy(points):
    pts=sorted(set((float(p[0]),float(p[1])) for p in points))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def half(seq):
        out=[]
        for p in seq:
            while len(out)>1 and cross(out[-2],out[-1],p)<=1e-12:out.pop()
            out.append(p)
        return out
    result=half(pts)[:-1]+half(reversed(pts))[:-1]
    if len(result)<3:raise ValueError('projected mask has no area')
    return result


def interpolate(a,b,t):
    def mix(x,y):return tuple(i+(j-i)*t for i,j in zip(x,y))
    return CompiledVertex(mix(a.position,b.position),mix(a.normal,b.normal),
        bytes(round(v) for v in mix(a.color,b.color)),tuple(mix(x,y) for x,y in zip(a.uvs,b.uvs)))


def clip_polygon(vertices,mask):
    """Sutherland-Hodgman in rear XY; interpolate original UV/Z/colour."""
    result=list(vertices)
    for a,b in zip(mask,mask[1:]+mask[:1]):
        def distance(v):
            p=v.position
            return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        out=[]
        for p,q in zip(result,result[1:]+result[:1]):
            dp,dq=distance(p),distance(q);ip,iq=dp>=-1e-12,dq>=-1e-12
            if ip:out.append(p)
            if ip!=iq:out.append(interpolate(p,q,dp/(dp-dq)))
        result=out
        if not result:break
    return result


def constrain_glow(data, *, halo_draw, lens_draw, inset_m=.0015):
    """Clip an existing halo to each taillight's projected source silhouette.

    A convex envelope is admitted only when its area agrees with the projected
    lens triangle area (no overlapping projection or concave missing area).
    Native switch metadata and lit draw positions are retained by the writer.
    """
    if not 0<=inset_m<=.003:raise ValueError('glow inset outside supported range')
    model=parse_dx_bytes(data);geoms=source_geometry(model);lens=geoms[lens_draw]
    masks={};areas={};partitions={}
    for sign in (-1,1):
        ts=[[lens.vertices[i].position for i in t] for t in lens.triangles
            if sum(lens.vertices[i].position[0] for i in t)*sign>0]
        hull=hull_xy([p for t in ts for p in t])
        area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(hull,hull[1:]+hull[:1])))/2
        projected=sum(abs((t[1][0]-t[0][0])*(t[2][1]-t[0][1])-(t[1][1]-t[0][1])*(t[2][0]-t[0][0]))/2 for t in ts)
        if abs(projected-area)>area*.025:raise ValueError('lens projection is not an admitted convex partition')
        cx,cy=sum(p[0] for p in hull)/len(hull),sum(p[1] for p in hull)/len(hull)
        minrad=min(math.hypot(x-cx,y-cy) for x,y in hull)
        scale=max(0,1-inset_m/minrad)
        masks[sign]=[(cx+(x-cx)*scale,cy+(y-cy)*scale) for x,y in hull]
        partitions[sign]=ts
        areas[str(sign)]={'hull_area_m2':area,'projected_triangles_area_m2':projected,'mask':masks[sign]}
    halo=geoms[halo_draw];vs=[];tris=[]
    for t in halo.triangles:
        points=[halo.vertices[i] for i in t]
        sign=-1 if sum(v.position[0] for v in points)<0 else 1
        bounded=clip_polygon(points,masks[sign])
        for surface in partitions[sign]:
            try:mask=hull_xy(surface)
            except ValueError:continue  # edge-on source wall has no rear footprint
            clipped=clip_polygon(bounded,mask)
            a,b,c=surface
            den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            def conform(v):
                x,y=v.position[:2]
                s=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/den
                t=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/den
                z=a[2]+s*(b[2]-a[2])+t*(c[2]-a[2])-.0015
                return dataclasses.replace(v,position=(x,y,z))
            for j in range(1,len(clipped)-1):
                tri=[conform(v) for v in (clipped[0],clipped[j],clipped[j+1])]
                p,q,r=[v.position for v in tri]
                if abs((q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]))<1e-12:continue
                off=len(vs);vs.extend(tri);tris.append((off,off+1,off+2))
    if not tris:raise ValueError('glow mask removed entire halo')
    result=rebuild_topology(data,{halo_draw:DrawGeometry(tuple(vs),tuple(tris))},bounds_mode='recompute')
    return result.data,{'method':'clip halo to source lens triangles, conform 1.5mm over lens; preserve UV, colour and native state',
        'input_triangles':len(halo.triangles),'output_triangles':len(tris),'inset_m':inset_m,
        'lens_envelopes':areas,'rebuild':result.to_dict()}


def add_cap_detail(data,source_map,face_pairs, *, target_draw, sample_uv, sample_rgb, subdivisions=8):
    """Shade source cap triangles as simple reflector cups behind existing glass.

    Subdivision stays exactly on the cap planes, offset 0.35 mm toward the front.
    The original opaque caps remain; covered upper surfaces are not selected.
    A constant opaque texel from the existing lamp atlas avoids repacking livery.
    """
    model=parse_dx_bytes(data);geoms=source_geometry(model);base=geoms[target_draw]
    vs=list(base.vertices);tris=list(base.triangles);records=[]
    byface={r['face']:r for r in source_map}
    for faces in face_pairs:
        selected=[]
        for fi in faces:
            r=byface[fi];g=geoms[r['draw']]
            selected.append([g.vertices[i] for i in g.triangles[r['tri']]])
        ps=[v.position for t in selected for v in t]
        lo=[min(p[k] for p in ps) for k in range(3)];hi=[max(p[k] for p in ps) for k in range(3)]
        if hi[0]-lo[0]<.03 or hi[1]-lo[1]<.03 or hi[2]-lo[2]>.001:raise ValueError('detail requires planar front cap pair')
        def vertex(t,a,b):
            weights=(1-a-b,a,b)
            p=tuple(sum(v.position[k]*w for v,w in zip(t,weights)) for k in range(3))
            x=2*(p[0]-lo[0])/(hi[0]-lo[0])-1;y=2*(p[1]-lo[1])/(hi[1]-lo[1])-1
            radius=math.hypot(x,y)
            shade=22+110*math.exp(-((radius-.68)/.19)**2)+105*math.exp(-((x+.18)**2+(y-.18)**2)/.027)
            shade=min(185,shade)
            color=bytes([min(255,round(shade*255/max(1,c))) for c in sample_rgb]+[255])
            # All UV layers use the same safe constant sample. Material records stay intact.
            return CompiledVertex((p[0],p[1],p[2]+.00035),(0,0,1),color,
                tuple(sample_uv for _ in t[0].uvs))
        for t in selected:
            grid={}
            for a in range(subdivisions+1):
                for b in range(subdivisions+1-a):
                    grid[a,b]=len(vs);vs.append(vertex(t,a/subdivisions,b/subdivisions))
            for a in range(subdivisions):
                for b in range(subdivisions-a):
                    tris.append((grid[a,b],grid[a+1,b],grid[a,b+1]))
                    if a+b<subdivisions-1:tris.append((grid[a+1,b],grid[a+1,b+1],grid[a,b+1]))
        records.append({'source_faces':faces,'bounds':[lo,hi]})
    result=rebuild_topology(data,{target_draw:DrawGeometry(tuple(vs),tuple(tris))},bounds_mode='recompute')
    return result.data,{'method':'subdivided retained opaque cap with simple reflector/bulb shading',
        'caps':records,'generated_triangles':len(tris)-len(base.triangles),'offset_m':.00035,
        'sample_uv':sample_uv,'sample_rgb':sample_rgb,'rebuild':result.to_dict()}


def extend_collar(data,source_map,faces, *, black_draw=9,padding_m=.012,depth_m=.012):
    """Add a bounded backing annulus around an explicit existing recess panel.

    It extends behind the frame, never across the panel mouth. The selector must
    identify a planar two-triangle panel, not an arbitrary opening to cap.
    """
    if not .006<=padding_m<=.015 or not .005<=depth_m<=.015:raise ValueError('collar exceeds small gap bounds')
    import vmesh_surface_repair as s
    model=parse_dx_bytes(data);geoms=source_geometry(model);lookup={r['face']:r for r in source_map}
    points=[]
    for fi in faces:
        r=lookup[fi];g=geoms[r['draw']];points.extend(g.vertices[i].position for i in g.triangles[r['tri']])
    n=s.normal(*points[:3]);n=n if n[2]>0 else tuple(-v for v in n)
    if abs(n[2])<.8 or max(abs(s.dot(s.sub(p,points[0]),n)) for p in points)>.001:raise ValueError('not planar front recess')
    u=s.unit((n[2],0,-n[0]));v=(n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0])
    origin=tuple(sum(p[k] for p in points)/len(points) for k in range(3))
    hull=hull_xy([(s.dot(s.sub(p,origin),u),s.dot(s.sub(p,origin),v)) for p in points])
    sx=max(p[0] for p in hull)-min(p[0] for p in hull);sy=max(p[1] for p in hull)-min(p[1] for p in hull)
    inner=[tuple(origin[k]+u[k]*x+v[k]*y for k in range(3)) for x,y in hull]
    # Small overlap with the existing backing avoids a coplanar duplicate layer.
    inner=[tuple(p[k]-.0007*n[k] for k in range(3)) for p in inner]
    outer=[tuple(origin[k]+u[k]*x*(1+2*padding_m/sx)+v[k]*y*(1+2*padding_m/sy)-depth_m*n[k] for k in range(3)) for x,y in hull]
    base=geoms[black_draw];vs=list(base.vertices);tris=list(base.triangles)
    for i in range(len(inner)):
        j=(i+1)%len(inner)
        for ps in ([inner[i],inner[j],outer[i]],[inner[j],outer[j],outer[i]]):
            off=len(vs);nn=s.normal(*ps)
            vs.extend(CompiledVertex(p,nn,bytes((255,255,255,255)),((.5,.5),)) for p in ps)
            tris.extend(((off,off+1,off+2),(off,off+2,off+1)))
    result=rebuild_topology(data,{black_draw:DrawGeometry(tuple(vs),tuple(tris))},bounds_mode='recompute')
    return result.data,{'source_faces':faces,'padding_m':padding_m,'depth_m':depth_m,
        'mouth_unchanged':True,'generated_triangles':len(tris)-len(base.triangles),'inner':inner,'outer':outer,
        'method':'bounded recess backing annulus behind existing frame, no mouth cap','rebuild':result.to_dict()}
