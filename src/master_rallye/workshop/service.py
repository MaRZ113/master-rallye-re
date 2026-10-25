"""Thin authoring service over the established SDK, DX/DXT and stock APIs.

Inputs are never edited. Every Workshop project owns a private working copy,
an immutable rendered baseline, typed edit recipes and fresh build directories.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import tempfile
import uuid
import zlib

from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes, encode_png, encode_dxt_pixels, PNG_ROWS_FLIP_VERTICAL
from master_rallye.texture_authoring import decode_rgba_png
from master_rallye.vehicle_project import VehicleProject, validate_vehicle
from master_rallye.addon_sdk import stock_project
from master_rallye.material_semantics import MaterialSemantics
from .adapters import EXTENSION_NAMES as EXTENSIONS,validate_extensions

def sha(data): return hashlib.sha256(data).hexdigest()

def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    os.replace(temporary,path)

def write_resource(path, raw):
    import time
    path=Path(path);temporary=path.with_name(path.name+'.updating')
    if path.is_file() and path.read_bytes()==raw:return
    temporary.write_bytes(raw)
    for attempt in range(20):
        try:os.replace(temporary,path);return
        except PermissionError:
            if attempt==19:raise
            time.sleep(.05)

def plain_tree(root):
    root=Path(root).absolute()
    for p in (root,*root.parents):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('Linked paths are not supported')
    if root.exists():
        for p in root.rglob('*'):
            if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('Linked source resources are not supported')
    return root

def _compiled_addon(project):
    author=VehicleProject.load(Path(project)/'vehicle-project.json')
    result=validate_vehicle(author)
    if result['status']=='FAIL':raise ValueError('; '.join(d['message'] for d in result['diagnostics']))
    resources={f.name:f.read_bytes() for f in author.source_vehicle_dir.iterdir() if f.is_file() and f.suffix.lower() in ('.dx','.dxt')}
    resources.update(result['compiled'])
    for role in ('car.dx','complete.dx','wheel.dx'):
        spec=author.resources.get(role,{})
        for key in ('scene_candidate','native_brake_scene_candidate'):
            if key in spec:
                profile=author.resolve(spec[key]).parent/'preview-profile.json'
                if profile.is_file() and 'preview-profile.json' not in resources:resources['preview-profile.json']=profile.read_bytes()
    return resources

def _owned(root, name):
    if not isinstance(name,str) or Path(name).name!=name or '/' in name or '\\' in name or ':' in name:raise ValueError('Unsafe resource name')
    return Path(root)/name

def declared_resource_identity(folder):
    """Read an existing sealed runtime's identity for inspection, never allocate."""
    folder=Path(folder).resolve()
    for parent in tuple(folder.parents)[:6]:
        plan_path=parent/'addon-plan.json';manifest_path=parent/'resource-manifest.json'
        if not plan_path.is_file() or not manifest_path.is_file():continue
        resource_root=parent/'resource-root'
        if not folder.is_relative_to(resource_root):continue
        relative=folder.relative_to(resource_root).as_posix()
        plan=json.loads(plan_path.read_text());manifest=json.loads(manifest_path.read_text())
        match=[r for r in plan.get('addons',[]) if r.get('assets',{}).get('model_package_root')==relative]
        record=next((r for r in manifest['resources'] if r['path']==relative+'/car.dx'),None)
        if len(match)==1 and record and sha((folder/'car.dx').read_bytes())==record['sha256']:
            return match[0]['addon_id'],match[0]['physical_id']
    return folder.name,None

class WorkshopProject:
    def __init__(self, root):
        self.root=plain_tree(root).resolve()
        self.data=json.loads((self.root/'workshop-project.json').read_text(encoding='utf-8'))
        if self.data.get('version')!=1 or self.data.get('kind') not in ('addon','stock','family'):raise ValueError('Unsupported Workshop project')
        if not isinstance(self.data.get('edits'),dict) or not isinstance(self.data.get('inputs'),dict):raise ValueError('Invalid project edit/input records')
        if set(self.data['edits'])-set(self.data['inputs']):raise ValueError('Edit targets an unowned resource')
        validate_extensions(self.data.get('extensions',{}))
        for name in self.data['inputs']:_owned(self.baseline,name)
        self.working=self.root/'working'

    @property
    def baseline(self):return self.root/'baseline'
    @property
    def assets(self):return self.root/'preview/assets'

    @classmethod
    def create(cls, source, output, *, kind=None, family=None, car_id=None):
        source=plain_tree(source).resolve();output=plain_tree(output).resolve()
        if output.exists():raise ValueError('Choose a fresh Workshop project folder')
        if output.is_relative_to(source):raise ValueError('Workshop output must be outside original inputs')
        if kind=='stock-new':
            output.mkdir(parents=True)
            try:stock_project.create(source,output/'working',family,car_id)
            except Exception:
                # Keep diagnostic directory; never remove user input trees.
                raise
            source_project=output/'working';kind='stock'
        else:
            kind=kind or ('addon' if (source/'addon.json').is_file() else 'stock' if (source/'stock-project.json').is_file() else 'family')
            output.mkdir(parents=True);source_project=source
            if kind in ('addon','stock'):shutil.copytree(source,output/'working')
            else:(output/'working').mkdir()
        author_sources={};imported_edits={}
        if kind=='addon':
            # Resolve source-relative paths before moving the authoring project.
            spec=json.loads((source_project/'vehicle-project.json').read_text())
            original=VehicleProject.load(source_project/'vehicle-project.json')
            spec['source_vehicle_dir']=str(original.source_vehicle_dir)
            for edit in spec['resources'].values():
                for key in ('candidate','topology_candidate','scene_candidate','native_brake_scene_candidate'):
                    if key in edit:edit[key]=str(original.resolve(edit[key]))
            for category,key in (('texture_edits','png'),('texture_replacements','candidate')):
                for edit in spec.get(category,{}).values():edit[key]=str(original.resolve(edit[key]))
            write_json(output/'working/vehicle-project.json',spec)
            write_json(output/'original-author.json',spec)
            manifest=json.loads((source_project/'addon.json').read_text());identity=manifest['addon_id']
            files=_compiled_addon(output/'working')
            paths=[f for f in original.source_vehicle_dir.iterdir() if f.is_file() and f.suffix.lower() in ('.dx','.dxt')]
            for edit in spec['resources'].values():
                paths.extend(Path(edit[key]) for key in ('candidate','topology_candidate','scene_candidate','native_brake_scene_candidate') if key in edit)
            for category,key in (('texture_edits','png'),('texture_replacements','candidate')):
                paths.extend(Path(edit[key]) for edit in spec.get(category,{}).values())
            author_sources={str(f):sha(f.read_bytes()) for f in paths}
        elif kind=='stock':
            metadata=json.loads((output/'working/stock-project.json').read_text());stock_project.identity(metadata['family'],metadata['car_id'])
            identity=metadata['family'];family=identity;car_id=metadata['car_id']
            changed=stock_project.validated_overrides(output/'working')
            if any(not name.lower().endswith('.dxt') for name in changed):raise ValueError('Existing stock geometry edits need the resource inspection workflow; texture-only Workshop import will not discard them')
            if len({Path(rel).name for rel in metadata['original_sha256']})!=len(metadata['original_sha256']):raise ValueError('Ambiguous nested stock resource names')
            imported_edits={Path(rel).name:raw for rel,raw in changed.items()}
            # Original pinned retail bytes, not an accidentally pre-edited copy.
            files={Path(rel).name:stock_project.safe(Path(metadata['source_root']),rel).read_bytes() for rel in metadata['original_sha256']}
            if any(sha(files[Path(rel).name])!=h for rel,h in metadata['original_sha256'].items()):raise ValueError('Original retail resource hash changed')
        elif kind=='family':
            family=source.name;identity=family
            declared,declared_id=declared_resource_identity(source)
            if car_id is None:car_id=declared_id
            identity=declared
            files={f.name:f.read_bytes() for f in source.iterdir() if f.is_file() and f.suffix.lower() in ('.dx','.dxt')}
            if (source/'preview-profile.json').is_file():files['preview-profile.json']=(source/'preview-profile.json').read_bytes()
            if not {'car.dx','complete.dx'}<=set(files):raise ValueError('Converted family needs car.dx and complete.dx')
        else:raise ValueError('Unsupported authoring kind')
        baseline=output/'baseline';baseline.mkdir()
        for name,raw in files.items():_owned(baseline,name).write_bytes(raw)
        data={'version':1,'kind':kind,'identity':identity,'family':family,'car_id':car_id,'source':str(source),
              'inputs':{name:sha(raw) for name,raw in files.items()},'edits':{},'history':[],
              'author_sources':author_sources,
              'extensions':{key:[] for key in EXTENSIONS},'build_settings':{},'last_build':None,
              'limitations':'D3D9 diagnostic preview; texture edits are whole-image overrides, not semantic base-paint recoloring'}
        if imported_edits:
            folder=output/'overrides';folder.mkdir()
            for name,raw in imported_edits.items():
                _owned(folder,sha(raw)+'.dxt').write_bytes(raw)
                data['edits'][name]={'operation':'existing-stock-override','baseline_sha256':data['inputs'][name],'output_sha256':sha(raw),'scope':'existing user authoring'}
        write_json(output/'workshop-project.json',data)
        project=cls(output);project.materialize();return project

    def save(self):
        validate_extensions(self.data.get('extensions',{}))
        write_json(self.root/'workshop-project.json',self.data)

    def configure_build(self, settings):
        if set(settings)!={'roster_candidate','retail_sma','retail_root'}:raise ValueError('Unsupported build inputs')
        folder=Path(settings['roster_candidate'])
        if not (folder/'roster-config.json').is_file():raise ValueError('Select an existing qualified roster candidate folder')
        if self.data['kind']=='addon':
            if not Path(settings['retail_sma']).is_file() or not Path(settings['retail_root']).is_dir():raise ValueError('Original Data.sma and unpacked retail data are required')
            roster=json.loads((folder/'roster-config.json').read_text())
            matches=[row for row in roster['projects'] if json.loads((Path(row['project'])/'addon.json').read_text())['addon_id']==self.data['identity']]
            if len(matches)!=1:raise ValueError('Selected roster needs exactly one matching author entry')
            self.data['car_id']=matches[0]['physical_id']
        self.data['build_settings']=settings;self.save()

    def verify_inputs(self):
        for path,expected in self.data.get('author_sources',{}).items():
            if sha(Path(path).read_bytes())!=expected:raise ValueError('Original author input changed: '+path)
        for name,expected in self.data['inputs'].items():
            if sha(_owned(self.baseline,name).read_bytes())!=expected:raise ValueError('Workshop baseline changed: '+name)

    def _record(self):
        self.data['history'].append(self._state())
        self.data['history']=self.data['history'][-30:]
        self.data['redo']=[]

    def _state(self):return json.loads(json.dumps({'__workshop_state__':1,'textures':self.data['edits'],'surfaces':self.data.get('surfaces',{})}))

    def _load_state(self,state):
        if state.get('__workshop_state__')==1:self.data['edits']=state['textures'];self.data['surfaces']=state['surfaces']
        else:self.data['edits']=state;self.data['surfaces']={}

    def edit_surface(self,model,draw_id,*,rgb=None,disable_reflection=None):
        from master_rallye.surface_authoring import apply_surface_edits
        if model not in ('car.dx','complete.dx','wheel.dx'):raise ValueError('Unsupported model')
        recipe=dict(self.data.get('surfaces',{}).get(model,{}).get(str(draw_id),{'draw_id':draw_id}))
        if rgb is not None:recipe['rgb']=rgb
        if disable_reflection is not None:recipe['disable_reflection']=disable_reflection
        raw=_owned(self.baseline,model).read_bytes();apply_surface_edits(raw,[recipe],source_sha256=sha(raw))
        self._record();self.data.setdefault('surfaces',{}).setdefault(model,{})[str(draw_id)]=recipe;self.materialize();self.save()

    def restore_surface(self,model,draw_id):
        self._record();self.data.setdefault('surfaces',{}).get(model,{}).pop(str(draw_id),None);self.materialize();self.save()

    def texture_usage(self,name):
        from master_rallye.assets import AssetResolver
        result=[];resolver=AssetResolver(self.assets);resolved_slots={}
        for path in sorted(self.assets.glob('*.dx')):
            model=parse_dx_bytes(path.read_bytes())
            for d in model.physical_draws:
                for slot in d.texture_slots:
                    if slot.value not in resolved_slots:resolved_slots[slot.value]=resolver.resolve_texture(slot.value)
                    resolved=resolved_slots[slot.value]
                    if resolved and resolved.name.casefold()==name.casefold():result.append({'model':path.name,'draw':d.draw_index,'slot':slot.slot,'group':d.group_label})
        return result

    def texture(self,name):return parse_dxt_bytes(_owned(self.assets,name).read_bytes())

    def preview_profile(self):
        """Preview-only rest pose, never a physics or runtime resource edit."""
        if self.data.get('preview_only') is not None:return self.data['preview_only']
        path=self.baseline/'preview-profile.json'
        if path.exists():return json.loads(path.read_text())
        from master_rallye.preview_scene import presentation_wheels
        try:return presentation_wheels(*(parse_dx_bytes((self.baseline/n).read_bytes()) for n in ('car.dx','complete.dx','wheel.dx')))
        except (ValueError,FileNotFoundError) as e:return {'provenance':'No qualified assembly: '+str(e),'race_wheel_instances':[]}

    def save_preview_profile(self,config):
        if not isinstance(config,dict) or len(config.get('race_wheel_instances',[])) not in (0,4):raise ValueError('Preview layout requires four wheels or an empty raw layout')
        from master_rallye.preview_scene import stage_vehicle
        path=self.root/'preview/wheel-edit.json';write_json(path,config)
        stage_vehicle(self.assets/'car.dx',self.root/'preview/wheel-check.mrpv',profile=path)
        self.data['preview_only']=config;self.save()

    def preview_profile_path(self):
        path=self.root/'preview/active-profile.json';write_json(path,self.preview_profile());return path

    def tint(self,name,rgb):
        self.verify_inputs();texture=parse_dxt_bytes(_owned(self.baseline,name).read_bytes())
        if len(rgb)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=2 for v in rgb):raise ValueError('RGB multipliers must be finite in0..2')
        pixels=bytearray(texture.bgra)
        for offset,gain in ((2,rgb[0]),(1,rgb[1]),(0,rgb[2])):
            pixels[offset::4]=bytes(min(255,round(v*gain)) for v in pixels[offset::4])
        self._record();self._apply(name,bytes(pixels),{'operation':'rgb-multiply','rgb':list(rgb),'alpha':'preserved','scope':'whole texture including any baked decals'})

    def replace_png(self,name,path):
        self.verify_inputs();template=parse_dxt_bytes(_owned(self.baseline,name).read_bytes());raw=Path(path).read_bytes()
        w,h,rgba=decode_rgba_png(raw)
        if (w,h)!=(template.width,template.height):raise ValueError('Replacement must retain source dimensions')
        native=encode_dxt_pixels(template,rgba,w,h,row_policy=PNG_ROWS_FLIP_VERTICAL)
        self._record();self._apply(name,native[20:],{'operation':'png-replace','input_sha256':sha(raw),'input_name':Path(path).name,'alpha':'user-supplied'})

    def _apply(self,name,pixels,recipe):
        texture=parse_dxt_bytes(_owned(self.baseline,name).read_bytes())
        raw=texture.header[:8]+struct.pack('<I',zlib.crc32(pixels)&0xffffffff)+texture.header[12:]+pixels
        parse_dxt_bytes(raw);folder=self.root/'overrides';folder.mkdir(exist_ok=True);_owned(folder,sha(raw)+'.dxt').write_bytes(raw)
        self.data['edits'][name]={**recipe,'affected_draws':self.texture_usage(name),'baseline_sha256':self.data['inputs'][name],'output_sha256':sha(raw)}
        self.materialize();self.save()

    def materialize(self):
        self.verify_inputs();self.assets.mkdir(parents=True,exist_ok=True)
        for name in self.data['inputs']:
            edited=self.data['edits'].get(name)
            raw=_owned(self.root/'overrides',edited['output_sha256']+'.dxt').read_bytes() if edited else _owned(self.baseline,name).read_bytes()
            if edited and sha(raw)!=edited['output_sha256']:raise ValueError('Edited texture changed outside project: '+name)
            write_resource(_owned(self.assets,name),raw)
        from master_rallye.surface_authoring import apply_surface_edits
        for model,edits in self.data.get('surfaces',{}).items():
            if model not in ('car.dx','complete.dx','wheel.dx'):raise ValueError('Unowned surface model')
            raw=_owned(self.baseline,model).read_bytes()
            output=apply_surface_edits(raw,list(edits.values()),source_sha256=self.data['inputs'][model]).data
            write_resource(_owned(self.assets,model),output)
        if self.data['kind']=='stock':
            meta=json.loads((self.working/'stock-project.json').read_text())
            for rel in meta['original_sha256']:
                shutil.copyfile(_owned(self.assets,Path(rel).name),stock_project.safe(self.working/'resources',rel))
        elif self.data['kind']=='addon':
            spec=json.loads((self.root/'original-author.json').read_text());original=VehicleProject.load(self.working/'vehicle-project.json')
            for model,edits in self.data.get('surfaces',{}).items():
                if edits:
                    entry=spec.setdefault('resources',{}).setdefault(model,{'source_sha256':sha((original.source_vehicle_dir/model).read_bytes())})
                    entry.setdefault('surface_layers',[]).append({'edits':list(edits.values()),'source_sha256':self.data['inputs'][model]})
            for name in self.data['edits']:
                png=self.root/'overrides'/(name+'.png');png.write_bytes(encode_png(self.texture(name)))
                donor=_owned(original.source_vehicle_dir,name).read_bytes()
                spec.setdefault('texture_replacements',{}).pop(name,None)
                spec.setdefault('texture_edits',{})[name]={'source_sha256':sha(donor),'png':str(png),'refresh_crc32':True}
            write_json(self.working/'vehicle-project.json',spec)

    def restore(self,name=None):
        self._record()
        if name is None:self.data['edits']={};self.data['surfaces']={}
        else:self.data['edits'].pop(name,None)
        self.materialize();self.save()

    def undo(self):
        if not self.data['history']:raise ValueError('No undo history')
        previous=self.data['history'].pop();self.data.setdefault('redo',[]).append(self._state())
        self._load_state(previous);self.materialize();self.save()

    def redo(self):
        if not self.data.get('redo'):raise ValueError('No redo history')
        state=self.data['redo'].pop();self.data['history'].append(self._state());self._load_state(state);self.materialize();self.save()

    def inspect(self,model='car.dx'):
        self.materialize();m=parse_dx_bytes(_owned(self.assets,model).read_bytes())
        if not m.diagnostics.validated:raise ValueError('DX semantic validation failed')
        textures=[]
        for f in sorted(self.assets.glob('*.dxt')):
            t=parse_dxt_bytes(f.read_bytes());textures.append({'name':f.name,'width':t.width,'height':t.height,'bytes':len(t.bgra),'sha256':sha(f.read_bytes()),'edited':f.name in self.data['edits']})
        draws=[{'id':d.draw_index,'group':d.group_label,'textures':[s.value for s in d.texture_slots],
                'flags':list(d.flags_0x20),'semantics':MaterialSemantics.from_draw(d).to_dict()} for d in m.physical_draws]
        return {'identity':self.data['identity'],'kind':self.data['kind'],'car_id':self.data['car_id'],
                'model':model,'vertices':m.vertex_count,'draws':draws,'textures':textures,'source':self.data['source'],
                'preview':'D3D9 fixed-function approximation; not actual game rendering'}

    def validate(self):
        self.materialize()
        for f in self.assets.iterdir():
            if f.suffix.lower()=='.dx' and not parse_dx_bytes(f.read_bytes()).diagnostics.validated:raise ValueError('Invalid DX: '+f.name)
            if f.suffix.lower()=='.dxt':parse_dxt_bytes(f.read_bytes())
        if self.data['kind']=='stock':
            with tempfile.TemporaryDirectory() as d:result=stock_project.build(self.working,Path(d)/'check')
        elif self.data['kind']=='addon':
            result=validate_vehicle(VehicleProject.load(self.working/'vehicle-project.json'))
            if result['status']=='FAIL':raise ValueError(str(result['diagnostics']))
            result={k:v for k,v in result.items() if k!='compiled'}
        else:result={'status':'PASS_RESOURCES_ONLY','runtime_installable':False}
        return {'status':'PASS','kind':self.data['kind'],'edits':len(self.data['edits']),'sdk':result,'runtime_qualified':False}

    def build(self,output,*,sdk_root,log=lambda message:None):
        self.validate();output=Path(output).resolve()
        if output.exists():raise ValueError('Choose a fresh build directory')
        if output.is_relative_to(self.root) and not output.is_relative_to(self.root/'builds'):raise ValueError('Build output must not overwrite project state')
        settings=self.data['build_settings'];output.mkdir(parents=True)
        if self.data['kind']=='family':
            shutil.copytree(self.assets,output/'assets');report={'status':'PASS_RESOURCES_ONLY','runtime_installable':False}
        else:
            import sys
            tools=str(Path(sdk_root)/'tools')
            if tools not in sys.path:sys.path.insert(0,tools)
            from build_sdk_roster import build as roster_build
            roster_path=Path(settings['roster_candidate'])/'roster-config.json'
            if not roster_path.is_file():raise ValueError('Choose an existing qualified roster candidate in Build settings')
            roster=json.loads(roster_path.read_text())
            snapshot=output/'project-snapshot'
            shutil.copytree(self.working,snapshot)
            # A later GUI Restore must not change this build's source recipe.
            if self.data['kind']=='addon':
                spec=json.loads((snapshot/'vehicle-project.json').read_text())
                textures=snapshot/'workshop-textures';textures.mkdir()
                author=VehicleProject.load(self.working/'vehicle-project.json')
                for name,edit in spec.get('texture_edits',{}).items():
                    image=author.resolve(edit['png']);destination=textures/(name+'.png');shutil.copyfile(image,destination);edit['png']=str(destination)
                write_json(snapshot/'vehicle-project.json',spec)
            write_json(output/'workshop-edit-ledger.json',{'project':str(self.root),'inputs':self.data['inputs'],'edits':self.data['edits'],'surfaces':self.data.get('surfaces',{}),'settings':settings})
            if self.data['kind']=='stock':
                report=stock_project.build(snapshot,output/'stock-overrides')
                roster.setdefault('stock_resource_projects',[]).append(str(snapshot))
            else:
                from master_rallye.addon_sdk.project import build_project
                capabilities=Path(sdk_root)/'research/vehicles/sdk/capabilities/retail-2001.json'
                log('Compiling author project using existing SDK...')
                report=build_project(snapshot,capabilities,output/'author-build',retail_data_sma=Path(settings['retail_sma']),retail_data_root=Path(settings['retail_root']))
                matches=[]
                for entry in roster['projects']:
                    identity=json.loads((Path(entry['project'])/'addon.json').read_text())['addon_id']
                    if identity==self.data['identity']:matches.append(entry)
                if len(matches)!=1:raise ValueError('This roster does not contain exactly one replaceable author entry; frozen base addons need a qualified author entry')
                matches[0].update(project=str(snapshot),build=str(output/'author-build'))
            log('Building isolated runtime candidate and launcher preflights...')
            write_json(output/'roster.json',roster);report=roster_build(roster,output/'candidate')
        self.data['last_build']=str(output);self.save();return report
