"""Lightweight Windows Studio shell; all authoring calls go through service.py."""
from __future__ import annotations
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .service import WorkshopProject, write_json
from master_rallye.dxt import DxtTexture, encode_png, PNG_ROWS_PRESERVE_STORED
from master_rallye.preview_scene import stage_vehicle
from master_rallye.dx import parse_dx_bytes
from master_rallye.material_semantics import MaterialSemantics

def bmp_png(path):
    import struct
    b=Path(path).read_bytes();offset=struct.unpack_from('<I',b,10)[0];w,h=struct.unpack_from('<ii',b,18)
    if b[:2]!=b'BM' or w<1 or h==0 or struct.unpack_from('<H',b,28)[0]!=32 or struct.unpack_from('<I',b,30)[0]!=0:raise ValueError('Unsupported GPU capture BMP')
    pixels=b[offset:];height=abs(h)
    if len(pixels)!=w*height*4:raise ValueError('Invalid GPU capture length')
    rows=[pixels[i*w*4:(i+1)*w*4] for i in range(height)]
    if h>0:rows.reverse()
    opaque=bytearray(b''.join(rows));opaque[3::4]=b'\xff'*(w*height)
    return encode_png(DxtTexture('GPU capture',1,0,w,height,bytes(opaque),b''),PNG_ROWS_PRESERVE_STORED)

class WorkshopApp:
    def __init__(self, root, workspace, sdk_root, viewer):
        self.root=root;self.workspace=Path(workspace).resolve();self.workspace.mkdir(parents=True,exist_ok=True)
        self.sdk_root=Path(sdk_root).resolve();self.viewer=Path(viewer).resolve();self.messages=queue.Queue();self.busy=False
        self.project=None;self.current_info=None;self.process=None;self.last_selection='';self.photos=[];self.library={}
        self.variant=tk.StringVar(value='Frontend');self.texture_name=tk.StringVar();self.texture_details=tk.StringVar();self.gain=[tk.StringVar(value='1.0') for _ in range(3)]
        self.status=tk.StringVar(value='Open an SDK project or create a qualified stock project to begin.')
        self.name=tk.StringVar(value='RALLY WORKSHOP');self.context=tk.StringVar(value='No vehicle selected')
        self._style();self._layout();self._load_library();self.root.after(100,self._poll)
        self._sync_controls()
        self.root.protocol('WM_DELETE_WINDOW',self.close)

    def _style(self):
        self.root.title('Rally Workshop — Vehicle SDK Studio');self.root.geometry('1460x900');self.root.minsize(1120,700);self.root.configure(bg='#202329')
        style=ttk.Style(self.root);style.theme_use('clam')
        style.configure('.',background='#252930',foreground='#e5e7eb',fieldbackground='#191d23',font=('Segoe UI',10))
        style.configure('TButton',padding=(9,6));style.map('TButton',background=[('active','#464134')])
        style.configure('Accent.TButton',background='#bb8736',foreground='#111318')
        style.configure('Treeview',background='#191d23',fieldbackground='#191d23',rowheight=27)
        style.map('Treeview',background=[('selected','#65502f')]);style.configure('TNotebook.Tab',padding=(10,8))
        style.map('TNotebook.Tab',background=[('selected','#55452b'),('active','#39414b')],foreground=[('selected','#f1cc8b')])
        style.map('TCombobox',fieldbackground=[('readonly','#191d23'),('disabled','#282d34')],foreground=[('readonly','#e5e7eb'),('disabled','#9ca3af')])
        style.configure('Header.TLabel',font=('Segoe UI',19,'bold'),foreground='#e5b56a')

    def _layout(self):
        top=ttk.Frame(self.root,padding=10);top.pack(fill='x')
        ttk.Label(top,text='RALLY WORKSHOP',style='Header.TLabel').pack(side='left',padx=(0,24))
        self.buttons={}
        for label,command in [('Open project',self.open_project),('Open DX family',self.open_family),('New stock',self.new_stock),('Save',self.save),('Validate',self.validate),('Build',self.build),('Restore all',lambda:self.restore(None))]:
            button=ttk.Button(top,text=label,command=command,style='Accent.TButton' if label=='Build' else 'TButton');button.pack(side='left',padx=3);self.buttons[label]=button
        self.outer=ttk.Panedwindow(self.root,orient='vertical');self.outer.pack(fill='both',expand=True,padx=10)
        main=ttk.Panedwindow(self.outer,orient='horizontal');self.outer.add(main,weight=5)
        left=ttk.Frame(main,padding=8);main.add(left,weight=1)
        ttk.Label(left,text='VEHICLE LIBRARY').pack(anchor='w',pady=(0,8))
        self.library_tree=ttk.Treeview(left,show='tree',selectmode='browse');self.library_tree.pack(fill='both',expand=True)
        self.library_tree.bind('<<TreeviewSelect>>',self._library_selected)
        ttk.Button(left,text='Remove from library',command=self.remove_library).pack(fill='x',pady=5)
        center=ttk.Frame(main,padding=9);main.add(center,weight=4)
        ttk.Label(center,textvariable=self.name,style='Header.TLabel').pack(anchor='w')
        ttk.Label(center,textvariable=self.context,wraplength=650).pack(anchor='w',pady=5)
        controls=ttk.Frame(center);controls.pack(fill='x',pady=6)
        self.model_box=ttk.Combobox(controls,textvariable=self.variant,values=['Race','Frontend','Wheel'],width=12,state='readonly');self.model_box.pack(side='left')
        self.model_box.bind('<<ComboboxSelected>>',lambda e:self.refresh())
        ttk.Button(controls,text='Open interactive 3D',command=self.open_viewer).pack(side='left',padx=7)
        ttk.Button(controls,text='Reload preview',command=self.refresh).pack(side='left')
        ttk.Label(center,text='Last compiled GPU capture · navigation runs in the managed native 3D window').pack(anchor='w',pady=(1,5))
        self.capture=tk.Label(center,bg='#1a1e24',fg='#b6bdc7',text='MANAGED D3D9 VIEWPORT\n\nOpen a project to render its actual resources.\nInteractive navigation runs in the existing native Previewer window.\n\nThis panel shows the latest GPU capture, not a simulated viewport.',font=('Segoe UI',12),justify='center')
        self.capture.pack(fill='both',expand=True)
        ttk.Label(center,text='3D: LMB orbit / geometric pick · MMB pan · wheel zoom · F focus · Home reset\nF3 actual-data HUD · Ctrl1–6 save / Shift1–6 recall view · R reload\nD3D9 approximation: world lighting, ordering and native damage still require game tests.',wraplength=680).pack(anchor='w',pady=9)
        right=ttk.Frame(main,padding=8);main.add(right,weight=2)
        tabs=ttk.Notebook(right);tabs.pack(fill='both',expand=True)
        materials=ttk.Frame(tabs,padding=6);tabs.add(materials,text='Inspect / Texture')
        self.draws=ttk.Treeview(materials,columns=('id','group'),show='headings',height=8,selectmode='browse');self.draws.heading('id',text='Draw');self.draws.heading('group',text='Group / native material')
        self.draws.column('id',width=45,stretch=False);self.draws.column('group',width=230);self.draws.pack(fill='both',expand=True);self.draws.bind('<<TreeviewSelect>>',self._draw_selected)
        self.inspector=tk.Text(materials,height=7,width=42,bg='#191d23',fg='#d5dae0',wrap='word',font=('Consolas',9),relief='flat');self.inspector.pack(fill='x',pady=6)
        self.texture_box=ttk.Combobox(materials,textvariable=self.texture_name,state='readonly');self.texture_box.pack(fill='x');self.texture_box.bind('<<ComboboxSelected>>',lambda e:self.show_texture())
        ttk.Label(materials,textvariable=self.texture_details,wraplength=330).pack(anchor='w',pady=3)
        self.texture_picture=tk.Label(materials,bg='#191d23',fg='#bdc4cf',text='Select a referenced texture',height=5);self.texture_picture.pack(fill='x',pady=5)
        row=ttk.Frame(materials);row.pack(fill='x')
        for label,var in zip(('R','G','B'),self.gain):ttk.Label(row,text=label).pack(side='left');ttk.Entry(row,textvariable=var,width=5).pack(side='left',padx=3)
        ttk.Label(materials,text='Whole-texture multiplier (0–2). Includes baked lettering.\nAlpha preserved; this is not a semantic base-paint tool.',wraplength=330).pack(anchor='w',pady=5)
        self.tint_button=ttk.Button(materials,text='Apply texture multiplier',command=self.tint);self.tint_button.pack(fill='x')
        ttk.Button(materials,text='Replace with same-size PNG…',command=self.replace_png).pack(fill='x',pady=4)
        row=ttk.Frame(materials);row.pack(fill='x');ttk.Button(row,text='Undo',command=self.undo).pack(side='left',expand=True,fill='x');ttk.Button(row,text='Restore texture',command=lambda:self.restore(self.texture_name.get())).pack(side='left',expand=True,fill='x')
        settings=ttk.Frame(tabs,padding=9);tabs.add(settings,text='Build / Scope')
        ttk.Button(settings,text='Configure build inputs…',command=self.configure).pack(fill='x')
        ttk.Button(settings,text='Open last build folder',command=self.open_build_folder).pack(fill='x',pady=7)
        ttk.Label(settings,text='IMPLEMENTED\nDX/DXT inspection, texture multiplier/PNG replacement, Save, Undo, Restore, validation, stock overrides and existing addon roster build.\n\nFUTURE — not editable in V-SDK3\nGlass damage, masked repaint, Classic MR Style, geometry/Blender bridge, scale/fit, Physics/Audio/Camera Studio.\n\nExisting CLI profiles remain intact. Converted-family-only projects build resource packages, not new CarIDs.',wraplength=320).pack(anchor='w',pady=10)
        bottom=ttk.Frame(self.outer,padding=7);self.outer.add(bottom,weight=1)
        ttk.Label(bottom,text='DIAGNOSTICS / BUILD LOG / PROVENANCE').pack(anchor='w')
        self.log=tk.Text(bottom,height=8,bg='#15191f',fg='#c5ccd6',font=('Consolas',9),wrap='word',relief='flat');self.log.pack(fill='both',expand=True)
        ttk.Label(self.root,textvariable=self.status,padding=(12,7)).pack(fill='x')

    def _load_library(self):
        path=self.workspace/'library.json'
        if path.exists():
            for p in json.loads(path.read_text()):
                try:self.add_library(WorkshopProject(p),save=False)
                except Exception as e:self.log.insert('end',f'Cannot reopen {p}: {e}\n')

    def _sync_controls(self):
        actions={'Save','Validate','Build','Restore all','Open interactive 3D','Reload preview','Apply texture multiplier','Replace with same-size PNG…','Undo','Restore texture','Configure build inputs…','Open last build folder'}
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child,ttk.Button):
                    text=str(child['text']);disabled=self.busy or (text in actions and self.project is None)
                    if self.project and text=='Undo':disabled=disabled or not self.project.data['history']
                    if self.project and text=='Restore texture':disabled=disabled or self.texture_name.get() not in self.project.data['edits']
                    if self.project and text=='Restore all':disabled=disabled or not self.project.data['edits']
                    if self.project and text=='Configure build inputs…':disabled=disabled or self.project.data['kind']=='family'
                    child.state(['disabled'] if disabled else ['!disabled'])
                walk(child)
        walk(self.root)

    def add_library(self,project,save=True):
        key=str(project.root)
        if key not in self.library:
            self.library[key]=project
            kind=project.data['kind'];group='group:'+kind
            if not self.library_tree.exists(group):self.library_tree.insert('', 'end',iid=group,text={'stock':'Stock vehicles','addon':'Imported addons','family':'Converted families'}[kind],open=True)
            self.library_tree.insert(group, 'end',iid=key,text=f"{project.data['identity']}  · {kind}")
        if save:write_json(self.workspace/'library.json',list(self.library))
        return key

    def remove_library(self):
        selected=self.library_tree.selection()
        if not selected or selected[0] not in self.library:self.status.set('Select a vehicle entry to remove.');return
        key=selected[0];self.library_tree.delete(key);self.library.pop(key);write_json(self.workspace/'library.json',list(self.library));self.status.set('Removed library entry; project files retained.')

    def _library_selected(self,event=None):
        if self.busy:return
        rows=self.library_tree.selection()
        if not rows or rows[0] not in self.library:return
        next_project=self.library[rows[0]]
        if self.project and self.project.root!=next_project.root:
            hwnd=self._viewer_window()
            if hwnd:
                import ctypes
                ctypes.windll.user32.PostMessageW(hwnd,0x10,0,0)
            self.process=None;self.last_selection=''
        self.project=next_project;self.name.set(self.project.data['identity']);self.refresh()

    def run(self,label,work,done=None):
        if self.busy:self.status.set('Wait for the current operation to finish.');return
        self.busy=True;self.status.set(label+'…');self.log.insert('end',label+'\n');self.log.see('end')
        self._sync_controls()
        self.library_tree.configure(selectmode='none');self.model_box.configure(state='disabled')
        def worker():
            try:self.messages.put(('done',work(),done,label))
            except Exception as e:
                import traceback
                self.messages.put(('error',str(e),traceback.format_exc(),label))
        threading.Thread(target=worker,daemon=True).start()

    def _poll(self):
        try:
            while True:
                kind,value,callback,label=self.messages.get_nowait()
                if kind=='log':self.log.insert('end',str(value)+'\n');continue
                self.busy=False
                self._sync_controls()
                self.library_tree.configure(selectmode='browse');self.model_box.configure(state='readonly')
                if kind=='error':self.status.set(label+' failed');self.log.insert('end',callback+'\n');messagebox.showerror(label,value,parent=self.root)
                else:
                    self.status.set(label+' — complete')
                    if callback:callback(value)
                    self.log.insert('end',label+' — PASS\n')
                self.log.see('end')
        except queue.Empty:pass
        if self.project:
            selection=self.project.root/'preview/selection.txt'
            if selection.exists():
                text=selection.read_text(encoding='utf-8',errors='replace')
                if text!=self.last_selection:
                    self.last_selection=text;parts=text.splitlines()
                    if len(parts)>=2:
                        try:
                            source_model,draw=parts[1].split(':')[:2]
                            if self.current_info and source_model==self.current_info['model']:
                                self.draws.selection_set(draw);self.draws.see(draw)
                            elif self.current_info:
                                item=self.current_info['source_draws'][source_model][int(draw)]
                                self.inspector.delete('1.0','end');self.inspector.insert('end',source_model+'\n'+json.dumps(item,indent=2))
                        except (IndexError,KeyError,ValueError,tk.TclError):pass
                    if len(parts)>2 and parts[2] in self.texture_box['values']:self.texture_name.set(parts[2]);self.show_texture()
        self.root.after(100,self._poll)

    def open_project(self):
        folder=filedialog.askdirectory(title='Open SDK addon, stock or Workshop project',parent=self.root)
        if not folder:return
        path=Path(folder)
        if (path/'workshop-project.json').exists():self._opened(WorkshopProject(path));return
        self.run('Create non-destructive Workshop copy',lambda:WorkshopProject.create(path,self._new_project()),self._opened)

    def open_family(self):
        path=filedialog.askopenfilename(title='Open converted car.dx / complete.dx',filetypes=[('Master Rallye DX','*.dx')],parent=self.root)
        if path:self.run('Open converted family',lambda:WorkshopProject.create(Path(path).parent,self._new_project(),kind='family'),self._opened)

    def _new_project(self):
        import uuid
        return self.workspace/'projects'/uuid.uuid4().hex[:12]

    def new_stock(self):
        folder=filedialog.askdirectory(title='Choose user-supplied unpacked retail data root',parent=self.root)
        if not folder:return
        dialog=tk.Toplevel(self.root);dialog.title('Qualified stock vehicle');value=tk.StringVar(value='Megane / CarID18')
        ttk.Label(dialog,text='Only source-qualified registry pairs are available.').pack(padx=15,pady=10)
        ttk.Combobox(dialog,textvariable=value,values=['Megane / CarID18','Pajero / CarID1'],state='readonly',width=30).pack(padx=15,pady=5)
        def create():
            family,car_id=('Megane',18) if value.get().startswith('Megane') else ('Pajero',1)
            dialog.destroy();self.run('Create stock copy-on-write project',lambda:WorkshopProject.create(folder,self._new_project(),kind='stock-new',family=family,car_id=car_id),self._opened)
        ttk.Button(dialog,text='Create private project',command=create).pack(padx=15,pady=12)

    def _opened(self,project):
        key=self.add_library(project);self.library_tree.selection_set(key)

    def _render(self,project,variant):
        source={'Race':'car.dx','Frontend':'complete.dx','Wheel':'wheel.dx'}[variant]
        info=project.inspect(source);scene=project.root/'preview/capture.mrpv';stage_vehicle(project.assets/source,scene)
        info['source_draws']={}
        for name in ('car.dx','complete.dx','wheel.dx'):
            path=project.assets/name
            if path.exists():
                model=parse_dx_bytes(path.read_bytes())
                info['source_draws'][name]={d.draw_index:{'id':d.draw_index,'group':d.group_label,'textures':[s.value for s in d.texture_slots],'semantics':MaterialSemantics.from_draw(d).to_dict()} for d in model.physical_draws}
        screenshot=project.root/'preview/latest.bmp'
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        subprocess.run([str(self.viewer),'--scene',str(scene),'--source',str(project.assets/source),'--model',variant.lower(),'--zoom','.68','--workshop','--capture',str(screenshot)],check=True,startupinfo=si,timeout=60)
        return info,bmp_png(screenshot)

    def refresh(self):
        if not self.project:return
        project=self.project;variant=self.variant.get()
        self.run('Inspect and render real MR resources',lambda:self._render(project,variant),self._rendered)

    def _rendered(self,result):
        info,png=result
        selected=self.draws.selection() if self.current_info and self.current_info['identity']==info['identity'] and self.current_info['model']==info['model'] else ()
        self.current_info=info
        self.context.set(f"{info['kind']} · CarID {info['car_id'] if info['car_id'] is not None else 'unassigned'} · {info['model']} · {info['vertices']} vertices · {len(info['draws'])} native draws")
        self.draws.delete(*self.draws.get_children())
        for d in info['draws']:self.draws.insert('', 'end',iid=str(d['id']),values=(d['id'],d['group'] or ' / '.join(str(v) for v in d['textures'])))
        names=[t['name'] for t in info['textures']];self.texture_box['values']=names
        if self.texture_name.get() not in names:self.texture_name.set(names[0] if names else '')
        image=tk.PhotoImage(data=png);factor=max(1,(image.width()+max(500,self.capture.winfo_width())-1)//max(500,self.capture.winfo_width()),(image.height()+max(350,self.capture.winfo_height())-1)//max(350,self.capture.winfo_height()));image=image.subsample(factor)
        self.photos=[image];self.capture.configure(image=image,text='');self.show_texture()
        self.inspector.delete('1.0','end');self.inspector.insert('end',f"Source: {info['source']}\n{info['preview']}\nEdits: {len(self.project.data['edits'])}\nNative alpha/flags are shown without inventing material classifications.")
        if selected and self.draws.exists(selected[0]):self.draws.selection_set(selected[0])
        self.log.insert('end',f"Provenance: {info['source']}\nWorkshop: {self.project.root}\n")
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd,0x800c,{'Race':1,'Frontend':2,'Wheel':3}[self.variant.get()],0)
        self._viewer_message(ord('R'))
        self._sync_controls()

    def show_texture(self):
        if not self.project or not self.texture_name.get():return
        try:
            texture=self.project.texture(self.texture_name.get());image=tk.PhotoImage(data=encode_png(texture));image=image.subsample(max(1,(image.width()+279)//280,(image.height()+109)//110));self.texture_photo=image;self.texture_picture.configure(image=image,text='')
            self.texture_details.set(f'{texture.width} × {texture.height} · FEED BGRA · {len(texture.bgra):,} bytes\n'+('Edited override' if self.texture_name.get() in self.project.data['edits'] else 'Original input'))
        except Exception as e:self.texture_picture.configure(image='',text=str(e))
        self._sync_controls()

    def _draw_selected(self,event=None):
        selected=self.draws.selection()
        if not selected or not self.current_info:return
        d=next((d for d in self.current_info['draws'] if d['id']==int(selected[0])),None)
        if not d:return
        self.inspector.delete('1.0','end');self.inspector.insert('end',json.dumps(d,indent=2)+'\nNative resource fields. D3D9 preview is approximate.')
        names=self.texture_box['values']
        for name in d['textures']:
            candidate=str(name)+'.dxt'
            if candidate in names:self.texture_name.set(candidate);self.show_texture();break
        self._viewer_message(int(selected[0]),selection=True)

    def tint(self):
        if self.project and self.texture_name.get():
            try:rgb=[float(v.get()) for v in self.gain]
            except ValueError:messagebox.showerror('RGB multiplier','Enter three numbers in0..2.');return
            project=self.project;name=self.texture_name.get();self.run('Apply reversible texture override',lambda:project.tint(name,rgb),lambda _:self.refresh())

    def replace_png(self):
        if not self.project or not self.texture_name.get():return
        path=filedialog.askopenfilename(filetypes=[('PNG image','*.png')],parent=self.root)
        if path:
            project=self.project;name=self.texture_name.get();self.run('Replace texture',lambda:project.replace_png(name,path),lambda _:self.refresh())

    def save(self):
        if self.project:self.project.save();self.status.set('Project saved; original source untouched.')

    def undo(self):
        if self.project:self.run('Undo texture edit',self.project.undo,lambda _:self.refresh())

    def restore(self,name):
        if self.project:self.run('Restore original texture state',lambda:self.project.restore(name),lambda _:self.refresh())

    def validate(self):
        if self.project:self.run('Validate through SDK',self.project.validate,lambda r:self.log.insert('end',json.dumps(r,indent=2,default=str)+'\n'))

    def configure(self):
        if not self.project:return
        dialog=tk.Toplevel(self.root);dialog.title('Build inputs — existing qualified SDK paths');fields={}
        labels={'roster_candidate':'Existing roster candidate folder','retail_sma':'Original retail Data.sma','retail_root':'Matching unpacked retail data root'}
        for key,label in labels.items():
            row=ttk.Frame(dialog,padding=7);row.pack(fill='x');ttk.Label(row,text=label,width=32).pack(side='left');v=tk.StringVar(value=self.project.data['build_settings'].get(key,''));fields[key]=v;ttk.Entry(row,textvariable=v,width=65).pack(side='left')
            def browse(k=key,var=v):
                value=filedialog.askopenfilename(parent=dialog) if k=='retail_sma' else filedialog.askdirectory(parent=dialog)
                if value:var.set(value)
            ttk.Button(row,text='Browse…',command=browse).pack(side='left')
        def save():
            try:self.project.configure_build({k:v.get() for k,v in fields.items()})
            except Exception as e:messagebox.showerror('Build inputs',str(e),parent=dialog);return
            dialog.destroy();self.status.set('Build settings saved. Original runtime files remain unchanged.')
        ttk.Button(dialog,text='Save build inputs',command=save).pack(pady=10)

    def build(self):
        if not self.project:return
        import uuid
        # MSVC compiler discovery fails in deeply nested project build paths.
        # Keep the proven launcher API intact and use a short owned SDK job root.
        project=self.project;output=self.sdk_root/'.research-output/workshop-builds'/uuid.uuid4().hex[:12]
        self.run('Build isolated candidate',lambda:project.build(output,sdk_root=self.sdk_root,log=lambda s:self.messages.put(('log',s,None,''))),lambda r:self.log.insert('end',f'Build saved: {output}\n'+json.dumps(r,indent=2,default=str)+'\n'))

    def open_build_folder(self):
        if self.project and self.project.data.get('last_build'):
            import os
            folder=Path(self.project.data['last_build'])
            if folder.is_dir():os.startfile(str(folder))
            else:self.status.set('The last build folder no longer exists.')
        else:self.status.set('Build a project first.')

    def _viewer_window(self):
        if not self.process or self.process.poll() is not None:return None
        import ctypes
        from ctypes import wintypes
        windows=[];user=ctypes.windll.user32
        callback=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        def enum(hwnd,lparam):
            pid=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if pid.value==self.process.pid and user.IsWindowVisible(hwnd):windows.append(hwnd)
            return True
        user.EnumWindows(callback(enum),0);return windows[0] if windows else None

    def _viewer_message(self,key,selection=False):
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd,0x800b if selection else 0x100,key,0)

    def open_viewer(self):
        if not self.project:return
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.SetForegroundWindow(hwnd);return
        project=self.project;model={'Race':'car.dx','Frontend':'complete.dx','Wheel':'wheel.dx'}[self.variant.get()]
        capture_scene=project.root/'preview/capture.mrpv';scene=project.root/'preview/interactive.mrpv'
        if not capture_scene.exists():self.status.set('Wait for the GPU preview to finish.');return
        import shutil
        shutil.copyfile(capture_scene,scene)
        self.process=subprocess.Popen([str(self.viewer),'--scene',str(scene),'--source',str(project.assets/model),'--python',sys.executable,'--exporter',str(self.sdk_root/'tools/preview_vehicle.py'),'--model',self.variant.get().lower(),'--zoom','.68','--workshop','--vehicle-id',str(project.data['car_id'] if project.data['car_id'] is not None else -1),'--provenance',project.data['source'],'--selection-file',str(project.root/'preview/selection.txt'),'--bookmark-file',str(project.root/'preview/bookmarks')])
        self.status.set('Interactive native Previewer opened. F1 shows all controls.')

    def close(self):
        if self.busy:self.status.set('Operation still running. Close after it finishes.');return
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd,0x10,0,0)
        self.root.destroy()

def main():
    import argparse
    root_path=Path(__file__).resolve().parents[3]
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,default=root_path/'.research-output/rally-workshop-workspace');p.add_argument('--viewer',type=Path,default=root_path/'.research-output/rally-workshop/bin/mr-vehicle-previewer.exe');p.add_argument('--project',type=Path);a=p.parse_args()
    if not a.viewer.is_file():raise RuntimeError('Build Rally Workshop first: python tools/build_rally_workshop.py')
    root=tk.Tk();app=WorkshopApp(root,a.workspace,root_path,a.viewer)
    if a.project:app._opened(WorkshopProject(a.project))
    elif app.library:root.after(250,lambda:app.library_tree.selection_set(next(iter(app.library))))
    root.mainloop()
