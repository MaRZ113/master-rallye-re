"""Frontend framing controls; live drafts never mutate gameplay or saved data."""
import json,subprocess
import tkinter as tk
from tkinter import ttk,messagebox
from .branding import apply_icon

class FrontendPanels:
    def open_frontend_presentation(self):
        if not self.project or self.busy:return
        old=getattr(self,'frontend_window',None)
        if old is not None and old.winfo_exists():old.destroy()
        owner=self.project;win=tk.Toplevel(self.root);apply_icon(win);win.title('Rally Workshop — Frontend Presentation');win.geometry('1040x780');self.frontend_window=win
        ttk.Label(win,text='Large VehicleSelect 3D model · NOT icons or gameplay camera\nVertical correction lowers the private camera target, raising the car. Source geometry and physics remain unchanged.\nD3D9 approximation; full viewport bounds checked. Panel margins are illustrative until owner D3D8 comparison.',padding=10).pack(fill='x')
        row=ttk.Frame(win,padding=8);row.pack(fill='x');value=tk.StringVar();view=tk.StringVar(value='modified');status=tk.StringVar()
        ttk.Label(row,text='Vertical presentation offset (m, ±1.5)').pack(side='left');ttk.Entry(row,textvariable=value,width=12).pack(side='left',padx=8);ttk.Combobox(row,textvariable=view,values=['original','modified','stock NewRav'],state='readonly',width=12).pack(side='left')
        self.frontend_offset=value;self.frontend_view=view
        diagram=tk.Canvas(win,width=640,height=240,bg='#202732',highlightthickness=0);diagram.pack(fill='x',padx=10)
        note=tk.Text(win,height=12,bg='#191d23',fg='#d5dae0');note.pack(fill='both',expand=True,padx=10);ttk.Label(win,textvariable=status,padding=8,wraplength=1000).pack(fill='x')
        session={'process':None,'revision':0,'job':None,'loading':False};self.frontend_session=session
        def current():return self.project is owner and win.winfo_exists()
        def shown(report):
            if not current():return
            session['loading']=True;value.set(str(report['profile']['vertical_offset_m']));session['loading']=False
            note.delete('1.0','end');note.insert('end',json.dumps(report,indent=2));draw(report);live()
        def draw(report):
            diagram.delete('all');w=640;h=240
            diagram.create_rectangle(1,1,w-1,h-1,outline='#ffb648');diagram.create_rectangle(w*.38,h*.53,w*.92,h*.9,outline='#647387',dash=(4,4));diagram.create_text(8,12,anchor='w',text='Full native viewport / dashed presentation area illustrative',fill='#d5dae0')
            for key,color in [('original','#8595a8'),('modified','#ffb648')]:
                b=report[key]['ndc'];lo,hi=b['minimum'],b['maximum'];diagram.create_rectangle((lo[0]+1)*w/2,(1-hi[1])*h/2,(hi[0]+1)*w/2,(1-lo[1])*h/2,outline=color,width=2)
            status.set('Draft only until Apply · positive offset raises model · '+('CLIPPING WARNING'if report['modified']['clipped']else'Full viewport bounds clear'))
        def inspect():
            if current():self.run('Inspect frontend presentation',owner.frontend_inspect,shown)
        def live(*_):
            if not current()or session['loading']:return
            from .camera_live import packet,send
            from master_rallye.frontend_presentation import pose
            try:
                offset=float(value.get())if view.get()=='modified'else 0.
                if not -1.5<=offset<=1.5:return
                session['revision']+=1;send(session['process'],packet(pose(offset),mode=4,revision=session['revision'],aspect=4/3,editable=False))
            except(ValueError,tk.TclError):pass
        def apply():
            if not current()or self.busy:return
            try:draft=float(value.get())
            except ValueError:messagebox.showerror('Frontend offset','Enter a finite number in ±1.5 m',parent=win);return
            self.run('Apply frontend-only correction',lambda:(owner.frontend_update(draft),owner.frontend_inspect())[1],shown)
        def auto():
            if current()and not self.busy:self.run('Match NewRav source baseline',owner.frontend_auto_frame,lambda v:(value.set(str(v)),live(),status.set('NewRav baseline draft; Apply required')))
        def reset():
            if current()and not self.busy:self.run('Reset original frontend',lambda:(owner.frontend_update(0.),owner.frontend_inspect())[1],shown)
        def history(redo=False):
            if current()and not self.busy:self.run('Frontend history',lambda:((owner.redo if redo else owner.undo)(),owner.frontend_inspect())[1],shown)
        def preview():
            if not current()or self.busy:return
            selected=view.get()
            try:draft=float(value.get())
            except ValueError:messagebox.showerror('Frontend offset','Enter a finite number in ±1.5 m',parent=win);return
            def launch(v):
                if not current():return
                close_process();p=v['pose'];args=[str(self.viewer),'--scene',v['scene'],'--source',v['source'],'--profile',v['preview_profile'],'--python',__import__('sys').executable,'--model','frontend','--frontend-presentation','--game-camera',*map(str,p['eye']),*map(str,p['target']),str(p['source_fov_degrees']),'--camera-state',str(owner.root/'preview/frontend/live.json'),'--camera-read-only','--game-mode','4','--camera-aspect',str(4/3),'--workshop'];session['process']=subprocess.Popen(args);session['revision']=0;win.after(600,live)
            self.run('Stage native frontend pose',lambda:owner.frontend_export(view=selected,offset=draft),launch)
        def close_process():
            p=session['process']
            if p is not None and p.poll()is None:p.terminate();p.wait(timeout=5)
            session['process']=None
        def close():close_process();win.destroy()
        row=ttk.Frame(win,padding=8);row.pack(fill='x')
        for label,command in [('Inspect / cancel draft',inspect),('Auto Frame · NewRav',auto),('Live 3D Preview',preview),('Apply',apply),('Reset original',reset),('Undo',history),('Redo',lambda:history(True)),('Save',lambda:owner.save()if current()and not self.busy else None),('Build',lambda:self.build()if current()else None)]:ttk.Button(row,text=label,command=command).pack(side='left')
        from .ui_actions import flow
        flow(row)
        self.frontend_actions={'inspect':inspect,'auto':auto,'preview':preview,'apply':apply,'reset':reset,'undo':history,'redo':lambda:history(True),'close':close}
        win.bind('<Destroy>',lambda e:close_process()if e.widget is win else None)
        value.trace_add('write',live);view.trace_add('write',live);win.protocol('WM_DELETE_WINDOW',close);inspect()
