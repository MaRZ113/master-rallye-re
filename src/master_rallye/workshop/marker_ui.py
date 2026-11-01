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
        self.marker_hex=tk.StringVar();self.marker_status=tk.StringVar();self.marker_mode=tk.StringVar(value='MANUAL');self.marker_alpha=tk.StringVar(value='1');self.marker_contrast=tk.BooleanVar(value=False);self.marker_analysis=None
        modes=ttk.Frame(box);modes.pack(fill='x')
        ttk.Combobox(modes,textvariable=self.marker_mode,values=('HISTORICAL','AUTO_DOMINANT','AUTO_AVERAGE','MANUAL'),state='readonly',width=18).pack(side='left')
        ttk.Button(modes,text='Recalculate paint colours',command=self.marker_recalculate_ui).pack(side='left')
        ttk.Checkbutton(modes,text='Restrained contrast lift',variable=self.marker_contrast,command=self.marker_preview).pack(side='left')
        ttk.Label(modes,text='Alpha').pack(side='left');alpha=ttk.Entry(modes,textvariable=self.marker_alpha,width=6);alpha.pack(side='left');alpha.bind('<KeyRelease>',lambda _:(self.marker_mode.set('MANUAL'),self.marker_preview()))
        self.marker_swatches=ttk.Frame(box);self.marker_swatches.pack(fill='x')
        self.marker_source=tk.StringVar();ttk.Label(box,textvariable=self.marker_source,wraplength=900).pack(fill='x')
        row=ttk.Frame(box);row.pack(fill='x');entry=ttk.Entry(row,textvariable=self.marker_hex,width=10);entry.pack(side='left');entry.bind('<KeyRelease>',lambda _:(self.marker_mode.set('MANUAL'),self.marker_preview()))
        def choose():
            value=colorchooser.askcolor(color=self.marker_hex.get()or'#FFFFFF',parent=self.vehicle_window)[1]
            if value:self.marker_mode.set('MANUAL');self.marker_hex.set(value);self.marker_preview()
        ttk.Button(row,text='Pick marker RGB…',command=choose).pack(side='left')
        palette=ttk.Combobox(row,values=list(PRESETS),state='readonly',width=12);palette.pack(side='left',padx=5)
        palette.bind('<<ComboboxSelected>>',lambda _:(self.marker_mode.set('MANUAL'),self.marker_hex.set(PRESETS[palette.get()]),self.marker_preview()))
        ttk.Button(row,text='Preview marker tint',command=self.marker_preview).pack(side='left')
        def apply():
            owner=self.project;mode=self.marker_mode.get()
            self.vehicle_action('Apply Race Progress Marker policy',lambda:owner.marker_select(mode,manual=[*normalized_rgb(self.marker_hex.get()),float(self.marker_alpha.get())],contrast=self.marker_contrast.get(),analysis=self.marker_analysis))
        ttk.Button(row,text='Apply marker color',command=apply).pack(side='left')
        def reset():
            owner=self.project;self.vehicle_action('Restore Race HUD color',lambda:owner.vehicle_reset('race_marker'))
        ttk.Button(row,text='Reset marker color',command=reset).pack(side='left')
        self.marker_picture=ttk.Label(box);self.marker_picture.pack(fill='x',pady=5)
        ttk.Label(box,textvariable=self.marker_status,wraplength=900).pack(fill='x')
        self.marker_hex.trace_add('write',lambda *_:self.marker_preview())
        self.marker_alpha.trace_add('write',lambda *_:self.marker_preview())
        self.marker_mode.trace_add('write',lambda *_:self.marker_preview())
        ttk.Button(box,text='Reset to verified historical colour',command=lambda:self.vehicle_action('Use original marker',lambda:self.project.marker_select('HISTORICAL'))).pack(anchor='w')
        ai=ttk.LabelFrame(parent,text='Native addon AI eligibility — new rosters only',padding=8);ai.pack(fill='x',pady=6);self.ai_vars={}
        for mode in ('quick_race','rallye_cup','master_rallye','invitation','challenge','practice'):
            v=tk.BooleanVar();self.ai_vars[mode]=v;ttk.Checkbutton(ai,text=mode,variable=v).pack(side='left')
        ttk.Button(ai,text='Apply AI modes',command=lambda:self.vehicle_action('Edit native AI eligibility',lambda:self.project.ai_update({k:v.get()for k,v in self.ai_vars.items()}))).pack(side='left')

    def marker_refresh(self):
        if not getattr(self,'marker_picture',None):return
        if self.project.data['kind']!='addon':
            self.marker_status.set('Stock registration color is read-only. Addon per-CarID marker authoring only.');self.marker_picture.configure(image='');return
        info=self.project.marker_inspect();context=self.project.marker_context();policy=context['policy']
        self.marker_hex.set(info['current']['hex']);self.marker_alpha.set(str(info['current']['rgba'][3]));self.marker_mode.set(policy['mode']);self.marker_contrast.set(policy.get('contrast',False));self.marker_analysis=context.get('analysis')
        self.marker_source.set('Policy: '+policy['mode']+'; historical: '+str(context.get('historical'))+'; suggestions remain separate from original evidence.')
        for mode,value in self.project.ai_inspect()['eligibility'].items():self.ai_vars[mode].set(value['enabled'])

    def marker_preview(self):
        try:
            from io import BytesIO
            from master_rallye.dxt import parse_dxt_bytes,encode_png
            p=self.project;info=p.marker_inspect();candidate=[*normalized_rgb(self.marker_hex.get()),float(self.marker_alpha.get())]
            from ..addon_sdk.marker_colour import select
            mode=self.marker_mode.get();policy={'mode':mode,'contrast':self.marker_contrast.get(),'rgba':candidate}
            candidate=select(policy,self.marker_analysis,p.marker_context().get('historical'))
            path=Path(p.data['build_settings']['retail_root'])/'DataGx/Hud/hud-template_003_000.dxt'
            if path.exists():
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()!='2485192edf007f5dc97a455be87ae8f6b18c01719da4c7b4d60f396c577ade93':raise ValueError('Local HUD marker source differs from qualified stock art')
                source=Image.open(BytesIO(encode_png(parse_dxt_bytes(raw)))).convert('RGBA');provenance='Qualified local 16×8 HUD frame'
            else:
                source=Image.new('RGBA',(16,8));ImageDraw.Draw(source).rectangle((1,2,14,6),fill='white');provenance='Synthetic reference (local HUD image unavailable)'
            result=Image.new('RGB',(640,100),'#1c2228');draw=ImageDraw.Draw(result)
            for col,(title,rgba)in enumerate([('Baseline',info['original']['rgba']),('Current / preview',candidate)]):
                draw.text((col*320+8,4),title,fill='white');marker=tinted_marker(source,rgba).resize((96,48),Image.Resampling.NEAREST)
                for x,bg in [(col*320+8,'#343a42'),(col*320+160,'#dddddd')]:draw.rectangle((x,25,x+140,90),fill=bg);result.paste(marker,(x+20,32),marker)
            self.marker_photo=ImageTk.PhotoImage(result);self.marker_picture.configure(image=self.marker_photo)
            self.marker_status.set(f"CarID {info['car_id']} · normalized RGB {candidate[:3]} · alpha {candidate[3]}\n{provenance}. Preview only until Apply; no shared texture, body paint or artwork edits.")
        except (ValueError,KeyError,OSError)as exc:self.marker_status.set(str(exc))

    def marker_recalculate_ui(self):
        try:
            self.marker_analysis=self.project.marker_recalculate();r=self.marker_analysis
            for widget in self.marker_swatches.winfo_children():widget.destroy()
            def choose(rgb):
                self.marker_mode.set('MANUAL');self.marker_hex.set('#'+''.join(f'{round(v*255):02X}'for v in rgb));self.marker_preview()
            for title,rgb in [('Dominant',r['dominant']),('Average',r['average'])]+[(f"{s['weight']:.0%}",s['rgb'])for s in r['swatches']]:
                color='#'+''.join(f'{round(v*255):02X}'for v in rgb);tk.Button(self.marker_swatches,text=title+' '+color,bg=color,command=lambda c=rgb:choose(c)).pack(side='left')
            self.marker_source.set(r['confidence']+' / '+r['method']+'; '+' '.join(r['limitations']))
            self.marker_preview()
        except (ValueError,OSError)as exc:self.marker_status.set(str(exc))
