"""Portable texture-only livery sessions over the established Workshop API.

No runtime registry, DX geometry, material binding or vehicle ID is authored.
The package carries its pinned baseline so Original also works after relocation.
"""
from pathlib import Path, PurePosixPath
import copy
import json
import shutil
import uuid

from master_rallye.assets import AssetResolver
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes, encode_png, encode_dxt_pixels, PNG_ROWS_FLIP_VERTICAL
from master_rallye.texture_authoring import decode_rgba_png
from master_rallye.topology_writer import source_geometry
from .service import WorkshopProject, sha, write_json, plain_tree


def relative_file(root, name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('Manifest paths must be relative POSIX paths')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Unsafe manifest path')
    result = Path(root).joinpath(*path.parts)
    plain_tree(result)
    return result


class LiverySession:
    def __init__(self, project, metadata=None):
        self.project = project
        self.metadata = metadata or self.stock_metadata()
        self.saved = None
        self.last_files = {}
        self.warnings = []
        self._index = None
        from .livery_artwork import default_presets
        self.artwork={};self.art_presets=default_presets()
        self.artwork_archive=[]
        self.model_identity={'variant':project.data.get('model_variant','PC'),'models':{n:h for n,h in project.data['inputs'].items() if n.endswith('.dx')},'basis':'Pinned native project model resources; ancestry is not inferred from a display label'}

    @classmethod
    def create(cls, source, workspace):
        source = Path(source)
        if (source/'workshop-project.json').is_file():
            # Snapshot the currently materialized native resources; leave the
            # existing authoring project and its geometry/material journal alone.
            original = WorkshopProject(source)
            original.verify_inputs()
            source = original.assets
            project = WorkshopProject.create(source, workspace, car_id=original.data['car_id'])
            project.data.update(identity=original.data['identity'], family=original.data['family'])
            # Retain the current geometry/material state as the texture-session
            # model, while preserving the established original texture baseline.
            # Do not mutate or replay the legacy project's unrelated editors.
            changed={}
            for name in project.data['inputs']:
                baseline=original.baseline/name
                if name.endswith('.dxt') and baseline.is_file():
                    current=(project.assets/name).read_bytes();raw=baseline.read_bytes()
                    (project.baseline/name).write_bytes(raw);project.data['inputs'][name]=sha(raw)
                    if current!=raw:changed[name]=current
            project.save()
            for name,raw in changed.items():project._apply(name,parse_dxt_bytes(raw).bgra,{'operation':'existing-workshop-texture','alpha':'preserved-existing'})
            project.materialize()
        else:
            project = WorkshopProject.create(source, workspace)
        return cls(project)

    def stock_metadata(self):
        p = self.project.data
        return {'livery_id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'mr-stock:'+str(p['identity'])+':'+sha(json.dumps(p['inputs'], sort_keys=True).encode()))),
                'name': 'Stock', 'number': '', 'crew': '', 'source': '', 'origin': 'Original',
                'vehicle_family': p['family'] or p['identity'], 'physical_id': p['car_id'], 'model_variant': p.get('model_variant','PC')}

    def new_livery(self, name):
        self.validate_variant()
        if not name.strip(): raise ValueError('Livery name is required')
        self.project.restore()
        variant=self.metadata['model_variant']
        self.metadata = {**self.stock_metadata(), 'livery_id': str(uuid.uuid4()), 'name': name.strip(), 'origin': 'Custom','model_variant':variant}
        self.artwork={role:entry for role,entry in self.artwork.items() if entry.get('historical_original')}
        for entry in self.artwork.values():entry['livery_id']=self.metadata['livery_id']
        self.saved = None

    def validate_variant(self):
        if self.metadata['model_variant']!=self.model_identity['variant']:
            raise ValueError('Model variant is fixed by the loaded source model; load a qualified variant instead of changing its label')

    def duplicate_current(self,name):
        self.validate_variant()
        if not name.strip():raise ValueError('Livery name is required')
        parent=self.metadata['livery_id']
        self.metadata={**copy.deepcopy(self.metadata),'livery_id':str(uuid.uuid4()),'parent_livery_id':parent,'name':name.strip()}
        self.artwork=copy.deepcopy(self.artwork)
        for entry in self.artwork.values():
            entry['livery_id']=self.metadata['livery_id']
            if 'input_signature' in entry:entry['input_signature']=self.signature()
        self.saved=None

    def accept_artwork(self,entry):
        if entry.get('input_signature')!=self.signature():raise ValueError('Candidate artwork is stale; regenerate first')
        if entry.get('preset')!=self.art_presets[entry['role']]:raise ValueError('Candidate preset changed; regenerate first')
        role=entry['role'];previous=self.artwork.get(role)
        if previous and (previous['sha256']!=entry['sha256'] or previous.get('historical_original') or previous.get('origin')!=entry.get('origin')):self.artwork_archive.append(copy.deepcopy(previous))
        self.artwork[role]=copy.deepcopy(entry)

    def signature(self):
        return sha(json.dumps({'metadata': self.metadata, 'edits': self.project.data['edits']}, sort_keys=True).encode())

    @property
    def dirty(self): return self.full_signature() != self.saved

    def full_signature(self):
        return sha(json.dumps({'textures':self.signature(),'artwork':self.artwork,'art_presets':self.art_presets,'artwork_archive':self.artwork_archive},sort_keys=True).encode())

    def index(self):
        if self._index is not None: return self._index
        assets = self.project.assets
        result = {p.name: [] for p in sorted(assets.glob('*.dxt'))}
        resolver = AssetResolver(assets)
        for path in sorted(assets.glob('*.dx')):
            model = parse_dx_bytes(path.read_bytes())
            geometry = source_geometry(model)
            for draw in model.physical_draws:
                for slot in draw.texture_slots:
                    texture = resolver.resolve_texture(slot.value)
                    if texture is None: continue
                    g = geometry[draw.draw_index]
                    # TEX0 is the actual base UV stream. Higher stages may be
                    # generated environment coordinates: never invent a UV map.
                    uv = [[list(g.vertices[i].uvs[0]) for i in tri] for tri in g.triangles] if slot.slot == 0 and model.uv_sets else []
                    uv_ids=[[g.vertices[i].source_vertex_id for i in tri] for tri in g.triangles] if uv else []
                    result.setdefault(texture.name, []).append({'model': path.name, 'draw': draw.draw_index,
                        'group': draw.group_label, 'stage': slot.slot, 'binding': slot.value, 'uv_triangles': uv,'uv_vertex_ids':uv_ids,
                        'uv_status': 'base UV0' if uv else 'Generated/secondary stage: UV layout not qualified'})
        self._index = result
        return result

    def export_png(self, name, path, original=False):
        self.check_name(name)
        raw = (self.project.baseline/name).read_bytes() if original else (self.project.assets/name).read_bytes()
        path = Path(path)
        self.output_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        from .texture_images import export_image
        self.warnings=export_image(encode_png(parse_dxt_bytes(raw)),path)
        self.last_files[name] = path
        return path

    def output_path(self, path):
        path = plain_tree(path).resolve()
        for root in (self.project.baseline, self.project.assets, Path(self.project.data['source'])):
            if path.is_relative_to(root.resolve()): raise ValueError('Export must be outside original and managed resources')

    def check_name(self, name):
        if name not in self.index() or Path(name).name != name: raise ValueError('Unknown texture target')

    def import_png(self, name, path, preserve_alpha=True):
        self.check_name(name)
        if self.png_pixels(name,path,preserve_alpha) == self.project.texture(name).bgra:
            self.last_files[name]=Path(path)
            return
        from .texture_images import load_image,rgba_png
        w,h,rgba,self.warnings=load_image(path)
        normalized=self.project.root/'image-imports';normalized.mkdir(exist_ok=True)
        raw=rgba_png(w,h,rgba);pin=normalized/(sha(raw)+'.png');pin.write_bytes(raw)
        self.project.replace_png(name, pin, preserve_original_alpha=preserve_alpha)
        self.last_files[name] = Path(path)

    def png_pixels(self,name,path,preserve_alpha):
        from .texture_images import load_image
        w,h,rgba,self.warnings=load_image(path)
        t=parse_dxt_bytes((self.project.baseline/name).read_bytes())
        pixels=bytearray(encode_dxt_pixels(t,rgba,w,h,row_policy=PNG_ROWS_FLIP_VERTICAL)[20:])
        if preserve_alpha:pixels[3::4]=t.bgra[3::4]
        return bytes(pixels)

    def export_all(self, folder):
        folder = Path(folder)
        self.output_path(folder)
        if folder.exists() and any(folder.iterdir()): raise ValueError('Choose a new or empty export folder')
        folder.mkdir(parents=True, exist_ok=True)
        entries = []
        for name in self.index():
            path = self.export_png(name, folder/(name+'.png'))
            texture = self.project.texture(name)
            entries.append({'resource': name, 'png': path.name, 'width': texture.width, 'height': texture.height,
                            'baseline_sha256': self.project.data['inputs'][name],
                            'usages': [{k:v for k,v in u.items() if k not in ('uv_triangles','uv_vertex_ids')} for u in self.index()[name]]})
        manifest = {'schema': 'mr-texture-roundtrip/1', 'vehicle_family': self.metadata['vehicle_family'],
                    'model_variant': self.metadata['model_variant'], 'entries': entries}
        write_json(folder/'textures.json', manifest)
        return folder/'textures.json'

    def import_manifest(self, path, preserve_alpha=True):
        path = Path(path)
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc.get('schema') != 'mr-texture-roundtrip/1' or doc.get('vehicle_family') != self.metadata['vehicle_family'] or doc.get('model_variant') != self.metadata['model_variant']:
            raise ValueError('Manifest vehicle family/model variant mismatch')
        prepared = [];seen=set()
        for entry in doc['entries']:
            name = entry['resource']; self.check_name(name)
            if name in seen: raise ValueError('Duplicate texture target')
            seen.add(name)
            if entry['baseline_sha256'] != self.project.data['inputs'][name]: raise ValueError('Manifest baseline mismatch')
            png = relative_file(path.parent, entry['png'])
            # Skip unchanged exports, avoiding meaningless edits to glass/glow.
            if self.png_pixels(name,png,preserve_alpha) != self.project.texture(name).bgra: prepared.append((name,png))
        before = copy.deepcopy(self.project.data)
        try:
            for name,png in prepared: self.import_png(name,png,preserve_alpha)
            if prepared:
                self.project.data['history'] = (before['history'] + [WorkshopProjectState(before)])[-30:]
                self.project.data['redo'] = []; self.project.save()
        except Exception:
            self.project.data = before; self.project.materialize(); self.project.save(); raise
        return [name for name,_ in prepared]

    @staticmethod
    def refresh_artwork(entry, raw):
        """Accept editable pixels without mislabelling them historical originals."""
        from master_rallye.addon_sdk.ui_assets import BANKS
        w,h,_=decode_rgba_png(raw)
        if (w,h)!=BANKS[entry['role']][3]:raise ValueError('Artwork dimensions mismatch')
        if sha(raw)==entry['sha256']:return entry
        entry=copy.deepcopy(entry)
        entry.update(previous_sha256=entry['sha256'],sha256=sha(raw),origin='Custom',historical_original=False,externally_edited=True)
        # External art is an explicit authored image, not a stale automatic capture.
        entry.pop('input_signature',None);entry.pop('preset',None)
        return entry

    def save_package(self, folder):
        self.validate_variant()
        folder = Path(folder); self.output_path(folder)
        if folder.exists(): raise ValueError('Save to a fresh package folder; original packages stay immutable')
        if self.metadata['origin'] not in ('Original','Historical','Custom','Reconstructed'): raise ValueError('Unknown provenance type')
        uuid.UUID(self.metadata['livery_id'])
        for entry in self.artwork.values():
            if 'input_signature' in entry and entry['input_signature']!=self.signature():raise ValueError('Generated artwork is stale after edits; regenerate before saving')
            if 'preset' in entry and entry['preset']!=self.art_presets[entry['role']]:raise ValueError('Artwork preset changed; regenerate before saving')
        folder.mkdir(parents=True)
        try:
            resources = []
            for name,h in self.project.data['inputs'].items():
                target = folder/'baseline'/name; target.parent.mkdir(exist_ok=True)
                shutil.copyfile(self.project.baseline/name,target)
                resources.append({'path':'baseline/'+name, 'sha256':h})
            textures = []
            for name in self.index():
                t = self.project.texture(name); target = folder/'textures'/name;target.parent.mkdir(exist_ok=True)
                shutil.copyfile(self.project.assets/name,target)
                textures.append({'resource':name,'path':'textures/'+name,'sha256':sha(target.read_bytes()),
                    'baseline_sha256':self.project.data['inputs'][name], 'width':t.width,'height':t.height,
                    'format':'FEED/BGRA32','roles_stages':[{k:v for k,v in u.items() if k not in ('uv_triangles','uv_vertex_ids')} for u in self.index()[name]]})
            artwork={};archive=[]
            items=[(role,entry,False) for role,entry in self.artwork.items()]+[(f'archived-{i}',entry,True) for i,entry in enumerate(self.artwork_archive)]
            for role,entry,archived in items:
                target=folder/'artwork'/(role+'.png');target.parent.mkdir(exist_ok=True)
                raw=Path(entry['png']).read_bytes()
                entry=self.refresh_artwork(entry,raw)
                target.write_bytes(raw);artwork[role]={k:v for k,v in entry.items() if k not in ('png','source_png')}
                artwork[role]['png']=target.relative_to(folder).as_posix()
                if entry.get('source_png'):
                    high=folder/'artwork'/(role+'-source.png');high.write_bytes(Path(entry['source_png']).read_bytes());artwork[role]['source_png']=high.relative_to(folder).as_posix()
                if archived:archive.append(artwork.pop(role))
            if artwork:
                write_json(folder/'ui-assets.json',{'version':1,'icons':{role:{'png':entry['png'],'sha256':entry['sha256'],'presentation':'source-pixels-v1'} for role,entry in artwork.items()}})
            doc = {'schema':'mr-livery/1','metadata':self.metadata,'model_identity':self.model_identity,'baseline':resources,'textures':textures,'artwork':artwork,'artwork_archive':archive,'art_presets':self.art_presets,
                'runtime_selection':'catalog-only; MODEL and LIVERY are independent', 'geometry':'unchanged baseline'}
            write_json(folder/'livery.json',doc)
        except Exception:
            # Retain diagnostics but never leave a valid-looking partial manifest.
            raise
        self.saved = self.full_signature()
        return folder/'livery.json'

    @classmethod
    def open_package(cls, path, workspace):
        path = Path(path);doc = json.loads(path.read_text(encoding='utf-8'))
        if doc.get('schema') != 'mr-livery/1': raise ValueError('Unsupported livery schema')
        uuid.UUID(doc['metadata']['livery_id'])
        for entry in doc['baseline']:
            if sha(relative_file(path.parent,entry['path']).read_bytes()) != entry['sha256']: raise ValueError('Package hash mismatch')
        session = cls.create(path.parent/'baseline',workspace)
        session.metadata = doc['metadata']
        if 'model_identity' in doc and doc['model_identity']!=session.model_identity:raise ValueError('Livery model identity differs from pinned source resources')
        if 'model_identity' in doc and session.metadata['model_variant']!=session.model_identity['variant']:raise ValueError('Livery variant label contradicts its pinned model identity')
        if session.metadata['model_variant']!=session.model_identity['variant']:
            session.warnings.append('Unverified legacy variant label replaced by the loaded native model identity')
            session.metadata['model_variant']=session.model_identity['variant']
        session.project.data.update(identity=doc['metadata']['vehicle_family'],family=doc['metadata']['vehicle_family'],car_id=doc['metadata']['physical_id'])
        declared={entry['path']:entry['sha256'] for entry in doc['baseline']}
        if len(declared)!=len(doc['baseline']) or declared!={'baseline/'+n:h for n,h in session.project.data['inputs'].items()}:raise ValueError('Incomplete or duplicate package baseline')
        if len({e['resource'] for e in doc['textures']})!=len(doc['textures']) or {e['resource'] for e in doc['textures']}!=set(session.index()):raise ValueError('Incomplete or duplicate texture catalogue')
        for entry in doc['textures']:
            name=entry['resource'];session.check_name(name)
            if entry['baseline_sha256']!=session.project.data['inputs'][name]:raise ValueError('Livery baseline mismatch')
            raw=relative_file(path.parent,entry['path']).read_bytes();t=parse_dxt_bytes(raw);base=session.project.texture(name)
            if (t.width,t.height)!=(base.width,base.height):raise ValueError('Livery dimensions mismatch')
            if t.header[:8]+t.header[12:]!=base.header[:8]+base.header[12:]:raise ValueError('Livery altered immutable FEED metadata')
            if sha(raw)!=entry['sha256']:session.warnings.append('Externally edited texture accepted after FEED metadata/dimension validation: '+name)
            if raw!=(session.project.baseline/name).read_bytes():
                session.project._apply(name,t.bgra,{'operation':'livery-reopen','alpha':'package'})
        session.project.data['history']=[];session.project.data['redo']=[];session.project.save()
        items=[(role,entry,False) for role,entry in doc.get('artwork',{}).items()]+[(None,entry,True) for entry in doc.get('artwork_archive',[])]
        for role,entry,archived in items:
            entry=copy.deepcopy(entry);image=relative_file(path.parent,entry['png'])
            refreshed=session.refresh_artwork(entry,image.read_bytes())
            if refreshed!=entry:session.warnings.append('Externally edited artwork accepted as Custom: '+str(role or entry['role']))
            entry=refreshed
            entry['png']=str(image)
            if entry.get('source_png'):
                high=relative_file(path.parent,entry['source_png'])
                source_raw=high.read_bytes();decode_rgba_png(source_raw)
                if sha(source_raw)!=entry['source_sha256']:
                    session.warnings.append('Externally edited artwork source accepted: '+high.name)
                    entry['source_sha256']=sha(source_raw)
                entry['source_png']=str(high)
            # The pixel inputs are reconstructed through the established codec;
            # rebind evidence after verifying all pinned resources above.
            if 'input_signature' in entry:entry['input_signature']=session.signature()
            if archived:session.artwork_archive.append(entry)
            else:session.artwork[role]=entry
        from .livery_artwork import normalize_presets
        session.art_presets=normalize_presets(doc.get('art_presets',session.art_presets))
        session.saved=session.full_signature()
        return session


def WorkshopProjectState(data):
    """Use the existing history schema, including unrelated authoring state."""
    project = object.__new__(WorkshopProject); project.data = data
    return project._state()
