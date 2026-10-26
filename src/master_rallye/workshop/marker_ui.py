"""Small Race HUD authoring panel; all persistence stays in SDK Core."""
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk,colorchooser
from PIL import Image,ImageDraw,ImageTk
from .race_marker import PRESETS,tinted_marker,normalized_rgb


class MarkerPanels:
    def marker_layout(self,parent):
        box=ttk.LabelFrame(parent,text='Race HUD / Progress Marker Color',padding=8);box.pack(fill='x',pady=6)
        self.marker_hex=tk.StringVar();self.marker_status=tk.StringVar()
        row=ttk.Frame(box);row.pack(fill='x');ttk.Entry(row,textvariable=self.marker_hex,width=10).pack(side='left')
        def choose():
            value=colorchooser.askcolor(color=self.marker_hex.get()or'#FFFFFF',parent=self.vehicle_window)[1]
            if value:self.marker_hex.set(value);self.marker_preview()
        ttk.Button(row,text='Pick marker RGB…',command=choose).pack(side='left')
        palette=ttk.Combobox(row,values=list(PRESETS),state='readonly',width=12);palette.pack(side='left',padx=5)
        palette.bind('<<ComboboxSelected>>',lambda _:(self.marker_hex.set(PRESETS[palette.get()]),self.marker_preview()))
        ttk.Button(row,text='Preview marker tint',command=self.marker_preview).pack(side='left')
        def apply():
            owner=self.project;value=self.marker_hex.get();self.vehicle_action('Apply Race Progress Marker RGB',lambda:owner.marker_update(value))
        ttk.Button(row,text='Apply marker color',command=apply).pack(side='left')
        def reset():
            owner=self.project;self.vehicle_action('Restore Race HUD color',lambda:owner.vehicle_reset('race_marker'))
        ttk.Button(row,text='Reset marker color',command=reset).pack(side='left')
        self.marker_picture=ttk.Label(box);self.marker_picture.pack(fill='x',pady=5)
        ttk.Label(box,textvariable=self.marker_status,wraplength=900).pack(fill='x')
        self.marker_hex.trace_add('write',lambda *_:self.marker_preview())

    def marker_refresh(self):
        if not getattr(self,'marker_picture',None):return
        if self.project.data['kind']!='addon':
            self.marker_status.set('Stock registration color is read-only. Addon per-CarID marker authoring only.');self.marker_picture.configure(image='');return
        self.marker_hex.set(self.project.marker_inspect()['current']['hex'])

    def marker_preview(self):
        try:
            from io import BytesIO
            from master_rallye.dxt import parse_dxt_bytes,encode_png
            p=self.project;info=p.marker_inspect();candidate=[*normalized_rgb(self.marker_hex.get()),info['original']['rgba'][3]]
            path=Path(p.data['build_settings']['retail_root'])/'DataGx/Hud/hud-template_003_000.dxt'
            if path.exists():
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()!='2485192edf007f5dc97a455be87ae8f6b18c01719da4c7b4d60f396c577ade93':raise ValueError('Local HUD marker source differs from qualified stock art')
                source=Image.open(BytesIO(encode_png(parse_dxt_bytes(raw)))).convert('RGBA');provenance='Qualified local 16×8 HUD frame'
            else:
                source=Image.new('RGBA',(16,8));ImageDraw.Draw(source).rectangle((1,2,14,6),fill='white');provenance='Synthetic reference (local HUD image unavailable)'
            result=Image.new('RGB',(640,100),'#1c2228');draw=ImageDraw.Draw(result)
            for col,(title,rgba)in enumerate([('Original',info['original']['rgba']),('Current / preview',candidate)]):
                draw.text((col*320+8,4),title,fill='white');marker=tinted_marker(source,rgba).resize((96,48),Image.Resampling.NEAREST)
                for x,bg in [(col*320+8,'#343a42'),(col*320+160,'#dddddd')]:draw.rectangle((x,25,x+140,90),fill=bg);result.paste(marker,(x+20,32),marker)
            self.marker_photo=ImageTk.PhotoImage(result);self.marker_picture.configure(image=self.marker_photo)
            self.marker_status.set(f"CarID {info['car_id']} · normalized RGB {candidate[:3]} · alpha locked {candidate[3]}\n{provenance}. Preview only until Apply; no shared texture, body paint or artwork edits.")
        except (ValueError,KeyError,OSError)as exc:self.marker_status.set(str(exc))
