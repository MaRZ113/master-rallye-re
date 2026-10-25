"""Read-only final candidate regression audit and explicitly approximate previews."""
from __future__ import annotations
import argparse,dataclasses,json,math,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.dxt import parse_dxt,decode_rgba_pixels
from build_vmesh_impreza_experimental import sha_file,dump
import vmesh_brake_lights as brake
import vmesh_final_cleanup as cleanup
import vmesh_raster as raster


def attrs(g,t):return [(g.vertices[i].position,g.vertices[i].normal,g.vertices[i].color,g.vertices[i].uvs) for i in t]


def audit(stage,before):
    family=stage/'runtime/resource-root/DataGx/Vehicles/ImprezaProto';old=before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    operations=json.loads((stage/'reports/cleanup-operations.json').read_text());checks={}
    changed=[];same=0;side_name=operations['tyre']['texture']
    manifest=json.loads((stage/'runtime/resource-manifest.json').read_text())
    for row in manifest['resources']:
        name=row['path'];a=stage/'runtime/resource-root'/name;b=before/'runtime/resource-root'/name
        if a.read_bytes()==b.read_bytes():same+=1;continue
        if name.lower()=='datagame/options.xml':continue
        if not name.startswith('DataGx/Vehicles/ImprezaProto/') or Path(name).name not in ('car.dx','complete.dx','headlamp-tga.dxt','nevwheel-tga.dxt',side_name):
            raise ValueError('unexpected resource change: '+name)
        changed.append(name)
    checks['sealed_resources']={'unchanged':same,'visual_changes':changed}
    for frame in ('car','complete'):
        a,b=(parse_dx_bytes((base/(frame+'.dx')).read_bytes()) for base in (family,old));ga,gb=source_geometry(a),source_geometry(b)
        added={}
        for draw,g in gb.items():
            if frame=='car' and draw==30:continue
            if len(ga[draw].triangles)<len(g.triangles):raise ValueError('source triangles removed')
            for index,t in enumerate(g.triangles):
                if attrs(g,t)!=attrs(ga[draw],ga[draw].triangles[index]):raise ValueError(f'original triangle changed {frame}:{draw}:{index}')
            delta=len(ga[draw].triangles)-len(g.triangles)
            if delta and draw not in (9,25):raise ValueError('undeclared geometry change')
            if delta:added[draw]=delta
        for da,db in zip(a.physical_draws,b.physical_draws):
            if (da.flags_0x20,da.unknown_0x24,da.tag,da.control_words,da.group_label,[s.value for s in da.texture_slots])!=(db.flags_0x20,db.unknown_0x24,db.tag,db.control_words,db.group_label,[s.value for s in db.texture_slots]):
                raise ValueError('native material/controller metadata drift')
        if frame=='car':
            ad,bd=(family/'car.dx').read_bytes(),(old/'car.dx').read_bytes()
            if ad[a.collision.offset:a.collision.end_offset]!=bd[b.collision.offset:b.collision.end_offset]:raise ValueError('collision changed')
            if brake.switch_layout(a)!=brake.switch_layout(b):raise ValueError('brake controller changed')
            checks['brake_lit_geometry_identical']=attrs(ga[29],ga[29].triangles[0])==attrs(gb[29],gb[29].triangles[0])
            for v in ga[30].vertices:
                lens=ga[24];found=False
                for t in lens.triangles:
                    ps=[lens.vertices[i].position for i in t]
                    try:h=cleanup.hull_xy(ps)
                    except ValueError:continue
                    inside=all((q[0]-p[0])*(v.position[1]-p[1])-(q[1]-p[1])*(v.position[0]-p[0])>=-2e-7 for p,q in zip(h,h[1:]+h[:1]))
                    if not inside:continue
                    p,q,r=ps;den=(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
                    s=((v.position[0]-p[0])*(r[1]-p[1])-(v.position[1]-p[1])*(r[0]-p[0]))/den
                    u=((q[0]-p[0])*(v.position[1]-p[1])-(q[1]-p[1])*(v.position[0]-p[0]))/den
                    z=p[2]+s*(q[2]-p[2])+u*(r[2]-p[2])-.0015
                    if abs(v.position[2]-z)<2e-6:found=True;break
                if not found:raise ValueError('glow outside source lens surface')
            checks['glow_vertices_on_lens']=len(ga[30].vertices)
        checks[frame]={'retained_triangle_attributes_exact':True,'added_triangles':added,'native_state_identical':True}
    if (family/'wheel.dx').read_bytes()!=(old/'wheel.dx').read_bytes():raise ValueError('wheel geometry/fitment changed')
    checks['wheel_geometry_byte_identical']=True
    for name in ('nevwheel-tga.dxt',side_name,'headlamp-tga.dxt'):
        a,b=parse_dxt(family/name),parse_dxt(old/name)
        if a.header!=b.header or (family/name).stat().st_size!=(old/name).stat().st_size:raise ValueError('DXT format/size changed')
        checks[name]={'sha256':sha_file(family/name),'dimensions':[a.width,a.height],'header_size_unchanged':True}
    rim=decode_rgba_pixels(parse_dxt(family/'nevwheel-tga.dxt'));prior=decode_rgba_pixels(parse_dxt(old/'nevwheel-tga.dxt'))
    for i in range(0,len(rim),4):
        if rim[i+3]!=prior[i+3] or prior[i+3] and rim[i:i+3]!=prior[i:i+3]:raise ValueError('source metal changed')
    checks['rim_metal_exact_and_face_opaque']=not any(d.flags_0x20[0] for d in parse_dx_bytes((family/'wheel.dx').read_bytes()).physical_draws)
    # The project PNGs are lossless RGBA inputs to these fixed-format DXT slots.
    import gtmat
    for name in ('headlamp-tga','nevwheel-tga',Path(side_name).stem):
        png=gtmat.GtTexture((stage/f'tex/{name}.png').read_bytes())
        if bytes(png.rgba)!=decode_rgba_pixels(parse_dxt(family/(name+'.dxt'))):raise ValueError('DXT/PNG roundtrip mismatch')
    checks['dxt_roundtrip_exact']=True
    # Guard the new constant swatch against source lamp imagery/UV footprints.
    tex=parse_dxt(family/'headlamp-tga.dxt');newpx=decode_rgba_pixels(tex)
    oldpx=decode_rgba_pixels(parse_dxt(old/'headlamp-tga.dxt'))
    cx,cy=operations['lamp_swatch']['pixel'];guard=operations['lamp_swatch']['guard_radius_texels']
    modified=set()
    for y in range(tex.height):
        for x in range(tex.width):
            i=4*(y*tex.width+x)
            if newpx[i:i+4]!=oldpx[i:i+4]:
                if abs(x-cx)>guard or abs(y-cy)>guard:raise ValueError('source lamp texture changed outside unused swatch')
                modified.add((x,y))
    for frame in ('car','complete'):
        g=source_geometry(parse_dx_bytes((old/(frame+'.dx')).read_bytes()))[25]
        for t in g.triangles:
            uv=[g.vertices[i].uvs[0] for i in t]
            xs=[u*tex.width for u,v in uv];ys=[(1-v)*tex.height for u,v in uv]
            if any(min(xs)-2<=x<=max(xs)+2 and min(ys)-2<=y<=max(ys)+2 for x,y in modified):
                raise ValueError('lamp swatch intrudes on source UV footprint')
    checks['headlamp_source_pixels_and_guarded_UV_footprints_preserved']=True
    build=json.loads((stage/'reports/build-validation.json').read_text())
    for name,h in build['protected_files_unchanged'].items():
        if sha_file(Path(name))!=h:raise ValueError('protected file changed')
    checks['protected_files_unchanged']=True
    archive=stage/'review'/(stage.name+'-candidate.zip')
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('candidate ZIP CRC failed')
        for name in ('car.dx','complete.dx','wheel.dx','headlamp-tga.dxt','nevwheel-tga.dxt',side_name):
            if z.read(stage.name+'/runtime/resource-root/DataGx/Vehicles/ImprezaProto/'+name)!=(family/name).read_bytes():raise ValueError('archive mismatch')
    checks['candidate_zip']={'sha256':sha_file(archive),'crc':'PASS','runtime_members_match':True}
    return {'status':'PASS_OFFLINE_RUNTIME_VISUAL_VERIFICATION_PENDING','checks':checks,'operations':operations}


def previews(stage,before):
    html=['<h1>V4.9 → V4.10 offline comparison</h1><p>Original DX/DXT geometry and materials. Approximation: no native environment coordinates, lights, mipmaps or input response. Brake cases explicitly selected. Wheel recess geometry is unchanged.</p>']
    cameras=[('front',raster.Camera(180,8,210,(0,.5,2.0)),'complete.dx'),
        ('front_oblique',raster.Camera(150,12,215,(0,.45,2.0)),'complete.dx'),
        ('wheel',raster.Camera(-70,10,530,(0,0,0)),'wheel.dx'),
        ('rear_brake_on',raster.Camera(0,8,220,(0,.55,-2.1)),'car.dx'),
        ('rear_brake_off',raster.Camera(0,8,220,(0,.55,-2.1)),'car.dx')]
    for view,cam,dx in cameras:
        html.append('<h2>'+view+'</h2>')
        for label,base in (('before',before),('after',stage)):
            family=base/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
            skip=(28,) if view=='rear_brake_on' else (29,30) if view=='rear_brake_off' else ()
            items=raster.load_dx_family(family,dx,skip_draws=skip)
            path=stage/'preview'/f'{label}_{view}.png'
            path.write_bytes(raster.png_rgb(760,420,raster.render(items,cam,760,420)))
            html.append(f'<h3>{label}</h3><img src="{path.name}">')
    # Constant helper contribution checks coverage/state only, not game parity.
    for label,base in (('before',before),('after',stage)):
        family=base/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
        model=parse_dx_bytes((family/'complete.dx').read_bytes());items=raster.load_dx_family(family)
        on=[]
        for item in items:
            d=model.physical_draws[int(item.name.split(':')[-1])]
            if item.texture and d.unknown_0x24&4:
                w,h,px=item.texture;hp=decode_rgba_pixels(parse_dxt(family/(d.texture_slots[1].value+'.dxt')))
                mean=[sum(hp[k::4])/(len(hp)//4) for k in range(3)];out=bytearray(px)
                for i in range(0,len(px),4):
                    for k in range(3):out[i+k]=min(255,round(px[i+k]+mean[k]*px[i+3]/255))
                on.append(dataclasses.replace(item,texture=(w,h,bytes(out))))
            else:on.append(item)
        for mode,draws in (('off',items),('on_constant_helper_only',on)):
            path=stage/'preview'/f'{label}_reflection_{mode}.png'
            path.write_bytes(raster.png_rgb(760,420,raster.render(draws,raster.Camera(150,10,135,(0,.8,.4)),760,420)))
            html.append(f'<h2>{label}: reflection {mode}</h2><img src="{path.name}">')
    (stage/'preview/index.html').write_text('\n'.join(html),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--before',type=Path,required=True);p.add_argument('--previews',action='store_true');a=p.parse_args()
    result=audit(a.stage,a.before);dump(a.stage/'reports/final-offline-audit.json',result)
    if a.previews:previews(a.stage,a.before)
    print(json.dumps({'status':result['status'],'checks':result['checks']},indent=2))

if __name__=='__main__':main()
