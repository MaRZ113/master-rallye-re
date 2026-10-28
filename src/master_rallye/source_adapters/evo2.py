"""Qualified read-only Evo2 Toyota 4Runner source adapter, never an MR compiler."""
from __future__ import annotations
import math
from pathlib import Path

from .. import universal_vehicle_scene as uvs
from .evo2_formats import parse_smf, pod2_members, member_bytes, safe_name, decode_classic_tiff

POD_SHA256='5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41'
EXE_SHA256='ab8286e6bce8a1bf3769acddfeb0a79df2e5d43c72f462a89aa90f477951ec75'
CATALOG='TRUCK/T4RSR52.TRK'
CATALOG_SHA256='d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4'
BODY='MODELS/4RUNNERSR5.SMF'
BODY_SHA256='a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e'
DISPLAY_NAME='Toyota 4Runner SR5 Sport Package 2WD'
FEET_TO_METRES=0.3048
NORMALIZATION=[FEET_TO_METRES,0.,0.,0.,0.,FEET_TO_METRES,0.,0.,0.,0.,-FEET_TO_METRES,0.,0.,0.,0.,1.]
SLOTS=('faxle.rtire','faxle.ltire','raxle.rtire','raxle.ltire')
# Exact names present in this model admitted by original stock BODY mask
# 005d43f0/table0067d198 plus detail2 COCKPIT/GLASSI; not generic role guesses.
STOCK_BODY_OBJECTS=frozenset(('BODY','COCKPIT','GLASSI','GLASSE','MIRRORL','MIRRORR','RFRACK','UNDBODY','WIPERLT','WIPERRR','WIPERRT'))


def parse_trk(data: bytes) -> dict:
    if len(data)>1024*1024:raise ValueError('TRK byte budget')
    try:text=data.decode('ascii')
    except UnicodeError as error:raise ValueError('TRK must be ASCII')from error
    lines=[(i+1,row.strip())for i,row in enumerate(text.splitlines())if row.strip()]
    if len(lines)>16384 or any(len(row)>4096 for _,row in lines):raise ValueError('TRK line budget')
    keys=('version','truckName','truckMake','truckModel','truckClass','truckModelYear','truckModelBaseName',
          'tireModelBaseName','truckLength','truckWidth','truckHeight','truckWheelbase','truckFrontTrack','truckRearTrack',
          'numStockParts','numColors',*(slot+'.static_bpos'for slot in SLOTS))
    records={}
    for key in keys:
        matches=[i for i,(_,row)in enumerate(lines)if row==key]
        if len(matches)!=1 or matches[0]+1>=len(lines):raise ValueError('missing/ambiguous TRK field: '+key)
        i=matches[0];records[key]={'value':lines[i+1][1],'key_line':lines[i][0],'value_line':lines[i+1][0]}
    if records['version']['value']!='7':raise ValueError('unsupported TRK version')
    if records['truckName']['value']!=DISPLAY_NAME or records['truckModelBaseName']['value'].upper()!='4RUNNERSR5' or records['tireModelBaseName']['value'].upper()!='4RUNTIRE':
        raise ValueError('catalog/model identity mismatch')
    positions={}
    for slot in SLOTS:
        try:p=[float(v)for v in records[slot+'.static_bpos']['value'].split(',')]
        except ValueError as error:raise ValueError('invalid TRK wheel position')from error
        if len(p)!=3 or not all(math.isfinite(v)and abs(v)<100 for v in p):raise ValueError('invalid wheel position range')
        positions[slot]=p
    # This is a selected qualified source, not a heuristic for other trucks.
    if not (positions[SLOTS[0]][0]>0 and positions[SLOTS[1]][0]<0 and positions[SLOTS[2]][0]>0 and positions[SLOTS[3]][0]<0 and
            positions[SLOTS[0]][2]>positions[SLOTS[2]][2] and positions[SLOTS[1]][2]>positions[SLOTS[3]][2]):
        raise ValueError('ambiguous/mismatched source axle axes')
    stock_count=int(records['numStockParts']['value']);color_count=int(records['numColors']['value'])
    if stock_count!=0 or not 0<=color_count<=128:raise ValueError('unqualified stock-equipment/color count')
    def array(key,count):
        hits=[i for i,(_,row)in enumerate(lines)if row==key]
        if len(hits)!=1:raise ValueError('ambiguous TRK array '+key)
        start=hits[0]+1
        if start+count>len(lines):raise ValueError('truncated TRK array')
        return [{'line':line,'value':row}for line,row in lines[start:start+count]]
    colors=array('colorList[]',color_count)
    for row in colors:
        fields=row['value'].split(',')
        if len(fields)!=7:raise ValueError('unsupported source color record')
        if not all(math.isfinite(float(v))for v in fields[:6]):raise ValueError('nonfinite source color')
    return {'records':records,'wheel_positions':positions,'stock_parts':array('stockPartList[]',stock_count),
            'color_records':colors,'raw_lines':[{'line':i,'text':row}for i,row in lines]}


def decode_tiff(data: bytes) -> tuple[dict,bytes,bytes,bytes]:
    return decode_classic_tiff(data)


def _read_source(root: Path):
    root=Path(root).absolute();uvs.unlinked(root)
    pod=uvs.read_bounded(root/'TRUCK.POD',512*1024*1024)
    if uvs.sha(pod)!=POD_SHA256:raise ValueError('unsupported/mismatched qualified Evo2 TRUCK.POD SHA256')
    exe=uvs.read_bounded(root/'4x42.exe',16*1024*1024)
    if uvs.sha(exe)!=EXE_SHA256:raise ValueError('unsupported Evo2 executable identity for static interpretation')
    entries=pod2_members(pod);by_name={e.name.casefold():e for e in entries}
    def get(name):
        e=by_name.get(safe_name(name).casefold())
        if e is None:raise ValueError('missing required source member: '+name)
        return e,member_bytes(pod,e)
    _,catalog=get(CATALOG);_,body=get(BODY)
    if uvs.sha(catalog)!=CATALOG_SHA256 or uvs.sha(body)!=BODY_SHA256:raise ValueError('qualified body/catalog resource hash mismatch')
    trk=parse_trk(catalog)
    return root,pod,exe,get,trk


def inspect_source(source_root: Path, catalog: str=CATALOG) -> dict:
    if catalog.casefold()!=CATALOG.casefold():raise ValueError('this pilot supports only TRUCK/T4RSR52.TRK')
    root,pod,exe,get,trk=_read_source(source_root)
    return {'schema':'evo2-source-catalog/1','display_name':DISPLAY_NAME,'model_year':2000,'catalog':CATALOG,
            'source_root':str(root),'pod_sha256':uvs.sha(pod),'exe_sha256':uvs.sha(exe),
            'wheel_details':['08','12','16'],'source_authenticity':'local modified installation; publisher provenance unverified',
            'wheel_positions':trk['wheel_positions']}


def _protected(source_root,config_path=None):
    roots=[Path(source_root),Path(__file__).resolve().parents[3]/'tools']
    config=Path(config_path)if config_path else Path(__file__).resolve().parents[3]/'research/vehicles/source-garage/roots.example.json'
    if not config.is_file():raise ValueError('source-root protection configuration is required and must exist')
    import json
    cfg=json.loads(uvs.read_bounded(config,1024*1024))
    if cfg.get('schema')!='source-garage-roots/1' or not isinstance(cfg.get('games'),list) or not 1<=len(cfg['games'])<=64:
        raise ValueError('unsupported source-root protection configuration')
    base=Path(cfg['base']);roots.extend((base,base.parent/'tools'))
    for game in cfg['games']:
        p=Path(game['path']);roots.append(p if p.is_absolute()else base/p)
    for p in cfg.get('protected_roots',[]):roots.append(Path(p))
    return roots


def create_scene(source_root: Path, output: Path, *, catalog: str=CATALOG, wheel_detail: str='16', config_path=None) -> dict:
    if catalog.casefold()!=CATALOG.casefold()or wheel_detail not in ('08','12','16'):raise ValueError('unqualified catalog/wheel detail')
    protected=_protected(source_root,config_path);uvs.output_directory(output,protected)
    root,pod,exe,get,trk=_read_source(source_root)
    assets={};resources={};meshes=[];nodes=[];materials=[];textures=[];texture_ids={};asset_bytes=0;decoded_texture_bytes=0
    def add_asset(path,blob):
        nonlocal asset_bytes
        if path in assets:raise ValueError('duplicate adapter sidecar')
        asset_bytes+=len(blob)
        if asset_bytes>uvs.MAX_OUTPUT_BYTES:raise ValueError('adapter aggregate sidecar output budget')
        assets[path]=blob
    def resource(name):
        e,blob=get(name);key=e.name.casefold()
        if key not in resources:
            relative='original/'+safe_name(e.name)
            add_asset(relative,blob)
            resources[key]={'member':e.name,'offset':e.offset,'bytes':e.size,'sha256':uvs.sha(blob),
                            'snapshot_path':relative,'stored_checksum':e.checksum,'stored_checksum_status':'NOT TESTED'}
        return resources[key],blob
    def texture(name):
        nonlocal decoded_texture_bytes
        key=name.casefold()
        if key in texture_ids:return texture_ids[key]
        rec,blob=resource('ART/'+safe_name(name));meta,rgba,samples,palette=decode_tiff(blob)
        decoded_texture_bytes+=len(rgba)
        if decoded_texture_bytes>uvs.MAX_TEXTURE_BYTES or len(textures)>=256:raise ValueError('adapter aggregate decoded texture budget')
        tid=f'texture-{len(textures):03d}';path=f'textures/{tid}.rgba';add_asset(path,rgba)
        rawpath=f'textures/{tid}.samples';add_asset(rawpath,samples)
        meta['source_channels']['raw_samples_path']=rawpath
        if palette:
            palpath=f'textures/{tid}.palette';add_asset(palpath,palette)
            meta['source_channels']['palette_path']=palpath
        textures.append({'id':tid,**meta,'rgba_path':path,'rgba_sha256':uvs.sha(rgba),'source':rec})
        texture_ids[key]=tid
        return tid
    def model(name,role):
        rec,blob=resource(name);decoded=parse_smf(blob);ids=[]
        for i,obj in enumerate(decoded['objects']):
            mid=f'mesh-{len(meshes):03d}';matid='material-'+mid[5:]
            material={'id':matid,'diffuse_texture_id':texture(obj['texture']),'raw_fields':obj['material_raw'],
                      'flags':{'transparent_raw':obj['material_raw'][3],'reflective_raw':obj['material_raw'][4]},
                      'source':{'member_sha256':rec['sha256'],'object_index':i,'object_name':obj['name'],'version':obj['material_version']},
                      'unsupported':['native lighting/reflection','native TIFF alpha policy'],
                      'preview':{'opacity':1.0,'policy':'original texture channels; no synthetic glass alpha'}}
            if obj['bump_texture']:
                material['bump_texture_id']=texture(obj['bump_texture']);material['unsupported'].append('native bump mapping')
            materials.append(material)
            frame=obj['vertices_by_frame'][0]
            meshes.append({'id':mid,'name':obj['name'],'positions':[v[:3]for v in frame],
                           'normals':[v[3:6]for v in frame],'uvs':[v[6:8]for v in frame],'triangles':obj['faces'],
                           'material_id':matid,'animation_frames':obj['vertices_by_frame'],
                           'source':{'member':rec['member'],'member_sha256':rec['sha256'],'object_index':i,
                                     'source_visible':obj['visible'],'unknown_object_field':obj['unknown_object_field'],
                                     'lod_info_raw':decoded['lod_info_raw'],'object_parent':'not encoded in selected SMF grammar'},
                           'role':role})
            ids.append(mid)
        return decoded,ids
    resource(CATALOG)
    body,body_ids=model(BODY,'body')
    nodes.append({'id':'body-root','name':'Body assembly (derived grouping)','mesh_ids':[],
                  'parent_id':None,'source_local_transform':None,'local_transform':uvs.IDENTITY[:],
                  'visible':True,'source_visible':True,'role':'body',
                  'transform_evidence':'source SMF positions share body frame; grouping is derived, no source parent invented'})
    for obj,mid in zip(body['objects'],body_ids):
        nodes.append({'id':'node-'+mid,'name':obj['name'],'mesh_ids':[mid],'parent_id':'body-root',
                      'source_local_transform':None,'local_transform':uvs.IDENTITY[:],
                      'source_visible':obj['visible'],'visible':obj['visible']and obj['name'].upper()in STOCK_BODY_OBJECTS,
                      'role':'body','transform_evidence':'no per-object matrix encoded; original body-space vertices retained',
                      'visibility_evidence':'native stock BODY mask005d43f0/table0067d198 + detail2 COCKPIT/GLASSI; numStockParts0'})
    variants={}
    for detail in ('08','12','16'):
        for side in ('L','R'):
            name=f'MODELS/4RUNTIRE{detail}{side}.SMF';parsed,ids=model(name,'wheel')
            variants[detail+side]={'member':name,'mesh_ids':ids,'vertices':parsed['vertices_including_frames'],'triangles':parsed['triangles']}
    for slot in SLOTS:
        p=trk['wheel_positions'][slot];side='R'if'.rtire'in slot else'L';matrix=uvs.IDENTITY[:]
        matrix[3],matrix[7],matrix[11]=p
        nodes.append({'id':slot,'name':slot,'mesh_ids':variants[wheel_detail+side]['mesh_ids'],
                      'parent_id':None,'source_local_transform':None,'local_transform':matrix,
                      'source_transform_record':{'translation':p[:],'rotation':None,'scale':None,
                                                 'member':CATALOG,'key':slot+'.static_bpos',
                                                 'note':'original translation record; no source4x4 matrix was stored'},
                      'source_visible':True,'visible':True,'role':'wheel','wheel_slot':slot,
                      'transform_evidence':{'kind':'source_bytes','member':CATALOG,'record':slot+'.static_bpos',
                                            'line':trk['records'][slot+'.static_bpos']['value_line'],
                                            'orientation':'distinct original L/R model; zero steer/spin inspection pose'}})
    fr,fl,rr,rl=[trk['wheel_positions'][s]for s in SLOTS]
    def bounds(points):
        return {'min':[min(p[i]for p in points)for i in range(3)],'max':[max(p[i]for p in points)for i in range(3)]}
    mesh_by_id={m['id']:m for m in meshes}
    wheel_measurements={}
    for key,variant in variants.items():
        points=[p for mid in variant['mesh_ids']for p in mesh_by_id[mid]['positions']]
        box=bounds(points)
        wheel_measurements[key]={'bounds_source':box,'width_source':box['max'][0]-box['min'][0],
                                 'outer_radius_source':max(math.hypot(p[1],p[2])for p in points),
                                 'geometry_is_original_distinct_side':True}
    source_points=[p for mid in body_ids for p in mesh_by_id[mid]['positions']]
    norm_points=[uvs.transform_point(NORMALIZATION,p)for p in source_points]
    inverse_error=max(abs((q[i]/FEET_TO_METRES)*(1 if i<2 else-1)-p[i])for p,q in zip(source_points,norm_points)for i in range(3))
    measures={'source_units':'ft','front_track_source':fr[0]-fl[0],'rear_track_source':rr[0]-rl[0],
              'wheelbase_static_source':fr[2]-rr[2],'wheelbase_catalog_source':float(trk['records']['truckWheelbase']['value']),
              'normalization_metres_per_source_unit':FEET_TO_METRES,
              'wheel_positions_source':trk['wheel_positions'],
              'wheel_positions_normalized':{s:uvs.transform_point(NORMALIZATION,p)for s,p in trk['wheel_positions'].items()},
              'front_track_metres':(fr[0]-fl[0])*FEET_TO_METRES,'rear_track_metres':(rr[0]-rl[0])*FEET_TO_METRES,
              'wheelbase_static_metres':(fr[2]-rr[2])*FEET_TO_METRES,
              'wheelbase_catalog_metres':float(trk['records']['truckWheelbase']['value'])*FEET_TO_METRES,
              'body_all_objects_bounds_source':bounds(source_points),'body_all_objects_bounds_normalized':bounds(norm_points),
              'source_normalization_roundtrip_max_error':inverse_error,
              'original_positions_normals_uvs_indices_edited':False,'wheel_variant_measurements':wheel_measurements,
              'rest_pose':'native highdetail2, wheelLOD inspection, zero steering/spin/axleangles; not gravity-settled runtime'}
    code_files=(Path(__file__),Path(__file__).with_name('evo2_formats.py'),Path(uvs.__file__))
    scene={'schema':uvs.SCHEMA,'metadata':{'display_name':DISPLAY_NAME,'model_year':2000,'source_adapter':'evo2-4runner/1',
                                         'implementation_sha256':{p.name:uvs.sha(p.read_bytes())for p in code_files}},
           'source':{'game':'4x4 Evolution 2','root':str(root),'catalog':CATALOG,'pod':{'path':'TRUCK.POD','bytes':len(pod),'sha256':uvs.sha(pod)},
                     'protected_roots':sorted({str(Path(p).absolute())for p in protected}),
                     'executable':{'path':'4x42.exe','bytes':len(exe),'sha256':uvs.sha(exe),'execution':'NEVER'},
                     'authenticity':'user-local modified installation; no publisher authenticity claim',
                     'resources':list(resources.values()),'catalog_original':trk},
           'coordinate_system':{'source':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,1],'units':'ft',
                                          'handedness':'left-handed anatomical vehicle frame; static interpretation'},
                                'normalized':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,-1],'units':'m','handedness':'right-handed'},
                                'source_to_normalized':NORMALIZATION[:],
                                'interpretation_status':'source-record-backed static frame; source-game dynamic rendering NOT TESTED',
                                'evidence':['TRK right/left tire X signs, front/rear axle Z positions',
                                            'original TRK light body axis positions explicitly labeled(ft); headlamp vs rear headings',
                                            'source dimensions/driver-head/roof-light positive height; derived RH mirrorZ preserves source values']},
           'meshes':meshes,'nodes':nodes,'materials':materials,'textures':textures,'wheel_variants':variants,'measurements':measures,
           'selection':{'wheel_detail':wheel_detail,'wheel_policy':'explicit static inspection detail; not source runtime graphics setting',
                        'catalog_stock_parts':trk['stock_parts'],
                        'hidden_objects':sorted(o['name']for o in body['objects']if o['name'].upper()not in STOCK_BODY_OBJECTS),
                        'body_detail':2,'wheel_lod_index':{'08':0,'12':1,'16':2}[wheel_detail],
                        'equipment_status':'native stock BODY draw mask, detail2; auxiliary axle/light systems remain separate',
                        'native_evidence':['005d43f0/table0067d198 stock visibility;005b2bd0 checks byte+e14',
                                           '005ed4b0 loads all6 wheel variants; wheelarrays170c/1718 selectedby12a0',
                                           '005f6ec0 zeroangles/highbodydetail preservesstatic_bpos;1.05 appliesonlydetail0']},
           'unknown_semantics':[{'id':'native-rendering','status':'UNSUPPORTED','meaning':'native reflections, lighting, alpha/glass and animation are not replicated'},
                                {'id':'catalog-wheelbase','status':'WARN','meaning':'static hub distance8.88ft differs from catalog wheelbase8.78ft; both preserved'},
                                {'id':'hierarchy','status':'WARN','meaning':'SMF flat object order retained; derived assembly groups are not original parent records'},
                                {'id':'source-colors','status':'NOT TESTED','meaning':'all nine original color records retained; no recolor algorithm inferred'},
                                {'id':'tiff-extra-samples','status':'UNSUPPORTED','meaning':'body indexed TIFF second sample and bump fourth sample unspecified; all raw channels and palettes preserved; opaque RGBA cache is an explicit neutral interpretation'},
                                {'id':'auxiliary-passes','status':'UNSUPPORTED','meaning':'Axler and Light meshes retained but disabled in static BODY pass; independent native axle/light dynamic rendering not reproduced'},
                                {'id':'native-dynamics','status':'NOT TESTED','meaning':'static_bpos is original datum, not a settled suspension/steering/animation runtime pose'}]}
    result=uvs.save_scene(scene,Path(output),assets,protected_roots=protected)
    if uvs.sha(uvs.read_bounded(root/'TRUCK.POD',512*1024*1024))!=POD_SHA256:raise ValueError('source changed during scene generation')
    return {**result,'display_name':DISPLAY_NAME,'measurements':measures,'wheel_detail':wheel_detail,
            'L0':'PASS','L1':'WARN','L2':'NOT TESTED','Gameplay':'NOT TESTED','source_unchanged':True}
