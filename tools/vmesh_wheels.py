"""Reusable donor-wheel conversion; no source-car identifiers or proprietary data.

The donor's draw/material identities and hub origin remain fixed. A caller selects
the rim draw explicitly; texture roles are then matched by ordered slot-0 names.
"""
from __future__ import annotations

import dataclasses
import hashlib
import math
from pathlib import Path

import gtmat
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt, decode_rgba_pixels, PNG_ROWS_FLIP_VERTICAL
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, source_geometry, rebuild_topology


def unit(v):
    n = math.sqrt(sum(x*x for x in v))
    return tuple(x/n for x in v) if n > 1e-12 else (1., 0., 0.)


def convert(wheel_bytes: bytes, *, rim_draw: int, segments: int = 36,
            rim_ratio: float | None = None):
    """Resample the existing radial rings and replace the rim by a textured disc.

    Positions stay centred on the original X rotation axis. The maximum Y/Z
    radius is unchanged; width and X offsets are unchanged. This is a donor
    reconstruction, not an import of missing source geometry.
    """
    if not 12 <= segments <= 128:
        raise ValueError("wheel segments must be in [12, 128]")
    model = parse_dx_bytes(wheel_bytes)
    old = source_geometry(model)
    if rim_draw not in old:
        raise ValueError("unknown rim draw")
    if rim_ratio is not None:
        return _profile_wheel(wheel_bytes, model, old, rim_draw, segments, rim_ratio)
    pts = [v.position for g in old.values() for v in g.vertices]
    ry, rz = (max(abs(p[k]) for p in pts) for k in (1, 2))
    if min(ry, rz) <= 1e-6 or max(ry, rz)/min(ry, rz) > 1.2:
        raise ValueError("wheel is not centred on a plausible X rotation axis")
    # Axis extents of a faceted circle can differ just because of vertex angles.
    # Use radial distances; do not infer ellipticity from bounding-box extents.
    radius = max(math.hypot(*p[1:]) for p in pts)
    sy = sz = 1.0
    edits = {}
    for d, g in old.items():
        verts = [dataclasses.replace(v,
                 position=(v.position[0], v.position[1]*sy, v.position[2]*sz),
                 normal=unit((v.normal[0], v.normal[1]/sy, v.normal[2]/sz))) for v in g.vertices]
        # Split each curved edge once. Interpolating radial length retains the
        # tyre's cross-section, while projecting the angle removes large facets.
        cache, tris = {}, []
        def midpoint(a, b):
            key = tuple(sorted((a,b)))
            if key not in cache:
                va, vb = verts[a], verts[b]
                p = tuple((x+y)/2 for x,y in zip(va.position,vb.position))
                r = (math.hypot(*va.position[1:])+math.hypot(*vb.position[1:]))/2
                rr = math.hypot(*p[1:])
                if rr > 1e-8:
                    p = (p[0],p[1]*r/rr,p[2]*r/rr)
                uv = tuple(tuple((x+y)/2 for x,y in zip(u,v)) for u,v in zip(va.uvs,vb.uvs))
                cache[key] = len(verts)
                verts.append(CompiledVertex(p,unit(tuple(x+y for x,y in zip(va.normal,vb.normal))),va.color,uv))
            return cache[key]
        for a,b,c in g.triangles:
            ab,bc,ca = midpoint(a,b),midpoint(b,c),midpoint(c,a)
            tris.extend(((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))
        edits[d] = DrawGeometry(tuple(verts),tuple(tris))
    rim = edits[rim_draw]
    rr = max(math.hypot(*v.position[1:]) for v in rim.vertices)
    centre_x = sum(v.position[0] for v in rim.vertices)/len(rim.vertices)
    side = -1 if centre_x < 0 else 1
    face_x = min(v.position[0] for v in rim.vertices) if side < 0 else max(v.position[0] for v in rim.vertices)
    color = rim.vertices[0].color
    vertices = [CompiledVertex((face_x,0.,0.),(side,0.,0.),color,((.5,.5),))]
    for i in range(segments):
        a = 2*math.pi*i/segments
        y,z = rr*math.cos(a),rr*math.sin(a)
        vertices.append(CompiledVertex((face_x,y,z),(side,0.,0.),color,((.5+z/(2*rr),.5+y/(2*rr)),)))
    triangles = [(0,i+1,(i+1)%segments+1) for i in range(segments)]
    if side < 0:
        triangles = [(a,c,b) for a,b,c in triangles]
    edits[rim_draw] = DrawGeometry(tuple(vertices),tuple(triangles))
    result = rebuild_topology(wheel_bytes,edits,bounds_mode="recompute")
    return result.data, {"method":"donor radial ring resampling, one subdivision, textured rim disc",
                         "rim_draw":rim_draw,"rim_texture":model.physical_draws[rim_draw].texture_slots[0].value,
                         "rim_radius":rr,"tyre_radius":radius,"rim_segments":segments,
                         "scale_yz":[sy,sz],"hub_translation":[0,0,0],"rebuild":result.to_dict()}


def texture_images(wheel_bytes: bytes, donor_dir: Path, rim_png: Path, report: dict, reflection: float = .10,
                   *, preserve_tyre: bool = False, dark_spoke_gaps: bool = False,
                   tyre_bead_guard_texels: float = 0):
    """Author rim and sidewall images in the donor's existing fixed-size slots.

    The input PNG is a complete disc. Alpha on opaque wheels is explicitly a
    reflection control. Solid dark spoke openings remain opaque in this mode.
    """
    if not math.isfinite(reflection) or not 0 <= reflection <= 1:
        raise ValueError("wheel reflection must be in [0, 1]")
    if not math.isfinite(tyre_bead_guard_texels) or not 0<=tyre_bead_guard_texels<=3:
        raise ValueError('tyre bead sampling guard must be in [0,3] texels')
    src = gtmat.GtTexture(rim_png.read_bytes())
    original_model = parse_dx_bytes((donor_dir/'wheel.dx').read_bytes()) if preserve_tyre else None
    original_geometry = source_geometry(original_model) if original_model else None
    if original_geometry:
        old_radius=max(math.hypot(*v.position[1:]) for g in original_geometry.values() for v in g.vertices)
        old_rim=max(math.hypot(*v.position[1:]) for v in original_geometry[report['rim_draw']].vertices)
        old_ratio=old_rim/old_radius
    model = parse_dx_bytes(wheel_bytes)
    rim_name = report["rim_texture"]
    ratio = report["rim_radius"]/report["tyre_radius"]
    images = {}
    for d in model.physical_draws:
        name = d.texture_slots[0].value
        t = parse_dxt(donor_dir/(name+'.dxt'))
        px = bytearray(decode_rgba_pixels(t,PNG_ROWS_FLIP_VERTICAL))
        original_px = bytes(px)
        # The rim draw and side-facing surfaces use planar disc UVs. The tread
        # has a repeatedly tiled U axis and is kept unchanged.
        g = source_geometry(model)[d.draw_index]
        us = [v.uvs[0][0] for v in g.vertices]
        tread = max(us)-min(us) > 2
        unified = report.get("unified_tyre",False)
        if tread and (preserve_tyre or not unified):
            continue
        for y in range(t.height):
            for x in range(t.width):
                u,v = (x+.5)/t.width,(y+.5)/t.height
                r = math.hypot(2*u-1,2*v-1)
                if preserve_tyre and name != rim_name and r > ratio:
                    # Sample only the donor's tyre annulus; move its bead to the
                    # larger rim without importing its old silver disc imagery.
                    guard=min((1-old_ratio)*.25,2*tyre_bead_guard_texels/min(t.width,t.height))
                    sr=old_ratio+guard+(r-ratio)*(1-old_ratio-guard)/(1-ratio)
                    su,sv=.5+(u-.5)*sr/max(r,1e-8),.5+(v-.5)*sr/max(r,1e-8)
                    xx,yy=min(t.width-1,max(0,int(su*t.width))),min(t.height-1,max(0,int(sv*t.height)))
                    pos,sp=(y*t.width+x)*4,(yy*t.width+xx)*4
                    px[pos:pos+4]=original_px[sp:sp+4]
                    continue
                if unified and not preserve_tyre:
                    # A common rubber palette for tread and both sidewalls.
                    # Procedural low-contrast grooves replace mismatched donor imagery.
                    if tread:
                        groove = ((x + (y//4)*2) % 12 < 2) or y % 11 < 2
                        shade = 10 if groove else 23
                    else:
                        shade = 18 + round(6*max(0,min(1,(r-ratio)/max(.01,1-ratio))))
                    px[(y*t.width+x)*4:(y*t.width+x)*4+3] = bytes((shade,shade,shade))
                if not tread and (name == rim_name or r <= ratio):
                    scale = 1 if name == rim_name else ratio
                    su,sv = .5+(u-.5)/scale,.5+(v-.5)/scale
                    sx,sy = min(src.w-1,max(0,int(su*src.w))),min(src.h-1,max(0,int(sv*src.h)))
                    pos,sp = (y*t.width+x)*4,(sy*src.w+sx)*4
                    px[pos:pos+3] = src.rgba[sp:sp+3]
                    if dark_spoke_gaps and src.rgba[sp+3] <= 128:
                        px[pos:pos+4]=bytes((9,10,12,0))
                        continue
                px[(y*t.width+x)*4+3] = round(255*reflection) if name == rim_name or not tread and r <= ratio else 0
        images[name+'.dxt'] = (t.width,t.height,bytes(px))
    return images, {"source_sha256":hashlib.sha256(rim_png.read_bytes()).hexdigest(),
                    "source_geometry_status":"DONOR_RECONSTRUCTION", "texture_role":"explicit supplied disc PNG",
                    "tyre_policy":"original donor tread, resampled donor sidewall annulus" if preserve_tyre else "converted",
                    "spoke_gap_policy":"opaque dark RGB, zero reflection alpha" if dark_spoke_gaps else "source RGB",
                    "reflection":reflection,"rim_to_tyre_radius":ratio,"edited_textures":sorted(images)}


def _profile_wheel(data, model, old, rim_draw, segments, rim_ratio):
    """Reconstruct a common tyre/rim profile in existing material slots.

    The ratio is an explicit visual-fit setting, not an inferred GT3 dimension.
    Exterior radius/width and the X-axis origin are retained from the fitted donor.
    """
    if not math.isfinite(rim_ratio) or not .5 <= rim_ratio <= .9:
        raise ValueError("rim ratio must be finite and in [0.5, 0.9]")
    points = [v.position for g in old.values() for v in g.vertices]
    radius = max(math.hypot(*p[1:]) for p in points)
    hw = max(abs(p[0]) for p in points)
    tread_draws = [d for d,g in old.items() if max(v.uvs[0][0] for v in g.vertices)-min(v.uvs[0][0] for v in g.vertices)>2]
    sides = [d for d in old if d not in tread_draws and d != rim_draw]
    if len(tread_draws)!=1 or len(sides)!=2 or len(old)!=4:
        raise ValueError("profile reconstruction requires one tread, two sides and one rim draw")
    rr = radius*rim_ratio
    color = bytes((255,255,255,255))
    edits = {}
    def mesh_rings(rings,tread=False):
        verts,tris = [],[]
        for j,(x,r,nx,nr) in enumerate(rings):
            for i in range(segments+1):
                a = 2*math.pi*i/segments
                yy,zz = math.cos(a),math.sin(a)
                uv = (i/segments*6,j/(len(rings)-1)) if tread else (.5+zz*r/(2*radius),.5+yy*r/(2*radius))
                verts.append(CompiledVertex((x,yy*r,zz*r),unit((nx,nr*yy,nr*zz)),color,(uv,)))
        for j in range(len(rings)-1):
            for i in range(segments):
                a=j*(segments+1)+i;b=a+1;c=a+segments+1;d=c+1
                for tri in ((a,b,c),(b,d,c)):
                    p,q,r=(verts[k].position for k in tri)
                    u,v = tuple(q[k]-p[k] for k in range(3)),tuple(r[k]-p[k] for k in range(3))
                    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                    if sum(n[k]*verts[tri[0]].normal[k] for k in range(3))<0:tri=(tri[0],tri[2],tri[1])
                    if sum(t*t for t in n)>1e-18:tris.append(tri)
        used=sorted({i for t in tris for i in t})
        remap={old:i for i,old in enumerate(used)}
        return DrawGeometry(tuple(verts[i] for i in used),tuple(tuple(remap[i] for i in t) for t in tris))
    edits[tread_draws[0]]=mesh_rings([(-hw*.7,radius,0,1),(hw*.7,radius,0,1)],True)
    for draw in sides:
        sign=-1 if sum(v.position[0] for v in old[draw].vertices)<0 else 1
        edits[draw]=mesh_rings([(sign*hw*.95,0,sign,0),(sign*hw*.95,rr,sign,0),
                                (sign*hw,radius*.94,sign*.6,.8),(sign*hw*.7,radius,0,1)])
    sign=-1 if sum(v.position[0] for v in old[rim_draw].vertices)<0 else 1
    face_x=sign*hw*.98
    vs=[CompiledVertex((face_x,0,0),(sign,0,0),color,((.5,.5),))]
    for i in range(segments):
        a=2*math.pi*i/segments;y,z=rr*math.cos(a),rr*math.sin(a)
        vs.append(CompiledVertex((face_x,y,z),(sign,0,0),color,((.5+z/(2*rr),.5+y/(2*rr)),)))
    ts=[(0,i+1,(i+1)%segments+1) if sign>0 else (0,(i+1)%segments+1,i+1) for i in range(segments)]
    edits[rim_draw]=DrawGeometry(tuple(vs),tuple(ts))
    result=rebuild_topology(data,edits,bounds_mode="recompute")
    return result.data,{"method":"unified radial tyre profile and explicit rim/tyre ratio", "unified_tyre":True,
                        "rim_draw":rim_draw,"rim_texture":model.physical_draws[rim_draw].texture_slots[0].value,
                        "rim_radius":rr,"tyre_radius":radius,"rim_segments":segments,"rim_ratio":rim_ratio,
                        "tyre_half_width":hw,"hub_translation":[0,0,0],"rebuild":result.to_dict()}


def recess_rim(data: bytes, reference: bytes, *, rim_draw: int, depth_scale=.40, lip_ratio=.94):
    """Optional shallow bowl derived from a stock wheel, with fixed tyre/hub envelope.

    Only an already flat rim is accepted. Remove its redundant outboard sidewall
    cap so the recessed disc cannot be hidden behind the old flat tyre face.
    """
    if not math.isfinite(depth_scale) or not .05<=depth_scale<=.6 or not .85<=lip_ratio<=.98:
        raise ValueError('rim recess parameters outside shallow profile bounds')
    model,stock=parse_dx_bytes(data),parse_dx_bytes(reference)
    geoms,ref=source_geometry(model),source_geometry(stock)
    if rim_draw not in geoms or rim_draw not in ref:raise ValueError('rim draw absent')
    rim=geoms[rim_draw];xs=[v.position[0] for v in rim.vertices]
    if max(xs)-min(xs)>1e-5:raise ValueError('rim already has depth; refusing a second recess')
    rr=max(math.hypot(*v.position[1:]) for v in rim.vertices)
    stock_r=max(math.hypot(*v.position[1:]) for v in ref[rim_draw].vertices)
    stock_depth=max(v.position[0] for v in ref[rim_draw].vertices)-min(v.position[0] for v in ref[rim_draw].vertices)
    if stock_r<=0 or stock_depth<=1e-5:raise ValueError('stock rim has no measured radial depth')
    depth=rr*(stock_depth/stock_r)*depth_scale
    sign=-1 if sum(xs)<0 else 1;outer=sum(xs)/len(xs);inner=outer-sign*depth
    angles=sorted({round(math.atan2(v.position[2],v.position[1])%(2*math.pi),9) for v in rim.vertices if math.hypot(*v.position[1:])>rr*.99})
    if len(angles)<12:raise ValueError('flat rim has too few radial segments')
    color=rim.vertices[0].color
    verts=[CompiledVertex((inner,0,0),(sign,0,0),color,((.5,.5),))]
    for x,radius,bevel in ((inner,rr*lip_ratio,False),(outer,rr,True)):
        for angle in angles:
            yy,zz=math.cos(angle),math.sin(angle)
            n=unit((sign*(rr-rr*lip_ratio),-depth*yy,-depth*zz)) if bevel else (sign,0,0)
            verts.append(CompiledVertex((x,radius*yy,radius*zz),n,color,((.5+radius*zz/(2*rr),.5+radius*yy/(2*rr)),)))
    n=len(angles);tris=[]
    for i in range(n):
        j=(i+1)%n
        for tri in ((0,1+i,1+j),(1+i,1+n+i,1+j),(1+j,1+n+i,1+n+j)):
            if sign<0:tri=(tri[0],tri[2],tri[1])
            tris.append(tri)
    edits={rim_draw:DrawGeometry(tuple(verts),tuple(tris))};removed={}
    for d,g in geoms.items():
        if d==rim_draw or sign*sum(v.position[0] for v in g.vertices)<=0:continue
        # Keep all tyre annulus/tread triangles; only discard a planar centre cap.
        kept=[t for t in g.triangles if not all(math.hypot(*g.vertices[i].position[1:])<=rr+1e-6 for i in t)]
        if len(kept)!=len(g.triangles):
            used=sorted({i for t in kept for i in t});ids={old:new for new,old in enumerate(used)}
            edits[d]=DrawGeometry(tuple(g.vertices[i] for i in used),tuple(tuple(ids[i] for i in t) for t in kept))
            removed[str(d)]=len(g.triangles)-len(kept)
    result=rebuild_topology(data,edits,bounds_mode='recompute')
    return result.data,{'method':'optional stock-derived shallow rim bowl','rim_draw':rim_draw,
                        'stock_depth_m':stock_depth,'stock_radius_m':stock_r,'depth_scale':depth_scale,
                        'recess_depth_m':depth,'lip_ratio':lip_ratio,'rim_radius_m':rr,
                        'removed_redundant_cap_triangles':removed,'hub_translation':[0,0,0],
                        'tyre_geometry_outside_rim':'retained','rebuild':result.to_dict()}


def round_tyre_shoulder(data: bytes, *, rim_draw: int, subdivisions=4):
    """Refine an admitted three-ring outboard annulus with tangent normals.

    Existing radius/maximum width and tread are fixed. This changes visual
    sidewall geometry, not wheel placement or any physics resource.
    """
    if not isinstance(subdivisions,int) or not 2<=subdivisions<=8:raise ValueError('shoulder subdivisions must be in [2,8]')
    model=parse_dx_bytes(data);geoms=source_geometry(model);rim=geoms[rim_draw]
    sign=-1 if sum(v.position[0] for v in rim.vertices)<0 else 1
    rr=max(math.hypot(*v.position[1:]) for v in rim.vertices)
    lip=max(sign*v.position[0] for v in rim.vertices)
    candidates=[d for d,g in geoms.items() if d!=rim_draw and sum(v.position[0]*sign for v in g.vertices)>0
                and max(v.uvs[0][0] for v in g.vertices)-min(v.uvs[0][0] for v in g.vertices)<=2]
    if len(candidates)!=1:raise ValueError('requires one outboard radial sidewall')
    draw=candidates[0];old=geoms[draw]
    rings=[]
    for v in sorted(old.vertices,key=lambda v:math.hypot(*v.position[1:])):
        r=math.hypot(*v.position[1:])
        if r<rr-1e-5:raise ValueError('remove the redundant rim centre cap before rounding')
        if not rings or abs(r-rings[-1][0])>1e-5:rings.append([r,[]])
        rings[-1][1].append(v)
    if len(rings)!=3:raise ValueError('shoulder refinement admits a three-ring radial profile only')
    points=[(sum(sign*v.position[0] for v in vs)/len(vs),sum(math.hypot(*v.position[1:]) for v in vs)/len(vs)) for _,vs in rings]
    (qa,ra),(qb,rb),(qc,rc)=points
    if not ra<rb<rc or qb<max(qa,qc) or lip>qb+1e-5:raise ValueError('invalid tyre shoulder envelope')
    qa=lip  # Seat the rubber bead against the retained outer metal lip.
    angles=sorted({round(math.atan2(v.position[2],v.position[1])%(2*math.pi),9) for v in rings[-1][1]})
    # atan2 at the wrap seam can differ by roundoff; keep a single seam vertex.
    angles=[a for i,a in enumerate(angles) if i==0 or a-angles[i-1]>1e-6]
    if len(angles)>1 and 2*math.pi-angles[-1]+angles[0]<1e-6:angles.pop()
    if len(angles)<12:raise ValueError('insufficient radial segments')
    def hermite(a,b,ta,tb,t):
        t2,t3=t*t,t*t*t
        value=tuple((2*t3-3*t2+1)*a[k]+(t3-2*t2+t)*ta[k]+(-2*t3+3*t2)*b[k]+(t3-t2)*tb[k] for k in range(2))
        tangent=tuple((6*t2-6*t)*a[k]+(3*t2-4*t+1)*ta[k]+(-6*t2+6*t)*b[k]+(3*t2-2*t)*tb[k] for k in range(2))
        return value,tangent
    profiles=[]
    for a,b,ta,tb in (((qa,ra),(qb,rb),(0,rb-ra),(0,rb-ra)),
                      ((qb,rb),(qc,rc),(0,2*(rc-rb)),(qc-qb,0))):
        for j in range(subdivisions):profiles.append(hermite(a,b,ta,tb,j/subdivisions))
    profiles.append(((qc,rc),(qc-qb,0)))
    verts,tris=[],[];color=old.vertices[0].color;n=len(angles)
    for (q,r),(dq,dr) in profiles:
        if not min(qa,qc)-1e-6<=q<=qb+1e-6 or not ra-1e-6<=r<=rc+1e-6:raise ValueError('rounded sidewall escaped original envelope')
        for angle in angles:
            yy,zz=math.cos(angle),math.sin(angle)
            verts.append(CompiledVertex((sign*q,r*yy,r*zz),unit((sign*dr,-dq*yy,-dq*zz)),color,
                                         ((.5+r*zz/(2*rc),.5+r*yy/(2*rc)),)))
    for ring in range(len(profiles)-1):
        for i in range(n):
            j=(i+1)%n;a=ring*n+i;b=ring*n+j;c=(ring+1)*n+i;d=(ring+1)*n+j
            for tri in ((a,b,c),(b,d,c)):
                p,q,r=(verts[k].position for k in tri);u=tuple(q[k]-p[k] for k in range(3));v=tuple(r[k]-p[k] for k in range(3))
                cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                if sum(cross[k]*verts[a].normal[k] for k in range(3))<0:tri=(tri[0],tri[2],tri[1])
                tris.append(tri)
    result=rebuild_topology(data,{draw:DrawGeometry(tuple(verts),tuple(tris))},bounds_mode='recompute')
    return result.data,{'method':'bounded Hermite shoulder rings and tangent-derived normals','draw':draw,
                        'subdivisions_per_section':subdivisions,'rings':len(profiles),'segments':n,
                        'bead_matches_rim_lip':True,'tread_geometry':'unchanged','hub_translation':[0,0,0],
                        'radius_m':rc,'maximum_half_width_m':qb,'rebuild':result.to_dict()}


def metallic_rim_image(wheel_bytes, image, *, rim_draw:int, reflection=.85):
    """Keep gold/source RGB; boost existing environment response only on metal.

    Black spoke gaps have alpha0, remain opaque native geometry and never get
    metallic reflections. The existing chrome helper binding is retained.
    """
    if not math.isfinite(reflection) or not 0<=reflection<=1:raise ValueError('rim reflection must be in [0,1]')
    model=parse_dx_bytes(wheel_bytes);draw=model.physical_draws[rim_draw]
    if draw.flags_0x20[0] or not draw.unknown_0x24&4 or draw.texture_slots[1].value=='Null':
        raise ValueError('metal rim requires existing opaque native environment material')
    w,h,rgba=image;out=bytearray(rgba);metal=dark=0
    for i in range(0,len(out),4):
        if rgba[i+3]>0:out[i+3]=round(255*reflection);metal+=1
        else:dark+=1
    return (w,h,bytes(out)),{'native_helper':draw.texture_slots[1].value,'reflection_alpha':round(255*reflection),
                             'metal_texels':metal,'dark_nonreflective_texels':dark,'source_rgb_unchanged':True,
                             'native_blend_and_test_flags':list(draw.flags_0x20[:2])}


def embed(complete_bytes: bytes, wheel_bytes: bytes, hubs, wheel_draws):
    """Replace frontend wheels with the same mesh used in race, matching slot 0.

    Signed X mirroring places the outward face on each side; winding and normals
    follow that reflection. Steering/spin origins remain local to wheel.dx.
    """
    model, wheel = parse_dx_bytes(complete_bytes),parse_dx_bytes(wheel_bytes)
    source = source_geometry(wheel)
    by_texture = {d.texture_slots[0].value:source[d.draw_index] for d in wheel.physical_draws}
    edits = {}
    for d in wheel_draws:
        name = model.physical_draws[d].texture_slots[0].value
        if name not in by_texture:
            raise ValueError("frontend/race wheel texture roles do not match")
        g = by_texture[name]
        vertices,tris = [],[]
        for h in hubs:
            # Selected donor rim faces -X in local space.
            mirror = 1 if h[0] < 0 else -1
            base = len(vertices)
            for v in g.vertices:
                p,n = v.position,v.normal
                vertices.append(dataclasses.replace(v,position=(h[0]+mirror*p[0],h[1]+p[1],h[2]+p[2]),
                                                    normal=(mirror*n[0],n[1],n[2]), source_vertex_id=None,
                                                    parent_source_vertex_id=None))
            tris.extend(tuple(base+i for i in ((a,c,b) if mirror<0 else (a,b,c))) for a,b,c in g.triangles)
        edits[d] = DrawGeometry(tuple(vertices),tuple(tris))
    return rebuild_topology(complete_bytes,edits,bounds_mode="recompute").data
