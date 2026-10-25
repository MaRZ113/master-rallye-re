"""Read-only runtime-resource audit plus private offline comparison artifacts.

Does not launch the game. Output files stay inside the explicitly supplied stage.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import sys
import zipfile
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt,decode_rgba_pixels,PNG_ROWS_FLIP_VERTICAL
from master_rallye.topology_writer import source_geometry
import vmesh_raster as raster
import vmesh_surface_repair as surfaces
import vmesh_brake_lights as brake_lights


def phase_checks(stage,before):
    family=stage/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    previous=before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    validation=json.loads((stage/'reports/validation-report.json').read_text())
    donor=Path(json.loads((stage/'project/vehicle-project.json').read_text())['source_vehicle_dir'])
    # Compare all sealed resources, not just an assumed family-local physics file.
    manifest=json.loads((stage/'runtime/resource-manifest.json').read_text())
    entries=manifest.get('resources',manifest.get('files',[]))
    if not entries:raise ValueError('sealed resource list unavailable')
    prefix='DataGx/Vehicles/ImprezaProto/'
    unchanged=0;visual_changes=[];editable=[]
    for entry in entries:
        path=entry['path'];current=stage/'runtime/resource-root'/path;prior=before/'runtime/resource-root'/path
        if not prior.exists():raise ValueError(f'previous sealed resource absent: {path}')
        if current.read_bytes()==prior.read_bytes():unchanged+=1;continue
        if path.lower()=='datagame/options.xml':editable.append(path);continue
        if path.startswith(prefix) and Path(path).suffix in ('.dx','.dxt'):visual_changes.append(path);continue
        raise ValueError(f'nonvisual/physics resource regression: {path}')
    frozen={}
    for name in ('addon.json','vehicle.cfg','physics.cfg'):
        if (family/name).exists() and (previous/name).exists():
            if (family/name).read_bytes()!=(previous/name).read_bytes():raise ValueError(f'configuration changed: {name}')
            frozen[name]=sha(family/name)
    car_data=(family/'car.dx').read_bytes();old_data=(previous/'car.dx').read_bytes()
    car,old_car=parse_dx_bytes(car_data),parse_dx_bytes(old_data)
    if car_data[car.collision.offset:car.collision.end_offset]!=old_data[old_car.collision.offset:old_car.collision.end_offset]:
        raise ValueError('collision suffix changed')
    hubs=[]
    for frame in ('car','complete'):
        a=json.loads((before/f'reports/convert-{frame}.json').read_text())['hubs_frame']
        b=json.loads((stage/f'reports/convert-{frame}.json').read_text())['hubs_frame']
        if a!=b:raise ValueError('wheel hub placement changed')
        hubs.append({'frame':frame,'unchanged':True,'hubs':b})
    wheel,old_wheel=(parse_dx_bytes((p/'wheel.dx').read_bytes()) for p in (family,previous))
    wg,owg=source_geometry(wheel),source_geometry(old_wheel)
    def attrs(g):return [(v.position,v.normal,v.color,v.uvs) for v in g.vertices]
    for d in (1,2):
        if attrs(wg[d])!=attrs(owg[d]) or wg[d].triangles!=owg[d].triangles:raise ValueError('tread/inboard wheel geometry changed')
    for axis in range(3):
        for fn in (min,max):
            if abs(fn(p[axis] for p in wheel.vertices.positions)-fn(p[axis] for p in old_wheel.vertices.positions))>1e-6:
                raise ValueError('wheel envelope or width changed')
    texture_hashes={}
    for d in wheel.physical_draws:
        name=d.texture_slots[0].value+'.dxt'
        if d.draw_index in (1,2) and (family/name).read_bytes()!=(previous/name).read_bytes():raise ValueError('tread/inboard wheel texture changed')
        texture_hashes[name]=sha(family/name)
    if (family/'merctread-tga.dxt').read_bytes()!=(donor/'merctread-tga.dxt').read_bytes():raise ValueError('stock tread changed')
    if any(d.flags_0x20[0] for d in wheel.physical_draws):raise ValueError('rim became translucent')
    profile=json.loads((stage/'reports/cleanup-profile.json').read_text())
    rim_pixels=decode_rgba_pixels(parse_dxt(family/'nevwheel-tga.dxt'),PNG_ROWS_FLIP_VERTICAL)
    old_rim_pixels=decode_rgba_pixels(parse_dxt(previous/'nevwheel-tga.dxt'),PNG_ROWS_FLIP_VERTICAL)
    if any(rim_pixels[i]!=old_rim_pixels[i] for i in range(len(rim_pixels)) if i%4!=3):raise ValueError('gold source rim RGB changed')
    target_alpha=round(255*profile['rim_reflection'])
    if any(rim_pixels[i]!=(target_alpha if old_rim_pixels[i]>0 else 0) for i in range(3,len(rim_pixels),4)):
        raise ValueError('metal reflection leaked into dark spoke gaps')
    shoulder=json.loads((stage/'reports/wheel-conversion.json').read_text())['geometry']['tyre_shoulder']
    sg=wg[shoulder['draw']]
    if len(sg.triangles)<=len(owg[shoulder['draw']].triangles) or shoulder['rings']<5:raise ValueError('rounded tyre rings absent')
    if any(abs(math.sqrt(sum(n*n for n in v.normal))-1)>1e-5 for v in sg.vertices):raise ValueError('nonunit tyre normal')
    rim=wg[3];depth=max(v.position[0] for v in rim.vertices)-min(v.position[0] for v in rim.vertices)
    if not .005<depth<.04:raise ValueError('rim depth outside shallow range')
    for frame in ('car','complete'):
        closure=json.loads((stage/f'reports/surface-repair-{frame}.json').read_text())
        if not closure['source_caps_only'] or closure['backing_source_faces'] or closure['top_mask_backing_source_faces']:
            raise ValueError('outer black lamp/decal backing reintroduced')
        if any(max(b['gap_m'])>.004001 for b in closure['bridges']):raise ValueError('wide speculative gap bridge')
    layout=brake_lights.switch_layout(car)
    if layout!=brake_lights.switch_layout(parse_dx_bytes((donor/'car.dx').read_bytes())):raise ValueError('stock switch changed')
    g=source_geometry(car);br=json.loads((stage/'reports/brake-lights.json').read_text())
    if len(g[layout['case2'][0]].triangles)!=br['lit_triangles'] or br['lit_triangles']<2:raise ValueError('source lit geometry absent')
    if len(g[layout['case2'][1]].triangles)!=br['halo_triangles'] or br['halo_triangles']<4:raise ValueError('stock glow absent')
    if len(g[layout['case1'][0]].triangles)!=1:raise ValueError('unexpected off-state emission')
    for name in ('breaklightson-tga.dxt','breaklightsonglow-tga.dxt'):
        if (family/name).read_bytes()!=(donor/name).read_bytes():raise ValueError('native brake texture changed')
    for a,b in zip(car.physical_draws,old_car.physical_draws):
        if (a.tag,a.control_words,a.group_label)!=(b.tag,b.control_words,b.group_label):raise ValueError('native state metadata changed')
    quality=collections.defaultdict(lambda:[0.,0.])
    for index,base in enumerate((before,stage)):
        folder=base/'runtime/resource-root/DataGx/Vehicles/ImprezaProto';m=parse_dx_bytes((folder/'car.dx').read_bytes());gg=source_geometry(m)
        for r in json.loads((base/'source-map/source-map-car.json').read_text())['records']:
            d=m.physical_draws[r['draw']];t=parse_dxt(folder/(d.texture_slots[0].value+'.dxt'))
            pts=[gg[r['draw']].vertices[i].uvs[0] for i in gg[r['draw']].triangles[r['tri']]]
            a,b,c=pts
            quality[r['material']][index]+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))*t.width*t.height/2
    rear=json.loads((stage/'reports/rear-decal-binding.json').read_text())['material']
    if quality[rear][1]<quality[rear][0]*1.6:raise ValueError('rear decal did not gain atlas detail')
    for material in profile['preserve_livery_density_materials']:
        if quality[material][1]<quality[material][0]*.999:raise ValueError('other livery atlas density regressed')
    control={r['material'] for r in validation['coverage_normalized'] if r['policy']=='solid paint control-alpha palette heuristic'}
    routes=json.loads((stage/'source-map/source-map-car.json').read_text())['records']
    if any(car.physical_draws[r['draw']].flags_0x20[0] for r in routes if r['material'] in control):raise ValueError('hood coverage regressed')
    cap_materials={r['material'] for r in validation['coverage_normalized'] if r['policy']=='explicit solid black constant swatch'}
    caps=[r for r in routes if r['source_role']=='black' and r['material'] in cap_materials]
    return {'collision_bytes_identical':True,'frozen_configuration':frozen,'wheel_hubs':hubs,
            'sealed_resource_regression':{'unchanged':unchanged,'visual_changes':sorted(visual_changes),
                                          'user_editable_options_difference':editable,
                                          'nonvisual_and_physics_changes':0,
                                          'boundary':'unindexed user-created player state/backups excluded'},
            'wheel_width_radius_envelope_unchanged':True,'wheel_textures_sha256':texture_hashes,'other_livery_density_preserved':True,
            'rim_recess_depth_m':depth,'source_lamp_occlusion_faces':len(caps),
            'rim_metal_reflection_alpha':target_alpha,'gold_rgb_and_dark_spoke_mask_preserved':True,
            'rounded_tyre_shoulder':shoulder,
            'brake_switch':layout,'lit_triangles':br['lit_triangles'],'halo_triangles':br['halo_triangles'],
            'native_brake_textures_identical':True,'unwanted_full_surface_backs':0,
            'atlas_detail':[{'material':m,'before_uv_texels':v[0],'after_uv_texels':v[1],
                             'linear_ratio':math.sqrt(v[1]/v[0]) if v[0]>0 else None} for m,v in quality.items()],
            'reflection_regression_boundary':'selectors/helpers checked on serialized assets; native reflections on/off need human captures'}


def ray_hit(origin,direction,tri,limit=.03):
    n=surfaces.normal(*tri);den=surfaces.dot(n,direction)
    if abs(den)<1e-10:return False
    t=surfaces.dot(n,surfaces.sub(tri[0],origin))/den
    if not .0001<t<limit:return False
    p=tuple(origin[k]+t*direction[k] for k in range(3))
    return surfaces.on_surface(p,tri,1e-5)




def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(stage: Path, before: Path):
    family = stage/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    old_family = before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    rows = collections.defaultdict(collections.Counter)
    same = 0
    max_move = 0.
    paint_masks=collections.Counter()
    new_source_faces={}
    removed_source_faces={}
    lamp_glass={}
    for frame in ('car','complete'):
        old = parse_dx_bytes((old_family/(frame+'.dx')).read_bytes())
        new = parse_dx_bytes((family/(frame+'.dx')).read_bytes())
        maps = [json.loads((s/f'source-map/source-map-{frame}.json').read_text())['records'] for s in (before,stage)]
        aa,bb = ({r['face']:r for r in mm} for mm in maps)
        policy=json.loads((stage/'reports/validation-report.json').read_text())['coverage_normalized']
        allowed_clear={r['material'] for r in policy if r['policy']=='preserve clear black non-lamp trim'}
        removed=[aa[f] for f in sorted(aa.keys()-bb.keys())]
        if any(r['material'] not in allowed_clear or r['source_role']!='black' for r in removed):raise ValueError('undeclared previous source face lost')
        removed_source_faces[frame]=[{'face':r['face'],'material':r['material'],'reason':'preserve originally clear non-lamp swatch'} for r in removed]
        restored=[bb[f] for f in sorted(bb.keys()-aa.keys())]
        policy=json.loads((stage/'reports/validation-report.json').read_text())['coverage_normalized']
        permitted={r['material'] for r in policy if r['policy'] in ('explicit solid black constant swatch','solid paint control-alpha palette heuristic')}
        solid_control={r['material'] for r in policy if r['policy']=='solid paint control-alpha palette heuristic'}
        binding=stage/'reports/rear-decal-binding.json'
        if binding.exists():permitted.add(json.loads(binding.read_text())['material'])
        decal_materials=set(json.loads((stage/'reports/surface-policy.json').read_text())['decal_materials'])
        if any(r['material'] not in permitted for r in restored):raise ValueError('undeclared restored source surface')
        new_source_faces[frame]=[{'face':r['face'],'material':r['material']} for r in restored]
        for fi in aa.keys() & bb.keys():
            a=aa[fi]
            b = bb[fi]
            def mode(model, r):
                gate,selector = model.physical_draws[r['draw']].flags_0x20[:2]
                return 'opaque' if not gate else 'cutout' if selector else 'blend'
            rows[(frame,a['obj'],a['material'],a['source_role'])][mode(old,a)+' -> '+mode(new,b)]+=1
            if a['source_role']=='paint' and mode(old,a)=='cutout':
                old_env=bool(old.physical_draws[a['draw']].unknown_0x24&4)
                new_draw=new.physical_draws[b['draw']]
                new_env=bool(new_draw.unknown_0x24&4)
                paint_masks[(frame,old_env,new_env)]+=1
                if (not new_env and a['material'] not in decal_materials) or mode(new,b)!=('opaque' if a['material'] in solid_control else 'cutout'):raise ValueError('structural paint mask lost reflection or alpha test')
            def points(model,r):
                d=model.physical_draws[r['draw']]
                return [model.vertices.positions[i] for i in model.draw_global_indices(d)[3*r['tri']:3*r['tri']+3]]
            for p,q in zip(points(old,a),points(new,b)):
                max_move=max(max_move,max(abs(x-y) for x,y in zip(p,q)))
            same+=1
        closure=json.loads((stage/f'reports/surface-repair-{frame}.json').read_text())
        glass=closure['lamp_glass'];gd=new.physical_draws[glass['native_glass_draw']]
        if not glass['generated_triangles'] or tuple(gd.flags_0x20[:2])!=(1,0) or not gd.unknown_0x24&4:
            raise ValueError('lamp glass is absent or not the native reflective blend pass')
        tex=parse_dxt(family/(gd.texture_slots[0].value+'.dxt'))
        px=decode_rgba_pixels(tex,PNG_ROWS_FLIP_VERTICAL)
        u,v=glass['uv'];i=(int((1-v)*tex.height)*tex.width+int(u*tex.width))*4
        rgba=list(px[i:i+4])
        if not 0<rgba[3]<128:raise ValueError('lamp glass is not lightly translucent')
        lamp_glass[frame]={'triangles':glass['generated_triangles'],'draw':gd.draw_index,
                           'native_flags':list(gd.flags_0x20[:2]),'helper':gd.texture_slots[1].value,
                           'swatch_rgba':rgba,'opaque_cavity_retained':glass['opaque_cavity_retained']}
    if max_move>1e-6: raise ValueError(f'body source position regression: {max_move}')
    # Recheck final embedded wheels, not an intermediate conversion file.
    wheel=parse_dx_bytes((family/'wheel.dx').read_bytes())
    complete=parse_dx_bytes((family/'complete.dx').read_bytes())
    wg,cg=source_geometry(wheel),source_geometry(complete)
    hubs=json.loads((stage/'reports/convert-complete.json').read_text())['hubs_frame']
    wd={d.texture_slots[0].value:wg[d.draw_index] for d in wheel.physical_draws}
    wheel_error=0.
    for d in (20,21,22,23):
        g=wd[complete.physical_draws[d].texture_slots[0].value]
        if len(cg[d].vertices)!=4*len(g.vertices): raise ValueError('frontend wheel count mismatch')
        for i,h in enumerate(hubs):
            mirror=1 if h[0]<0 else -1
            for a,b in zip(g.vertices,cg[d].vertices[i*len(g.vertices):(i+1)*len(g.vertices)]):
                expected=(h[0]+mirror*a.position[0],h[1]+a.position[1],h[2]+a.position[2])
                wheel_error=max(wheel_error,max(abs(x-y) for x,y in zip(expected,b.position)))
    if wheel_error>1e-6: raise ValueError('frontend and race wheel geometry differ')
    # Verify all three static package boundaries after serialization.
    validation=json.loads((stage/'reports/validation-report.json').read_text())
    if validation['pool_alpha_flag_mismatches']: raise ValueError('alpha state mismatch')
    if validation['material_mapping_verification']['opaque_pool_triangles_with_transparent_footprint']:
        raise ValueError('opaque coverage regression')
    # Wheel placement is deliberately frozen; clearance stays a diagnostic.
    packages=[]
    # The review archive will contain this audit. Exclude its own hash to avoid
    # a recursive manifest; check its CRC separately after final packaging.
    for p in sorted((stage/'review').glob('*-candidate.zip')):
        with zipfile.ZipFile(p) as z:
            bad=z.testzip()
            if bad:raise ValueError(f'ZIP CRC failure: {bad}')
            packages.append({'name':p.name,'bytes':p.stat().st_size,'members':len(z.namelist()),'crc':'PASS','sha256':sha(p)})
    return {'status':'PASS_OFFLINE_NOT_RUNTIME_QUALIFIED','source_face_records_compared':same,
            'maximum_source_position_delta_m':max_move,'maximum_frontend_wheel_delta_m':wheel_error,
            'restored_source_faces':new_source_faces,'removed_source_faces':removed_source_faces,'lamp_glass':lamp_glass,
            'paint_mask_environment_transitions':[{'frame':f,'before_env':a,'after_env':b,'faces':n} for (f,a,b),n in paint_masks.items()],
            'surface_passes':[{'frame':f,'object':o,'material':m,'source_role':r,'transitions':dict(v)}
                              for (f,o,m,r),v in rows.items()], 'packages':packages}


def comparison(stage: Path, before: Path):
    folder=stage/'preview'
    views={'windscreen_base':(165,25,390,(0,1.25,1.02)),
           'window_edges':(90,5,300,(0,1.32,0)),
           'front_reflection_control':(145,9,150,(0,.9,.7)),
           'rear_reflection_control':(30,8,150,(0,.9,-.7))}
    html=['<h2>Surface close-ups and encoded reflection control</h2>',
          '<p>Left: V4.8. Right: V4.9. Close-ups are software previews, not game captures. ',
          'Reflection-control images show texture alpha times declared helper brightness as grayscale (black = zero). ',
          'Blend and non-environment cutout surfaces are blue; reflective cutouts use grayscale with their coverage mask. This is a material diagnostic, ',
          'not a simulation of the environment stage or its final brightness.</p><table>']
    for view,(az,el,scale,centre) in views.items():
        html.append('<tr>')
        for label,base in (('vmesh48',before),('vmesh49',stage)):
            family=base/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
            items=raster.load_dx_family(family,'complete.dx',skip_draws=(20,21,22,23))
            if 'reflection_control' in view:
                model=parse_dx_bytes((family/'complete.dx').read_bytes())
                meta=json.loads((base/'reports/validation-report.json').read_text())
                brightness={r['helper']:r.get('brightness_scale',1) for r in meta['environment_helper_normalization']['edits']}
                converted=[]
                for item in items:
                    draw=model.physical_draws[int(item.name.split(':')[-1])]
                    if item.texture:
                        w,h,px=item.texture
                        px=bytearray(px)
                        for i in range(0,len(px),4):
                            if item.blend or item.alpha_test and not draw.unknown_0x24&4: px[i:i+3]=bytes((65,110,180))
                            else:
                                value=round(px[i+3]*brightness.get(draw.texture_slots[1].value,1)) if draw.unknown_0x24&4 else 0
                                alpha=px[i+3] if item.alpha_test else 255
                                px[i:i+4]=bytes((value,value,value,alpha))
                        item=dataclasses.replace(item,texture=(w,h,bytes(px)))
                    converted.append(item)
                items=converted
            path=folder/f'{label}_{view}.png'
            path.write_bytes(raster.png_rgb(800,420,raster.render(items,raster.Camera(az,el,scale,centre),800,420)))
            html.append(f'<td><h3>{label}: {view}</h3><img src="{path.name}"></td>')
        html.append('</tr>')
    html.append('</table>')
    index=folder/'index.html'
    text=index.read_text()
    marker='<!-- V49_DETAIL_AUDIT -->'
    text=text.split(marker)[0]+marker+'\n'+''.join(html)
    index.write_text(text,encoding='utf-8')


def state_previews(stage,before):
    """Explicit offline state selection; never a claim of observed input response."""
    folder=stage/'preview';html=['<h2>Brake state and reflection-path regression previews</h2>',
        '<p>Brake images explicitly select the stock cases offline. They do not measure game input response. ',
        'Reflection OFF uses albedo; the ON diagnostic adds a constant average helper colour times texture alpha. ',
        'It does not simulate environment coordinates, native lighting, mipmaps or exact final brightness.</p>']
    summary=[]
    for label,base in (('vmesh48',before),('vmesh49',stage)):
        family=base/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
        car=parse_dx_bytes((family/'car.dx').read_bytes());layout=brake_lights.switch_layout(car)
        for state in (1,2):
            skip=layout['case2'] if state==1 else layout['case1']
            items=raster.load_dx_family(family,'car.dx',skip_draws=skip)
            path=folder/f'{label}_brake_case{state}.png'
            path.write_bytes(raster.png_rgb(800,420,raster.render(items,raster.Camera(0,8,260,(0,.65,-2.1)),800,420)))
            html.append(f'<h3>{label} brake case{state} (offline selection)</h3><img src="{path.name}">')
        model=parse_dx_bytes((family/'complete.dx').read_bytes())
        items=raster.load_dx_family(family,'complete.dx')
        reflected=[];controlled=[]
        for item in items:
            d=model.physical_draws[int(item.name.split(':')[-1])]
            if item.texture and d.unknown_0x24&4:
                w,h,px=item.texture;name=d.texture_slots[1].value
                helper=parse_dxt(family/(name+'.dxt'));hp=decode_rgba_pixels(helper)
                mean=[sum(hp[k::4])/(len(hp)//4) for k in range(3)];out=bytearray(px)
                for i in range(0,len(px),4):
                    for k in range(3):out[i+k]=min(255,round(px[i+k]+mean[k]*px[i+3]/255))
                if out[3::4]!=px[3::4]:raise ValueError('reflection diagnostic changed coverage')
                reflected.append(dataclasses.replace(item,texture=(w,h,bytes(out))))
                controlled.append(d.draw_index)
            else:reflected.append(item)
        for mode,draws in (('off',items),('on_constant_helper_diagnostic',reflected)):
            path=folder/f'{label}_reflections_{mode}.png'
            path.write_bytes(raster.png_rgb(800,420,raster.render(draws,raster.Camera(150,12,135,(0,.9,.5)),800,420)))
            html.append(f'<h3>{label} reflections {mode}</h3><img src="{path.name}">')
        wheel=parse_dx_bytes((family/'wheel.dx').read_bytes());wheel_items=raster.load_dx_family(family,'wheel.dx')
        lit_wheel=[];light=surfaces.unit((-1,.6,-.4))
        for item in wheel_items:
            d=wheel.physical_draws[int(item.name.split(':')[-1])];indices=wheel.draw_global_indices(d);triangles=[]
            for ti,tri in enumerate(item.tris):
                colors=[]
                for k in range(3):
                    n=wheel.vertices.normals[indices[3*ti+k]];brightness=.3+.7*max(0,surfaces.dot(n,light))
                    colors.append(tuple(round(value*brightness) for value in tri[6+k]))
                triangles.append((*tri[:6],*colors))
            lit_wheel.append(dataclasses.replace(item,tris=triangles))
        for name,az in (('wheel_face',-90),('wheel_depth',-60)):
            path=folder/f'{label}_{name}.png'
            path.write_bytes(raster.png_rgb(650,520,raster.render(lit_wheel,raster.Camera(az,8,540,(0,0,0)),650,520)))
            html.append(f'<h3>{label} {name}: illustrative normal lighting, not native shading</h3><img src="{path.name}">')
        summary.append({'candidate':label,'environment_draws':controlled,'coverage_alpha_unchanged':True,
                        'native_environment_mapping':'not simulated','brake_cases_selected':[1,2]})
    index=folder/'index.html';text=index.read_text(encoding='utf-8');marker='<!-- V49_STATE_PREVIEWS -->'
    index.write_text(text.split(marker)[0]+marker+'\n'+''.join(html),encoding='utf-8')
    return summary


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',type=Path,required=True)
    ap.add_argument('--before',type=Path,required=True)
    ap.add_argument('--previews',action='store_true')
    args=ap.parse_args()
    result=audit(args.stage,args.before)
    result['phase_checks']=phase_checks(args.stage,args.before)
    (args.stage/'reports/final-offline-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if args.previews:
        comparison(args.stage,args.before)
        result['offline_state_previews']=state_previews(args.stage,args.before)
        (args.stage/'reports/final-offline-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='surface_passes'},indent=2))


if __name__=='__main__':main()
