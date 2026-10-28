"""Automatic GT3 build profile: no hand-written hubs, envelopes or pins.

Derives every per-car field of the `gt3_vehicle.build` profile from the
source car itself plus the chosen MR donor:

* selections: model 0, LOD0 (always, arches are real geometry there), default
  callback branches; unresolved callbacks are retried with branch 0;
* wheel arches: side-view raster of the outer body skin -> circle fit per
  axle -> GT wheelbase, track and arch radius;
* fitment (the accepted Subaru Impreza Prototype approach): the body is
  uniformly scaled so its wheelbase equals the donor's embedded hub spacing
  and placed so arch centres sit on the donor hubs; the visual tyre keeps the
  donor (MR) envelope, limited by the arch; rim/tyre ratio 0.80;
* references: donor models / environment hashed at derivation time.

Mode `standard` uses stock MR tyres (donor geometry + donor textures) and MR
material conventions; `full` keeps GT tyre imagery and all source passes.
"""
from __future__ import annotations
import gzip,hashlib,math
from pathlib import Path
import numpy as np
from .gt3_source import inspect_car,read_source
from .addon_sdk.gt3_scene import reconstruct,GT3_CORE_SHA256,packet_has_uvs
from .dx import parse_dx_bytes
from .preview_scene import presentation_wheels

MODES=('standard','full')
GRID=.01


def digest(raw):return hashlib.sha256(raw).hexdigest()


def resolve_callbacks(raw,component,*,engine_sha256=GT3_CORE_SHA256,lod=0,limit=8):
    """Default branches; any callback the trace blocks on is retried with 0."""
    callbacks={'0':0,'7':0}
    for _ in range(limit):
        try:
            scene=reconstruct(raw,component=component,lod=lod,callbacks=callbacks,engine_sha256=engine_sha256,strict_textures=False)
            return callbacks,scene
        except ValueError as exc:
            text=str(exc)
            if 'unresolved' not in text:raise
            import re
            ids=[i for i in re.findall(r"'(?:callback(?:_id)?|parameter)': (\d+)",text)if i not in callbacks]
            if not ids:raise
            callbacks[ids[0]]=0
    raise ValueError('GT3 callback resolution budget exceeded')


def wheel_face_bindings(scene,texture_sets):
    """Candidate source-image bindings only for external packets with UVs.

    UV presence excludes generated texgen passes; it does not prove the image
    identity. The second-bank candidate still requires visual qualification.
    """
    bindings={};with_uv=[];without_uv=[]
    for d in scene['draws']:
        if 'runtime external environment texture'not in d['issues']:continue
        slot=d['state'].get('external_texture_index')
        if slot is None:continue
        record={'shape':d['source_shape'],'packet':d['packet'],'slot':slot}
        if not packet_has_uvs(d['vertices'],d['triangles']):without_uv.append(record);continue
        with_uv.append(record)
        if len(texture_sets)>1 and texture_sets[1]['textures']>0:
            bindings[str(slot)]={'texture_set':1,'texture':0,'evidence':'Automatic candidate: original UV-bearing external wheel packet uses second-bank face image 0; image identity still needs visual qualification. No-UV texgen packets are excluded by the source adapter.'}
    return bindings,{'uv_bearing_external_packets':with_uv,'unbound_no_uv_packets':without_uv,'boundary':'Original UV prerequisite, not proof of native GT3 external-slot dispatch.'}


def body_triangles(scene,*,with_alpha=False):
    """Triangles in the MR frame (source front -Z -> MR front +Z).

    With `with_alpha`, also return per-triangle (uv[3], alpha image or None)
    so texture cut-outs (GT arch openings drawn by alpha) count as empty."""
    out=[];extra=[]
    for d in scene['draws']:
        vs=d['vertices'];tex=d.get('texture');alpha=None
        # Untextured blended passes are reflection overlays over the real
        # surface; they would fill alpha-cut wheel arches in the silhouette.
        if with_alpha and tex is None and d['gif'].get('blend'):continue
        if tex is not None:
            reg=tex['registers'];a=np.frombuffer(bytes(tex['rgba_ps2']),np.uint8)[3::4].reshape(tex['height'],tex['width'])
            alpha=a if reg.get('tcc',1)else None
        for t in d['triangles']:
            out.append([(-vs[i]['position'][0],vs[i]['position'][1],-vs[i]['position'][2])for i in t])
            if with_alpha:extra.append(([tuple(vs[i]['uv'])if vs[i]['uv']else(0.,0.)for i in t],alpha))
    tris=np.asarray(out,dtype=float)
    return (tris,extra)if with_alpha else tris


def side_raster(tris,extra=None):
    """Occupancy (y,z) image of outward-facing outer skin, per-slice width."""
    zmin,zmax=float(tris[:,:,2].min()),float(tris[:,:,2].max());nz=int((zmax-zmin)/GRID)+3;ny=int(max(1.,tris[:,:,1].max()+.1)/GRID)+3
    cz=tris[:,:,2].mean(1);cx=tris[:,:,0].mean(1)
    # Local half-width per 10 cm section: flared arches are wider than the cabin.
    section=((cz-zmin)/.1).astype(int);width=np.zeros(section.max()+1)
    np.maximum.at(width,section,np.abs(cx))
    n=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);l=np.linalg.norm(n,axis=1)+1e-12
    keep=(tris[:,:,1].max(1)>=.1)&(np.abs(cx)>=width[section]-.06)&(np.abs(n[:,0])/l>=.25)&(np.sign(n[:,0])==np.sign(cx))
    img=np.zeros((ny,nz),bool)
    for k in np.nonzero(keep)[0]:
        t=tris[k];zs=(t[:,2]-zmin)/GRID;ys=t[:,1]/GRID
        z0,z1=max(0,int(zs.min())),min(nz-1,int(zs.max())+1);y0,y1=max(0,int(ys.min())),min(ny-1,int(ys.max())+1)
        if z1<z0 or y1<y0:continue
        Z,Y=np.meshgrid(np.arange(z0,z1+1)+.5,np.arange(y0,y1+1)+.5)
        a,b,c=np.stack([zs,ys],1)
        area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        if abs(area)<.05:continue # degenerate in side view (faces front/back)
        d1=(b[0]-a[0])*(Y-a[1])-(b[1]-a[1])*(Z-a[0]);d2=(c[0]-b[0])*(Y-b[1])-(c[1]-b[1])*(Z-b[0]);d3=(a[0]-c[0])*(Y-c[1])-(a[1]-c[1])*(Z-c[0])
        sign=1. if area>0 else -1.;tol=-.5*max(1.,math.sqrt(abs(area)))
        inside=(sign*d1>=tol)&(sign*d2>=tol)&(sign*d3>=tol)
        if extra is not None and extra[k][1] is not None and inside.any():
            uv,alpha=extra[k];h,w=alpha.shape
            # Barycentric UV per pixel; PS2 alpha <= 32 (of 128) is a hole.
            wa=np.clip(d2*sign/abs(area),0,1);wb=np.clip(d3*sign/abs(area),0,1);wc=np.clip(1-wa-wb,0,1)
            u=wa*uv[0][0]+wb*uv[1][0]+wc*uv[2][0];v=wa*uv[0][1]+wb*uv[1][1]+wc*uv[2][1]
            xi=(np.mod(u,1.)*w).astype(int).clip(0,w-1);yi=(np.mod(v,1.)*h).astype(int).clip(0,h-1)
            inside&=alpha[yi,xi]>32
        img[y0:y1+1,z0:z1+1]|=inside
    return img,zmin,width


def _circle(points):
    p=np.asarray(points);A=np.c_[2*p[:,0],2*p[:,1],np.ones(len(p))];b=(p**2).sum(1)
    cz,cy,k=np.linalg.lstsq(A,b,rcond=None)[0];return cz,cy,math.sqrt(max(1e-9,k+cz*cz+cy*cy))


def detect_arches(tris,extra=None):
    """Front/rear arch circles from the side silhouette bottom edge."""
    img,zmin,width=side_raster(tris,extra);nz=img.shape[1]
    # Ground strips (GT tyre shadows/splash boards) live below ~12 cm.
    img=img.copy();img[:int(.12/GRID)]=False
    bottom=np.array([np.argmax(img[:,z])if img[:,z].any()else -1 for z in range(nz)],float)*GRID
    valid=bottom>=0
    if valid.sum()<50:raise ValueError('GT body side silhouette too sparse for arch detection')
    sill=float(np.percentile(bottom[valid],15))
    raised=valid&(bottom>sill+.12)
    runs=[];start=None
    for z in range(nz):
        if raised[z]and start is None:start=z
        if (not raised[z]or z==nz-1)and start is not None:
            end=z if raised[z]else z-1
            if (end-start)*GRID>=.25:runs.append((start,end))
            start=None
    mid=(nz-1)/2;front=[r for r in runs if (r[0]+r[1])/2>mid];rear=[r for r in runs if (r[0]+r[1])/2<=mid]
    if not front or not rear:raise ValueError('GT arches not found on both axles')
    arches={}
    for name,group in (('front',front),('rear',rear)):
        fits=[]
        for a,b in sorted(group,key=lambda r:r[0]-r[1]):
            # Fit only the curved part of the arch edge, not the vertical lips.
            top=bottom[a:b+1].max();edge=[(zmin+(z+.5)*GRID,bottom[z])for z in range(a,b+1)if bottom[z]>sill+.35*(top-sill)]
            if len(edge)<8:continue
            cz,cy,r=_circle(edge)
            if .22<=r<=.6 and -.1<=cy<=.5 and zmin+a*GRID-.1<=cz<=zmin+(b+1)*GRID+.1:fits.append((a,b,top,cz,cy,r))
        if not fits:raise ValueError(f'no plausible {name} wheel arch circle')
        a,b,top,cz,cy,r=fits[0]
        zs=tris[:,:,2];near=np.abs(zs.mean(1)-cz)<r
        outer=float(np.abs(tris[near][:,:,0]).max())if near.any()else float(width.max())
        arches[name]={'centre_z':float(cz),'centre_y':float(cy),'radius':float(r),'chord':[zmin+a*GRID,zmin+(b+1)*GRID],'top_y':float(top),'outer_x':outer}
    arches['wheelbase']=arches['front']['centre_z']-arches['rear']['centre_z'];arches['sill_y']=sill
    if not 1.6<=arches['wheelbase']<=3.6:raise ValueError(f"implausible detected wheelbase {arches['wheelbase']:.3f} m")
    return arches


def donor_geometry(donor):
    donor=Path(donor);models={n:(donor/n).read_bytes()for n in ('car.dx','complete.dx','wheel.dx')}
    car,complete,wheel=(parse_dx_bytes(models[n])for n in ('car.dx','complete.dx','wheel.dx'))
    pose=presentation_wheels(car,complete,wheel,diagnostics=True);hubs=[w['translation']for w in pose['race_wheel_instances']]
    dy=pose['body_translation'][1]
    frontend=[[h[0],h[1]+dy,h[2]]for h in hubs]
    zf=max(h[2]for h in hubs);zr=min(h[2]for h in hubs)
    wp=wheel.vertices.positions
    return {'models':models,'frame_dy':dy,'frontend_hubs':frontend,'wheelbase':zf-zr,'hub_mid_z':(zf+zr)/2,
            'hub_y':sum(h[1]for h in frontend)/4,'track_half':sum(abs(h[0])for h in hubs)/4,
            'wheel_radius':max(math.hypot(p[1],p[2])for p in wp),'wheel_half_width':max(abs(p[0])for p in wp),'wheel':wheel}


def rank_donors(arches,retail_vehicles):
    """Retail families ordered by wheelbase/track similarity (suggestion only)."""
    rows=[]
    for folder in sorted(Path(retail_vehicles).iterdir()):
        try:g=donor_geometry(folder)
        except Exception:continue
        track=(arches['front']['outer_x']+arches['rear']['outer_x'])/2-.12
        score=abs(math.log(g['wheelbase']/arches['wheelbase']))+.5*abs(math.log(g['track_half']/max(.3,track)))
        rows.append({'family':folder.name,'score':round(score,4),'wheelbase':round(g['wheelbase'],3),'track_half':round(g['track_half'],3),'body_scale':round(g['wheelbase']/arches['wheelbase'],4)})
    return sorted(rows,key=lambda r:r['score'])


def stock_tyre_draws(wheel):
    """Donor tyre roles by geometry: tread = widest-normal-radial draw."""
    from .topology_writer import source_geometry
    g=source_geometry(wheel);rows=[]
    for d in wheel.physical_draws:
        if d.tag!=2 or any(d.flags_0x20[:2]):continue
        vs=g[d.draw_index].vertices
        radial=sum(abs(math.hypot(v.normal[1],v.normal[2]))for v in vs)/len(vs);rmin=min(math.hypot(v.position[1],v.position[2])for v in vs)
        rows.append((d.draw_index,radial,rmin))
    if len(rows)<3:raise ValueError('donor wheel lacks separate tyre draws')
    tread=max(rows,key=lambda r:r[1]);rest=sorted((r for r in rows if r is not tread),key=lambda r:-r[2])
    # Sidewall = outermost annulus among the axial draws; inner = next; rim draws excluded.
    side=[r for r in rest if r[2]>.5*tread[2]]
    if len(side)<2:side=rest[:2]
    return {'tread':tread[0],'sidewall':side[0][0],'inner':side[1][0]}


def derive(source,donor,*,mode='standard',environment_reference='whitepaint-tga.dxt',identity=None,model_key=None,engine_sha256=GT3_CORE_SHA256):
    """Return (profile, report). `source` may be a gzip'd GT3 cars/day member."""
    if mode not in MODES:raise ValueError('mode must be standard or full')
    raw=read_source(source);inspect_car(raw);donor=Path(donor)
    body_callbacks,body=resolve_callbacks(raw,'body',engine_sha256=engine_sha256)
    wheel_callbacks,wheel=resolve_callbacks(raw,'wheel',engine_sha256=engine_sha256)
    arches=detect_arches(*body_triangles(body,with_alpha=True));g=donor_geometry(donor)
    scale=g['wheelbase']/arches['wheelbase']
    warnings=[]
    if not .8<=scale<=1.25:warnings.append(f'body scale {scale:.3f} to fit donor wheelbase is large; choose a closer donor (see donor ranking)')
    gt_mid=(arches['front']['centre_z']+arches['rear']['centre_z'])/2
    # Fitted lip circles sit below the hub; a GT tyre fills the arch minus ~6 cm.
    gt_y=sum(max(arches[k]['centre_y'],arches[k]['radius']-.06)for k in ('front','rear'))/2;arches['hub_y']=gt_y
    arch_r=min(arches['front']['radius'],arches['rear']['radius'])*scale
    tyre_r=min(g['wheel_radius'],arch_r-.015)
    if tyre_r<g['wheel_radius']-.06:warnings.append(f'arch limits visual tyre to {tyre_r:.3f} m (donor {g["wheel_radius"]:.3f} m); wheels float unless physics WheelRadius follows')
    hub_x=g['track_half'];half_width=min(g['wheel_half_width'],.13)
    translation=[0.,g['hub_y']-gt_y*scale,g['hub_mid_z']-gt_mid*scale]
    # Some external slots point at the wheel's second texture set (face image).
    tex_sets=inspect_car(raw)['wheel']['texture_sets'];bindings,binding_audit=wheel_face_bindings(wheel,tex_sets)
    references={n:digest(v)for n,v in g['models'].items()}
    env=donor/environment_reference
    if not env.is_file():raise ValueError('donor environment reference missing: '+environment_reference)
    references[environment_reference]=digest(env.read_bytes())
    tyres=stock_tyre_draws(g['wheel'])
    profile={'version':1,'source_sha256':digest(raw),'engine_sha256':engine_sha256,'model_key':model_key or '0x0',
        'source_identity':identity or {'source':Path(source).name},
        'selections':{'body':{'model':0,'lod':0,'callbacks':body_callbacks,'external_texture_bindings':{}},
                      'wheel':{'model':0,'lod':0,'callbacks':wheel_callbacks,'external_texture_bindings':bindings}},
        'lighting_policy':{'lighting_fallback':'native_mr_lighting','evidence':'Automatic profile: MR fixed-function lighting replaces GT3 VU lighting.'},
        'material_policy':{'qualified_environment':True,'clip_clamp_geometry':True,'strict':False,**({'max_texture_dim':256}if mode=='standard'else{})},
        'references':references,
        'wheel':{'reference_part':0,'radius_m':round(.8*tyre_r,4),'outboard_x_m':-round(half_width*.9,4),'source_outward_x':-1,'evidence':'Automatic: rim/tyre ratio 0.80 inside the donor MR wheel envelope.'},
        'tyre':{'draws':tyres,'radius_m':round(tyre_r,4),'bead_radius_m':round(.8*tyre_r,4),'half_width_m':round(half_width,4),'tread_band':[0,.5625],'sidewall_band':[.625,.96875],
                'evidence':'Automatic: donor MR tyre topology scaled to the arch-limited donor envelope.','texture':'stock' if mode=='standard' else 'source'},
        'assembly':{'environment_reference':environment_reference,'body_translation_m':[round(v,4)for v in translation],'body_scale':round(scale,5),
                    'race_body_translation_m':[0.,round(-g['frame_dy'],4),0.],
                    'frontend_hubs_m':[[round(v,4)for v in h]for h in sorted(g['frontend_hubs'],key=lambda h:(-h[2],h[0]))],
                    'evidence':f"Automatic: GT arches wheelbase {arches['wheelbase']:.3f} m scaled x{scale:.4f} onto donor {donor.name} hubs (wheelbase {g['wheelbase']:.3f} m)."},
        'mode':mode,
        'limitations':['Automatic profile: arch detection and donor fit are geometric estimates; owner in-game check required.',
                       'GT3 VU lighting approximated with MR lighting.','Race wheels use donor physics hubs; body scaled to that wheelbase.']+warnings}
    report={'arches':arches,'donor':{'family':donor.name,'wheelbase':g['wheelbase'],'track_half':g['track_half'],'wheel_radius':g['wheel_radius'],'frame_dy':g['frame_dy']},
            'body_scale':scale,'tyre_radius':tyre_r,'warnings':warnings,'source_triangles':body['report']['selected_triangles'],'wheel_external_bindings':binding_audit}
    return profile,report
