"""Optional offline DX/DXT preview source renderer; separate cameras per UI role.

Consumes user-owned MR vehicle resources, without Blender or GT dependencies.
Uses fixed approximate diffuse light, calibrated frontend perspective and a
separate orthographic side camera, supersampling
before SDK composition. It does not simulate native runtime reflections.
"""
import argparse,dataclasses,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.addon_sdk.ui_preview import PROFILES
import gtmat,vmesh_raster as raster

def frame_camera(points,camera,W,H,padding=12):
    """Fit the projected box, including perspective's asymmetric screen centre.

    Scale alone is insufficient: a model centred in world space can project
    off-centre and lose its nose/wheels before any PNG normalization occurs.
    """
    camera.scale=1.;camera.offset=(0.,0.)
    projected=[raster._project(p,camera,0,0) for p in points]
    limits=[(min(p[k] for p in projected),max(p[k] for p in projected)) for k in (0,1)]
    spans=[b-a for a,b in limits]
    if min(spans)<=0:raise ValueError('degenerate preview silhouette')
    camera.scale=min((W-2*padding)/spans[0],(H-2*padding)/spans[1])
    camera.offset=tuple(-(a+b)*camera.scale/2 for a,b in limits)
    ps=[raster._project(p,camera,W,H) for p in points]
    bounds=[min(p[k] for p in ps) for k in (0,1)]+[max(p[k] for p in ps) for k in (0,1)]
    if bounds[0]<padding-1e-6 or bounds[1]<padding-1e-6 or bounds[2]>W-padding+1e-6 or bounds[3]>H-padding+1e-6:raise ValueError('source projection clips viewport')
    return bounds

def render_sources(family,out,*,roles=None,azimuth=None,elevation=None,padding=12,model_name='complete.dx',wheel_profile=None):
    if roles is not None and (not roles or len(set(roles))!=len(roles) or set(roles)-set(PROFILES)):raise ValueError('unknown preview roles')
    if type(padding)is not int or not 1<=padding<=64:raise ValueError('preview padding must be 1..64 pixels')
    for value,low,high in ((azimuth,-360,360),(elevation,-85,85)):
        if value is not None and (type(value)not in(int,float) or not math.isfinite(value) or not low<=value<=high):raise ValueError('UI camera outside supported bounds')
    if out.exists():raise ValueError('output exists')
    if model_name not in ('car.dx','complete.dx'):raise ValueError('unsupported preview model')
    model=parse_dx_bytes((family/model_name).read_bytes())
    if len(model.vertices.positions)>200000 or sum(d.triangle_count for d in model.physical_draws)>100000:raise ValueError('preview model exceeds offline budget')
    out.mkdir(parents=True);items=raster.load_dx_family(family,model_name);geoms=source_geometry(model)
    if not model.diagnostics.validated:raise ValueError('invalid source DX')
    if model_name=='car.dx':
        from master_rallye.preview_scene import preview_transform
        config=wheel_profile or {};instances=config.get('race_wheel_instances',[])
        if len(instances)!=4 or not config.get('provenance'):raise ValueError('Race artwork requires four source-qualified presentation wheel instances')
        wheel=parse_dx_bytes((family/'wheel.dx').read_bytes());wheel_geoms=source_geometry(wheel);wheel_items=raster.load_dx_family(family,'wheel.dx')
        if not wheel.diagnostics.validated:raise ValueError('invalid wheel DX')
        if len(model.vertices.positions)+4*len(wheel.vertices.positions)>200000 or sum(d.triangle_count for d in model.physical_draws)+4*sum(d.triangle_count for d in wheel.physical_draws)>100000:raise ValueError('assembled preview exceeds offline budget')
        for instance in instances:
            vec,scale=preview_transform(instance)
            for index,item in enumerate(wheel_items):
                g=wheel_geoms[index];vertices=tuple(dataclasses.replace(v,position=vec(v.position,True),normal=vec(v.normal)) for v in g.vertices)
                triangles=tuple((a,c,b) if math.prod(scale)<0 else (a,b,c) for a,b,c in g.triangles)
                new=dataclasses.replace(g,vertices=vertices,triangles=triangles);tris=[]
                for ids in triangles:tris.append(tuple(vertices[i].position for i in ids)+tuple(vertices[i].uvs[0] if vertices[i].uvs else (0.,0.) for i in ids)+tuple(tuple(vertices[i].color[:3]) for i in ids))
                geoms[len(items)]=new;items.append(dataclasses.replace(item,tris=tris))
    points=[v.position for g in geoms.values() for v in g.vertices];centre=tuple((min(p[k] for p in points)+max(p[k] for p in points))/2 for k in range(3));reports={}
    for role,profile in PROFILES.items():
        if roles is not None and role not in roles:continue
        angles=(profile['camera'][0] if azimuth is None else azimuth,profile['camera'][1] if elevation is None else elevation)
        camera=raster.Camera(*angles,1,centre,profile['distance'])
        W,H=512,320;projection_bounds=frame_camera(points,camera,W,H,padding);lit=[];mask=[]
        light=(.50,.75,.45) if role=='vehicle_select_art' else (-.5,.8,.3);length=math.sqrt(sum(x*x for x in light));light=tuple(x/length for x in light)
        for d,item in enumerate(items):
            g=geoms[d];tris=[];white=[]
            for t,ids in zip(item.tris,g.triangles):
                colors=[]
                for idx in ids:
                    v=g.vertices[idx];strength=profile['ambient']+profile['key']*max(0,sum(a*b for a,b in zip(v.normal,light)))
                    colors.append(tuple(min(255,round(c*strength)) for c in v.color[:3]))
                tris.append((*t[:6],*colors));white.append((*t[:6],(255,255,255),(255,255,255),(255,255,255)))
            texture=item.texture
            if texture:
                w,h,p=texture;p=bytearray(p)
                for i in range(0,len(p),4):p[i:i+3]=b'\xff\xff\xff'
                texture=(w,h,bytes(p))
            lit.append(dataclasses.replace(item,tris=tris));mask.append(dataclasses.replace(item,tris=white,texture=texture))
        rgb=raster.render(lit,camera,W,H,bg=(0,0,0));alpha=raster.render(mask,camera,W,H,bg=(0,0,0));rgba=bytearray()
        for i in range(W*H):
            a=alpha[3*i];rgba.extend([min(255,round(c*255/a)) if a else 0 for c in rgb[3*i:3*i+3]]+[a])
        (out/(role+'.png')).write_bytes(gtmat.png_from_rgba(W,H,rgba));reports[role]={'camera_azimuth':camera.az,'camera_elevation':camera.el,'distance_m':camera.distance,'projection':'perspective' if camera.distance else 'orthographic','source_size':[W,H],'projection_bounds':projection_bounds,'viewport_padding':padding,'image_plane_offset':list(camera.offset),'lighting':'fixed diffuse approximation; no environment reflection','profile':'mr-native-v1','source_model':model_name,'wheel_provenance':(wheel_profile or {}).get('provenance','embedded frontend geometry')}
    (out/'render.json').write_text(json.dumps(reports,indent=2));return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vehicle-family',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(render_sources(a.vehicle_family,a.output),indent=2))
