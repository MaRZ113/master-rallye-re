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
from .texture_view import TextureView
from .branding import apply_icon,taskbar_identity
from .appearance_ui import AppearancePanels
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

class WorkshopApp(AppearancePanels):
    def __init__(self, root, workspace, sdk_root, viewer):
        apply_icon(root);self.root=root;self.workspace=Path(workspace).resolve();self.workspace.mkdir(parents=True,exist_ok=True)
        self.sdk_root=Path(sdk_root).resolve();self.viewer=Path(viewer).resolve();self.messages=queue.Queue();self.busy=False
        self.project=None;self.current_info=None;self.process=None;self.last_selection='';self.photos=[];self.library={}
        self.assembled=tk.BooleanVar(value=True);self.texture_popup=None
        self.variant=tk.StringVar(value='Frontend');self.texture_name=tk.StringVar();self.texture_details=tk.StringVar();self.gain=[tk.StringVar(value='1.0') for _ in range(3)]
        self.status=tk.StringVar(value='Open an SDK project or create a qualified stock project to begin.')
        self.name=tk.StringVar(value='RALLY WORKSHOP');self.context=tk.StringVar(value='No vehicle selected')
        self._style();self._layout();self._load_library();self.root.after(100,self._poll)
        self._sync_controls()
        self.root.bind('<F1>',lambda e:self.show_help())
        layout=self.workspace/'window-layout.json'
        if layout.exists():
            try:
                saved=json.loads(layout.read_text());self.root.geometry(saved['geometry'])
                def restore_splits():
                    for i,v in enumerate(saved.get('horizontal',[])):self.main_split.sashpos(i,v)
                    for i,v in enumerate(saved.get('vertical',[])):self.outer.sashpos(i,v)
                self.root.after(300,restore_splits)
            except (ValueError,KeyError,tk.TclError):pass
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
        for label,command in [('Open project',self.open_project),('Open DX family',self.open_family),('New stock',self.new_stock),('Save',self.save),('Validate',self.validate),('Build',self.build),('Restore all',lambda:self.restore(None)),('Help',self.show_help)]:
            button=ttk.Button(top,text=label,command=command,style='Accent.TButton' if label=='Build' else 'TButton');button.pack(side='left',padx=3);self.buttons[label]=button
        self.outer=ttk.Panedwindow(self.root,orient='vertical');self.outer.pack(fill='both',expand=True,padx=10)
        main=ttk.Panedwindow(self.outer,orient='horizontal');self.main_split=main;self.outer.add(main,weight=5)
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
        ttk.Button(controls,text='Outside',command=lambda:self._viewer_message(ord('1'))).pack(side='left')
        ttk.Button(controls,text='Inside',command=lambda:self._viewer_message(ord('2'))).pack(side='left')
        ttk.Checkbutton(center,text='Show assembled wheels (Race only, preview rest pose)',variable=self.assembled,command=self.refresh).pack(anchor='w')
        ttk.Label(center,text='Last compiled GPU capture · navigation runs in the managed native 3D window').pack(anchor='w',pady=(1,5))
        self.capture=tk.Label(center,bg='#1a1e24',fg='#b6bdc7',text='MANAGED D3D9 VIEWPORT\n\nOpen a project to render its actual resources.\nInteractive navigation runs in the existing native Previewer window.\n\nThis panel shows the latest GPU capture, not a simulated viewport.',font=('Segoe UI',12),justify='center')
        self.capture.pack(fill='both',expand=True)
        ttk.Label(center,text='3D: LMB orbit / geometric pick · MMB pan · wheel zoom · F focus · Home reset\nF3 actual-data HUD · Ctrl1–6 save / Shift1–6 recall view · R reload\nD3D9 approximation: world lighting, ordering and native damage still require game tests.',wraplength=680).pack(anchor='w',pady=9)
        right=ttk.Frame(main,padding=8);main.add(right,weight=2)
        tabs=ttk.Notebook(right);tabs.pack(fill='both',expand=True)
        materials=ttk.Frame(tabs,padding=6);tabs.add(materials,text='Inspect / Texture')
        self.draws=ttk.Treeview(materials,columns=('id','group'),show='tree headings',height=8,selectmode='browse');self.draws.heading('id',text='Draw');self.draws.heading('group',text='Group / native material')
        self.draws.column('#0',width=160);self.draws.column('id',width=45,stretch=False);self.draws.column('group',width=230);self.draws.pack(fill='both',expand=True);self.draws.bind('<<TreeviewSelect>>',self._draw_selected)
        self.inspector=tk.Text(materials,height=7,width=42,bg='#191d23',fg='#d5dae0',wrap='word',font=('Consolas',9),relief='flat');self.inspector.pack(fill='x',pady=6)
        self.surface_status=tk.StringVar(value='Select a native draw to inspect edit capabilities.')
        ttk.Label(materials,textvariable=self.surface_status,wraplength=330).pack(fill='x',pady=4)
        sr=ttk.Frame(materials);sr.pack(fill='x');self.surface_gain=[tk.StringVar(value='1') for _ in range(3)]
        for label,var in zip(('R','G','B'),self.surface_gain):ttk.Label(sr,text=label).pack(side='left');ttk.Entry(sr,textvariable=var,width=5).pack(side='left')
        self.surface_button=ttk.Button(materials,text='Apply selected-surface RGB',command=self.edit_surface);self.surface_button.pack(fill='x')
        ttk.Button(materials,text='Assign Existing Texture…',command=self.assign_texture).pack(fill='x')
        ttk.Button(materials,text='Material help',command=lambda:self.show_help('materials')).pack(fill='x')
        self.reflection_off=tk.BooleanVar();self.reflection_button=ttk.Checkbutton(materials,text='Disable existing environment pass (selected draw)',variable=self.reflection_off,command=self.edit_reflection);self.reflection_button.pack(fill='x')
        strength_row=ttk.Frame(materials);strength_row.pack(fill='x');self.reflection_strength=tk.DoubleVar(value=1.)
        ttk.Label(strength_row,text='Reflection weight × source').pack(side='left');ttk.Spinbox(strength_row,from_=0,to=2,increment=.1,width=5,textvariable=self.reflection_strength).pack(side='left')
        self.strength_button=ttk.Button(strength_row,text='Apply weight',command=self.edit_reflection_strength);self.strength_button.pack(side='left')
        ttk.Label(materials,text='Opaque environment only. Preserves source mask; saturated weights cannot brighten further. Blended/cutout alpha is read-only.',wraplength=350).pack(fill='x')
        row=ttk.Frame(materials);row.pack(fill='x');ttk.Button(row,text='Restore surface',command=self.restore_surface).pack(side='left',fill='x',expand=True);ttk.Button(row,text='Redo',command=self.redo).pack(side='left',fill='x',expand=True)
        self.original_capture=tk.BooleanVar();ttk.Checkbutton(materials,text='Before / original GPU view',variable=self.original_capture,command=self.refresh).pack(anchor='w')
        texture_tab=ttk.Frame(tabs,padding=6);tabs.add(texture_tab,text='Texture Studio')
        self.texture_box=ttk.Combobox(texture_tab,textvariable=self.texture_name,state='readonly');self.texture_box.pack(fill='x');self.texture_box.bind('<<ComboboxSelected>>',lambda e:self.show_texture())
        ttk.Label(texture_tab,textvariable=self.texture_details,wraplength=330).pack(anchor='w',pady=3)
        self.usage_tree=ttk.Treeview(texture_tab,columns=('model','draw','slot'),show='headings',height=4)
        for field in ('model','draw','slot'):self.usage_tree.heading(field,text=field);self.usage_tree.column(field,width=80)
        self.usage_tree.pack(fill='x');usage_scroll=ttk.Scrollbar(texture_tab,orient='vertical',command=self.usage_tree.yview);self.usage_tree.configure(yscrollcommand=usage_scroll.set);usage_scroll.pack(side='right',fill='y')
        self.texture_view=TextureView(texture_tab,self._texture_input);self.texture_view.pack(fill='both',expand=True)
        ttk.Button(texture_tab,text='Enlarge / detach texture viewer',command=self.detach_texture).pack(fill='x')
        ttk.Button(texture_tab,text='Texture help',command=lambda:self.show_help('textures')).pack(fill='x')
        row=ttk.Frame(texture_tab);row.pack(fill='x')
        for label,var in zip(('R','G','B'),self.gain):ttk.Label(row,text=label).pack(side='left');ttk.Entry(row,textvariable=var,width=5).pack(side='left',padx=3)
        ttk.Label(texture_tab,text='Whole-texture multiplier (0–2). Includes baked lettering.\nAlpha preserved; this is not a semantic base-paint tool.',wraplength=330).pack(anchor='w',pady=5)
        self.tint_button=ttk.Button(texture_tab,text='Apply texture multiplier',command=self.tint);self.tint_button.pack(fill='x')
        ttk.Button(texture_tab,text='Replace with same-size PNG…',command=self.replace_png).pack(fill='x',pady=4)
        row=ttk.Frame(texture_tab);row.pack(fill='x');ttk.Button(row,text='Undo',command=self.undo).pack(side='left',expand=True,fill='x');ttk.Button(row,text='Restore texture',command=lambda:self.restore(self.texture_name.get())).pack(side='left',expand=True,fill='x')
        fit_tab=ttk.Frame(tabs,padding=8);tabs.add(fit_tab,text='Wheel Fitment')
        self._fit_layout(fit_tab)
        self.appearance_layout(tabs)
        settings=ttk.Frame(tabs,padding=9);tabs.add(settings,text='Build / Scope')
        ttk.Button(settings,text='Configure build inputs…',command=self.configure).pack(fill='x')
        ttk.Button(settings,text='Open last build folder',command=self.open_build_folder).pack(fill='x',pady=7)
        ttk.Label(settings,text='IMPLEMENTED\nNative model/draw/material inspection, selected-surface RGB and existing environment pass controls, texture impact warnings and PNG replacement, filtered RGBA/Alpha image views, preview wheel fitting, qualified masked paint, appearance snapshots, local stock references, existing stock crew fitting, Save, Undo/Redo/Restore, validation and isolated stock/addon builds.\n\nFUTURE — not editable in this milestone\nGeometry/Blender bridge, scale/fit, Physics/Audio/Camera Studio.\n\nExisting CLI profiles remain intact. Converted-family-only projects build resource packages, not new CarIDs.',wraplength=320).pack(anchor='w',pady=10)
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
        actions={'Save','Validate','Build','Restore all','Open interactive 3D','Reload preview','Apply texture multiplier','Replace with same-size PNG…','Undo','Restore texture','Configure build inputs…','Open last build folder','Assign Existing Texture…'}
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child,ttk.Button):
                    text=str(child['text']);disabled=self.busy or ((text in actions or text in {'Apply selected-surface RGB','Restore surface','Redo'}) and self.project is None)
                    if self.project and text=='Undo':disabled=disabled or not self.project.data['history']
                    if self.project and text=='Restore texture':disabled=disabled or self.texture_name.get() not in self.project.data['edits']
                    if self.project and text=='Restore all':disabled=disabled or not (self.project.data['edits'] or any(self.project.data.get('surfaces',{}).values()))
                    if self.project and text=='Redo':disabled=disabled or not self.project.data.get('redo')
                    if self.project and text=='Configure build inputs…':disabled=disabled or self.project.data['kind']=='family'
                    child.state(['disabled'] if disabled else ['!disabled'])
                walk(child)
        walk(self.root)
        if hasattr(self,'surface_button'):
            selection=self._surface_selection() if self.project else None
            caps={}
            if selection:
                from master_rallye.surface_authoring import surface_capabilities
                caps=surface_capabilities((self.project.baseline/selection[0]).read_bytes(),selection[1])
            self.surface_button.state(['!disabled'] if not self.busy and caps.get('diffuse_rgb_editable') else ['disabled'])
            self.reflection_button.state(['!disabled'] if not self.busy and caps.get('reflection_disable_editable') else ['disabled'])
            self.strength_button.state(['!disabled'] if not self.busy and caps.get('reflection_strength_editable') else ['disabled'])

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
            self.current_info=None;self.draws.delete(*self.draws.get_children());self.texture_name.set('')
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
                            if self.current_info and source_model in self.current_info['source_draws']:
                                node=self._draw_node(source_model,int(draw));self.draws.selection_set(node);self.draws.see(node)
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
        dialog=tk.Toplevel(self.root);apply_icon(dialog);dialog.title('Qualified stock vehicle');value=tk.StringVar(value='Megane / CarID18')
        ttk.Label(dialog,text='Only source-qualified registry pairs are available.').pack(padx=15,pady=10)
        ttk.Combobox(dialog,textvariable=value,values=['Megane / CarID18','Pajero / CarID1'],state='readonly',width=30).pack(padx=15,pady=5)
        def create():
            family,car_id=('Megane',18) if value.get().startswith('Megane') else ('Pajero',1)
            dialog.destroy();self.run('Create stock copy-on-write project',lambda:WorkshopProject.create(folder,self._new_project(),kind='stock-new',family=family,car_id=car_id),self._opened)
        ttk.Button(dialog,text='Create private project',command=create).pack(padx=15,pady=12)

    def _opened(self,project):
        key=self.add_library(project);self.library_tree.selection_set(key)

    def _render(self,project,variant,*,assembled=True,original=False):
        source={'Race':'car.dx','Frontend':'complete.dx','Wheel':'wheel.dx'}[variant]
        info=project.inspect(source);scene=project.root/'preview/capture.mrpv';render_source=project.assets/source
        if original:render_source=project.baseline/source
        stage=stage_vehicle(render_source,scene,profile=project.preview_profile_path());info['wheel_outside_camera']=stage['wheel_outside_camera'];info['wheel_profile']=project.preview_profile()
        info['source_draws']={}
        for name in ('car.dx','complete.dx','wheel.dx'):
            path=project.assets/name
            if path.exists():
                model=parse_dx_bytes(path.read_bytes())
                info['source_draws'][name]={d.draw_index:{'id':d.draw_index,'group':d.group_label,'textures':[s.value for s in d.texture_slots],'semantics':MaterialSemantics.from_draw(d).to_dict()} for d in model.physical_draws}
        screenshot=project.root/'preview/latest.bmp'
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        subprocess.run([str(self.viewer),'--scene',str(scene),'--source',str(render_source),'--model',variant.lower(),'--zoom','.68','--workshop','--capture',str(screenshot)]+([] if assembled else ['--raw-race']),check=True,startupinfo=si,timeout=60)
        return info,bmp_png(screenshot)

    def refresh(self):
        if not self.project:return
        project=self.project;variant=self.variant.get();assembled=self.assembled.get();original=self.original_capture.get()
        self.run('Inspect and render real MR resources',lambda:self._render(project,variant,assembled=assembled,original=original),self._rendered)

    def _rendered(self,result):
        info,png=result
        selected=self.draws.selection() if self.current_info and self.current_info['identity']==info['identity'] and self.current_info['model']==info['model'] else ()
        self.current_info=info
        self.context.set(('Assembled Race · ' if self.variant.get()=='Race' and self.assembled.get() else 'Raw Race · ' if self.variant.get()=='Race' else '')+f"{info['kind']} · CarID {info['car_id'] if info['car_id'] is not None else 'unassigned'} · {info['model']} · {info['vertices']} vertices · {len(info['draws'])} native draws")
        self.draws.delete(*self.draws.get_children())
        for model,draws in info['source_draws'].items():
            parent='model:'+model;self.draws.insert('', 'end',iid=parent,text={'car.dx':'Race / car.dx','complete.dx':'Frontend / complete.dx','wheel.dx':'Wheel / wheel.dx'}[model],open=model==info['model'])
            for d in draws.values():
                group=parent+':group:'+str(d['group'] or 'Unclassified native draws')
                if not self.draws.exists(group):self.draws.insert(parent,'end',iid=group,text=d['group'] or 'Unclassified native draws',open=True)
                node=self._draw_node(model,d['id']);self.draws.insert(group,'end',iid=node,text='Physical draw',values=(d['id'],d['group'] or ' / '.join(str(v) for v in d['textures'])),open=False)
                mat=f'material:{model}:{d["id"]}';self.draws.insert(node,'end',iid=mat,text='Native material',values=('',str(d['semantics'].get('classification','raw DX states'))))
                for slot,name in enumerate(d['textures']):self.draws.insert(mat,'end',iid=f'texture:{model}:{d["id"]}:{slot}',text=f'Slot {slot}',values=('',str(name)))
        names=[t['name'] for t in info['textures']];self.texture_box['values']=names
        if self.texture_name.get() not in names:self.texture_name.set(names[0] if names else '')
        image=tk.PhotoImage(data=png);factor=max(1,(image.width()+max(500,self.capture.winfo_width())-1)//max(500,self.capture.winfo_width()),(image.height()+max(350,self.capture.winfo_height())-1)//max(350,self.capture.winfo_height()));image=image.subsample(factor)
        self.photos=[image];self.capture.configure(image=image,text='');self.show_texture()
        self._fit_loaded();self.appearance_loaded()
        if self.variant.get()=='Wheel' and abs(info['wheel_outside_camera']['mean_axial_vote'])<=.2:self.log.insert('end','Wheel outside direction is ambiguous: generic camera retained; inspect both sides.\n')
        self._inspect(f"Source: {info['source']}\n{info['preview']}\nEdits: {len(self.project.data['edits'])}\nNative alpha/flags are shown without inventing material classifications.")
        if selected and self.draws.exists(selected[0]):self.draws.selection_set(selected[0])
        self.log.insert('end',f"Provenance: {info['source']}\nWorkshop: {self.project.root}\n")
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd,0x800c,{'Race':1,'Frontend':2,'Wheel':3}[self.variant.get()],0)
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd,0x800d,int(self.assembled.get()),0)
        if not self.original_capture.get():self._viewer_message(ord('R'))
        self._sync_controls()

    def _fit_layout(self,parent):
        ttk.Label(parent,text='PREVIEW ONLY — never changes game physics, wheel anchors or DX.\nOffsets are absolute rest-pose transforms in model units.',wraplength=320).pack(anchor='w')
        self.fit_status=tk.StringVar();ttk.Label(parent,textvariable=self.fit_status,wraplength=320).pack(anchor='w',pady=7)
        self.fit_index=tk.StringVar(value='0');box=ttk.Combobox(parent,textvariable=self.fit_index,values=['0','1','2','3'],state='readonly',width=35);self.fit_box=box;box.pack(anchor='w');box.bind('<<ComboboxSelected>>',lambda _:self._fit_loaded())
        self.fit_values={}
        for key in ('X','Y','Z','Yaw radians','Scale X','Scale Y','Scale Z'):
            row=ttk.Frame(parent);row.pack(fill='x',pady=3);ttk.Label(row,text=key,width=15).pack(side='left');v=tk.StringVar();self.fit_values[key]=v;ttk.Entry(row,textvariable=v,width=14).pack(side='left')
        for label,action in [('Save preview wheel pose',self._fit_save),('Reset source profile',self._fit_reset),('Load qualified profile…',self._fit_import),('Create explicit manual preview',self._fit_manual)]:ttk.Button(parent,text=label,command=action).pack(fill='x',pady=5)
        ttk.Label(parent,text='Source indices are preserved. Preview labels use +Z front / +X left; signed XYZ and profile provenance remain authoritative. No positions are guessed.',wraplength=320).pack(anchor='w')

    def _fit_loaded(self):
        if not self.project:return
        config=self.project.preview_profile();rows=config.get('race_wheel_instances',[]);self.fit_status.set(config.get('provenance','')+'\n'+str(len(rows))+' qualified/manual instances')
        if len(rows)==4:
            values=[]
            for i,row in enumerate(rows):
                x,_,z=row['translation'];role=('Front' if z>0 else 'Rear')+'-'+('left (+X)' if x>0 else 'right (−X)') if abs(x)>.001 and abs(z)>.001 else 'Unassigned manual pose'
                values.append(f'{i} · {role}')
            index=int(self.fit_index.get().split(' · ')[0]);self.fit_box.configure(values=values);self.fit_index.set(values[index])
            item=rows[index];values=[*item['translation'],item['rotation_y'],*item.get('scale',[1,1,1])]
            for var,value in zip(self.fit_values.values(),values):var.set(f'{value:.7g}')
        else:
            for var in self.fit_values.values():var.set('')

    def _fit_save(self):
        if not self.project:return
        try:
            config=json.loads(json.dumps(self.project.preview_profile()));rows=config.get('race_wheel_instances',[])
            if len(rows)!=4:raise ValueError('Load qualified positions or explicitly create a manual preview first')
            values=[float(v.get()) for v in self.fit_values.values()];rows[int(self.fit_index.get().split(' · ')[0])]={'translation':values[:3],'rotation_y':values[3],'scale':values[4:]}
            config['provenance']='User preview adjustment; source: '+config['provenance'];self.project.save_preview_profile(config);self.refresh()
        except Exception as e:messagebox.showerror('Preview fitment',str(e),parent=self.root)

    def _fit_reset(self):
        if self.project:self.project.data.pop('preview_only',None);self.project.save();self.refresh()

    def _fit_import(self):
        if not self.project:return
        path=filedialog.askopenfilename(title='Source-qualified preview profile',filetypes=[('JSON','*.json')],parent=self.root)
        if path:
            try:self.project.save_preview_profile(json.loads(Path(path).read_text()));self.refresh()
            except Exception as e:messagebox.showerror('Preview profile',str(e),parent=self.root)

    def _fit_manual(self):
        if self.project and messagebox.askyesno('Manual preview only','No positions will be guessed. Create four overlapping identity transforms for explicit manual editing? This does not change gameplay.',parent=self.root):
            self.project.save_preview_profile({'provenance':'Explicit user manual preview, unqualified rest pose','race_wheel_instances':[{'translation':[0,0,0],'rotation_y':0,'scale':[1,1,1]} for _ in range(4)]});self.refresh()

    def _texture_input(self,original=False):
        if not self.project or not self.texture_name.get():return None
        if original:
            from master_rallye.dxt import parse_dxt_bytes
            return parse_dxt_bytes((self.project.baseline/self.texture_name.get()).read_bytes())
        return self.project.texture(self.texture_name.get())

    def detach_texture(self):
        if self.texture_popup and self.texture_popup.winfo_exists():self.texture_popup.lift();return
        win=tk.Toplevel(self.root);apply_icon(win);win.title('Texture Studio — RGBA / alpha / Original comparison');win.geometry('1000x760');win.minsize(500,350);self.texture_popup=win
        path=self.workspace/'texture-window.json'
        if path.exists():
            try:win.geometry(json.loads(path.read_text())['geometry'])
            except (ValueError,KeyError,tk.TclError):pass
        view=TextureView(win,self._texture_input);view.pack(fill='both',expand=True);self.detached_view=view;view.load()
        def close():write_json(path,{'geometry':win.geometry()});win.destroy()
        win.protocol('WM_DELETE_WINDOW',close)

    def show_texture(self):
        if not self.project or not self.texture_name.get():return
        try:
            texture=self.project.texture(self.texture_name.get());self.texture_view.load()
            if self.texture_popup and self.texture_popup.winfo_exists():self.detached_view.load()
            usage=self.project.texture_usage(self.texture_name.get())
            self.usage_tree.delete(*self.usage_tree.get_children())
            for u in usage:self.usage_tree.insert('', 'end',values=(u['model'],u['draw'],u['slot']))
            self.texture_details.set(f'{len(usage)} draw/slot references · {texture.width} × {texture.height} · FEED BGRA · {len(texture.bgra):,} bytes\n'+('Edited override' if self.texture_name.get() in self.project.data['edits'] else 'Original input'))
        except Exception as e:self.texture_details.set(str(e))
        self._sync_controls()

    @staticmethod
    def _draw_node(model,index):return f'draw:{model}:{index}'

    def _surface_selection(self):
        selected=self.draws.selection()
        if not selected or not self.current_info:return None
        parts=selected[0].split(':')
        if len(parts)<3 or parts[0] not in ('draw','material','texture'):return None
        model=parts[1];index=int(parts[2]);return model,index

    def _inspect(self,text):
        self.inspector.configure(state='normal');self.inspector.delete('1.0','end');self.inspector.insert('end',text);self.inspector.configure(state='disabled')

    def _draw_selected(self,event=None):
        selected=self._surface_selection()
        if selected is None:return
        model,index=selected;d=self.current_info['source_draws'][model][index]
        from master_rallye.surface_authoring import surface_capabilities
        caps=surface_capabilities((self.project.baseline/model).read_bytes(),index)
        self.surface_status.set(caps['reason']+(' · Shared source: all assembled wheel instances' if model=='wheel.dx' else '')+'\nRGB preserves alpha, UVs and topology. Existing texture assignment is a separate qualified slot operation, not semantic paint.')
        self.surface_button.state(['!disabled'] if caps['diffuse_rgb_editable'] and not self.busy else ['disabled']);self.reflection_button.state(['!disabled'] if caps['reflection_disable_editable'] and not self.busy else ['disabled'])
        recipe=self.project.data.get('surfaces',{}).get(model,{}).get(str(index),{})
        for var,value in zip(self.surface_gain,recipe.get('rgb',[1,1,1])):var.set(str(value))
        self.reflection_off.set(recipe.get('disable_reflection',False))
        self.reflection_strength.set(recipe.get('reflection_strength',1.))
        self.strength_button.state(['!disabled'] if caps.get('reflection_strength_editable') and not self.busy else ['disabled'])
        self._inspect(model+'\n'+json.dumps({**d,'authoring':caps},indent=2)+'\nNative fields; D3D9 rendering is approximate.')
        for name in d['textures']:
            candidate=str(name)+'.dxt'
            if candidate in self.texture_box['values']:self.texture_name.set(candidate);self.show_texture();break
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd,0x800e,({'car.dx':1,'complete.dx':2,'wheel.dx':3}[model]<<16)|index,0)

    def edit_surface(self):
        selection=self._surface_selection()
        if not selection:return
        try:rgb=[float(v.get()) for v in self.surface_gain]
        except ValueError:messagebox.showerror('Surface RGB','Enter finite RGB values in 0..2.');return
        model,index=selection;self.original_capture.set(False)
        self.run('Apply selected-surface vertex RGB',lambda:self.project.edit_surface(model,index,rgb=rgb),lambda _:self.refresh())

    def show_help(self,topic=None):
        from .help_view import HelpWindow
        HelpWindow(self.root,self.sdk_root/'docs/sdk/help',topic=topic)

    def assign_texture(self):
        selection=self._surface_selection()
        if not self.project or not selection:return
        model,index=selection
        from master_rallye.texture_binding import binding_compatibility
        native=parse_dx_bytes((self.project.assets/model).read_bytes());draw=native.physical_draws[index]
        selected=self.draws.selection()[0].split(':');slot=int(selected[3]) if selected[0]=='texture' else 0
        win=tk.Toplevel(self.root);apply_icon(win);win.title('Assign Existing Texture — native slot');win.geometry('1100x760');win.minsize(850,600)
        ttk.Label(win,text=f'{model} / draw {index} / slot {slot} / current: {draw.texture_slots[slot].value}',wraplength=1000).pack(anchor='w',padx=10,pady=8)
        ttk.Label(win,text='Owned textures only. Names and resolution may differ; UVs and pixels stay unchanged. Compatibility follows the native material state.',wraplength=1000).pack(anchor='w',padx=10)
        filters=ttk.Frame(win);filters.pack(fill='x',padx=10,pady=8)
        search=tk.StringVar();compatible=tk.BooleanVar(value=True);count=tk.StringVar()
        ttk.Label(filters,text='Search').pack(side='left');ttk.Entry(filters,textvariable=search,width=32).pack(side='left',padx=8)
        ttk.Checkbutton(filters,text='Compatible only',variable=compatible).pack(side='left');ttk.Label(filters,textvariable=count).pack(side='right')
        body=ttk.Frame(win);body.pack(fill='both',expand=True,padx=10)
        items=tk.Listbox(body,width=39,exportselection=False);items.pack(side='left',fill='y')
        bar=ttk.Scrollbar(body,command=items.yview);bar.pack(side='left',fill='y');items.configure(yscrollcommand=bar.set)
        candidates=[];shown=[]
        def image_input(original=False):
            return self.project.texture(shown[items.curselection()[0]][0].name) if items.curselection() else None
        preview=TextureView(body,image_input);preview.pack(side='left',fill='both',expand=True)
        details=tk.StringVar();ttk.Label(win,textvariable=details,wraplength=1050).pack(fill='x',padx=10,pady=8)
        for path in sorted(self.project.assets.glob('*.dxt')):
            try:
                info=binding_compatibility(native,index,slot,path.stem,self.project.binding_texture)
                candidates.append((path,True,'; '.join(info['warnings'])))
            except ValueError as e:candidates.append((path,False,str(e)))
        candidates.sort(key=lambda item:(not item[1],item[0].name.casefold()))
        def inspect(event=None):
            if not items.curselection():return
            path,ok,reason=shown[items.curselection()[0]];t=self.project.texture(path.name);alpha=t.bgra[3::4]
            details.set(f'{path.name} | {t.width} × {t.height} | {len(t.bgra):,} BGRA bytes | alpha {min(alpha)}..{max(alpha)}\n'+reason)
            assign.state(['!disabled'] if ok else ['disabled']);preview.load()
        def refresh(*args):
            shown[:]=[c for c in candidates if (c[1] or not compatible.get()) and search.get().casefold() in c[0].name.casefold()]
            items.delete(0,'end')
            for path,ok,reason in shown:items.insert('end',('OK  ' if ok else '—   ')+path.name)
            count.set(f'{sum(c[1] for c in candidates)} compatible / {len(candidates)} total; {len(shown)} shown')
            assign.state(['disabled']);details.set('Select a texture to inspect its compatibility and full preview.')
        def apply():
            if not items.curselection():return
            path,ok,reason=shown[items.curselection()[0]]
            if not ok:return
            project=self.project;win.destroy()
            self.run('Assign owned texture to selected native slot',lambda:project.assign_existing_texture(model,index,slot,path.stem),lambda _:self.refresh())
        assign=ttk.Button(win,text='Assign selected texture',command=apply);assign.pack(pady=8)
        items.bind('<<ListboxSelect>>',inspect);search.trace_add('write',refresh);compatible.trace_add('write',refresh);refresh()

    def edit_reflection_strength(self):
        selection=self._surface_selection()
        if not self.project or not selection:return
        try:gain=self.reflection_strength.get()
        except tk.TclError:return
        self.run('Set opaque native reflection weight',lambda:self.project.edit_surface(*selection,reflection_strength=gain),lambda _:self.refresh())

    def edit_reflection(self):
        selection=self._surface_selection()
        if not selection:return
        model,index=selection;self.original_capture.set(False)
        recipe=dict(self.project.data.get('surfaces',{}).get(model,{}).get(str(index),{}));rgb=recipe.get('rgb');disabled=self.reflection_off.get()
        self.run('Set source-qualified environment pass',lambda:self.project.edit_surface(model,index,rgb=rgb,disable_reflection=disabled),lambda _:self.refresh())

    def restore_surface(self):
        selection=self._surface_selection()
        if selection:self.run('Restore selected surface',lambda:self.project.restore_surface(*selection),lambda _:self.refresh())

    def redo(self):
        if self.project:self.run('Redo edit',self.project.redo,lambda _:self.refresh())

    def _confirm_texture_edit(self):
        usage=self.project.texture_usage(self.texture_name.get());text='Whole-texture edit, including baked logos/decals/glass/atlas regions.\nAffected native draws across all variants:\n'+ '\n'.join(f'{u["model"]} / draw {u["draw"]} / slot {u["slot"]}' for u in usage[:12])+f'\nTotal {len(usage)} references. The complete scrollable list is in Texture Studio. This affects the whole shared image, not the selected surface.'
        return messagebox.askyesno('Shared texture impact — confirm whole-image edit',text,parent=self.root)

    def tint(self):
        if self.project and self.texture_name.get():
            try:rgb=[float(v.get()) for v in self.gain]
            except ValueError:messagebox.showerror('RGB multiplier','Enter three numbers in0..2.');return
            if not self._confirm_texture_edit():return
            project=self.project;name=self.texture_name.get();self.run('Apply reversible texture override',lambda:project.tint(name,rgb),lambda _:self.refresh())

    def replace_png(self):
        if not self.project or not self.texture_name.get():return
        path=filedialog.askopenfilename(filetypes=[('PNG image','*.png')],parent=self.root)
        if path:
            if not self._confirm_texture_edit():return
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
        dialog=tk.Toplevel(self.root);apply_icon(dialog);dialog.title('Build inputs — existing qualified SDK paths');fields={}
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
        self.process=subprocess.Popen([str(self.viewer),'--scene',str(scene),'--source',str(project.assets/model),'--python',sys.executable,'--exporter',str(self.sdk_root/'tools/preview_vehicle.py'),'--model',self.variant.get().lower(),'--zoom','.68','--workshop','--vehicle-id',str(project.data['car_id'] if project.data['car_id'] is not None else -1),'--provenance',project.data['source'],'--selection-file',str(project.root/'preview/selection.txt'),'--bookmark-file',str(project.root/'preview/bookmarks'),'--profile',str(project.preview_profile_path())]+([] if self.assembled.get() else ['--raw-race']))
        self.status.set('Interactive native Previewer opened. F1 shows all controls.')

    def close(self):
        if self.busy:self.status.set('Operation still running. Close after it finishes.');return
        hwnd=self._viewer_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd,0x10,0,0)
        write_json(self.workspace/'window-layout.json',{'geometry':self.root.geometry(),'horizontal':[self.main_split.sashpos(i) for i in range(2)],'vertical':[self.outer.sashpos(0)]})
        self.root.destroy()

def main():
    import argparse
    root_path=Path(__file__).resolve().parents[3]
    default_viewer=root_path/'.research-output/rally-workshop/bin/mr-vehicle-previewer.exe'
    manifest=root_path/'.research-output/rally-workshop/application-build.json'
    if manifest.is_file():default_viewer=Path(json.loads(manifest.read_text()).get('viewer_path',default_viewer))
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,default=root_path/'.research-output/rally-workshop-workspace');p.add_argument('--viewer',type=Path,default=default_viewer);p.add_argument('--project',type=Path);a=p.parse_args()
    if not a.viewer.is_file():raise RuntimeError('Build Rally Workshop first: python tools/build_rally_workshop.py')
    taskbar_identity();root=tk.Tk();app=WorkshopApp(root,a.workspace,root_path,a.viewer)
    if a.project:app._opened(WorkshopProject(a.project))
    elif app.library:root.after(250,lambda:app.library_tree.selection_set(next(iter(app.library))))
    root.mainloop()
