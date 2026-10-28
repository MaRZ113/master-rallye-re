"""Original GT colorway selection history over immutable independent versions.

Switching source color never recolors a texture or destructively rebaselines an
edited Workshop project. Each original variant has its own editable project.
Selection Undo/Redo/Restore is separate from manual Paint/Material edit history.
"""
import copy,json,shutil
from pathlib import Path
from .gt3_vehicle import build,digest
from .gt3_source import inspect_car,read_source
from .gt3_colourways import catalog,select
from .addon_sdk.import_project import prepare
from .workshop.service import WorkshopProject,write_json,plain_tree

class GTSourceProject:
    def __init__(self,root):
        self.root=plain_tree(root).resolve();self.path=self.root/'gt-source-project.json'
        self.data=json.loads(self.path.read_text(encoding='utf-8'))
        if self.data.get('schema')!='gt-source-project/1':raise ValueError('Unsupported GT source project')
        for name,expected in self.data['immutable'].items():
            if name not in ('model.bin','profile.json','carcolor.db','carcolor.sdb','identity.json'):raise ValueError('Unsafe GT source project input')
            if digest((self.root/'inputs'/name).read_bytes())!=expected:raise ValueError('GT source project immutable input changed: '+name)
        colours=self.data['colourways']
        for index in [self.data['selected'],self.data['default'],*self.data['undo'],*self.data['redo']]:
            if type(index)is not int or not 0<=index<len(colours):raise ValueError('Invalid GT source selection history')
        if len(self.data['undo'])>256 or len(self.data['redo'])>256:raise ValueError('GT source selection history budget')

    @classmethod
    def create_auto(cls,source,donor,inventory,region,car_key,colour_database,colour_strings,identity,output,*,render_ui,mode='full',colour=0):
        """Reuse automatic geometry fitting with an exact original catalog join."""
        inventory=plain_tree(inventory)
        if inventory.stat().st_size>192*1024*1024:raise ValueError('GT inventory report budget')
        raw_inventory=inventory.read_bytes();report=json.loads(raw_inventory)
        if report.get('schema')!='gt-garage-inventory/1':raise ValueError('Qualified Garage source inventory required')
        cars=report.get('catalogs',{}).get(region,{}).get('vehicles',[])
        matches=[c for c in cars if c['car_key']==car_key]
        if len(matches)!=1 or matches[0]['association_status']!='PASS':raise ValueError('Exact source catalog association required')
        car=matches[0];entry=report['members'].get('cars/day/'+str(car.get('model_code')),{});raw=read_source(source)
        if entry.get('status')!='PASS'or entry.get('sha256')!=digest(raw):raise ValueError('Catalog/source member hash mismatch')
        engine=report['source'].get('edition_files',{}).get('CORE.GT3',{}).get('sha256')
        from .addon_sdk.gt3_scene import GT3_CORE_SHA256
        if engine!=GT3_CORE_SHA256:raise ValueError('Automatic GT3 source edition requires separate native qualification')
        for path,key in ((colour_database,'catalog'),(colour_strings,'strings')):
            if digest(Path(path).read_bytes())!=report.get('colour_sources',{}).get(key,{}).get('decoded_sha256'):raise ValueError('Original color tables differ from source inventory')
        from .gt_auto_profile import derive
        profile,fit=derive(source,donor,mode=mode,engine_sha256=engine,model_key=car['association_evidence']['model_key'],identity={'model_code':car['model_code'],'car_key':car_key,'catalog_region':region,'volume_sha256':report['source']['sha256'],'association':car['association_evidence']})
        project=cls.create(source,donor,profile,colour_database,colour_strings,identity,output,render_ui=render_ui,colour=colour)
        project.data['automatic_derivation']={'inventory_sha256':digest(raw_inventory),'car_key':car_key,'region':region,'mode':mode,'fit_report':fit,'boundary':'Original catalog/colorway association; automatic donor fit is an authoring approximation, not recovered native GT3 rig.'};project.save();return project

    @classmethod
    def create(cls,source,donor,profile,colour_database,colour_strings,identity,output,*,render_ui,colour=0):
        output=plain_tree(output).resolve()
        if output.exists():raise ValueError('GT source project requires a fresh directory')
        source=plain_tree(source);donor=plain_tree(donor)
        if output.is_relative_to(donor.resolve()):raise ValueError('GT source project output must be outside retail donor')
        raw=read_source(source);parsed=inspect_car(raw);profile=copy.deepcopy(profile)
        if digest(raw)!=profile['source_sha256']:raise ValueError('Source/profile identity mismatch')
        colour_database=Path(colour_database).read_bytes();colour_strings=Path(colour_strings).read_bytes()
        names=catalog(colour_database,colour_strings)
        choices=[select(names,int(profile['model_key'],0),i,parsed['body'])for i in range(parsed['body']['source_colourway_count'])]
        if type(colour)is not int or not 0<=colour<len(choices):raise ValueError('Original source colourway outside catalog')
        if set(identity)!={'name','family','manufacturer','model'}:raise ValueError('Explicit addon identity required')
        output.mkdir(parents=True);inputs=output/'inputs';inputs.mkdir()
        (inputs/'model.bin').write_bytes(raw);(inputs/'carcolor.db').write_bytes(colour_database);(inputs/'carcolor.sdb').write_bytes(colour_strings)
        write_json(inputs/'profile.json',profile);write_json(inputs/'identity.json',{'addon':identity})
        write_json(output/'gt-source-project.json',{'schema':'gt-source-project/1','original_source':str(source.resolve()),'donor':str(donor.resolve()),'immutable':{p.name:digest(p.read_bytes())for p in inputs.iterdir()},'colourways':choices,'selected':colour,'default':colour,'undo':[],'redo':[],'versions':{},'boundary':'Each original colorway owns an independent Workshop project. Manual edits are preserved per version, never silently copied across source colors. No game registration or installation.'})
        project=cls(output);project._ensure(colour,render_ui);project.save();return project

    def save(self):write_json(self.path,self.data)

    def _ensure(self,index,render_ui):
        key=str(index)
        if key in self.data['versions']:
            self.current(index).verify_inputs();return
        version=self.root/'versions'/f'colour-{index:03d}';inputs=self.root/'inputs'
        if version.exists():raise ValueError('Incomplete colorway build retained for diagnosis; choose a fresh source project')
        profile=json.loads((inputs/'profile.json').read_text(encoding='utf-8'));candidate=version/'converted'
        build(inputs/'model.bin',Path(self.data['donor']),profile,candidate,colour=index,colour_database=inputs/'carcolor.db',colour_strings=inputs/'carcolor.sdb')
        author=prepare(candidate,Path(self.data['donor']),inputs/'identity.json',version/'authoring',render_ui=render_ui,source_format='GT3 ModelSet1')
        workshop=WorkshopProject.create(author,version/'workshop')
        workshop.data['source_colourway']={'source_project':str(self.root),'source_index':index,'record':self.data['colourways'][index],'boundary':'Original palette/material variant; manual paint is separate.'};workshop.save()
        self.data['versions'][key]={'root':str(workshop.root.relative_to(self.root)),'report_sha256':digest((candidate/'conversion-report.json').read_bytes())}

    def current(self,index=None):
        index=self.data['selected']if index is None else index
        record=self.data['versions'].get(str(index))
        if record is None:raise ValueError('Source colourway has not been built')
        path=(self.root/record['root']).resolve()
        if not path.is_relative_to(self.root/'versions'):raise ValueError('Source colorway version escapes project')
        report=path.parent/'converted/conversion-report.json'
        if digest(report.read_bytes())!=record['report_sha256']:raise ValueError('Source colorway conversion report changed')
        return WorkshopProject(path)

    def choose(self,index,*,render_ui):
        if type(index)is not int or not 0<=index<len(self.data['colourways']):raise ValueError('Original source colourway outside catalog')
        self._ensure(index,render_ui)
        if index!=self.data['selected']:
            self.data['undo']=(self.data['undo']+[self.data['selected']])[-256:];self.data['redo']=[];self.data['selected']=index;self.save()
        return self.current()

    def step(self,redo=False):
        source,target=('redo','undo')if redo else('undo','redo')
        if not self.data[source]:return self.current()
        selected=self.data[source][-1];self.current(selected).verify_inputs()
        self.data[source].pop();self.data[target]=(self.data[target]+[self.data['selected']])[-256:];self.data['selected']=selected;self.save();return self.current()

    def restore(self):
        return self.choose(self.data['default'],render_ui=None)
