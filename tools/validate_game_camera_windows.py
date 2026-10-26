"""Exercise real Windows Camera Lab, Race HUD controls and D3D9 event paths.

Private qualified Workshop project required. Never launches Master Rallye.
"""
import argparse,json,shutil,subprocess,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject,write_json,sha
from master_rallye.workshop.gui import WorkshopApp
from validate_rally_workshop import screenshot


def validate(reference,viewer,output):
    output=Path(output)
    if output.exists():raise ValueError('Choose a fresh Windows evidence directory')
    output.mkdir(parents=True);shutil.copytree(reference,output/'project');p=WorkshopProject(output/'project');p.materialize()
    resources={f.name:sha(f.read_bytes())for f in p.assets.iterdir()if f.is_file()};original=p.marker_inspect();errors=[]
    root=tk.Tk();app=WorkshopApp(root,output/'workspace',ROOT,viewer)
    root.report_callback_exception=lambda *args:errors.append(str(args))
    def pump():
        end=time.monotonic()+180;idle=0
        while time.monotonic()<end:
            root.update();time.sleep(.03);idle=0 if app.busy else idle+1
            if errors:raise ValueError(errors)
            if idle>=6:return
        raise TimeoutError('Camera Lab worker timeout')
    def descendants(widget):
        for child in widget.winfo_children():yield child;yield from descendants(child)
    def click(window,label):
        button=next(b for b in descendants(window)if isinstance(b,ttk.Button)and str(b['text'])==label)
        if button.instate(['disabled']):raise AssertionError('Disabled action: '+label)
        button.invoke();pump()
    def check(value,message):
        if not value:raise AssertionError(message)
    report={'status':'RUNNING','gameplay':'PENDING_OWNER','private_project':str(p.root)}
    try:
        with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *a,**k:errors.append(str(a))):
            app._opened(p);pump();app.open_vehicle_studios();pump();app.vehicle_tabs.select(app.details_tab)
            app.marker_hex.set('#20D9E8');click(app.vehicle_window,'Preview marker tint');screenshot(app.vehicle_window,output/'marker-before-apply.png')
            check(p.marker_inspect()==original,'Preview changed native registration');click(app.vehicle_window,'Apply marker color');check(p.marker_inspect()['current']['hex']=='#20D9E8','Marker not authored')
            app.save();pump();check(WorkshopProject(p.root).marker_inspect()==p.marker_inspect(),'Marker save/reopen failed')
            app.undo();pump();check(p.marker_inspect()==original,'Marker undo failed');app.redo();pump();screenshot(app.vehicle_window,output/'marker-applied.png')
            click(app.vehicle_window,'Reset marker color');check(p.marker_inspect()==original,'Marker reset failed');app.undo();pump()
            marker=p.marker_inspect();app.open_camera_lab();pump();win=app.camera_lab_window;screenshot(win,output/'camera-original.png')
            for key,value in [('half_length_m','2.25'),('height_m','1.5')]:app.camera_lab_fields[key].set(value)
            click(win,'Apply qualified extents');current=p.camera_inspect()['current'];check(current=={'half_length_m':2.25,'height_m':1.5},'Custom camera not applied')
            click(win,'Save');click(win,'Undo');check(p.camera_inspect()['current']!=current,'Camera undo failed');click(win,'Redo');check(p.camera_inspect()['current']==current,'Camera redo failed')
            click(win,'Reset donor');check(p.vehicle_state()['camera']==p.vehicle_defaults()['camera'],'Camera donor reset failed');click(win,'Undo')
            click(win,'Reset original native');check(p.vehicle_state()['camera']is None,'Original camera reset failed');click(win,'Undo');check(p.marker_inspect()==marker,'Camera changed marker')
            app.camera_lab_view.set('original');click(win,'Capture selected view');app.camera_lab_view.set('modified');click(win,'Capture selected view');screenshot(win,output/'camera-modified-capture.png')
            click(win,'Gameplay Camera Preview');first=app.game_camera_process;check(first.poll()is None,'Standalone Gameplay preview did not open')
            click(win,'Free Inspection + camera/frustum guides');second=app.game_camera_process;first.wait(timeout=5);check(second is not first and second.poll()is None,'Owned preview replacement failed')
            app.close_camera_lab_preview();second.wait(timeout=5)
            app.show_help('game-camera');helpwin=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title().endswith('Offline Help'));screenshot(helpwin,output/'help.png');helpwin.destroy()
            app.validate();pump();p.save();reopened=WorkshopProject(p.root);reopened.materialize();check(reopened.vehicle_state()==p.vehicle_state(),'Authoring state lost on reopen')
            check(resources=={f.name:sha(f.read_bytes())for f in p.assets.iterdir()if f.is_file()},'Camera/marker changed geometry/textures')
            app.project=None;click(win,'Reset original native');check(reopened.vehicle_state()==p.vehicle_state(),'Stale popup mutated project');app.project=p
            value=p.camera_lab_export(view='modified',guides=False);pose=value['pose']
            args=[str(viewer),'--scene',value['scene'],'--source',value['source'],'--profile',str(Path(value['scene']).parent/'profile.json'),'--model','race','--game-camera',*map(str,pose['eye']),*map(str,pose['target']),str(pose['source_fov_degrees']),'--free-inspection','--exercise',str(output/'viewer-events')]
            subprocess.run(args,check=True,timeout=120)
            report.update(status='PASS_ACTUAL_WINDOWS_CAMERA_MARKER',marker=marker,camera=reopened.camera_lab_inspect(),resource_bytes_unchanged=True,save_undo_redo_reset_reopen=True,standalone_owned_viewer_lifetime=True,stale_window_guard=True,viewer_event_report=json.loads((output/'viewer-events.json').read_text()),ui_errors=errors)
    finally:
        app.close();write_json(output/'windows-validation.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('reference','viewer','output'):parser.add_argument('--'+key,type=Path,required=True)
    a=parser.parse_args();print(validate(a.reference,a.viewer,a.output)['status'])
