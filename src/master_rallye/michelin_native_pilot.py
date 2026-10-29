"""One Michelin RAV4 authoring policy over the shared UVS/MR compiler and SDK.

Original scenes and damage targets stay immutable. MR scale, wheel basis, glass,
brake and donor physics are explicit reversible adaptations, not donor gameplay.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import replace
import copy
import json
import math
import shutil
from . import universal_vehicle_scene as u
from .universal_scene_bridge import compile_scene
from .scene_dx_writer import write_scene_dx
from .source_garage_pilot import ROOT,_json,_copy_scene,_admit_output,_renderer,_configure

FAMILY='MichelinRav4'
NAME='Michelin Toyota RAV4'
SCENES={'Car25A.PDO':'7ab8b1525fb078aee8fcd524a3d8b3816670668708102e9a4a36ec257074f27c',
        'Car06A.PDO':'3b229c81d304c520be0d6e3fa50d51d442c6c363d8b04d24a20a4d395701ba4e'}
SCALE=.38/.3400000035762787
TURN=[-1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,-1.,0.,0.,0.,0.,1.]
SLOTS=('front_left','front_right','rear_right','rear_left')
PANES={'screenfront':list(range(74,84)),'screenrear':list(range(84,90)),
       'screenleft':list(range(144,149))+list(range(154,158)),
       'screenright':list(range(149,154))+list(range(158,162))}
LAMP_IDS=list(range(57,63))+list(range(84,90))
LAMP_RECTS=((43,55,57,80),(198,55,212,80))


def qualified(path):
    path=Path(path);s=u.load_scene(path);catalog=s['source'].get('catalog')
    if catalog not in SCENES or u.sha(u.read_bounded(path,u.MAX_JSON_BYTES))!=SCENES[catalog]:
        raise ValueError('Exact accepted Michelin assembly required')
    return s


def profile(path):
    s=qualified(path);nodes={n['id']:n for n in s['nodes']}
    hubs=s['metadata']['wheel_selection']['hubs']
    zcentre=sum(h['initial_hub_xyz'][2]for h in hubs)/4
    fit=u.IDENTITY[:];fit[7]=-.05-hubs[0]['initial_hub_xyz'][1]*SCALE;fit[11]=-zcentre*SCALE
    for i in (0,5,10):fit[i]=SCALE
    mats={}
    for m in s['materials']:
        t=next(t for t in s['textures']if t['id']==m['diffuse_texture_id'])
        key=t['source_channels'].get('native_index0_coverage',False)
        mats[m['id']]={'mode':'alpha_test'if key else'opaque','interpretation':'mr_authoring',
            'role':'original indexed cutout'if key else'original opaque diffuse',
            'preserve_source_colors':True,
            'evidence':'Original geometry/UV/RGB retained. Native Michelin magenta/index0 binary coverage mapped to MR cutout; threshold128 is MR authoring, not recovered source alpha-test reference. Reflections disabled.'}
        if key:mats[m['id']]['alpha_ref']=128
    return {'schema':'universal-scene-mr-profile/1','source_scene_sha256':SCENES[s['source']['catalog']],
            'normalized_to_mr':TURN[:],'authoring_transform':fit,
            'transform_evidence':'Explicit uniform MR authoring scale: stock Forester radius0.38 MR metres / source wheel radius0.3400000036 source units. This does NOT identify source units as metres. Source+Z FRONT and +Y roof; source-X maps MR anatomical left via shared reflection/winding/normal conversion. Common Z axle centering and Y front hub=-0.05 MR datum preserve every relative body/hub position.',
            'body_node_ids':['original-xo'],'wheel_slots':dict(zip(SLOTS,('wheel-0','wheel-1','wheel-2','wheel-3'))),
            'canonical_wheel_slot':'front_right','wheel_local_transforms':{'front_left':TURN[:],'rear_left':TURN[:]},
            'wheel_transform_evidence':'Source rim material lies on +X (T0004 front x=.059986..125550, dark back x=-.125550). Proper Ypi rotates source-X hubs outward; source+X hubs retain identity. MR native left-side Ypi subsequently compensated in local resources. Original moving Michelin matrices remain WARN.',
            'materials':mats,'texture_row_policy':'preserve','uv_v_policy':'preserve'}


def semantic_parts(result):
    from .glass_authoring import subset
    if result['report']['source_scene_sha256']!=SCENES['Car25A.PDO']:raise ValueError('RAV4 topology only; Megane is not auto-promoted')
    parts=[];panes={};core=[];brake=None
    for record,part in zip(result['report']['body_draws'],result['body_parts']):
        mesh=record['mesh_id'];count=len(part.geometry.triangles)
        if mesh=='body-texture-000':
            if count!=162:raise ValueError('RAV4 untextured topology changed')
            selected={i for ids in PANES.values()for i in ids}
            parts.append(replace(part,geometry=subset(part.geometry,[i for i in range(count)if i not in selected])))
            for name,ids in PANES.items():
                g=subset(part.geometry,ids)
                # Explicit MR intact glass: original plane coordinates and gray RGB,
                # no added cabin boxes or changed door/pillar triangles.
                g=replace(g,vertices=tuple(replace(v,color=v.color[:3]+bytes([96]))for v in g.vertices))
                panes[name]=len(parts);parts.append(replace(part,geometry=g,alpha=True,alpha_test=False,environment=False))
        elif mesh=='body-texture-007':
            if count!=90:raise ValueError('RAV4 rear topology changed')
            core.append(len(parts));parts.append(replace(part,geometry=subset(part.geometry,[i for i in range(count)if i not in LAMP_IDS])))
            brake=len(parts);parts.append(replace(part,geometry=subset(part.geometry,LAMP_IDS)))
        else:
            if mesh in ('body-texture-004','body-texture-005','body-texture-006','body-texture-008','body-texture-009'):core.append(len(parts))
            parts.append(part)
    if len(panes)!=4 or brake is None:raise ValueError('Missing bounded native glass/lamp ownership')
    return parts,panes,brake,core


def lamp_maps(texture):
    """Reuse SDK lamp generator, retaining only bounded original red lens pixels."""
    from .addon_sdk.auto_features import lamp_textures,feed
    from .dxt import parse_dxt_bytes
    if (texture.width,texture.height)!=(256,128):raise ValueError('Pinned rear atlas dimensions changed')
    lit,glow,_=lamp_textures(texture);lit=bytearray(parse_dxt_bytes(lit).bgra);glow=bytearray(parse_dxt_bytes(glow).bgra)
    allowed=[]
    for y in range(texture.height):
        for x in range(texture.width):
            i=(y*texture.width+x)*4;b,g,r,a=texture.bgra[i:i+4]
            keep=any(x0<=x<x1 and y0<=y<y1 for x0,y0,x1,y1 in LAMP_RECTS)and r>g*1.3 and r>b*1.3 and r>30
            if keep:allowed.append(y*texture.width+x)
            else:lit[i:i+4]=texture.bgra[i:i+4];glow[i:i+4]=bytes(4)
    if not allowed:raise ValueError('No qualified red lens pixels')
    return feed(lit,texture.width,texture.height),feed(glow,texture.width,texture.height),allowed


def enhance(assets,result,donor,output):
    from .addon_sdk.auto_features import procedural_cracks
    from .addon_sdk.native_states import author_states
    from .dxt import parse_dxt_bytes
    parts,panes,lamp,core=semantic_parts(result)
    tex=parse_dxt_bytes((assets/(parts[lamp].textures[0]+'.dxt')).read_bytes())
    lit,glow,pixels=lamp_maps(tex)
    names=('mr-michelin-rav4-stop-lit-tga','mr-michelin-rav4-stop-glow-tga','mr-michelin-rav4-cracks-tga')
    for name,blob in zip(names,(lit,glow,procedural_cracks())):(assets/(name+'.dxt')).write_bytes(blob)
    raw=write_scene_dx((donor/'car.dx').read_bytes(),parts)
    recipe={'source_sha256':u.sha(raw),'panes':[{'label':name,'source_draw':i,'triangles':list(range(len(parts[i].geometry.triangles))),
        'broken_uv_axes':[0,1]if name in('screenfront','screenrear')else[2,1],'broken_texture':names[2]}for name,i in panes.items()],
        'brake':{'source_draw':lamp,'triangles':list(range(len(parts[lamp].geometry.triangles))),
                 'lit_texture':names[0],'glow_texture':names[1],
                 'evidence':'Only original rear-corner triangles57..62/84..89 and red texels in explicit lens rectangles; emblem, paint, reverse/indicator and headlights excluded. No enlarged glow geometry.'}}
    native,report=author_states(raw,recipe);(assets/'car.dx').write_bytes(native)
    (assets/'complete.dx').write_bytes(write_scene_dx((donor/'complete.dx').read_bytes(),parts+result['complete_parts'][len(result['body_parts']):]))
    _json(output/'native-state-recipe.json',recipe)
    ordinary=[i for i in range(len(parts))if i not in {*panes.values(),lamp}]
    semantic={'glass_mesh':'body-texture-000','panes':PANES,'source_glass_flags':0x30000,
              'rear_lamp_mesh':'body-texture-007','rear_lamp_triangles':LAMP_IDS,'lens_rectangles':LAMP_RECTS,
              'allowed_lit_pixels':pixels,'source_positions_moved':False}
    _json(output/'semantic-ownership.json',semantic)
    return {'native_states':report,'collision_core_draw_indices':[ordinary.index(i)for i in core],
            'glass':'Original bounded pane geometry only; MR alpha96, four existing zones, generated crack alternatives. Source glass renderer parity WARN.',
            'crew':'Original Michelin static helmet/body/cage retained. No second crew, steering wheel or black interior box.',
            'damage':'Stock MR deformation/controller mechanisms retained; no external Michelin morph target used as intact geometry or event mapping.',
            'reflections':'Disabled; complete original opaque material groups retained.',
            'audio':'Explicit stock Forester profile8, not Michelin recordings.', 'gameplay':'NOT TESTED'}


def physics(retail_sma,result):
    from .addon_sdk.physics_profile import MEMBERS
    from .addon_sdk.project import read_sma_member
    hubs=result['report']['hubs'];front=hubs['front_left']['derived_hub_mr'];rear=hubs['rear_left']['derived_hub_mr']
    positions=[v.position for p in result['body_parts']for v in p.geometry.vertices]
    bounds=[max(p[i]for p in positions)-min(p[i]for p in positions)for i in range(3)]
    overrides={'Dimensions/Length':bounds[2],'Dimensions/Width':bounds[0],'Dimensions/Height':bounds[1],
        'Dimensions/WheelBase':front[2]-rear[2],'Dimensions/TrackWidthFront':2*abs(front[0]),'Dimensions/TrackWidthRear':2*abs(rear[0]),
        'Dimensions/WheelRadiusFront':.38,'Dimensions/WheelRadiusRear':.38,
        'Suspension/Front/RideHeight':-front[1],'Suspension/Rear/RideHeight':-rear[1]}
    return {'profile_version':1,'donor_family':'Forester','runtime_family':FAMILY,
            'source_sha256':{p:u.sha(read_sma_member(retail_sma,p))for p in MEMBERS},'overrides':{MEMBERS[0]:overrides},
            'notes':'Independent stock Forester AWD compact-SUV baseline: retain stock1340kg, springs35500/32500, damping2100/2000, solver and travel. Uniform authoring scale derives from stock0.38m tyre radius; source units not metres. Common datum preserves relative body/hubs. Separate initial MR ride offsets reflect source front/rear hub Y difference, not recovered Michelin settlement. Owner tuning/gameplay pending.'}


def create(scene_path,donor_dir,retail_sma,output,*,retail_root,base_roster,build=True):
    path=Path(scene_path).absolute();scene=qualified(path)
    if scene['source']['catalog']!='Car25A.PDO':raise ValueError('Only RAV4 native pilot authorized')
    donor=Path(donor_dir).absolute();retail_root=Path(retail_root).absolute();retail_sma=Path(retail_sma).absolute()
    if donor!=retail_root/'DataGx/Vehicles/Forester':raise ValueError('Explicit clean retail Forester donor required')
    output=_admit_output(output,scene,[path.parent,Path(scene['source']['root']),donor,retail_root,retail_sma,Path(base_roster)])
    from .addon_sdk.project import read_sma_member
    for item in donor.iterdir():
        if item.is_file()and item.suffix.lower()in('.dx','.dxt'):
            if u.read_bounded(item,u.MAX_OUTPUT_BYTES)!=read_sma_member(retail_sma,'DataGx/Vehicles/Forester/'+item.name):raise ValueError('Donor differs from clean SMA')
    p=profile(path);result=compile_scene(path,p);output.mkdir(parents=True)
    copied=_copy_scene(path,output/'inputs/source-scene');_json(output/'source-profile.json',p);_json(output/'conversion-report.json',result['report'])
    baseline=output/'source-baseline/assets';baseline.mkdir(parents=True)
    for name,raw in result['textures'].items():(baseline/name).write_bytes(raw)
    for name,parts in [('car.dx',result['body_parts']),('complete.dx',result['complete_parts']),('wheel.dx',result['wheel_parts'])]:
        (baseline/name).write_bytes(write_scene_dx((donor/name).read_bytes(),parts))
    candidate=output/'converted';shutil.copytree(baseline,candidate/'assets')
    adaptations=enhance(candidate/'assets',result,donor,output);_json(output/'native-adaptations.json',adaptations)
    slots=('front_left','front_right','rear_left','rear_right');resources={}
    from .addon_sdk.wheel_orientation import orient_parts
    for i,slot in enumerate(slots):
        parts=result['wheel_parts_by_slot'][slot]
        if slot.endswith('left'):parts=orient_parts(parts,source_outward_x=1,target_outward_x=-1)
        name='wheel-source%d.dx'%i;resources[name]=write_scene_dx((donor/'wheel.dx').read_bytes(),parts)
        (candidate/'assets'/name).write_bytes(resources[name])
    _json(candidate/'assets/preview-profile.json',{'race_wheel_instances':[{'translation':result['report']['hubs'][slot]['derived_hub_mr'],'rotation_y':math.pi if slot.endswith('left')else 0.,'scale':[1.,1.,1.]}for slot in slots],
        'race_wheel_resources':list(resources),'provenance':'Original wheels; explicit source outward rotations and inverse MR0/piY local-resource compensation.'})
    _json(output/'identity.json',{'addon':{'name':NAME,'family':FAMILY,'manufacturer':'TOYOTA','model':'RAV4 MICHELIN'}})
    from .addon_sdk.import_project import prepare
    author=prepare(candidate,donor,output/'identity.json',output/'author',render_ui=_renderer,source_format='Michelin UVS v1')
    spec=json.loads((author/'vehicle-project.json').read_text());source=Path(spec['source_vehicle_dir'])
    if not source.is_absolute():source=(author/source).resolve()
    for name,raw in resources.items():(source/name).write_bytes(raw)
    phys=physics(retail_sma,result);phys['collision_fit']={'source_sha256':u.sha((candidate/'assets/car.dx').read_bytes()),
        'core_draw_indices':adaptations['collision_core_draw_indices'],'padding_m':[0.,0.,0.],
        'evidence':'Fit existing Forester collision hull topology to opaque structural shell, excluding source crew, panes, lamps and wheels; no new collision system.'}
    _json(author/'physics-profile.json',phys)
    addon=json.loads((author/'addon.json').read_text());addon['assets']['required_roles'].extend(resources)
    addon['audio']['stock_audio_profile_id']=8;addon['results']['display_name']='TOYOTA RAV4 MICHELIN'
    addon['description']='Private Michelin RAV4, authentic LOD0/UV/livery and static crew; original wheels with explicit MR orientation, Forester physics/audio adaptations. Source runtime parity and D3D8 gameplay pending.'
    _json(author/'addon.json',addon)
    from .workshop.service import WorkshopProject
    w=WorkshopProject.create(author,output/'workshop',kind='addon',car_id=29)
    w.data['universal_source']={'scene_path':str(copied),'scene_sha256':SCENES['Car25A.PDO'],'manifest_sha256':u.sha((copied.parent/'manifest.json').read_bytes()),
        'conversion_report':str(output/'conversion-report.json'),'conversion_report_sha256':u.sha((output/'conversion-report.json').read_bytes()),'adapter':'michelin-neutral/1','baseline':'Source Fidelity'}
    w.data['source_baseline']={'assets':str(baseline),'sha256':{p.name:u.sha(p.read_bytes())for p in baseline.iterdir()if p.is_file()},'native_adaptations':str(output/'native-adaptations.json')}
    w.save();_configure(w,Path(base_roster),output,retail_sma,retail_root,runtime_family=FAMILY)
    w.camera_reset_original();w.camera_mode_update(2,{});w.marker_update([.95,.78,.12]);w.shadow_update('auto')
    framing=w.frontend_auto_frame();w.frontend_update(framing)
    report={'schema':'michelin-native-pilot/1','status':'PASS_AUTHORING_GAMEPLAY_PENDING','output':str(output),'workshop':str(w.root),'author':str(author),
            'source_scene':str(copied),'frontend_auto_frame':framing,'gameplay':'NOT TESTED','owner_approval':'PENDING','roster_limit':30}
    if build:report['build']=w.build(output/'builds/source-fidelity',sdk_root=ROOT)
    w.verify_inputs();_json(output/'pilot-report.json',report);return report
