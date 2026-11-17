"""TXR3 (PS2) vehicle -> MR Classic native project, same policy as the Dakar 2 pilot.

Owner policy (2026-11-11/13): source geometry and diffuse textures, stock MR materials
by semantic role, donor physics with measured dimensions. TXR3 has no wheels in the car
container, so the retail donor wheels are used (MR authoring, recorded in the scene).
"""
from __future__ import annotations
import json,math
from dataclasses import replace
from pathlib import Path
from . import universal_vehicle_scene as uvs
from .universal_scene_bridge import compile_scene
from .scene_dx_writer import write_scene_dx
from .topology_writer import DrawGeometry
from .source_garage_pilot import ROOT,_admit_output,_copy_scene,_json,_renderer
from .dakar2_classic_pilot import (BASIS,RIDE_HEIGHT,MR_MATERIALS,MATERIAL_FAMILY,SLOTS,adapt,axle_fit,symmetric_hubs,
                                   _physics,_bounds,_wheel_radius,_merge,orient)

WHEEL_NODES={'front_left':'fl_wheel','front_right':'fr_wheel','rear_left':'bl_wheel','rear_right':'br_wheel'}
DONOR_WHEEL_ROLES={'pstread-tga':'tyre','pswheel64-tga':'tyre','pswheel643-tga':'tyre','pswheel64_2-tga':'chrome','pwheelrim-tga':'chrome'}
VEHICLES={
    'VEHICROSS':{'family':'VehiCROSS','name':'Isuzu VehiCROSS (TXR3)','manufacturer':'ISUZU','model':'VEHICROSS',
        'results':'ISUZU VEHICROSS','donor':'Pajero','audio':1,'class':'T1',
        # TXR3 TIM index -> role (textured materials)
        'textures':{0:'paint',1:'paint',9:'paint',35:'paint',11:'trim',36:'trim',38:'trim',42:'trim',27:'trim',
                    29:'trim',30:'trim',31:'trim',32:'trim',33:'trim',34:'trim',28:'chrome',
                    19:'lamp',26:'lamp',23:'lamp',12:'lamp',13:'lamp',2:'lamp',37:'lamp',52:'lamp',46:'lamp',
                    43:'brake',39:'brake'},
        'alpha_test_textures':{1},
        # material record index -> role, wins over the TIM map (TIM 0 at diffuse 0.5 = unpainted lower cladding,
        # TIM 9 at 0.5 = hood scoop insert)
        'materials':{0:'trim',10:'trim',43:'trim'},
        # TIM 26 headlight lens overlay: blend flag + graded alpha in TXR3; opaque it paints the lamps white.
        'alpha_blend_materials':{59},
        # untextured material record index -> role
        'solid':{1:'glass',3:'trim',6:'trim',7:'trim',5:'interior',8:'interior',16:'interior',35:'interior',
                 23:'trim',24:'trim',26:'trim',28:'trim',30:'trim',32:'trim',37:'trim',39:'trim',55:'trim',60:'trim'},
        'glass_material':1,
    },
}


def _roles(scene,spec):
    roles={}
    for m in scene['materials']:
        key=m['id']
        if spec.get('role_fn'):
            role=spec['role_fn'](m)
        elif key.startswith('mat-'):
            raw=m['raw_fields'][0];idx=int(key[4:])
            if idx in spec.get('materials',{}):
                role=spec['materials'][idx]
            elif raw['textured']:
                tex=int(m['diffuse_texture_id'].split('-')[1]);role=spec['textures'].get(tex)
            else:
                role=spec['solid'].get(idx)
            if role is None:raise ValueError('no MR role for '+spec.get('label','TXR3')+' material %s (%s)'%(key,m['diffuse_texture_id']))
        else:
            role=DONOR_WHEEL_ROLES[m['raw_fields'][0]['donor_texture']]
        roles[key]=role
    return roles


def pilot_profile(scene_path,spec,fit=None):
    path=Path(scene_path);scene=uvs.load_scene(path);roles=_roles(scene,spec)
    materials={}
    for key,role in roles.items():
        mr_role='lamp'if role=='brake'else role
        rule={'interpretation':'mr_authoring','role':'MR Classic '+mr_role,
              'evidence':spec.get('label','TXR3')+' diffuse texture/colour with the stock MR '+mr_role+' material (owner policy); source GPU state not reproduced.'}
        m=next(x for x in scene['materials']if x['id']==key)
        tex=m['diffuse_texture_id']
        if role=='glass'or key in{'mat-%02d'%k for k in spec.get('alpha_blend_materials',())}:rule['mode']='alpha_blend'
        elif tex.startswith('tim-')and int(tex[4:7])in spec.get('alpha_test_textures',()):rule.update(mode='alpha_test',alpha_ref=100)
        elif role=='chrome'and key.endswith(('d03','d04')):rule.update(mode='alpha_test',alpha_ref=100)
        else:rule.update(mode='opaque',allow_alpha_flatten=True)
        materials[key]=rule
    from .scene_semantics import features
    used={mid for n in scene['nodes']for mid in n['mesh_ids']}
    policy={row['id']:{'disposition':'mr_classic_material','evidence':'Owner policy: source geometry and diffuse textures with stock MR materials.',
                       'impact':spec.get('label','TXR3')+' '+row['kind']+' replaced by the MR role material.'}for row in features(scene,used)}
    profile={'schema':'universal-scene-mr-profile/1','source_scene_sha256':uvs.sha(uvs.read_bounded(path,uvs.MAX_JSON_BYTES)),
             'normalized_to_mr':BASIS,'authoring_transform':fit or uvs.IDENTITY[:],
             'transform_evidence':'Normalized +X right/+Y up/-Z front -> MR +X left/+Y up/+Z front. Body scaled to the donor wheelbase; axles centred, mean hub at Y=-RideHeight.',
             'body_node_ids':['body'],'wheel_slots':dict(WHEEL_NODES),'canonical_wheel_slot':'front_right','materials':materials,
             'texture_row_policy':'preserve','uv_v_policy':'preserve','source_feature_policy':policy}
    return profile,roles


def _scaled_fit(fit,scale):
    out=fit[:]
    for r in range(3):out[5*r]=scale
    return out


def _split_glass(part):
    """MR frame: +Z front, +X vehicle left.

    A pane is a side window only when its face normal is clearly lateral (|nx| > 1.25 |nz|) and it lies away from the
    centre line (|x| > 0.45 of the glass half width); everything else is windscreen or rear window, split at the
    middle of the glass Z range. The old rule (front = within .55 m of the foremost glass point, rear = within .35 m
    of the rearmost) put the upper rear window and the outer windscreen of slanted RCX glass into the side panes, so
    those triangles cracked with the wrong pane (owner 2026-11-16; Quattro: a 0.17 m2 rear triangle was 'left')."""
    from .glass_authoring import subset
    g=part.geometry;P=[v.position for v in g.vertices]
    zs=[p[2]for p in P];zmid=(max(zs)+min(zs))/2;xhalf=max(abs(p[0])for p in P)or 1.
    bins={'screenfront':[],'screenrear':[],'screenleft':[],'screenright':[]}
    for i,t in enumerate(g.triangles):
        a,b,c=(P[k]for k in t);c3=[(a[j]+b[j]+c[j])/3 for j in range(3)]
        u=[b[j]-a[j]for j in range(3)];w=[c[j]-a[j]for j in range(3)]
        n=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]]
        if not any(n):                           # degenerate: fall back to the vertex normals
            n=[sum(g.vertices[k].normal[j]for k in t)for j in range(3)]
        if abs(n[0])>1.25*abs(n[2])and abs(c3[0])>.45*xhalf:bins['screenleft'if c3[0]>0 else'screenright'].append(i)
        else:bins['screenfront'if c3[2]>zmid else'screenrear'].append(i)
    return {k:replace(part,geometry=subset(g,v))for k,v in bins.items()if v}


def create_pilot(scene_path,vehicle,retail_sma,retail_root,output,*,render_ui=None,car_id=29):
    from .addon_sdk.project import _physics_family_overlays,read_sma_member
    from .addon_sdk.manifest import load_capabilities
    from .addon_sdk.native_states import author_states
    from .addon_sdk.auto_features import procedural_cracks,lamp_textures
    from .addon_sdk.wheel_orientation import orient_parts
    from .addon_sdk.import_project import prepare
    from .dxt import parse_dxt_bytes
    spec=VEHICLES[vehicle];family=spec['family'];L=spec.get('label','TXR3')
    path=Path(scene_path).absolute();retail_sma=Path(retail_sma).absolute();retail_root=Path(retail_root).absolute()
    donor=retail_root/'DataGx/Vehicles'/spec['donor'];scene=uvs.load_scene(path)
    output=_admit_output(output,scene,[path.parent,donor,retail_sma,retail_root])
    capabilities,_=load_capabilities(ROOT/'research/vehicles/sdk/capabilities/retail-2001.json')
    _physics_family_overlays(data_sma=retail_sma,retail_data_root=retail_root,capabilities=capabilities,donor_family=spec['donor'],runtime_family=family)
    for item in donor.iterdir():
        if item.is_file()and item.suffix.lower()in('.dx','.dxt'):
            if item.read_bytes()!=read_sma_member(retail_sma,f"DataGx/Vehicles/{spec['donor']}/{item.name}"):
                raise ValueError('donor differs from clean retail SMA: '+item.name)
    from .gt_auto_profile import donor_geometry
    g=donor_geometry(donor)
    wheels={n['name']:n['local_transform']for n in scene['nodes']if n['role']=='wheel'}
    ax=spec.get('long_axis',3);wb=abs(wheels['FL_WHEEL'][ax]-wheels['BL_WHEEL'][ax]);scale=1. if spec.get('keep_source_scale')else g['wheelbase']/wb
    probe,roles=pilot_profile(path,spec,_scaled_fit(uvs.IDENTITY[:],scale))
    fit=_scaled_fit(axle_fit(compile_scene(path,probe)),scale)
    # axle_fit measured hubs that already include the scale; keep its translation, re-apply scale on the diagonal
    profile,roles=pilot_profile(path,spec,fit)
    first=compile_scene(path,profile)
    hubs,hub_report=symmetric_hubs(first)
    half=g['track_half']
    if not spec.get('source_track'):
        for s in SLOTS:hubs[s][0]=half if s.endswith('left')else -half
        hub_report.update(front_track=2*half,rear_track=2*half)
    profile.update(hub_overrides=hubs,hub_evidence='MR symmetric axles: '+L+' wheel centres scaled to the donor wheelbase; donor track width.')
    result=compile_scene(path,profile)
    output.mkdir(parents=True)
    copied=_copy_scene(path,output/'inputs/source-scene')
    _json(output/'source-profile.json',profile);_json(output/'conversion-report.json',result['report'])
    ledger=[];report=result['report']
    body=adapt(result['body_parts'],report['body_draws'],{k:('lamp'if v=='brake'else v)for k,v in roles.items()},ledger)
    nb=len(result['body_parts'])
    complete_wheels=adapt(result['complete_parts'][nb:],report['complete_draws'][nb:],roles,ledger)
    wheel_slots={s:adapt(result['wheel_parts_by_slot'][s],report['wheel_template_draws'][s],roles,ledger)for s in SLOTS}
    assets=output/'converted/assets';assets.mkdir(parents=True)
    for name,raw in result['textures'].items():(assets/name).write_bytes(raw)
    for env in sorted({e for e in MR_MATERIALS.values()if e}):
        (assets/(env+'.dxt')).write_bytes(read_sma_member(retail_sma,f'DataGx/Vehicles/{MATERIAL_FAMILY}/{env}.dxt'))
    # semantic body: ordinary draws, glass panes, one brake draw; core = paint draws
    ordinary=[];core=[];lamps=[];glass=None;heads=[]
    for part,rec in zip(body,report['body_draws']):
        role=roles[rec['material_id']]
        if rec['material_id']==(spec.get('glass_key')or'mat-%02d'%spec['glass_material']):glass=part
        elif role=='brake':lamps.append(part)
        else:
            if role=='paint':core.append(len(ordinary))
            if role=='lamp':heads.append(len(ordinary))
            ordinary.append(part)
    parts=list(ordinary);panes={}
    for label,p in _split_glass(glass).items():panes[label]=len(parts);parts.append(p)
    lamp=len(parts);parts.append(_merge(lamps))
    fam=family.lower();lens=[]
    if spec.get('lens_textures'):
        # Renderer lamp contract (retail_vehicle_contract 3): lens draws are found by texture name, so the head and
        # brake lamps get their own crops of the atlas named like retail lenses (headlight / brakelight).
        from .retail_vehicle_contract import lens_crop
        if heads:lens+=lens_crop(parts,heads,assets,f'{fam}-headlight-tga')
        lens+=lens_crop(parts,[lamp],assets,f'{fam}-brakelight-tga')
    lit,glow,_=lamp_textures(parse_dxt_bytes((assets/(parts[lamp].textures[0]+'.dxt')).read_bytes()))
    # Retail names of the brake ON layer and glow card: the renderer's night lamp code keys on
    # "breaklightson" (brake sections / brake glints) and "glow" (glow card); RCX set 1-3 used stop-lit/stop-glow.
    names=((f'{fam}-breaklightson-tga',f'{fam}-breaklightsonglow-tga',f'{fam}-cracks-tga')if spec.get('lens_textures')else
           (f'{fam}-stop-lit-tga',f'{fam}-stop-glow-tga',f'{fam}-cracks-tga'))
    # Cracked glass: the donor's own retail MR cracked windscreen (owner 2026-11-14: the procedural one looks artificial).
    cracked=donor/'windscreenc32-tga.dxt'
    for name,raw in zip(names,(lit,glow,cracked.read_bytes()if cracked.is_file()else procedural_cracks())):(assets/(name+'.dxt')).write_bytes(raw)
    raw=write_scene_dx((donor/'car.dx').read_bytes(),parts)
    recipe={'source_sha256':uvs.sha(raw),
            'panes':[{'label':label,'source_draw':i,'triangles':list(range(len(parts[i].geometry.triangles))),
                      'broken_uv_axes':[0,1]if label in('screenfront','screenrear')else[2,1],'broken_texture':names[2]}for label,i in panes.items()],
            'brake':{'source_draw':lamp,'triangles':list(range(len(parts[lamp].geometry.triangles))),'lit_texture':names[0],'glow_texture':names[1],
                     'evidence':spec.get('brake_evidence','TXR3 tail lamp (TIM 43) and roof high stop lamp (TIM 39) meshes.')}}
    car,states=author_states(raw,recipe)
    from .retail_vehicle_contract import prelight_dx
    prelight={}
    if spec.get('retail_prelight',True):
        # Retail vertex prelight (retail_vehicle_contract 1): converter colours were 255 -> too bright in the menu
        # and under the grime pass (owner 2026-11-17).
        car,prelight['car.dx']=prelight_dx(car)
    (assets/'car.dx').write_bytes(car)
    # Frontend frame: wheels on Y=0 like retail complete.dx (owner 2026-11-16: RCX cars sat low in Vehicle Select).
    from .complete_ground import lift_complete_dx
    complete=lift_complete_dx(write_scene_dx((donor/'complete.dx').read_bytes(),parts+complete_wheels))[0]
    if spec.get('retail_prelight',True):complete,prelight['complete.dx']=prelight_dx(complete)
    (assets/'complete.dx').write_bytes(complete)
    (assets/'wheel.dx').write_bytes(write_scene_dx((donor/'wheel.dx').read_bytes(),wheel_slots['front_right']))
    _json(output/'native-state-recipe.json',recipe)
    wheel_resources={}
    for i,slot in enumerate(SLOTS):
        sp=wheel_slots[slot]
        if slot.endswith('left'):sp=orient_parts(sp,source_outward_x=1,target_outward_x=-1)
        wheel_resources[f'wheel-source{i}.dx']=write_scene_dx((donor/'wheel.dx').read_bytes(),sp)
    for name,data in wheel_resources.items():(assets/name).write_bytes(data)
    _json(assets/'preview-profile.json',{'race_wheel_instances':[{'translation':hubs[s],'rotation_y':math.pi if s.endswith('left')else 0.,'scale':[1.,1.,1.]}for s in SLOTS],
        'race_wheel_resources':list(wheel_resources),'provenance':'Retail donor wheels on '+L+' hubs.'})
    lo,hi=_bounds(parts)
    dims={**hub_report,'length':hi[2]-lo[2],'width':hi[0]-lo[0],'height':hi[1]-lo[1],'wheel_radius':_wheel_radius(wheel_slots['front_right'])}
    # Hull ground clearance (retail_vehicle_contract 2): the donor hull is fitted to the paint draws, but its bottom is
    # kept at the donor's height above the tyre contact (hub Y = -RideHeight, minus the wheel radius). A hull on the
    # sills of a small-wheeled car sits lower than MaxBounce above the contact and catches the course BSP on every
    # compression (owner 2026-11-17: RCX cars snag on Clashin Darroch / Fire Rock where stock cars do not).
    from .retail_vehicle_contract import ride_heights,donor_clearance,contact_y,fit_collision_floor
    suspension=ride_heights(retail_sma,spec['donor'])
    clearance=donor_clearance((donor/'car.dx').read_bytes(),suspension,g['wheel_radius'])
    floor=contact_y(suspension,dims['wheel_radius'])+clearance
    _,hull=fit_collision_floor(car,core,floor)
    hull.update(donor_clearance_m=clearance,contact_y_m=contact_y(suspension,dims['wheel_radius']),suspension=suspension,
                rest_clearance_m=hull['hull_floor_y_m']-contact_y(suspension,dims['wheel_radius']),
                bump_margin_m=hull['hull_floor_y_m']-contact_y(suspension,dims['wheel_radius'])-max(suspension['FrontMaxBounce'],suspension['RearMaxBounce']),
                evidence=L+' body paint draws; affine fit of the retail donor hull with the donor hull ground clearance.')
    _json(output/'identity.json',{'addon':{'name':spec['name'],'family':family,'manufacturer':spec['manufacturer'],'model':spec['model']}})
    author=prepare(output/'converted',donor,output/'identity.json',output/'author',render_ui=render_ui or _renderer,
                   source_format=spec.get('source_format','TXR3 PS2 Universal Vehicle Scene'),vehicle_class=spec['class'])
    project=json.loads((author/'vehicle-project.json').read_text());folder=Path(project['source_vehicle_dir'])
    if not folder.is_absolute():folder=(author/folder).resolve()
    for name,data in wheel_resources.items():(folder/name).write_bytes(data)
    physics=_physics(retail_sma,family,spec['donor'],dims)
    physics['notes']=physics['notes'].replace('Dakar 2',L)
    physics['collision_fit']={'source_sha256':uvs.sha(car),'core_draw_indices':core,'padding_m':[0.,0.,0.],'floor_y_m':round(floor,5),
                              'evidence':L+' body paint draws; affine fit of the retail donor hull, floor = donor hull clearance above the tyre contact.'}
    from .addon_sdk.physics_collision import fit_collision
    _,collision=fit_collision(car,physics['collision_fit']);hull['sdk_fit']=collision
    physics['notes']+=(' Collision: donor hull fitted to the paint draws, floor at %.3f m (body %.3f m) = donor clearance %.3f m above the '
                       'tyre contact.'%(hull['hull_floor_y_m'],hull['body_floor_y_m'],clearance))
    _json(output/'collision-fit-report.json',hull);_json(author/'physics-profile.json',physics)
    addon=json.loads((author/'addon.json').read_text())
    addon['audio']['stock_audio_profile_id']=spec['audio'];addon['assets']['required_roles'].extend(wheel_resources)
    addon['results']['display_name']=spec['results']
    addon['description']=('Private '+spec.get('source_label','TXR3 (PS2)')+' '+spec['name']+' in MR Classic mode: original geometry and diffuse textures, stock Master Rallye '
                          'materials by semantic role, retail '+spec['donor']+' wheels and physics with measured dimensions. Gameplay not claimed.')
    _json(author/'addon.json',addon)
    from .workshop.service import WorkshopProject
    workshop=WorkshopProject.create(author,output/'workshop',kind='addon',car_id=car_id)
    workshop.data['universal_source']={'scene_path':str(copied),'scene_sha256':uvs.sha(copied.read_bytes()),
        'manifest_sha256':uvs.sha((copied.parent/'manifest.json').read_bytes()),'conversion_report':str(output/'conversion-report.json'),
        'conversion_report_sha256':uvs.sha((output/'conversion-report.json').read_bytes()),'adapter':spec.get('adapter_id','txr3-ps2/1'),'baseline':'MR Classic'}
    workshop.save()
    summary={'schema':'txr3-classic-pilot/1','vehicle':vehicle,'family':family,'output':str(output),'author':str(author),
             'workshop':str(workshop.root),'dimensions':dims,'body_scale':scale,'hub_fit':fit,'orientation_ledger':ledger,
             'native_states':states,'collision_core_draws':core,'hull':{k:hull[k]for k in('body_floor_y_m','hull_floor_y_m','rest_clearance_m','bump_margin_m')},
             'prelight':prelight,'lens_textures':lens,'panes':{k:len(parts[v].geometry.triangles)for k,v in panes.items()},
             'gameplay':'NOT TESTED'}
    _json(output/'pilot-report.json',summary)
    return summary
