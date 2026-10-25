"""Viewport-sized Tk raster inspection. No persistent texture/image copies."""
import math
from dataclasses import replace
from fractions import Fraction
import tkinter as tk
from tkinter import ttk
from master_rallye.dxt import encode_png,DxtTexture

class TextureView(ttk.Frame):
    def __init__(self,parent,loader,**kw):
        super().__init__(parent,**kw);self.loader=loader;self.scale=1.;self.fit=True;self.original=tk.BooleanVar();self.channel=tk.StringVar(value='RGBA');self.source=None;self.pending=None
        bar=ttk.Frame(self);bar.pack(fill='x')
        for text,action in [('Fit',self.fit_window),('1:1',self.actual),('−',lambda:self.zoom(.8)),('+',lambda:self.zoom(1.25))]:ttk.Button(bar,text=text,width=4,command=action).pack(side='left')
        ttk.Combobox(bar,textvariable=self.channel,values=['RGBA','RGB','Alpha'],state='readonly',width=6).pack(side='left');self.channel.trace_add('write',lambda *_:self.load())
        ttk.Checkbutton(bar,text='Original',variable=self.original,command=self.load).pack(side='left')
        frame=ttk.Frame(self);frame.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(frame,bg='#202329',highlightthickness=0,width=300,height=220)
        sy=ttk.Scrollbar(frame,orient='vertical',command=lambda *a:self.scroll('y',*a));sx=ttk.Scrollbar(frame,orient='horizontal',command=lambda *a:self.scroll('x',*a))
        self.canvas.configure(xscrollcommand=sx.set,yscrollcommand=sy.set);self.canvas.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1)
        self.canvas.bind('<Configure>',lambda _:self.schedule());self.canvas.bind('<MouseWheel>',lambda e:self.zoom(1.25 if e.delta>0 else .8));self.canvas.bind('<ButtonPress-1>',lambda e:self.canvas.scan_mark(e.x,e.y));self.canvas.bind('<B1-Motion>',self.pan)
        self.label=ttk.Label(self,text='');self.label.pack(fill='x')
    def load(self):
        texture=self.loader(self.original.get())
        if texture is None:return
        self.texture=texture;pixels=texture.bgra
        if self.channel.get()=='Alpha':pixels=b''.join(bytes((a,a,a,255)) for a in pixels[3::4])
        elif self.channel.get()=='RGB':
            b=bytearray(pixels);b[3::4]=b'\xff'*(texture.width*texture.height);pixels=bytes(b)
        self.source=tk.PhotoImage(data=encode_png(replace(texture,bgra=pixels)))
        self.schedule()
    def fit_window(self):self.fit=True;self.schedule()
    def actual(self):self.fit=False;self.scale=1.;self.canvas.xview_moveto(0);self.canvas.yview_moveto(0);self.schedule()
    def zoom(self,factor):self.fit=False;self.scale=max(.03125,min(16,self.scale*factor));self.schedule()
    def scroll(self,axis,*args):getattr(self.canvas,axis+'view')(*args);self.schedule()
    def pan(self,e):self.canvas.scan_dragto(e.x,e.y,gain=1);self.schedule()
    def schedule(self):
        if self.pending:self.after_cancel(self.pending)
        self.pending=self.after(35,self.draw)
    def draw(self):
        self.pending=None
        if self.source is None:return
        c=self.canvas;w=max(1,c.winfo_width());h=max(1,c.winfo_height());sw=self.source.width();sh=self.source.height()
        if self.fit:self.scale=min(w/sw,h/sh)
        ratio=Fraction(max(1/1024,self.scale)).limit_denominator(1024);n,d=ratio.numerator,ratio.denominator;self.scale=n/d
        c.configure(scrollregion=(0,0,math.ceil(sw*self.scale),math.ceil(sh*self.scale)))
        x=max(0,int(c.canvasx(0)));y=max(0,int(c.canvasy(0)));x0=min(sw-1,int(x/self.scale));y0=min(sh-1,int(y/self.scale));x1=min(sw,math.ceil((x+w)/self.scale)+1);y1=min(sh,math.ceil((y+h)/self.scale)+1)
        # Crop BEFORE scaling. Even a 16x zoom retains only viewport-sized raster.
        self.visible=tk.PhotoImage();self.visible.tk.call(self.visible,'copy',self.source,'-from',x0,y0,x1,y1,'-zoom',n,n,'-subsample',d,d)
        c.delete('all')
        for a in range(x//16*16,x+w+16,16):
            for b in range(y//16*16,y+h+16,16):c.create_rectangle(a,b,a+16,b+16,fill='#777777' if (a//16+b//16)%2 else '#aaaaaa',outline='')
        c.create_image(x0*self.scale,y0*self.scale,image=self.visible,anchor='nw');self.label.configure(text=f'{sw} × {sh} · {self.scale:.2f}x · {self.channel.get()} · '+('original' if self.original.get() else 'edited/current'))
