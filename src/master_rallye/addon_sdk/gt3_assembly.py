"""Explicit MR compatibility wheel fitting, separate from GT3 source decoding.

GT3 rim geometry stays intact. Its normalized local frame is fitted to an
author-declared MR wheel envelope. Stock MR tyre topology is a documented
fallback for GT3's runtime-generated tyre, not a recovered GT3 tyre mesh.
No physical wheel attachment or handling parameter is changed here.
"""
from dataclasses import replace
import math
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry,CompiledVertex,DrawGeometry
from master_rallye.scene_dx_writer import ScenePart

def radial(v):return math.hypot(v.position[1],v.position[2])

def fit_rim(parts,config):
    if set(config)!={'reference_part','radius_m','outboard_x_m','source_outward_x','evidence'}or not config['evidence']:raise ValueError('Explicit GT3 rim fitting profile required')
    no=config['reference_part'];radius=config['radius_m'];outer=config['outboard_x_m'];sign=config['source_outward_x']
    if type(no)is not int or not 0<=no<len(parts)or sign not in (-1,1)or not .1<=radius<=.5 or not -.3<=outer<0:raise ValueError('GT3 MR rim envelope bounds')
    if sign!=-1:raise ValueError('Fit canonical MR -X outward wheel first')
    rr=max(radial(v)for v in parts[no].geometry.vertices)
    if rr<=0:raise ValueError('No source rim radial extent')
    scale=radius/rr;front=min(v.position[0]for p in parts for v in p.geometry.vertices);shift=outer-front*scale
    out=[replace(p,geometry=DrawGeometry(tuple(replace(v,position=(v.position[0]*scale+shift,v.position[1]*scale,v.position[2]*scale),source_vertex_id=None)for v in p.geometry.vertices),p.geometry.triangles))for p in parts]
    return out,{'radius_reference_part':no,'source_radius':rr,'uniform_scale':scale,'axial_frame_translation_m':shift,'profile':config,'boundary':'MR compatibility local rim fit, not native GT3 wheel-instance recovery; no hub relocation.'}

def stock_tyres(reference,config,texture_name):
    """`texture_name=None` keeps the donor MR tyre textures and UVs (standard)."""
    required={'draws','radius_m','bead_radius_m','half_width_m','tread_band','sidewall_band','evidence'}
    if not required<=set(config) or set(config)-required-{'texture'} or not config['evidence']:raise ValueError('Explicit source/stock tyre approximation required')
    roles=config['draws'];m=parse_dx_bytes(reference);g=source_geometry(m)
    if set(roles)!={'sidewall','tread','inner'}or any(type(i)is not int or i not in g for i in roles.values())or len(set(roles.values()))!=3:raise ValueError('Explicit separate stock tyre draws required')
    radius,bead,hw=config['radius_m'],config['bead_radius_m'],config['half_width_m']
    if not .1<bead<radius<=.7 or not .04<=hw<=.3:raise ValueError('MR tyre envelope bounds')
    vs=[v for i in roles.values()for v in g[i].vertices];rhi=max(radial(v)for v in vs);rlo=min(radial(v)for v in g[roles['sidewall']].vertices);xhi=max(abs(v.position[0])for v in vs)
    if not 0<rlo<rhi or xhi<=0:raise ValueError('Stock tyre annulus missing')
    a=(radius-bead)/(rhi-rlo);b=bead-a*rlo;axial=hw/xhi;parts=[]
    for role,i in roles.items():
        d=m.physical_draws[i]
        if d.tag!=2 or d.control_words or any(d.flags_0x20[:2]):raise ValueError('Tyre reference must be ordinary opaque geometry')
        old=g[i];new=[];ts=[];lookup={};band=config['tread_band'if role=='tread'else'sidewall_band']
        if len(band)!=2 or not 0<=band[0]<band[1]<=1:raise ValueError('Source tyre texture bands must be explicit normalized ranges')
        for tri in old.triangles:
            us=[math.atan2(old.vertices[k].position[2],old.vertices[k].position[1])/(2*math.pi)%1 for k in tri]
            if max(us)-min(us)>.5:us=[u+1 if u<.5 else u for u in us]
            ids=[]
            for k,u in zip(tri,us):
                v=old.vertices[k];x,y,z=v.position;r=radial(v);derivative=a if r>=rlo else bead/rlo;target=a*r+b if r>=rlo else r*bead/rlo;f=target/r if r>1e-12 else derivative
                nx,ny,nz=v.normal
                if r>1e-12:
                    nr=(ny*y+nz*z)/r;ny,nz=(ny-nr*y/r)/f+nr*y/r/derivative,(nz-nr*z/r)/f+nr*z/r/derivative
                else:ny/=f;nz/=f
                n=(nx/axial,ny,nz);length=math.sqrt(sum(q*q for q in n));n=tuple(q/length for q in n)if length else(1.,0.,0.)
                fraction=(x/(2*hw/axial)+.5)if role=='tread'else max(0.,min(1.,(target-bead)/(radius-bead)))
                uv=(u,band[0]+fraction*(band[1]-band[0]))if texture_name else v.uvs[0];key=(k,round(u,9))if texture_name else (k,)
                if key not in lookup:
                    lookup[key]=len(new);new.append(CompiledVertex((x*axial,y*f,z*f),n,v.color if texture_name is None else bytes([255]*4),(uv,)))
                ids.append(lookup[key])
            ts.append(tuple(ids))
        parts.append(ScenePart(DrawGeometry(tuple(new),tuple(ts)),(texture_name,'Null','Null')if texture_name else (d.texture_tuple[0],'Null','Null')))
    return parts,{'profile':config,'texture':'donor MR tyre textures/UVs' if texture_name is None else texture_name,'stock_reference_triangles':sum(len(g[i].triangles)for i in roles.values()),'output_triangles':sum(len(p.geometry.triangles)for p in parts),'source_tyre_topology':'Stock MR fallback; GT3 tyre is generated by its runtime','uv':'Explicit source tread/sidewall bands, cylindrical seam split; original source image unchanged.'}

def scale_parts(parts,factor):
    """Uniform body scale about the source origin; normals are unchanged."""
    if not .5<=factor<=2:raise ValueError('Body scale outside 0.5..2')
    if factor==1:return list(parts)
    return [replace(p,geometry=DrawGeometry(tuple(replace(v,position=tuple(c*factor for c in v.position),source_vertex_id=None)for v in p.geometry.vertices),p.geometry.triangles))for p in parts]


def place(parts,translation,angle=0.):
    if len(translation)!=3 or not all(math.isfinite(v)and abs(v)<20 for v in (*translation,angle)):raise ValueError('Invalid explicit wheel/body transform')
    c,s=math.cos(angle),math.sin(angle)
    def vector(p,position=False):
        q=(c*p[0]+s*p[2],p[1],-s*p[0]+c*p[2]);return tuple(q[k]+translation[k]if position else q[k]for k in range(3))
    return [replace(p,geometry=DrawGeometry(tuple(replace(v,position=vector(v.position,True),normal=vector(v.normal),source_vertex_id=None)for v in p.geometry.vertices),p.geometry.triangles))for p in parts]
