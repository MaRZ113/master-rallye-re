"""One explicitly qualified Evo2 scene, authored through the common MR SDK.

The generic scene bridge owns geometry conversion. This service chooses the
reviewed 4Runner/Terrano policy, records every adaptation, and builds an isolated
alternative using the existing author/Workshop/roster compilers.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil
import sys

from . import universal_vehicle_scene as uvs
from .universal_scene_bridge import compile_scene
from .scene_dx_writer import write_scene_dx

ROOT=Path(__file__).resolve().parents[2]
FAMILY='Evo2FourRunner'
NAME='Toyota 4Runner Stable'
CATALOG='TRUCK/T4RSR52.TRK'
POD_SHA256='5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41'
BODY_SHA256='a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e'


def _json(path,value):
    path.write_bytes(uvs.canonical(value))


def pilot_profile(scene_path):
    """Explicit, reviewable policy; no source-game or vehicle-name guessing."""
    path=Path(scene_path);scene=uvs.load_scene(path)
    if scene['source'].get('catalog')!=CATALOG:
        raise ValueError('Only the reviewed Evo2 Toyota 4Runner catalog is qualified')
    if scene['source'].get('pod',{}).get('sha256')!=POD_SHA256 or scene['meshes'][0]['source'].get('member_sha256')!=BODY_SHA256:
        raise ValueError('Only the exact reviewed Evo2 POD/body revision is qualified')
    if scene.get('selection',{}).get('wheel_detail')!='16' or scene.get('selection',{}).get('body_detail')!=2:
        raise ValueError('Reviewed pilot requires body detail2 and wheel detail16 scene')
    materials={}
    for row in scene['materials']:
        materials[row['id']]={'mode':'opaque',
            'interpretation':'mr_authoring','role':'source diffuse',
            'evidence':'Reviewed source object/UV association; unspecified TIFF sample is retained separately, never interpreted as source alpha. MR diffuse coverage is an explicit authoring choice.',
            'allow_alpha_flatten':True}
    basis=[-1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,-1.,0.,0.,0.,0.,1.]
    fit=uvs.IDENTITY[:];fit[11]=-.10668
    return {'schema':'universal-scene-mr-profile/1','source_scene_sha256':uvs.sha(uvs.read_bounded(path,uvs.MAX_JSON_BYTES)),
        'normalized_to_mr':basis,'authoring_transform':fit,
        'transform_evidence':'Source TRK/SMF +X right,+Y up,+Z front, feet; independently qualified native MR +X anatomical left,+Y up,+Z front. One common Z datum -0.10668m centers literal TRK axle hubs. No vertical fit or suspension settlement.',
        'body_node_ids':[n['id']for n in scene['nodes']if n.get('role')=='body' and n.get('visible') and n['mesh_ids']],
        'wheel_slots':{'front_right':'faxle.rtire','front_left':'faxle.ltire','rear_right':'raxle.rtire','rear_left':'raxle.ltire'},
        'canonical_wheel_slot':'front_right','materials':materials,
        'texture_row_policy':'preserve','uv_v_policy':'preserve'}


def _admit_output(output,scene,inputs):
    output=Path(output).absolute();uvs.unlinked(output)
    if output.exists():raise ValueError('Fresh pilot output required')
    roots=[Path(p).absolute()for p in scene['source'].get('protected_roots',[])]
    roots.extend(Path(p).absolute()for p in inputs)
    for protected in roots:
        uvs.unlinked(protected)
        if output==protected or output.is_relative_to(protected) or protected.is_relative_to(output):
            raise ValueError('Pilot output overlaps protected source/input: '+str(protected))
    return output


def _copy_scene(path,output):
    """Copy only the already validated, bounded content-addressed manifest."""
    uvs.load_scene(path)
    manifest=uvs.load_json(uvs.read_bounded(path.parent/'manifest.json',2*1024*1024))
    output.mkdir(parents=True)
    for name in [*manifest['files'],'manifest.json']:
        target=output/uvs.relative_name(name);target.parent.mkdir(parents=True,exist_ok=True)
        raw=uvs.read_bounded(path.parent/name,uvs.MAX_OUTPUT_BYTES)
        with target.open('xb')as stream:stream.write(raw)
    uvs.load_scene(output/'scene.json')
    return output/'scene.json'


def _renderer(assets,output):
    toolpath=str(ROOT/'tools')
    if toolpath not in sys.path:sys.path.insert(0,toolpath)
    from generate_vehicle_ui_previews import render_sources
    return render_sources(assets,output)


def _drive_type(scene):
    """Qualify the target axle torque split, independent of donor enum values."""
    lines=scene['source'].get('catalog_original',{}).get('raw_lines',[])
    values={}
    for index,row in enumerate(lines):
        if row.get('text')in('faxle.torque_pct','raxle.torque_pct'):
            if row['text']in values or index+1>=len(lines):raise ValueError('Ambiguous original axle torque records')
            values[row['text']]=lines[index+1].get('text')
    if values!={'faxle.torque_pct':'0.000000','raxle.torque_pct':'1.000000'}:
        raise ValueError('Reviewed source rear-drive axle torque split changed')
    # Existing MR Physics Studio qualifies0 AWD,1 RWD,2 FWD. This deliberately
    # does not map Evo2's unrelated drive_type enumeration into native MR.
    return 1


def _physics(retail_sma,scene):
    from .addon_sdk.project import read_sma_member
    from .addon_sdk.physics_profile import MEMBERS
    m=scene['measurements']
    # Radius is the source catalog wheel radius, not a visual bounding-box fit.
    radius=.388704
    return {'profile_version':1,'donor_family':'Terrano','runtime_family':FAMILY,
        'source_sha256':{n:uvs.sha(read_sma_member(retail_sma,n))for n in MEMBERS},
        'overrides':{MEMBERS[0]:{'Dimensions/WheelBase':m['wheelbase_static_metres'],
            'Dimensions/TrackWidthFront':m['front_track_metres'],'Dimensions/TrackWidthRear':m['rear_track_metres'],
            'Dimensions/WheelRadiusFront':radius,'Dimensions/WheelRadiusRear':radius,
            'Engine/DriveType':_drive_type(scene)}},
        'ride_height_reference_m':{'Front':.18288,'Rear':.18288},'ride_height_reference_binding':'registry_name',
        'notes':'Independent clean-retail Terrano SUV family. Measured TRK axle spans and documented TRK wheel radius override dimensions. Original TRUCK/T4RSR52.TRK lines91/92 faxle.torque_pct=0.000000 and93/94 raxle.torque_pct=1.000000 qualify rear-wheel drive: authored MR Engine/DriveType=1 via qualified Physics Studio0AWD/1RWD/2FWD mapping, not Evo2 drive_type enum. Per-family reference +0.18288m reproduces literal source hubY=-0.18288 by qualified native Y=-RideHeight (004407FC..004408C0), preserving menu/base Terrano ride setting0. Terrano mass, spring/damper/other engine/tyre values retained; Evo2 catalog mass and solver values have no qualified unit/solver mapping. No gameplay settlement claim.'}


def create_pilot(scene_path,donor_dir,retail_sma,output,*,retail_root=None,base_roster=None,profile=None,render_ui=None,build=True,visual_options=None,upper_brake_lamp=False):
    from .fourrunner_visual_kit import options
    visual_options=options(visual_options)
    if type(upper_brake_lamp)is not bool:raise ValueError('Upper brake lamp requires an explicit boolean')
    path=Path(scene_path).absolute();donor=Path(donor_dir).absolute();retail_sma=Path(retail_sma).absolute()
    retail_root=Path(retail_root or retail_sma.parent/'Data.sma_unpacked').absolute()
    scene=uvs.load_scene(path)
    if build and not base_roster:raise ValueError('Explicit existing qualified base_roster required to build isolated candidate')
    if donor.name!='Terrano' or donor!=retail_root/'DataGx/Vehicles/Terrano':
        raise ValueError('Pilot requires explicit clean retail Terrano resource folder')
    output=_admit_output(output,scene,[path.parent,donor,retail_sma,retail_root])
    from .addon_sdk.project import _physics_family_overlays
    from .addon_sdk.manifest import load_capabilities
    capabilities,_=load_capabilities(ROOT/'research/vehicles/sdk/capabilities/retail-2001.json')
    _physics_family_overlays(data_sma=retail_sma,retail_data_root=retail_root,capabilities=capabilities,donor_family='Terrano',runtime_family=FAMILY)
    # All donor templates are checked against exact retail SMA before writing.
    from .addon_sdk.project import read_sma_member
    for item in donor.iterdir():
        if item.is_file() and item.suffix.lower()in('.dx','.dxt'):
            uvs.unlinked(item)
            if item.read_bytes()!=read_sma_member(retail_sma,'DataGx/Vehicles/Terrano/'+item.name):
                raise ValueError('Donor loose resource differs from exact clean retail SMA: '+item.name)
    admitted=pilot_profile(path)
    selected=copy.deepcopy(profile)if profile else admitted
    result=compile_scene(path,selected)
    output.mkdir(parents=True)
    copied=_copy_scene(path,output/'inputs/source-scene')
    _json(output/'source-profile.json',selected)
    baseline=output/'source-baseline/assets';baseline.mkdir(parents=True)
    for name,raw in result['textures'].items():(baseline/name).write_bytes(raw)
    for role,parts in [('car.dx',result['body_parts']),('complete.dx',result['complete_parts']),('wheel.dx',result['wheel_parts'])]:
        (baseline/role).write_bytes(write_scene_dx((donor/role).read_bytes(),parts))
    for slot,parts in result['wheel_parts_by_slot'].items():
        (baseline/('wheel-'+slot+'.dx')).write_bytes(write_scene_dx((donor/'wheel.dx').read_bytes(),parts))
    _json(output/'conversion-report.json',result['report'])
    candidate=output/'converted';shutil.copytree(baseline,candidate/'assets')
    adaptations=_enhance(candidate/'assets',result,retail_root,output,retail_sma=retail_sma,visual_options=visual_options,upper_brake_lamp=upper_brake_lamp)
    _json(output/'native-adaptations.json',adaptations)
    display_name=NAME+' + Upper Brake Test'if upper_brake_lamp else NAME
    identity={'addon':{'name':display_name,'family':FAMILY,'manufacturer':'TOYOTA','model':'4RUNNER SR5'}}
    import math
    slots=('front_left','front_right','rear_left','rear_right')
    preview={'race_wheel_instances':[{'translation':result['report']['hubs'][slot]['derived_hub_mr'],
        'rotation_y':math.pi if slot.endswith('left')else 0.,'scale':[1.,1.,1.]}for slot in slots],
        'race_wheel_resources':['wheel-source'+str(i)+'.dx'for i in range(4)],
        'provenance':'Exact source4wheel hub-local geometry with original side-specific textures; native0/piY basis independently inverted perresource. Literal TRK unloaded hub translations, not settled physics.'}
    _json(candidate/'assets/preview-profile.json',preview)
    _json(output/'identity.json',identity)
    from .addon_sdk.import_project import prepare
    author=prepare(candidate,donor,output/'identity.json',output/'author',render_ui=render_ui or _renderer,source_format='Evo2 Universal Vehicle Scene')
    # Native order is front+X(left),front-X(right),rear+X(left),rear-X(right).
    # The original controller adds a proper Y half-turn at positive-X hubs;
    # undo it in those local resources so runtime restores the exact source.
    from .addon_sdk.wheel_orientation import orient_parts
    resources=[]
    for index,slot in enumerate(('front_left','front_right','rear_left','rear_right')):
        parts=result['wheel_parts_by_slot'][slot]
        if slot.endswith('left'):parts=orient_parts(parts,source_outward_x=1,target_outward_x=-1)
        raw=write_scene_dx((donor/'wheel.dx').read_bytes(),parts)
        spec=json.loads((author/'vehicle-project.json').read_text())
        source_folder=Path(spec['source_vehicle_dir'])
        if not source_folder.is_absolute():source_folder=(author/source_folder).resolve()
        target=source_folder/('wheel-source'+str(index)+'.dx');target.write_bytes(raw)
        resources.append({'name':target.name,'path':str(target),'sha256':uvs.sha(raw)})
    physics=_physics(retail_sma,scene)
    physics['collision_fit']={'source_sha256':uvs.sha((candidate/'assets/car.dx').read_bytes()),
        'core_draw_indices':adaptations['collision_core_draw_indices'],'padding_m':[0.,0.,0.],
        'evidence':'Explicit source Body structural shell, excluding windows/roof accessories/wheels/crew; affine fit of clean Terrano hull retains topology. Common source-to-MR and axle-centering Z datum already applied; no additional vertical shift or runtime contact qualification.'}
    from .addon_sdk.physics_collision import fit_collision
    _,collision_report=fit_collision((candidate/'assets/car.dx').read_bytes(),physics['collision_fit'])
    _json(output/'collision-fit-report.json',collision_report)
    _json(author/'physics-profile.json',physics)
    addon=json.loads((author/'addon.json').read_text());addon['audio']['stock_audio_profile_id']=7
    addon['assets']['required_roles'].extend(r['name']for r in resources)
    addon['results']['display_name']='TOYOTA 4RUNNER'
    addon['description']='Private Evo2 4Runner Source Fidelity; clean retail Terrano physics with measured axle/radius overrides and source torque-split-qualified MR rear-wheel drive, explicitly authored MR Navara audio profile7 and stock seated crew. Native material/damage/light approximations are recorded; source SMF material/animation semantics and D3D8 gameplay are not claimed equivalent.'
    _json(author/'addon.json',addon)
    from .workshop.service import WorkshopProject
    workshop=WorkshopProject.create(author,output/'workshop',kind='addon',car_id=29)
    workshop.data['universal_source']={'scene_path':str(copied),'scene_sha256':uvs.sha(copied.read_bytes()),
        'manifest_sha256':uvs.sha((copied.parent/'manifest.json').read_bytes()),'conversion_report':str(output/'conversion-report.json'),
        'conversion_report_sha256':uvs.sha((output/'conversion-report.json').read_bytes()),'adapter':'evo2-smf-pod2/1','baseline':'Source Fidelity'}
    workshop.data['source_baseline']={'assets':str(baseline),'sha256':{p.name:uvs.sha(p.read_bytes())for p in baseline.iterdir()if p.is_file()},'native_adaptations':str(output/'native-adaptations.json')}
    workshop.save()
    from .crew_authoring import qualify_converted_crew
    definitions={}
    for model in ('car.dx','complete.dx'):
        raw=(workshop.baseline/model).read_bytes()
        ledger={'outputs':{model:{'sha256':uvs.sha(raw)}},'conversion':{model:adaptations['crew']['records']}}
        definitions[model]=qualify_converted_crew(raw,ledger,model)
    workshop.register_crew_models(definitions)
    report={'status':'PASS_AUTHORING_GAMEPLAY_PENDING','variant':'Stable + Upper Brake Test'if upper_brake_lamp else '4Runner Stable','owner_approval':'PENDING_NEW_CANDIDATE_TEST','output':str(output),'author':str(author),'workshop':str(workshop.root),
        'source_scene':str(copied),'conversion_report':str(output/'conversion-report.json'),'native_adaptations':str(output/'native-adaptations.json'),
        'gameplay':'NOT TESTED','runtime_single_wheel_safe':False,'roster_limit':30}
    if base_roster:
        _configure(workshop,Path(base_roster),output,retail_sma,retail_root)
        workshop.camera_reset_original();workshop.camera_mode_update(2,{})
        workshop.marker_update([.12,.32,.56]);workshop.shadow_update('auto')
        framing=workshop.frontend_auto_frame();workshop.frontend_update(framing)
        report['frontend_auto_frame']=framing
        if build:report['build']=workshop.build(output/'builds/source-fidelity',sdk_root=ROOT)
    workshop.verify_inputs();_json(output/'pilot-report.json',report)
    return report


def _configure(workshop,base_roster,output,retail_sma,retail_root,*,runtime_family=FAMILY):
    from .addon_sdk.project import build_project
    config_path=base_roster/'roster-config.json'if base_roster.is_dir()else base_roster
    uvs.unlinked(config_path);config=json.loads(uvs.read_bounded(config_path,1024*1024))
    if len([r for r in config['projects']if r['physical_id']==29])!=1:raise ValueError('Base roster requires exactly one existing alternative CarID29')
    author=Path(workshop.data['source']);author_build=output/'configuration-author-build'
    build_project(author,ROOT/'research/vehicles/sdk/capabilities/retail-2001.json',author_build,retail_data_sma=retail_sma,retail_data_root=retail_root)
    for row in config['projects']:
        if row['physical_id']==29:row.update(project=str(author),build=str(author_build))
    source=json.loads((author/'vehicle-project.json').read_text())['source_vehicle_dir'];source=Path(source)
    if not source.is_absolute():source=(author/source).resolve()
    config['wheel_profiles']=[p for p in config.get('wheel_profiles',[])if p['runtime_family']!=runtime_family]+[{
        'runtime_family':runtime_family,'resource_keys':['Vehicles/'+runtime_family+'/wheel-source'+str(i)for i in range(4)],
        'resource_sha256':[uvs.sha((source/('wheel-source'+str(i)+'.dx')).read_bytes())for i in range(4)]}]
    # Only this alternative identity is rebound; original config remains untouched.
    roster=output/'roster';roster.mkdir();_json(roster/'roster-config.json',config)
    workshop.configure_build({'roster_candidate':str(roster),'retail_sma':str(retail_sma),'retail_root':str(retail_root)})


def _enhance(assets,result,retail_root,output,*,retail_sma=None,visual_options=None,upper_brake_lamp=False):
    """Explicit native adaptations, always separate from SourceBaseline."""
    from dataclasses import replace
    from .addon_sdk.crew import fit_crew
    from .addon_sdk.auto_features import procedural_cracks
    from .addon_sdk.native_states import author_states
    from .fourrunner_semantics import author_apertures
    parts,pane_indices,lamp_index,pane_records,semantic_report=author_apertures(result)
    _json(output/'semantic-apertures.json',semantic_report)
    from .fourrunner_upper_lamp import author
    parts,upper_report=author(parts,lamp_index,semantic_report,enabled=upper_brake_lamp)
    _json(output/'upper-brake-lamp.json',upper_report)
    from .fourrunner_visual_kit import apply
    parts,core_indices,visual_report=apply(parts,result,retail_root,retail_sma,assets,visual_options,semantic_report)
    _json(output/'mr-visual-kit.json',visual_report)
    ordinary=[i for i in range(len(parts))if i not in {*pane_indices.values(),lamp_index}]
    native_core_indices=[ordinary.index(i)for i in core_indices]
    # Static MR crew adaptation uses the original Navara selected seated pair.
    # The source head marker is a reference, not proof of a skeletal mapping.
    config=json.loads((ROOT/'src/master_rallye/addon_sdk/presets/navara_crew.json').read_text())
    for who,placement in config['placements']['race'].items():
        placement.update(lateral=(-.036056 if who=='driver'else -.043944),vertical=0.,longitudinal=-.10668,yaw_degrees=0.)
    crew,crew_records=fit_crew(retail_root/'DataGx/Vehicles/Navara',config,'race',assets)
    parts.extend(crew)
    donor=retail_root/'DataGx/Vehicles/Terrano'
    raw=write_scene_dx((donor/'car.dx').read_bytes(),parts)
    textures={p.name.lower():p.read_bytes()for p in assets.glob('*.dxt')}
    recipe={'source_sha256':uvs.sha(raw)}
    # Explicit lens-only draw is independent of subsequent body partition IDs.
    # Generic texture generation is reused; geometry ownership is never inferred
    # from red corner samples after a topology edit.
    from .addon_sdk.auto_features import lamp_textures
    from .dxt import parse_dxt_bytes
    lit,glow,_=lamp_textures(parse_dxt_bytes(textures[parts[lamp_index].textures[0].lower()+'.dxt']))
    lit_name='mr-4runner-stop-lit-tga';glow_name='mr-4runner-stop-glow-tga'
    generated={lit_name+'.dxt':lit,glow_name+'.dxt':glow}
    recipe['brake']={'source_draw':lamp_index,'triangles':list(range(len(parts[lamp_index].geometry.triangles))),
        'lit_texture':lit_name,'glow_texture':glow_name,
        'evidence':'Explicit original rear lens atlas apertures clipped within exact source auxiliary footprint; see semantic-apertures.json barycentric source triangle ledger. No paint/bumper or clear reverse/indicator area is a brake surface.'}
    brake_report={'brake_triangles':len(recipe['brake']['triangles']),
        'evidence':[recipe['brake']['evidence']],'warnings':['MR brake adaptation; original Evo2 runtime light behavior not recovered.']}
    # Each pane contains BOTH original face layers where supplied; no roof or
    # lower door sheet is made translucent, and no absent rear pane is invented.
    crack='mr-4runner-authored-cracks-tga';(assets/(crack+'.dxt')).write_bytes(procedural_cracks())
    recipe['panes']=[{'label':label,'source_draw':index,'triangles':list(range(len(parts[index].geometry.triangles))),
        'broken_uv_axes':[0,1]if label=='screenfront'else[2,1],'broken_texture':crack}for label,index in pane_indices.items()]
    for name,blob in generated.items():(assets/name).write_bytes(blob)
    car,native_report=author_states(raw,recipe);(assets/'car.dx').write_bytes(car)
    # Frontend complete model retains exactly four distinct source wheel
    # instances and the same pane/crew authoring in its intact presentation.
    wheel_start=len(result['body_parts'])
    complete=parts+result['complete_parts'][wheel_start:]
    (assets/'complete.dx').write_bytes(write_scene_dx((donor/'complete.dx').read_bytes(),complete))
    _json(output/'native-state-recipe.json',recipe)
    _json(output/'crew-recipe.json',config)
    return {'status':'PASS_NATIVE_AUTHORING_GAMEPLAY_PENDING','source_baseline_unchanged':True,
        'upper_brake_lamp':upper_report,
        'collision_core_draw_indices':native_core_indices,'visual_kit':visual_report,
        'materials':'Explicit source-atlas apertures partition side glass from opaque rubber/door/pillars. Accepted windshield unchanged. Vertex alpha89/255 is authored MR glass, never source TIFF alpha.',
        'pane_source_triangle_ids':pane_records,'semantic_apertures':str(output/'semantic-apertures.json'),'glass_damage':native_report,
        'glass_boundary':'Source GlassI/E have no rear vehicle window; rear damage UNSUPPORTED pending Body atlas/geometry qualification. Side selection is a bounded MR pane interpretation, not source damage semantics.',
        'brake':brake_report,'brake_boundary':'Lens-only convex UV masks within original rear auxiliary footprint, with barycentric source IDs in semantic-apertures.json. Headlights, bumper, paint and clear indicator/reverse areas excluded.',
        'crew':{'source':'clean retail Navara','source_sha256':config['source_sha256'],'records':crew_records,'placement':'Explicit rigid MR seated pair adaptation; source driver head marker used only as lateral reference. No source crew/animation claim.'},
        'wheel':'Four exact side-specific native wheel resources retained; per-wheel rolling selector qualification pending.',
        'gameplay':'NOT TESTED'}
