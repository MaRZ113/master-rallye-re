"""Physics, qualified follow extents and presentation authoring over SDK Core.

Only working copies change. Native identities and source asset names stay fixed.
"""
from __future__ import annotations
import copy,hashlib,json,math,re,shutil,uuid
from pathlib import Path
from master_rallye.addon_sdk.physics_profile import MEMBERS,compile_family,validate_player_defaults,POSITIVE,NONNEGATIVE
from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes
from .camera_lab import CameraLabAuthoring

def sha(data):return hashlib.sha256(data).hexdigest()
def typed(row):
    value=row['value'];kind=row['type']
    if kind=='Bool':return value.lower()=='true'
    if kind=='Int':return int(value)
    if kind=='Float':return float(value)
    if kind in ('Vector2','Vector3'):return [float(x) for x in value.split()]
    return value

def field_info(path,kind,member):
    editable=path.split('/')[0] in ('Dimensions','Chassis','Engine','Steering','Suspension')
    if member==MEMBERS[1]:
        from master_rallye.vehicle_family_broker import PLAYER_MODIFICATION_FIELDS
        editable=path.split('/Modifications/',1)[-1] in PLAYER_MODIFICATION_FIELDS
    if path in ('Engine/Gears','Engine/TorqueEntries'):editable=False
    unit='native units; per-field semantics not qualified'
    if path.startswith('Dimensions/') or path.endswith(('/RideHeight','/MaxBounce','/MaxDroop','/CentreOfGravity')):unit='m'
    if path.endswith(('/TotalMass','/UnsprungMass')):unit='kg'
    if path.endswith(('/RevLimit','/IdleRevs')):unit='RPM'
    if path.endswith(('/PeakTorque','/MaxClutchTorque','/BrakeTorqueFront','/BrakeTorqueRear','/HandBrakeTorque')):unit='N m'
    if path.endswith('/Gravity'):unit='m/s²'
    if path.endswith('/MomentOfInertia'):unit='configured radius vector (m), non-cuboid mode; not a direct kg m² tensor'
    guard='typed SDK validation + dependent schema checks; observed ranges are not engine limits'
    if path in POSITIVE:guard='>0; finite float32, |value|≤1e9; dependent checks'
    if path in NONNEGATIVE:guard='≥0; finite float32, |value|≤1e9; dependent checks'
    if path.startswith('Dimensions/'):guard='(0,20] m'
    if path.endswith('/RideHeight'):guard='±2 m; initialization datum, not measured equilibrium'
    if path.endswith(('/MaxBounce','/MaxDroop')):guard='[0,2] m'
    if path=='Engine/DriveType':guard='0 AWD / 1 RWD / 2 FWD (native configuration mapping)'
    if path=='Engine/BrakeBias':guard='[0,1]'
    if path.endswith('LSDBias'):guard='[1,20], conservative author guard'
    if member==MEMBERS[1]:
        unit+='; additive player delta (GearRatioDiff is relative multiplier delta)'
        guard='finite typed delta; existing compiler validates effective base + delta and dependent player defaults, not absolute base-field limits'
    return {'editable':editable,'units':unit,'bounds':guard,'group':('/'.join(path.split('/')[:2]) if path.startswith(('Suspension/','Player')) else path.split('/')[0]),
            'evidence':'Existing typed physics compiler; V-PHYS1/2 reader/consumer map. Initialization only, no live solver.'}

class VehicleAuthoring(CameraLabAuthoring):
    def vehicle_state(self):
        from .service import write_json
        if not self.data.get('vehicle_authoring'):
            base=self.root/'author-baseline';base.mkdir(exist_ok=True);pins={}
            for name in ('addon.json','physics-profile.json','ui-assets.json','camera-profile.json'):
                source=self.working/name;dest=base/name
                if source.exists():
                    if not dest.exists():shutil.copyfile(source,dest)
                    pins[name]=sha(dest.read_bytes())
            self.data['vehicle_baseline_pins']=pins
            addon=json.loads((base/'addon.json').read_text()) if 'addon.json' in pins else {}
            self.data['vehicle_authoring']={'physics':json.loads((base/'physics-profile.json').read_text()) if 'physics-profile.json' in pins else None,
                'camera':json.loads((base/'camera-profile.json').read_text()) if 'camera-profile.json' in pins else None,'details':{k:addon.get('frontend',{}).get(k,'') for k in ('manufacturer','model','combined')},'aliases':{},'art':{}}
            self.data['vehicle_authoring']['details'].update(display_name=addon.get('results',{}).get('display_name',''),description=addon.get('description',''))
            self.save()
        for name,digest in self.data['vehicle_baseline_pins'].items():
            if sha((self.root/'author-baseline'/name).read_bytes())!=digest:raise ValueError('Vehicle author baseline changed: '+name)
        state=copy.deepcopy(self.data['vehicle_authoring'])
        if 'race_marker'not in state:
            base=self.root/'author-baseline/addon.json'
            state['race_marker']=json.loads(base.read_text()).get('race_colour_rgba')if base.exists()else None
        return state

    def _retail_members(self):
        """One exact-archive authority, reused from the existing project compiler."""
        from master_rallye.addon_sdk.project import _physics_family_overlays
        from master_rallye.addon_sdk.manifest import load_capabilities
        from master_rallye.addon_sdk.ui_assets import _open_sma_archive,archive_member
        from master_rallye.vehicle_project import VehicleProject
        s=self.data['build_settings'];author=VehicleProject.load(self.working/'vehicle-project.json')
        addon=json.loads((self.working/'addon.json').read_text())
        caps,_=load_capabilities(Path(__file__).resolve().parents[3]/'research/vehicles/sdk/capabilities/retail-2001.json')
        _physics_family_overlays(data_sma=Path(s['retail_sma']),retail_data_root=Path(s['retail_root']),capabilities=caps,donor_family=author.vehicle_name,runtime_family=addon['identity']['runtime_family'])
        with _open_sma_archive(Path(s['retail_sma'])) as archive:return {name:archive_member(archive,name) for name in MEMBERS}

    def physics_compile(self, profile=None):
        state=self.vehicle_state();profile=profile or state['physics']
        if self.data['kind']!='addon' or profile is None:raise ValueError('Independent typed physics requires a qualified addon physics profile')
        baseline=json.loads((self.root/'author-baseline/physics-profile.json').read_text())
        if (profile['donor_family'],profile['runtime_family'])!=(baseline['donor_family'],baseline['runtime_family']):raise ValueError('Physics family identities are locked')
        members=self._retail_members();result={};reports={}
        for member,raw in members.items():
            result[member],reports[member]=compile_family(raw,profile,donor_family=profile['donor_family'],runtime_family=profile['runtime_family'],source_label=member)
        validate_player_defaults(result[MEMBERS[0]],result[MEMBERS[1]],profile['runtime_family'],profile.get('ride_height_reference_m'))
        return result,reports

    def physics_inspect(self,reference=None):
        state=self.vehicle_state();profile=state['physics']
        if self.data['kind']!='addon' or profile is None:raise ValueError('Physics editor is addon-only; stock passthrough preserved')
        members=self._retail_members();compiled,_=self.physics_compile(profile);rows=[]
        for member,raw in members.items():
            doc=parse_vehicle_config_bytes(raw,build='retail-2001-verified');original=doc.families[profile['donor_family']]
            other=doc.families.get(reference or profile['donor_family'],{})
            current=parse_vehicle_config_bytes(compiled[member],build='retail-2001-verified').families[profile['runtime_family']]
            for path,row in original.items():
                info=field_info(path,row['type'],member)
                rows.append({'member':member,'path':path,'type':row['type'],'original':typed(row),'value':typed(current[path]),
                             'reference':typed(other[path]) if path in other and other[path]['type']==row['type'] else None,**info})
        families=[]
        from master_rallye.addon_sdk.physics_profile import _base_validate
        for family in parse_vehicle_config_bytes(members[MEMBERS[0]],build='retail-2001-verified').families:
            try:_base_validate(members[MEMBERS[0]],family);families.append(family)
            except (ValueError,KeyError):pass
        return {'rows':rows,'families':sorted(families),'donor':profile['donor_family'],'runtime_family':profile['runtime_family'],'pins':profile['source_sha256'],
                'warning':'Game initialization, not a live simulator. Dimensions/ride datum affect physics wheel anchors; do not auto-correct visual geometry or camera.'}

    def _vehicle_commit(self,state):
        from .service import write_json
        self._record();self.data['vehicle_authoring']=copy.deepcopy(state);self.vehicle_materialize();self.save()

    def physics_update(self,member,path,value):
        info=self.physics_inspect();row=next((r for r in info['rows'] if (r['member'],r['path'])==(member,path)),None)
        if not row or not row['editable']:raise ValueError('Read-only or unsupported native physics field')
        state=self.vehicle_state();state['physics'].setdefault('overrides',{}).setdefault(member,{})[path]=value
        self.physics_compile(state['physics']);self._vehicle_commit(state)

    def physics_copy_reference(self,family,group):
        info=self.physics_inspect(family)
        if family not in info['families']:raise ValueError('Reference family is not typed/schema qualified')
        state=self.vehicle_state();copied=[];retained=[]
        for row in info['rows']:
            if row['member']!=MEMBERS[0] or row['group']!=group:continue
            # Fitment, count-driven arrays and collision stay with this car.
            if not row['editable'] or row['reference'] is None or row['path'].startswith('Dimensions/') or row['path'].endswith('/RideHeight') or re.fullmatch(r'Engine/(?:Gear|ChangeUpRevs|ChangeDownRevs|TorqueEntry)\d+',row['path']):retained.append(row['path']);continue
            state['physics'].setdefault('overrides',{}).setdefault(row['member'],{})[row['path']]=row['reference'];copied.append(row['path'])
        if not copied:raise ValueError('No compatible non-fitment fields in this reference group')
        self.physics_compile(state['physics']);state['physics']['notes']+='\nExplicit stock reference '+family+' group '+group+' (fitment/count arrays retained).'
        self._vehicle_commit(state);return {'copied':copied,'retained':retained,'source':family,'pins':info['pins']}

    def camera_source(self):
        """Reuse SDK resource transforms, then pin exact output checked again by roster."""
        from master_rallye.addon_sdk.project import _mechanical_artifacts,_apply_visual_fitment
        from master_rallye.vehicle_project import VehicleProject
        if self.data['kind']=='stock':
            from master_rallye.addon_sdk.stock_project import QUALIFIED_STOCK
            if not self.data['car_id'] or QUALIFIED_STOCK.get(self.data['car_id'])!=self.data['family']:raise ValueError('Stock camera CarID/family is not qualified; CarID0 is read-only')
            return (self.assets/'car.dx').read_bytes()
        if self.data['kind']!='addon':raise ValueError('Camera requires a qualified addon or stock copy-on-write project')
        state=self.vehicle_state();p=state['physics'];s=self.data['build_settings'];author=VehicleProject.load(self.working/'vehicle-project.json')
        resources={n:(self.assets/n).read_bytes() for n in ('car.dx','complete.dx','wheel.dx')}
        if p and p.get('collision_fit'):
            from master_rallye.addon_sdk.physics_collision import fit_collision
            resources['car.dx'],_=fit_collision(resources['car.dx'],p['collision_fit'])
        family=json.loads((self.working/'addon.json').read_text())['identity']['runtime_family']
        resources,_=_mechanical_artifacts(self.working,family,resources,Path(s['retail_sma']),donor_family=author.vehicle_name)
        resources,_=_apply_visual_fitment(self.working,resources)
        return resources['car.dx']

    def camera_inspect(self):
        from master_rallye.dx import parse_dx_bytes
        from master_rallye.bounds import parse_bounds1339
        raw=self.camera_source();model=parse_dx_bytes(raw);bounds=parse_bounds1339(model.collision.unparsed_data)
        if bounds is None:raise ValueError('No qualified native model bounds')
        state=self.vehicle_state();original={'half_length_m':(bounds.maximum[2]-bounds.minimum[2])/2,'height_m':bounds.maximum[1]-bounds.minimum[1]}
        family=json.loads((self.working/'addon.json').read_text())['identity']['runtime_family'] if self.data['kind']=='addon' else self.data['family']
        return {'source_model_sha256':sha(raw),'original':original,'current':(state['camera'] or {}).get('follow_extents',original),
                'car_id':self.data['car_id'],'family':family,'minimum':bounds.minimum,'maximum':bounds.maximum,
                'boundary':'Only native follow extents are editable, not direct distance/position. FOV/smoothing/focus/replay authoring unsupported. Camera Lab static pose diagnostics and Free Inspection remain separate.'}

    def camera_update(self,half_length,height,car_id=None):
        from master_rallye.addon_sdk.camera_profile import bind_camera_profile
        info=self.camera_inspect();target=info['car_id'] if car_id is None else car_id
        if target!=self.data['car_id']:raise ValueError('Camera target must match this qualified project CarID')
        profile={'version':1,'car_id':target,'policy':'native_follow_extents','runtime_family':info['family'],
                 'source_model_sha256':info['source_model_sha256'],'follow_extents':{'half_length_m':half_length,'height_m':height}}
        bind_camera_profile(profile,self.camera_source());state=self.vehicle_state();state['camera']=profile;self._vehicle_commit(state)

    def camera_reset_original(self):
        state=self.vehicle_state();state['camera']=None;self._vehicle_commit(state)

    def details_update(self,fields):
        from master_rallye.addon_sdk.manifest import _validate_one
        if self.data['kind']!='addon':raise ValueError('Stock display identity is read-only; native stock resource renaming is not supported')
        limits={'manufacturer':32,'model':64,'combined':96,'display_name':64,'description':8192}
        if set(fields)!=set(limits):raise ValueError('Invalid vehicle display fields')
        for key,value in fields.items():
            if not isinstance(value,str) or len(value)>limits[key] or (key!='description' and (not value.strip() or any(not 32<=ord(c)<=126 for c in value))):raise ValueError(key+': printable ASCII required within SDK character budget '+str(limits[key]))
        addon=json.loads((self.working/'addon.json').read_text());addon['frontend'].update({k:fields[k] for k in ('manufacturer','model','combined')});addon['results']['display_name']=fields['display_name'];addon['description']=fields['description'];_validate_one(addon)
        state=self.vehicle_state();state['details']=dict(fields);self._vehicle_commit(state)

    def marker_inspect(self):
        from .race_marker import colour_info
        if self.data['kind']!='addon':raise ValueError('Marker authoring requires an independently registered addon CarID; stock registration is read-only')
        state=self.vehicle_state();baseline=json.loads((self.root/'author-baseline/addon.json').read_text())['race_colour_rgba']
        current=state['race_marker'];colour_info(current)
        if current[3]!=baseline[3]:raise ValueError('Race marker alpha ownership changed')
        return {'original':colour_info(baseline),'current':colour_info(current),'car_id':self.data['car_id'],'boundary':'VehicleRecord +24..+30 -> Race/CarN/Colour. Per-vehicle marker only; shared HUD image and body/UI art unchanged.'}

    def marker_update(self,rgb):
        from .race_marker import normalized_rgb
        info=self.marker_inspect();state=self.vehicle_state();state['race_marker']=[*normalized_rgb(rgb),info['original']['rgba'][3]]
        self._vehicle_commit(state);return self.marker_inspect()

    def alias_update(self,texture,label):
        if texture not in self.data['inputs'] or not texture.endswith('.dxt'):raise ValueError('Alias needs an owned texture ID')
        if not isinstance(label,str) or len(label)>80 or any(ord(c)<32 for c in label):raise ValueError('Alias must be bounded display text')
        state=self.vehicle_state()
        if label.strip():state['aliases'][texture]={'label':label.strip(),'source_sha256':self.data['inputs'][texture]}
        else:state['aliases'].pop(texture,None)
        self._vehicle_commit(state)

    def texture_search(self,query=''):
        aliases=self.vehicle_state()['aliases'];q=query.casefold()
        return [{'name':n,'alias':aliases.get(n,{}).get('label','')} for n in self.data['inputs'] if n.endswith('.dxt') and (not q or q in (n+' '+aliases.get(n,{}).get('label','')).casefold())]

    def vehicle_reset(self,section=None):
        state=self.vehicle_state();defaults=self.vehicle_defaults()
        if section is not None and section not in defaults:raise ValueError('Unknown authoring section')
        for key in ([section] if section else defaults):state[key]=defaults[key]
        self._vehicle_commit(state)

    def vehicle_defaults(self):
        base=self.root/'author-baseline'
        for name,digest in self.data['vehicle_baseline_pins'].items():
            if sha((base/name).read_bytes())!=digest:raise ValueError('Vehicle author baseline changed: '+name)
        defaults={'physics':json.loads((base/'physics-profile.json').read_text()) if (base/'physics-profile.json').exists() else None,'camera':json.loads((base/'camera-profile.json').read_text()) if (base/'camera-profile.json').exists() else None,'aliases':{},'art':{}}
        addon=json.loads((base/'addon.json').read_text()) if (base/'addon.json').exists() else {}
        defaults['details']={k:addon.get('frontend',{}).get(k,'') for k in ('manufacturer','model','combined')}
        defaults['details'].update(display_name=addon.get('results',{}).get('display_name',''),description=addon.get('description',''))
        defaults['race_marker']=addon.get('race_colour_rgba')
        return defaults

    def vehicle_inherit(self,other):
        """Exact metadata replay for compatible new visual versions; report conflicts."""
        if not other.data.get('vehicle_authoring'):return {'applied':[],'conflicts':[]}
        source=other.vehicle_state();state=self.vehicle_state();report={'applied':[],'conflicts':[]}
        state['physics']=source['physics'];state['details']=source['details'];state['race_marker']=source['race_marker']
        for name,alias in source['aliases'].items():
            if self.data['inputs'].get(name)==alias['source_sha256']:state['aliases'][name]=alias;report['applied'].append(name)
            else:report['conflicts'].append({'alias':name,'reason':'texture changed or omitted by this appearance version'})
        if source['camera']:report['conflicts'].append({'camera':'Requalify source-model hash for new visual version'})
        if source['art']:report['conflicts'].append({'art':'Regenerate for new source geometry; original pins retained in source project'})
        self._vehicle_commit(state);return report

    def vehicle_restore_author_baseline(self,author):
        """Seed new visual versions from original author data, before replaying layers."""
        if not self.data.get('vehicle_authoring'):return
        from .service import write_json
        self.vehicle_defaults() # Check immutable author pins first.
        base=self.root/'author-baseline';author=Path(author)
        for name in ('physics-profile.json','ui-assets.json','camera-profile.json'):
            if name in self.data['vehicle_baseline_pins']:shutil.copyfile(base/name,author/name)
        if (base/'addon.json').exists():
            original=json.loads((base/'addon.json').read_text());addon=json.loads((author/'addon.json').read_text())
            for key in ('manufacturer','model','combined'):addon['frontend'][key]=original['frontend'][key]
            addon['results']['display_name']=original['results']['display_name'];addon['description']=original.get('description','')
            addon['race_colour_rgba']=original['race_colour_rgba']
            write_json(author/'addon.json',addon)

    def vehicle_materialize(self):
        from .service import write_json,write_resource,plain_tree
        if not self.data.get('vehicle_authoring'):return
        state=self.vehicle_state();base=self.root/'author-baseline'
        if state['physics'] is not None:
            target=self.working/'physics-profile.json';original=json.loads((base/'physics-profile.json').read_text())
            if state['physics']==original:write_resource(target,(base/'physics-profile.json').read_bytes())
            elif json.loads(target.read_text())!=state['physics']:write_json(target,state['physics'])
        if self.data['kind']=='addon':
            addon=json.loads((self.working/'addon.json').read_text());original=json.loads((base/'addon.json').read_text());fields=state['details']
            addon['frontend'].update({k:fields[k] for k in ('manufacturer','model','combined')});addon['results']['display_name']=fields['display_name'];addon['description']=fields['description']
            if state['race_marker'][3]!=original['race_colour_rgba'][3]:raise ValueError('Race marker alpha remains read-only')
            from .race_marker import colour_info
            colour_info(state['race_marker']);addon['race_colour_rgba']=state['race_marker']
            # Metadata-only aliases must not rewrite zero-edit author bytes.
            if addon==original:write_resource(self.working/'addon.json',(base/'addon.json').read_bytes())
            elif addon!=json.loads((self.working/'addon.json').read_text()):write_json(self.working/'addon.json',addon)
            if 'ui-assets.json' in self.data['vehicle_baseline_pins']:
                ui=json.loads((base/'ui-assets.json').read_text())
                for role,entry in state['art'].items():
                    digest=entry['input_sha256'];raw=(self.root/'art-pins'/(digest+'.png')).read_bytes()
                    if sha(raw)!=digest:raise ValueError('Applied vehicle art changed')
                    rel='workshop-art/'+digest+'.png';target=plain_tree(self.working/rel);target.parent.mkdir(exist_ok=True);write_resource(target,raw)
                    ui['icons'][role]={'png':rel,'sha256':digest,'presentation':'mr-native-v1'}
                path=self.working/'ui-assets.json'
                if not state['art']:write_resource(path,(base/'ui-assets.json').read_bytes())
                elif json.loads(path.read_text())!=ui:write_json(path,ui)

    def vehicle_validate(self):
        if not self.data.get('vehicle_authoring'):return None
        state=self.vehicle_state();report={'aliases':len(state['aliases']),'camera':None,'physics':None,'gameplay':'PENDING_OWNER'}
        for name,alias in state['aliases'].items():
            if self.data['inputs'].get(name)!=alias['source_sha256']:raise ValueError('Alias source changed: '+name)
        if self.data['kind']=='addon':
            from master_rallye.addon_sdk.manifest import _validate_one
            from master_rallye.addon_sdk.ui_assets import build_ui_assets
            addon=json.loads((self.working/'addon.json').read_text());original=json.loads((self.root/'author-baseline/addon.json').read_text())
            for key in ('identity','physical_id','addon_id','vehicle_class','assets'):
                if addon[key]!=original[key]:raise ValueError('Locked native identity changed: '+key)
            _validate_one(addon)
            if addon['race_colour_rgba']!=state['race_marker']or state['race_marker'][3]!=original['race_colour_rgba'][3]:raise ValueError('Race marker state/alpha differs from authored ownership')
            if state['physics'] is not None:report['physics']=self.physics_compile()[1]
            _,ui=build_ui_assets(self.working,addon,Path(self.data['build_settings']['retail_sma']));report['ui']=ui
        if state['camera']:
            from master_rallye.addon_sdk.camera_profile import bind_camera_profile
            if state['camera']['car_id']!=self.data['car_id']:raise ValueError('Camera target changed from project identity')
            report['camera']=bind_camera_profile(state['camera'],self.camera_source())
        return report

    def camera_build_roster(self,roster,snapshot,build):
        from .service import write_json
        profile=self.vehicle_state()['camera']
        paths=[]
        for old in roster.get('camera_profiles',[]):
            existing=json.loads(Path(old).read_text())
            if existing['car_id']!=self.data['car_id']:paths.append(old)
        if profile:
            path=Path(snapshot)/'camera-profile.json';write_json(path,profile);paths.append(str(path))
        if paths:roster['camera_profiles']=paths
        else:roster.pop('camera_profiles',None)

    def art_generate(self,*,model='complete.dx',role=None,azimuth=None,elevation=None,padding=12):
        from .service import write_json
        from generate_vehicle_ui_previews import render_sources
        from master_rallye.addon_sdk.ui_preview import compose_preview
        from master_rallye.addon_sdk.ui_assets import decode_rgba_png
        import gtmat
        if model not in ('car.dx','complete.dx'):raise ValueError('Unsupported source presentation')
        self.materialize();out=self.root/'generated-art'/uuid.uuid4().hex
        render_inputs=self.art_input_pins()
        report=render_sources(self.assets,out,roles=[role] if role else None,azimuth=azimuth,elevation=elevation,padding=padding,model_name=model,wheel_profile=self.preview_profile() if model=='car.dx' else None)
        for key in report:
            image=decode_rgba_png((out/(key+'.png')).read_bytes());raw,style=compose_preview(image,key)
            size=(128,128) if key=='vehicle_select_art' else (32,16);path=out/(key+'-native.png');path.write_bytes(gtmat.png_from_rgba(*size,raw))
            source=out/(key+'.png')
            report[key].update(png=str(path),sha256=sha(path.read_bytes()),source_png=str(source),input_sha256=sha(source.read_bytes()),composition=style,source_model_sha256=sha((self.assets/model).read_bytes()),render_input_sha256=render_inputs)
        write_json(out/'generation.json',report);return report

    def art_input_pins(self):
        return {p.name:sha(p.read_bytes()) for p in self.assets.iterdir() if p.is_file() and p.suffix.lower() in ('.dx','.dxt')}

    def art_apply(self,report):
        from .service import plain_tree,write_resource
        from master_rallye.addon_sdk.ui_assets import decode_rgba_png,BANKS
        from master_rallye.addon_sdk.ui_preview import compose_preview
        if self.data['kind']!='addon':raise ValueError('Stock art preview is allowed; replacing stock bank frames is unsupported (append-only addon workflow)')
        state=self.vehicle_state();addon=json.loads((self.working/'addon.json').read_text());pins=self.root/'art-pins';pins.mkdir(exist_ok=True)
        for role,entry in report.items():
            if role not in BANKS or addon['frontend'][role]['policy']!='project_frame':raise ValueError('Vehicle art needs an existing qualified append-only project frame')
            if entry.get('source_model') not in ('car.dx','complete.dx') or entry.get('render_input_sha256')!=self.art_input_pins():raise ValueError('Art geometry/material/texture source changed; regenerate before Apply')
            path=plain_tree(entry['png'])
            if not path.resolve().is_relative_to((self.root/'generated-art').resolve()):raise ValueError('Art must come from this project generation')
            raw=path.read_bytes();w,h,_=decode_rgba_png(raw)
            if (w,h)!=BANKS[role][3] or sha(raw)!=entry['sha256']:raise ValueError('Generated art dimensions/hash changed')
            if entry['source_model_sha256']!=sha((self.assets/entry['source_model']).read_bytes()):raise ValueError('Art source changed; regenerate before Apply')
            source=plain_tree(entry['source_png'])
            if not source.resolve().is_relative_to((self.root/'generated-art').resolve()):raise ValueError('Art source outside owned generation')
            input_raw=source.read_bytes()
            if sha(input_raw)!=entry['input_sha256'] or compose_preview(decode_rgba_png(input_raw),role)[0]!=decode_rgba_png(raw)[2]:raise ValueError('Generated preview does not match canonical single-pass composition')
            write_resource(pins/(sha(input_raw)+'.png'),input_raw);state['art'][role]=copy.deepcopy(entry)
        self._vehicle_commit(state)

    def art_preview_png(self,role,*,original=False):
        """Display exact compiler output, including legacy alignment and row policy."""
        import tempfile
        from .service import write_json
        from master_rallye.addon_sdk.ui_assets import build_ui_assets
        from master_rallye.dxt import parse_dxt_bytes,encode_png,PNG_ROWS_FLIP_VERTICAL
        if self.data['kind']!='addon' or not (self.root/'author-baseline/ui-assets.json').exists():return None
        addon=json.loads((self.working/'addon.json').read_text())
        if original:
            config=json.loads((self.root/'author-baseline/ui-assets.json').read_text())
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                for entry in config['icons'].values():
                    source=self.working/entry['png'];target=root/entry['png'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
                write_json(root/'ui-assets.json',config);files,report=build_ui_assets(root,addon,Path(self.data['build_settings']['retail_sma']))
        else:files,report=build_ui_assets(self.working,addon,Path(self.data['build_settings']['retail_sma']))
        return encode_png(parse_dxt_bytes(files[report['roles'][role]['frame_path']]),row_policy=PNG_ROWS_FLIP_VERTICAL)
