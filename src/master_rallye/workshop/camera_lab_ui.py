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
        ttk.Label(win,text='Static first-update camera pose: original x86 replay qualified under controlled flat target inputs.\nDynamics / acceleration / terrain / pitch history / final D3D8 projection remain approximate or unknown.\nFollow extents are inputs to the native calculation, NOT direct camera distance or height.',padding=8,wraplength=1020).pack(fill='x')
        row=ttk.Frame(win,padding=8);row.pack(fill='x');preset=tk.StringVar(value='0');view=tk.StringVar(value='modified');split=tk.BooleanVar(value=False)
        self.camera_lab_view=view;self.camera_lab_preset=preset;self.camera_lab_split=split
        ttk.Label(row,text='Native follow array index').pack(side='left');ttk.Combobox(row,textvariable=preset,values=['0','1','2'],width=4,state='readonly').pack(side='left')
        ttk.Checkbutton(row,text='Source split-screen parameters (static only)',variable=split).pack(side='left',padx=5)
        ttk.Combobox(row,textvariable=view,values=['original','donor','modified'],width=12,state='readonly').pack(side='left')
        fields=ttk.Frame(win,padding=8);fields.pack(fill='x');half=tk.StringVar();height=tk.StringVar()
        self.camera_lab_fields={'half_length_m':half,'height_m':height}
        for label,value in [('Native follow half-length input (m)',half),('Native height extent input (m)',height)]:ttk.Label(fields,text=label).pack(side='left');ttk.Entry(fields,textvariable=value,width=12).pack(side='left',padx=5)
        note=tk.Text(win,height=19,wrap='word',bg='#191d23',fg='#d5dae0');note.pack(fill='both',expand=True,padx=8);result={}
        def current():return self.project is owner and win.winfo_exists()
        def shown(report):
            if not current():return
            result.clear();result.update(report);half.set(str(report['identity']['current']['half_length_m']));height.set(str(report['identity']['current']['height_m']))
            note.configure(state='normal');note.delete('1.0','end');note.insert('end',json.dumps(report,indent=2));note.configure(state='disabled')
        # Freeze all Tk values before worker threads; changing projects invalidates callbacks.
        def inspect():
            if not current():return
            index=int(preset.get());spl=split.get();self.run('Inspect native camera inputs',lambda:owner.camera_lab_inspect(index,spl),shown)
        def edit(mode):
            if not current()or self.busy:return
            values=(half.get(),height.get())
            def work():
                if mode=='custom':owner.camera_update(float(values[0]),float(values[1]))
                elif mode=='donor':owner.vehicle_reset('camera')
                else:owner.camera_reset_original()
                return owner.camera_lab_inspect(int(index),spl)
            index=preset.get();spl=split.get();self.run('Camera '+mode,work,shown)
        def history(redo=False):
            if not current()or self.busy:return
            index=int(preset.get());spl=split.get()
            def work():
                (owner.redo if redo else owner.undo)();return owner.camera_lab_inspect(index,spl)
            self.run('Camera history',work,shown)
        footer=ttk.Frame(win);footer.pack(side='bottom',fill='x',before=note)
        actions=ttk.Frame(footer,padding=8);actions.pack(fill='x')
        for label,command in [('Inspect / compare',inspect),('Apply qualified extents',lambda:edit('custom')),('Reset original native',lambda:edit('original')),('Reset donor',lambda:edit('donor')),('Save',lambda:owner.save() if current()and not self.busy else None),('Undo',history),('Redo',lambda:history(True))]:ttk.Button(actions,text=label,command=command).pack(side='left')
        picture=ttk.Label(footer);picture.pack(fill='x',pady=5)
        def export(free=False,capture=False):
            if not current()or self.busy:return
            selection=view.get();index=int(preset.get());spl=split.get()
            def work():
                value=owner.camera_lab_export(view=selection,preset=index,split=spl)
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
                    self.game_camera_process=subprocess.Popen(value['args']+['--workshop'])
            self.run('Stage synchronized camera / wheels',work,rendered)
        views=ttk.Frame(footer,padding=8);views.pack(fill='x')
        for label,command in [('Gameplay Camera Preview',lambda:export()),('Free Inspection + camera/frustum guides',lambda:export(True)),('Capture selected view',lambda:export(capture=True)),('Build isolated candidate',lambda:self.build()if current()else None)]:ttk.Button(views,text=label,command=command).pack(side='left')
        inspect()

    def close_camera_lab_preview(self):
        process=getattr(self,'game_camera_process',None)
        if process is not None and process.poll()is None:process.terminate()
        self.game_camera_process=None
