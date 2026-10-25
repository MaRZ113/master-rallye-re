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


def ray_hit(origin,direction,tri,limit=.03):
    n=surfaces.normal(*tri);den=surfaces.dot(n,direction)
    if abs(den)<1e-10:return False
    t=surfaces.dot(n,surfaces.sub(tri[0],origin))/den
    if not .0001<t<limit:return False
    p=tuple(origin[k]+t*direction[k] for k in range(3))
    return surfaces.on_surface(p,tri,1e-5)


def phase_checks(stage,before):
    family=stage/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    donor=Path(json.loads((stage/'project/vehicle-project.json').read_text())['source_vehicle_dir'])
    if (family/'merctread-tga.dxt').read_bytes()!=(donor/'merctread-tga.dxt').read_bytes():raise ValueError('stock tread changed')
    tex=decode_rgba_pixels(parse_dxt(family/'nevwheel-tga.dxt'),PNG_ROWS_FLIP_VERTICAL)
    dark=sum(tuple(tex[i:i+4])==(9,10,12,0) for i in range(0,len(tex),4))
    wheel=parse_dx_bytes((family/'wheel.dx').read_bytes())
    if not dark or any(d.flags_0x20[0] for d in wheel.physical_draws):raise ValueError('spoke gaps are not dark opaque geometry')
    a=json.loads((stage/'reports/validation-report.json').read_text())
    for name,pool in a['material_plan']['pools'].items():
        if pool['pass']=='reflective_cutout':
            px=decode_rgba_pixels(parse_dxt(family/(name+'.dxt')),PNG_ROWS_FLIP_VERTICAL)
            if not set(px[3::4])<={0,255}:raise ValueError('structural coverage alpha is attenuated again')
    quality=collections.defaultdict(lambda:[0.,0.])
    geometry=[]
    for index,base in enumerate((before,stage)):
        fp=base/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
        model=parse_dx_bytes((fp/'car.dx').read_bytes());g=source_geometry(model)
        mm=json.loads((base/'source-map/source-map-car.json').read_text())['records']
        geometry.append((model,g,{r['face']:r for r in mm},fp))
        materials=set(json.loads((stage/'reports/surface-policy.json').read_text())['decal_materials'])
        sizes={}
        for r in mm:
            if r['material'] not in materials:continue
            d=model.physical_draws[r['draw']];name=d.texture_slots[0].value
            if name not in sizes:
                t=parse_dxt(fp/(name+'.dxt'));sizes[name]=(t.width,t.height)
            w,h=sizes[name];vs=[g[r['draw']].vertices[i] for i in g[r['draw']].triangles[r['tri']]]
            u,v,z=[(p.uvs[0][0]*w,p.uvs[0][1]*h) for p in vs]
            quality[r['material']][index]+=abs((v[0]-u[0])*(z[1]-u[1])-(v[1]-u[1])*(z[0]-u[0]))/2
    closure=json.loads((stage/'reports/surface-repair-car.json').read_text())
    if not any(c['rear'] for c in closure['recess_collars']):raise ValueError('rear recess closure absent')
    new_model,new_g,new_map,fp=geometry[1]
    old_model,old_g,old_map,old_fp=geometry[0]
    backs={}
    for label,g in [('before',old_g),('after',new_g)]:
        backs[label]=[[g[9].vertices[i].position for i in t] for t in g[9].triangles]
    restored=[r for r in a['coverage_normalized'] if r['policy']=='solid paint control-alpha palette heuristic']
    if not restored:raise ValueError('paint control-alpha repair absent')
    restored_materials={r['material'] for r in restored}
    tested=before_clear=after_solid=after_painted=0
    textures={}
    def sample_at(record,weights,geometry):
        model,g,_,folder=geometry
        draw=model.physical_draws[record['draw']];name=draw.texture_slots[0].value
        cache_key=(str(folder),name)
        if cache_key not in textures:
            t=parse_dxt(folder/(name+'.dxt'));textures[cache_key]=(t.width,t.height,decode_rgba_pixels(t,PNG_ROWS_FLIP_VERTICAL))
        w,h,px=textures[cache_key]
        vs=[g[record['draw']].vertices[i] for i in g[record['draw']].triangles[record['tri']]]
        u,v=(sum(weights[t]*vs[t].uvs[0][k] for t in range(3)) for k in range(2))
        index=((int((1-v)*h)%h)*w+int(u*w)%w)*4
        rgba=px[index:index+4]
        solid=not draw.flags_0x20[0] or bool(draw.flags_0x20[1] and rgba[3]>128)
        return rgba,solid
    for fi,r in new_map.items():
        if r['material'] not in restored_materials:continue
        for i in range(1,16):
            for j in range(1,16-i):
                weights=(i/16,j/16,1-(i+j)/16)
                old_px,old_solid=sample_at(old_map[fi],weights,geometry[0])
                new_px,new_solid=sample_at(r,weights,geometry[1])
                tested+=1;before_clear+=not old_solid;after_solid+=new_solid
                after_painted+=max(new_px[:3])>=24 and max(new_px[:3])-min(new_px[:3])>=16
    if not tested or after_solid!=tested:raise ValueError('restored paint still has coverage holes')
    if not before_clear or after_painted!=tested:raise ValueError('paint repair did not replace clear coverage with chromatic paint')
    if closure['top_mask_backing_source_faces']:raise ValueError('unexpected black top mask underlays remain')
    glass=new_g[35];count=closure['lamp_glass']['generated_triangles']
    ids={i for t in glass.triangles[-count:] for i in t}
    if len(ids)>=count*3:raise ValueError('lamp glass vertices were not shared')
    if any(abs(math.sqrt(sum(x*x for x in glass.vertices[i].normal))-1)>1e-5 for i in ids):raise ValueError('non-unit lamp normal')
    return {'stock_tread_sha256':sha(family/'merctread-tga.dxt'),'dark_opaque_rim_texels':dark,
            'wheel_radial_envelope_m':max(math.hypot(*p[1:]) for p in wheel.vertices.positions),
            'lens_triangles':count,'lens_shared_vertex_count':len(ids),
            'hood_paint_coverage':{'tested':tested,'before_clear_samples':before_clear,'after_solid_samples':after_solid,
                                   'after_chromatic_samples':after_painted,'restored_materials':restored,
                                   'black_top_mask_underlays':0,
                                   'boundary':'interior grid samples on repaired source faces; no in-game lighting claim'},
            'recess_collars':closure['recess_collars'],
            'decal_uv_texel_area':[{'material':m,'before':v[0],'after':v[1],
                                   'linear_scale':math.sqrt(v[1]/v[0]) if v[0]>0 else None} for m,v in quality.items()]}


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(stage: Path, before: Path):
    family = stage/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    old_family = before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    rows = collections.defaultdict(collections.Counter)
    same = 0
    max_move = 0.
    paint_masks=collections.Counter()
    new_source_faces={}
    lamp_glass={}
    for frame in ('car','complete'):
        old = parse_dx_bytes((old_family/(frame+'.dx')).read_bytes())
        new = parse_dx_bytes((family/(frame+'.dx')).read_bytes())
        maps = [json.loads((s/f'source-map/source-map-{frame}.json').read_text())['records'] for s in (before,stage)]
        aa,bb = ({r['face']:r for r in mm} for mm in maps)
        if not aa.keys()<=bb.keys(): raise ValueError('previous source faces were lost')
        restored=[bb[f] for f in sorted(bb.keys()-aa.keys())]
        policy=json.loads((stage/'reports/validation-report.json').read_text())['coverage_normalized']
        permitted={r['material'] for r in policy if r['policy'] in ('explicit solid black constant swatch','solid paint control-alpha palette heuristic')}
        solid_control={r['material'] for r in policy if r['policy']=='solid paint control-alpha palette heuristic'}
        binding=stage/'reports/rear-decal-binding.json'
        if binding.exists():permitted.add(json.loads(binding.read_text())['material'])
        decal_materials=set(json.loads((stage/'reports/surface-policy.json').read_text())['decal_materials'])
        if any(r['material'] not in permitted for r in restored):raise ValueError('undeclared restored source surface')
        new_source_faces[frame]=[{'face':r['face'],'material':r['material']} for r in restored]
        for fi,a in aa.items():
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
    if any(h['visible_samples_inside_tyre'] for h in validation['material_aware_wheel_clearance']['hubs']):
        raise ValueError('sampled wheel/body penetration')
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
            'restored_source_faces':new_source_faces,'lamp_glass':lamp_glass,
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
          '<p>Left: V4.7. Right: V4.8. Close-ups are software previews, not game captures. ',
          'Reflection-control images show texture alpha times declared helper brightness as grayscale (black = zero). ',
          'Blend and non-environment cutout surfaces are blue; reflective cutouts use grayscale with their coverage mask. This is a material diagnostic, ',
          'not a simulation of the environment stage or its final brightness.</p><table>']
    for view,(az,el,scale,centre) in views.items():
        html.append('<tr>')
        for label,base in (('vmesh47',before),('vmesh48',stage)):
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
    marker='<!-- V48_DETAIL_AUDIT -->'
    text=text.split(marker)[0]+marker+'\n'+''.join(html)
    index.write_text(text,encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',type=Path,required=True)
    ap.add_argument('--before',type=Path,required=True)
    ap.add_argument('--previews',action='store_true')
    args=ap.parse_args()
    result=audit(args.stage,args.before)
    result['phase_checks']=phase_checks(args.stage,args.before)
    (args.stage/'reports/final-offline-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if args.previews: comparison(args.stage,args.before)
    print(json.dumps({k:v for k,v in result.items() if k!='surface_passes'},indent=2))


if __name__=='__main__':main()
