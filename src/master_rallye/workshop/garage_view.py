"""Read-only Compatibility Lab UI over the shared GT Garage CLI reports."""
import json
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,simpledialog
from .branding import apply_icon

class GarageWindow:
    def __init__(self,parent,tool_root,on_open=None):
        self.tool_root=Path(tool_root);self.process=None;self.log=None;self.report=None;self.path=None;self.rows={}
        self.source_project=None;self.on_open=on_open;self.operation='scan';self.report_path=None
        self.window=tk.Toplevel(parent);apply_icon(self.window);self.window.title('GT Garage Lab — source compatibility');self.window.geometry('1050x740');self.window.protocol('WM_DELETE_WINDOW',self.close)
        bar=ttk.Frame(self.window,padding=8);bar.pack(fill='x')
        ttk.Button(bar,text='Open inventory report',command=self.choose_report).pack(side='left')
        ttk.Button(bar,text='Scan local GT3 VOL',command=self.start_scan).pack(side='left',padx=8)
        ttk.Button(bar,text='Stop owned scan',command=self.cancel).pack(side='left')
        self.region=tk.StringVar(value='us');box=ttk.Combobox(bar,textvariable=self.region,values=['us','eu','jp'],state='readonly',width=5);box.pack(side='left',padx=10);box.bind('<<ComboboxSelected>>',lambda e:self.populate())
        sourcebar=ttk.Frame(self.window,padding=8);sourcebar.pack(fill='x')
        ttk.Button(sourcebar,text='Open GT source project',command=self.open_source).pack(side='left')
        ttk.Button(sourcebar,text='Create from selected',command=self.create_source).pack(side='left',padx=4)
        sourcebar=ttk.Frame(self.window,padding=8);sourcebar.pack(fill='x')
        self.colour=tk.StringVar();self.colour_box=ttk.Combobox(sourcebar,textvariable=self.colour,state='readonly',width=26);self.colour_box.pack(side='left',padx=8)
        ttk.Button(sourcebar,text='Select / build original',command=self.choose_colour).pack(side='left')
        for label,verb in [('Source Undo','undo'),('Source Redo','redo'),('Source Restore','restore')]:ttk.Button(sourcebar,text=label,command=lambda v=verb:self.source_history(v)).pack(side='left',padx=2)
        ttk.Button(sourcebar,text='Open selected in Workshop',command=self.open_selected).pack(side='left',padx=5)
        self.status=tk.StringVar(value='L0 = source/table evidence. L1/L2 and owner gameplay are separate acceptance levels.')
        ttk.Label(self.window,textvariable=self.status,wraplength=1000,padding=8).pack(fill='x')
        pane=ttk.Panedwindow(self.window,orient='vertical');pane.pack(fill='both',expand=True,padx=8,pady=4)
        frame=ttk.Frame(pane);pane.add(frame,weight=3)
        self.tree=ttk.Treeview(frame,columns=('model','colours','association','model_status','L1','L2'),show='tree headings',selectmode='browse');self.tree.heading('#0',text='Catalog vehicle')
        for k,label in [('model','Source code'),('colours','Colors'),('association','Association'),('model_status','L0 model'),('L1','L1'),('L2','L2')]:self.tree.heading(k,text=label);self.tree.column(k,width=95)
        self.tree.column('#0',width=280);scroll=ttk.Scrollbar(frame,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',self.selected)
        self.details=tk.Text(pane,bg='#191d23',fg='#e5e7eb',wrap='word',height=12,state='disabled');pane.add(self.details,weight=2)
    def show_text(self,text):
        self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('end',text);self.details.configure(state='disabled')
    def load(self,path):
        path=Path(path)
        if path.stat().st_size>192*1024*1024:raise ValueError('Garage report exceeds display budget')
        report=json.loads(path.read_text(encoding='utf-8'))
        if report.get('schema')!='gt-garage-inventory/1' or not isinstance(report.get('catalogs'),dict):raise ValueError('Qualified GT Garage inventory schema required')
        self.report=report;self.path=path;self.report_path=path;self.populate()
    def choose_report(self):
        name=filedialog.askopenfilename(parent=self.window,title='Open private GT Garage report',filetypes=[('Garage JSON','*.json')])
        if name:
            try:self.load(name)
            except (ValueError,OSError)as e:messagebox.showerror('GT Garage Lab',str(e),parent=self.window)
    def populate(self):
        if self.report is None:return
        self.tree.delete(*self.tree.get_children());self.rows={}
        cars=self.report['catalogs'].get(self.region.get(),{}).get('vehicles',[])
        if len(cars)>4096:raise ValueError('Garage catalog display budget')
        for i,car in enumerate(cars):
            key=str(i);self.rows[key]=car
            self.tree.insert('', 'end',iid=key,text=car['maker']+' '+car['name'],values=(car.get('model_code','?'),len(car.get('source_colourways',[])),car['association_status'],car.get('model_status','NOT TESTED'),car.get('L1','NOT TESTED'),car.get('L2','NOT TESTED')))
        self.status.set(f"{len(cars)} catalog entries · {self.report.get('summary',{}).get('inspected',0)} source members inspected · L0 is not conversion or gameplay acceptance")
        self.show_text(json.dumps({'source':self.report['source'],'coverage':self.report.get('summary',{}),'boundary':self.report['boundary']},indent=2,ensure_ascii=False))
    def selected(self,event=None):
        selected=self.tree.selection()
        if not selected:return
        c=self.rows[selected[0]];model=self.report['members'].get('cars/day/'+str(c.get('model_code')),{});body=model.get('body',{})
        info={'catalog':c,'source_model':{k:model[k]for k in ('status','sha256','bytes','reason','provenance')if k in model},'body':{k:body[k]for k in ('models','material_count','source_colourway_count','shape_triangle_sum_not_a_lod','selected_lod_geometry_status','material_roles_status')if k in body},'boundary':'Color names/IDs are source metadata, not tint presets. Unknown materials remain unqualified. Build only from a separately qualified immutable source import.'}
        self.show_text(json.dumps(info,ensure_ascii=False,indent=2))
    def open_source(self):
        name=filedialog.askopenfilename(parent=self.window,title='Open immutable GT source project',filetypes=[('Source project','gt-source-project.json')])
        if not name:return
        try:
            from ..gt_source_project import GTSourceProject
            self.source_project=GTSourceProject(Path(name).parent);self.refresh_source()
        except (ValueError,OSError,KeyError)as e:messagebox.showerror('Original GT colorway',str(e),parent=self.window)
    def create_source(self):
        if self.process is not None:return
        selected=self.tree.selection()
        if self.report is None or not selected:
            self.status.set('Select an exactly associated catalog vehicle first');return
        car=self.rows[selected[0]]
        if car.get('association_status')!='PASS':
            self.status.set('An exact catalog/source association is required');return
        paths={}
        for key,title in [('source','Original extracted GT3 model (.gz or decoded)'),('colour-database','Original carcolor.db'),('colour-strings','Original carcolor.sdb')]:
            name=filedialog.askopenfilename(parent=self.window,title=title)
            if not name:return
            paths[key]=name
        donor=filedialog.askdirectory(parent=self.window,title='Read-only retail MR donor vehicle directory')
        if not donor:return
        output=filedialog.asksaveasfilename(parent=self.window,title='New private GT source project directory (must not exist)')
        if not output:return
        family=simpledialog.askstring('Addon identity','Unique runtime family (letters and digits):',parent=self.window,initialvalue='Gt'+str(car['model_code']).title())
        if not family:return
        target=Path(output)
        if target.exists():messagebox.showerror('New source project','Choose a directory that does not exist',parent=self.window);return
        if target.resolve().is_relative_to(Path(donor).resolve()):messagebox.showerror('New source project','Output must be outside the read-only retail donor',parent=self.window);return
        identity=target.parent/(target.name+'.identity.json')
        if identity.exists():messagebox.showerror('New source project','Identity sidecar already exists; choose another name',parent=self.window);return
        identity.parent.mkdir(parents=True,exist_ok=True)
        identity.write_text(json.dumps({'addon':{'name':car['maker']+' '+car['name'],'manufacturer':car['maker'],'model':car['name'],'family':family}},indent=2),encoding='utf-8')
        command=[sys.executable,str(self.tool_root/'tools/gt_source_project.py'),'create','--inventory',str(self.report_path),'--region',self.region.get(),'--car-key',car['car_key'],'--donor',donor,'--identity',str(identity),'--output',str(target),'--mode','full']
        for key,value in paths.items():command.extend(['--'+key,value])
        self.operation='source';self.path=target/'gt-source-project.json';self.log=(target.parent/(target.name+'.build.log')).open('w',encoding='utf-8')
        try:self.process=subprocess.Popen(command,cwd=self.tool_root,stdout=self.log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except OSError as e:self.log.close();self.log=None;self.status.set(str(e));return
        self.status.set('Deriving an independent source project from the exact catalog join. Donor fitting remains an approximation.');self.window.after(250,self.poll)
    def refresh_source(self):
        s=self.source_project
        if s is None:return
        self.colour_box.configure(values=[f"{i}: {c['latin_name']}"for i,c in enumerate(s.data['colourways'])]);self.colour_box.current(s.data['selected'])
        self.status.set('Original source colors: separate immutable versions. Source Undo/Redo changes selection; manual Paint history stays in each version.')
        self.show_text(json.dumps({'selected_original_colorway':s.data['colourways'][s.data['selected']],'workshop':str(s.current().root),'versions':s.data['versions'],'boundary':s.data['boundary']},indent=2,ensure_ascii=False))
    def choose_colour(self):
        if self.source_project is None:return
        if self.process is not None:self.status.set('Wait for the owned scan/build to finish');return
        index=self.colour_box.current()
        if index<0:return
        self.operation='source';self.path=self.source_project.root/'gt-source-project.json'
        self.log=self.path.with_suffix('.build.log').open('w',encoding='utf-8')
        command=[sys.executable,str(self.tool_root/'tools/gt_source_project.py'),'select','--project',str(self.source_project.root),'--colour',str(index)]
        try:self.process=subprocess.Popen(command,cwd=self.tool_root,stdout=self.log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except OSError as e:self.log.close();self.log=None;self.status.set(str(e));return
        self.status.set('Building an independent original colorway. Source files and the other editable versions remain unchanged.');self.window.after(250,self.poll)
    def source_history(self,verb):
        if self.source_project is None or self.process is not None:return
        try:
            if verb=='restore':self.source_project.restore()
            else:self.source_project.step(verb=='redo')
            self.refresh_source()
        except (ValueError,OSError)as e:messagebox.showerror('Source selection history',str(e),parent=self.window)
    def open_selected(self):
        if self.source_project is None or self.process is not None:return
        try:
            p=self.source_project.current();p.verify_inputs()
            if self.on_open:self.on_open(p)
        except (ValueError,OSError)as e:messagebox.showerror('Open original colorway',str(e),parent=self.window)
    def start_scan(self):
        if self.process is not None:self.status.set('An owned Garage scan is already active');return
        source=filedialog.askopenfilename(parent=self.window,title='Read-only local GT3 volume',filetypes=[('GT3 volume','*.VOL'),('All files','*')])
        if not source:return
        output=filedialog.asksaveasfilename(parent=self.window,title='Private checkpoint report (existing file resumes)',defaultextension='.json',initialdir=str(self.tool_root/'.research-output/vehicles/gt-garage'))
        if not output:return
        self.operation='scan'
        self.path=Path(output);self.path.parent.mkdir(parents=True,exist_ok=True);self.log=self.path.with_suffix('.scan.log').open('w',encoding='utf-8')
        command=[sys.executable,str(self.tool_root/'tools/gt_garage.py'),'--vol',source,'--output',output]
        if self.path.exists():command.append('--resume')
        try:self.process=subprocess.Popen(command,cwd=self.tool_root,stdout=self.log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except OSError as e:self.log.close();self.log=None;self.status.set('Could not start read-only scan: '+str(e));return
        self.status.set('Hashing original volume and scanning bounded source records. Stop leaves the last checkpoint intact.');self.window.after(250,self.poll)
    def poll(self):
        if self.process is None:return
        code=self.process.poll()
        if code is None:self.window.after(250,self.poll);return
        self.process=None;self.log.close();self.log=None
        if code:self.status.set('Operation stopped or failed; inspect '+str(self.path.with_suffix('.build.log'if self.operation=='source'else'.scan.log')))
        else:
            try:
                if self.operation=='source':
                    from ..gt_source_project import GTSourceProject
                    self.source_project=GTSourceProject(self.path.parent);self.refresh_source()
                else:self.load(self.path)
            except (ValueError,OSError)as e:self.status.set(str(e))
    def cancel(self):
        if self.process is not None:self.process.terminate()
    def close(self):
        self.cancel()
        if self.process is not None:
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        if self.log:self.log.close()
        self.window.destroy()
