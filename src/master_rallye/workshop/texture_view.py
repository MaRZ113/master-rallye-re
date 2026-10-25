"""Display-only, premultiplied-alpha viewport resampling; native pixels stay immutable."""
import math
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

MAX_SOURCE_PIXELS=16*1024*1024
MAX_VIEW_PIXELS=4*1024*1024

def display_image(texture,channel='RGBA'):
    if texture.width*texture.height>MAX_SOURCE_PIXELS:raise ValueError('Texture inspection exceeds the 16M-pixel display budget; native resource is unchanged')
    image=Image.frombytes('RGBA',(texture.width,texture.height),texture.bgra,'raw','BGRA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    if channel=='Alpha':
        alpha=image.getchannel('A');image=Image.merge('RGBA',(alpha,alpha,alpha,Image.new('L',image.size,255)))
    elif channel=='RGB':image.putalpha(255)
    elif channel!='RGBA':raise ValueError('Unknown display channel')
    return image

def rasterize(image,scale,viewport,*,pixel=False,premultiplied=None):
    """Global image-to-display mapping; crop output, never enlarge a whole image.

    Pillow filters directly from the immutable source box. RGBa premultiplication
    prevents invisible texel RGB from bleeding into transparent filtered edges.
    """
    if not math.isfinite(scale) or not 1/1024<=scale<=16:raise ValueError('Invalid display zoom')
    sw,sh=image.size;fw,fh=max(1,round(sw*scale)),max(1,round(sh*scale))
    x,y,w,h=(int(v) for v in viewport);w=min(4096,max(1,w));h=min(4096,max(1,h),max(1,MAX_VIEW_PIXELS//w));x=max(0,x);y=max(0,y)
    dw,dh=min(w,fw-x),min(h,fh-y)
    if dw<=0 or dh<=0:return None,(x,y)
    if (fw,fh)==(sw,sh):return image.crop((x,y,x+dw,y+dh)),(x,y)
    box=(x*sw/fw,y*sh/fh,(x+dw)*sw/fw,(y+dh)*sh/fh)
    if pixel:return image.resize((dw,dh),Image.Resampling.NEAREST,box=box),(x,y)
    source=premultiplied if premultiplied is not None else image.convert('RGBa')
    method=Image.Resampling.LANCZOS if scale<1 else Image.Resampling.BICUBIC
    return source.resize((dw,dh),method,box=box).convert('RGBA'),(x,y)

class TextureView(ttk.Frame):
    def __init__(self,parent,loader,**kw):
        super().__init__(parent,**kw);self.loader=loader;self.scale=1.;self.fit=True;self.original=tk.BooleanVar();self.channel=tk.StringVar(value='RGBA');self.pixel=tk.BooleanVar();self.source=None;self.pending=None
        bar=ttk.Frame(self);bar.pack(fill='x')
        for text,action in [('Fit',self.fit_window),('1:1',self.actual),('−',lambda:self.zoom(.8)),('+',lambda:self.zoom(1.25))]:ttk.Button(bar,text=text,width=4,command=action).pack(side='left')
        ttk.Combobox(bar,textvariable=self.channel,values=['RGBA','RGB','Alpha'],state='readonly',width=6).pack(side='left');self.channel.trace_add('write',lambda *_:self.load())
        ttk.Checkbutton(bar,text='Original',variable=self.original,command=self.load).pack(side='left')
        ttk.Checkbutton(self,text='Pixel-sharp / nearest (1:1 always exact)',variable=self.pixel,command=self.schedule).pack(anchor='w')
        frame=ttk.Frame(self);frame.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(frame,bg='#202329',highlightthickness=0,width=300,height=220)
        sy=ttk.Scrollbar(frame,orient='vertical',command=lambda *a:self.scroll('y',*a));sx=ttk.Scrollbar(frame,orient='horizontal',command=lambda *a:self.scroll('x',*a))
        self.canvas.configure(xscrollcommand=sx.set,yscrollcommand=sy.set);self.canvas.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1)
        self.canvas.bind('<Configure>',lambda _:self.schedule());self.canvas.bind('<MouseWheel>',lambda e:self.zoom(1.25 if e.delta>0 else .8,e));self.canvas.bind('<ButtonPress-1>',lambda e:self.canvas.scan_mark(e.x,e.y));self.canvas.bind('<B1-Motion>',self.pan)
        self.label=ttk.Label(self,text='');self.label.pack(fill='x')
    def load(self):
        texture=self.loader(self.original.get())
        if texture is None:return
        self.texture=texture;self.source=display_image(texture,self.channel.get());self.premul=self.source.convert('RGBa');self.schedule()
    def fit_window(self):self.fit=True;self.schedule()
    def actual(self):self.fit=False;self.scale=1.;self.canvas.xview_moveto(0);self.canvas.yview_moveto(0);self.schedule()
    def zoom(self,factor,event=None):
        if self.source is None:return
        c=self.canvas;px=event.x if event else c.winfo_width()/2;py=event.y if event else c.winfo_height()/2
        oldw=max(1,round(self.source.width*self.scale));oldh=max(1,round(self.source.height*self.scale));u=c.canvasx(px)/oldw;v=c.canvasy(py)/oldh
        self.fit=False;self.scale=max(1/64,min(16,self.scale*factor));fw=max(1,round(self.source.width*self.scale));fh=max(1,round(self.source.height*self.scale))
        c.configure(scrollregion=(0,0,fw,fh));c.xview_moveto((u*fw-px)/fw);c.yview_moveto((v*fh-py)/fh);self.schedule()
    def scroll(self,axis,*args):getattr(self.canvas,axis+'view')(*args);self.schedule()
    def pan(self,e):self.canvas.scan_dragto(e.x,e.y,gain=1);self.schedule()
    def schedule(self):
        if self.pending:self.after_cancel(self.pending)
        self.pending=self.after(35,self.draw)
    def draw(self):
        self.pending=None
        if self.source is None:return
        c=self.canvas;w=max(1,c.winfo_width());h=max(1,c.winfo_height());sw,sh=self.source.size
        if self.fit:self.scale=max(1/1024,min(16,w/sw,h/sh))
        fw,fh=max(1,round(sw*self.scale)),max(1,round(sh*self.scale));c.configure(scrollregion=(0,0,fw,fh))
        x=max(0,int(c.canvasx(0)));y=max(0,int(c.canvasy(0)));image,origin=rasterize(self.source,self.scale,(x,y,w,h),pixel=self.pixel.get(),premultiplied=self.premul);self.last_raster=image
        c.delete('all')
        for a in range(x//16*16,x+w+16,16):
            for b in range(y//16*16,y+h+16,16):c.create_rectangle(a,b,a+16,b+16,fill='#777777' if (a//16+b//16)%2 else '#aaaaaa',outline='')
        if image is not None:self.visible=ImageTk.PhotoImage(image);c.create_image(*origin,image=self.visible,anchor='nw')
        c.create_rectangle(0,0,fw,fh,outline='#bb8736')
        self.label.configure(text=f'{sw} × {sh} · {self.scale:.2f}x · {self.channel.get()} · '+('original' if self.original.get() else 'edited/current'))
