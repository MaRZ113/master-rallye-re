"""Actual Windows GT Garage/source selection actions; private inputs only."""
import argparse,json,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.gui import WorkshopApp
from master_rallye.gt_source_project import GTSourceProject
from master_rallye.workshop.service import write_json
from validate_rally_workshop import descendants,screenshot

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inventory','source-project','viewer','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('create-source','donor','colour-database','colour-strings'):p.add_argument('--'+name,type=Path)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);root=tk.Tk();app=WorkshopApp(root,out/'workspace',ROOT,a.viewer)
    report={'status':'RUNNING','actions':[],'boundary':'Actual Windows Tk controls and D3D9 captures, not D3D8 gameplay'};errors=[];state={'index':0,'last':time.monotonic()}
    def record(name):report['actions'].append(name);write_json(out/'windows-validation.json',report)
    def button(win,text):return next(w for w in descendants(win)if isinstance(w,ttk.Button)and w['text']==text)
    def open_garage():button(root,'GT Garage Lab').invoke();record('Open actual GT Garage Lab button')
    def inventory():
        g=app.garage_window
        with patch('master_rallye.workshop.garage_view.filedialog.askopenfilename',return_value=str(a.inventory)):button(g.window,'Open inventory report').invoke()
        key=next(k for k,c in g.rows.items()if c.get('model_code')=='re0011');g.tree.selection_set(key);g.tree.see(key);g.selected();root.update();screenshot(g.window,out/'catalog-clio.png');record('Read-only complete catalog, exact Clio association and four original colors')
    def source():
        g=app.garage_window
        if a.create_source:
            if not all((a.donor,a.colour_database,a.colour_strings)):raise ValueError('Creation validation needs donor and original color tables')
            with patch('master_rallye.workshop.garage_view.filedialog.askopenfilename',side_effect=[str(a.create_source),str(a.colour_database),str(a.colour_strings)]),patch('master_rallye.workshop.garage_view.filedialog.askdirectory',return_value=str(a.donor)),patch('master_rallye.workshop.garage_view.filedialog.asksaveasfilename',return_value=str(a.source_project)),patch('master_rallye.workshop.garage_view.simpledialog.askstring',return_value='GtClio3'):
                button(g.window,'Create from selected').invoke()
            record('Create from exact catalog selection via shared automatic CLI');return
        with patch('master_rallye.workshop.garage_view.filedialog.askopenfilename',return_value=str(a.source_project/'gt-source-project.json')):button(g.window,'Open GT source project').invoke()
        select_blue()
    def select_blue():
        g=app.garage_window
        assert g.source_project is not None
        g.colour_box.current(1);button(g.window,'Select / build original').invoke();record('Choose original Illiad Blue via shared CLI/Core')
    def inspect_source():
        g=app.garage_window;assert g.source_project.data['selected']==1
        screenshot(g.window,out/'source-blue.png');button(g.window,'Source Undo').invoke();assert g.source_project.data['selected']==0
        button(g.window,'Source Redo').invoke();assert g.source_project.data['selected']==1
        button(g.window,'Source Restore').invoke();assert g.source_project.data['selected']==0
        reopened=GTSourceProject(a.source_project);assert reopened.data['selected']==0
        screenshot(g.window,out/'source-restored.png');button(g.window,'Open selected in Workshop').invoke();record('Source Undo/Redo/Restore/reopen and Open selected')
    def inspect_workshop():
        assert app.project and app.project.data['source_colourway']['source_index']==0
        assert app.project.validate()['status']=='PASS';screenshot(root,out/'workshop-clio.png');record('Actual Workshop project and generated resources validate')
    steps=[open_garage,inventory,source,*([select_blue]if a.create_source else[]),inspect_source,inspect_workshop]
    def tick():
        try:
            g=getattr(app,'garage_window',None)
            if app.busy or g and g.process is not None:
                if time.monotonic()-state['last']>180:raise TimeoutError('Owned GUI operation exceeded budget')
                root.after(200,tick);return
            if state['index']>=len(steps):
                assert not errors,errors;report['status']='PASS_WINDOWS_GUI';write_json(out/'windows-validation.json',report);app.close();return
            steps[state['index']]();state['index']+=1;state['last']=time.monotonic();root.after(900,tick)
        except Exception as e:
            import traceback
            report['status']='FAIL';report['error']=str(e);report['traceback']=traceback.format_exc();write_json(out/'windows-validation.json',report);root.destroy()
    with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *args,**kw:errors.append(str(args))):root.after(500,tick);root.mainloop()
    print(json.dumps(report,indent=2))
    if report['status']!='PASS_WINDOWS_GUI':raise SystemExit(1)

if __name__=='__main__':main()
