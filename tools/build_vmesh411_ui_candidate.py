"""Generate only Subaru UI assets and rebuild its existing Vehicle SDK candidate."""
from __future__ import annotations
import argparse,dataclasses,json,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import gtmat,vmesh_raster as raster
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--icon',type=Path);p.add_argument('--small-icon',type=Path);a=p.parse_args()
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
    png=a.icon.read_bytes() if a.icon else render_icon(family)
    decode_rgba_png(png);(out/'project/ui').mkdir();(out/'project/ui/subaru.png').write_bytes(png)
    small=a.small_icon.read_bytes() if a.small_icon else png;decode_rgba_png(small)
    (out/'project/ui/subaru-small.png').write_bytes(small)
    config={'version':1,'icons':{}}
    for role,basename in [('vehicle_select_art','subaru.png'),('smallcarsheet','subaru-small.png')]:
        addon['frontend'][role]={'policy':'project_frame','frame':BANKS[role][1]}
        config['icons'][role]={'png':'ui/'+basename,'sha256':sha_file(out/'project/ui'/basename)}
    dump(out/'project/addon.json',addon);dump(out/'project/ui-assets.json',config)
    dump(out/'reports/ui-source.json',{'source':'USER_PROVIDED_RGBA8_PNG' if a.icon else 'ACTUAL_V410_CANDIDATE_MODEL_RENDER',
        'original_GT3_icon_used':False,'source_png_sha256':sha_file(out/'project/ui/subaru.png'),
        'baseline':str(before),'baseline_dx_sha256':{n:sha_file(family/n) for n in ('car.dx','complete.dx','wheel.dx')}})
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
    for path in (before/'runtime/resource-root').rglob('*'):
        if path.is_file():
            rel=path.relative_to(before/'runtime/resource-root');dest=current/rel
            if not dest.exists():raise ValueError('missing prior resource '+str(rel))
            if dest.read_bytes()!=path.read_bytes():
                if rel.as_posix().lower() not in ('datascene/frontendscreens/vehicleselect.xml','datagame/options.xml'):
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
        with _open_sma_archive(retail/'Data.sma') as z:
            from master_rallye.dxt import parse_dxt_bytes
            donor_tex=parse_dxt_bytes(z.read(f'{prefix}_{template:03d}_000.dxt'))
        (out/'preview'/(role+'-before.png')).write_bytes(encode_png(donor_tex))
        preview.append(f'<h2>{role}</h2><p>Before / after. Native size: {size}.</p><img style="width:256px;image-rendering:pixelated" src="{role}-before.png"><img style="width:256px;image-rendering:pixelated" src="{role}.png">')
    (out/'preview/source.png').write_bytes(png)
    (out/'preview/index.html').write_text('<h1>Subaru UI integration</h1><p>Offline texture previews; runtime loading of extended banks still requires the user test.</p>'+''.join(preview)+'<h2>Source model render</h2><img src="source.png">',encoding='utf-8')
    dump(out/'reports/validation.json',{'status':'PASS_OFFLINE_UI_RUNTIME_TEST_PENDING','steps':steps,'ui':ui,'prior_resource_changes':changes,
        'all_vehicle_resources_byte_identical':True,'protected_files_unchanged':protected,'physical_id':27,'class_local':'T2/local7','widget':'T2_Car8'})
    handoff='''# V-MESH4.11 private Subaru UI candidate

Vehicle geometry/materials/physics are byte-identical to V4.10. Only the Subaru UI selectors and four appended-bank resources change.
Vehicle Select: appended CarSheet frame32. SmallCarSheet: appended frame30 for physical ID27. All stock frames remain intact.
The supplied Subaru icon is rendered from the working model; the available GT3 named mini entry is a shared orange placeholder and was not used.
Verify with launcher/mr-runtime-launcher.exe --verify "<retail MRallye.exe>" runtime and --verify-launch-environment "<retail MRallye.exe>" runtime; when ready, use --integrated with the same arguments.
Human runtime check needed: Subaru versus stock Navara in Vehicle Select, reentry, locked/unlocked selection, race and Results UI, and unrelated vehicles. No game was launched during preparation. Original EXE/DLL/Data.sma unchanged. Private assets must not be redistributed.
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
