"""Lightweight Heritage Garage over the reusable native source adapter."""
import json,subprocess,uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog
from .branding import apply_icon


class HeritagePanels:
    def open_heritage(self):
        if self.busy:return
        w=tk.Toplevel(self.root);apply_icon(w);w.title('Rally Workshop — MR Heritage Garage');w.geometry('1000x720');self.heritage_window=w
        source=tk.StringVar();family=tk.StringVar();name=tk.StringVar(value='MR Demo Heritage');runtime=tk.StringVar(value='HeritageVehicle');donor=tk.StringVar(value='Trooper');audio=tk.StringVar(value='7');features=tk.StringVar();retail_sma=tk.StringVar(value=str(self.sdk_root.parent/'corpora/retail/Data.sma') if hasattr(self,'sdk_root') else '');rows={}
        self.heritage_fields={'source':source,'family':family,'name':name,'runtime_family':runtime,'physics_donor':donor,'audio':audio,'features':features,'retail_sma':retail_sma}
        for key,label in [('source','Read-only Demo installation'),('family','Source native vehicle family'),('name','Independent addon display identity'),('runtime_family','Unique runtime namespace'),('physics_donor','Exact retail physics family (explicit)'),('audio','Tuned retail sound profile0–24 (explicit)'),('retail_sma','Original retail Data.sma for editable physics'),('features','Optional source-pinned native features JSON')]:
            row=ttk.Frame(w,padding=5);row.pack(fill='x');ttk.Label(row,text=label,width=43).pack(side='left')
            if key=='family':box=ttk.Combobox(row,textvariable=family,state='readonly');box.pack(side='left',fill='x',expand=True)
            else:ttk.Entry(row,textvariable=self.heritage_fields[key]).pack(side='left',fill='x',expand=True)
        note=tk.Text(w,bg='#191d23',fg='#e5e7eb',wrap='word',height=16);note.pack(fill='both',expand=True,padx=8)
        ttk.Label(w,text='Native MR fidelity; no GT Classic conversion. Class T2 is an explicit isolated test configuration.\nSource audio association is unqualified: select a known retail tuning profile consciously (7 = Navara).\nNew project does not install or replace a stock/addon slot. Configure a separate roster before Build.',padding=8).pack(fill='x')
        def show(value):
            if not w.winfo_exists():return
            note.delete('1.0','end');note.insert('end',json.dumps(value,indent=2,default=str))
        def inspect():
            from master_rallye.addon_sdk.heritage_source import edition,inspect_family
            path=source.get()
            def work():
                identity=edition(path);items=[inspect_family(f)for f in sorted((Path(path)/'DataGx/Vehicles').iterdir())if f.is_dir()];return identity,items
            def done(result):
                if not w.winfo_exists():return
                identity,items=result;rows.clear();rows.update({v['family']:v for v in items});box['values']=list(rows)
                if rows:family.set(next(iter(rows)))
                show({'source':identity,'vehicles':[{k:v[k]for k in ('family','qualified_for_staging','problems')}for v in items]})
            self.run('Inspect read-only Demo edition',work,done)
        def browse():
            path=filedialog.askdirectory(title='Original Demo installation',parent=w)
            if path:source.set(path);inspect()
        def choose_features():
            path=filedialog.askopenfilename(title='Explicit native glass/light recipe',filetypes=[('JSON','*.json')],parent=w)
            if path:features.set(path)
        def preview():
            from master_rallye.addon_sdk.heritage_source import stage_family
            from master_rallye.preview_scene import stage_vehicle
            path,selected=source.get(),family.get();output=self.workspace/'heritage-previews'/uuid.uuid4().hex[:12]
            def work():
                value=stage_family(path,selected,output);folder=Path(value['package']);scene=folder/'source.mrpv';stage_vehicle(folder/'car.dx',scene);value['scene']=str(scene);return value
            def done(value):
                if not w.winfo_exists():return
                show(value);self.close_camera_lab_preview();self.game_camera_process=subprocess.Popen([str(self.viewer),'--scene',value['scene'],'--source',str(Path(value['package'])/'car.dx'),'--model','frontend','--workshop'])
            self.run('Preview compatible native source',work,done)
        def create():
            from master_rallye.addon_sdk.heritage_source import create_author,apply_features
            from .service import WorkshopProject
            values={k:v.get()for k,v in self.heritage_fields.items()};folder=self._new_project();author=folder.with_name(folder.name+'-heritage-author')
            def work():
                create_author(values['source'],values['family'],author,name=values['name'],runtime_family=values['runtime_family'],physics_donor=values['physics_donor'],stock_audio_profile_id=int(values['audio']),retail_sma=values['retail_sma'])
                if values['features']:apply_features(author,values['features'])
                return WorkshopProject.create(author,folder)
            def done(project):
                if not w.winfo_exists():return
                w.destroy();self._opened(project)
            self.run('Create immutable Heritage project',work,done)
        buttons=ttk.Frame(w,padding=8);buttons.pack(fill='x')
        for label,command in [('Select Demo installation',browse),('Inspect edition',inspect),('Preview source',preview),('Native features profile…',choose_features),('Create Heritage project',create),('Help',lambda:self.show_help('heritage'))]:ttk.Button(buttons,text=label,command=command).pack(side='left')
