"""Thin authoring service over the established SDK, DX/DXT and stock APIs.

Inputs are never edited. Every Workshop project owns a private working copy,
an immutable rendered baseline, typed edit recipes and fresh build directories.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
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

from .audio import AudioAuthoring
from .vehicle_authoring import VehicleAuthoring
from .audio_import import AudioImportAuthoring
from .gt_audio import GTAudioAuthoring
from .shadow import ShadowAuthoring

class WorkshopProject(AudioAuthoring,VehicleAuthoring,AudioImportAuthoring,GTAudioAuthoring,ShadowAuthoring):
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
              'limitations':'D3D9 diagnostic preview; paint needs explicit hash-qualified masks; shared image replacement affects every declared owner; no automatic semantic classification or skeletal authoring'}
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
        from master_rallye.addon_sdk.heritage_source import verify_author
        verify_author(self.working)
        for path,expected in self.data.get('author_sources',{}).items():
            if sha(Path(path).read_bytes())!=expected:raise ValueError('Original author input changed: '+path)
        for name,expected in self.data['inputs'].items():
            if sha(_owned(self.baseline,name).read_bytes())!=expected:raise ValueError('Workshop baseline changed: '+name)
        for region in self.data.get('paint_regions',{}).values():
            digest=region['mask_sha256']
            if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest) or region['texture']not in self.data['inputs'] or region['source_sha256']!=self.data['inputs'][region['texture']]:raise ValueError('Invalid paint region identity')
            if sha((self.root/'paint-masks'/(digest+'.png')).read_bytes())!=digest:raise ValueError('Paint mask changed')
        if self.data.get('mechanical_input_sha256') and sha((self.root/'original-mechanical.json').read_bytes())!=self.data['mechanical_input_sha256']:raise ValueError('Mechanical baseline changed')
        if self.data.get('shadow_input_sha256') and sha((self.root/'original-shadow.json').read_bytes())!=self.data['shadow_input_sha256']:raise ValueError('Shadow baseline changed')

    def _record(self):
        self.data['history'].append(self._state())
        self.data['history']=self.data['history'][-30:]
        self.data['redo']=[]

    def _state(self):return json.loads(json.dumps({'__workshop_state__':1,'textures':self.data['edits'],'surfaces':self.data.get('surfaces',{}),
        **{k:self.data.get(k,{}) for k in ('appearance_profiles','crew','paint_regions','color_presets','audio','vehicle_authoring','shadow')},'appearance':self.data.get('appearance','Source Fidelity')}))

    def _load_state(self,state):
        previous_audio=self.data.get('audio')
        previous_vehicle=self.data.get('vehicle_authoring')
        if state.get('__workshop_state__')==1:
            self.data['edits']=state['textures'];self.data['surfaces']=state['surfaces']
            for key in ('appearance_profiles','crew','paint_regions','color_presets','audio','vehicle_authoring','shadow'):self.data[key]=state.get(key,{})
            self.data['appearance']=state.get('appearance','Source Fidelity')
        else:self.data['edits']=state;self.data['surfaces']={}
        if previous_audio and not self.data.get('audio'):
            baseline=self.root/'audio-baseline.json'
            if sha(baseline.read_bytes())!=previous_audio['baseline_sha256']:raise ValueError('Audio baseline changed')
            profile=json.loads(baseline.read_text())
            self.data['audio']={**previous_audio,'profile':profile,'enabled':{k:True for k in ('engine','transmission_whine','turbo_spool','bov_release') if k in profile}}
        if previous_vehicle and not self.data.get('vehicle_authoring'):self.data['vehicle_authoring']=self.vehicle_defaults()

    def switch_appearance(self,name):
        if name not in ('Source Fidelity','Classic MR Style','Custom'):raise ValueError('Unknown appearance profile')
        self._record();profiles=self.data.setdefault('appearance_profiles',{})
        profiles[self.data.get('appearance','Source Fidelity')]={'textures':self.data['edits'],'surfaces':self.data.get('surfaces',{})}
        target=json.loads(json.dumps(profiles.get(name,{'textures':{},'surfaces':{}})))
        self.data['edits']=target['textures'];self.data['surfaces']=target['surfaces'];self.data['appearance']=name
        self.materialize();self.save()

    def register_paint_region(self,name,texture,mask_path,evidence):
        from master_rallye.paint_authoring import masked_paint
        if not isinstance(name,str) or not name.strip() or len(name)>80:raise ValueError('Choose a short region name')
        raw=_owned(self.baseline,texture).read_bytes();mask=Path(mask_path).read_bytes()
        _,audit=masked_paint(raw,mask,[255,255,255],source_sha256=self.data['inputs'][texture],evidence=evidence)
        usage=self.texture_usage(texture)
        if usage and not audit['nonzero_alpha_selected_texels'] and all(any(parse_dx_bytes((self.assets/use['model']).read_bytes()).physical_draws[use['draw']].flags_0x20[:2]) for use in usage):raise ValueError('Mask selects only invisible alpha texels in a blend/cutout overlay. Qualify the underlying opaque paint pass instead.')
        existing=self.data.get('paint_regions',{}).get(name)
        if existing and (existing['texture']!=texture or existing['mask_sha256']!=sha(mask)):raise ValueError('Use a new region name for a different mask or texture; existing paint recipes stay pinned')
        folder=self.root/'paint-masks';folder.mkdir(exist_ok=True);(folder/(sha(mask)+'.png')).write_bytes(mask)
        self._record();self.data.setdefault('paint_regions',{})[name]={'texture':texture,'source_sha256':sha(raw),'mask_sha256':sha(mask),'evidence':evidence,'audit':audit}
        self.save();return audit

    def paint_region(self,name,color):
        from master_rallye.paint_authoring import masked_paint
        region=self.data.get('paint_regions',{})[name];texture=region['texture']
        mask=(self.root/'paint-masks'/(region['mask_sha256']+'.png')).read_bytes()
        if sha(mask)!=region['mask_sha256']:raise ValueError('Paint mask changed')
        previous=self.data['edits'].get(texture)
        if previous and previous['operation']!='qualified-masked-paint':raise ValueError('Restore this texture before painting; another texture edit owns its pixels')
        layers=dict(previous.get('paint_layers',{})) if previous else {};layers[name]=color
        raw=_owned(self.baseline,texture).read_bytes();audits=[]
        for key,value in layers.items():
            r=self.data['paint_regions'][key];image=(self.root/'paint-masks'/(r['mask_sha256']+'.png')).read_bytes()
            if sha(image)!=r['mask_sha256']:raise ValueError('Paint mask changed')
            raw,audit=masked_paint(raw,image,value,source_sha256=sha(raw),evidence=r['evidence']);audits.append(audit)
        self._record();self._apply(texture,raw[20:],{'operation':'qualified-masked-paint','paint_layers':layers,'audits':audits,'alpha':'preserved'})
        return audit

    def save_color_preset(self,name,color):
        if not isinstance(name,str) or not name.strip() or len(name)>80:raise ValueError('Choose a short preset name')
        if len(color)!=3 or any(type(v)is not int or not 0<=v<=255 for v in color):raise ValueError('Invalid color')
        self._record();self.data.setdefault('color_presets',{})[name]=list(color);self.save()

    @staticmethod
    def stock_materials(folder):
        """Local stock reference catalogue; parsing is not vehicle registration."""
        from master_rallye.assets import AssetResolver
        folder=plain_tree(folder);result=[]
        for f in sorted(folder.glob('*.dx')):
            m=parse_dx_bytes(f.read_bytes())
            if not m.diagnostics.validated:raise ValueError('Invalid reference DX')
            for d in m.physical_draws:
                slots=[]
                for slot in d.texture_slots:
                    p=AssetResolver(folder).resolve_texture(slot.value)
                    if p:
                        raw=p.read_bytes();t=parse_dxt_bytes(raw)
                        slots.append({'slot':slot.slot,'stem':slot.value,'path':str(p),'sha256':sha(raw),'width':t.width,'height':t.height,'alpha_range':[min(t.bgra[3::4]),max(t.bgra[3::4])]})
                result.append({'model':f.name,'source_sha256':sha(f.read_bytes()),'draw':d.draw_index,'textures':slots,'semantics':MaterialSemantics.from_draw(d).to_dict(),
                               'uv_warning':'No automatic UV adaptation. Compare layout, repeats, seams and alpha before assignment.'})
        return result

    def use_stock_texture(self,model,draw_id,slot,reference,*,allow_shared=False,resample_environment=False):
        """Replace a private owned slot image, then use Binding v2 to validate it.

        Shared atlases require explicit acknowledgement. New retail resources
        are never added to the retail tree or silently substituted by name.
        """
        from master_rallye.texture_binding import binding_compatibility
        from master_rallye.assets import AssetResolver
        if type(slot)is not int or slot not in (0,1):raise ValueError('Only qualified existing slots 0/1')
        self.verify_inputs();m=parse_dx_bytes(_owned(self.assets,model).read_bytes())
        if type(draw_id)is not int or not 0<=draw_id<len(m.physical_draws):raise ValueError('Unknown draw')
        stem=m.physical_draws[draw_id].texture_slots[slot].value
        target=AssetResolver(self.assets).resolve_texture(stem)
        if target is None or target.name not in self.data['inputs']:raise ValueError('Target slot has no owned image')
        source=plain_tree(reference['path']);raw=source.read_bytes()
        if sha(raw)!=reference['sha256']:raise ValueError('Stock reference changed')
        a=parse_dxt_bytes(raw);b=self.texture(target.name)
        adaptation='none; source and target dimensions match'
        if (a.width,a.height)!=(b.width,b.height):
            if slot!=1 or not resample_environment:raise ValueError('Diffuse transfer requires matching dimensions; opaque environment resizing requires explicit opt-in')
            from PIL import Image
            import io
            image=Image.frombytes('RGBA',(a.width,a.height),a.bgra,'raw','BGRA')
            image=image.convert('RGBa').resize((b.width,b.height),Image.Resampling.LANCZOS).convert('RGBA')
            pixels=image.tobytes('raw','BGRA')
            raw=b.header[:8]+struct.pack('<I',zlib.crc32(pixels)&0xffffffff)+b.header[12:]+pixels
            adaptation=f'Explicit premultiplied-alpha environment-only LANCZOS resize {a.width}x{a.height} to {b.width}x{b.height}; native UVs unchanged'
            a=parse_dxt_bytes(raw)
        usage=self.texture_usage(target.name)
        if len(usage)>1 and not allow_shared:raise ValueError('Shared target texture affects '+str(len(usage))+' slots; explicit acknowledgement required')
        def provider(value):return raw if value==stem else self.binding_texture(value)
        for use in usage:
            model_bytes=_owned(self.assets,use['model']).read_bytes();parsed=parse_dx_bytes(model_bytes)
            binding_compatibility(parsed,use['draw'],use['slot'],stem,provider)
        self._record();self._apply(target.name,a.bgra,{'operation':'local-stock-reference','source_sha256':reference['sha256'],'source_path':str(source),'source_slot':reference['slot'],'adaptation':adaptation,'scope':'all declared uses of this owned texture','uv':'unchanged; visual compatibility requires owner inspection'})

    def register_crew(self,model,definition):
        return self.register_crew_models({model:definition})

    def register_crew_models(self,definitions):
        from master_rallye.crew_authoring import apply_crew_fit
        if not definitions:raise ValueError('Empty crew preset')
        for model,definition in definitions.items():
            if model not in ('car.dx','complete.dx'):raise ValueError('Crew requires race or frontend body')
            raw=_owned(self.baseline,model).read_bytes()
            if definition['model_sha256']!=sha(raw):raise ValueError('Crew preset belongs to another model revision')
            apply_crew_fit(raw,definition,{},source_sha256=sha(raw))
        self._record()
        for model,definition in definitions.items():self.data.setdefault('crew',{})[model]={'definition':json.loads(json.dumps(definition)),'placements':{}}
        self.materialize();self.save()

    def fit_crew(self,model,person,placement):
        from master_rallye.crew_authoring import apply_crew_fit
        entry=self.data.get('crew',{}).get(model)
        if not entry:raise ValueError('Import a source-qualified crew preset for this model first')
        placements={**entry['placements'],person:placement};raw=_owned(self.baseline,model).read_bytes()
        _,report=apply_crew_fit(raw,entry['definition'],placements,source_sha256=sha(raw))
        self._record();entry['placements']=placements;self.materialize();self.save();return report

    def edit_surface(self,model,draw_id,*,rgb=None,disable_reflection=None,reflection_strength=None):
        from master_rallye.surface_authoring import apply_surface_edits
        if model not in ('car.dx','complete.dx','wheel.dx'):raise ValueError('Unsupported model')
        recipe=dict(self.data.get('surfaces',{}).get(model,{}).get(str(draw_id),{'draw_id':draw_id}))
        if rgb is not None:recipe['rgb']=rgb
        if disable_reflection is not None:recipe['disable_reflection']=disable_reflection
        if reflection_strength is not None:recipe['reflection_strength']=reflection_strength
        raw=_owned(self.baseline,model).read_bytes();apply_surface_edits(raw,[recipe],source_sha256=sha(raw),texture_provider=self.binding_texture)
        self._record();self.data.setdefault('surfaces',{}).setdefault(model,{})[str(draw_id)]=recipe;self.materialize();self.save()

    def restore_surface(self,model,draw_id):
        self._record();self.data.setdefault('surfaces',{}).get(model,{}).pop(str(draw_id),None);self.materialize();self.save()

    def binding_texture(self,stem):
        from master_rallye.assets import AssetResolver
        path=AssetResolver(self.assets).resolve_texture(stem)
        if path is None or path.name not in self.data['inputs']:raise ValueError('Texture is not owned by this project: '+stem)
        raw=path.read_bytes();expected=self.data['edits'].get(path.name,{}).get('output_sha256',self.data['inputs'][path.name])
        if sha(raw)!=expected:raise ValueError('Owned texture changed outside project: '+path.name)
        return raw

    def assign_existing_texture(self,model,draw_id,slot,target):
        from master_rallye.surface_authoring import apply_surface_edits
        if model not in ('car.dx','complete.dx','wheel.dx'):raise ValueError('Unsupported model')
        if type(slot) is not int or slot not in (0,1):raise ValueError('Only existing diffuse/environment slots 0/1 are qualified')
        self.verify_inputs()
        recipe=dict(self.data.get('surfaces',{}).get(model,{}).get(str(draw_id),{'draw_id':draw_id}))
        recipe['bindings']={**recipe.get('bindings',{}),str(slot):target}
        raw=_owned(self.baseline,model).read_bytes()
        apply_surface_edits(raw,[recipe],source_sha256=sha(raw),texture_provider=self.binding_texture)
        self._record();self.data.setdefault('surfaces',{}).setdefault(model,{})[str(draw_id)]=recipe
        self.materialize();self.save()

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
            output=apply_surface_edits(raw,list(edits.values()),source_sha256=self.data['inputs'][model],texture_provider=self.binding_texture).data
            write_resource(_owned(self.assets,model),output)
        from master_rallye.crew_authoring import apply_crew_fit
        crew_layers={}
        for model,entry in self.data.get('crew',{}).items():
            if model not in ('car.dx','complete.dx') or entry['definition']['model_sha256']!=self.data['inputs'][model]:raise ValueError('Crew definition baseline changed')
            raw=_owned(self.assets,model).read_bytes()
            layer={'source_sha256':sha(raw),**entry};output,_=apply_crew_fit(raw,entry['definition'],entry['placements'],source_sha256=sha(raw))
            crew_layers[model]=layer;write_resource(_owned(self.assets,model),output)
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
            for model,layer in crew_layers.items():
                entry=spec.setdefault('resources',{}).setdefault(model,{'source_sha256':sha((original.source_vehicle_dir/model).read_bytes())})
                if 'crew_layer' in entry:raise ValueError('Author already owns a crew layer; merge in the source project first')
                entry['crew_layer']=layer
            mechanical=self.working/'mechanical-attachments.json'
            if mechanical.exists():
                immutable=self.root/'original-mechanical.json'
                if not immutable.exists():
                    initial=mechanical.read_bytes();definition=json.loads(initial)['definition']
                    if definition['source_sha256']!=self.data['inputs']['car.dx']:raise ValueError('Mechanical baseline does not match imported car')
                    immutable.write_bytes(initial);self.data['mechanical_input_sha256']=sha(initial);self.save()
                from master_rallye.addon_sdk.visual_fitment import rebase_unchanged_mechanics
                profile=json.loads(immutable.read_text())
                profile['definition']=rebase_unchanged_mechanics((self.baseline/'car.dx').read_bytes(),(self.assets/'car.dx').read_bytes(),profile['definition'])
                write_json(mechanical,profile)
            shadow=self.working/'shadow-profile.json'
            if shadow.exists():
                immutable=self.root/'original-shadow.json'
                if not immutable.exists():
                    initial=shadow.read_bytes();immutable.write_bytes(initial);self.data['shadow_input_sha256']=sha(initial);self.save()
                before=(self.baseline/'car.dx').read_bytes();after=(self.assets/'car.dx').read_bytes()
                if mechanical.exists():
                    from master_rallye.addon_sdk.mechanical_attachments import build_mechanical_resources
                    wheel=(self.baseline/'wheel.dx').read_bytes();template=(original.source_vehicle_dir/'car.dx').read_bytes()
                    old=json.loads((self.root/'original-mechanical.json').read_text())
                    before=build_mechanical_resources(before,wheel,old['definition'],stock_brake_template=template)[0]['car.dx']
                    after=build_mechanical_resources(after,wheel,profile['definition'],stock_brake_template=template)[0]['car.dx']
                from master_rallye.addon_sdk.vehicle_shadow import rebase_unchanged_footprint
                write_json(shadow,rebase_unchanged_footprint(before,after,json.loads(immutable.read_text())))
            write_json(self.working/'vehicle-project.json',spec)
        self.audio_materialize()
        self.vehicle_materialize()
        self.shadow_materialize()

    def restore(self,name=None):
        self._record()
        if name is None:
            self.data['edits']={};self.data['surfaces']={};self.data['shadow']={}
            for entry in self.data.get('crew',{}).values():entry['placements']={}
            if self.data.get('audio'):
                state=self.data['audio'];baseline=self.root/'audio-baseline.json'
                if sha(baseline.read_bytes())!=state['baseline_sha256']:raise ValueError('Audio baseline changed')
                state['profile']=json.loads(baseline.read_text());state['enabled']={k:True for k in ('engine','transmission_whine','turbo_spool','bov_release') if k in state['profile']}
                state.pop('layer_imports',None)
            if self.data.get('vehicle_authoring'):self.data['vehicle_authoring']=self.vehicle_defaults()
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
        self.vehicle_validate()
        if self.data.get('shadow_baseline') is not None or self.data.get('shadow'):self.shadow_calculate()
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
        from .classic import require_classic_approval
        require_classic_approval(self)
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
            write_json(output/'workshop-edit-ledger.json',{'project':str(self.root),'inputs':self.data['inputs'],'edits':self.data['edits'],'surfaces':self.data.get('surfaces',{}),'crew':self.data.get('crew',{}),'audio':self.data.get('audio',{}),'vehicle_authoring':self.data.get('vehicle_authoring',{}),'appearance':self.data.get('appearance','Source Fidelity'),'settings':settings})
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
            self.camera_build_roster(roster,snapshot,output/'author-build')
            log('Building isolated runtime candidate and launcher preflights...')
            write_json(output/'roster.json',roster);report=roster_build(roster,output/'candidate')
        self.data['last_build']=str(output);self.save();return report
