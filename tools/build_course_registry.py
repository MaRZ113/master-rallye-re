"""Compose accepted V-CAP3 and a Course manifest into one private runtime.

Output is confined to this worktree's ignored COURSE-CAP2 directory. Nothing
is installed. The same accepted Vehicle launcher source builds the executable.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import time
import types
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from course_capacity_audit import extract,pe_image,check_resources
# Keep the two worktrees' Python packages in independent namespaces. Their
# historical __init__ modules eagerly import different Vehicle SDK revisions.
_package=types.ModuleType('_mr_course_cap2')
_package.__path__=[str(ROOT/'src/master_rallye')]
sys.modules['_mr_course_cap2']=_package
_registry=importlib.import_module('_mr_course_cap2.course_registry')
_native=importlib.import_module('_mr_course_cap2.course_runtime')
resource_path,identity_contract=_registry.resource_path,_registry.identity_contract
qualify,append_native=_native.qualify,_native.append_native


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(doc):return (json.dumps(doc,sort_keys=True,indent=2)+'\n').encode()
def read(path):return json.loads(Path(path).read_text())


def prepare_scene_resources(catalog, resources):
    """Optional derived RaceTest variants; geometry and native formats retained.

    A prepared external Course can instead supply complete resource overrides.
    Reusing a source scene is explicitly reported as a route variant, not an
    imported terrain. Copy AI bytes to an independent binding, not a new claim
    about an AI authoring format.
    """
    from _mr_course_cap2.course_entry import build_entry_racetest
    from _mr_course_cap2.course_atlas import read_marker_list
    values={k.casefold():k for k in resources}
    report=[]
    for race in catalog['races'][39:]:
        variant=race.get('prepare_variant')
        if not variant:continue
        targets=[race['scene'],race['icont'],str(Path(race['scene']).with_suffix('.hnt')).replace('\\','/')]
        if any(p.casefold() in values for p in targets):raise ValueError('Derived variant would overwrite an inherited resource')
        src=resources[values[resource_path(variant['source_scene']).casefold()]]
        scene=Path(src)
        route=read_marker_list(scene,'RaceLine')
        tree=ET.parse(scene).getroot()
        models=[v.get('Value') for e in tree.iter('Egg') if e.get('Name','').lower()=='landscape' for v in e.iter('Value') if v.get('Name')=='en3d Model Name']
        name=Path(race['scene']).stem
        raw,detail=build_entry_racetest(scene,entry_name=name,model_name=models[0],route=route,source_xmls=[scene],marker_spacing=variant.get('marker_spacing',20.0))
        # Keep the native source's full limit polylines rather than estimating
        # a lateral profile. Full route endpoints are unchanged in this variant.
        native=ET.parse(scene).getroot();new=ET.fromstring(raw)
        for parent in new.iter():
            for node in list(parent):
                if node.tag=='List' and node.get('Name') in ('LeftInnerLimit','LeftOuterLimit','RightInnerLimit','RightOuterLimit'):
                    original=next(n for n in native.iter('List') if n.get('Name')==node.get('Name'))
                    index=list(parent).index(node);parent.remove(node);parent.insert(index,copy.deepcopy(original))
        raw=ET.tostring(new,encoding='utf-8')
        resources[race['scene']]=raw
        hnt=scene.with_suffix('.hnt')
        resources[str(Path(race['scene']).with_suffix('.hnt')).replace('\\','/')]=hnt.read_bytes()
        ai=resources[values[resource_path(variant['source_icont']).casefold()]]
        resources[race['icont']]=Path(ai).read_bytes()
        report.append({**detail,'race_id':race['id'],'scene':race['scene'],'ai':race['icont'],
                       'source_ai_bytes_preserved':True,'new_terrain':False,'limits':'source full polylines preserved'})
    return report


def scene_menu(raw,catalog):
    root=ET.fromstring(raw)
    eggs=[e for e in root.iter('Egg') if e.get('Name')=='BagooCup3']
    if len(eggs)!=1:raise ValueError('Course Select template widget differs')
    template=eggs[0];parent=next(p for p in root.iter() if template in list(p))
    for r in catalog['races'][39:]:
        egg=copy.deepcopy(template);egg.set('Name','CourseRegistryRace'+str(r['id']))
        local=catalog['reverse_menu'][r['id']][1]
        for v in egg.iter('Value'):
            n=v.get('Name')
            if n=='X ID':v.set('Value',str(local))
            if n=='Y ID':v.set('Value','0')
            if n=='XPos*':v.set('Value',f'Frontend/RaceSelect/Button{local}XPos')
            if n=='en2d Image Bank Index':v.set('Value',str(r['menu']['flag_frame']))
        parent.append(egg)
    return ET.tostring(root,encoding='utf-8')


def gameplay_contract(catalog,resources,vehicle_contract):
    """Gameplay dependencies, with decorative pixels and scene dressing excluded."""
    from _mr_course_cap2.dx_course import parse_course_dx_bytes
    value=lambda x:x if isinstance(x,bytes) else Path(x).read_bytes()
    paths={p.casefold():p for p in resources}
    def raw(p):return value(resources[paths[p.casefold()]])
    def node(e):return [e.tag,sorted(e.attrib.items()),[node(child) for child in e]]
    names={'Cars','StartArea','FinishArea','SplitTimes','RaceLine','LeftInnerLimit','LeftOuterLimit','RightInnerLimit','RightOuterLimit'}
    deps={}
    for r in catalog['races']:
        root=ET.fromstring(raw(r['scene']))
        logic=[node(e) for e in root.iter('List') if e.get('Name') in names]
        deps['race:'+str(r['id'])]=digest(encoded({'scene_logic':logic,'ai':digest(raw(r['icont']))}))
    for c in catalog['courses']:
        model=parse_course_dx_bytes(raw(c['model']))
        deps['course:'+c['key']]=digest(model.trailing.data)
    contract={'schema':'mr-vehicle-course-competition-contract/1','vehicle_contract':vehicle_contract,
              'course_contract':identity_contract(catalog),'dependencies':deps}
    contract['sha256']=digest(encoded(contract))
    return contract


def seed_progress(raw,catalog):
    root=ET.fromstring(raw);broker=root.find('Broker')
    if broker is None:raise ValueError('PlayerState has no native Broker')
    names={v.get('Name') for v in broker.findall('Value')}
    for r in catalog['races'][39:]:
        key='Progress/BestTimes/CourseRegistryV1/'+r['progress_key']
        if key not in names:
            ET.SubElement(broker,'Value',Name=key,Type='Float',Value='86400.00000',SaveOptions='False',SavePlayerState='True')
    return ET.tostring(root,encoding='utf-8')


def compose_course_artwork(catalog,resources,artwork_root=None):
    """Append native sprite frames with the accepted SDK bank/FEED APIs."""
    import struct,zlib
    from master_rallye.addon_sdk.ui_assets import parse_bank,append_frame
    from master_rallye.texture_authoring import decode_rgba_png
    from master_rallye.dxt import parse_dxt_bytes,encode_dxt_pixels
    value=lambda x:x if isinstance(x,bytes) else Path(x).read_bytes()
    paths={p.casefold():p for p in resources};report=[]
    def bank_path(role):return paths[('DataGx/Frontend/RaceSelect/'+role+'.dxb').casefold()]
    def add(role,template,png):
        if artwork_root is None:raise ValueError('Artwork PNGs require an explicit artwork_root')
        relative=resource_path(png);root=Path(artwork_root).resolve();path=(root/relative).resolve()
        if not path.is_relative_to(root):raise ValueError('Artwork path escapes its source root')
        bank=bank_path(role);raw=value(resources[bank]);before=parse_bank(raw)
        name=before['names'][template]
        tex_path=paths[(str(Path(bank).parent/name)+'.dxt').replace('\\','/').casefold()]
        tex=parse_dxt_bytes(value(resources[tex_path]));w,h,rgba=decode_rgba_png(path.read_bytes())
        if (w,h)!=(tex.width,tex.height):raise ValueError('Course artwork PNG must match native template dimensions')
        newbank,newname=append_frame(raw,template)
        output=(str(Path(bank).parent/newname)+'.dxt').replace('\\','/')
        if output.casefold() in paths:raise ValueError('New Course artwork frame collides with existing resource')
        pixels=bytearray(encode_dxt_pixels(tex,rgba,w,h));struct.pack_into('<I',pixels,8,zlib.crc32(pixels[20:])&0xffffffff)
        resources[bank]=newbank;resources[output]=bytes(pixels);paths[output.casefold()]=output
        return before['count']
    for r in catalog['races'][39:]:
        art=r.get('artwork',{});pair=r['menu']['screenshot_pair']
        if art.get('screenshots'):
            if len(art['screenshots'])!=2:raise ValueError('Native Course artwork needs two screenshot frames')
            first=add('screenshotsheet',pair*2,art['screenshots'][0])
            second=add('screenshotsheet',pair*2+1,art['screenshots'][1])
            if first%2 or second!=first+1:raise ValueError('Course screenshot pair is not aligned')
            r['menu']['screenshot_pair']=first//2
        if art.get('flag_png'):r['menu']['flag_frame']=add('flagsheet',r['menu']['flag_frame'],art['flag_png'])
        if art:report.append({'race_id':r['id'],'screenshot_pair':r['menu']['screenshot_pair'],'flag_frame':r['menu']['flag_frame'],
                              'provenance':art.get('provenance','custom'),'original_frames_preserved':True})
        if r['menu']['screenshot_pair']*2+1>=parse_bank(value(resources[bank_path('screenshotsheet')]))['count']:
            raise ValueError('Course screenshot-pair binding exceeds the actual native bank')
        if r['menu']['flag_frame']>=parse_bank(value(resources[bank_path('flagsheet')]))['count']:
            raise ValueError('Course flag binding exceeds the actual native bank')
    return report


def build(config,out,*,compile_launcher=True):
    start=time.perf_counter();out=Path(out).resolve()
    allowed=(ROOT/'.research-output/course-cap2').resolve()
    if not out.is_relative_to(allowed) or out.exists():raise ValueError('Use a fresh COURSE-CAP2 private output')
    vehicle=Path(config['vehicle_source']).resolve();base=Path(config['vehicle_runtime']).resolve()
    for name in list(sys.modules):
        if name=='master_rallye' or name.startswith('master_rallye.'):del sys.modules[name]
    sys.path[:0]=[str(vehicle/'tools'),str(vehicle/'src')]
    import addon_runtime as runtime
    import j2_frontend_reentry as j2
    import prepare_sdk_capacity_probe as probe
    import patch_vehicle_registry_id26 as registry
    import build_vehicle_registry as vehicles
    source=Path(config['retail_exe']).read_bytes();rp=read(base/'runtime-profile.json')
    if digest(source)!=rp['retail_exe']['sha256']:raise ValueError('Retail source identity mismatch')
    # Exact digests seal compiled native inputs, not editable Course textures.
    for name,key in [('addon-plan.json','addon_plan_sha256'),('native-patch-manifest.json','native_patch_manifest_sha256'),('native-patch-ops.rvp','native_patch_operations_sha256'),('resource-manifest.json','resource_manifest_sha256')]:
        if digest((base/name).read_bytes())!=rp[key]:raise ValueError('Accepted Vehicle compiled input changed: '+name)
    vehicle_manifest=Path(config['vehicle_manifest']).read_bytes()
    if json.loads(vehicle_manifest)!=read(base.parent/'registry-build.json'):raise ValueError('Vehicle source manifest differs from accepted runtime build')
    parent_blob=(base/'native-extension.bin').read_bytes()
    if digest(parent_blob)!=rp['native_extension']['sha256']:raise ValueError('Accepted native payload changed')
    # Validate MRVC and the sealed parent resource set before deriving anything.
    import build_runtime_launcher as launcher
    launcher._capacity_descriptor(rp,rp['native_extension'],parent_blob)
    files={n:(base/n).read_bytes() for n in ['resource-manifest.json']}
    vehicles.verify_bundle(base,{'files':files})
    _,image,rows=j2._parse_and_reconstruct(source,(base/'native-patch-ops.rvp').read_bytes())
    baseline,_=extract(source)
    catalog=qualify(read(config['course_manifest']),baseline,rp)
    _,offset=pe_image(source)
    resources={r['path']:base/'resource-root'/r['path'] for r in read(base/'resource-manifest.json')['resources']}
    for path,source_path in config.get('resource_overrides',{}).items():
        path=resource_path(path)
        if path.casefold() in {p.casefold() for p in resources}:raise ValueError('Inherited resource overwrite prohibited: '+path)
        resources[path]=Path(source_path).read_bytes()
    prepared=prepare_scene_resources(catalog,resources)
    artwork=compose_course_artwork(catalog,resources,config.get('artwork_root'))
    menu='DataScene/FrontendScreens/RaceSelect.xml'
    value=lambda x:x if isinstance(x,bytes) else Path(x).read_bytes()
    resources[menu]=scene_menu(value(resources[menu]),catalog)
    image,blob,native=append_native(source,image,parent_blob,catalog,emitter=registry._CodeImage,pe_offset=offset)
    allocation=max(rp['native_extension']['allocation_size'],(len(blob)+65535)//65536*65536)
    if allocation+catalog['layout']['allocation_size']>rp['capacity_profile']['memory_budget_bytes']:
        raise ValueError('Combined arena and object exceed accepted memory budget')
    plan=read(base/'addon-plan.json')
    plan['registry_layout'].update(allocation_size=catalog['layout']['allocation_size'],race_count=catalog['layout']['race_count'])
    plan['course_registry']={'identity_sha256':identity_contract(catalog),'schema':catalog['schema']}
    plan_raw=encoded(plan);plan_sha=digest(plan_raw)
    extension={**native,'allocation_size':allocation,'payload_va':0x10000000,'payload_size':len(blob)}
    pm,rvp=probe.patch_artifacts(source,image,rows,image,extension,plan_sha,read(base/'native-patch-manifest.json'),
        profile_name=rp['profile'],provenance_layer='COURSE-CAP2',extension_key='course_registry_extension',
        derivation='single accepted Vehicle plus manifest Course transaction; original retail preimages')
    rr=[]
    for path,v in sorted(resources.items()):
        raw=value(v);rr.append({'path':path,'size':len(raw),'sha256':digest(raw),'role':'composed-vehicle-course-resource'})
    index=runtime._resource_index(rr)
    rm=encoded({'schema_version':1,'resources':rr,'resource_count':len(rr),'index_sha256':digest(index),
                'runtime_state_paths':sorted(runtime.RUNTIME_STATE_PATHS),'addon_plan_sha256':plan_sha})
    profile=copy.deepcopy(rp)
    profile.update(addon_plan_sha256=plan_sha,native_patch_manifest_sha256=digest(pm),native_patch_operations_sha256=digest(rvp),
        resource_manifest_sha256=digest(rm),resource_index_sha256=digest(index),resource_count=len(rr),
        reconstructed_reference_file_sha256=digest(image),course_registry_descriptor=native['entries']['descriptor'],
        course_registry_layout=catalog['layout'],native_extension={**rp['native_extension'],'size':len(blob),'sha256':digest(blob),'allocation_size':allocation},runtime_qualified=False)
    previous=read(base/'competition-contract.json')
    # This combines stable gameplay identities; artwork/texture pixels excluded.
    contract=gameplay_contract(catalog,resources,previous['sha256'])
    profile['competition_contract_sha256']=contract['sha256']
    state_source=Path(config.get('player_state_source',base/'resource-root/DataGame/PlayerState.xml'))
    state=state_source.read_bytes()
    if not 1<=len(state)<=4*1024*1024:raise ValueError('Source PlayerState is not a bounded native save')
    from master_rallye.addon_sdk.roster_identity import preflight_player_state
    ident=read(base/'roster-identity.json');preflight=preflight_player_state(state,ident,ident)
    previous_course=read(config['previous_course_contract']) if config.get('previous_course_contract') else None
    if previous_course is not None:
        if previous_course.get('sha256')!=digest(encoded({k:v for k,v in previous_course.items() if k!='sha256'})):
            raise ValueError('Previous Course competition contract has an invalid fingerprint')
    same_contract=previous_course is not None and previous_course['sha256']==contract['sha256']
    has_course_progress=any('CourseRegistryV1/' in v.get('Name','') for v in ET.fromstring(state).iter('Value'))
    if (preflight['active_competitions'] or has_course_progress) and not same_contract:
        raise ValueError('Saved competition/Course records require the matching previous gameplay contract; source left unchanged. Use an inactive fresh profile for changed Course dependencies')
    state=seed_progress(state,catalog)
    stage=time.perf_counter()
    bundle=out/'runtime';bundle.mkdir(parents=True)
    metadata={'addon-plan.json':plan_raw,'native-patch-manifest.json':pm,'native-patch-ops.rvp':rvp,
              'native-extension.bin':blob,'runtime-profile.json':encoded(profile),'resource-manifest.json':rm,'resource-index.tsv':index,
              'competition-contract.json':encoded(contract),'course-registry.json':encoded(catalog),'course-build-audit.json':encoded({'native':native,'prepared_variants':prepared,'artwork':artwork,'runtime_qualified':False})}
    for name in ['roster-identity.json','artwork-bindings.json']:metadata[name]=(base/name).read_bytes()
    for path,v in resources.items():
        target=bundle/'resource-root'/path;target.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(v,bytes):target.write_bytes(v)
        else:shutil.copyfile(v,target)
    (bundle/'resource-root/DataGame/PlayerState.xml').write_bytes(state)
    metadata['competition-baseline.txt']=(contract['sha256']+'\n'+digest(state)+'\n').encode()
    for name,raw in metadata.items():(bundle/name).write_bytes(raw)
    checked=vehicles.verify_bundle(bundle,{'files':metadata})
    launcher._course_descriptor(profile,profile['native_extension'],blob)
    check_resources(catalog,bundle/'resource-root')
    result={'status':'PRIVATE_COURSE_RUNTIME_CANDIDATE_NOT_GAMEPLAY_TESTED','runtime_qualified':False,
            'layout':catalog['layout'],'native_operations':len(json.loads(pm)['operations']),
            'compose_seconds':stage-start,'bundle_seconds':time.perf_counter()-start,'verification':checked}
    if compile_launcher:
        result['launcher']=launcher.build_launcher(bundle=bundle,output=out/'launcher',retail_exe=Path(config['retail_exe']),
            bundle_verifier=lambda:checked,sdk_binding_input=True,research_root=ROOT/'.research-output')
    result['total_seconds']=time.perf_counter()-start
    (out/'build-input.json').write_bytes(encoded(config));(out/'validation.json').write_bytes(encoded(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--no-launcher',action='store_true')
    a=p.parse_args();print(json.dumps(build(read(a.manifest),a.output,compile_launcher=not a.no_launcher),indent=2))
