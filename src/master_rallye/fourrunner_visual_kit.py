"""Optional, reversible MR presentation kit; no physics or source mutations."""
from dataclasses import replace
import hashlib
from pathlib import Path
from .assets import AssetResolver
from .dx import parse_dx_bytes
from .dxt import parse_dxt_bytes
from .glass_authoring import subset
from .semantic_aperture import partition,compose_ledger
from .scene_dx_writer import ScenePart
from .topology_writer import CompiledVertex,DrawGeometry,source_geometry
from .addon_sdk.auto_features import feed

OPTIONS=('paint_reflection','mirror_insets','cabin','rear_glazing','underbody_frame')
NAVARA_SHA='2d3727f5bcd889ba38891276111c53f9c4d67cee1f5ece13de374a8235690655'


def options(value):
    if value is None:return dict.fromkeys(OPTIONS,False)
    if not isinstance(value,dict)or set(value)-set(OPTIONS)or any(type(v)is not bool for v in value.values()):
        raise ValueError('Unknown or non-boolean MR visual option')
    return {k:value.get(k,False)for k in OPTIONS}


def box(lo,hi,texture):
    """Closed opaque structural box with independent correctly culled faces."""
    vertices=[];triangles=[]
    for axis in range(3):
        a=(axis+1)%3;b=(axis+2)%3
        for sign in (-1,1):
            normal=tuple(float(sign if k==axis else 0)for k in range(3));start=len(vertices)
            corners=[(0,0),(1,0),(1,1),(0,1)]
            if sign<0:corners=corners[::-1]
            for u,v in corners:
                p=[0.,0.,0.];p[axis]=(hi if sign>0 else lo)[axis];p[a]=(hi if u else lo)[a];p[b]=(hi if v else lo)[b]
                vertices.append(CompiledVertex(tuple(p),normal,bytes([255]*4),((float(u),float(v)),)))
            triangles.extend(((start,start+1,start+2),(start,start+2,start+3)))
    return ScenePart(DrawGeometry(tuple(vertices),tuple(triangles)),(texture,'Null','Null'))


def apply(parts,result,retail_root,retail_sma,assets,value,semantic_report):
    opts=options(value);report={'schema':'mr-visual-kit/1','options':opts,'components':[],
        'physics_hubs_ride_height_unchanged':True,'original_source_unchanged':True,
        'limitations':['Authored MR presentation, not original Evo2 cabin or suspension.',
                       'No animated steering wheel or moving axle solver is introduced.']}
    parts=list(parts);core=[0];body_mapping=semantic_report['body_partition_ledger']
    report['source_scene_sha256']=result['report']['source_scene_sha256']
    report['implementation_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    def record(role,**fields):report['components'].append({'role':role,**fields})
    def texture(root,stem):
        path=AssetResolver(root).resolve_texture(stem)
        if path is None:raise ValueError('MR visual-kit texture missing: '+stem)
        data=path.read_bytes();parse_dxt_bytes(data);sha=hashlib.sha256(data).hexdigest();name='mr-kit-'+sha[:20]+'-tga'
        from .addon_sdk.project import read_sma_member
        if data!=read_sma_member(retail_sma,path.resolve().relative_to(retail_root.resolve()).as_posix()):
            raise ValueError('MR visual-kit reference differs from clean retail SMA')
        target=assets/(name+'.dxt')
        if target.exists()and target.read_bytes()!=data:raise ValueError('MR visual-kit texture collision')
        target.write_bytes(data);record('MR reference texture',source=str(path),source_sha256=sha,target=name)
        return name
    def alpha(part,byte):return replace(part,geometry=replace(part.geometry,vertices=tuple(replace(v,color=v.color[:3]+bytes([byte]))for v in part.geometry.vertices)))
    if not any(opts.values()):return parts,core,report
    navara=retail_root/'DataGx/Vehicles/Navara';terrano=retail_root/'DataGx/Vehicles/Terrano'
    # Body paint uses only whole triangles whose UV corners lie in reviewed
    # paint-only atlas rectangles. Mixed lens/trim/window triangles stay diffuse.
    if opts['paint_reflection']:
        g=parts[0].geometry
        regions=[(110.,18.,248.,117.),(378.,192.,480.,347.),(182.,207.,268.,274.),(5.,351.,210.,398.)]
        selected=[i for i,t in enumerate(g.triangles)if any(all(x0<=g.vertices[v].uvs[0][0]*512<=x1 and y0<=g.vertices[v].uvs[0][1]*512<=y1 for v in t)for x0,y0,x1,y1 in regions)]
        if not selected:raise ValueError('Qualified paint-only atlas selection empty')
        part=parts[0];env=texture(terrano,'silverpaint-tga')
        core.append(len(parts));parts.append(alpha(replace(part,geometry=subset(g,selected),textures=(part.textures[0],env,'Null'),environment=True),46))
        remaining=sorted(set(range(len(g.triangles)))-set(selected))
        parts[0]=replace(part,geometry=subset(g,remaining))
        record('paint environment',flat_draw=core[-1],input_partition_triangle_ids=selected,atlas_rectangles_pixels=regions,
               original_body_triangle_ledger=[body_mapping[i]for i in selected],
               reflection_strength=46/255,opaque=True,evidence='Explicit MR paint-only UV rectangles; mixed triangles remain unchanged. Workshop Material Studio supports strength, disable, Undo and Restore.')
        body_mapping=[body_mapping[i]for i in remaining]
    if opts['mirror_insets']:
        env=texture(terrano,'chrome-tga');stem='mr-kit-mirror-grey-tga';(assets/(stem+'.dxt')).write_bytes(feed(bytes([65,65,65,255]),1,1))
        for row in result['report']['body_draws']:
            if row['node_id']not in ('node-mesh-012','node-mesh-013'):continue
            index=row['draw_index'];part=parts[index];g=part.geometry;ids=[53,54,55]
            if len(g.triangles)!=56:raise ValueError('Qualified mirror topology changed')
            parts[index]=replace(part,geometry=subset(g,sorted(set(range(56))-set(ids))))
            target=len(parts);parts.append(alpha(replace(part,geometry=subset(g,ids),textures=(stem,env,'Null'),environment=True),160))
            record('mirror inset',node_id=row['node_id'],source_triangle_ids=ids,flat_draw=target,original_textures=list(part.textures),
                   interpretation='MR grey/chrome mirror approximation on the original rear-facing inset cap; housing/mount triangles remain source diffuse. No live rear-view renderer.')
    if opts['cabin']:
        raw=(navara/'car.dx').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=NAVARA_SHA:raise ValueError('Qualified Navara cabin revision changed')
        model=parse_dx_bytes(raw);g=source_geometry(model)[0]
        if len(g.triangles)!=293 or model.physical_draws[0].texture_tuple!=('underdash-tga','Null','Null'):
            raise ValueError('Qualified Navara cabin draw changed')
        tex=texture(navara,'underdash-tga')
        for role,ids,scale,offset in [
            ('MR steering wheel',list(range(100,118)),(1.,1.,1.),(-.036056,0.,-.10668)),
            ('MR dashboard',[118,119,120,123,124,125,126,127,128,129,130,131,132,133,134,135,141,145,146,147],(.83,1.,.65),(0.,-.065,.05))]:
            selected=subset(g,ids)
            # Positive diagonal scales preserve handedness and winding.
            def transformed(v):
                n=tuple(v.normal[k]/scale[k]for k in range(3));length=sum(x*x for x in n)**.5
                return replace(v,position=tuple(v.position[k]*scale[k]+offset[k]for k in range(3)),normal=tuple(x/length for x in n))
            target=len(parts);parts.append(ScenePart(replace(selected,vertices=tuple(transformed(v)for v in selected.vertices)),(tex,'Null','Null')))
            record(role,flat_draw=target,source_family='Navara',source_sha256=NAVARA_SHA,source_draw=0,source_triangle_ids=ids,scale=list(scale),translation_m=list(offset),
                   evidence='Original Navara car.txt sw Index100 Size18 and matching independent DX connected component; dashboard bounded selected original underdash surfaces. Steering wheel follows exactly the same rigid offset as the driver; no crew mutation.')
    dark='mr-kit-dark-structure-tga'
    if opts['cabin']or opts['rear_glazing']or opts['underbody_frame']:
        (assets/(dark+'.dxt')).write_bytes(feed(bytes([20,19,18,255]),1,1))
    if opts['rear_glazing']:
        # Original rear windows are Body-atlas geometry, not GlassI/GlassE.
        # Native rear damage is intentionally not created by this option.
        masks=[[(5,296),(66,296),(87,330),(87,341),(5,341)],
               [(101,296),(192,300),(207,330),(198,341),(112,342)],
               [(392,27),(424,43),(434,75),(434,136),(392,151)]]
        # The front of the rear-door window has a near-collinear corner;
        # explicit strict convex masks exclude rubber/paint borders.
        for pixels in masks:
            g=parts[0].geometry
            inside,outside,ledger=partition(g,range(len(g.triangles)),[tuple(x/512 for x in p)for p in pixels],uv_layer=0)
            for side in ('inside','outside'):ledger[side]=compose_ledger(ledger[side],body_mapping)
            body_mapping=ledger['outside']
            if not inside.triangles:raise ValueError('Qualified rear glazing aperture empty')
            part=parts[0];parts[0]=replace(part,geometry=outside);core.append(len(parts))
            parts.append(alpha(replace(part,geometry=inside,alpha=True,alpha_test=False,environment=False),100))
            record('rear glazing',flat_draw=core[-1],atlas_polygon_pixels=pixels,partition_ledger=ledger,
                   interpretation='Optional static MR glazing on original Body surface. No independent rear damage zone.')
    if opts['cabin']or opts['rear_glazing']:
        target=len(parts);parts.append(box((-.55,.38,-1.98),(.55,1.315,-.52),dark))
        record('dark rear cabin backing',flat_draw=target,interpretation='Authored closed opaque inner volume; no see-through empty rear cabin. Not original donor geometry.')
    if opts['underbody_frame']:
        # A body-fixed structural frame is a safe simplified representation:
        # ends stop well inside both wheel envelopes and never pretend to join
        # a sprung hub. No bars are placed in steering/rolling resources.
        beams=[((x-.035,-.075,-1.52),(x+.035,.015,1.52))for x in (-.34,.34)]
        beams += [((-.49,-.095,z-.045),(.49,-.005,z+.045))for z in (-1.353312,1.353312)]
        targets=[]
        for lo,hi in beams:targets.append(len(parts));parts.append(box(lo,hi,dark))
        record('body-fixed underbody frame',flat_draws=targets,beam_bounds_m=beams,
               interpretation='48 triangle MR structural support kit; body-frame crossmembers only. Endpoints X+/-0.49m stay inside original wheels. No unsupported moving axle or disconnected wheel-contact rods; physics/collision/hubs unchanged.')
    return parts,core,report
