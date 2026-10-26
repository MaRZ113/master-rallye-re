"""Stock-profile opaque rim construction, reusing the frozen Subaru algorithm."""
from dataclasses import replace
import math
from .dx import parse_dx_bytes
from .dxt import parse_dxt_bytes,encode_png,encode_dxt_pixels,PNG_ROWS_FLIP_VERTICAL
from .texture_authoring import decode_rgba_png
from .scene_dx_writer import ScenePart,write_scene_dx
from .topology_writer import CompiledVertex,DrawGeometry,source_geometry
from .wheel_layers import stock_profile,layer_rim


def split_geometry(g,count):
    """Keep the qualified fixed draw grammar while distributing one material."""
    if len(g.triangles)<count:raise ValueError('Not enough triangles for existing rim slots')
    parts=[]
    for j in range(count):
        ts=g.triangles[j*len(g.triangles)//count:(j+1)*len(g.triangles)//count]
        ids=sorted({i for t in ts for i in t});mapping={i:k for k,i in enumerate(ids)}
        parts.append(DrawGeometry(tuple(replace(g.vertices[i],source_vertex_id=None)for i in ids),tuple(tuple(mapping[i]for i in t)for t in ts)))
    return parts


def classic_rim(raw,reference,face_texture,config):
    m=parse_dx_bytes(raw);geoms=source_geometry(m);ids=config['rim_draws']
    if ids!=sorted(set(ids))or not ids:raise ValueError('Explicit rim draw set required')
    selected=[m.physical_draws[i]for i in ids]
    if any(d.tag!=2 or d.control_words or any(d.flags_0x20[:2])or d.texture_tuple!=selected[0].texture_tuple or d.unknown_0x24!=7 for d in selected):raise ValueError('Rim must have one qualified opaque environment material')
    vs=[v for i in ids for v in geoms[i].vertices];rr=max(math.hypot(v.position[1],v.position[2])for v in vs)
    sign=-1 if sum(v.position[0]for v in vs)<0 else 1;outer=min(v.position[0]for v in vs)if sign<0 else max(v.position[0]for v in vs)
    ref=stock_profile(reference,config['reference_face'],config['reference_shelf']);segments=ref['source_triangles'][0]
    # Stock's first bevel protrudes 0.17 mm beyond its nominal bead. Reserve
    # that measured distance inward, so the outermost new vertex never exceeds
    # the source rim envelope. This is local construction, not a hub offset.
    refsign=-1 if ref['rings'][0][1]<0 else 1
    clearance=max(0.,max(refsign*(x-ref['rings'][0][1]) for _,x in ref['rings']))*rr/ref['radius']
    outer-=sign*(clearance+1e-6)
    if not 12<=segments<=64:raise ValueError('Unqualified stock radial tessellation')
    color=bytes([255]*4);vertices=[CompiledVertex((outer,0,0),(sign,0,0),color,((.5,.5),))]
    for j in range(segments):
        a=2*math.pi*j/segments;y,z=math.cos(a),math.sin(a)
        vertices.append(CompiledVertex((outer,rr*y,rr*z),(sign,0,0),color,((.5+.5*z,.5+.5*y),)))
    triangles=[(0,1+j,1+(j+1)%segments)if sign>0 else(0,1+(j+1)%segments,1+j)for j in range(segments)]
    # Keep original tyres in this temporary construction so the existing shelf
    # guard sees the full, unchanged wheel envelope rather than a zero-width face.
    parts=[ScenePart(DrawGeometry(tuple(vertices),tuple(triangles)),selected[0].texture_tuple,environment=True)]
    parts.extend(ScenePart(g,m.physical_draws[i].texture_tuple,environment=bool(m.physical_draws[i].unknown_0x24&4))for i,g in geoms.items())
    virtual=write_scene_dx(raw,parts)
    texture=parse_dxt_bytes(face_texture);w,h,rgba=decode_rgba_png(encode_png(texture))
    layered,image,report=layer_rim(virtual,reference,(w,h,rgba),rim_draw=0,reference_face=config['reference_face'],reference_shelf=config['reference_shelf'],shelf_width_scale=config['shelf_width_scale'],face_uv_scale=config['face_uv_scale'])
    g=source_geometry(parse_dx_bytes(layered))[0];v=list(g.vertices);ts=list(g.triangles)
    # A recessed opaque centre, rather than the stock convex hub boss. The
    # source-qualified hub remains at zero; only the optional rim insert changes.
    edge_r,edge_x=report['target_rings'][-1]
    depth=config.get('face_center_depth_m',.006)
    if not 0<=depth<=.015:raise ValueError('Inset centre depth outside recipe limits')
    v[0]=replace(v[0],position=(edge_x-sign*depth,0,0))
    for i in range(1,report['segments']+1):
        y,z=v[i].position[1:];normal=(sign,-depth*y/(edge_r*edge_r),-depth*z/(edge_r*edge_r));length=math.sqrt(sum(q*q for q in normal))
        v[i]=replace(v[i],normal=tuple(q/length for q in normal))
    report['classic_center_x']=v[0].position[0]
    # Opposite corner is outside the guarded inset circular image domain.
    pixels=bytearray(image[2]);dark=(16,18,20,0)
    for y in range(h-7,h):
        for x in range(w-7,w):pixels[(y*w+x)*4:(y*w+x)*4+4]=bytes(dark)
    uv=((w-3.5)/w,1-(h-3.5)/h);back=config['backing_x_m'];radius=rr*.96
    envelope=[min(q.position[0]for g0 in geoms.values()for q in g0.vertices),max(q.position[0]for g0 in geoms.values()for q in g0.vertices)]
    if not envelope[0]<=back<=envelope[1]or sign*(back-outer)>=0:raise ValueError('Backing must be inside the qualified tyre envelope, behind the face')
    def emit(t):ts.append(t if sign>0 else(t[0],t[2],t[1]))
    # Both sides of the rear cap and a dark barrel keep inner/oblique views solid.
    for facing in (sign,-sign):
        offset=len(v);v.append(CompiledVertex((back,0,0),(facing,0,0),color,(uv,)))
        for j in range(segments):
            a=2*math.pi*j/segments;v.append(CompiledVertex((back,radius*math.cos(a),radius*math.sin(a)),(facing,0,0),color,(uv,)))
        for j in range(segments):
            t=(offset,offset+1+j,offset+1+(j+1)%segments);ts.append(t if facing>0 else(t[0],t[2],t[1]))
    edge_r,edge_x=report['target_rings'][-1];offset=len(v)
    for r,x in ((edge_r,edge_x),(radius,back)):
        for j in range(segments):
            a=2*math.pi*j/segments;y,z=math.cos(a),math.sin(a);v.append(CompiledVertex((x,r*y,r*z),(0,-y,-z),color,(uv,)))
    for j in range(segments):
        k=(j+1)%segments;emit((offset+j,offset+k,offset+segments+j));emit((offset+k,offset+segments+k,offset+segments+j))
    full=DrawGeometry(tuple(v),tuple(ts));parts=split_geometry(full,len(ids))
    encoded=encode_dxt_pixels(texture,bytes(pixels),w,h,row_policy=PNG_ROWS_FLIP_VERTICAL)
    return dict(zip(ids,parts)),encoded,{**report,'backing_x_m':back,'rim_triangles_before':sum(len(geoms[i].triangles)for i in ids),'rim_triangles_after':len(full.triangles),'draw_slots_preserved':ids,'tyre_draws_preserved':sorted(set(geoms)-set(ids)),
        'alpha':'original face alpha stays reflection weight; new dark swatch alpha0 in opaque materials, no transparent face'}


def map_embedded_wheels(template,complete,groups,edits):
    """Accept supplied instances only when every original part matches exactly."""
    a=parse_dx_bytes(template);b=parse_dx_bytes(complete);ga=source_geometry(a);gb=source_geometry(b);result={};evidence=[]
    for group in groups:
        draw_ids=group['draws'];tr=group['translation'];angle=group['rotation_y'];c,s=math.cos(angle),math.sin(angle)
        if len(draw_ids)!=len(ga):raise ValueError('Embedded wheel must match every template part')
        def vector(p,position=False):
            q=(c*p[0]+s*p[2],p[1],-s*p[0]+c*p[2]);return tuple(q[k]+tr[k]if position else q[k]for k in range(3))
        for no,target in enumerate(draw_ids):
            old,new=ga[no],gb[target]
            if old.triangles!=new.triangles or len(old.vertices)!=len(new.vertices)or a.physical_draws[no].texture_tuple!=b.physical_draws[target].texture_tuple:raise ValueError('Embedded source topology/material mismatch')
            for x,y in zip(old.vertices,new.vertices):
                if max(abs(p-q)for p,q in zip(vector(x.position,True),y.position))>2e-5 or max(abs(p-q)for p,q in zip(vector(x.normal),y.normal))>2e-5 or x.uvs!=y.uvs or x.color!=y.color:raise ValueError('Embedded source instance differs from qualified transform')
            if no in edits:result[target]=DrawGeometry(tuple(replace(v,position=vector(v.position,True),normal=vector(v.normal),source_vertex_id=None)for v in edits[no].vertices),edits[no].triangles)
        evidence.append({'draws':draw_ids,'translation':tr,'rotation_y':angle,'all_original_parts_match':True})
    return result,evidence
