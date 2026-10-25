"""Offline, locale-ready help with stable topic identifiers and English fallback."""
import json
import tkinter as tk
from tkinter import ttk
from .branding import apply_icon


def load_topics(root, locale='en'):
    if not locale.replace('-','').isalpha():raise ValueError('Invalid help locale')
    entries=json.loads((root/'index.json').read_text(encoding='utf-8'))
    topics=[]
    for entry in entries:
        key=entry['id']
        if not key.replace('-','').isalnum():raise ValueError('Invalid help topic')
        path=root/locale/(key+'.md')
        if not path.is_file():path=root/'en'/(key+'.md')
        topics.append((key,entry['title'],path.read_text(encoding='utf-8')))
    return topics


class HelpWindow:
    def __init__(self,parent,root,topic=None,locale='en'):
        win=tk.Toplevel(parent);apply_icon(win);win.title('Rally Workshop — Offline Help');win.geometry('1000x700')
        self.window=win;self.topics=load_topics(root,locale);query=tk.StringVar()
        ttk.Label(win,text='Search topics and text (offline)').pack(anchor='w',padx=8)
        ttk.Entry(win,textvariable=query).pack(fill='x',padx=8,pady=4)
        body=ttk.Panedwindow(win,orient='horizontal');body.pack(fill='both',expand=True)
        items=tk.Listbox(body,width=28);body.add(items,weight=1)
        frame=ttk.Frame(body);body.add(frame,weight=4)
        text=tk.Text(frame,wrap='word',padx=12,pady=12);text.pack(side='left',fill='both',expand=True)
        bar=ttk.Scrollbar(frame,command=text.yview);bar.pack(side='right',fill='y');text.configure(yscrollcommand=bar.set)
        visible=[]
        def show(event=None):
            if not items.curselection():return
            key,title,content=visible[items.curselection()[0]]
            text.configure(state='normal');text.delete('1.0','end');text.insert('end',content);text.configure(state='disabled')
        def search(*args):
            visible[:]=[row for row in self.topics if query.get().casefold() in (' '.join(row)).casefold()]
            items.delete(0,'end')
            for row in visible:items.insert('end',row[1])
            if visible:items.selection_set(0);show()
        query.trace_add('write',search);items.bind('<<ListboxSelect>>',show);search()
        if topic:
            for i,row in enumerate(visible):
                if row[0]==topic:items.selection_clear(0,'end');items.selection_set(i);show();break
