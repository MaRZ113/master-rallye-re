"""Real Tk, owned D3D9 IPC, history and persistence acceptance; private inputs."""
import argparse,copy,json,shutil,subprocess,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject,write_json,sha
from master_rallye.workshop.gui import WorkshopApp
from master_rallye.workshop.camera_live import owned_window,send,packet
from master_rallye.frontend_presentation import pose
from validate_rally_workshop import screenshot

def validate(reference,viewer,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);shutil.copytree(reference,output/'project');p=WorkshopProject(output/'project');p.materialize();p.frontend_update(0.)
    assets={f.name:sha(f.read_bytes())for f in p.assets.iterdir()if f.is_file()};baseline=copy.deepcopy(p.vehicle_state());root=tk.Tk();app=WorkshopApp(root,output/'workspace',ROOT,viewer);errors=[]
    root.report_callback_exception=lambda *args:errors.append(str(args))
    def pump(seconds=.5):
        end=time.monotonic()+180;idle=0
        while time.monotonic()<end:
            root.update();time.sleep(.025);idle=0 if app.busy else idle+.025
            if errors:raise AssertionError(errors)
            if idle>=seconds:return
        raise TimeoutError('Presentation worker stalled')
    def children(w):
        for c in w.winfo_children():yield c;yield from children(c)
    def button(parent,label):next(w for w in children(parent)if isinstance(w,ttk.Button)and w['text']==label).invoke();pump()
    def action(name):app.frontend_actions[name]();pump()
    try:
        with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *a,**kw:errors.append(str(a))):
            app._opened(p);pump();app.open_vehicle_studios();pump();app.vehicle_tabs.select(app.details_tab);pump()
            app.details_fields['display_name'].set('WORKSHOP CREW');pump();assert p.vehicle_state()==baseline and app.results_photo.width()==900
            screenshot(app.vehicle_window,output/'results-draft.png');button(app.results_picture.master,'Apply Results Name')
            edited=p.vehicle_state();assert edited['details']['display_name']=='WORKSHOP CREW'
            assert {k:v for k,v in edited['details'].items()if k!='display_name'}=={k:v for k,v in baseline['details'].items()if k!='display_name'}
            button(app.results_picture.master,'Undo');assert p.vehicle_state()==baseline
            button(app.results_picture.master,'Redo');assert p.vehicle_state()==edited
            button(app.results_picture.master,'Restore Results Name');assert p.vehicle_state()['details']['display_name']==p.vehicle_defaults()['details']['display_name']
            button(app.results_picture.master,'Undo');assert p.vehicle_state()==edited
            p.save();assert WorkshopProject(p.root).vehicle_state()==edited
            icon=p.results_name_preview();assert icon['dimensions']==[32,16]
            app.open_frontend_presentation();pump();screenshot(app.frontend_window,output/'frontend-editor.png');action('preview');pump(1.)
            process=app.frontend_session['process'];assert process.poll()is None and owned_window(process)
            before=copy.deepcopy(p.vehicle_state());app.frontend_offset.set('0.35');pump();path=p.root/'preview/frontend/live.json';state=json.loads(path.read_text());assert state['mode']==4 and abs(state['target'][1]-pose(.35)['target'][1])<1e-5
            assert p.vehicle_state()==before and app.frontend_session['process']is process
            def capture(name):
                live=json.loads(path.read_text());send(process,packet({'eye':live['eye'],'target':live['target'],'source_fov_degrees':45.},mode=4,aspect=4/3,revision=live['revision']+1,capture=True,editable=False));pump();shutil.copyfile(str(path)+'.bmp',output/(name+'.bmp'))
            capture('trooper-modified');app.frontend_view.set('original');pump();capture('trooper-original');app.frontend_view.set('modified');pump()
            action('auto');draft=float(app.frontend_offset.get());assert abs(draft-.453632)<.0001 and p.vehicle_state()==before
            action('apply');authored=p.vehicle_state();assert abs(authored['frontend']['vertical_offset_m']-draft)<1e-6
            p.save();assert WorkshopProject(p.root).vehicle_state()==authored
            action('undo');assert p.vehicle_state()==before;action('redo');assert p.vehicle_state()==authored
            action('reset');assert p.vehicle_state()['frontend']is None;action('undo');assert p.vehicle_state()==authored
            screenshot(app.frontend_window,output/'frontend-authored.png');capture('trooper-autoframe')
            app.frontend_view.set('stock NewRav');action('preview');pump(1.);process=app.frontend_session['process'];assert process.poll()is None
            path=p.root/'preview/frontend/live.json';capture('newrav-reference');assert p.vehicle_state()==authored
            action('close');assert process.poll()is not None
            assert {f.name:sha(f.read_bytes())for f in p.assets.iterdir()if f.is_file()}==assets,'Presentation changed resource bytes'
            p.vehicle_validate();report={'status':'PASS_WINDOWS_PRESENTATION','results_icon':icon,'offset_m':draft,'saved_reopened':True,'history_reset_restore':True,'same_process_live_draft':True,'stock_reference_read_only':True,'resource_bytes_unchanged':len(assets),'gameplay':'PENDING_OWNER'};write_json(output/'validation.json',report)
            return report
    finally:
        if getattr(app,'frontend_actions',None):
            try:app.frontend_actions['close']()
            except tk.TclError:pass
        app.close_camera_lab_preview();root.destroy()

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for key in('reference','viewer','output'):a.add_argument('--'+key,type=Path,required=True)
    p=a.parse_args();print(validate(p.reference,p.viewer,p.output)['status'])
