"""Exercise actual Tk source preflight without activating windows over the game."""
from pathlib import Path
import argparse,json,sys,time,tkinter as tk
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye import universal_vehicle_scene as u
from master_rallye.workshop.gui import WorkshopApp
from qualify_source_garage import CORPUS


def run(output,viewer):
    paths=[ROOT/entry[0]for entry in CORPUS.values()]
    output=u.output_directory(output,[p.parent for p in paths]);output.mkdir(parents=True)
    root=tk.Tk();root.withdraw();errors=[];root.report_callback_exception=lambda *e:errors.append(str(e))
    app=WorkshopApp(root,output/'workspace',ROOT,viewer);checks=[]
    def settle():
        stable=0;deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            root.update();time.sleep(.025)
            if errors:raise AssertionError(str(errors))
            stable=0 if app.busy else stable+1
            if stable>=8:return
        raise AssertionError('Actual Tk worker timeout')
    try:
        app.open_source_garage();garage=app.source_garage_window;garage.window.withdraw()
        garage.qualification();assert not app.busy
        for name,entry in CORPUS.items():
            path=ROOT/entry[0];digest=u.sha(path.read_bytes());garage._open(path);settle()
            garage.qualification();settle()
            dialog=next(w for w in garage.window.winfo_children()if isinstance(w,tk.Toplevel)and w.title().startswith('Source qualification'))
            text=next(w for w in dialog.winfo_children()if isinstance(w,tk.Text))
            report=json.loads(text.get('1.0','end'));assert report['source_scene_sha256']==digest
            assert report['levels']['L4']=='NOT TESTED'and not report['native_entry_allowed']
            assert not dialog.winfo_ismapped() # hidden parent prevents activation
            dialog.destroy();assert u.sha(path.read_bytes())==digest
            checks.append({'vehicle':name,'source_scene_sha256':digest,'actual_open_worker_dialog':True})
        evo_path=ROOT/CORPUS['Evo2-4Runner'][0]
        garage._open(evo_path);settle();garage.source_color.set('4')
        garage.derive_evo2_color();settle()
        derived=garage.scene_root/'scene.json';reopened=u.load_scene(derived)
        assert reopened['metadata']['source_color_experiment']['source_color_index']==3
        assert str(garage.color_button['state'])!='disabled'
        assert garage.action_buttons['Create 4Runner Stable…'].instate(['disabled'])
        assert u.sha(evo_path.read_bytes())==checks[0]['source_scene_sha256']
        result={'schema':'source-qualification-windows/1','status':'PASS_ACTUAL_HIDDEN_TK','vehicles':checks,'errors':errors,
                'evo2_original_color_worker_reopened':str(derived),'derived_native_creation_disabled':True,
                'foreground_activation':False,'gui_screenshot':'NOT CAPTURED; keep owner game focus','gameplay':'NOT TESTED'}
        (output/'validation.json').write_bytes(u.canonical(result));return result
    finally:root.destroy()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True)
    a=p.parse_args();print(run(a.output.absolute(),a.viewer.absolute()))
