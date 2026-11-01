"""Small asynchronous authoring panel for the isolated V-SET1 package builder."""
import json
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import uuid


def open_setup_authoring(parent, tool_root):
    tool_root=Path(tool_root)
    w=tk.Toplevel(parent);w.title('Rally Workshop — In-game Setup pilot');w.geometry('820x640')
    data=json.loads((tool_root/'research/vehicles/vset1/seatbuggy-pilot.json').read_text())
    ttk.Label(w,text='Separate setup package · no CarID allocation or changes to the open vehicle',wraplength=760).pack(pady=12)
    fields={};form=ttk.Frame(w,padding=10);form.pack(fill='x')
    for row,(key,label)in enumerate((('identity','Stable package identity'),('family','Existing source family'),('car_id','Existing physical CarID'),('livery_default','Original livery label'),('livery_alternative','Derived livery label'),('alternative_tyre','Complete original tire table'))):
        ttk.Label(form,text=label).grid(row=row,column=0,sticky='w');v=tk.StringVar(value=str(data[key]));fields[key]=v
        if key=='alternative_tyre':ttk.Combobox(form,textvariable=v,state='readonly',values=tuple(x for x in ('harddirt','tarmac','gravel','grass','mud') if x!=data['stock_tyre']),width=58).grid(row=row,column=1,sticky='ew')
        else:ttk.Entry(form,textvariable=v,width=60).grid(row=row,column=1,sticky='ew')
    paths={}
    for row,(key,label)in enumerate((('upstream','Accepted PS2 renderer pc-port folder'),('ps2-assets','Existing private PS2Vehicles folder'),('retail','Qualified retail unpacked root'),('candidate','Accepted SDK CMD candidate folder'),('game-root','Original game directory')),start=6):
        ttk.Label(form,text=label).grid(row=row,column=0,sticky='w');v=tk.StringVar();paths[key]=v
        ttk.Entry(form,textvariable=v,width=60).grid(row=row,column=1,sticky='ew')
        def browse(variable=v):
            value=filedialog.askdirectory(parent=w)
            if value:variable.set(value)
        ttk.Button(form,text='…',command=browse,width=3).grid(row=row,column=2)
    form.columnconfigure(1,weight=1)
    defaults={key:tk.BooleanVar(value=bool(data[key]))for key in ('default_livery','default_tyre')}
    options=ttk.Frame(w);options.pack(fill='x',padx=10)
    ttk.Checkbutton(options,text='Default: alternative livery',variable=defaults['default_livery']).pack(side='left')
    ttk.Checkbutton(options,text='Default: alternative tires',variable=defaults['default_tyre']).pack(side='left')
    def recipe():
        config=dict(data)
        for key,v in fields.items():config[key]=int(v.get())if key=='car_id'else v.get()
        config['ps2_family']=config['family'].upper()
        for key,v in defaults.items():config[key]=int(v.get())
        return config
    def load_recipe():
        value=filedialog.askopenfilename(parent=w,filetypes=[('Setup authoring recipe','*.json')])
        if not value:return
        try:
            from ..addon_sdk.vehicle_setup import decode_json
            content=decode_json(Path(value).read_bytes());config=content.get('vehicle',content)
            if config.get('schema')!='vehicle-setup-pilot/1':raise ValueError('Select a V-SET1 authoring recipe')
            for key,v in fields.items():v.set(str(config[key]))
            for key,v in defaults.items():v.set(bool(config[key]))
            for key,v in paths.items():v.set(content.get('inputs',{}).get(key,v.get()))
            data.clear();data.update(config)
        except (ValueError,OSError,KeyError)as e:messagebox.showerror('Setup recipe',str(e),parent=w)
    def save_recipe():
        value=filedialog.asksaveasfilename(parent=w,defaultextension='.json',filetypes=[('Setup authoring recipe','*.json')])
        if not value:return
        try:
            if Path(value).exists():raise ValueError('Choose a new recipe file; original inputs are preserved')
            Path(value).write_text(json.dumps({'schema':'vehicle-setup-authoring/1','vehicle':recipe(),'inputs':{k:v.get()for k,v in paths.items()}},indent=2)+'\n')
        except (ValueError,OSError)as e:messagebox.showerror('Setup recipe',str(e),parent=w)
    ttk.Button(options,text='Load recipe',command=load_recipe).pack(side='right')
    ttk.Button(options,text='Save recipe',command=save_recipe).pack(side='right')
    status=tk.StringVar(value='Original source bytes stay read-only. The pilot uses a private windowed game host. No installed DLL is replaced.')
    ttk.Label(w,textvariable=status,wraplength=780).pack(fill='x',padx=12,pady=10)
    logbox=tk.Text(w,height=12,wrap='word');logbox.pack(fill='both',expand=True,padx=12)
    running={}
    last_output={}
    def preview():
        path=last_output.get('path')
        if path is None:return
        from PIL import Image,ImageTk
        window=tk.Toplevel(w);window.title('Original and derived livery panels')
        window.image=ImageTk.PhotoImage(Image.open(path/'livery-panels.png'))
        ttk.Label(window,image=window.image).pack()
    def poll():
        process=running.get('process')
        if process is None:return
        if process.poll()is None:w.after(400,poll);return
        running['log'].close();text=running['path'].read_text(errors='replace');logbox.delete('1.0','end');logbox.insert('end',text[-16000:])
        status.set(('Build complete; owner gameplay remains pending. 'if process.returncode==0 else'Build rejected; inspect the exact diagnostic. ')+str(running['output']))
        if process.returncode==0:last_output['path']=running['output'];preview_button.configure(state='normal')
        running.clear();button.configure(state='normal')
    def build():
        if running:return
        try:
            config=recipe()
            if any(not v.get()for v in paths.values()):raise ValueError('Select all five local source/baseline folders')
            base=tool_root/'.research-output/vehicles/v-set1';base.mkdir(parents=True,exist_ok=True)
            token='workshop-'+uuid.uuid4().hex[:10];config_path=base/(token+'.json');output=base/token
            config_path.write_text(json.dumps(config,indent=2)+'\n');log_path=base/(token+'.log');stream=log_path.open('w',encoding='utf-8')
            command=[sys.executable,str(tool_root/'tools/build_vehicle_setup_pilot.py'),'--output',str(output),'--vehicle-config',str(config_path),'--build']
            for key,v in paths.items():command.extend(['--'+key,v.get()])
            try:process=subprocess.Popen(command,cwd=tool_root,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            except Exception:stream.close();raise
            running.update(process=process,log=stream,path=log_path,output=output);button.configure(state='disabled');status.set('Validating source pins, panel UV ownership and complete tire tables, then building the private runtime…');w.after(400,poll)
        except (ValueError,OSError)as e:messagebox.showerror('Setup package',str(e),parent=w)
    button=ttk.Button(w,text='Build isolated setup candidate',command=build);button.pack(pady=10)
    preview_button=ttk.Button(w,text='Preview original / derived livery panels',command=preview,state='disabled');preview_button.pack(pady=4)
    def close():
        if running:status.set('Wait for the owned build to finish before closing this panel.');return
        w.destroy()
    w.protocol('WM_DELETE_WINDOW',close)
    return w
