"""Independent frozen-bundle scope checks and actual-resource wheel previews."""
from __future__ import annotations
import argparse,dataclasses,json,math,sys,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import gtmat,vmesh_raster as raster
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels
from master_rallye.addon_sdk.ui_assets import alpha_bounds,BANKS,archive_member
from master_rallye.vehicle_packaging import _open_sma_archive
from build_vmesh_impreza_experimental import dump,sha_file

def radius(v):return math.hypot(*v.position[1:])
def semantic(g):
    return (g.triangles,tuple((v.position,v.normal,v.color,v.uvs) for v in g.vertices))

def preview(stage,before,reference):
    old=before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    new=stage/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    chunks=[]
    for label,family in (('before',old),('after',new),('stock-pajero',reference)):
        items=raster.load_dx_family(family,'wheel.dx');model=parse_dx_bytes((family/'wheel.dx').read_bytes());geoms=source_geometry(model)
        # Fixed diagnostic light makes surface slope legible; this is not the
        # game's environment map, material lighting, filtering or mip sampling.
        lit=[];light=(-.8,.45,.35);ln=math.sqrt(sum(x*x for x in light));light=tuple(x/ln for x in light)
        for d,item in enumerate(items):
            g=geoms[d];tris=[]
            for t,ids in zip(item.tris,g.triangles):
                colors=[]
                for idx in ids:
                    v=g.vertices[idx];strength=.4+.6*max(0,sum(a*b for a,b in zip(v.normal,light)))
                    colors.append(tuple(round(c*strength) for c in v.color[:3]))
                tris.append((*t[:6],*colors))
            lit.append(dataclasses.replace(item,tris=tris))
        for az in (-90,-55):
            w,h=360,360;rgb=raster.render(lit,raster.Camera(az,8,380,(0,0,0)),w,h)
            png=gtmat.png_from_rgba(w,h,b''.join(rgb[i:i+3]+b'\xff' for i in range(0,len(rgb),3)))
            name=f'wheel-{label}-{abs(az)}.png';(stage/'preview'/name).write_bytes(png)
            chunks.append(f'<figure><img width="300" src="{name}"><figcaption>{label}; az {az}</figcaption></figure>')
    path=stage/'preview/index.html'
    path.write_text(path.read_text().replace('<h1>Subaru UI integration</h1>','<h1>Subaru final UI / wheel candidate</h1>')+'<h2>Actual DX/DXT wheel layers</h2><p>Offline diagnostic lighting only. Native reflections and filtering need a game test.</p><section style="display:flex;flex-wrap:wrap">'+''.join(chunks)+'</section>',encoding='utf-8')

def audit(stage,before):
    current=stage/'runtime/resource-root';basezip=before/'review'/(before.name+'-candidate.zip')
    with zipfile.ZipFile(basezip) as z:
        prefix=before.name+'/runtime/resource-root/'
        baseline={n[len(prefix):]:z.read(n) for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
    actual={p.relative_to(current).as_posix():p.read_bytes() for p in current.rglob('*') if p.is_file()}
    # The older review ZIP omitted the unchanged prepared runtime archive.
    # Verify its exact sealed-baseline identity rather than the retail archive
    # (runtime preparation builds a ZIP-compatible copy of the retail SMA).
    source=Path(json.loads((stage/'project/vehicle-project.json').read_text())['source_vehicle_dir']);stock=source.parents[3]/'Data.sma'
    if set(actual)-set(baseline)!={'Data.sma'} or set(baseline)-set(actual):raise ValueError('runtime file set changed')
    if sha_file(current/'Data.sma')!='131d61ee8241df9cee4885db046e4e68d4df8177df40638bab01662ee12dc736':raise ValueError('prepared baseline archive changed')
    changes=sorted(n for n in baseline if actual[n]!=baseline[n])
    family='DataGx/Vehicles/ImprezaProto/'
    expected=sorted(['DataGx/Frontend/VehicleSelect/carsheet_032_000.dxt']+[family+x for x in ('complete.dx','wheel.dx','nevwheel-tga.dxt')])
    if changes!=expected:raise ValueError('unexpected resource changes: '+str(changes))
    checks={};report=json.loads((stage/'reports/wheel-layers.json').read_text());rim=report['frontend_rim_draw']
    for filename,changed_draw in (('wheel.dx',3),('complete.dx',rim)):
        old=parse_dx_bytes(baseline[family+filename]);new=parse_dx_bytes(actual[family+filename]);a=source_geometry(old);b=source_geometry(new)
        if not new.diagnostics.validated or new.diagnostics.warnings!=old.diagnostics.warnings:raise ValueError('DX validation regression')
        if len(old.physical_draws)!=len(new.physical_draws):raise ValueError('draw count changed')
        for x,y in zip(old.physical_draws,new.physical_draws):
            fields=('tag','texture_tuple','group_label','control_words','flags_0x20','unknown_0x24')
            if any(getattr(x,k)!=getattr(y,k) for k in fields):raise ValueError('native material identity changed')
        for d in a:
            if d!=changed_draw and semantic(a[d])!=semantic(b[d]):raise ValueError('unrelated draw geometry/UV/normals changed')
        checks[filename]={'changed_draw':changed_draw,'other_draw_geometry_exact':True,'native_material_states_exact':True}
        if filename=='wheel.dx':
            if any(d.flags_0x20[0] for d in new.physical_draws):raise ValueError('transparent wheel face')
            for g in (a,b):
                envelope=(max(radius(v) for gg in g.values() for v in gg.vertices),max(abs(v.position[0]) for gg in g.values() for v in gg.vertices))
                if g is a:oldenv=envelope
                elif any(abs(x-y)>1e-7 for x,y in zip(oldenv,envelope)):raise ValueError('wheel envelope changed')
            g=b[3];n=report['segments'];edge=g.vertices[1:1+n];shelfedge=g.vertices[-n:]
            for x,y in zip(edge,shelfedge):
                if x.position!=y.position:raise ValueError('face/shelf crack')
            for v in g.vertices:
                if abs(sum(c*c for c in v.normal)-1)>2e-6:raise ValueError('nonunit rim normal')
            # Central insert samples the source circle; every shelf vertex uses
            # the same protected corner swatch, never the rim artwork/tyre UVs.
            shelf_uv={v.uvs for v in g.vertices[1+n:]}
            if len(shelf_uv)!=1 or g.vertices[0].uvs in shelf_uv:raise ValueError('shelf UV domain overlaps face')
            checks['wheel_envelope_m']=list(oldenv);wheel=b
        else:complete=b
    # Existing hub anchors only; no wheel placement recomputation.
    wg=wheel[3];cg=complete[rim];count=len(wg.vertices)
    if len(cg.vertices)!=4*count:raise ValueError('frontend rim copy count')
    for j,hub in enumerate(report['inherited_hubs']):
        mirror=1 if hub[0]<0 else -1
        for local,instance in zip(wg.vertices,cg.vertices[j*count:(j+1)*count]):
            desired=(hub[0]+mirror*local.position[0],hub[1]+local.position[1],hub[2]+local.position[2])
            if max(abs(x-y) for x,y in zip(desired,instance.position))>2e-6:raise ValueError('frontend wheel placement mismatch')
    name=family+'nevwheel-tga.dxt';a=parse_dxt_bytes(baseline[name]);b=parse_dxt_bytes(actual[name]);ap=decode_rgba_pixels(a);bp=decode_rgba_pixels(b)
    if a.header[:8]+a.header[12:]!=b.header[:8]+b.header[12:] or b.word_0x08!=zlib.crc32(b.bgra)&0xffffffff:raise ValueError('rim DXT header/CRC invalid')
    for y in range(a.height):
        for x in range(a.width):
            if x>=7 or y>=7:
                i=4*(y*a.width+x)
                if ap[i:i+4]!=bp[i:i+4]:raise ValueError('rim artwork changed outside swatch')
    # Both banks/widget/native selector and correct race frame already proved
    # byte identical by the exhaustive four-resource delta above.
    prefix,_,template,size=BANKS['vehicle_select_art']
    with _open_sma_archive(stock) as z:ref=parse_dxt_bytes(archive_member(z,f'{prefix}_{template:03d}_000.dxt'))
    target=alpha_bounds((*size,decode_rgba_pixels(ref)));frame=parse_dxt_bytes(actual[prefix+'_032_000.dxt']);bounds=alpha_bounds((*size,decode_rgba_pixels(frame)))
    if not (target[0]<bounds[0]<bounds[2]<target[2] and target[1]<bounds[1]<bounds[3]<target[3]):raise ValueError('icon outside donor alignment bounds')
    if frame.word_0x08!=zlib.crc32(frame.bgra)&0xffffffff:raise ValueError('UI CRC mismatch')
    for filename in ('native-patch-manifest.json',):
        with zipfile.ZipFile(basezip) as z:
            if z.read(before.name+'/runtime/'+filename)!=(stage/'runtime'/filename).read_bytes():raise ValueError('native selector operations changed')
    for name in ('ui/subaru-small.png',):
        if (stage/'project'/name).read_bytes()!=(before/'project'/name).read_bytes():raise ValueError('qualified race source changed')
    candidate=stage/'review'/(stage.name+'-candidate.zip')
    with zipfile.ZipFile(candidate) as z:
        if z.testzip():raise ValueError('candidate ZIP CRC failure')
        for name,data in actual.items():
            if z.read(stage.name+'/runtime/resource-root/'+name)!=data:raise ValueError('ZIP/runtime mismatch')
    result={'status':'PASS_OFFLINE_RUNTIME_TEST_PENDING','baseline':'immutable V411 candidate ZIP; ignores live user saves/settings drift','resource_count':len(actual),'changed_resources':changes,
        'checks':checks,'icon_template_bounds':target,'icon_output_bounds':bounds,'race_thumbnail_and_banks_byte_identical':True,'physics_and_car_dx_byte_identical':True,
        'frontend_four_rim_instances_match_frozen_hubs':True,'opaque_wheel_face':True,'rim_source_pixels_preserved_except_guarded_corner':True,'rim_crc32_valid':True,'native_patch_manifest_byte_identical':True,'candidate_sha256':sha_file(candidate)}
    dump(stage/'reports/final-audit.json',result);preview(stage,before,source.parent/'Pajero');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--before',type=Path,required=True);a=p.parse_args();print(json.dumps(audit(a.stage,a.before),indent=2))
