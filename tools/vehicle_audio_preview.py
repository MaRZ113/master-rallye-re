"""Small Windows audio panel using the qualified original-x86 MR audition path.

No game code/assets bundled; optional Tk and Unicorn are needed for audition.
There is no fabricated throttle layer: throttle affects RPM through game physics.
"""
import argparse,json,subprocess,sys,threading,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.audio_profile import compile_audio,decode_pcm,canonical_wav


def add_whine_preview(engine_wav,whine_wav,response,rpm,load,gear):
    from vehicle_whine_audition import audition_whine
    engine,fmt=decode_pcm(engine_wav)
    if (fmt['sample_rate'],fmt['channels'],fmt['bits_per_sample'])!=(48000,1,16):
        raise ValueError('preview mix needs canonical engine PCM')
    extra,report=audition_whine(whine_wav,response,[rpm],[load],[gear],fmt['frames']/48000)
    whine,_=decode_pcm(extra);mixed=[a+b for a,b in zip(engine,whine)]
    if len(mixed)!=len(engine):raise ValueError('preview mix duration mismatch')
    clipped=sum(not -32768<=x<=32767 for x in mixed)
    return canonical_wav([max(-32768,min(32767,x)) for x in mixed]),{**report,'clipped_samples':clipped,
        'scope':'Native engine DSP plus authored independent-loop approximation; no DirectSound spatial mix'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',type=Path);p.add_argument('--source-root',type=Path)
    p.add_argument('--exe',type=Path,default=ROOT.parent/'MRallye.exe');p.add_argument('--cache',type=Path,default=ROOT/'.research-output/vehicles/audio-preview')
    p.add_argument('--rev-limit',type=int,default=7000);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    import tkinter as tk
    from tkinter import ttk,filedialog
    window=tk.Tk();window.title('Vehicle SDK — Native MR Audio Preview');window.geometry('780x540')
    profile_path=tk.StringVar(value=str(a.profile or ''));root_path=tk.StringVar(value=str(a.source_root or ''))
    rpm=tk.IntVar(value=min(3500,a.rev_limit));limit=tk.IntVar(value=a.rev_limit);status=tk.StringVar(value='Select an audio profile and its source project folder.')
    enabled={name:tk.BooleanVar(value=True) for name in ('engine','transmission_whine','turbo_spool','bov_release')};scripted_lift=tk.BooleanVar(value=False);include_whine=enabled['transmission_whine'];load=tk.DoubleVar(value=1.);gear=tk.IntVar(value=2)
    frame=ttk.Frame(window,padding=14);frame.pack(fill='both',expand=True)
    def browse_profile():
        name=filedialog.askopenfilename(filetypes=[('SDK audio profile','*.json')])
        if name:profile_path.set(name);root_path.set(str(Path(name).parent))
    for label,value,command in [('Audio profile',profile_path,browse_profile),('Source project',root_path,lambda:root_path.set(filedialog.askdirectory() or root_path.get()))]:
        row=ttk.Frame(frame);row.pack(fill='x',pady=3);ttk.Label(row,text=label,width=15).pack(side='left');ttk.Entry(row,textvariable=value).pack(side='left',fill='x',expand=True);ttk.Button(row,text='Browse',command=command).pack(side='right')
    ttk.Label(frame,text='Engine RPM (native normalized RPM → MR synthesis)').pack(anchor='w',pady=(15,0))
    controls=ttk.Frame(frame);controls.pack(fill='x');ttk.Spinbox(controls,from_=0,to=30000,textvariable=rpm,width=10).pack(side='left')
    ttk.Label(controls,text='   Rev limit').pack(side='left');ttk.Spinbox(controls,from_=500,to=20000,textvariable=limit,width=10).pack(side='left')
    whine_controls=ttk.Frame(frame);whine_controls.pack(fill='x',pady=8)
    ttk.Label(whine_controls,text='Control inputs').pack(side='left')
    ttk.Label(whine_controls,text='  Signed load / peak').pack(side='left');ttk.Spinbox(whine_controls,from_=-1,to=1,increment=.1,textvariable=load,width=6).pack(side='left')
    ttk.Label(whine_controls,text='  Gear index (1=N)').pack(side='left');ttk.Spinbox(whine_controls,from_=0,to=16,textvariable=gear,width=4).pack(side='left')
    layers_row=ttk.Frame(frame);layers_row.pack(fill='x')
    for name,var in enabled.items():
        ttk.Checkbutton(layers_row,text=name,variable=var).pack(side='left')
    ttk.Checkbutton(frame,text='Script sustained load then lift (BOV trigger audition)',variable=scripted_lift).pack(anchor='w')
    ttk.Label(frame,text='Original MR engine synthesis and near-listener SFX gain curve.\nOptional layers use authored controls; no race spatial mix or DirectSound thread timing.',wraplength=650).pack(anchor='w',pady=12)
    ttk.Label(frame,textvariable=status,wraplength=610).pack(anchor='w')
    buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=10)
    busy=False;result_path=None
    def finished(ok,message,path=None):
        nonlocal busy,result_path
        busy=False;play.configure(state='normal');status.set(message);result_path=path
        if ok and not a.self_test:
            import winsound
            winsound.PlaySound(str(path),winsound.SND_FILENAME|winsound.SND_ASYNC)
        if a.self_test:
            window._self_test_ok=ok;window.destroy()
    def render():
        nonlocal busy
        if busy:return
        try:
            name=Path(profile_path.get());source=Path(root_path.get());definition=json.loads(name.read_text());values,report=compile_audio(definition,source)
            current_rpm=rpm.get();rev_limit=limit.get()
            whine=report.get('transmission_whine') if include_whine.get() else None
            layer_selection={name:var.get() for name,var in enabled.items()};lift=scripted_lift.get()
            current_load=load.get();current_gear=gear.get()
            if not -1<=current_load<=1 or not 0<=current_gear<=16:raise ValueError('load or gear outside preview guard')
            if not 0<=current_rpm<=30000 or not 500<=rev_limit<=20000:raise ValueError('RPM or rev limit outside preview guard')
            folder=a.cache.resolve()/uuid.uuid4().hex;folder.mkdir(parents=True)
            resource=folder/'engine.wav';resource.write_bytes(next(iter(values.values())));output=folder/'audition.wav'
        except Exception as exc:
            status.set(str(exc))
            if a.self_test:window._self_test_ok=False;window.destroy()
            return
        busy=True;play.configure(state='disabled');status.set('Rendering one second through original native MR DSP…')
        command=[sys.executable,str(ROOT/'tools/vehicle_audio_audition.py'),'--exe',str(a.exe.resolve()),'--resource',str(resource),'--stock-audio-profile-id',str(definition['stock_audio_profile_id']),'--rpm',str(current_rpm),'--rev-limit',str(rev_limit),'--seconds','1','--output',str(output)]
        def worker():
            try:
                r=subprocess.run(command,capture_output=True,text=True,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if r.returncode:raise ValueError((r.stderr or r.stdout)[-600:])
                from vehicle_audio_layers import mix_layers
                mixed,mix=mix_layers(output.read_bytes(),values,report,current_rpm,current_load,current_gear,layer_selection,lift=lift)
                output.write_bytes(mixed);output.with_suffix('.mix.json').write_text(json.dumps(mix,indent=2)+'\n')
                message='Audition ready; clipped samples: '+str(mix['clipped_samples'])+'; BOV events: '+str(len(mix['bov_events']))+'. Reloads profile each render.'
                window.after(0,lambda:finished(True,message,output))
            except Exception as exc:
                message=str(exc);window.after(0,lambda:finished(False,message))
        threading.Thread(target=worker,daemon=True).start()
    play=ttk.Button(buttons,text='Render and listen',command=render);play.pack(side='left')
    def solo(name):
        for key,var in enabled.items():var.set(key==name)
        scripted_lift.set(name=='bov_release')
        render()
    for name in enabled:
        ttk.Button(buttons,text='Solo '+{'engine':'engine','transmission_whine':'whine','turbo_spool':'spool','bov_release':'BOV'}[name],command=lambda n=name:solo(n)).pack(side='left',padx=2)
    def stop():
        import winsound
        winsound.PlaySound(None,0)
    ttk.Button(buttons,text='Stop',command=stop).pack(side='left',padx=6)
    ttk.Label(frame,text='Uses your exact local MR executable as read-only DSP input. Does not launch Master Rallye.',wraplength=610).pack(anchor='w')
    if a.self_test:window.after(100,render)
    window.mainloop()
    if a.self_test:
        if not getattr(window,'_self_test_ok',False):raise SystemExit('Audio panel self-test failed')
        print('PASS_AUDIO_PANEL_NATIVE_RENDER')

if __name__=='__main__':main()
