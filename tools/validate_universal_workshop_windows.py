"""Actual Windows Source Garage -> MR Workshop flow, with private owner inputs.

Creates a new isolated authoring project and GPU captures; never launches D3D8.
Service/Studio reversibility is tested separately by validate_source_garage_pilot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.universal_vehicle_scene import load_scene,output_directory
from master_rallye.workshop.gui import WorkshopApp
from master_rallye.workshop.service import WorkshopProject
from master_rallye.preview_scene import stage_vehicle
from validate_rally_workshop import screenshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('scene','donor','retail-sma','retail-root','base-roster','viewer','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--mr-visual-kit',action='store_true')
    args=parser.parse_args();scene=load_scene(args.scene)
    output=output_directory(args.output,[args.scene.parent,args.donor,args.retail_sma.parent,args.retail_root,
        scene['source']['root'],*scene['source'].get('protected_roots',[])])
    output.mkdir(parents=True);errors=[];root=tk.Tk()
    root.report_callback_exception=lambda *e:errors.append(str(e))
    app=WorkshopApp(root,output/'workspace',ROOT,args.viewer)
    def settle():
        deadline=time.monotonic()+300
        stable=0
        while time.monotonic()<deadline:
            root.update();time.sleep(.025)
            stable=0 if app.busy else stable+1
            if errors:raise AssertionError('Windows callback errors: '+str(errors))
            if stable>=12:return
        raise AssertionError('Windows worker timeout')
    def capture(name,source,model='race',preset=4,extra=()):
        from PIL import Image
        staged=output/(name+'.mrpv')
        profile=project.preview_profile_path()
        if source.name not in ('car.dx','complete.dx','wheel.dx'):
            profile=output/'wheel-local-layout.json'
            profile.write_text(json.dumps({'provenance':'Isolated exact native wheel resource in its local rest basis','race_wheel_instances':[]}))
        stage_vehicle(source,staged,profile=profile)
        bmp=output/(name+'.bmp')
        info=subprocess.STARTUPINFO();info.dwFlags|=subprocess.STARTF_USESHOWWINDOW;info.wShowWindow=0
        zoom='1.2' if preset==5 else '.9' if source.name.startswith('wheel-source') else '.68'
        subprocess.run([str(args.viewer),'--scene',str(staged),'--source',str(source),'--model',model,
                        '--preset',str(preset),'--zoom',zoom,'--capture',str(bmp),*extra],
                       check=True,timeout=60,startupinfo=info)
        with Image.open(bmp)as image:image.save(output/(name+'.png'))
    try:
        with patch('tkinter.messagebox.showerror',side_effect=lambda *a,**k:errors.append(str(a))):
            settle();app.open_source_garage();window=app.source_garage_window
            window._open(args.scene);window.create_mr_dialog()
            values={'donor_dir':args.donor,'retail_sma':args.retail_sma,'retail_root':args.retail_root,'base_roster':args.base_roster}
            for key,value in values.items():window.mr_fields[key].set(str(value))
            if args.mr_visual_kit:
                for value in window.mr_visual_options.values():value.set(True)
            screenshot(window.mr_dialog,output/'create-dialog.png')
            window.mr_create_button.invoke();settle()
            project=app.project
            if project is None or project.data['kind']!='addon' or project.data.get('car_id')!=29:
                raise AssertionError('Real Source Garage creation did not open its isolated addon')
            project.verify_inputs();app.validate();settle()
            visual=json.loads(Path(project.data['source_baseline']['native_adaptations']).read_text())['visual_kit']['options']
            if args.mr_visual_kit and not all(visual.values()):raise AssertionError('GUI visual choices did not reach the authoring service')
            drive=next(row['value']for row in project.physics_inspect()['rows']
                       if row['member']=='DataGame/vehicles.xml'and row['path']=='Engine/DriveType')
            if drive!=1:raise AssertionError('Qualified 2WD source did not receive the explicit MR RWD adaptation')
            screenshot(root,output/'workshop-opened.png')
            app.show_source_provenance();settle()
            provenance=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title()=='Immutable source provenance')
            screenshot(provenance,output/'source-provenance.png');provenance.destroy()
            app.variant.set('Frontend');app.refresh();settle();screenshot(root,output/'workshop-frontend.png')
            app.variant.set('Race');app.refresh();settle()
            for name,preset in (('front',1),('rear',2),('left',3),('isometric',4),('top',5),('right',6)):
                capture('mr-race-'+name,project.assets/'car.dx',preset=preset)
            capture('mr-frontend',project.assets/'complete.dx',model='frontend')
            capture('mr-brakes-on',project.assets/'car.dx',preset=2,extra=('--brake',))
            from PIL import Image
            for index in range(4):
                source=project.assets/('wheel-source'+str(index)+'.dx')
                for side,preset in (('outside',6),('inside',3)):
                    capture('wheel'+str(index)+'-'+side,source,model='wheel',preset=preset)
            report={'schema':'universal-workshop-windows/1','status':'PASS','project':str(project.root),
                    'source_garage_create_dialog':True,'actual_create_validate_open':True,'source_provenance_dialog':True,
                    'car_id':project.data['car_id'],'mr_drive_type':drive,'viewer_sha256':hashlib.sha256(args.viewer.read_bytes()).hexdigest(),
                    'captures':[p.name for p in sorted(output.glob('*.png'))],'errors':errors,'mr_visual_options':visual,
                    'boundary':'Actual Tk and D3D9 only; source-game renderer and D3D8 gameplay NOT TESTED'}
            (output/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
    finally:
        print('WINDOWS_UI_CLOSING',flush=True)
        # Enter the real event loop for teardown, as the application does.
        # Calling destroy after a long series of synchronous GPU captures
        # leaves Tk callback/variable cleanup outside its running main loop.
        root.after_idle(app.close)
        root.mainloop()
        print('WINDOWS_UI_CLOSED',flush=True)


if __name__=='__main__':main()
