"""Hash-qualified Silver policy over the shared Universal Scene/MR authoring SDK.

No TC parser, native compiler or source repair lives here. All adjustments are
private MR authoring choices; the accepted neutral scene remains immutable.
"""
from __future__ import annotations
import json
import math
import shutil
from dataclasses import replace
from pathlib import Path

from . import universal_vehicle_scene as uvs
from .universal_scene_bridge import compile_scene
from .scene_dx_writer import write_scene_dx
from .source_garage_pilot import _admit_output, _copy_scene, _json, _renderer, _configure, ROOT

FAMILY = 'PDSilver'
NAME = 'Paris-Dakar Pajero Silver #271'
SCENE_SHA256 = '9d3edfe6b4a5187a44946784c6fb1f836eed1ec311c6f8c42f0bf388108342c9'
TC_SHA256 = 'fe5b111f88309fa8167d9df8a996a8d478c912a2a189126d5534bad3f14a82ae'
PANES = {'screenfront': list(range(22,30)), 'screenleft': list(range(30,34)), 'screenright': list(range(34,38))}
# Exact atlas rectangles, inset to red lenses. Repeated V is intentional in
# the original rear lamp UVs (0.988..1.992); never clamp the source UV array.
LENS_RECTS = ((11/64,3/64,52/64,19/64), (7/64,43/64,58/64,61/64))


def pilot_profile(scene_path):
    path=Path(scene_path); scene=uvs.load_scene(path)
    if uvs.sha(uvs.read_bounded(path,uvs.MAX_JSON_BYTES)) != SCENE_SHA256:
        raise ValueError('Silver requires the exact reviewed immutable source scene')
    if scene['source'].get('catalog')!='Data/PajeroSilver.tc' or scene['source'].get('container_sha256')!=TC_SHA256:
        raise ValueError('Silver source catalog/hash mismatch')
    materials={m['id']:{'mode':'alpha_blend' if m['id']=='r0001-mat-06' else 'opaque',
        'interpretation':'mr_authoring','role':'original diffuse; Win material partitioned before native states',
        'evidence':'Exact source mesh/material/texture association. Indexed RGBA preserved, including original glass alpha. MR blend is an explicit approximation; original blend/test threshold and reflections are not reproduced.'}
        for m in scene['materials']}
    fit=uvs.IDENTITY[:]; fit[3]=-.00113275; fit[7]=-.63896; fit[11]=-.0044
    hubs={'front_left':[1.622151/2,-.05,2.52778/2], 'front_right':[-1.622151/2,-.05,2.52778/2],
          'rear_left':[1.746406/2,-.05,-2.52778/2], 'rear_right':[-1.746406/2,-.05,-2.52778/2]}
    return {'schema':'universal-scene-mr-profile/1','source_scene_sha256':SCENE_SHA256,
        'normalized_to_mr':[-1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,-1.,0.,0.,0.,0.,1.],
        'authoring_transform':fit,
        'transform_evidence':'Source +X right/+Y up/+Z front; normalized mirrorZ; MR +X left/+Y up/+Z front. Author numeric 1 source unit=1 MR metre (source physical units unproven). Common datum X=-.00113275,Y=-.63896,Z=-.0044 rebases source attachmentY=.58896 to native Pajero Y=-RideHeight=-.05 and centers axles. Body/hub relationships retained, not gravity settlement or body lowering.',
        'body_node_ids':[n['id']for n in scene['nodes']if n.get('role')=='body' and n.get('visible') and n['mesh_ids']],
        'wheel_slots':dict(zip(('front_left','front_right','rear_left','rear_right'),('wheel-0','wheel-1','wheel-2','wheel-3'))),
        'canonical_wheel_slot':'front_right','materials':materials,'texture_row_policy':'preserve','uv_v_policy':'preserve',
        'hub_overrides':hubs,'hub_evidence':'MR symmetric axle representation; exact measured track and wheelbase. Source front/rear axle X centers differ by 0.0000005 source units; common origin leaves +/-0.00000025m residual removed explicitly. No vertical or fore/aft wheel fit.'}


def _merge(parts):
    from .topology_writer import DrawGeometry
    if not parts:raise ValueError('Empty semantic selection')
    vertices=[]; triangles=[]
    for part in parts:
        start=len(vertices);vertices.extend(part.geometry.vertices)
        triangles.extend(tuple(start+i for i in t)for t in part.geometry.triangles)
    return replace(parts[0],geometry=DrawGeometry(tuple(vertices),tuple(triangles)))


def semantic_parts(result):
    """Complete partition: headlights, exact panes, red lenses, ordinary body.

    Every lamp cut carries a barycentric ledger back to the eight original
    source triangles; all pane/headlight triangle IDs are immutable source IDs.
    """
    from .glass_authoring import subset
    from .semantic_aperture import partition, compose_ledger
    if result['report']['source_scene_sha256']!=SCENE_SHA256:raise ValueError('Unqualified Silver semantics')
    rows={r['mesh_id']:r['draw_index']for r in result['report']['body_draws']}
    original=list(result['body_parts']); glass_index=rows['r0001-mat-06'];lamp_index=rows['r0001-mat-01']
    glass=original[glass_index]; lamp=original[lamp_index]
    if len(glass.geometry.triangles)!=38 or len(lamp.geometry.triangles)!=8:raise ValueError('Silver material topology changed')
    parts=[];core=[]
    for i,part in enumerate(original):
        if i==lamp_index:continue
        if i==glass_index:
            parts.append(replace(part,geometry=subset(part.geometry,list(range(22)))))
        else:
            # Conservative shell bounds, no windows/wheels/effects. Source crew
            # shares the body atlas; no claim of an independently decoded rig.
            core.append(len(parts));parts.append(part)
    remaining=lamp.geometry
    parents=[{'source_triangle':i,'barycentric':[(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]}for i in range(8)]
    lenses=[];lens_ledger=[]
    for tile in range(3):
        for u0,v0,u1,v1 in LENS_RECTS:
            inside,outside,ledger=partition(remaining,range(len(remaining.triangles)),
                [(u0,v0+tile),(u1,v0+tile),(u1,v1+tile),(u0,v1+tile)],uv_layer=0)
            if inside.triangles:
                lenses.append(replace(lamp,geometry=inside));lens_ledger.extend(compose_ledger(ledger['inside'],parents))
            parents=compose_ledger(ledger['outside'],parents);remaining=outside
    if not remaining.triangles or not lenses:raise ValueError('Silver lamp partition is empty')
    parts.append(replace(lamp,geometry=remaining))
    panes={}
    for label,ids in PANES.items():
        panes[label]=len(parts);parts.append(replace(glass,geometry=subset(glass.geometry,ids)))
    brake_index=len(parts);parts.append(_merge(lenses))
    return parts,panes,brake_index,core,{'schema':'silver-native-semantics/1','source_scene_sha256':SCENE_SHA256,
        'headlight_source_mesh':'r0001-mat-06','headlight_source_triangles':list(range(22)),
        'pane_source_mesh':'r0001-mat-06','panes':PANES,'rear_window':'UNSUPPORTED: no qualified separate rear pane',
        'lamp_source_mesh':'r0001-mat-01','lamp_rectangles_uv':LENS_RECTS,'lamp_v_tiles':[0,1,2],
        'brake_source_triangle_ledger':lens_ledger,'ordinary_lamp_source_triangle_ledger':parents,
        'source_positions_moved':False,'boundary':'MR lens/damage authoring; no original game lighting/damage parity'}


def _enhance(assets,result,donor,output):
    from .addon_sdk.native_states import author_states
    from .addon_sdk.auto_features import procedural_cracks,lamp_textures
    from .dxt import parse_dxt_bytes
    parts,panes,lamp,core,semantics=semantic_parts(result)
    _json(output/'semantic-partition.json',semantics)
    lit,glow,_=lamp_textures(parse_dxt_bytes((assets/(parts[lamp].textures[0]+'.dxt')).read_bytes()))
    names=('mr-silver-stop-lit-tga','mr-silver-stop-glow-tga','mr-silver-cracks-tga')
    for name,raw in zip(names,(lit,glow,procedural_cracks())):(assets/(name+'.dxt')).write_bytes(raw)
    raw=write_scene_dx((donor/'car.dx').read_bytes(),parts)
    recipe={'source_sha256':uvs.sha(raw),
        'panes':[{'label':label,'source_draw':i,'triangles':list(range(len(parts[i].geometry.triangles))),
            'broken_uv_axes':[0,1]if label=='screenfront'else[2,1],'broken_texture':names[2]}for label,i in panes.items()],
        'brake':{'source_draw':lamp,'triangles':list(range(len(parts[lamp].geometry.triangles))),
            'lit_texture':names[0],'glow_texture':names[1],
            'evidence':'Exact rear lamp mesh, red lens atlas rectangles only, repeated V, barycentric ledger semantic-partition.json. Clear/orange areas and headlights excluded.'}}
    car,report=author_states(raw,recipe);(assets/'car.dx').write_bytes(car)
    complete=parts+result['complete_parts'][len(result['body_parts']):]
    (assets/'complete.dx').write_bytes(write_scene_dx((donor/'complete.dx').read_bytes(),complete))
    ordinary=[i for i in range(len(parts))if i not in {*panes.values(),lamp}]
    _json(output/'native-state-recipe.json',recipe)
    return {'schema':'silver-native-adaptations/1','native_states':report,'collision_core_draw_indices':[ordinary.index(i)for i in core],
        'glass':'Original indexed RGBA retained. Native front/left/right broken alternatives use authored crack texture. Rear damage unsupported. Source double/reflection flags not globally enabled.',
        'brake':'Only exact red lens UV masks; MR ON/OFF/glow is an authored adaptation.',
        'crew':'Original source static crew retained in body. No duplicate retail crew or invented source skeletal controls.',
        'suspension':'Common coordinate origin rebase only; retail Pajero .05 ride settings and solver retained. Original gravity settlement unqualified.',
        'reflections':'UNSUPPORTED source shader parity; diffuse Source Fidelity baseline, no new environment patches.',
        'gameplay':'NOT TESTED'}


def _physics(retail_sma):
    from .addon_sdk.physics_profile import MEMBERS
    from .addon_sdk.project import read_sma_member
    return {'profile_version':1,'donor_family':'Pajero','runtime_family':FAMILY,
        'source_sha256':{p:uvs.sha(read_sma_member(retail_sma,p))for p in MEMBERS},
        'overrides':{MEMBERS[0]:{'Dimensions/Length':4.094415,'Dimensions/Width':2.07965195,'Dimensions/Height':1.73084103,
            'Dimensions/WheelBase':2.52778,'Dimensions/TrackWidthFront':1.622151,'Dimensions/TrackWidthRear':1.746406,
            'Dimensions/WheelRadiusFront':.390497,'Dimensions/WheelRadiusRear':.390497}},
        'notes':'Independent clean retail Pajero family, measured source numerical dimensions at explicit 1 unit=1 MR metre authoring scale. Radius is source Description .390497; actual wheel radial bound .395454214 (~4.96mm larger). Retain stock mass1500, AWD, engine, tyre, spring/damper and RideHeight .05. Source mass2150/rest.46/options are not mapped to a different solver. Common model origin maps source attachmentY .58896 to MR hubY -.05; not source runtime suspension settlement. Owner gameplay qualification pending.'}


def create_pilot(scene_path,donor_dir,retail_sma,output,*,retail_root,base_roster,build=True,render_ui=None):
    path=Path(scene_path).absolute();donor=Path(donor_dir).absolute();retail_sma=Path(retail_sma).absolute();retail_root=Path(retail_root).absolute()
    profile=pilot_profile(path);scene=uvs.load_scene(path)
    if donor!=retail_root/'DataGx/Vehicles/Pajero':raise ValueError('Explicit clean retail Pajero donor required')
    output=_admit_output(output,scene,[path.parent,donor,retail_sma,retail_root])
    from .addon_sdk.project import _physics_family_overlays,read_sma_member
    from .addon_sdk.manifest import load_capabilities
    capabilities,_=load_capabilities(ROOT/'research/vehicles/sdk/capabilities/retail-2001.json')
    _physics_family_overlays(data_sma=retail_sma,retail_data_root=retail_root,capabilities=capabilities,donor_family='Pajero',runtime_family=FAMILY)
    for item in donor.iterdir():
        if item.is_file()and item.suffix.lower()in('.dx','.dxt'):
            uvs.unlinked(item)
            if item.read_bytes()!=read_sma_member(retail_sma,'DataGx/Vehicles/Pajero/'+item.name):raise ValueError('Donor differs from exact retail SMA: '+item.name)
    result=compile_scene(path,profile);output.mkdir(parents=True)
    copied=_copy_scene(path,output/'inputs/source-scene');_json(output/'source-profile.json',profile);_json(output/'conversion-report.json',result['report'])
    baseline=output/'source-baseline/assets';baseline.mkdir(parents=True)
    for name,raw in result['textures'].items():(baseline/name).write_bytes(raw)
    for name,parts in [('car.dx',result['body_parts']),('complete.dx',result['complete_parts']),('wheel.dx',result['wheel_parts'])]:
        (baseline/name).write_bytes(write_scene_dx((donor/name).read_bytes(),parts))
    candidate=output/'converted';shutil.copytree(baseline,candidate/'assets')
    adaptations=_enhance(candidate/'assets',result,donor,output);_json(output/'native-adaptations.json',adaptations)
    slots=('front_left','front_right','rear_left','rear_right')
    from .addon_sdk.wheel_orientation import orient_parts
    wheel_resources={}
    for i,slot in enumerate(slots):
        parts=result['wheel_parts_by_slot'][slot]
        if slot.endswith('left'):parts=orient_parts(parts,source_outward_x=1,target_outward_x=-1)
        name='wheel-source'+str(i)+'.dx'
        wheel_resources[name]=write_scene_dx((donor/'wheel.dx').read_bytes(),parts)
        (candidate/'assets'/name).write_bytes(wheel_resources[name])
    preview={'race_wheel_instances':[{'translation':result['report']['hubs'][slot]['derived_hub_mr'],'rotation_y':math.pi if slot.endswith('left')else 0.,'scale':[1.,1.,1.]}for slot in slots],
        'race_wheel_resources':['wheel-source'+str(i)+'.dx'for i in range(4)],'provenance':'Original source wheel mesh and side rotations; per-slot native Ypi compensation, explicit common datum only.'}
    _json(candidate/'assets/preview-profile.json',preview)
    _json(output/'identity.json',{'addon':{'name':NAME,'family':FAMILY,'manufacturer':'MITSUBISHI','model':'PAJERO SILVER'}})
    from .addon_sdk.import_project import prepare
    author=prepare(candidate,donor,output/'identity.json',output/'author',render_ui=render_ui or _renderer,source_format='Paris-Dakar Universal Vehicle Scene')
    spec=json.loads((author/'vehicle-project.json').read_text());source_folder=Path(spec['source_vehicle_dir'])
    if not source_folder.is_absolute():source_folder=(author/source_folder).resolve()
    resources=list(wheel_resources)
    for name,raw in wheel_resources.items():(source_folder/name).write_bytes(raw)
    physics=_physics(retail_sma)
    physics['collision_fit']={'source_sha256':uvs.sha((candidate/'assets/car.dx').read_bytes()),'core_draw_indices':adaptations['collision_core_draw_indices'],
        'padding_m':[0.,0.,0.],'evidence':'Conservative original opaque structural body/bumper/bonnet/backdoor bounds, excluding window/headlight/lamp/wheel/shadow draws. Source crew shares body draw; not an independently rigged collision selection. Affine fit of retail Pajero hull topology only.'}
    from .addon_sdk.physics_collision import fit_collision
    _,collision=fit_collision((candidate/'assets/car.dx').read_bytes(),physics['collision_fit']);_json(output/'collision-fit-report.json',collision);_json(author/'physics-profile.json',physics)
    addon=json.loads((author/'addon.json').read_text());addon['audio']['stock_audio_profile_id']=1;addon['assets']['required_roles'].extend(resources)
    addon['results']['display_name']='PAJERO SILVER 271'
    addon['description']='Private owner-local Paris-Dakar Silver #271 source reconstruction. Independent retail MR Pajero physics/audio; measured dimensions and explicit common coordinate origin. Authored MR glass/brake/shadow features, source static crew. No original renderer, source audio, prerelease MR geometry identity or gameplay parity claim.'
    _json(author/'addon.json',addon)
    from .workshop.service import WorkshopProject
    workshop=WorkshopProject.create(author,output/'workshop',kind='addon',car_id=29)
    workshop.data['universal_source']={'scene_path':str(copied),'scene_sha256':SCENE_SHA256,'manifest_sha256':uvs.sha((copied.parent/'manifest.json').read_bytes()),
        'conversion_report':str(output/'conversion-report.json'),'conversion_report_sha256':uvs.sha((output/'conversion-report.json').read_bytes()),'adapter':'paris-dakar-source/1','baseline':'Source Fidelity'}
    workshop.data['source_baseline']={'assets':str(baseline),'sha256':{p.name:uvs.sha(p.read_bytes())for p in baseline.iterdir()if p.is_file()},'native_adaptations':str(output/'native-adaptations.json')}
    workshop.save();_configure(workshop,Path(base_roster),output,retail_sma,retail_root,runtime_family=FAMILY)
    workshop.camera_reset_original();workshop.camera_mode_update(2,{})
    workshop.marker_update([.65,.68,.72]);workshop.shadow_update('auto');framing=workshop.frontend_auto_frame();workshop.frontend_update(framing)
    report={'schema':'silver-native-pilot/1','status':'PASS_AUTHORING_GAMEPLAY_PENDING','output':str(output),'author':str(author),'workshop':str(workshop.root),
        'source_scene':str(copied),'source_scene_sha256':SCENE_SHA256,'frontend_auto_frame':framing,'roster_limit':30,'gameplay':'NOT TESTED','owner_approval':'PENDING'}
    if build:report['build']=workshop.build(output/'builds/source-fidelity',sdk_root=ROOT)
    workshop.verify_inputs();_json(output/'pilot-report.json',report)
    return report
