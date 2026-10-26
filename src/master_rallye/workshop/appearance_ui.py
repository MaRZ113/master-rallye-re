"""Paint/style and crew panels. All mutations use the shared project service."""
import io
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageChops, ImageEnhance
from .branding import apply_icon
from master_rallye.paint_authoring import COLOR_PRESETS


def hint(widget,text):
    """Small delayed tooltip; no input capture or background worker."""
    state={'timer':None,'window':None}
    def hide(*_):
        if state['timer']:
            try:widget.after_cancel(state['timer'])
            except tk.TclError:pass
            state['timer']=None
        if state['window']:
            state['window'].destroy();state['window']=None
    def show():
        state['timer']=None;win=tk.Toplevel(widget);state['window']=win;win.overrideredirect(True);win.geometry(f'+{widget.winfo_rootx()}+{widget.winfo_rooty()+widget.winfo_height()+4}')
        tk.Label(win,text=text,bg='#55452b',fg='#fff0cc',wraplength=360,justify='left',padx=8,pady=6).pack()
    widget.bind('<Enter>',lambda _:state.update(timer=widget.after(650,show)),add='+');widget.bind('<Leave>',hide,add='+');widget.bind('<ButtonPress>',hide,add='+');widget.bind('<Destroy>',hide,add='+')


class AppearancePanels:
    def appearance_layout(self,tabs):
        paint=ttk.Frame(tabs,padding=8);tabs.add(paint,text='Paint / Style')
        self.appearance_name=tk.StringVar(value='Source Fidelity')
        box=ttk.Combobox(paint,textvariable=self.appearance_name,values=['Source Fidelity','Classic MR Style','Custom'],state='readonly');box.pack(fill='x')
        box.bind('<<ComboboxSelected>>',lambda e:self.appearance_switch())
        hint(box,'Qualified Classic versions are separate projects rebuilt from the immutable import. Custom appearance edits remain separate; no repeated lossy conversion.')
        ttk.Label(paint,text='Source Fidelity / qualified Classic conversion / Custom edits. Classic requires a source-qualified recipe, preview and explicit report approval before building.',wraplength=350).pack(fill='x',pady=6)
        ttk.Button(paint,text='Rebuild as Classic…',command=self.rebuild_classic_version).pack(fill='x')
        ttk.Button(paint,text='Review / approve Classic report…',command=self.review_classic_report).pack(fill='x',pady=3)
        ttk.Button(paint,text='Matched Original / Modified / Difference',command=self.compare_appearance).pack(fill='x')
        self.paint_region_name=tk.StringVar();self.region_box=ttk.Combobox(paint,textvariable=self.paint_region_name,state='readonly');self.region_box.pack(fill='x',pady=8)
        ttk.Button(paint,text='Import qualified paint mask…',command=self.import_paint_mask).pack(fill='x')
        self.paint_color=tk.StringVar(value='190,28,32');ttk.Entry(paint,textvariable=self.paint_color).pack(fill='x',pady=5)
        self.color_name=tk.StringVar();self.color_box=ttk.Combobox(paint,textvariable=self.color_name,state='readonly');self.color_box.pack(fill='x')
        self.color_box.bind('<<ComboboxSelected>>',lambda e:self.choose_color_preset())
        ttk.Button(paint,text='Save named color…',command=self.save_color).pack(fill='x')
        ttk.Button(paint,text='Paint qualified region',command=self.paint_selected_region).pack(fill='x',pady=5)
        ttk.Label(paint,text='RGB bytes 0–255. Luminance tint inside a hash-pinned greyscale mask; black protects logos and other content. Alpha stays unchanged. Shared atlases require an explicit mask.',wraplength=350).pack(fill='x')
        ttk.Button(paint,text='Browse local stock materials…',command=self.browse_stock_materials).pack(fill='x',pady=8)
        self.appearance_edits=tk.Text(paint,height=8,width=40,bg='#191d23',fg='#d5dae0',wrap='word');self.appearance_edits.pack(fill='both',expand=True)
        ttk.Button(paint,text='Paint / style help',command=lambda:self.show_help('appearance')).pack(fill='x')
        crew=ttk.Frame(tabs,padding=8);tabs.add(crew,text='Crew Inspector')
        ttk.Label(crew,text='Existing qualified stock crew · rigid rest-pose correction\nNo skeleton or animation authoring.',wraplength=350).pack(fill='x')
        ttk.Button(crew,text='Import qualified crew preset…',command=self.import_crew_preset).pack(fill='x',pady=6)
        ttk.Button(crew,text='Qualify crew from conversion report…',command=self.qualify_crew_report).pack(fill='x')
        self.crew_name=tk.StringVar();self.crew_box=ttk.Combobox(crew,textvariable=self.crew_name,state='readonly');self.crew_box.pack(fill='x');self.crew_box.bind('<<ComboboxSelected>>',lambda e:self.crew_selected())
        self.crew_values={}
        for key,label in [('lateral','Lateral X (m)'),('vertical','Vertical Y (m)'),('longitudinal','Longitudinal Z (m)'),('yaw_degrees','Yaw (degrees)')]:
            row=ttk.Frame(crew);row.pack(fill='x',pady=3);ttk.Label(row,text=label).pack(side='left');v=tk.StringVar(value='0');self.crew_values[key]=v;entry=ttk.Entry(row,textvariable=v,width=10);entry.pack(side='right');hint(entry,'Compiled rigid rest-pose correction, relative to the immutable imported model. Does not change physics, cameras or animation controls.')
        ttk.Button(crew,text='Apply crew correction',command=self.apply_crew_correction).pack(fill='x',pady=5)
        ttk.Button(crew,text='Reset person rest pose',command=lambda:self.apply_crew_correction(reset=True)).pack(fill='x')
        ttk.Button(crew,text='Highlight crew component',command=self.highlight_crew).pack(fill='x',pady=5)
        self.crew_details=tk.Text(crew,width=40,height=14,bg='#191d23',fg='#d5dae0',wrap='word');self.crew_details.pack(fill='both',expand=True)
        ttk.Button(crew,text='Crew fitting help',command=lambda:self.show_help('crew')).pack(fill='x')

    def appearance_loaded(self):
        if not self.project:return
        p=self.project;self.appearance_name.set(p.data.get('appearance','Source Fidelity'))
        regions=list(p.data.get('paint_regions',{}));self.region_box['values']=regions
        if self.paint_region_name.get()not in regions:self.paint_region_name.set(regions[0]if regions else '')
        self.color_box['values']=list({**COLOR_PRESETS,**p.data.get('color_presets',{})})
        generation=p.data.get('classic_generation',{});status='Qualified immutable-source Classic version'if generation.get('version_style')=='Classic MR Style'else'Original Source Fidelity; independent Classic version available'if generation else'Manual appearance snapshots only; Rebuild as Classic generates a qualified conversion'
        self.appearance_edits.delete('1.0','end');self.appearance_edits.insert('end',json.dumps({'conversion':status,'textures':{n:e['operation']for n,e in p.data['edits'].items()},'surfaces':p.data.get('surfaces',{})},indent=2))
        model={'Race':'car.dx','Frontend':'complete.dx','Wheel':'wheel.dx'}[self.variant.get()]
        people=list(p.data.get('crew',{}).get(model,{}).get('definition',{}).get('people',{}));self.crew_box['values']=people
        if self.crew_name.get()not in people:self.crew_name.set(people[0]if people else '')
        self.crew_selected()

    def appearance_action(self,label,operation):
        if self.project and not self.busy:self.run(label,operation,lambda _:self.refresh())

    def appearance_switch(self):
        if not self.project:return
        name=self.appearance_name.get();links=self.project.data.get('style_versions',{})
        if name in links:
            from .service import WorkshopProject
            if Path(links[name])!=self.project.root:self._opened(WorkshopProject(links[name]))
            elif self.project.data.get('appearance')!=name:self.appearance_action('Restore this version edit layer',lambda:self.project.switch_appearance(name))
            return
        if name=='Classic MR Style':
            self.appearance_name.set(self.project.data.get('appearance','Source Fidelity'));self.rebuild_classic_version();return
        self.appearance_action('Switch custom appearance snapshot',lambda:self.project.switch_appearance(name))

    def rebuild_classic_version(self):
        if not self.project or self.busy:return
        recipe=filedialog.askopenfilename(title='Qualified Classic conversion recipe (exact source hashes)',filetypes=[('JSON','*.json')],parent=self.root)
        if not recipe:return
        stock=filedialog.askdirectory(title='Local read-only stock DataGx/Vehicles reference folder',parent=self.root)
        if not stock:return
        output=filedialog.asksaveasfilename(title='New Classic version folder (must not exist)',parent=self.root)
        if not output:return
        parent=self.project
        def build():
            from .classic import rebuild_classic
            return rebuild_classic(parent,recipe,stock,output)
        def opened(result):
            classic,fidelity,report=result;self.add_library(fidelity);self._opened(classic)
            messagebox.showinfo('Classic conversion generated','Source Fidelity remains independent. Inspect the preview and conversion report. Classic builds remain blocked until you explicitly approve that exact report.\n\nManual override conflicts: '+str(len(report['manual_layers']['conflicts'])),parent=self.root)
        self.run('Rebuild Classic from immutable import',build,opened)

    def review_classic_report(self):
        if not self.project:return
        g=self.project.data.get('classic_generation')
        if not g:messagebox.showinfo('Classic report','Generate a qualified Classic version first.',parent=self.root);return
        report=Path(g['report']).read_text(encoding='utf-8');win=tk.Toplevel(self.root);apply_icon(win);win.title('Classic conversion report — review before build');win.geometry('1000x750')
        text=tk.Text(win,wrap='word');text.pack(fill='both',expand=True);text.insert('1.0',report);text.configure(state='disabled')
        project=self.project
        def accept():
            if not messagebox.askyesno('Approve this Classic build input?','I reviewed this conversion report, the preview and its omissions/approximations. Allow this exact Classic version as a build input?',parent=win):return
            from .classic import approve_classic
            try:approve_classic(project,g['report_sha256'])
            except ValueError as exc:messagebox.showerror('Report changed',str(exc),parent=win);return
            win.destroy();self.status.set('Exact Classic report approved for builds.')
        ttk.Button(win,text='Approve this exact report for builds',command=accept).pack(pady=8)

    def import_paint_mask(self):
        if not self.project:return
        texture=self.texture_name.get()
        if not texture:messagebox.showerror('Paint mask','Select its owned texture in Texture Studio first.',parent=self.root);return
        path=filedialog.askopenfilename(title='Exact-size opaque greyscale mask for '+texture,filetypes=[('PNG','*.png')],parent=self.root)
        if not path:return
        name=simpledialog.askstring('Paint region','Name this qualified region:',parent=self.root)
        if not name:return
        evidence=simpledialog.askstring('Mask qualification','Describe verified paint ownership and protected logos/decals/windows:',parent=self.root)
        if not evidence:return
        self.appearance_action('Register qualified mask',lambda:self.project.register_paint_region(name,texture,path,evidence))

    def _paint_rgb(self):return [int(x.strip())for x in self.paint_color.get().split(',')]

    def choose_color_preset(self):
        if self.project:
            value={**COLOR_PRESETS,**self.project.data.get('color_presets',{})}.get(self.color_name.get())
            if value:self.paint_color.set(','.join(str(x)for x in value))

    def save_color(self):
        if not self.project:return
        name=simpledialog.askstring('Color preset','Preset name:',parent=self.root)
        if name:self.appearance_action('Save named color',lambda:self.project.save_color_preset(name,self._paint_rgb()))

    def paint_selected_region(self):
        if self.project and self.paint_region_name.get():self.appearance_action('Paint qualified mask',lambda:self.project.paint_region(self.paint_region_name.get(),self._paint_rgb()))

    def import_crew_preset(self):
        if not self.project:return
        path=filedialog.askopenfilename(title='Hash-qualified crew preset',filetypes=[('JSON','*.json')],parent=self.root)
        if not path:return
        def register():
            values=json.loads(Path(path).read_text());definitions=values.get('models',values)
            self.project.register_crew_models(definitions)
        self.appearance_action('Register qualified crew components',register)

    def crew_selected(self):
        if not self.project:return
        model={'Race':'car.dx','Frontend':'complete.dx','Wheel':'wheel.dx'}[self.variant.get()];entry=self.project.data.get('crew',{}).get(model)
        self.crew_details.delete('1.0','end')
        if not entry or not self.crew_name.get():self.crew_details.insert('end','No qualified existing crew selector for this model revision. Import an exact-hash preset; geometry guessing and automatic rig generation are unsupported.');return
        person=self.crew_name.get();placement=entry['placements'].get(person,{})
        for k,v in self.crew_values.items():v.set(str(placement.get(k,0)))
        from master_rallye.crew_authoring import apply_crew_fit
        from .service import sha
        raw=(self.project.assets/model).read_bytes()
        # Inspect from baseline so an applied placement is never applied twice.
        raw=(self.project.baseline/model).read_bytes();_,report=apply_crew_fit(raw,entry['definition'],entry['placements'],source_sha256=sha(raw))
        self.crew_details.insert('end',json.dumps({'model':model,'preset':entry['definition'].get('preset'),'qualification':entry['definition']['evidence'],'person':next(r for r in report if r['person']==person),'scope':'Compiled resource change. Gameplay of new positions is unconfirmed; existing animation/control records preserved.'},indent=2))

    def qualify_crew_report(self):
        if not self.project:return
        path=filedialog.askopenfilename(title='Original converter report for this exact model revision',filetypes=[('JSON','*.json')],parent=self.root)
        if not path:return
        def qualify():
            from master_rallye.crew_authoring import qualify_converted_crew
            report=json.loads(Path(path).read_text());definitions={}
            for model in ('car.dx','complete.dx'):
                definitions[model]=qualify_converted_crew((self.project.baseline/model).read_bytes(),report,model)
            self.project.register_crew_models(definitions)
        self.appearance_action('Qualify exact converted stock crew',qualify)

    def apply_crew_correction(self,reset=False):
        if not self.project or not self.crew_name.get():return
        model={'Race':'car.dx','Frontend':'complete.dx','Wheel':'wheel.dx'}[self.variant.get()];person=self.crew_name.get()
        def operation():return self.project.fit_crew(model,person,{k:0 if reset else float(v.get())for k,v in self.crew_values.items()})
        self.appearance_action('Compile crew rest-pose correction',operation)

    def highlight_crew(self):
        if not self.project or not self.crew_name.get():return
        model={'Race':'car.dx','Frontend':'complete.dx','Wheel':'wheel.dx'}[self.variant.get()]
        person=self.project.data['crew'][model]['definition']['people'][self.crew_name.get()]
        node=self._draw_node(model,person['draws'][0]);self.draws.selection_set(node);self.draws.see(node);self._draw_selected()

    def compare_appearance(self):
        if not self.project or self.busy:return
        project=self.project;variant=self.variant.get();assembled=self.assembled.get()
        def render():
            from .classic import source_project
            _,before=self._render(source_project(project),variant,assembled=assembled,original=True)
            _,after=self._render(project,variant,assembled=assembled,original=False)
            return before,after
        def show(pair):
            a,b=(Image.open(io.BytesIO(p)).convert('RGB')for p in pair);diff=ImageEnhance.Contrast(ImageChops.difference(a,b)).enhance(3)
            window=tk.Toplevel(self.root);apply_icon(window);window.title('Matched GPU views — Original / Modified / Difference ×3');window.geometry('1250x530');window.images=[]
            for label,image in zip(('Original','Modified','Difference ×3'),(a,b,diff)):
                frame=ttk.Frame(window);frame.pack(side='left',fill='both',expand=True);ttk.Label(frame,text=label).pack();image.thumbnail((400,430));photo=ImageTk.PhotoImage(image);window.images.append(photo);ttk.Label(frame,image=photo).pack()
            project.root.joinpath('preview/comparison-before.png').write_bytes(pair[0]);project.root.joinpath('preview/comparison-after.png').write_bytes(pair[1]);diff.save(project.root/'preview/comparison-difference.png')
        self.run('Render matched before / after',render,show)

    def browse_stock_materials(self):
        if not self.project:return
        folder=filedialog.askdirectory(title='Local stock MR vehicle family (read-only reference)',parent=self.root)
        if not folder:return
        def show(rows):
            win=tk.Toplevel(self.root);apply_icon(win);win.title('Local stock materials — explicit compatibility');win.geometry('1000x700')
            ttk.Label(win,text='Reference catalogue only. No automatic paint classification or UV adaptation. Select a target surface in the main inspector first.',wraplength=950).pack(fill='x',padx=10,pady=8)
            tree=ttk.Treeview(win,columns=('model','draw','slot','image','size'),show='headings',height=12);tree.pack(fill='both',expand=True)
            for key in ('model','draw','slot','image','size'):tree.heading(key,text=key);tree.column(key,width=150)
            refs={};details=tk.Text(win,height=9,wrap='word');details.pack(fill='x')
            for row in rows:
                for texture in row['textures']:
                    key=str(len(refs));refs[key]=(row,texture);tree.insert('','end',iid=key,values=(row['model'],row['draw'],texture['slot'],texture['stem'],f"{texture['width']} × {texture['height']}"))
            def selected(*_):
                if tree.selection():details.delete('1.0','end');details.insert('end',json.dumps(refs[tree.selection()[0]],indent=2))
            tree.bind('<<TreeviewSelect>>',selected)
            def apply():
                selection=self._surface_selection()
                if not tree.selection()or not selection:return
                model,draw=selection;row,texture=refs[tree.selection()[0]]
                slot=simpledialog.askinteger('Target slot','Existing target slot: 0 diffuse, 1 opaque environment',minvalue=0,maxvalue=1,parent=win)
                if slot is None:return
                from master_rallye.dx import parse_dx_bytes
                from master_rallye.assets import AssetResolver
                native=parse_dx_bytes((self.project.assets/model).read_bytes());target=AssetResolver(self.project.assets).resolve_texture(native.physical_draws[draw].texture_tuple[slot])
                if target is None:messagebox.showerror('No owned image','The target slot is empty.',parent=win);return
                usage=self.project.texture_usage(target.name)
                impact=tk.Toplevel(win);apply_icon(impact);impact.title('All affected texture uses');impact.geometry('720x520')
                ttk.Label(impact,text=f'{target.name}: {len(usage)} affected slots. Native UVs stay unchanged. Review shared ownership before applying.',wraplength=680).pack(padx=10,pady=8)
                listing=tk.Text(impact,wrap='word');listing.pack(fill='both',expand=True,padx=10);listing.insert('end',json.dumps(usage,indent=2));listing.configure(state='disabled')
                approved=tk.BooleanVar(value=False)
                def accept():approved.set(True);impact.destroy()
                ttk.Button(impact,text='Apply to these declared uses',command=accept).pack(fill='x',padx=10,pady=8)
                impact.transient(win);impact.grab_set();win.wait_window(impact)
                if not approved.get():return
                resize=False
                if slot==1:resize=messagebox.askyesno('Environment map dimensions','Allow filtered resizing of this opaque environment reference to the existing owned texture dimensions? Diffuse resizing remains unsupported.',parent=win)
                win.destroy();self.appearance_action('Apply explicit local stock reference',lambda:self.project.use_stock_texture(model,draw,slot,texture,allow_shared=True,resample_environment=resize))
            ttk.Button(win,text='Use reference on selected owned slot…',command=apply).pack(fill='x',padx=10,pady=6)
        self.run('Inspect local stock material states',lambda:self.project.stock_materials(folder),show)
