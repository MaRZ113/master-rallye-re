"""Reviewed source/conversion dialog; optional GT browsing stays separate."""
import json,queue,threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from .branding import apply_icon
from .audio import LAYERS,LABELS
from .audio_import import decoder_capabilities

def play(path=None):
    import winsound
    winsound.PlaySound(str(path) if path else None,winsound.SND_FILENAME|winsound.SND_ASYNC if path else 0)

class AudioImportWindow:
    def __init__(self,app,path,evidence=None):
        self.app=app;self.project=app.project;self.path=Path(path);self.evidence=evidence;self.report=None;self.busy=False;self.queue=queue.Queue();self.revision=0
        win=tk.Toplevel(app.root);self.window=win;apply_icon(win);win.title('Audio Import 2.0 — review before assignment');win.geometry('960x740');win.transient(app.root);win.grab_set();win.protocol('WM_DELETE_WINDOW',self.close)
        ttk.Label(win,text=self.project.data['identity']+' / CarID '+str(self.project.data['car_id'])+' · '+self.path.name+'\nWAV PCM uses the existing SDK decoder; optional local FFmpeg decodes qualified FLAC/MP3/Ogg/WAV variants. Originals remain unchanged. Source limit: 30 s / 64 MiB.',padding=10,wraplength=930).pack(fill='x')
        self.layer=tk.StringVar(value=app.audio_layer.get());row=ttk.Frame(win,padding=5);row.pack(fill='x');ttk.Label(row,text='Assign to independent MR layer').pack(side='left');ttk.Combobox(row,textvariable=self.layer,values=LAYERS,state='readonly',width=25).pack(side='left')
        self.fields={}
        for key,label,value in [('start','Trim start (decoded frames; blank = default)',''),('end','Trim exclusive end (blank = first 4 seconds)',''),('crossfade','Circular loop crossfade (source frames)',0),('gain_db','Native gain (dB)',-3)]:
            row=ttk.Frame(win,padding=4);row.pack(fill='x');ttk.Label(row,text=label,width=58).pack(side='left');var=tk.StringVar(value=str(value));self.fields[key]=var;ttk.Entry(row,textvariable=var,width=24).pack(side='left');var.trace_add('write',lambda *_:self.invalidate())
        self.dc=tk.BooleanVar(value=True);self.loop=tk.BooleanVar(value=False)
        ttk.Checkbutton(win,text='Remove DC before native conversion',variable=self.dc,command=self.invalidate).pack(anchor='w',padx=10)
        ttk.Checkbutton(win,text='Use original forward loop when present (explicit choice; replaces trim)',variable=self.loop,command=self.invalidate).pack(anchor='w',padx=10)
        ttk.Label(win,text='BOV always plays once. A source loop only selects an interval; it does not turn BOV into a continuous layer.\nFor engine: one recording through MR synthesis, not original GT multi-band playback.',wraplength=920,padding=5).pack(fill='x')
        bar=ttk.Frame(win,padding=6);bar.pack(fill='x');self.buttons={}
        for title,cmd in [('Prepare / refresh comparison',self.prepare),('Play decoded source excerpt',lambda:self.listen('original-preview.wav')),('Play converted native WAV',lambda:self.listen('converted.wav')),('Stop',lambda:play())]:
            b=ttk.Button(bar,text=title,command=cmd);b.pack(side='left');self.buttons[title]=b
        self.canvas=tk.Canvas(win,height=120,bg='#151a20',highlightthickness=0);self.canvas.pack(fill='x',padx=10)
        self.info=tk.Text(win,height=10,wrap='word',bg='#1b2027',fg='#d8dde5',insertbackground='white');self.info.pack(fill='both',expand=True,padx=10,pady=6)
        self.status=tk.StringVar(value='Prepare a comparison; no project layer has changed.');ttk.Label(win,textvariable=self.status,wraplength=930,padding=6).pack(fill='x')
        self.accept_button=ttk.Button(win,text='Apply reviewed source to selected layer',command=self.accept);self.accept_button.pack(fill='x',padx=10,pady=8)
        self.sync();win.after(100,self.poll)

    def sync(self):
        for name,b in self.buttons.items():b.state(['disabled'] if self.busy or ('Play' in name and self.report is None) else ['!disabled'])
        self.accept_button.state(['!disabled'] if self.report and not self.busy else ['disabled'])

    def invalidate(self):
        self.revision+=1
        self.report=None
        if hasattr(self,'accept_button'):self.sync();self.status.set('Settings changed; prepare a new comparison before Apply.')

    def prepare(self):
        if self.busy:return
        try:
            start=self.fields['start'].get().strip();end=self.fields['end'].get().strip()
            if bool(start)!=bool(end):raise ValueError('Provide both trim endpoints or leave both blank')
            options={'trim':[int(start),int(end)] if start else None,'crossfade':int(self.fields['crossfade'].get()),'gain_db':float(self.fields['gain_db'].get()),'remove_dc':self.dc.get(),'use_source_loop':self.loop.get(),'source_evidence':self.evidence}
        except Exception as exc:self.status.set(str(exc));return
        self.busy=True;self.report=None;self.sync();self.status.set('Decoding and compiling existing native resource format…')
        revision=self.revision
        def worker():
            try:self.queue.put((revision,True,self.project.audio_prepare_import(self.path,**options)))
            except Exception as exc:self.queue.put((revision,False,str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def poll(self):
        if not self.window.winfo_exists():return
        try:
            revision,okay,value=self.queue.get_nowait();self.busy=False
            if revision!=self.revision:
                self.report=None;self.status.set('Settings changed during decoding; prepare again before Apply.');self.sync();self.window.after(100,self.poll);return
            if okay:
                self.report=value;detail={k:value[k] for k in ('original_sha256','decoded_sha256','native_sha256','media','source','loop_endpoint_jump_pcm16','decoded_full_scale_samples','decoder_clipping_boundary','source_evidence','boundary')}
                detail['native_levels']={k:value['compiler'][k] for k in ('output_format','peak_pcm16','rms_pcm16')}
                self.info.configure(state='normal');self.info.delete('1.0','end');self.info.insert('end',json.dumps(detail,indent=2));self.info.configure(state='disabled');self.draw_wave()
                self.status.set('Comparison ready. Source = decoded/downmixed excerpt, no authored gain/DC/crossfade. Converted = exact compiler WAV. '+('Loop seam warning; audition/crossfade recommended.' if value['loop_endpoint_jump_pcm16']>2048 and not value['source']['crossfade_frames'] else ''))
            else:self.status.set(value)
            self.sync()
        except queue.Empty:pass
        self.window.after(100,self.poll)

    def draw_wave(self):
        from master_rallye.addon_sdk.audio_profile import decode_pcm
        c=self.canvas;c.delete('all');width=max(850,c.winfo_width());height=120
        for index,(name,color) in enumerate([('original-preview.wav','#82919e'),('converted.wav','#e5b56a')]):
            samples,_=decode_pcm((Path(self.report['preview_root'])/name).read_bytes());step=max(1,len(samples)//int(width));points=[]
            for i in range(0,len(samples),step):points.extend((i/len(samples)*width,30+index*60-samples[i]/32768*24))
            if len(points)>=4:c.create_line(*points,fill=color)
            c.create_text(8,12+index*60,text=name,fill=color,anchor='w')

    def listen(self,name):
        if self.report and not self.busy:play(Path(self.report['preview_root'])/name)

    def accept(self):
        if not self.report or self.busy:return
        if self.app.project is None or self.app.project.root!=self.project.root:self.status.set('Active vehicle changed. Reopen this import for the intended vehicle.');return
        p=self.project;report=self.report;layer=self.layer.get();self.close();self.app.audio_action('Apply reviewed Audio Import 2.0 source',lambda:p.audio_apply_import(report,layer))

    def close(self):
        play();self.window.destroy()
