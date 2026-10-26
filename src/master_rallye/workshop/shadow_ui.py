"""Shadow Studio: explicit native bounds authoring with honest diagnostic guides."""
import json
import subprocess
import tkinter as tk
from tkinter import ttk
from .branding import apply_icon
from .shadow import CONTROLS


class ShadowPanels:
    def open_shadow_studio(self):
        if not self.project:return
        if getattr(self,'shadow_window',None) and self.shadow_window.winfo_exists():
            self.shadow_window.destroy()
        owner=self.project
        w=tk.Toplevel(self.root);self.shadow_window=w;apply_icon(w)
        w.title('Rally Workshop — Shadow Studio');w.geometry('980x800');w.minsize(760,660)
        ttk.Label(w,text=owner.data['identity']+' · CarID '+str(owner.data['car_id']),padding=10).pack(fill='x')
        row=ttk.Frame(w,padding=6);row.pack(fill='x')
        def owned(command):
            if self.project is owner and getattr(self,'shadow_window',None)is w and w.winfo_exists():command()
        for label,command in [('Save',self.save),('Undo',self.undo),('Redo',self.redo),('Validate',self.validate),('Build',self.build),('Help',lambda:self.show_help('shadows'))]:
            ttk.Button(row,text=label,command=lambda action=command:owned(action)).pack(side='left')
        fields=ttk.Frame(w,padding=8);fields.pack(fill='x');self.shadow_fields={}
        for i,(key,value) in enumerate(CONTROLS.items()):
            ttk.Label(fields,text=key).grid(row=i//2,column=(i%2)*2,sticky='w',padx=8,pady=3)
            v=tk.StringVar(value=str(value));self.shadow_fields[key]=v
            ttk.Entry(fields,textvariable=v,width=14).grid(row=i//2,column=(i%2)*2+1,sticky='ew',padx=8)
        fields.columnconfigure(1,weight=1);fields.columnconfigure(3,weight=1)
        self.shadow_canvas=tk.Canvas(w,height=240,bg='#191d23',highlightthickness=0);self.shadow_canvas.pack(fill='both',expand=True,padx=10)
        ttk.Label(w,text='Top: body amber · Original/native red · Selected green. X right / Z up; metres.\nAlpha threshold selects texture support for bounds calculation; does not change shadow opacity.',wraplength=900,padding=8).pack(fill='x')
        self.shadow_note=tk.Text(w,height=7,bg='#191d23',fg='#d5dae0',wrap='word');self.shadow_note.pack(fill='x',padx=10)
        actions=ttk.Frame(w,padding=8);actions.pack(fill='x')
        def invoke(mode=None):
            if self.project is not owner:
                self.shadow_note.insert('end','\nProject changed; reopen Shadow Studio.');return
            # Tk variables belong to the UI thread. Parse in the worker only
            # after taking an immutable text snapshot here.
            snapshot={k:v.get() for k,v in self.shadow_fields.items()} if mode=='custom' else {}
            def work():
                if mode is None:return owner.shadow_calculate()
                values={k:int(v) if k=='alpha_threshold' else float(v) for k,v in snapshot.items()}
                return owner.shadow_update(mode,**values)
            def shown(report):
                if self.project is owner and getattr(self,'shadow_window',None)is w and w.winfo_exists():self.shadow_show(report)
            self.run('Shadow '+str(mode or 'inspect'),work,shown)
        for label,mode in [('Inspect current',None),('Original native','original'),('Auto Fit','auto'),('Apply Custom','custom'),('Reset donor','donor')]:
            ttk.Button(actions,text=label,command=lambda m=mode:invoke(m)).pack(side='left',expand=True,fill='x')
        def preview():
            if self.project is not owner:return
            def opened(result):
                if self.project is not owner or getattr(self,'shadow_window',None)is not w or not w.winfo_exists():return
                scene,_=result
                self.shadow_process=subprocess.Popen([str(self.viewer),'--scene',str(scene),'--model','race','--preset','5','--workshop'])
            self.run('Export shadow guides',owner.shadow_preview_export,opened)
        ttk.Button(w,text='Open D3D9 top-down / ground guides',command=preview).pack(fill='x',padx=8,pady=7)
        self.shadow_canvas.bind('<Configure>',lambda _:self.shadow_draw())
        self.shadow_report=None;invoke()

    def shadow_show(self,report):
        if not self.shadow_window.winfo_exists():return
        self.shadow_report=report
        for k,v in self.shadow_fields.items():v.set(str(report['profile'][k]))
        self.shadow_note.delete('1.0','end');self.shadow_note.insert('end',json.dumps({k:report[k] for k in ('mode','enabled','body_bounds_xz_m','generated_alpha_support_xz_m','generated_quad_size_xz_m','texture_alpha_support_uv','evidence','preview')},indent=2))
        self.shadow_draw()

    def shadow_draw(self):
        report=getattr(self,'shadow_report',None)
        if not report:return
        c=self.shadow_canvas;c.delete('all');w,h=max(1,c.winfo_width()),max(1,c.winfo_height())
        keys=('body_bounds_xz_m','native_alpha_support_xz_m','generated_alpha_support_xz_m')
        boxes=[report[k] for k in keys];lo=[min(b[0][i] for b in boxes) for i in range(2)];hi=[max(b[1][i] for b in boxes) for i in range(2)]
        scale=min((w-40)/(hi[0]-lo[0]),(h-30)/(hi[1]-lo[1]));cx=(lo[0]+hi[0])/2;cz=(lo[1]+hi[1])/2
        for b,color in zip(boxes,('#e8b257','#ed6666','#70df87')):
            c.create_rectangle(w/2+(b[0][0]-cx)*scale,h/2-(b[1][1]-cz)*scale,w/2+(b[1][0]-cx)*scale,h/2-(b[0][1]-cz)*scale,outline=color,width=2)
