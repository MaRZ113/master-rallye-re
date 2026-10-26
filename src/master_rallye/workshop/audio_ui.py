"""Audio Studio widgets. All authoring, validation and audition use SDK services."""
import json
import sys
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from .audio import LAYERS, LABELS
from master_rallye.addon_sdk.audio_profile import RESPONSE_BOUNDS

def wav_import_options(parent,path):
    """Inspect before importing; long source recordings need an explicit short trim."""
    from .audio import read_wav,sha
    from .branding import apply_icon
    raw,samples,fmt=read_wav(path);window=tk.Toplevel(parent);apply_icon(window)
    window.title('Import local PCM WAV — private project copy');result={}
    ttk.Label(window,text=Path(path).name+'\n'+json.dumps(fmt)+'\nDuration: %.3f s\nSHA256 %s\nOutput: mono PCM16 48000 Hz. Original remains unchanged.\nChoose 0.1–4 s; trim and crossfade are in SOURCE frames.'%(len(samples)/fmt['sample_rate'],sha(raw)),wraplength=540,padding=12).pack(fill='x')
    fields={};defaults={'start':0,'end':min(len(samples),fmt['sample_rate']*4),'crossfade':0,'gain_db':0}
    for name,value in defaults.items():
        row=ttk.Frame(window,padding=5);row.pack(fill='x');ttk.Label(row,text=name,width=18).pack(side='left')
        fields[name]=tk.StringVar(value=str(value));ttk.Entry(row,textvariable=fields[name],width=25).pack(side='left')
    dc=tk.BooleanVar(value=True);ttk.Checkbutton(window,text='Remove DC',variable=dc).pack(anchor='w',padx=12)
    status=tk.StringVar();ttk.Label(window,textvariable=status).pack(fill='x')
    def accept():
        try:
            result.update(trim=[int(fields['start'].get()),int(fields['end'].get())],crossfade=int(fields['crossfade'].get()),gain_db=float(fields['gain_db'].get()),remove_dc=dc.get())
            a,b=result['trim'];cf=result['crossfade']
            if not 0<=a<b<=len(samples) or not .1<=(b-a)/fmt['sample_rate']<=4 or not 0<=cf<=4096 or cf*8>b-a or not -36<=result['gain_db']<=12:raise ValueError('Trim, gain or crossfade outside SDK bounds')
            window.destroy()
        except Exception as exc:result.clear();status.set(str(exc))
    ttk.Button(window,text='Import pinned copy',command=accept).pack(fill='x',padx=12,pady=8)
    window.transient(parent);window.grab_set();parent.wait_window(window)
    return result or None

class AudioPanels:
    def audio_sync(self):
        if not hasattr(self,'audio_tab'):return
        supported=bool(self.project and self.project.data['kind']=='addon' and (self.project.working/'audio-profile.json').is_file())
        def walk(parent):
            for widget in parent.winfo_children():
                if isinstance(widget,(ttk.Button,ttk.Spinbox,ttk.Entry,ttk.Radiobutton,ttk.Checkbutton)):
                    widget.state(['disabled'] if self.busy or not supported else ['!disabled'])
                walk(widget)
        walk(self.audio_tab)
        if self.audio_layer.get()=='engine':self.audio_enable_button.state(['disabled'])

    def audio_layout(self, tabs):
        self.audio_tab=ttk.Frame(tabs,padding=8);tabs.add(self.audio_tab,text='Audio')
        canvas=tk.Canvas(self.audio_tab,bg='#232830',highlightthickness=0);self.audio_canvas=canvas
        scroll=ttk.Scrollbar(self.audio_tab,orient='vertical',command=canvas.yview);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
        canvas.configure(yscrollcommand=scroll.set);f=ttk.Frame(canvas);item=canvas.create_window((0,0),window=f,anchor='nw')
        f.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width))
        def wheel(e):
            if str(e.widget).startswith(str(self.audio_tab)):canvas.yview_scroll(-int(e.delta/120),'units')
        self.root.bind('<MouseWheel>',wheel,add='+')
        self.audio_layer=tk.StringVar(value=LAYERS[0]);self.audio_mute={k:tk.BooleanVar(value=False) for k in LAYERS}
        self.audio_solo={k:tk.BooleanVar(value=False) for k in LAYERS};self.audio_fields={}
        self.audio_status=tk.StringVar(value='Qualified addon custom audio only; stock passthrough is preserved.')
        self.audio_source=tk.StringVar();self.audio_preset=tk.StringVar()
        for key,label in zip(LAYERS,LABELS):
            row=ttk.Frame(f);row.pack(fill='x')
            ttk.Radiobutton(row,text=label,variable=self.audio_layer,value=key,command=self.audio_loaded).pack(side='left')
            ttk.Checkbutton(row,text='Mute',variable=self.audio_mute[key]).pack(side='right')
            ttk.Checkbutton(row,text='Solo',variable=self.audio_solo[key]).pack(side='right')
        ttk.Label(f,text='Mute / Solo affect audition only. BOV is a one-shot; other layers are continuous.',wraplength=340).pack(fill='x',pady=4)
        ttk.Label(f,textvariable=self.audio_source,wraplength=340).pack(fill='x')
        row=ttk.Frame(f);row.pack(fill='x')
        ttk.Button(row,text='Import Local WAV…',command=self.audio_import_dialog).pack(side='left')
        ttk.Button(row,text='Assign Existing…',command=self.audio_assign_dialog).pack(side='left')
        self.audio_enabled=tk.BooleanVar(value=True)
        self.audio_enable_button=ttk.Checkbutton(f,text='Enable in candidate (engine always active)',variable=self.audio_enabled)
        self.audio_enable_button.pack(anchor='w')
        self.audio_form=ttk.Frame(f);self.audio_form.pack(fill='x')
        row=ttk.Frame(f);row.pack(fill='x')
        ttk.Button(row,text='Apply parameters',command=self.audio_apply).pack(side='left')
        ttk.Button(row,text='Reset layer',command=lambda:self.audio_action('Reset audio layer',lambda:self.project.audio_reset(self.audio_layer.get()))).pack(side='left')
        ttk.Button(row,text='Diagnostics',command=self.audio_diagnostics).pack(side='left')
        row=ttk.Frame(f);row.pack(fill='x',pady=4)
        self.audio_preset_box=ttk.Combobox(row,textvariable=self.audio_preset,width=16);self.audio_preset_box.pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Save preset',command=self.audio_save_named).pack(side='left')
        ttk.Button(row,text='Load',command=lambda:self.audio_action('Load audio preset',lambda:self.project.audio_load_preset(self.audio_preset.get()))).pack(side='left')
        ttk.Button(f,text='Import preset from another addon project…',command=self.audio_transfer_dialog).pack(fill='x')
        self.audio_exe=tk.StringVar(value=str(self.sdk_root.parent/'MRallye.exe'))
        ttk.Label(f,text='Read-only original MRallye.exe for DSP audition').pack(anchor='w')
        row=ttk.Frame(f);row.pack(fill='x');ttk.Entry(row,textvariable=self.audio_exe).pack(side='left',fill='x',expand=True)
        def browse_exe():
            path=filedialog.askopenfilename(parent=self.root,filetypes=[('Original MR executable','*.exe')])
            if path:self.audio_exe.set(path)
        ttk.Button(row,text='Browse',command=browse_exe).pack(side='left')
        self.audio_rpm=tk.StringVar(value='900,2000,4000,6000,3000,900');self.audio_load=tk.DoubleVar(value=1.);self.audio_gear=tk.IntVar(value=2);self.audio_lift=tk.BooleanVar(value=True)
        ttk.Label(f,text='Audition RPM sequence (1–8 values)').pack(anchor='w')
        ttk.Entry(f,textvariable=self.audio_rpm).pack(fill='x')
        self.audio_rev_limit=tk.IntVar(value=7000)
        row=ttk.Frame(f);row.pack(fill='x');ttk.Label(row,text='Audition rev limit (does not edit physics)').pack(side='left')
        ttk.Spinbox(row,from_=500,to=20000,textvariable=self.audio_rev_limit,width=7).pack(side='left')
        row=ttk.Frame(f);row.pack(fill='x')
        ttk.Label(row,text='Signed load').pack(side='left');ttk.Spinbox(row,from_=-1,to=1,increment=.1,textvariable=self.audio_load,width=5).pack(side='left')
        ttk.Label(row,text=' Gear (1=N)').pack(side='left');ttk.Spinbox(row,from_=0,to=16,textvariable=self.audio_gear,width=4).pack(side='left')
        ttk.Checkbutton(f,text='Script sustained load → rapid release',variable=self.audio_lift).pack(anchor='w')
        row=ttk.Frame(f);row.pack(fill='x')
        ttk.Button(row,text='Audition / mix',command=self.audio_listen).pack(side='left')
        ttk.Button(row,text='Stop',command=self.audio_stop).pack(side='left')
        ttk.Button(row,text='Undo',command=self.undo).pack(side='left')
        ttk.Button(row,text='Redo',command=self.redo).pack(side='left')
        ttk.Button(row,text='Restore audio',command=lambda:self.audio_action('Restore audio baseline',lambda:self.project.audio_reset())).pack(side='left')
        ttk.Label(f,textvariable=self.audio_status,wraplength=340).pack(fill='x',pady=4)
        ttk.Button(f,text='Audio help / preview limitations',command=lambda:self.show_help('audio')).pack(fill='x')

    def audio_loaded(self):
        if not self.project:return
        for child in self.audio_form.winfo_children():child.destroy()
        self.audio_fields={}
        try:
            state=self.project.audio_state();key=self.audio_layer.get();profile=state['profile']
            if key not in profile:raise ValueError('Layer absent: import a compatible response preset first')
            source=profile[key] if key=='engine' else profile[key]['source']
            title=state['imports'].get(source['source_sha256'],{}).get('name',Path(source['source_path']).name)
            from .audio import read_wav
            _,_,fmt=read_wav(self.project.root/'audio-sources'/(source['source_sha256']+'.wav'))
            format_text=f"{fmt['channels']} ch · {fmt['bits_per_sample']} bit · {fmt['sample_rate']} Hz · {fmt['frames']/fmt['sample_rate']:.3f} s → mono PCM16 48000 Hz"
            self.audio_source.set(title+' · '+('one-shot' if key=='bov_release' else 'continuous')+'\n'+format_text+'\nSHA256 '+source['source_sha256'][:16]+'… (full hashes / levels: Diagnostics)\n'+('Native stock synthesis profile '+str(profile['stock_audio_profile_id'])+'; source attribution: profile notes / Diagnostics' if key=='engine' else profile[key]['provenance']))
            self.audio_enabled.set(state['enabled'].get(key,True));self.audio_enable_button.configure(state='disabled' if key=='engine' else 'normal')
            entries={'gain_db':(source['gain_db'],(-36,12)),'trim_start':(source['trim_frames'][0],(0,2000000)),
                     'trim_end':(source['trim_frames'][1],(1,2000000)),'crossfade_frames':(source['crossfade_frames'],(0,4096)),
                     'remove_dc':(source['remove_dc'],None)}
            if key=='engine':entries['stock_audio_profile_id']=(profile['stock_audio_profile_id'],(0,22))
            else:
                for name,bounds in RESPONSE_BOUNDS[key].items():entries[name]=(profile[key]['response'][name],bounds)
                entries['mute_neutral']=(profile[key]['response'].get('mute_neutral',False),None)
            # Two columns keep the full BOV/spool parameter set visible.
            for i,(name,(value,bounds)) in enumerate(entries.items()):
                row,col=divmod(i,2);frame=ttk.Frame(self.audio_form);frame.grid(row=row,column=col,sticky='ew',padx=2)
                ttk.Label(frame,text=name.replace('_',' '),font=('Segoe UI',8)).pack(anchor='w')
                var=tk.BooleanVar(value=value) if bounds is None else tk.StringVar(value=str(value));self.audio_fields[name]=var
                if bounds is None:ttk.Checkbutton(frame,variable=var).pack(anchor='w')
                else:ttk.Spinbox(frame,textvariable=var,from_=bounds[0],to=bounds[1],increment=1 if name in ('trim_start','trim_end','crossfade_frames','stock_audio_profile_id') else .1,width=14).pack(fill='x')
            available=self.project.audio_available_presets();self.audio_preset_box['values']=list(available)
            self.audio_status.set('Presets: '+(', '.join(available) or '(none)')+'\nPCM WAV only. Estimated spool/load; no physical boost sensor. Spool disable mutes sound, retaining BOV estimator. Gameplay listening pending.')
        except Exception as exc:
            self.audio_source.set('');self.audio_status.set(str(exc))

    def audio_action(self,label,work):
        if not self.project or self.busy:return
        self.run(label,work,lambda _:self.audio_loaded())

    def audio_apply(self):
        if not self.project or self.busy:return
        try:
            key=self.audio_layer.get();profile=self.project.audio_state()['profile'];fields={k:v.get() for k,v in self.audio_fields.items()}
            source=dict(profile[key] if key=='engine' else profile[key]['source'])
            source.update(gain_db=float(fields['gain_db']),trim_frames=[int(fields['trim_start']),int(fields['trim_end'])],crossfade_frames=int(fields['crossfade_frames']),remove_dc=fields['remove_dc'])
            response=None if key=='engine' else {name:float(fields[name]) for name in RESPONSE_BOUNDS[key]}
            if response is not None:response['mute_neutral']=fields['mute_neutral']
            enabled=self.audio_enabled.get();stock=int(fields['stock_audio_profile_id']) if key=='engine' else None
            self.audio_action('Compile audio edits',lambda:self.project.audio_update(key,source=source,response=response,enabled=enabled,stock_profile=stock))
        except Exception as exc:self.audio_status.set(str(exc))

    def audio_import_dialog(self):
        if not self.project or self.busy:return
        path=filedialog.askopenfilename(parent=self.root,filetypes=[('RIFF PCM WAV','*.wav')])
        if path:
            try:
                options=wav_import_options(self.root,path)
                if options:
                    key=self.audio_layer.get();self.audio_action('Import and qualify private WAV',lambda:self.project.audio_import(key,path,**options))
            except Exception as exc:self.audio_status.set(str(exc))

    def audio_assign_dialog(self):
        if not self.project or self.busy:return
        try:
            catalog=self.project.audio_catalog();window=tk.Toplevel(self.root);window.title('Assign Existing — pinned project audio')
            from .branding import apply_icon
            apply_icon(window);items=ttk.Treeview(window,columns=('name','role','sha'),show='headings',height=10)
            for field in ('name','role','sha'):items.heading(field,text=field);items.column(field,width=180)
            for digest,entry in catalog.items():items.insert('','end',iid=digest,values=(entry['name'],entry['last_role'],digest[:16]))
            items.pack(fill='both',expand=True)
            key=self.audio_layer.get()
            def choose():
                if not items.selection():return
                digest=items.selection()[0];window.destroy();self.audio_action('Assign pinned source',lambda:self.project.audio_assign(key,digest))
            ttk.Button(window,text='Assign source (keep destination response)',command=choose).pack(fill='x');window.transient(self.root)
        except Exception as exc:self.audio_status.set(str(exc))

    def audio_diagnostics(self):
        if not self.project or self.busy:return
        self.run('Compile / inspect audio',self.project.audio_inspect,lambda r:self.log.insert('end',json.dumps(r,indent=2)+'\n'))

    def audio_save_named(self):
        name=self.audio_preset.get();self.audio_action('Save audio preset',lambda:self.project.audio_save_preset(name))

    def audio_transfer_dialog(self):
        if not self.project or self.busy:return
        folder=filedialog.askdirectory(parent=self.root,title='Source addon Workshop project (explicit destination CarID / namespace rebinding)')
        if not folder:return
        from .service import WorkshopProject
        try:
            donor=WorkshopProject(folder);names=donor.audio_state()['presets']
            name=simpledialog.askstring('Import compatible preset','Name: '+', '.join(names),parent=self.root)
            if name:self.audio_action('Rebind preset to destination addon',lambda:self.project.audio_transfer(donor,name))
        except Exception as exc:self.audio_status.set(str(exc))

    def audio_listen(self):
        if not self.project or self.busy:return
        try:
            solo={k for k,v in self.audio_solo.items() if v.get()}
            enabled={k:not self.audio_mute[k].get() and (not solo or k in solo) for k in LAYERS}
            rpms=[float(v.strip()) for v in self.audio_rpm.get().split(',')]
            load=self.audio_load.get();gear=self.audio_gear.get();lift=self.audio_lift.get();rev_limit=self.audio_rev_limit.get();exe=Path(self.audio_exe.get())
            if not -1<=load<=1 or not 0<=gear<=16:raise ValueError('Audition controls outside bounds')
            # Shared existing DSP diagnostic tools, loaded from the SDK checkout.
            toolpath=str(self.sdk_root/'tools')
            if toolpath not in sys.path:sys.path.insert(0,toolpath)
            output=self.project.root/'auditions'/(uuid.uuid4().hex+'.wav')
            def finished(report):
                self.audio_status.set('Audition: '+str(output)+'\nClipped: '+str(sum(m['clipped_samples'] for m in report['mix']))+'; BOV events: '+str(sum(len(m['bov_events']) for m in report['mix'])))
                import winsound
                winsound.PlaySound(str(output),winsound.SND_FILENAME|winsound.SND_ASYNC)
            project=self.project
            self.run('Original native DSP / authored supplemental mix',lambda:project.audio_audition(exe,output,rpms=rpms,load=load,gear=gear,enabled=enabled,lift=lift,rev_limit=rev_limit),finished)
        except Exception as exc:self.audio_status.set(str(exc))

    def audio_stop(self):
        import winsound
        winsound.PlaySound(None,0)
