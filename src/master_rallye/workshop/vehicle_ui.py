"""Physics/Camera/Presentation workspace; mutations belong to SDK project service."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from .branding import apply_icon
from .vehicle_authoring import typed

class VehiclePanels:
    def open_vehicle_studios(self):
        if not self.project:return
        if getattr(self,'vehicle_window',None) is not None and self.vehicle_window.winfo_exists():self.vehicle_window.lift();self.vehicle_loaded();return
        w=tk.Toplevel(self.root);self.vehicle_window=w;apply_icon(w);w.title('Rally Workshop — Physics / Camera / Vehicle Details');w.geometry('1020x820')
        bar=ttk.Frame(w,padding=8);bar.pack(fill='x');self.vehicle_header=tk.StringVar();ttk.Label(bar,textvariable=self.vehicle_header).pack(side='left')
        for title,command in [('Save',self.save),('Undo',self.undo),('Redo',self.redo),('Validate',self.validate),('Build',self.build),('Help',lambda:self.show_help('physics-camera'))]:ttk.Button(bar,text=title,command=command).pack(side='right')
        tabs=ttk.Notebook(w);tabs.pack(fill='both',expand=True,padx=8,pady=5);self.vehicle_tabs=tabs
        physics=ttk.Frame(tabs,padding=8);tabs.add(physics,text='Physics Studio');self.physics_tab=physics
        row=ttk.Frame(physics);row.pack(fill='x');self.phys_reference=tk.StringVar();self.phys_reference_box=ttk.Combobox(row,textvariable=self.phys_reference,state='readonly',width=20);self.phys_reference_box.pack(side='left')
        ttk.Button(row,text='Inspect qualified sources',command=self.physics_load).pack(side='left');ttk.Button(row,text='Copy selected reference group',command=self.physics_copy).pack(side='left');ttk.Button(row,text='Reset physics',command=lambda:self.vehicle_action('Restore physics',lambda:self.project.vehicle_reset('physics'))).pack(side='left')
        self.phys_search=tk.StringVar();entry=ttk.Entry(physics,textvariable=self.phys_search);entry.pack(fill='x',pady=5);self.phys_search.trace_add('write',lambda *_:self.physics_fill())
        self.phys_reference_box.bind('<<ComboboxSelected>>',lambda *_:self.physics_load())
        frame=ttk.Frame(physics);frame.pack(fill='both',expand=True)
        self.phys_tree=ttk.Treeview(frame,columns=('original','current','reference','unit'),show='tree headings',selectmode='browse')
        for key,title,width in [('#0','Native field',300),('original','Donor',105),('current','Current',105),('reference','Reference',105),('unit','Units',220)]:self.phys_tree.heading(key,text=title);self.phys_tree.column(key,width=width)
        self.phys_tree.pack(side='left',fill='both',expand=True);scroll=ttk.Scrollbar(frame,command=self.phys_tree.yview);scroll.pack(side='right',fill='y');self.phys_tree.configure(yscrollcommand=scroll.set);self.phys_tree.bind('<<TreeviewSelect>>',self.physics_selected)
        self.phys_note=tk.StringVar(value='Inspect sources to load exact retail member hashes and typed initialization fields. This is not a live physics solver.');ttk.Label(physics,textvariable=self.phys_note,wraplength=960).pack(fill='x',pady=6)
        self.phys_editor=ttk.Frame(physics);self.phys_editor.pack(fill='x');self.phys_fields=[];self.physics_info=None;self.physics_owner=None
        ttk.Button(physics,text='Apply selected typed field',command=self.physics_apply).pack(anchor='e')

        camera=ttk.Frame(tabs,padding=10);tabs.add(camera,text='Gameplay Camera');self.camera_tab=camera
        ttk.Label(camera,text='Experimental native follow extents — separate from Previewer orbit/pan/bookmarks.\nThese are model-bound extents, not direct camera height/distance.',wraplength=900).pack(fill='x')
        ttk.Button(camera,text='Inspect exact source and bounds',command=self.camera_load).pack(anchor='w',pady=6)
        self.camera_fields={}
        for key,label in [('car_id','Target physical CarID (must match this project)'),('half_length_m','Follow half-length (m)'),('height_m','Follow height extent (m)')]:
            row=ttk.Frame(camera);row.pack(fill='x',pady=5);ttk.Label(row,text=label,width=48).pack(side='left');v=tk.StringVar();self.camera_fields[key]=v;ttk.Entry(row,textvariable=v,width=15).pack(side='left')
        self.camera_canvas=tk.Canvas(camera,height=250,bg='#1a1e24',highlightthickness=0);self.camera_canvas.pack(fill='both',expand=True,pady=10)
        for v in self.camera_fields.values():v.trace_add('write',lambda *_:self.camera_overlay())
        self.camera_note=tk.StringVar(value='Load qualified model first. Unsupported CarIDs fail closed.');ttk.Label(camera,textvariable=self.camera_note,wraplength=950).pack(fill='x')
        ttk.Label(camera,text='READ ONLY / unsupported: FOV, smoothing, look-at offsets, replay/rear camera controls.\nNo geometry, suspension, collision, audio or Previewer camera changes.',wraplength=900).pack(fill='x',pady=8)
        row=ttk.Frame(camera);row.pack(fill='x');ttk.Button(row,text='Apply follow extents',command=self.camera_apply).pack(side='left');ttk.Button(row,text='Reset camera override',command=lambda:self.vehicle_action('Restore camera',lambda:self.project.vehicle_reset('camera'))).pack(side='left')
        self.camera_info=None

        details=ttk.Frame(tabs,padding=10);tabs.add(details,text='Vehicle Details / Aliases');self.details_tab=details
        self.details_fields={}
        for key,label in [('manufacturer','Manufacturer (32)'),('model','Model (64)'),('combined','Combined display name (96)'),('display_name','Race Results display name (64)'),('description','Project description (8192)')]:
            row=ttk.Frame(details);row.pack(fill='x',pady=3);ttk.Label(row,text=label,width=32).pack(side='left');v=tk.StringVar();self.details_fields[key]=v;ttk.Entry(row,textvariable=v).pack(fill='x',expand=True)
        ttk.Label(details,text='Printable ASCII for game names. Numbers above are conservative SDK authoring budgets, not proven native buffer limits. Description is project metadata.',wraplength=950).pack(fill='x')
        row=ttk.Frame(details);row.pack(fill='x',pady=6);ttk.Button(row,text='Apply display identity',command=self.details_apply).pack(side='left');ttk.Button(row,text='Restore display identity',command=lambda:self.vehicle_action('Restore names',lambda:self.project.vehicle_reset('details'))).pack(side='left')
        self.identity_note=tk.StringVar();ttk.Label(details,textvariable=self.identity_note,wraplength=950).pack(fill='x',pady=5)
        self.alias_search=tk.StringVar();ttk.Entry(details,textvariable=self.alias_search).pack(fill='x');self.alias_search.trace_add('write',lambda *_:self.alias_fill())
        self.alias_tree=ttk.Treeview(details,columns=('alias',),show='tree headings',height=7);self.alias_tree.heading('#0',text='Original stable resource ID');self.alias_tree.heading('alias',text='Friendly name (metadata only)');self.alias_tree.pack(fill='both',expand=True);self.alias_tree.bind('<<TreeviewSelect>>',self.alias_selected)
        row=ttk.Frame(details);row.pack(fill='x');self.alias_name=tk.StringVar();ttk.Entry(row,textvariable=self.alias_name).pack(side='left',fill='x',expand=True);ttk.Button(row,text='Save friendly name',command=self.alias_apply).pack(side='left');ttk.Button(row,text='Inspect original texture',command=self.alias_inspect).pack(side='left')
        ttk.Label(details,text='Search by alias or original name. Shared atlas usages remain independent; alias does not rename files or change DX bindings.').pack(fill='x')

        art=ttk.Frame(tabs,padding=10);tabs.add(art,text='Generate Vehicle Art');self.art_tab=art
        self.art_role=tk.StringVar(value='both');ttk.Combobox(art,textvariable=self.art_role,values=['both','vehicle_select_art','smallcarsheet'],state='readonly').pack(fill='x')
        self.art_model=tk.StringVar(value='complete.dx');ttk.Combobox(art,textvariable=self.art_model,values=['complete.dx','car.dx'],state='readonly').pack(fill='x',pady=4)
        self.art_angles={}
        for key,label,default in [('azimuth','Yaw override (blank = native-style role default)',''),('elevation','Pitch override (blank = role default)',''),('padding','Render framing padding, pixels','12')]:
            row=ttk.Frame(art);row.pack(fill='x',pady=4);ttk.Label(row,text=label,width=58).pack(side='left');v=tk.StringVar(value=default);self.art_angles[key]=v;ttk.Entry(row,textvariable=v,width=12).pack(side='left')
        row=ttk.Frame(art);row.pack(fill='x',pady=8);ttk.Button(row,text='Generate preview (not applied)',command=self.art_generate_ui).pack(side='left');ttk.Button(row,text='Apply generated art to vehicle',command=self.art_apply_ui).pack(side='left');ttk.Button(row,text='Restore original vehicle art',command=lambda:self.vehicle_action('Restore UI art',lambda:self.project.vehicle_reset('art'))).pack(side='left')
        self.art_preview=ttk.Frame(art);self.art_preview.pack(fill='both',expand=True);self.art_images=[];self.pending_art={}
        self.art_note=tk.StringVar(value='Frontend contains qualified wheels. CPU diffuse renderer / mr-native-v1 composition; no game-reflection parity. Generate → compare → explicit Apply → Build.');ttk.Label(art,textvariable=self.art_note,wraplength=950).pack(fill='x',pady=8)
        self.vehicle_status=tk.StringVar();ttk.Label(w,textvariable=self.vehicle_status,padding=10,wraplength=990).pack(fill='x')
        self.vehicle_loaded()

    def vehicle_loaded(self):
        if not getattr(self,'vehicle_window',None) or not self.vehicle_window.winfo_exists() or not self.project:return
        p=self.project;state=p.vehicle_state();self.vehicle_header.set(p.data['identity']+' · '+p.data['kind']+' · runtime CarID '+str(p.data['car_id']))
        if self.physics_owner!=str(p.root):
            self.physics_info=None;self.physics_owner=str(p.root);self.phys_tree.delete(*self.phys_tree.get_children());self.camera_info=None;self.pending_art={};self.phys_selected=None
            for w in self.phys_editor.winfo_children():w.destroy()
            for v in self.camera_fields.values():v.set('')
            for w in self.art_preview.winfo_children():w.destroy()
        for key,v in self.details_fields.items():v.set(state['details'][key])
        if p.data['kind']=='addon':
            addon=json.loads((p.working/'addon.json').read_text());self.identity_note.set('LOCKED native identity / families / namespaces:\n'+json.dumps({'addon_id':addon['addon_id'],'runtime_CarID':p.data['car_id'],'author_slot':addon['physical_id'],'identity':addon['identity'],'resource_root':addon['assets']['model_package_root']},ensure_ascii=False))
        else:self.identity_note.set('Stock identity is read-only. Friendly aliases and generated previews are metadata; original stock UI frame replacement is unsupported.')
        self.alias_fill();self.physics_fill()
        signature=(str(p.root),tuple((k,v['sha256']) for k,v in state['art'].items()))
        if not self.pending_art and signature!=getattr(self,'shown_art',None):
            self.art_show(state['art'],applied=True);self.shown_art=signature
        if self.camera_info:
            values=(state['camera'] or {}).get('follow_extents',self.camera_info['original'])
            for key,v in values.items():self.camera_fields[key].set(str(v))
        self.vehicle_sync()

    def vehicle_sync(self):
        if not getattr(self,'vehicle_window',None) or not self.vehicle_window.winfo_exists():return
        p=self.project;addon=p is not None and p.data['kind']=='addon';physics=addon and bool(p.data.get('vehicle_authoring',{}).get('physics'))
        camera=addon
        if p is not None and p.data['kind']=='stock':
            from master_rallye.addon_sdk.stock_project import QUALIFIED_STOCK
            camera=bool(p.data['car_id']) and QUALIFIED_STOCK.get(p.data['car_id'])==p.data['family']
        unsupported=set()
        if not physics:unsupported.update(('Inspect qualified sources','Copy selected reference group','Reset physics','Apply selected typed field'))
        if not addon:unsupported.update(('Apply display identity','Restore display identity','Apply generated art to vehicle','Restore original vehicle art'))
        if not camera:unsupported.update(('Inspect exact source and bounds','Apply follow extents','Reset camera override'))
        if not getattr(self,'camera_info',None):unsupported.add('Apply follow extents')
        if not getattr(self,'pending_art',{}):unsupported.add('Apply generated art to vehicle')
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child,ttk.Button) and (self.busy or str(child['text']) in unsupported):child.state(['disabled'])
                walk(child)
        walk(self.vehicle_window)

    def vehicle_action(self,label,work):
        if not self.project or self.busy:return
        def done(report):
            self.vehicle_loaded();self.vehicle_status.set(label+' — saved')
            if report is not None:self.log.insert('end',json.dumps(report,indent=2,default=str)+'\n')
        self.run(label,work,done)

    def physics_load(self):
        if not self.project or self.busy:return
        p=self.project;reference=self.phys_reference.get() or None
        def done(info):
            self.physics_info=info;self.phys_reference_box['values']=info['families']
            if not self.phys_reference.get():self.phys_reference.set(info['donor'])
            self.phys_note.set(info['warning']+'\nRetail pins: '+json.dumps(info['pins']));self.physics_fill()
        self.run('Read hash-qualified physics source/profile',lambda:p.physics_inspect(reference),done)

    def physics_fill(self):
        if not getattr(self,'physics_info',None):return
        selected=self.phys_tree.selection();self.phys_tree.delete(*self.phys_tree.get_children());q=self.phys_search.get().casefold();state=self.project.vehicle_state()
        self.phys_rows={}
        for index,row in enumerate(self.physics_info['rows']):
            if q and q not in (row['member']+' '+row['path']).casefold():continue
            row=dict(row);row['value']=state['physics']['overrides'].get(row['member'],{}).get(row['path'],row['original']);key='field:'+str(index);group=row['member']+':'+row['group']
            if not self.phys_tree.exists(group):self.phys_tree.insert('','end',iid=group,text=group,open=True)
            self.phys_rows[key]=row;self.phys_tree.insert(group,'end',iid=key,text=row['path']+(' [read-only]' if not row['editable'] else ''),values=(str(row['original']),str(row['value']),str(row['reference']),row['units']))
        if selected and self.phys_tree.exists(selected[0]):self.phys_tree.selection_set(selected)
        else:self.physics_selected()

    def physics_selected(self,*_):
        selected=self.phys_tree.selection();row=self.phys_rows.get(selected[0]) if selected else None
        for widget in self.phys_editor.winfo_children():widget.destroy()
        self.phys_fields=[];self.phys_selected=row
        if not row:return
        self.phys_note.set(row['path']+' · '+row['type']+' · '+row['units']+'\n'+row['bounds']+'\n'+row['evidence'])
        if not row['editable']:return
        values=row['value'] if isinstance(row['value'],list) else [row['value']]
        for value in values:
            var=tk.BooleanVar(value=value) if row['type']=='Bool' else tk.StringVar(value=str(value));self.phys_fields.append(var)
            if row['type']=='Bool':ttk.Checkbutton(self.phys_editor,text='Enabled',variable=var).pack(side='left')
            else:ttk.Entry(self.phys_editor,textvariable=var,width=24).pack(side='left',padx=3)

    def physics_apply(self):
        row=getattr(self,'phys_selected',None)
        if not row or not row['editable'] or self.busy:return
        try:
            kind=row['type'];values=[v.get() for v in self.phys_fields]
            value=values[0] if kind in ('Bool','String') else int(values[0]) if kind=='Int' else [float(v) for v in values] if kind.startswith('Vector') else float(values[0])
            p=self.project;self.vehicle_action('Apply typed physics',lambda:p.physics_update(row['member'],row['path'],value))
        except Exception as exc:self.vehicle_status.set(str(exc))

    def physics_copy(self):
        row=getattr(self,'phys_selected',None)
        if row:
            p=self.project;family=self.phys_reference.get();group=row['group'];self.vehicle_action('Copy compatible reference group',lambda:p.physics_copy_reference(family,group))

    def camera_load(self):
        if not self.project or self.busy:return
        def done(info):
            self.camera_info=info;self.camera_fields['car_id'].set(str(info['car_id']))
            for key,value in info['current'].items():self.camera_fields[key].set(str(value))
            self.camera_note.set('Runtime family '+info['family']+' · source SHA256 '+info['source_model_sha256']+'\nBefore: '+str(info['original'])+'\n'+info['boundary']);self.camera_overlay()
        self.run('Read source-qualified camera bounds',self.project.camera_inspect,done)

    def camera_overlay(self):
        if not getattr(self,'camera_info',None):return
        c=self.camera_canvas;c.delete('all');w=max(800,c.winfo_width());h=max(200,c.winfo_height());original=self.camera_info['original']
        try:changed={'half_length_m':float(self.camera_fields['half_length_m'].get()),'height_m':float(self.camera_fields['height_m'].get())}
        except ValueError:return
        maximum=max(original['half_length_m']*2,original['height_m'],changed['half_length_m']*2,changed['height_m'],.1);scale=min((w-90)/maximum,(h-60)/maximum)
        for title,ext,color in [('Source bounds',original,'#aeb6c2'),('Follow extents (camera only)',changed,'#e5b56a')]:
            half=ext['half_length_m']*scale;vertical=ext['height_m']*scale/2;c.create_rectangle(w/2-half,h/2-vertical,w/2+half,h/2+vertical,outline=color,width=2)
            c.create_text(15,18 if title.startswith('Source') else 38,anchor='w',text=title+' '+str(ext),fill=color)
        c.create_text(w-100,h-15,text='Side extent diagram: Z / Y',fill='#b5bdc9')

    def camera_apply(self):
        try:
            p=self.project;half=float(self.camera_fields['half_length_m'].get());height=float(self.camera_fields['height_m'].get());car=int(self.camera_fields['car_id'].get());self.vehicle_action('Apply native follow extents',lambda:p.camera_update(half,height,car))
        except Exception as exc:self.vehicle_status.set(str(exc))

    def details_apply(self):
        fields={k:v.get() for k,v in self.details_fields.items()};p=self.project;self.vehicle_action('Apply display names (native identity fixed)',lambda:p.details_update(fields))

    def alias_fill(self):
        if not hasattr(self,'alias_tree') or not self.project:return
        self.alias_tree.delete(*self.alias_tree.get_children())
        for row in self.project.texture_search(self.alias_search.get()):self.alias_tree.insert('','end',iid=row['name'],text=row['name'],values=(row['alias'],))

    def alias_selected(self,*_):
        selected=self.alias_tree.selection()
        if selected:self.alias_name.set(self.alias_tree.item(selected[0],'values')[0])

    def alias_apply(self):
        selected=self.alias_tree.selection()
        if selected:
            p=self.project;name=selected[0];label=self.alias_name.get();self.vehicle_action('Save friendly texture alias',lambda:p.alias_update(name,label))

    def alias_inspect(self):
        selected=self.alias_tree.selection()
        if selected:self.texture_name.set(selected[0]);self.show_texture()

    def art_generate_ui(self):
        if not self.project or self.busy:return
        try:
            p=self.project;role=self.art_role.get();options={k:(int(v.get()) if k=='padding' else float(v.get()) if v.get().strip() else None) for k,v in self.art_angles.items()};model=self.art_model.get()
            def done(report):
                self.pending_art.update(report)
                self.art_show(self.pending_art)
                self.art_note.set('Generated only, not yet applied. '+json.dumps({k:{'sha256':v['sha256'],'source':v['source_model_sha256'],'composition':v['composition']} for k,v in report.items()}))
            self.run('Generate MR-style vehicle art',lambda:p.art_generate(model=model,role=None if role=='both' else role,**options),done)
        except Exception as exc:self.vehicle_status.set(str(exc))

    def art_show(self,report,applied=False):
        from PIL import Image,ImageTk
        import io
        for w in self.art_preview.winfo_children():w.destroy()
        self.art_images=[]
        for key,entry in report.items():
            row=ttk.Frame(self.art_preview);row.pack(fill='x',pady=6);ttk.Label(row,text=key+' (original → '+('applied' if applied else 'generated')+')',width=40).pack(side='left')
            before=self.project.art_preview_png(key,original=True)
            after=self.project.art_preview_png(key) if applied else Path(entry['png']).read_bytes()
            for raw in [before,after]:
                if raw is None:continue
                image=Image.open(io.BytesIO(raw)).convert('RGBA');image=image.resize((256,256) if key=='vehicle_select_art' else (256,128),Image.Resampling.NEAREST)
                photo=ImageTk.PhotoImage(image,master=self.root);self.art_images.append(photo);ttk.Label(row,image=photo).pack(side='left',padx=5)
        if applied:self.art_note.set('Applied project art persists. Native bank inclusion is verified by Build; D3D8 frontend/Results remain owner tests.')

    def art_apply_ui(self):
        if self.pending_art:
            p=self.project;report=dict(self.pending_art)
            def done(_):
                self.pending_art={};self.vehicle_loaded();self.vehicle_status.set('Reviewed art applied; Build still required for native bank installation.')
            self.run('Apply reviewed vehicle art',lambda:p.art_apply(report),done)
