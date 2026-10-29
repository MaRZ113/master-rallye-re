"""Owner-local D3D9 evidence, exact source conservation and native comparison.

Neutral originals stay intact. Wheel-facing variants are explicit MR rest-pose
experiments, not recovered moving Michelin matrices. No MR game is launched.
"""
from pathlib import Path
import argparse,copy,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye import universal_vehicle_scene as u
from master_rallye.michelin_native_pilot import qualified,TURN,profile
from master_rallye.source_scene_preview import stage_source_scene,capture_views
from master_rallye.preview_scene import stage_vehicle
from master_rallye.workshop.service import WorkshopProject


def sheet(paths,output,labels):
    from PIL import Image,ImageDraw
    canvas=Image.new('RGB',(1440,750),(30,30,30));draw=ImageDraw.Draw(canvas)
    for i,(path,label)in enumerate(zip(paths,labels)):
        with Image.open(path)as im:
            im=im.convert('RGB');im.thumbnail((480,340));x=i%3*480;y=i//3*375
            canvas.paste(im,(x,y+28));draw.text((x+6,y+6),label,fill='white')
    canvas.save(output)


def windows_gui(pilot,scenes,viewer,output):
    """Open actual project and both originals in existing Tk application APIs."""
    import tkinter as tk
    import time
    from master_rallye.workshop.gui import WorkshopApp
    from validate_rally_workshop import screenshot
    output=u.output_directory(output,[pilot,scenes]);output.mkdir(parents=True)
    root=tk.Tk();errors=[];root.report_callback_exception=lambda *e:errors.append(str(e))
    app=WorkshopApp(root,output/'workspace',ROOT,viewer)
    def settle():
        deadline=time.monotonic()+90;stable=0
        while time.monotonic()<deadline:
            root.update();time.sleep(.025)
            if errors:raise AssertionError(str(errors))
            stable=0 if app.busy else stable+1
            if stable>=12:return
        raise AssertionError('Windows worker timeout')
    try:
        app._opened(WorkshopProject(pilot/'workshop'));settle();app.validate();settle()
        screenshot(root,output/'rav4-workshop.png')
        app.show_source_provenance();settle()
        dialog=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title()=='Immutable source provenance')
        screenshot(dialog,output/'rav4-provenance.png');dialog.destroy()
        app.open_source_garage();window=app.source_garage_window
        for catalog in ('Car25A','Car06A'):
            window._open(scenes/catalog/'assembly/scene/scene.json');settle()
            screenshot(window.window,output/(catalog+'-original-garage.png'))
        result={'status':'PASS_ACTUAL_WINDOWS_TK','errors':errors,'native_project_open_validate':True,'source_provenance_dialog':True,
            'original_neutral_reopen':['Car25A','Car06A'],'gameplay':'NOT TESTED'}
        (output/'validation.json').write_bytes(u.canonical(result));return result
    finally:root.destroy()


def run(scenes,pilot,viewer,output):
    from PIL import Image
    output=u.output_directory(output,[scenes,pilot]);output.mkdir(parents=True)
    views=('front','rear','left','right','top','isometric');report={'schema':'michelin-fidelity-evidence/1','neutral':{}}
    for catalog in ('Car25A','Car06A'):
        path=scenes/catalog/'assembly/scene/scene.json';scene=qualified(path)
        manifest=json.loads((path.parent/'manifest.json').read_text())
        assets={n:(path.parent/n).read_bytes()for n in manifest['files']if n!='scene.json'}
        original_bytes=path.read_bytes();derived=copy.deepcopy(scene)
        for node in derived['nodes']:
            if node['id']in('wheel-0','wheel-3'):
                node['local_transform']=u.multiply(node['local_transform'],TURN)
                node['transform_evidence']+='; explicit derived MR rest-pose Ypi for source-X rim outward; source_local_transform unchanged; Michelin moving basis WARN'
        derived['metadata']['mr_rest_pose_experiment']={'source_scene_sha256':u.sha(original_bytes),'not_source_runtime':True,'rotation':TURN}
        destination=output/catalog/'derived-scene'
        u.save_scene(derived,destination,assets)
        assert u.load_scene(destination/'scene.json')['meshes']==scene['meshes']
        for kind,s,root in (('original',scene,path.parent),('wheel-facing',derived,destination)):
            preview=output/catalog/(kind+'.mrpv');stage_source_scene(s,preview,scene_root=root)
            repeat=output/catalog/(kind+'-repeat.mrpv');stage_source_scene(s,repeat,scene_root=root)
            assert preview.read_bytes()==repeat.read_bytes()
            captures=output/catalog/kind
            capture_views(viewer,preview,captures,provenance=catalog+' '+kind+' | opaque source glass; L2 WARN',cull='cw')
            sheet([captures/(v+'.png')for v in views],output/(catalog+'-'+kind+'.png'),[catalog+' '+v+' | L2 WARN'for v in views])
        # Wheel/material/cull closeups: both real sides and a top window view.
        for mode in ('cw','ccw','none'):
            preview=output/catalog/'wheel-facing.mrpv'
            from master_rallye.source_scene_preview import viewer_command
            bmp=output/catalog/('cull-'+mode+'.bmp')
            subprocess.run(viewer_command(viewer,preview,capture=bmp,cull=mode,provenance='Cull diagnostic only; source renderer unqualified'),check=True,timeout=45)
            with Image.open(bmp)as im:im.save(bmp.with_suffix('.png'))
        for node in derived['nodes']:
            if node['id']!='wheel-1':node['mesh_ids']=[]
        preview=output/catalog/'wheel.mrpv';stage_source_scene(derived,preview,scene_root=destination)
        capture_views(viewer,preview,output/catalog/'wheel-closeup',provenance='Original tyre/rim and RGB, derived rest pose; no source motion parity',cull='cw')
        assert path.read_bytes()==original_bytes
        report['neutral'][catalog]={'original_scene_sha256':u.sha(original_bytes),'derived_scene_sha256':u.sha((destination/'scene.json').read_bytes()),
            'geometry_uv_materials_unchanged':True,'preview_repeat':True,'original_unchanged':True,'L2':'WARN',
            'LODs':[{'level':i,'scene_sha256':u.sha((scenes/catalog/('LOD%d'%i)/'scene/scene.json').read_bytes())}for i in range(4)]}
    work=WorkshopProject(pilot/'workshop');work.verify_inputs()
    native=output/'native';native.mkdir();preview=native/'native.mrpv'
    stage_vehicle(work.assets/'car.dx',preview,profile=work.preview_profile_path())
    for model in ('race','frontend'):
        for view in views:
            bmp=native/(model+'-'+view+'.bmp')
            # Orthographic inspection only: native material/state packets and
            # model selection remain staged MR data, not source draw states.
            command=[str(viewer),'--scene',str(preview),'--model',model,'--neutral-source','--orthographic','--fixed-view',view,
                '--source-front','positive-z','--cull','cw','--depth-write','shader','--provenance','MR authored native resources; D3D9, not Michelin or D3D8 runtime','--capture',str(bmp)]
            subprocess.run(command,check=True,timeout=45)
            with Image.open(bmp)as im:im.save(bmp.with_suffix('.png'))
        sheet([native/(model+'-'+v+'.png')for v in views],output/('RAV4-native-'+model+'.png'),['MR '+model+' '+v+' | D3D8 pending'for v in views])
    for name,extra in (('brake-off',[]),('brake-on',['--brake']),('window-closeup',['--preset','4','--zoom','.5']),('alpha-diagnostic',['--model','wheel','--preset','4'])):
        bmp=native/(name+'.bmp');command=[str(viewer),'--scene',str(preview),'--model','race','--preset','2','--cull','cw','--depth-write','shader','--capture',str(bmp),*extra]
        subprocess.run(command,check=True,timeout=45)
        with Image.open(bmp)as im:im.save(bmp.with_suffix('.png'))
    sheet([output/'Car25A/original'/('isometric.png'),output/'Car25A/wheel-facing/isometric.png',native/'race-isometric.png',native/'window-closeup.png',native/'brake-off.png',native/'brake-on.png'],output/'RAV4-source-native.png',
        ['Immutable Michelin neutral','Derived wheel rest pose; L2 WARN','MR native adaptation; D3D8 pending','Original panes, MR alpha96','MR brake OFF','MR brake ON, bounded lens mask'])
    report.update(native_project=str(work.root),gameplay='NOT TESTED',owner_approval='PENDING',viewer_sha256=u.sha(viewer.read_bytes()))
    (output/'validation.json').write_bytes(u.canonical(report));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('scenes','pilot','viewer','output'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--gui-only',action='store_true')
    a=p.parse_args()
    if a.gui_only:windows_gui(a.pilot.absolute(),a.scenes.absolute(),a.viewer.absolute(),a.output.absolute())
    else:run(a.scenes.absolute(),a.pilot.absolute(),a.viewer.absolute(),a.output.absolute())
