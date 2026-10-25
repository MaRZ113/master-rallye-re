"""Narrow final cleanup of a hash-bound V4.9 project; never launches the game."""
from __future__ import annotations
import argparse,json,math,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import gtmat
import vmesh_final_cleanup as finish
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt,decode_rgba_pixels,PNG_ROWS_FLIP_VERTICAL
from master_rallye.topology_writer import source_geometry
from build_vmesh_impreza_experimental import Runner,dump,sha_file,ADDON_ID


def safe_lamp_sample(image,models):
    """Allocate a guarded constant swatch outside every existing lamp UV box."""
    w,h,px=image;used=set()
    for model in models:
        g=source_geometry(model)[25]
        for tri in g.triangles:
            uv=[g.vertices[i].uvs[0] for i in tri]
            xs=[u*w for u,v in uv];ys=[(1-v)*h for u,v in uv]
            if min(xs)<0 or max(xs)>w or min(ys)<0 or max(ys)>h:raise ValueError('wrapped lamp UV unsupported')
            for y in range(max(0,math.floor(min(ys))-2),min(h,math.ceil(max(ys))+3)):
                for x in range(max(0,math.floor(min(xs))-2),min(w,math.ceil(max(xs))+3)):used.add((x,y))
    for y in range(3,h-3):
        for x in range(3,w-3):
            tile=[(xx,yy) for yy in range(y-3,y+4) for xx in range(x-3,x+4)]
            if any(p in used for p in tile):continue
            out=bytearray(px)
            for xx,yy in tile:out[4*(yy*w+xx):4*(yy*w+xx)+4]=bytes((240,240,240,184))
            return ((x+.5)/w,1-(y+.5)/h),[240,240,240],(w,h,bytes(out)),{'pixel':[x,y],'guard_radius_texels':3,'existing_UV_boxes_untouched':True}
    raise ValueError('lamp atlas has no guarded unused swatch')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--profile',type=Path,required=True)
    args=ap.parse_args();before=args.before.resolve();out=args.output.resolve()
    profile=json.loads(args.profile.read_text())
    family=before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    for name,value in profile['baseline_sha256'].items():
        if sha_file(family/name)!=value:raise ValueError('baseline mismatch: '+name)
    if out.exists():raise ValueError('output exists; refusing overwrite')
    for folder in ('dx','tex','reports','review','preview'): (out/folder).mkdir(parents=True)
    for folder in ('project','tex','source-map'):shutil.copytree(before/folder,out/folder,dirs_exist_ok=True)
    for name in ('wheel.dx','car.dx','complete.dx'):shutil.copy2(before/'dx'/name,out/'dx'/name)
    vp=json.loads((out/'project/vehicle-project.json').read_text());donor=Path(vp['source_vehicle_dir'])
    exe=Path(profile['retail_exe']);dll=Path(profile['installed_proxy'])
    protected={str(p):sha_file(p) for p in (exe,dll)}
    for p,h in protected.items():
        if profile['protected_sha256'][Path(p).name]!=h:raise ValueError('protected input mismatch')
    reports={}
    lamp=parse_dxt(family/'headlamp-tga.dxt')
    sample,rgb,lamp_image,reports['lamp_swatch']=safe_lamp_sample((lamp.width,lamp.height,decode_rgba_pixels(lamp)),
        [parse_dx_bytes((before/f'dx/{frame}.dx').read_bytes()) for frame in ('car','complete')])
    (out/'tex/headlamp-tga.png').write_bytes(gtmat.png_from_rgba(*lamp_image))
    for frame in ('car','complete'):
        smap=json.loads((out/f'source-map/source-map-{frame}.json').read_text())['records']
        data=(out/f'dx/{frame}.dx').read_bytes()
        data,detail=finish.add_cap_detail(data,smap,profile['headlamp_cap_face_pairs'],
            target_draw=25,sample_uv=sample,sample_rgb=rgb)
        data,collar=finish.extend_collar(data,smap,profile['intercooler_faces'],
            padding_m=profile['intercooler_padding_m'],depth_m=profile['intercooler_depth_m'])
        reports[frame]={'headlamp_detail':detail,'intercooler_collar':collar}
        if frame=='car':
            data,reports['brake_glow']=finish.constrain_glow(data,halo_draw=30,lens_draw=24,inset_m=profile['glow_inset_m'])
        (out/f'dx/{frame}.dx').write_bytes(data)
    wheel=parse_dx_bytes((family/'wheel.dx').read_bytes());wg=source_geometry(wheel)
    donorwheel=parse_dx_bytes((donor/'wheel.dx').read_bytes());dg=source_geometry(donorwheel)
    def radius(gs):return max(math.hypot(*v.position[1:]) for g in gs for v in g.vertices)
    newratio=radius([wg[3]])/radius(wg.values());oldratio=radius([dg[3]])/radius(dg.values())
    side_name=wheel.physical_draws[0].texture_slots[0].value+'.dxt'
    stockside=parse_dxt(donor/side_name)
    side=finish.tyre_only_sidewall((stockside.width,stockside.height,decode_rgba_pixels(stockside,PNG_ROWS_FLIP_VERTICAL)),old_ratio=oldratio,new_ratio=newratio)
    rim_name=wheel.physical_draws[3].texture_slots[0].value+'.dxt';rim=parse_dxt(family/rim_name)
    interior,reports['rim_interior']=finish.rim_interior((rim.width,rim.height,decode_rgba_pixels(rim,PNG_ROWS_FLIP_VERTICAL)))
    reports['tyre']={'texture':side_name,'old_ratio':oldratio,'new_ratio':newratio,'method':'stock donor rubber only, extended beneath bead; no rim imagery in sidewall'}
    for name,img in ((side_name,side),(rim_name,interior)):
        path=out/'tex'/(Path(name).stem+'.png');path.write_bytes(gtmat.png_from_rgba(*img))
        vp['texture_edits'][name]={'source_sha256':sha_file(donor/name),'png':'../tex/'+path.name}
    dump(out/'project/vehicle-project.json',vp)
    dump(out/'reports/cleanup-profile.json',profile);dump(out/'reports/cleanup-operations.json',reports)
    run=Runner(out/'reports/commands.log');retail=donor.parents[3];steps={}
    retail_args=['--retail-data-sma',retail/'Data.sma','--retail-data-root',retail/'Data.sma_unpacked']
    steps['validate_vehicle']=run.mrtool('validate-vehicle',out/'project/vehicle-project.json')
    steps['project_validate']=run.mrtool('addon','project-validate',out/'project',*retail_args)
    steps['project_build']=run.mrtool('addon','project-build',out/'project',*retail_args,'--output',out/'author-build')
    steps['author_verify']=run.mrtool('addon','verify',out/'author-build')
    common=['--manifest',ROOT/'research/vehicles/sdk/examples/mercedes-ml320.json','--manifest',out/'project/addon.json','--project-build',f'{ADDON_ID}={out / "author-build"}']
    steps['runtime_prepare']=run.mrtool('addon','runtime-prepare',*common,'--output',out/'runtime')
    steps['runtime_verify']=run.mrtool('addon','runtime-verify',out/'runtime',*common)
    steps['launcher_build']=run.mrtool('addon','runtime-launcher-build',out/'runtime',*common,'--launcher-output',out/'launcher')
    for flag in ('--verify','--verify-launch-environment'):
        proc=subprocess.run([str(out/'launcher/mr-runtime-launcher.exe'),flag,str(exe),str(out/'runtime')],capture_output=True,text=True)
        if proc.returncode:raise ValueError(proc.stdout+proc.stderr)
        steps[flag]={'exit':proc.returncode,'output':proc.stdout}
    for p,h in protected.items():
        if sha_file(Path(p))!=h:raise ValueError('protected file changed')
    dump(out/'reports/build-validation.json',{'steps':steps,'protected_files_unchanged':protected,
        'baseline':str(before),'status':'OFFLINE_BUILD_VALIDATED_RUNTIME_VISUAL_CHECK_PENDING'})
    handoff='''# V-MESH4.10 private Subaru candidate

Final narrow cleanup of V4.9. No wheel fitment or physics changes. Original EXE and graphics DLL untouched.
Use the included launcher with --verify and --verify-launch-environment before --integrated, passing the retail MRallye.exe and runtime directory.
Compare Vehicle Select/race with reflections ON/OFF, headlight interiors and intercooler edges; rear view brake released/pressed and oblique views of taillight glow; wheel sidewall and opaque disc interior.
The baseline brake input response/placement was confirmed by the user. New surface-constrained glow and other visual changes require the user's game test. Offline previews approximate materials and do not simulate native environment mapping.
Private converted research assets: no redistribution. Race wheel placement and physics are deferred.
'''
    (out/'HANDOFF.md').write_text(handoff,encoding='utf-8')
    archive=out/'review'/(out.name+'-candidate.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for folder in ('runtime','launcher'):
            for p in sorted((out/folder).rglob('*')):
                if p.is_file():z.write(p,Path(out.name)/p.relative_to(out))
        z.writestr(out.name+'/HANDOFF.md',handoff)
    print(json.dumps({'output':str(out),'candidate':str(archive),'sha256':sha_file(archive)},indent=2))


if __name__=='__main__':main()
