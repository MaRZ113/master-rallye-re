"""Real Windows Classic recipe generation, version navigation and report GUI.

Dialog paths are supplied; compilation, widgets and GPU captures are real.
Does not automatically approve any conversion for game-candidate builds.
"""
import argparse,json,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.gui import WorkshopApp
from master_rallye.workshop.service import WorkshopProject,write_json
from master_rallye.workshop.classic import require_classic_approval
from validate_rally_workshop import screenshot,descendants


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('project','recipe','stock-root','viewer','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);root=tk.Tk();app=WorkshopApp(root,a.output/'workspace',ROOT,a.viewer)
    result={'status':'RUNNING','actions':[],'boundary':'Actual Windows Tk/D3D9, no game launch or implicit owner approval'};errors=[];index=0;idle=0;last=time.monotonic();classic=None;before=None
    def record(action):result['actions'].append(action);write_json(a.output/'validation.json',result)
    def button(text):next(w for w in descendants(root)if isinstance(w,ttk.Button)and w['text']==text).invoke()
    def opened():
        nonlocal before
        project=WorkshopProject(a.project);before={n:(project.baseline/n).read_bytes()for n in('car.dx','complete.dx','wheel.dx')};app._opened(project)
    def generate():
        with patch('master_rallye.workshop.appearance_ui.filedialog.askopenfilename',return_value=str(a.recipe)),patch('master_rallye.workshop.appearance_ui.filedialog.askdirectory',return_value=str(a.stock_root)),patch('master_rallye.workshop.appearance_ui.filedialog.asksaveasfilename',return_value=str(a.output/'versions')):button('Rebuild as Classic…')
    def generated():
        nonlocal classic
        classic=app.project;assert classic.data['classic_generation']['version_style']=='Classic MR Style';assert (classic.baseline/'car.dx').read_bytes()!=before['car.dx'];screenshot(root,a.output/'classic-gui.png');record('Actual Rebuild as Classic button generated independent versions and GPU preview')
        classic.undo();assert classic.data['appearance']=='Classic MR Style';classic.redo();assert classic.data['appearance']=='Classic MR Style';record('Undo/Redo of transferred layers retains the correct Classic baseline identity')
        button('Review / approve Classic report…');root.update();win=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title().startswith('Classic conversion report'));screenshot(win,a.output/'report-pending-gui.png');win.destroy()
        try:require_classic_approval(classic)
        except ValueError:record('Unapproved Classic remains blocked for builds')
        else:raise AssertionError('GUI implicitly approved a conversion')
    def compare():button('Matched Original / Modified / Difference')
    def comparison():
        assert (classic.root/'preview/comparison-before.png').read_bytes()!=(classic.root/'preview/comparison-after.png').read_bytes();win=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title().startswith('Matched GPU'));screenshot(win,a.output/'comparison-gui.png');win.destroy();record('Matched source-import versus Classic native GPU comparison')
        app.appearance_name.set('Source Fidelity');app.appearance_switch()
    def source():
        assert app.project.data['appearance']=='Source Fidelity';assert all((app.project.baseline/n).read_bytes()==raw for n,raw in before.items());screenshot(root,a.output/'fidelity-gui.png');record('Source Fidelity dropdown navigates to byte-exact independent source version')
        app.appearance_name.set('Classic MR Style');app.appearance_switch()
    def reopened():
        assert app.project.root==classic.root
        app.project=WorkshopProject(classic.root);app.project.materialize();assert app.project.data['classic_generation']['approved_report_sha256']is None;record('Classic reopening persists source link and pending approval')
        result['status']='PASS_WINDOWS_CLASSIC_WORKFLOW';write_json(a.output/'validation.json',result);app.close()
    actions=[opened,generate,generated,compare,comparison,source,reopened]
    def tick():
        nonlocal index,idle,last
        try:
            if errors:raise ValueError(errors)
            if time.monotonic()-last>360:raise TimeoutError('Classic GUI worker timeout')
            idle=0 if app.busy else idle+1
            if idle>=3:actions[index]();index+=1;idle=0;last=time.monotonic()
            if index<len(actions):root.after(150,tick)
        except Exception as exc:
            import traceback
            result.update(status='FAIL',error=str(exc),traceback=traceback.format_exc());write_json(a.output/'validation.json',result);root.destroy()
    root.report_callback_exception=lambda *args:errors.append(str(args))
    with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *args,**kw:errors.append(str(args))),patch('master_rallye.workshop.appearance_ui.messagebox.showinfo',return_value=None):root.after(400,tick);root.mainloop()
    if result['status']!='PASS_WINDOWS_CLASSIC_WORKFLOW':raise ValueError(result)
    print(result['status'])


if __name__=='__main__':main()
