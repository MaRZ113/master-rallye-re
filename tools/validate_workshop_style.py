"""Exercise actual Binding v2 and local-stock browser/impact GUI on private data."""
import argparse,json,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.gui import WorkshopApp
from master_rallye.workshop.service import WorkshopProject,write_json
from master_rallye.dx import parse_dx_bytes
from validate_rally_workshop import descendants,screenshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('project','reference-family','reference-stem','target-diffuse','owned-environment','viewer','output'):parser.add_argument('--'+key,required=True)
    a=parser.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);root=tk.Tk();app=WorkshopApp(root,out/'workspace',ROOT,a.viewer)
    report={'status':'RUNNING','actions':[],'boundary':'Real Windows GUI and native GPU; not gameplay'};errors=[];index=0;idle=0;last=time.monotonic()
    def record(text,data=None):report['actions'].append({'action':text,'data':data});write_json(out/'validation.json',report)
    def opened():app._opened(WorkshopProject(a.project))
    def classic():app.appearance_name.set('Classic MR Style');app.appearance_switch()
    def assign(model):
        native=parse_dx_bytes((app.project.assets/model).read_bytes());draw=next(d for d in native.physical_draws if d.texture_tuple[0]==a.target_diffuse and d.unknown_0x24==7 and not any(d.flags_0x20[:2]))
        app.draws.selection_set(f'texture:{model}:{draw.draw_index}:1');app._draw_selected();app.assign_texture();root.update()
        win=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title().startswith('Assign Existing'))
        items=next(w for w in descendants(win)if isinstance(w,tk.Listbox));chosen=next(i for i in range(items.size())if items.get(i).endswith(a.owned_environment+'.dxt'))
        items.selection_set(chosen);items.see(chosen);items.event_generate('<<ListboxSelect>>');root.update();time.sleep(.1);root.update()
        screenshot(win,out/(model+'-binding.png'));next(w for w in descendants(win)if isinstance(w,ttk.Button)and w['text']=='Assign selected texture').invoke();record('native owned environment binding',{'model':model,'draw':draw.draw_index,'target':a.owned_environment})
    def browse():
        with patch('master_rallye.workshop.appearance_ui.filedialog.askdirectory',return_value=a.reference_family):app.browse_stock_materials()
    def use_reference():
        win=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title().startswith('Local stock'))
        tree=next(w for w in descendants(win)if isinstance(w,ttk.Treeview));key=next(k for k in tree.get_children()if tree.item(k,'values')[3]==a.reference_stem)
        tree.selection_set(key);tree.see(key);tree.event_generate('<<TreeviewSelect>>');root.update();screenshot(win,out/'stock-reference-browser.png')
        def acknowledge():
            impact=next(w for w in win.winfo_children()if isinstance(w,tk.Toplevel)and w.title()=='All affected texture uses');root.update();screenshot(impact,out/'all-affected-uses.png')
            next(w for w in descendants(impact)if isinstance(w,ttk.Button)and w['text']=='Apply to these declared uses').invoke()
        root.after(500,acknowledge)
        with patch('master_rallye.workshop.appearance_ui.simpledialog.askinteger',return_value=1),patch('master_rallye.workshop.appearance_ui.messagebox.askyesno',return_value=True):
            next(w for w in descendants(win)if isinstance(w,ttk.Button)and w['text']=='Use reference on selected owned slot…').invoke()
    def check():
        p=app.project;p.validate();edit=p.data['edits'][a.owned_environment+'.dxt'];assert edit['operation']=='local-stock-reference';assert 'LANCZOS'in edit['adaptation'];record('stock reference through actual browser/impact controls',edit)
        app.compare_appearance()
    def compare():
        win=next(w for w in root.winfo_children()if isinstance(w,tk.Toplevel)and w.title().startswith('Matched GPU'));screenshot(win,out/'classic-comparison.png');win.destroy();record('Classic GPU comparison')
        app.run('Build Classic MR Style candidate',lambda:app.project.build(out/'build',sdk_root=ROOT))
    def finish():
        assert(out/'build/candidate/Launch-SDK-Roster.cmd').is_file();record('Classic isolated candidate build PASS')
        report['status']='PASS_WINDOWS_CLASSIC_STYLE';write_json(out/'validation.json',report);app.close()
    actions=[opened,classic,lambda:assign('car.dx'),lambda:assign('complete.dx'),browse,use_reference,check,compare,finish]
    def tick():
        nonlocal index,idle,last
        try:
            if errors:raise ValueError(errors)
            if time.monotonic()-last>480:raise TimeoutError('Style GUI timeout')
            idle=0 if app.busy else idle+1
            if idle>=3:actions[index]();index+=1;idle=0;last=time.monotonic()
            if index<len(actions):root.after(150,tick)
        except Exception as e:
            import traceback
            report.update(status='FAIL',error=str(e),traceback=traceback.format_exc());write_json(out/'validation.json',report);root.destroy()
    root.report_callback_exception=lambda *args:errors.append(str(args))
    with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *args,**kw:errors.append(args)):
        root.after(500,tick);root.mainloop()
    if report['status']!='PASS_WINDOWS_CLASSIC_STYLE':raise ValueError(report)
    print(report['status'])


if __name__=='__main__':main()
