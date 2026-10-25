"""Real Windows V-SDK4B GUI/GPU exercise on private prepared Workshop projects.

Only dialog answers are provided by the harness. Tk widgets, asynchronous
workers, native captures, Core compilers and optional roster builds are real.
"""
import argparse,hashlib,json,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.gui import WorkshopApp
from master_rallye.workshop.service import WorkshopProject,write_json
from validate_rally_workshop import screenshot,descendants


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('lancer','stock','viewer','output'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--build',action='store_true')
    parser.add_argument('--addon-region',default='Unlettered white body strips')
    parser.add_argument('--stock-region',default='Undecorated shaded blue panel')
    a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    root=tk.Tk();app=WorkshopApp(root,a.output/'workspace',ROOT,a.viewer);errors=[]
    report={'status':'RUNNING','boundary':'Real Windows Tk/D3D9 and SDK compilation, not gameplay','actions':[]};baselines={};painted={};gpu_before={};index=0;idle=0;last=time.monotonic()
    def record(name,details=None):report['actions'].append({'action':name,'details':details});write_json(a.output/'validation.json',report)
    def button(label):
        widget=next(w for w in descendants(root)if isinstance(w,ttk.Button)and w['text']==label)
        assert not widget.instate(['disabled']);widget.invoke()
    def tab(label):
        notebook=next(w for w in descendants(root)if isinstance(w,ttk.Notebook))
        notebook.select(next(t for t in notebook.tabs()if notebook.tab(t,'text')==label));root.update()
    def open_project(path):app._opened(WorkshopProject(path))
    def before():
        p=app.project;baselines[p.data['kind']]={n:(p.assets/n).read_bytes()for n in ('car.dx','complete.dx','wheel.dx')};gpu_before[p.data['kind']]=(p.root/'preview/latest.bmp').read_bytes();record('open prepared '+p.data['kind'],str(p.root));screenshot(root,a.output/(p.data['kind']+'-before-gui.png'))
    def custom():app.appearance_name.set('Custom');app.appearance_switch()
    def paint():
        tab('Paint / Style');app.paint_region_name.set(a.addon_region if app.project.data['kind']=='addon'else a.stock_region);app.paint_color.set('40,140,190'if app.project.data['kind']=='addon'else'240,210,80');button('Paint qualified region')
    def painted_check():
        p=app.project;painted[p.data['kind']]=(p.root/'preview/latest.bmp').read_bytes();assert p.data['edits'];p.validate()
        difference=sum(x!=y for x,y in zip(gpu_before[p.data['kind']][54:],painted[p.data['kind']][54:]));assert difference>100,('No visible paint change',difference);record('visible paint GPU bytes',difference)
        screenshot(root,a.output/(p.data['kind']+'-paint-gui.png'));record('visible qualified paint / validate',p.data['edits'])
        p.save();q=WorkshopProject(p.root);q.materialize();assert q.data['edits']==p.data['edits']
        for name in p.data['inputs']:assert (q.assets/name).read_bytes()==(p.assets/name).read_bytes()
        record('saved/reopened exact compiled resources')
    def crew():
        tab('Crew Inspector');app.crew_name.set('driver');app.crew_selected();app.crew_values['vertical'].set('-.015');button('Apply crew correction')
    def crew_check():
        p=app.project;assert (p.assets/'complete.dx').read_bytes()!=baselines['addon']['complete.dx'];assert (p.assets/'wheel.dx').read_bytes()==baselines['addon']['wheel.dx'];p.validate();screenshot(root,a.output/'crew-correction-gui.png');record('compiled driver -15 mm; wheel unchanged')
        # Model variants have independent corrections; apply the same intentional edit to race.
        app.variant.set('Race');app.refresh()
    def crew_race():
        tab('Crew Inspector');app.crew_name.set('driver');app.crew_selected();app.crew_values['vertical'].set('-.015');button('Apply crew correction')
    def compare():tab('Paint / Style');button('Matched Original / Modified / Difference')
    def comparison_check():
        assert (app.project.root/'preview/comparison-before.png').read_bytes()!=(app.project.root/'preview/comparison-after.png').read_bytes()
        win=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title().startswith('Matched GPU'))
        screenshot(win,a.output/(app.project.data['kind']+'-comparison.png'));win.destroy();record('matched original/modified/difference real GPU')
    def history():
        p=app.project;state=p._state();before={n:f.read_bytes()for n in p.data['inputs']for f in [p.assets/n]};p.undo();p.redo();assert p._state()==state
        assert all((p.assets/n).read_bytes()==raw for n,raw in before.items());record('undo/redo preserves complete appearance/crew state')
    def build():
        if a.build:app.run('V-SDK4B isolated build',lambda:app.project.build(a.output/(app.project.data['kind']+'-build'),sdk_root=ROOT))
    def built():
        if a.build:assert (a.output/(app.project.data['kind']+'-build/candidate/Launch-SDK-Roster.cmd')).is_file();record('sealed '+app.project.data['kind']+' candidate built')
    def source():app.appearance_name.set('Source Fidelity');app.appearance_switch()
    def source_check():
        assert not app.project.data['edits'];record('source profile switch restores source textures; crew separate')
        app.appearance_name.set('Custom');app.appearance_switch()
    def preset():
        app.paint_color.set('40,140,190')
        with patch('master_rallye.workshop.appearance_ui.simpledialog.askstring',return_value='Owner blue'):button('Save named color…')
    def preset_check():assert app.project.data['color_presets']['Owner blue']==[40,140,190];record('named color persists')
    def finish():
        app.project.save();report.update(status='PASS_WINDOWS_APPEARANCE_AND_CREW',errors=errors);write_json(a.output/'validation.json',report);app.close()
    actions=[lambda:open_project(a.lancer),before,custom,paint,painted_check,crew,crew_check,crew_race,compare,comparison_check,history,preset,preset_check,build,built,source,source_check,
             lambda:open_project(a.stock),before,custom,paint,painted_check,compare,comparison_check,history,build,built,finish]
    def tick():
        nonlocal index,idle,last
        try:
            if errors:raise ValueError(str(errors))
            if time.monotonic()-last>480:raise TimeoutError('GUI operation stalled')
            idle=0 if app.busy else idle+1
            if idle>=3:actions[index]();index+=1;idle=0;last=time.monotonic()
            if index<len(actions):root.after(150,tick)
        except Exception as e:
            import traceback
            report.update(status='FAIL',error=str(e),traceback=traceback.format_exc());write_json(a.output/'validation.json',report);root.destroy()
    root.report_callback_exception=lambda *args:errors.append(str(args))
    with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *args,**kw:errors.append(args)):
        root.after(500,tick);root.mainloop()
    if report['status']!='PASS_WINDOWS_APPEARANCE_AND_CREW':raise ValueError(report)
    print(report['status'])


if __name__=='__main__':main()
