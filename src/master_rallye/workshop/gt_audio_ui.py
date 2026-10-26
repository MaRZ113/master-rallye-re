"""Optional GT source browser feeding the ordinary reviewed Audio Import 2.0."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog
from .branding import apply_icon
from .audio_import_ui import AudioImportWindow,play

class GTSoundWindow:
    def __init__(self,app):
        self.app=app;self.project=app.project;self.adapter=None;self.inspection=None;self.route=None;self.selector=None;self.exported=None;self.loading=False
        win=tk.Toplevel(app.root);self.window=win;apply_icon(win);win.title('GT Audio Source Adapter — '+self.project.data['identity']+' / CarID '+str(self.project.data['car_id']));win.geometry('1120x880');win.protocol('WM_DELETE_WINDOW',self.close)
        self.game=tk.StringVar(value='gt4');row=ttk.Frame(win,padding=5);row.pack(fill='x');ttk.Label(row,text='Optional game source').pack(side='left');box=ttk.Combobox(row,textvariable=self.game,values=['gt4','gt3'],state='readonly',width=8);box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda *_:self.load_settings())
        self.fields={}
        for key,label in [('source','GT4 extracted root / GT3 original VOL'),('catalog','Optional existing private Lab catalog JSON'),('core','Optional original GT3 CORE / qualified GT4 ELF')]:
            row=ttk.Frame(win,padding=3);row.pack(fill='x');ttk.Label(row,text=label,width=50).pack(side='left');var=tk.StringVar();self.fields[key]=var;ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True)
            ttk.Button(row,text='Browse',command=lambda k=key:self.browse(k)).pack(side='left')
            var.trace_add('write',lambda *_:self.config_changed())
        row=ttk.Frame(win,padding=5);row.pack(fill='x');ttk.Button(row,text='Load / generate read-only source catalog',command=self.configure).pack(side='left');ttk.Button(row,text='GT source Help',command=lambda:app.show_help('audio-import')).pack(side='left')
        self.query=tk.StringVar();row=ttk.Frame(win,padding=4);row.pack(fill='x');ttk.Label(row,text='Exact source vehicle ID or verified GT4 model code').pack(side='left');ttk.Entry(row,textvariable=self.query).pack(side='left',fill='x',expand=True);ttk.Button(row,text='Find sounds for this vehicle',command=self.find).pack(side='left')
        vf=ttk.Frame(win);vf.pack(fill='x',padx=8);self.vehicles=ttk.Treeview(vf,columns=('sound','codes'),show='tree headings',height=4);self.vehicles.heading('#0',text='Source vehicle ID');self.vehicles.heading('sound',text='Shared Sound ID');self.vehicles.heading('codes',text='Verified model codes');self.vehicles.pack(side='left',fill='x',expand=True);scroll=ttk.Scrollbar(vf,command=self.vehicles.yview);scroll.pack(side='right',fill='y');self.vehicles.configure(yscrollcommand=scroll.set);self.vehicles.bind('<<TreeviewSelect>>',lambda *_:self.query.set(self.vehicles.selection()[0]) if self.vehicles.selection() else None)
        self.bank=tk.StringVar();row=ttk.Frame(win,padding=5);row.pack(fill='x');self.bank_box=ttk.Combobox(row,textvariable=self.bank,state='readonly',width=55);self.bank_box.pack(side='left',fill='x',expand=True);ttk.Button(row,text='Inspect bank / RPM bands',command=self.inspect).pack(side='left')
        self.event=tk.StringVar(value='turbine2');ttk.Combobox(row,textvariable=self.event,values=['turbine2','turbine','b_off','shift_change'],state='readonly',width=15).pack(side='left');ttk.Button(row,text='Inspect named route',command=self.event_inspect).pack(side='left')
        ef=ttk.Frame(win);ef.pack(fill='x',padx=8);self.entries=ttk.Treeview(ef,columns=('codec','rpm','loop','offset'),show='tree headings',height=6)
        for key,label in [('#0','Sample / entry ID'),('codec','Support'),('rpm','Reference RPM / raw control'),('loop','Original loop frames'),('offset','Decoded member sample offset')]:self.entries.heading(key,text=label);self.entries.column(key,width=200 if key!='#0' else 120)
        self.entries.pack(side='left',fill='x',expand=True);scroll=ttk.Scrollbar(ef,command=self.entries.yview);scroll.pack(side='right',fill='y');self.entries.configure(yscrollcommand=scroll.set);self.entries.bind('<<TreeviewSelect>>',self.entry_selected)
        row=ttk.Frame(win,padding=5);row.pack(fill='x');self.rate_mode=tk.StringVar(value='nominal');ttk.Combobox(row,textvariable=self.rate_mode,values=['nominal','native'],state='readonly',width=12).pack(side='left');self.rate=tk.StringVar(value='24000');ttk.Entry(row,textvariable=self.rate,width=10).pack(side='left');ttk.Label(row,text='Explicit nominal Hz, or qualified native leaf/anchor pitch').pack(side='left')
        row=ttk.Frame(win,padding=5);row.pack(fill='x');ttk.Button(row,text='Export selected private audition',command=self.export).pack(side='left');ttk.Button(row,text='Play source recording',command=lambda:play(self.exported['wav']) if self.exported else None).pack(side='left');ttk.Button(row,text='Stop',command=lambda:play()).pack(side='left');ttk.Button(row,text='Use in Audio Import 2.0…',command=self.use).pack(side='left')
        self.status=tk.StringVar(value='Configure local sources. GT3 short mesh-code mapping is not inferred. Named events are source associations, not proven acoustic identities.');ttk.Label(win,textvariable=self.status,wraplength=1090,padding=8).pack(side='bottom',fill='x')
        self.details=tk.Text(win,wrap='word',height=6,bg='#1b2027',fg='#d8dde5',state='disabled');self.details.pack(fill='both',expand=True,padx=8);self.load_settings()

    def load_settings(self):
        self.loading=True
        record=self.project.audio_state().get('gt_sources',{}).get(self.game.get(),{}).get('config',{})
        for key,var in self.fields.items():var.set(record.get(key,''))
        self.adapter=None;self.inspection=None;self.route=None;self.exported=None;self.selector=None
        self.vehicles.delete(*self.vehicles.get_children());self.entries.delete(*self.entries.get_children());self.bank_box['values']=[];self.bank.set('')
        self.loading=False

    def config_changed(self):
        if self.loading:return
        self.adapter=None;self.inspection=None;self.route=None;self.exported=None;self.selector=None
        if hasattr(self,'status'):self.status.set('Source settings changed. Load/verify the catalog again before inspection or export.')

    def browse(self,key):
        value=filedialog.askdirectory(parent=self.window) if key=='source' and self.game.get()=='gt4' else filedialog.askopenfilename(parent=self.window)
        if value:self.fields[key].set(value)

    def run(self,label,work,done):
        if self.app.busy:return
        if self.app.project is None or self.app.project.root!=self.project.root:self.status.set('Active vehicle changed. Reopen the GT source browser for that project; no implicit cross-car edit.');return
        def finished(value):
            if self.window.winfo_exists():done(value)
        self.app.run(label,work,finished)

    def configure(self):
        config={'game':self.game.get(),**{key:var.get() for key,var in self.fields.items() if var.get().strip()}}
        p=self.project
        def work():p.gt_audio_configure(config);return p.gt_audio_adapter(config['game'])
        def done(adapter):
            if config!={'game':self.game.get(),**{key:var.get() for key,var in self.fields.items() if var.get().strip()}}:
                self.status.set('Settings changed during loading; verify the new configuration again. No MR audio changed.');return
            self.adapter=adapter;self.inspection=None;self.route=None;self.selector=None;self.exported=None;self.vehicles.delete(*self.vehicles.get_children())
            for row in adapter.catalog['vehicles']:self.vehicles.insert('','end',iid=row['vehicle_id'],text=row['vehicle_id'],values=(row['sound_id'],', '.join(row.get('model_codes',[]))))
            self.bank_box['values']=sorted(adapter.allowed);self.status.set('Source catalog loaded: '+str(adapter.catalog.get('counts'))+'. No MR audio changed. Select an exact source vehicle or explicit shared bank.')
        self.run('Load qualified optional GT catalog',work,done)

    def find(self):
        if not self.adapter:return
        selector=self.query.get();adapter=self.adapter
        def done(row):
            self.vehicles.selection_set(row['vehicle_id']);self.vehicles.see(row['vehicle_id'])
            self.selector=row['vehicle_id'];self.bank_box['values']=list(row['banks'])+sorted(adapter.allowed-set(row['banks']));candidate=row.get('default_native_bank_candidate',{}).get('bank_id');self.bank.set(candidate or (row['banks'][0] if row['banks'] else ''))
            self.show(row);self.status.set('Verified source association; default tuning is a static candidate. Choose any available alternate bank. Shared engine rows: '+str(len(row.get('engine_rows_sharing_sound',[])))+'; no unique acoustic identity or full engine mix claimed.')
        self.run('Find verified GT vehicle sound banks',lambda:adapter.find_vehicle(selector),done)

    def populate(self,report):
        self.inspection=report;self.exported=None;self.entries.delete(*self.entries.get_children())
        for e in report['entries']:
            loop=[e.get('loop_start_sample'),e.get('loop_end_sample')];rpm=e.get('rpm_interpretation',{}).get('reference_rpm',e.get('words_u16',[])[:3]);self.entries.insert('','end',iid=str(e['entry_id']),text=str(e['entry_id']),values=(e.get('codec_status'),str(rpm),str(loop),str(e.get('sample_file_offset'))))
        self.show({k:v for k,v in report.items() if k!='entries'});self.status.set('Inspect original records, loops and support status; select one PCM-valid recording. Nominal rate is an explicit user choice.')

    def inspect(self):
        if not self.adapter:return
        bank=self.bank.get();self.route=None;self.inspection=None;self.exported=None;self.entries.delete(*self.entries.get_children());self.run('Inspect original GT bank',lambda:self.adapter.inspect(bank),self.populate)

    def event_inspect(self):
        if not self.adapter:return
        name=self.event.get();self.route=None;self.inspection=None;self.exported=None;self.entries.delete(*self.entries.get_children())
        def done(route):
            self.route=route;self.bank.set(route['bank_id']);self.populate(route['inspection']);self.entries.selection_set(route['entry_id']);self.entries.see(route['entry_id']);self.entry_selected();self.status.set('Static named-event route recovered. turbine2 has native drivetrain control evidence; perceived whine/acoustic identity and original mix remain unverified.')
        self.run('Resolve qualified native named route',lambda:self.adapter.event_selection(name),done)

    def entry_selected(self,*_):
        if not self.inspection or not self.entries.selection():return
        key=self.entries.selection()[0]
        if self.route and key!=self.route['entry_id']:self.route=None
        entry=next(e for e in self.inspection['entries'] if str(e['entry_id'])==key);self.show({'entry':entry,'named_route':self.route and {k:v for k,v in self.route.items() if k!='inspection'},'boundary':'sample offset belongs to decoded bank/member; do not add it to compressed RoFS offset. Engine bands are individual recordings.'})

    def show(self,value):self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('end',json.dumps(value,indent=2));self.details.configure(state='disabled')

    def export(self):
        if not self.adapter or not self.inspection or not self.entries.selection():return
        try:rate=int(self.rate.get())
        except ValueError:self.status.set('Enter an explicit integer nominal sample rate');return
        game=self.adapter.game;bank=self.bank.get();entry=self.entries.selection()[0];selector=self.selector;mode=self.rate_mode.get();event=self.route['event']['name'] if self.route else None;expected=self.inspection['sha256'];p=self.project
        def done(result):self.exported=result;self.show(result['evidence']);self.status.set('Private source WAV ready. Audition, then Use in Audio Import 2.0 for loop/gain/conversion review; MR layers are still unchanged.')
        self.run('Export selected original GT recording',lambda:p.gt_audio_export(game,bank,entry,selector=selector,rate=rate,rate_mode=mode,event_name=event,expected_bank_sha256=expected),done)

    def use(self):
        if self.app.project is None or self.app.project.root!=self.project.root:self.status.set('Active vehicle changed; reopen this browser for the intended vehicle.');return
        if self.exported and not self.app.busy:self.app.audio_import2_window=AudioImportWindow(self.app,self.exported['wav'],self.exported['evidence'])

    def close(self):play();self.window.destroy()
