"""Fixed Results label authoring over existing identity and UI-frame Core."""
from tkinter import ttk
import tkinter as tk
from PIL import Image,ImageDraw,ImageFont,ImageTk


class ResultsPanels:
    def results_layout(self,parent):
        box=ttk.LabelFrame(parent,text='Driver / Results Name · fixed vehicle presentation',padding=8);box.pack(fill='x',pady=6)
        ttk.Label(box,text='Uses the field above. This changes the fixed Results label, not AI DriverID, behavior or the vehicle model name.\nHuman/network participant names retain their native paths.',wraplength=930).pack(fill='x')
        self.results_picture=ttk.Label(box);self.results_picture.pack(fill='x',pady=6);self.results_status=tk.StringVar();ttk.Label(box,textvariable=self.results_status,wraplength=930).pack(fill='x')
        row=ttk.Frame(box);row.pack(fill='x',pady=4)
        def apply():
            owner=self.project;value=self.details_fields['display_name'].get();self.vehicle_action('Apply fixed Results Name',lambda:owner.results_name_update(value))
        def restore():
            owner=self.project;self.vehicle_action('Restore fixed Results Name',owner.results_name_reset)
        for label,command in [('Apply Results Name',apply),('Undo',self.undo),('Redo',self.redo),('Restore Results Name',restore)]:ttk.Button(row,text=label,command=command).pack(side='left')
        self._results_icon=None;self.details_fields['display_name'].trace_add('write',lambda *_:self.results_preview())

    def results_refresh(self):
        if not getattr(self,'results_picture',None):return
        try:
            info=self.project.results_name_preview();self._results_icon=Image.open(info['png']).convert('RGBA');self._results_info=info;self.results_preview()
        except(ValueError,KeyError,OSError)as exc:
            self._results_icon=None;self.results_picture.configure(image='');self.results_status.set(str(exc))

    def results_preview(self):
        if getattr(self,'_results_icon',None)is None:return
        value=self.details_fields['display_name'].get();image=Image.new('RGB',(900,62),'#26313e');draw=ImageDraw.Draw(image)
        try:font=ImageFont.truetype('segoeui.ttf',18)
        except OSError:font=ImageFont.load_default()
        draw.line((0,60,900,60),fill='#e5b56a',width=2);draw.text((12,20),'1',font=font,fill='#e5b56a');icon=self._results_icon.resize((64,32),Image.Resampling.NEAREST);image.paste(icon,(45,14),icon)
        draw.text((126,20),value,font=font,fill='#f1f2f5');draw.text((782,20),'00:00.00',font=font,fill='#d0d5dd')
        self.results_photo=ImageTk.PhotoImage(image);self.results_picture.configure(image=self.results_photo)
        self.results_status.set(f"Existing32×16 icon, frame {self._results_info['frame']} · draft until Apply · {len(value)}/64 ASCII characters.\nRow layout/font is illustrative; icon bytes come from the actual SDK Results resource.")
