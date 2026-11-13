"""4x4 Evolution 2 GameCube exclusive trucks -> Universal Vehicle Scene v1 (MR Classic pilots).

Source: TRUCK.pod extracted from the GC disc (research/source-formats, evo2-gc/tools/rvz.py).
Same POD2/SMF/TIFF grammar as the PC game (evo2_formats). Unlike the qualified 4Runner
adapter (evo2.py) this one is generic over the four GC-only TRK catalogs and selects the
stock object set by an explicit, recorded rule (body objects + TRK stock parts).
"""
from __future__ import annotations
import math
from pathlib import Path
from .. import universal_vehicle_scene as uvs
from .evo2_formats import parse_smf,pod2_members,member_bytes,safe_name,decode_classic_tiff

FT=0.3048
# Source +X right (TRK rtire x > 0), +Y up, +Z front, feet -> normalized +X right, +Y up, -Z front, metres.
NORMALIZATION=[FT,0.,0.,0., 0.,FT,0.,0., 0.,0.,-FT,0., 0.,0.,0.,1.]
SLOTS={'FL_WHEEL':('faxle.ltire','L'),'FR_WHEEL':('faxle.rtire','R'),'BL_WHEEL':('raxle.ltire','L'),'BR_WHEEL':('raxle.rtire','R')}
TRUCKS={'CFRT':'TRUCK/CFRT.TRK','JWR':'TRUCK/JWR.TRK','SMT':'TRUCK/SMT.TRK','WDRT':'TRUCK/WDRT.TRK'}
# Always-present body objects (stock shell, interior, exterior glass, mirrors, wipers, beds/covers/spares).
BASE={'AXLEF','AXLER','BODY','COCKPIT','GLASSE','MIRRORL','MIRRORR','WIPERLT','WIPERRT','UNDBODY','BEDCOVR','SPARE','SPARE2','BUMPERF','BUMPERR','CLADRT','BIKINI'}
# TRK stockPartList entry -> SMF objects it shows.
STOCK={'SKIDPLATES':('SKID',),'RACESKIDPLATES':('SKID',),'BUSHGUARD':('BUSHBAR',),'MUDFLAPS':('MUDFLPS',),
       'ROLLBAR':('ROLLBR1',),'FOGLIGHTS':('FOGB1','FOGB2','FOGB3','FOGB4'),'DRIVINGLIGHTS':('FOGR1','FOGR2','FOGR3','FOGR4')}
# Lens overlay quads (transparent flag) used as the MR brake draw; other Light* are light-pass sprites.
BRAKE={'LIGHTBL','LIGHTBR','LIGHTBC'}


def parse_trk(data:bytes)->dict:
    text=data.decode('latin-1');lines=[r.strip()for r in text.splitlines()if r.strip()]
    def get(key):
        hits=[i for i,r in enumerate(lines)if r==key]
        if len(hits)!=1:raise ValueError('missing/ambiguous TRK field '+key)
        return lines[hits[0]+1]
    if get('version')!='7':raise ValueError('unsupported TRK version')
    out={k:get(k)for k in('frontSuspType','rearSuspType','frontSuspSpringType','rearSuspSpringType','truckName','truckMake','truckModel','truckClass','truckModelBaseName','tireModelBaseName',
                          'truckWheelbase','truckFrontTrack','truckRearTrack','numStockParts','numColors')}
    n=int(out['numStockParts']);i=lines.index('stockPartList[]')if n else 0
    out['stock_parts']=lines[i+1:i+1+n]if n else[]
    out['wheel_positions']={s:[float(v)for v in get(s+'.static_bpos').split(',')]for s,_ in SLOTS.values()}
    out['raw_lines']=lines
    return out


# Every accessory object that can appear on Evo 2 trucks (full kit = all present ones).
ACCESSORIES={'SKID','BUSHBAR','MUDFLPS','ROLLBR1','ROLLBR2','SNORKEL','WINCH','RFRACK','RACK','STEPS','FFLARES','HSCOOP','VISOR','BUGSHLD',
             'FOGB1','FOGB2','FOGB3','FOGB4','FOGR1','FOGR2','FOGR3','FOGR4'}
KITS=('bare','stock','full')


def visible_objects(trk,kit='stock'):
    """bare = body only; stock = TRK stockPartList; full = every accessory in the model (Evo 2 upgrade shop)."""
    if kit not in KITS:raise ValueError('kit must be one of '+', '.join(KITS))
    vis=set(BASE)
    if kit=='stock':
        for part in trk['stock_parts']:vis.update(STOCK.get(part.upper(),()))
    elif kit=='full':vis|=ACCESSORIES
    return vis


def create_scene(truck_pod:Path,output:Path,truck:str,*,wheel_detail='16',suspension=True,kit='stock')->dict:
    pod_path=Path(truck_pod).absolute();uvs.unlinked(pod_path);protected=[pod_path.parent]
    output=Path(output).absolute();uvs.output_directory(output,protected)
    if output.exists():raise ValueError('Fresh source output required')
    pod=uvs.read_bounded(pod_path,512*1024*1024);entries={e.name.casefold():e for e in pod2_members(pod)}
    assets={};resources={};meshes=[];materials=[];textures=[];nodes=[];tex_ids={}
    def get(name):
        e=entries.get(safe_name(name).casefold())
        if e is None:raise ValueError('missing member '+name)
        blob=member_bytes(pod,e);key=e.name.casefold()
        if key not in resources:
            rel='original/'+safe_name(e.name);assets[rel]=blob
            resources[key]={'member':e.name,'offset':e.offset,'bytes':e.size,'sha256':uvs.sha(blob),'snapshot_path':rel}
        return resources[key],blob
    def texture(name):
        k=name.casefold()
        if k in tex_ids:return tex_ids[k]
        rec,blob=get('ART/'+safe_name(name));meta,rgba,samples,palette=decode_classic_tiff(blob)
        tid='texture-%03d'%len(textures);path='textures/%s.rgba'%tid;assets[path]=rgba
        meta['source_channels']['raw_samples_path']='textures/%s.samples'%tid;assets[meta['source_channels']['raw_samples_path']]=samples
        if palette:meta['source_channels']['palette_path']='textures/%s.palette'%tid;assets[meta['source_channels']['palette_path']]=palette
        textures.append({'id':tid,**meta,'rgba_path':path,'rgba_sha256':uvs.sha(rgba),'source':rec});tex_ids[k]=tid
        return tid
    def glass_texture(tid):
        # MR authoring (as the 4Runner pilot's 89/255): Evo2 TIFF carries no usable glass alpha, the
        # glass shares the body atlas, so the glass object gets its own copy at alpha 140.
        src=next(t for t in textures if t['id']==tid);rgba=bytearray(assets[src['rgba_path']])
        rgba[3::4]=bytes([140])*(len(rgba)//4);gid=tid+'-glass';path='textures/%s.rgba'%gid;assets[path]=bytes(rgba)
        textures.append({**{k:v for k,v in src.items()if k not in('id','rgba_path','rgba_sha256')},'id':gid,'rgba_path':path,'rgba_sha256':uvs.sha(bytes(rgba))})
        return gid
    def model(name,prefix,keep=None):
        rec,blob=get(name);decoded=parse_smf(blob);ids=[];hidden=[]
        for i,obj in enumerate(decoded['objects']):
            if keep is not None and obj['name'].upper()not in keep:hidden.append(obj['name']);continue
            mid='mat-%s-%s'%(prefix,obj['name'].lower())
            tid=texture(obj['texture'])
            if obj['name'].upper()=='GLASSE':tid=glass_texture(tid)
            materials.append({'id':mid,'diffuse_texture_id':tid,'raw_fields':obj['material_raw'],
                'object':obj['name'],'flags':{'transparent_raw':obj['material_raw'][3],'reflective_raw':obj['material_raw'][4]},
                'unsupported':['native lighting/reflection','native TIFF alpha policy'],'preview':{'opacity':1.,'policy':'source texture'}})
            frame=obj['vertices_by_frame'][0]
            meshes.append({'id':mid,'name':obj['name'],'positions':[v[:3]for v in frame],'normals':[v[3:6]for v in frame],
                'uvs':[v[6:8]for v in frame],'triangles':obj['faces'],'material_id':mid,
                'source':{'member':rec['member'],'member_sha256':rec['sha256'],'object_index':i,'source_visible':obj['visible']}})
            ids.append(mid)
        return ids,hidden
    catalog_name=TRUCKS.get(truck,truck);_,catalog=get(catalog_name);trk=parse_trk(catalog)
    keep=visible_objects(trk,kit)|BRAKE
    body_ids,hidden=model('MODELS/%s.SMF'%trk['truckModelBaseName'],'body',keep)
    wheels={}
    for side in('L','R'):
        wheels[side],_=model('MODELS/%s%s%s.SMF'%(trk['tireModelBaseName'],wheel_detail,side),'wheel'+side.lower())
    by_id={m['id']:m for m in meshes}
    xs=[p[0]for mid in wheels['R']for p in by_id[mid]['positions']];width=max(xs)-min(xs)
    susp_report=None
    if suspension:
        from .evo2_suspension import build
        rec,act=get('ART/SUSP.ACT');rec2,raw=get('ART/SUSP.RAW')
        rgba=bytearray()
        for i in raw[:64*64]:rgba+=bytes(act[3*i:3*i+3])+bytes([255])
        tid='texture-susp';assets['textures/%s.rgba'%tid]=bytes(rgba)
        textures.append({'id':tid,'width':64,'height':64,'rgba_path':'textures/%s.rgba'%tid,'rgba_sha256':uvs.sha(bytes(rgba)),
                         'source_channels':{'mode':'8-bit RAW + ACT palette','raw':rec2['member'],'palette':rec['member']},'source':rec2})
        groups=build(trk,{'front':width,'rear':width})
        for name,(P,N,T,U) in groups.items():
            mid='mat-susp-'+name
            materials.append({'id':mid,'diffuse_texture_id':tid,'raw_fields':[],'object':'SUSP_'+name.upper(),
                'flags':{'transparent_raw':'0','reflective_raw':'0'},'unsupported':['camera-facing ribbons rebuilt as tubes (static rest pose)'],
                'preview':{'opacity':1.,'policy':'SUSP.RAW'}})
            meshes.append({'id':mid,'name':'SUSP_'+name.upper(),'positions':P,'normals':N,'uvs':U,'triangles':T,'material_id':mid,
                'source':{'generated':'Evo 2 procedural suspension (evo2_suspension.py, 4x42.exe FUN_005fdad0/FUN_006006d0)',
                          'trk':{k:trk[k]for k in('frontSuspType','rearSuspType','frontSuspSpringType','rearSuspSpringType')},'tyre_width_ft':width}})
            body_ids.append(mid)
        susp_report={k:len(v[2])for k,v in groups.items()}
    nodes.append({'id':'body','name':'BODY','parent_id':None,'mesh_ids':body_ids,'visible':True,'source_visible':True,'role':'body',
        'local_transform':uvs.IDENTITY[:],'source_local_transform':None,'transform_evidence':'SMF objects share the body frame'})
    for slot,(rec,side) in SLOTS.items():
        p=trk['wheel_positions'][rec];m=uvs.IDENTITY[:];m[3],m[7],m[11]=p
        nodes.append({'id':slot.lower(),'name':slot,'parent_id':None,'mesh_ids':wheels[side],'visible':True,'source_visible':True,'role':'wheel',
            'local_transform':m,'source_local_transform':None,
            'transform_evidence':{'kind':'source_bytes','member':catalog_name,'record':rec+'.static_bpos','side_model':side}})
    fr,fl,rr,rl=(trk['wheel_positions'][s]for s in('faxle.rtire','faxle.ltire','raxle.rtire','raxle.ltire'))
    scene={'schema':uvs.SCHEMA,'metadata':{'adapter':'evo2-gc-truck/1','display_name':trk['truckName'],
            'implementation_sha256':{p.name:uvs.sha(p.read_bytes())for p in(Path(__file__),Path(__file__).with_name('evo2_formats.py'))}},
        'source':{'game':'4x4 Evolution 2 (GameCube, GE4E7D)','root':str(pod_path.parent),'catalog':catalog_name,
                  'pod':{'path':pod_path.name,'bytes':len(pod),'sha256':uvs.sha(pod)},'protected_roots':[str(p)for p in protected],
                  'resources':list(resources.values()),'catalog_original':{k:v for k,v in trk.items()if k!='raw_lines'}},
        'coordinate_system':{'source':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,1],'units':'ft'},
            'normalized':{'right_axis':[1,0,0],'up_axis':[0,1,0],'forward_axis':[0,0,-1],'units':'m'},'source_to_normalized':NORMALIZATION[:],
            'interpretation_status':'TRK tire signs/axle Z (same frame as the qualified PC 4Runner adapter)','evidence':['TRK static_bpos']},
        'meshes':meshes,'materials':materials,'textures':textures,'nodes':nodes,
        'measurements':{'wheelbase_static_m':(fr[2]-rr[2])*FT,'front_track_m':(fr[0]-fl[0])*FT,'rear_track_m':(rr[0]-rl[0])*FT,
                        'wheelbase_catalog_m':float(trk['truckWheelbase'])*FT},
        'selection':{'wheel_detail':wheel_detail,'visible_rule':'kit %s: BASE objects (+ TRK stock parts for stock, + all accessories for full) + rear lens quads as brake'%kit,'kit':kit,
                     'stock_parts':trk['stock_parts'],'hidden_objects':hidden},
        'unknown_semantics':[{'id':'native-rendering','status':'UNSUPPORTED','meaning':'Evo2 reflections, light passes and alpha are not reproduced'}]}
    result=uvs.save_scene(scene,output,assets,protected_roots=protected)
    return {**result,'truck':truck,'name':trk['truckName'],'hidden':hidden,'measurements':scene['measurements'],'suspension':susp_report}
