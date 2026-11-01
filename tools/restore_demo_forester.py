"""V-DEF1 orchestration of existing Heritage/Workshop/CMD authoring services.

Private original inputs are never modified. No native converter or new hook
implementation lives here. The 31st record remains an explicit owner test.
"""
from pathlib import Path
import argparse,hashlib,json,re,struct,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk import heritage_source as heritage
from master_rallye.addon_sdk.project import read_sma_member
from master_rallye.addon_sdk.physics_profile import MEMBERS
from master_rallye.addon_sdk.historical_physics import source_family_profile
from master_rallye.addon_sdk.auto_features import derive
from master_rallye.addon_sdk.ui_assets import parse_bank,fit_rgba
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.workshop.service import WorkshopProject
from master_rallye.universal_vehicle_scene import output_directory


def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def localized_records(raw,pointer):
    """Read original aligned category/index/string-pointer records, not code."""
    out=[]
    for hit in re.finditer(re.escape(struct.pack('<I',pointer)),raw):
        offset=hit.start()
        if offset>=8 and offset%4==0:
            category,index=struct.unpack_from('<2I',raw,offset-8)
            if category<256 and index<256:out.append({'file_offset':offset-8,'category':category,'index':index,'pointer':pointer})
    return out


def identity_evidence(demo,ps2):
    pc=(demo/'MRallye.exe').read_bytes();elf=ps2.read_bytes()
    if sha(pc)!='611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728':raise ValueError('Original 9.3.1 identity evidence is missing')
    if sha(elf)!='b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2':raise ValueError('Original PS2 identity evidence is missing')
    if elf[0x354ac8:0x354ac8+18]!=b'DARREN SUTHERLAND\0' or elf[0x3540f0:0x3540f0+9]!=b'FORESTER\0':raise ValueError('PS2 original string bytes differ')
    vehicle=localized_records(elf,0x4530f0);driver=localized_records(elf,0x453ac8)
    if len(vehicle)!=6 or len(driver)!=6 or any(r['category']!=52 or r['index']!=8 for r in vehicle)or any(r['category']!=57 or r['index']!=8 for r in driver):raise ValueError('PS2 localized vehicle/driver association differs')
    pc_name=localized_records(pc,0x66e068);pc_combined=localized_records(pc,0x66df5c)
    if len(pc_name)!=2 or any(r['category']!=52 or r['index']!=8 for r in pc_name):raise ValueError('Demo localized Forester binding differs')
    scene=demo/'DataScene/FrontendScreens/Wjd/VehicleSelect.xml';tree=ET.fromstring(scene.read_bytes())
    widgets=[e for e in tree.iter('Egg')if e.get('Name')=='T2_Car2']
    if len(widgets)!=1:raise ValueError('Demo Forester widget is ambiguous')
    values={n.get('Name'):n.get('Value')for n in widgets[0].iter('Value')}
    if values.get('en2d Image Bank Index')!='1' or values.get('X ID')!='1' or values.get('Y ID')!='1':raise ValueError('Demo Forester widget/frame binding differs')
    bankpath=demo/'DataGx/Frontend/VehicleSelect/carsheet.dxb';bank=parse_bank(bankpath.read_bytes());name=bank['names'][1]
    if name!='carsheet_001_000':raise ValueError('Demo artwork frame resource differs')
    return {'demo_exe_sha256':sha(pc),'ps2_elf_sha256':sha(elf),'demo_localized_model':pc_name,'demo_localized_combined':pc_combined,
            'ps2_localized_model':vehicle,'ps2_localized_driver':driver,'vehicle':'SUBARU FORESTER','driver':'DARREN SUTHERLAND',
            'widget':'T2_Car2','class_local_index':1,'original_id':8,'frame':1,'frame_texture':name,
            'scene_sha256':sha(scene.read_bytes()),'bank_sha256':sha(bankpath.read_bytes()),
            'boundary':'Original localized data records and XML/image-bank bindings; no PS2 instruction or runtime emulation claim. Driver attribution is PS2 evidence, not a newly found PC driver literal.'}


def prepare(demo,rebaked,retail_sma,ps2,roster_config,output,*,retail_corrections=False,mini_icon=None):
    output=output_directory(output,[demo,rebaked,retail_sma,ps2,roster_config])
    if not output.is_relative_to((ROOT/'.research-output').absolute()):raise ValueError('Private repository output required')
    output.mkdir(parents=True);identity=identity_evidence(demo,ps2);write(output/'identity-evidence.json',identity)
    original=demo/'DataGx/Vehicles/Forester'
    for n in ('car.gxm','wheel.gxm'):
        if (original/n).read_bytes()!=(rebaked/n).read_bytes():raise ValueError('Canonical source GXM changed: '+n)
    complete_sources=[original/n for n in ('complete.gxm','comlplete.gxm')if(original/n).is_file()]
    if len(complete_sources)!=1 or complete_sources[0].read_bytes()!=(rebaked/'complete.gxm').read_bytes():raise ValueError('Canonical complete GXM differs from original source (including shipped filename spelling)')
    expected={'car.dx':'fbe8d15af205a3cbe95773d5241372352729f7fbcef21e61386123209a80a423','complete.dx':'72a3b98f616d55e66e43bf0bbc2702bdb5ff464406ae7e14338cc3c4a5a4ee15'}
    for n,digest in expected.items():
        if sha((rebaked/n).read_bytes())!=digest:raise ValueError('Canonical audited rebake changed: '+n)
    from master_rallye.dx_revision_upgrade import validate_existing_rev135
    from master_rallye.demo_vehicle_audit import dx_evidence
    qualifications={}
    for n in ('car.dx','complete.dx','wheel.dx'):
        raw=(rebaked/n).read_bytes();validation=validate_existing_rev135(raw,n)
        fixed,count=heritage.repair_global_indices(raw,require_order_equivalence=True)
        a=dx_evidence(raw,n);b=dx_evidence(fixed,n)
        fingerprints=('surface_sha256','uv_surface_sha256','normal_color_surface_sha256','material_surface_sha256','draw_state_sha256','collision_sha256')
        if any(a[k]!=b[k]for k in fingerprints):raise ValueError('Cache-only repair changed a native source stream')
        qualifications[n]={'source_sha256':sha(raw),'authoring_sha256':sha(fixed),'cache_positions_changed':count,'input_validation':validation,'preserved_fingerprints':{k:a[k]for k in fingerprints}}
    write(output/'source-authoring-qualification.json',qualifications)
    pins={str(p):sha(p.read_bytes())for p in rebaked.iterdir()if p.is_file()}
    project=output/'author';heritage.create_author(demo,'Forester',project,name='Demo Forester 9.3.1',runtime_family='DefForester',
        physics_donor='Forester',stock_audio_profile_id=8,vehicle_class='T2',retail_sma=retail_sma,features=None,family_folder=rebaked)
    members={n:read_sma_member(retail_sma,n)for n in MEMBERS};source=(demo/'DataGame/vehicles.xml').read_bytes()
    physics,report=source_family_profile(source,members,source_family='Forester',donor_family='Forester',runtime_family='DefForester')
    if retail_corrections:
        # create_author already made an independent, unmodified retail clone.
        # Keep the historical profile as evidence only, never feed its tyre
        # coefficients to the corrected candidate's retail solver.
        write(output/'historical-physics-reference.json',{'profile':physics,'report':report})
        physics=json.loads((project/'physics-profile.json').read_text())
        report={'policy':'Exact independent retail Forester/WOOLDAND clone','source_sha256':physics['source_sha256'],'overrides':physics['overrides'],'owned_tyres':None,'owner_reason':'Demo physics/tyre wear is unsuitable for retail; owner requested retail defaults'}
    write(project/'physics-profile.json',physics);write(output/'physics-preservation.json',report)
    ev=project/'source-evidence';ev.mkdir();(ev/'demo-vehicles.xml').write_bytes(source)
    assets=project/'assets/source/Forester';textures={p.name.casefold():p.read_bytes()for p in assets.glob('*.dxt')}
    raw=(assets/'car.dx').read_bytes();states,extra,detail=derive(raw,textures,sidecar_text=(rebaked/'car.txt').read_text(),gxm_raw=(rebaked/'car.gxm').read_bytes())
    if detail['warnings']or detail['zones']!={'screenfront':6,'screenleft':5,'screenright':5}or detail['brake_triangles']!=12:raise ValueError('Canonical source feature ownership differs')
    feature=project/'native-features';feature.mkdir();donor=read_sma_member(retail_sma,'DataGx/Vehicles/Forester/car.dx');(feature/'technical-donor.dx').write_bytes(donor)
    extra['mr-auto-cracked-tga.dxt']=read_sma_member(retail_sma,'DataGx/Vehicles/Forester/windscreenc32-tga.dxt')
    aliases={}
    for stem in (('breaklightsonglow-tga','perspex-tga','breaklightson-tga')if retail_corrections else('breaklightsonglow-tga','perspex-tga')):
        blob=read_sma_member(retail_sma,'DataGx/Vehicles/Forester/'+stem+'.dxt');alias='mr-ref-'+sha(blob)[:10]+'-'+stem;aliases[stem]=alias;extra[alias+'.dxt']=blob
    additions={}
    for name,blob in extra.items():
        path=feature/name;path.write_bytes(blob);additions[name]={'path':str(path.absolute()),'sha256':sha(blob)}
    recipe={'version':1,'additional_textures':additions,'states':states,'evidence':'Exact Demo GXM/TXT pane/lamp ownership; retail WOOLDAND native blight glow topology/UV/material copied with independent measured uniform per-lens fitting. Rear pane absent; no body cutout.',
            'brake_glow_reference':{'path':str((feature/'technical-donor.dx').absolute()),'sha256':sha(donor),'texture_aliases':aliases}}
    if retail_corrections:recipe['brake_glow_reference']['include_on_core']=True
    write(feature/'recipe.json',recipe);audit=heritage.apply_features(project,feature/'recipe.json');write(output/'native-features.json',{'ownership':detail,'authoring':audit})
    if retail_corrections:
        from master_rallye.frontend_presentation import align_complete_rest_frame
        resources={n:(assets/n).read_bytes()for n in heritage.ROLES};reference={n:read_sma_member(retail_sma,'DataGx/Vehicles/Forester/'+n)for n in heritage.ROLES}
        aligned,framing=align_complete_rest_frame(resources,reference)
        (assets/'complete.dx').write_bytes(aligned);write(output/'frontend-frame.json',framing)
        provenance=json.loads((project/'heritage-import.json').read_text());provenance['frontend_frame']=framing;provenance['resource_pins']={p.name:sha(p.read_bytes())for p in assets.iterdir()if p.is_file()};write(project/'heritage-import.json',provenance)
    addon=json.loads((project/'addon.json').read_text());addon['frontend'].update(manufacturer='SUBARU',model='FORESTER',combined='SUBARU FORESTER',stats=[6,7,5,4]);addon['results']['display_name']='DARREN SUTHERLAND'
    addon['description']='Authentic Demo9.3.1 geometry/artwork/physical values; PS2-qualified Darren Sutherland; retail MR solver/glass/glow/audio adaptations. Independent experimental ID30.';write(project/'addon.json',addon)
    from PIL import Image
    icon=demo/('DataGx/Frontend/VehicleSelect/'+identity['frame_texture']+'.dxt');texture=parse_dxt_bytes(icon.read_bytes())
    rgba=Image.frombytes('RGBA',(texture.width,texture.height),texture.bgra,'raw','BGRA').transpose(Image.Transpose.FLIP_TOP_BOTTOM);rgba.save(project/'ui/vehicle_select_art.png')
    w,h,pixels=32,16,None;pixels=fit_rgba((rgba.width,rgba.height,rgba.tobytes()),w,h);Image.frombytes('RGBA',(w,h),pixels).save(project/'ui/smallcarsheet.png')
    ui=json.loads((project/'ui-assets.json').read_text())
    if retail_corrections:
        from master_rallye.dxt import decode_rgba_pixels
        if mini_icon is None:raise ValueError('Corrected candidate requires an explicit qualified Demo mini icon')
        mini=Path(mini_icon);mt=parse_dxt_bytes(mini.read_bytes())
        bank=mini.parent/'smallcarsheet.dxb';mb=parse_bank(bank.read_bytes())
        if mini.stem not in mb['names']:raise ValueError('Mini icon is not referenced by its original Demo bank')
        if (mt.width,mt.height)!=(32,16):raise ValueError('Original Demo mini icon dimensions differ')
        Image.frombytes('RGBA',(32,16),decode_rgba_pixels(mt)).save(project/'ui/smallcarsheet.png')
        ui['icons']['smallcarsheet']['presentation']='source-pixels-v1'
        identity['original_mini_icon']={'path':str(mini),'sha256':sha(mini.read_bytes()),'bank_sha256':sha(bank.read_bytes()),'frame':mb['names'].index(mini.stem),'association':'Original Demo9.10.0 smallcarsheet frame4, visually inspected pink Forester SIDE artwork. Demo9.3.1 frame1 is a separate 64x32 three-quarter icon, not selected. No claim of identical original registry IDs.'}
        addon['description']='Authentic Demo9.3.1 geometry/CarSheet, original Demo9.10.0 side mini icon, PS2-qualified Darren; independent retail Forester physics, native glass and complete donor ON core/halo. Frontend-only measured rest-frame rebase. ID30.';write(project/'addon.json',addon)
    for role in ('vehicle_select_art','smallcarsheet'):ui['icons'][role]['sha256']=sha((project/'ui'/(role+'.png')).read_bytes())
    write(project/'ui-assets.json',ui);identity['icon_source_sha256']=sha(icon.read_bytes());identity['results_icon']='Derived 32x16 fit of the authentic Demo CarSheet, not a recovered distinct Results frame';write(output/'identity-evidence.json',identity)
    if retail_corrections:
        identity['results_icon']='Authentic original Demo9.10.0 smallcarsheet frame4; exact RGBA, no menu image resize or tone adjustment';write(output/'identity-evidence.json',identity)
    config=json.loads(roster_config.read_text())
    if [r['physical_id']for r in config['projects']]!=[28,29]:raise ValueError('An existing 30-entry roster is required without replacing its projects')
    config.update(experimental_record_count=31);config['projects'].append({'project':str(project.absolute()),'build':str(output/'not-built'),'physical_id':30})
    plan=output/'runtime-plan';plan.mkdir();write(plan/'roster-config.json',config)
    workshop=WorkshopProject.create(project,output/'workshop',kind='addon');workshop.configure_build({'roster_candidate':str(plan.absolute()),'retail_sma':str(retail_sma.absolute()),'retail_root':str((retail_sma.parent/'Data.sma_unpacked').absolute())})
    result=workshop.build(output/'workshop/builds/first',sdk_root=ROOT,log=lambda s:print(s,flush=True))
    changed=[name for name,pin in pins.items()if sha(Path(name).read_bytes())!=pin]
    write(output/'restoration-result.json',{'status':'READY_FOR_OWNER_TEST','runtime_qualified':False,'workshop':str(workshop.root),'candidate':str(output/'workshop/builds/first/candidate'),
          'source_pins':pins,'source_changes':changed,'physics':report,'identity':identity,'build':result,
          'retail_corrections':retail_corrections,'unverified':['31st independent record complete lifecycle','Results driver identity and full race completion','corrected glow core, retail tyre wear, mini icon and frontend height in D3D8','No separate source rear glass surface; no invented rear damage zone','Broken glass UV/normals approximate retail appearance; original intact pane attributes preserved','Randomizer coexistence not newly tested; existing CMD environment rules apply']})
    if changed:raise ValueError('Immutable source changed')
    (output/'Open-Forester-Workshop.cmd').write_text('@echo off\n"'+sys.executable+'" "'+str(ROOT/'tools/rally_workshop.py')+'" --project "%~dp0workshop" --workspace "%~dp0workshop-workspace"\nif errorlevel 1 pause\n')
    return workshop


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for name in ('demo','rebaked','retail-sma','ps2','roster-config','output'):a.add_argument('--'+name,required=True,type=Path)
    a.add_argument('--retail-corrections',action='store_true',help='Owner revision: retail physics, original mini icon, reference ON core and frontend frame')
    a.add_argument('--mini-icon',type=Path,help='Explicit original Demo side-view smallcarsheet texture (with original bank beside it)')
    x=a.parse_args();prepare(x.demo,x.rebaked,x.retail_sma,x.ps2,x.roster_config,x.output,retail_corrections=x.retail_corrections,mini_icon=x.mini_icon)
