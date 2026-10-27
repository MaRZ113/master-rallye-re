"""Real Windows Tk + continuously running D3D9 camera editor acceptance."""
import argparse,ctypes,json,shutil,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject,sha,write_json
from master_rallye.workshop.gui import WorkshopApp
from master_rallye.workshop.camera_live import owned_window,send
from validate_rally_workshop import screenshot


def validate(reference,viewer,output):
    output=Path(output)
    if output.exists():raise ValueError('Fresh evidence directory required')
    output.mkdir(parents=True);shutil.copytree(reference,output/'project');project=WorkshopProject(output/'project');project.materialize()
    resources={f.name:sha(f.read_bytes())for f in project.assets.iterdir()if f.is_file()};root=tk.Tk();app=WorkshopApp(root,output/'workspace',ROOT,viewer);errors=[];result={'status':'RUNNING','gameplay':'PENDING_OWNER'}
    root.report_callback_exception=lambda *a:errors.append(str(a))
    def pump(seconds=.6):
        end=time.monotonic()+180;idle=0
        while time.monotonic()<end:
            root.update();time.sleep(.025);idle=0 if app.busy else idle+.025
            if errors:raise AssertionError(errors)
            if idle>=seconds:return
        raise TimeoutError('Camera2 GUI worker timeout')
    def widgets(w):
        for child in w.winfo_children():yield child;yield from widgets(child)
    def click(label):next(w for w in widgets(app.camera_lab_window)if isinstance(w,ttk.Button)and w['text']==label).invoke();pump()
    def feedback():
        paths=sorted((project.root/'preview/game-camera/modified').glob('live-*.json'),key=lambda p:p.stat().st_mtime)
        assert paths,'No actual viewer acknowledgment'
        return paths[-1],json.loads(paths[-1].read_text())
    try:
        with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *a,**k:errors.append(str(a))):
            app._opened(project);pump();app.open_camera_lab();pump();win=app.camera_lab_window
            baseline=project.vehicle_state();click('Open Live Preview');process=app.game_camera_process;pump(1.)
            assert process.poll()is None and owned_window(process)
            modes=[]
            for mode in range(5):
                app.camera_lab_preset.set(str(mode));pump();app.camera_live_fields['FOV'].set(str(75+mode*4));app.camera_live_aspect.set('16:9');pump()
                path,state=feedback();assert state['mode']==mode and abs(state['source_fov_degrees']-(75+mode*4))<.01,state
                assert app.game_camera_process is process and project.vehicle_state()==baseline,'Draft saved or restarted viewer'
                click('Capture Live View');pump();assert Path(str(path)+'.bmp').exists()
                shutil.copyfile(str(path)+'.bmp',output/f'mode-{mode}.bmp');modes.append(state)
            app.camera_lab_preset.set('0');pump();app.camera_live_fields['FOV'].set('78');app.camera_live_fields['Dist Back'].set('4.2');pump();click('Apply Live Draft')
            authored=project.vehicle_state();assert authored!=baseline and authored['camera']['mode_overrides']['follow0']['FOV']==78
            click('Save');assert WorkshopProject(project.root).vehicle_state()==authored
            click('Undo');assert project.vehicle_state()==baseline;click('Redo');assert project.vehicle_state()==authored
            click('Reset selected mode');assert not(project.vehicle_state()['camera']or{}).get('mode_overrides',{}).get('follow0');click('Undo');assert project.vehicle_state()==authored
            app.camera_live_fields['FOV'].set('100');pump();click('Cancel Live Draft');assert float(app.camera_live_fields['FOV'].get())==78
            path,state=feedback();hwnd=owned_window(process);user=ctypes.windll.user32
            user.SendMessageW(hwnd,0x20a,120<<16,0);pump();_,after=feedback();assert after['source_fov_degrees']<state['source_fov_degrees']
            user.SendMessageW(hwnd,0x201,1,(100<<16)|100);user.SendMessageW(hwnd,0x200,1,(120<<16)|130);user.SendMessageW(hwnd,0x202,0,0);pump();_,dragged=feedback();assert dragged['eye']!=after['eye'];assert project.vehicle_state()==authored
            screenshot(win,output/'live-editor.png');click('Capture Live View');shutil.copyfile(str(path)+'.bmp',output/'live-drag.bmp')
            assert not send(process,b'invalid');_,unchanged=feedback();assert unchanged==feedback()[1]
            app.camera_lab_view.set('original');pump();_,original=feedback();user.SendMessageW(hwnd,0x20a,120<<16,0);pump();assert feedback()[1]==original,'Original comparison was editable'
            app.camera_lab_view.set('modified');pump();click('Reset original native');assert project.vehicle_state()['camera']is None;click('Undo');assert project.vehicle_state()==authored
            assert app.game_camera_process is process and process.poll()is None
            assert resources=={f.name:sha(f.read_bytes())for f in project.assets.iterdir()if f.is_file()}
            app.close_camera_lab_preview();assert process.poll()is not None;click('Open Live Preview');second=app.game_camera_process;assert second is not process;app.close_camera_lab_preview();assert second.poll()is not None
            result.update(status='PASS_WINDOWS_LIVE_CAMERA2',modes=modes,one_process_for_all_edits=True,preview_drafts_not_saved=True,apply_save_reopen_undo_redo_cancel_reset=True,viewport_drag_and_wheel=True,original_read_only=True,resources_unchanged=True,owned_close_reopen=True,errors=errors)
    finally:app.close();write_json(output/'validation.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('reference','viewer','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(validate(a.reference,a.viewer,a.output)['status'])
