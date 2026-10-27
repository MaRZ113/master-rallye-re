"""Gameplay Camera Lab UI over the shared source-qualified camera service."""
import json,subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from .branding import apply_icon


class CameraLabPanels:
    def open_camera_lab(self):
        if not self.project or self.busy:return
        previous=getattr(self,'camera_lab_window',None)
        if previous is not None and previous.winfo_exists():
            if getattr(self,'camera_lab_owner',None)is self.project:previous.lift();return
            previous.destroy()
        owner=self.project;win=tk.Toplevel(self.root);apply_icon(win);win.title('Rally Workshop — Game Camera Lab');win.geometry('1080x850')
        self.camera_lab_window=win;self.camera_lab_owner=owner
        header=ttk.Frame(win,padding=8);header.pack(fill='x');ttk.Label(header,text=owner.data['identity']+' · Game Camera Lab').pack(side='left')
        ttk.Button(header,text='Help / evidence levels',command=lambda:self.show_help('game-camera')).pack(side='right')
        ttk.Label(win,text='Five real views: Follow0–2, Fixed0–1. Static flat poses and source FOV/aspect arithmetic checked against original x86.\nDynamics, terrain, pitch history and final D3D8 presentation remain pending. Mode overrides affect normal AND split.\nFollow extents remain separate model inputs. Fixed offsets are initialized by native model bounds and stay read-only.',padding=8,wraplength=1020).pack(fill='x')
        row=ttk.Frame(win,padding=8);row.pack(fill='x');preset=tk.StringVar(value='0');view=tk.StringVar(value='modified');split=tk.BooleanVar(value=False)
        self.camera_lab_view=view;self.camera_lab_preset=preset;self.camera_lab_split=split
        ttk.Label(row,text='Game mode: 0–2 Follow, 3–4 Fixed').pack(side='left');ttk.Combobox(row,textvariable=preset,values=['0','1','2','3','4'],width=4,state='readonly').pack(side='left')
        ttk.Checkbutton(row,text='Source split-screen parameters (static only)',variable=split).pack(side='left',padx=5)
        ttk.Combobox(row,textvariable=view,values=['original','donor','modified'],width=12,state='readonly').pack(side='left')
        fields=ttk.Frame(win,padding=8);fields.pack(fill='x');half=tk.StringVar();height=tk.StringVar()
        self.camera_lab_fields={'half_length_m':half,'height_m':height}
        for label,value in [('Native follow half-length input (m)',half),('Native height extent input (m)',height)]:ttk.Label(fields,text=label).pack(side='left');ttk.Entry(fields,textvariable=value,width=12).pack(side='left',padx=5)
        live=ttk.LabelFrame(win,text='Live native camera draft · normal AND split scope · Apply saves / Cancel discards',padding=7);live.pack(fill='x',padx=8)
        draft={name:tk.StringVar()for name in ('FOV','Dist Front','Dist Back','Dist Up')};entries={};aspect=tk.StringVar(value='Window')
        for name,value in draft.items():
            ttk.Label(live,text=name).pack(side='left');entries[name]=ttk.Entry(live,textvariable=value,width=8);entries[name].pack(side='left',padx=3)
        ttk.Combobox(live,textvariable=aspect,values=['Window','4:3','16:9','16:10','32:9'],state='readonly',width=8).pack(side='left')
        self.camera_live_fields=draft;self.camera_live_aspect=aspect
        compose=ttk.Frame(win,padding=(8,3));compose.pack(fill='x');auto_frame=tk.BooleanVar(value=True);framing_note=tk.StringVar(value='Preview-only drafts; Original retains exact source framing.')
        ttk.Checkbutton(compose,text='Auto-frame Follow draft (unsaved)',variable=auto_frame).pack(side='left');ttk.Label(compose,textvariable=framing_note).pack(side='left',padx=8)
        note=tk.Text(win,height=14,wrap='word',bg='#191d23',fg='#d5dae0');note.pack(fill='both',expand=True,padx=8);result={};session={'revision':0,'gesture':0,'job':None,'loading':False,'path':None}
        def current():return self.project is owner and win.winfo_exists()
        def shown(report):
            if not current():return
            if report['mode']['id']!=int(preset.get())or report['split']!=split.get():win.after(100,inspect);return
            result.clear();result.update(report);half.set(str(report['identity']['current']['half_length_m']));height.set(str(report['identity']['current']['height_m']))
            if session.get('bounds'):result['preview_bounds']=session['bounds']
            note.configure(state='normal');note.delete('1.0','end');note.insert('end',json.dumps(report,indent=2));note.configure(state='disabled')
            load_draft()
            if session['path']and auto_frame.get():frame_draft()
        # Freeze all Tk values before worker threads; changing projects invalidates callbacks.
        def inspect():
            if not current():return
            index=int(preset.get());spl=split.get();self.run('Inspect native camera inputs',lambda:owner.camera_lab_inspect(split=spl,mode=index),shown)
        def edit(mode):
            if not current()or self.busy:return
            values=(half.get(),height.get())
            def work():
                if mode=='custom':owner.camera_update(float(values[0]),float(values[1]))
                elif mode=='donor':owner.vehicle_reset('camera')
                else:owner.camera_reset_original()
                return owner.camera_lab_inspect(split=spl,mode=int(index))
            index=preset.get();spl=split.get();self.run('Camera '+mode,work,shown)
        def history(redo=False):
            if not current()or self.busy:return
            index=int(preset.get());spl=split.get()
            def work():
                (owner.redo if redo else owner.undo)();return owner.camera_lab_inspect(split=spl,mode=index)
            self.run('Camera history',work,shown)
        footer=ttk.Frame(win);footer.pack(side='bottom',fill='x',before=note)
        actions=ttk.Frame(footer,padding=8);actions.pack(fill='x')
        for label,command in [('Inspect / compare',inspect),('Apply qualified extents',lambda:edit('custom')),('Reset original native',lambda:edit('original')),('Reset donor',lambda:edit('donor')),('Save',lambda:owner.save() if current()and not self.busy else None),('Undo',history),('Redo',lambda:history(True))]:ttk.Button(actions,text=label,command=command).pack(side='left')
        picture=ttk.Label(footer);picture.pack(fill='x',pady=5)
        def export(free=False,capture=False,live_session=False):
            if not current()or self.busy:return
            selection=view.get();index=int(preset.get());spl=split.get()
            def work():
                value=owner.camera_lab_export(view=selection,split=spl,mode=index)
                pose=value['pose'];args=[str(self.viewer),'--scene',value['scene'],'--source',value['source'],'--model','race','--game-camera',*map(str,pose['eye']),*map(str,pose['target']),str(pose['source_fov_degrees'])]
                if free:args+=['--free-inspection','--preset','4','--zoom','.45']
                if capture:
                    target=Path(value['scene']).parent/('free.bmp'if free else'gameplay.bmp');args+=['--capture',str(target)]
                    si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
                    subprocess.run(args,startupinfo=si,check=True,timeout=60)
                    value['capture']=str(target)
                value['args']=args;return value
            def rendered(value):
                if not current():return
                if capture:
                    from PIL import Image,ImageTk
                    with Image.open(value['capture'])as im:
                        im.thumbnail((700,250));picture.photo=ImageTk.PhotoImage(im);picture.configure(image=picture.photo)
                else:
                    self.close_camera_lab_preview()
                    session['path']=None
                    args=value['args']+['--workshop']
                    if live_session:
                        import uuid
                        path=Path(value['scene']).parent/('live-'+uuid.uuid4().hex+'.json');session.update(path=path,revision=0,gesture=0)
                        args+=['--camera-state',str(path),'--game-mode',str(index)]
                        if selection!='modified':args+=['--camera-read-only']
                        session['bounds']=value['report']['preview_bounds'];result['preview_bounds']=session['bounds']
                    self.game_camera_process=subprocess.Popen(args)
                    session['process']=self.game_camera_process
                    if live_session and auto_frame.get():frame_draft()
            self.run('Stage synchronized camera / wheels',work,rendered)
        views=ttk.Frame(footer,padding=8);views.pack(fill='x')
        for label,command in [('Gameplay Camera Preview',lambda:export()),('Free Inspection + camera/frustum guides',lambda:export(True)),('Capture selected view',lambda:export(capture=True)),('Build isolated candidate',lambda:self.build()if current()else None)]:ttk.Button(views,text=label,command=command).pack(side='left')
        def values():return {name:float(draft[name].get())for name in result['mode']['native_editable']}
        def update_live(capture=False):
            if not current()or not result or not session['path']:return False
            if result['mode']['id']!=int(preset.get())or result['split']!=split.get():return False
            from .camera_live import packet,send,draft_pose
            try:
                selection=view.get();pose=draft_pose(result,values(),selection);a=aspect.get();ratio=0. if a=='Window'else float(a.split(':')[0])/float(a.split(':')[1])
                bounds=result.get('preview_bounds');height_above=pose['eye'][1]-(bounds['minimum'][1]-.02)if bounds else None
                if height_above is not None:framing_note.set(f'Eye {height_above:.2f} m above illustrative rest-pose ground · Apply required')
                session['revision']+=1
                return send(getattr(self,'game_camera_process',None),packet(pose,mode=int(preset.get()),revision=session['revision'],aspect=ratio,capture=capture,editable=selection=='modified'))
            except(ValueError,KeyError,tk.TclError):return False
        def schedule(*args):
            if session['loading']or not current():return
            if session['job']:win.after_cancel(session['job'])
            session['job']=win.after(70,lambda:(session.update(job=None),update_live()))
        def load_draft(*args):
            if not result or not current():return
            session['loading']=True
            for name,value in draft.items():
                value.set(str(result['parameters'][view.get()].get(name,'')))
                entries[name].configure(state='normal'if name in result['mode']['native_editable']and view.get()=='modified'else'readonly')
            session['loading']=False;schedule()
        def frame_draft():
            if not current()or not result or result['mode']['kind']!='follow'or view.get()!='modified':return
            from .camera_live import fit_follow_draft
            try:
                a=aspect.get();ratio=16/9 if a=='Window'else float(a.split(':')[0])/float(a.split(':')[1]);fields=fit_follow_draft(result,values(),ratio)
                session['loading']=True
                for name,value in fields.items():draft[name].set(f'{value:.6g}')
                session['loading']=False;schedule()
            except(ValueError,KeyError):session['loading']=False
        def apply_draft():
            if not current()or self.busy or view.get()!='modified':return
            try:fields=values()
            except ValueError:return
            index=int(preset.get());spl=split.get()
            def work():owner.camera_mode_update(index,fields);return owner.camera_lab_inspect(split=spl,mode=index)
            self.run('Apply native camera mode draft',work,shown)
        def reset_mode():
            if not current()or self.busy:return
            index=int(preset.get());spl=split.get()
            def work():owner.camera_mode_update(index,{});return owner.camera_lab_inspect(split=spl,mode=index)
            self.run('Reset selected native camera mode',work,shown)
        def poll():
            if not current():return
            path=session['path'];process=getattr(self,'game_camera_process',None)
            if path and process is not None and process.poll()is None:
                if not path.exists():update_live()
                else:
                    try:
                        feedback=json.loads(path.read_text());gesture=feedback['gesture']
                        if feedback['revision']==session['revision']and gesture>session['gesture']and feedback['mode']==int(preset.get())and view.get()=='modified':
                            session['gesture']=gesture;session['loading']=True;draft['FOV'].set(str(feedback['source_fov_degrees']))
                            if result['mode']['kind']=='follow':
                                ext=result['identity']['current'];draft['Dist Front'].set(str(feedback['target'][2]));draft['Dist Back'].set(str(-feedback['eye'][2]-ext['half_length_m']));draft['Dist Up'].set(str(feedback['eye'][1]-ext['height_m']))
                            session['loading']=False
                    except(OSError,ValueError,KeyError):session['loading']=False
            session['poll_job']=win.after(100,poll)
        for value in draft.values():value.trace_add('write',schedule)
        aspect.trace_add('write',schedule);view.trace_add('write',load_draft)
        preset.trace_add('write',lambda *a:inspect()if not self.busy else None);split.trace_add('write',lambda *a:inspect()if not self.busy else None)
        live_actions=ttk.Frame(footer,padding=8);live_actions.pack(fill='x')
        for label,command in [('Open Live Preview',lambda:export(live_session=True)),('Frame car (draft)',frame_draft),('Apply Live Draft',apply_draft),('Cancel Live Draft',load_draft),('Capture Live View',lambda:update_live(True))]:ttk.Button(live_actions,text=label,command=command).pack(side='left')
        ttk.Label(live_actions,text='LMB eye · Ctrl+LMB target · wheel FOV; flat static only').pack(side='left',padx=6)
        ttk.Button(compose,text='Reset selected mode',command=reset_mode).pack(side='right')
        def closed():
            if getattr(self,'camera_lab_owner',None)is owner:self.close_camera_lab_preview()
            win.destroy()
        def destroyed(event):
            if event.widget is not win:return
            for key in ('job','poll_job'):
                if session.get(key):
                    try:win.after_cancel(session[key])
                    except tk.TclError:pass
            if session.get('process')is getattr(self,'game_camera_process',None):self.close_camera_lab_preview()
        win.bind('<Destroy>',destroyed,add='+');win.protocol('WM_DELETE_WINDOW',closed);session['poll_job']=win.after(100,poll)
        inspect()

    def close_camera_lab_preview(self):
        process=getattr(self,'game_camera_process',None)
        if process is not None and process.poll()is None:
            process.terminate()
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        self.game_camera_process=None
