"""V4.12: template-aligned frontend icon and stock-reference wheel layering."""
from __future__ import annotations
import argparse,dataclasses,json,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import gtmat,vmesh_raster as raster
import vmesh_wheel_layers as layers
import vmesh_wheels as wheels
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry
from build_vmesh_impreza_experimental import Runner,dump,sha_file,ADDON_ID
from master_rallye.addon_sdk.ui_assets import BANKS,parse_bank,fit_rgba
from master_rallye.texture_authoring import decode_rgba_png
from master_rallye.dxt import parse_dxt,encode_png,decode_rgba_pixels
from master_rallye.vehicle_packaging import _open_sma_archive

def render_icon(family):
    items=raster.load_dx_family(family);mask=[]
    for item in items:
        texture=item.texture
        if texture:
            w,h,px=texture;px=bytearray(px)
            for i in range(0,len(px),4):px[i:i+3]=bytes((255,255,255))
            texture=(w,h,bytes(px))
        tris=[(*t[:6],(255,255,255),(255,255,255),(255,255,255)) for t in item.tris]
        mask.append(dataclasses.replace(item,texture=texture,tris=tris))
    w,h=512,256;cam=raster.Camera(145,8,96,(0,.65,0))
    rgb=raster.render(items,cam,w,h,bg=(0,0,0));alpha=raster.render(mask,cam,w,h,bg=(0,0,0));rgba=bytearray()
    for i in range(w*h):
        a=alpha[3*i];rgba.extend([min(255,round(c*255/a)) if a else 0 for c in rgb[3*i:3*i+3]]+[a])
    return gtmat.png_from_rgba(w,h,rgba)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--icon',type=Path);p.add_argument('--small-icon',type=Path);p.add_argument('--wheel-profile',type=Path,default=ROOT/'research/vehicles/vmesh412/subaru-wheel.json');a=p.parse_args()
    before=a.before.resolve();out=a.output.resolve()
    if out.exists():raise ValueError('output exists')
    for name in ('project','dx','tex'):shutil.copytree(before/name,out/name)
    for name in ('reports','review','preview'): (out/name).mkdir()
    family=before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    addon=json.loads((out/'project/addon.json').read_text());project=json.loads((out/'project/vehicle-project.json').read_text())
    donor=Path(project['source_vehicle_dir']);retail=donor.parents[3];exe=retail.parents[1]/'MRallye.exe'
    # The candidate preserves the protected installation used by prior phases.
    exe=ROOT.parent/'MRallye.exe';dll=ROOT.parent/'d3d8.dll';protected={str(p):sha_file(p) for p in (exe,dll)}
    if protected[str(exe)]!='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4':raise ValueError('retail executable mismatch')
    if a.small_icon:raise ValueError('this final pass preserves the human-qualified race thumbnail')
    if a.icon:
        shutil.copyfile(a.icon,out/'project/ui/subaru.png')
        config=json.loads((out/'project/ui-assets.json').read_text())
        config['icons']['vehicle_select_art']['sha256']=sha_file(out/'project/ui/subaru.png')
        dump(out/'project/ui-assets.json',config)
    png=(out/'project/ui/subaru.png').read_bytes()
    reference=donor.parent/'Pajero'/'wheel.dx'
    wtex=parse_dxt(family/'nevwheel-tga.dxt')
    profile=json.loads(a.wheel_profile.read_text())
    if set(profile)!={'version','shelf_width_scale','face_uv_scale'} or profile['version']!=1:raise ValueError('unsupported wheel profile')
    shutil.copyfile(a.wheel_profile,out/'project/wheel-layers.json')
    wheel,rim_image,wheel_report=layers.layer_rim((family/'wheel.dx').read_bytes(),reference.read_bytes(),
        (wtex.width,wtex.height,decode_rgba_pixels(wtex)),shelf_width_scale=profile['shelf_width_scale'],face_uv_scale=profile['face_uv_scale'])
    (out/'dx/wheel.dx').write_bytes(wheel)
    (out/'tex/nevwheel-tga.png').write_bytes(gtmat.png_from_rgba(*rim_image))
    project['texture_edits']['nevwheel-tga.dxt']['refresh_crc32']=True
    # Recover existing hub anchors from the unchanged tyre material's four
    # frontend instances, rather than deriving new placement or using physics.
    oldwheel=parse_dx_bytes((family/'wheel.dx').read_bytes());complete=parse_dx_bytes((out/'dx/complete.dx').read_bytes())
    wg=source_geometry(oldwheel);cg=source_geometry(complete)
    side_name=oldwheel.physical_draws[0].texture_slots[0].value
    side_draw=next(d.draw_index for d in complete.physical_draws if d.texture_slots[0].value==side_name)
    rim_draw=next(d.draw_index for d in complete.physical_draws if d.texture_slots[0].value=='nevwheel-tga')
    local=wg[0].vertices[0].position;count=len(wg[0].vertices);hubs=[]
    if len(cg[side_draw].vertices)!=4*count:raise ValueError('frontend wheel anchor layout changed')
    for i in range(4):
        v=cg[side_draw].vertices[i*count].position;mirror=1 if v[0]<0 else -1
        hubs.append([v[0]-mirror*local[0],v[1]-local[1],v[2]-local[2]])
    updated=wheels.embed((out/'dx/complete.dx').read_bytes(),wheel,hubs,[rim_draw])
    (out/'dx/complete.dx').write_bytes(updated)
    dump(out/'project/vehicle-project.json',project)
    dump(out/'reports/wheel-layers.json',{**wheel_report,'reference_sha256':sha_file(reference),'reference_path':str(reference),
        'frontend_rim_draw':rim_draw,'inherited_hubs':hubs,'hub_placement_policy':'recover existing anchors; no translation, rotation or physics change'})
    dump(out/'reports/ui-source.json',{'source':'CALLER_PROVIDED_FRONTEND_PNG' if a.icon else 'EXISTING_V411_ICON_PNG_UNCHANGED','race_png_unchanged':True,'source_png_sha256':sha_file(out/'project/ui/subaru.png')})
    run=Runner(out/'reports/commands.log');steps={};retail_args=['--retail-data-sma',retail/'Data.sma','--retail-data-root',retail/'Data.sma_unpacked']
    steps['project_validate']=run.mrtool('addon','project-validate',out/'project',*retail_args)
    steps['project_build']=run.mrtool('addon','project-build',out/'project',*retail_args,'--output',out/'author-build')
    steps['author_verify']=run.mrtool('addon','verify',out/'author-build')
    common=['--manifest',ROOT/'research/vehicles/sdk/examples/mercedes-ml320.json','--manifest',out/'project/addon.json','--project-build',f'{ADDON_ID}={out/"author-build"}']
    steps['runtime_prepare']=run.mrtool('addon','runtime-prepare',*common,'--output',out/'runtime')
    steps['runtime_verify']=run.mrtool('addon','runtime-verify',out/'runtime',*common)
    steps['launcher_build']=run.mrtool('addon','runtime-launcher-build',out/'runtime',*common,'--launcher-output',out/'launcher')
    for flag in ('--verify','--verify-launch-environment'):
        proc=subprocess.run([str(out/'launcher/mr-runtime-launcher.exe'),flag,str(exe),str(out/'runtime')],capture_output=True,text=True)
        if proc.returncode:raise ValueError(proc.stdout+proc.stderr)
        steps[flag]={'exit':0,'output':proc.stdout}
    current=out/'runtime/resource-root';changes=[]
    # A tested runtime directory contains user saves and mutable settings. The
    # frozen candidate ZIP is the asset baseline, not that live directory.
    with zipfile.ZipFile(before/'review'/(before.name+'-candidate.zip')) as prior_zip:
        prefix=before.name+'/runtime/resource-root/'
        baseline={n[len(prefix):]:prior_zip.read(n) for n in prior_zip.namelist() if n.startswith(prefix) and not n.endswith('/')}
    for name,prior_data in baseline.items():
            rel=Path(name);dest=current/rel
            if not dest.exists():raise ValueError('missing prior resource '+str(rel))
            if dest.read_bytes()!=prior_data:
                if rel.as_posix().lower() not in ('datagx/frontend/vehicleselect/carsheet_032_000.dxt','datagx/vehicles/imprezaproto/complete.dx','datagx/vehicles/imprezaproto/wheel.dx','datagx/vehicles/imprezaproto/nevwheel-tga.dxt'):
                    raise ValueError('unrelated resource changed '+str(rel))
                changes.append(rel.as_posix())
    for path,h in protected.items():
        if sha_file(Path(path))!=h:raise ValueError('protected file changed')
    ui=json.loads((out/'author-build/ui-assets.report.json').read_text());preview=[]
    for role,r in ui['roles'].items():
        bank=parse_bank((current/r['bank_path']).read_bytes())
        if bank['names'][r['frame']]!=Path(r['frame_path']).stem:raise ValueError('UI reference invalid')
        tex=parse_dxt(current/r['frame_path']);(out/'preview'/(role+'.png')).write_bytes(encode_png(tex))
        prefix,count,template,size=BANKS[role]
        donor_tex=parse_dxt(before/'runtime/resource-root'/r['frame_path'])
        (out/'preview'/(role+'-before.png')).write_bytes(encode_png(donor_tex))
        preview.append(f'<h2>{role}</h2><p>Before / after. Native size: {size}.</p><img style="width:256px;image-rendering:pixelated" src="{role}-before.png"><img style="width:256px;image-rendering:pixelated" src="{role}.png">')
    (out/'preview/source.png').write_bytes(png)
    (out/'preview/index.html').write_text('<h1>Subaru UI integration</h1><p>Offline texture previews; runtime loading of extended banks still requires the user test.</p>'+''.join(preview)+'<h2>Source model render</h2><img src="source.png">',encoding='utf-8')
    dump(out/'reports/validation.json',{'status':'PASS_OFFLINE_UI_RUNTIME_TEST_PENDING','steps':steps,'ui':ui,'prior_resource_changes':changes,
        'body_and_physics_preserved_except_frontend_rim_geometry':True,'protected_files_unchanged':protected,'physical_id':27,'class_local':'T2/local7','widget':'T2_Car8'})
    handoff='''# V-MESH4.12 private Subaru final candidate

Frontend icon pixels now align with the original CarSheet artwork bounds; native widget/atlas records and the correct race thumbnail are unchanged.
Wheel rim uses a measured stock Pajero shelf and recessed opaque face with separate guarded UV domains. Tyre geometry/materials, hub placement, physics and race body remain unchanged.
Use the included launcher with --verify and --verify-launch-environment before --integrated, passing the retail MRallye.exe and runtime directory. This build was not launched in-game.
Check Vehicle Select icon containment/alignment and wheel appearance in frontend/race. The optional frontend source is recorded separately; custom PNG input remains supported.
No original EXE, graphics DLL or game archive modified. Private research assets must not be redistributed.
'''
    (out/'HANDOFF.md').write_text(handoff,encoding='utf-8');archive=out/'review'/(out.name+'-candidate.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for folder in ('runtime','launcher'):
            for path in sorted((out/folder).rglob('*')):
                if path.is_file():z.write(path,Path(out.name)/path.relative_to(out))
        z.writestr(out.name+'/HANDOFF.md',handoff)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('candidate ZIP CRC failed')
    print(json.dumps({'candidate':str(archive),'sha256':sha_file(archive)},indent=2))

if __name__=='__main__':main()
