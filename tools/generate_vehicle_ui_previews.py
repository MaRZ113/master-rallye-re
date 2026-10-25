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

def render_sources(family,out):
    if out.exists():raise ValueError('output exists')
    model=parse_dx_bytes((family/'complete.dx').read_bytes())
    if len(model.vertices.positions)>200000 or sum(d.triangle_count for d in model.physical_draws)>100000:raise ValueError('preview model exceeds offline budget')
    out.mkdir(parents=True);items=raster.load_dx_family(family);geoms=source_geometry(model)
    if not model.diagnostics.validated:raise ValueError('invalid source DX')
    points=[v.position for g in geoms.values() for v in g.vertices];centre=tuple((min(p[k] for p in points)+max(p[k] for p in points))/2 for k in range(3));reports={}
    for role,profile in PROFILES.items():
        camera=raster.Camera(*profile['camera'],1,centre,profile['distance'])
        W,H=512,320;projection_bounds=frame_camera(points,camera,W,H);lit=[];mask=[]
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
        (out/(role+'.png')).write_bytes(gtmat.png_from_rgba(W,H,rgba));reports[role]={'camera_azimuth':camera.az,'camera_elevation':camera.el,'distance_m':camera.distance,'projection':'perspective' if camera.distance else 'orthographic','source_size':[W,H],'projection_bounds':projection_bounds,'viewport_padding':12,'image_plane_offset':list(camera.offset),'lighting':'fixed diffuse approximation; no environment reflection','profile':'mr-native-v1'}
    (out/'render.json').write_text(json.dumps(reports,indent=2));return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vehicle-family',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(render_sources(a.vehicle_family,a.output),indent=2))
