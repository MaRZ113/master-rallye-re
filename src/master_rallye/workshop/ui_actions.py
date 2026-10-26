"""Original line icons and bounded responsive action rows, without icon fonts."""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk

ICONS={
 'save': [('line',(3,2,15,2,15,16,3,16,3,2)),('line',(6,2,6,7,12,7,12,2)),('line',(6,16,6,11,12,11,12,16))],
 'undo': [('line',(7,3,2,7,7,11)),('line',(2,7,11,7,15,10,15,15))],
 'redo': [('line',(11,3,16,7,11,11)),('line',(16,7,7,7,3,10,3,15))],
 'restore': [('line',(4,5,8,2,14,4,16,10,13,15,7,16,3,12)),('line',(2,2,2,7,7,7))],
 'validate': [('line',(2,9,7,14,16,3))],
 'build': [('line',(2,5,9,1,16,5,16,13,9,17,2,13,2,5,9,9,16,5)),('line',(9,9,9,17))],
 'preview': [('line',(1,9,5,4,13,4,17,9,13,14,5,14,1,9)),('ellipse',(7,6,11,12))],
 'play': [('polygon',(5,2,16,9,5,16))],
 'stop': [('rectangle',(4,4,14,14))],
 'camera': [('line',(1,5,5,5,7,2,12,2,14,5,17,5,17,15,1,15,1,5)),('ellipse',(6,6,12,12))],
}


def action_name(text):
    t=text.lower()
    for prefix,name in [('undo','undo'),('redo','redo'),('save','save'),('restore','restore'),('reset','restore'),('reload','restore'),('validate','validate'),('build','build'),('play','play'),('stop','stop'),('open interactive','preview'),('preview','preview'),('outside','camera'),('inside','camera'),('camera','camera'),('top-down','camera')]:
        if t.startswith(prefix):return name


def scroll_page(parent,*,padding=6):
    """A real resizable notebook page with vertical overflow, not clipped packs."""
    page=ttk.Frame(parent);canvas=tk.Canvas(page,bg='#252930',highlightthickness=0)
    scroll=ttk.Scrollbar(page,orient='vertical',command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
    body=ttk.Frame(canvas,padding=padding);body._scroll_owner=canvas
    item=canvas.create_window((0,0),window=body,anchor='nw')
    def update(_=None):
        canvas.itemconfigure(item,width=max(1,canvas.winfo_width()),height=max(canvas.winfo_height(),body.winfo_reqheight()))
        canvas.configure(scrollregion=canvas.bbox('all'))
    canvas.bind('<Configure>',update);body.bind('<Configure>',update)
    return body,page


def icon(master,name):
    size=max(16,round(18*float(master.tk.call('tk','scaling'))/(96/72)))
    im=Image.new('RGBA',(size*3,size*3));d=ImageDraw.Draw(im);scale=size*3/18
    for operation,coords in ICONS[name]:
        coords=tuple(round(v*scale)for v in coords)
        if operation=='line':d.line(coords,fill='#e8b257',width=max(3,round(scale)),joint='curve')
        else:getattr(d,operation)(coords,outline='#e8b257',fill='#e8b257'if operation=='polygon'else None,width=max(3,round(scale)))
    return ImageTk.PhotoImage(im.resize((size,size),Image.Resampling.LANCZOS),master=master)


def flow(frame):
    """Reflow existing packed actions in source order; no label truncation."""
    if hasattr(frame,'_action_flow'):return
    children=frame.pack_slaves()
    if len(children)<2 or sum(isinstance(c,ttk.Button)for c in children)<2:return
    if any(c.winfo_manager()!='pack' or c.pack_info().get('side') not in ('left','right') for c in children):return
    if not all(isinstance(c,(ttk.Button,ttk.Label,ttk.Combobox))for c in children):return
    frame._action_flow=children
    for c in children:c.pack_forget()
    frame.pack_propagate(False)
    def layout(_=None):
        if not frame.winfo_exists():return
        padding=frame.tk.splitlist(frame.cget('padding')) if isinstance(frame,ttk.Frame) else ()
        padding=[frame.winfo_pixels(v)for v in padding];padx=padding[0]if padding else 0;pady=padding[1]if len(padding)>1 else padx
        width=max(1,frame.winfo_width()-2*padx);x=y=5;line=0
        for c in children:
            w,h=c.winfo_reqwidth(),c.winfo_reqheight()
            if x>5 and x+w+5>width:x=5;y+=line+5;line=0
            c.place(x=x,y=y,width=w,height=h);x+=w+5;line=max(line,h)
        frame.configure(height=y+line+5+2*pady)
    frame.bind('<Configure>',layout,add='+');frame.after_idle(layout)


def install(app):
    from .appearance_ui import hint
    def size_window(window):
        factor=max(.75,float(window.tk.call('tk','scaling'))/(96/72))
        if factor<1.05:return
        sw,sh=window.winfo_screenwidth(),window.winfo_screenheight()
        w,h=window.winfo_width(),window.winfo_height();mw,mh=window.minsize()
        window.minsize(min(round(mw*factor),sw-40),min(round(mh*factor),sh-80))
        window.geometry(f'{min(round(w*factor),sw-40)}x{min(round(h*factor),sh-80)}')
    def clamp_panes():
        if not hasattr(app,'main_split'):return
        panes=app.main_split;total=panes.winfo_width()
        if total<100:return
        children=panes.winfo_children()
        if len(children)!=3:return
        def buttons(node):
            result=[]
            for child in node.winfo_children():
                if isinstance(child,ttk.Button):result.append(child.winfo_reqwidth())
                result.extend(buttons(child))
            return result
        factor=float(panes.tk.call('tk','scaling'))/(96/72)
        right=min(total*.52,max([round(310*factor)]+buttons(children[2]))+24)
        a,b=panes.sashpos(0),panes.sashpos(1)
        left=max([round(130*factor)]+buttons(children[0]))+20
        a=max(round(left),min(a,round(total*.25)))
        b=max(a+round(220*factor),min(b,round(total-right)))
        if panes.sashpos(0)!=a:panes.sashpos(0,a)
        if panes.sashpos(1)!=b:panes.sashpos(1,b)
    def mapped(event):
        widget=event.widget
        if isinstance(widget,(tk.Tk,tk.Toplevel)) and not hasattr(widget,'_actions_sized'):
            widget._actions_sized=True;widget.after_idle(lambda:size_window(widget))
        if isinstance(widget,ttk.Panedwindow) and widget is getattr(app,'main_split',None) and not hasattr(widget,'_actions_clamp'):
            widget._actions_clamp=True;widget.bind('<Configure>',lambda _:widget.after_idle(clamp_panes),add='+')
        if isinstance(widget,ttk.Label) and (len(str(widget.cget('text')))>30 or str(widget.cget('textvariable'))) and not hasattr(widget,'_actions_wrap'):
            widget._actions_wrap=True
            widget.master.bind('<Configure>',lambda e,w=widget:w.configure(wraplength=max(120,w.master.winfo_width()-20)) if w.winfo_exists() else None,add='+')
        if isinstance(widget,ttk.Button) and not hasattr(widget,'_action_icon'):
            name=action_name(str(widget['text']))
            if name:
                widget._action_icon=icon(widget,name);widget.configure(image=widget._action_icon,compound='left')
                hint(widget,str(widget['text'])+' · F1 for controls / shortcuts')
            widget.after_idle(lambda:flow(widget.master) if widget.winfo_exists() else None)
        elif isinstance(widget,ttk.Notebook) and not hasattr(widget,'_action_selector'):
            if widget.winfo_manager()=='pack':
                row=ttk.Frame(widget.master);row.pack(fill='x',before=widget)
                ttk.Label(row,text='Workspace').pack(side='left',padx=4)
                names=[widget.tab(t,'text')for t in widget.tabs()]
                chooser=ttk.Combobox(row,state='readonly',values=names);chooser.pack(side='left',fill='x',expand=True,pady=3)
                def sync(_=None):
                    if widget.winfo_exists() and widget.select():chooser.set(widget.tab(widget.select(),'text'))
                chooser.bind('<<ComboboxSelected>>',lambda e:widget.select(widget.tabs()[chooser.current()]))
                widget.bind('<<NotebookTabChanged>>',sync,add='+');sync()
            # Native Tk tabs do not scroll: provide a complete keyboard selector.
            def choose(_):
                labels=[widget.tab(t,'text')for t in widget.tabs()]
                popup=tk.Toplevel(widget);popup.title('Choose workspace');popup.transient(app.root)
                box=ttk.Combobox(popup,state='readonly',values=labels,width=42);box.pack(padx=12,pady=12);box.focus_set()
                box.bind('<<ComboboxSelected>>',lambda e:(widget.select(widget.tabs()[box.current()]),popup.destroy()))
            widget.bind('<Button-3>',choose,add='+');widget.bind('<Control-space>',choose,add='+')
            widget._action_selector=True;hint(widget,'Right-click tabs or Ctrl+Space: list every workspace')
    app.root.bind_all('<Map>',mapped,add='+')
    def wheel(event):
        node=event.widget
        if isinstance(node,(tk.Text,ttk.Treeview,tk.Listbox)):return
        while node is not None:
            if hasattr(node,'_scroll_owner'):
                node._scroll_owner.yview_scroll(-1 if event.delta>0 else 1,'units');return 'break'
            node=getattr(node,'master',None)
    app.root.bind_all('<MouseWheel>',wheel,add='+')
