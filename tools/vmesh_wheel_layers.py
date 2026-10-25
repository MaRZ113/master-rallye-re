"""Optional stock-reference rim shelf and recessed insert, in existing draw slots.

Geometry layers use separate UV regions: full circular face versus guarded solid
metal swatch outside that circle. Tyre draws/UVs/textures and hub origin stay fixed.
"""
from __future__ import annotations
import dataclasses,math
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry,CompiledVertex,DrawGeometry,rebuild_topology

def radius(v):return math.hypot(*v.position[1:])

def stock_profile(reference,face_draw=3,shelf_draw=4):
    model=parse_dx_bytes(reference);geoms=source_geometry(model)
    if face_draw not in geoms or shelf_draw not in geoms:raise ValueError('stock wheel requires separate face and shelf draws')
    face,shelf=geoms[face_draw],geoms[shelf_draw]
    rr=max(radius(v) for v in shelf.vertices)
    rings={}
    for v in shelf.vertices:rings.setdefault(round(radius(v)/rr,5),[]).append(v.position[0])
    if len(rings)!=3:raise ValueError('stock shelf must have exactly three radial rings')
    profile=[(r,sum(xs)/len(xs)) for r,xs in sorted(rings.items(),reverse=True)]
    edge=max(radius(v) for v in face.vertices)/rr
    centers=[v.position[0] for v in face.vertices if radius(v)<1e-5]
    if not centers or abs(edge-profile[-1][0])>1e-4:raise ValueError('stock face/shelf edge mismatch')
    return {'radius':rr,'rings':profile,'center_x':sum(centers)/len(centers),
        'face_draw':face_draw,'shelf_draw':shelf_draw,'source_triangles':[len(face.triangles),len(shelf.triangles)]}

def metal_swatch(image):
    w,h,px=image
    if min(w,h)<32:raise ValueError('rim texture too small for a guarded corner swatch')
    # The circular face samples the unit disc. This 7x7 corner is beyond its
    # footprint and bilinear guard; no source face texel needs moving/rescaling.
    tile=[(x,y) for y in range(7) for x in range(7)]
    if min(math.hypot(2*(x+.5)/w-1,2*(y+.5)/h-1) for x,y in tile)<=1+2/min(w,h):
        raise ValueError('corner swatch intrudes on circular face UV domain')
    metal=[px[i:i+4] for i in range(0,len(px),4) if px[i+3]>128]
    if not metal:raise ValueError('rim has no explicit reflective metal pixels')
    color=bytes(round(sum(p[k] for p in metal)/len(metal)) for k in range(4));out=bytearray(px)
    for x,y in tile:out[4*(y*w+x):4*(y*w+x)+4]=color
    return (w,h,bytes(out)),((3.5)/w,1-(3.5)/h),{'tile':[0,0,7,7],'rgba':list(color),'face_uv_unit_disc_preserved':True}

def layer_rim(data,reference,image,*,rim_draw=3,reference_face=3,reference_shelf=4,shelf_width_scale=1.,face_uv_scale=1.):
    if isinstance(shelf_width_scale,bool) or not math.isfinite(shelf_width_scale) or not .2<=shelf_width_scale<=1:raise ValueError('shelf_width_scale must be between .2 and 1')
    if isinstance(face_uv_scale,bool) or not math.isfinite(face_uv_scale) or not .5<=face_uv_scale<=1:raise ValueError('face_uv_scale must be between .5 and 1')
    model=parse_dx_bytes(data);geoms=source_geometry(model)
    if rim_draw not in geoms:raise ValueError('target rim draw absent')
    original=geoms[rim_draw];rr=max(radius(v) for v in original.vertices)
    sign=-1 if sum(v.position[0] for v in original.vertices)<0 else 1
    radii={round(radius(v)/rr,5) for v in original.vertices}
    if len(radii) not in (2,3) or 0 not in radii:raise ValueError('target must be a flat or simple recessed radial rim; refusing repeated layering')
    bead=[v.position[0] for v in original.vertices if radius(v)>rr*.999]
    if max(bead)-min(bead)>1e-5:raise ValueError('target rim bead is not planar')
    outer=sum(bead)/len(bead)
    ref=stock_profile(reference,reference_face,reference_shelf);refsign=-1 if ref['rings'][0][1]<0 else 1
    rx=ref['rings'][0][1];scale=rr/ref['radius']
    rings=[((1-(1-ratio)*shelf_width_scale)*rr,outer+sign*refsign*(x-rx)*scale) for ratio,x in ref['rings']]
    center=outer+sign*refsign*(ref['center_x']-rx)*scale
    # Preserve the existing rim's outboard plane, including its tyre bead seam.
    center=sign*min(sign*center,sign*outer)
    maxwidth=max(abs(v.position[0]) for g in geoms.values() for v in g.vertices)
    if max(abs(x) for r,x in rings)>maxwidth+1e-6 or abs(center)>maxwidth+1e-6:raise ValueError('stock rim profile exceeds fixed wheel envelope')
    angles=sorted({round(math.atan2(v.position[2],v.position[1])%(2*math.pi),8) for v in original.vertices if radius(v)>rr*.99})
    if not 12<=len(angles)<=128:raise ValueError('unsupported target radial tessellation')
    edited,uv,swatch=metal_swatch(image);vs=[];tris=[];color=bytes((255,255,255,255));n=len(angles)
    edge_r,edge_x=rings[-1];dx=edge_x-center
    vs.append(CompiledVertex((center,0,0),(sign,0,0),color,((.5,.5),)))
    for a in angles:
        y,z=math.cos(a),math.sin(a);normal=(sign, -sign*dx/edge_r*y,-sign*dx/edge_r*z);length=math.sqrt(sum(c*c for c in normal))
        vs.append(CompiledVertex((edge_x,edge_r*y,edge_r*z),tuple(c/length for c in normal),color,((.5+.5*face_uv_scale*z,.5+.5*face_uv_scale*y),)))
    def emit(t):tris.append(t if sign>0 else (t[0],t[2],t[1]))
    for i in range(n):emit((0,1+i,1+(i+1)%n))
    # The insert and shelf meet at the same positions, but have separate vertices
    # and UVs. This keeps artwork off the shelf and both off the tyre sidewall.
    for (r0,x0),(r1,x1) in zip(rings,rings[1:]):
        off=len(vs);dr,dd=r0-r1,x1-x0
        for r,x in ((r0,x0),(r1,x1)):
            for a in angles:
                y,z=math.cos(a),math.sin(a);nn=(sign*dr,sign*dd*y,sign*dd*z);ln=math.sqrt(sum(c*c for c in nn))
                vs.append(CompiledVertex((x,r*y,r*z),tuple(c/ln for c in nn),color,(uv,)))
        for i in range(n):
            j=(i+1)%n;emit((off+i,off+j,off+n+i));emit((off+j,off+n+j,off+n+i))
    result=rebuild_topology(data,{rim_draw:DrawGeometry(tuple(vs),tuple(tris))},bounds_mode='recompute')
    return result.data,edited,{'method':'stock measured three-ring shelf and recessed opaque insert; separate guarded UV domains',
        'reference':ref,'target_radius_m':rr,'target_rings':rings,'center_x':center,'outer_plane':outer,
        'rim_depth_m':abs(edge_x-outer),'center_outward_clamped':True,'segments':n,'face_triangles':n,'shelf_triangles':4*n,
        'shelf_width_scale':shelf_width_scale,'face_uv_scale':face_uv_scale,
        'metal_swatch':swatch,'hub_translation':[0,0,0],'tyre_draws_unchanged':True,'rebuild':result.to_dict()}
