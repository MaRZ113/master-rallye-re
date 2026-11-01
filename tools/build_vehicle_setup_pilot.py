"""Build a private V-SET1 renderer overlay; never install into a game folder.

Uses the current accepted PS2 renderer stage and validates its published source
pins. The borrowed renderer sources and private game pixels stay ignored.
"""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tools')]
from master_rallye.addon_sdk.setup_sources import ps2_model, public_model, transfer_rgb_rows
from master_rallye.addon_sdk.vehicle_setup import digest, tyre_table
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes


def replace_once(path, old, new):
    data = path.read_text(encoding='utf-8')
    if data.count(old) != 1:
        raise ValueError('Unqualified renderer integration seam: ' + str(path))
    path.write_text(data.replace(old, new), encoding='utf-8')


def uv_witness(model_raw, parsed, native, index):
    at = 64 + struct.unpack_from('<I', model_raw, 12)[0] + len(parsed['draws'])*28
    vertices = list(struct.iter_unpack('<6fI2f', model_raw[at:at+parsed['vertices']*36]))
    at += parsed['vertices']*36
    indices = [i[0] for i in struct.iter_unpack('<I', model_raw[at:at+parsed['indices']*4])]
    name = parsed['textures'][index]['source']['path'].replace('\\','/').split('/')[-1][:-4].lower()
    source = [vertices[indices[j]][7:] for d in parsed['draws'] if d['textures'][0] == index
              for j in range(d['first'], d['first']+d['count'])]
    target = [native.uv_sets[0].values[i] for d in native.physical_draws
              if d.texture_tuple[0].lower() == name for i in native.draw_global_indices(d)]
    quantize = lambda p: tuple(round(v, 6) for v in p)
    a, b = Counter(map(quantize, source)), Counter(map(quantize, target))
    return {'texture': name, 'ps2_corners': len(source), 'pc_corners': len(target),
            'uv_corner_multisets_equal_1e6': a == b,
            'ps2_corners_with_pc_uv': sum(n for v,n in a.items() if v in b),
            'pc_corners_with_ps2_uv': sum(n for v,n in b.items() if v in a),
            'qualification': 'CORNER_COVERAGE_ONLY; panel visualization remains owner test'}


def prepare(output, upstream, ps2_assets, retail, config_path=None):
    from master_rallye.addon_sdk.vehicle_setup import decode_json, TOKEN
    config_path = config_path or ROOT/'research/vehicles/vset1/seatbuggy-pilot.json'
    config_raw = Path(config_path).read_bytes(); config = decode_json(config_raw)
    from master_rallye.addon_sdk import setup_adapter
    adapter=json.loads((ROOT/'research/vehicles/vset1/retail-adapter.json').read_text())
    adapter_proof=setup_adapter.validate((Path(retail).parent/'MRallye.exe').read_bytes(),adapter)
    if config.get('schema')!='vehicle-setup-pilot/1' or any(not TOKEN.fullmatch(config[k]) for k in ('identity','family','ps2_family','stock_tyre','alternative_tyre')) or type(config['car_id']) is not int or not 0<=config['car_id']<=255:
        raise ValueError('Invalid pilot manifest')
    if any(type(config.get(k)) is not int or config[k] not in (0,1) for k in ('default_livery','default_tyre')):
        raise ValueError('Unsupported preset default')
    if config['stock_tyre']!='native-default':raise ValueError('Stock is a native pass-through, never a substituted tire family')
    output = Path(output).resolve()
    allowed = (ROOT/'.research-output/vehicles/v-set1').resolve()
    if not output.is_relative_to(allowed) or output == allowed or output.exists():
        raise ValueError('Choose a fresh private V-SET1 output')
    upstream = Path(upstream).resolve()
    report = json.loads((upstream/'dist/current/build-report.json').read_text())
    stage = upstream/'.staging/ps2-enabled'
    port = stage/'ps2-research/pc-port'
    verified = {}
    for relative, expected in report['ps2_source_sha256'].items():
        p = port/relative
        if digest(p.read_bytes()) != expected:
            raise ValueError('Accepted upstream stage changed: ' + relative)
        verified[relative] = expected
    asset_raw = (Path(ps2_assets)/(config['ps2_family']+'-CAR-FLEET.ps2model')).read_bytes()
    car = ps2_model(asset_raw)
    complete = ps2_model((Path(ps2_assets)/(config['ps2_family']+'-COMPLETE-FLEET.ps2model')).read_bytes())
    native_raw=(Path(retail)/'DataGx/Vehicles'/config['family']/'car.dx').read_bytes()
    if car['metadata'].get('pc_source_sha256')!=digest(native_raw):raise ValueError('Wrong native technical source for this qualified PS2 model')
    import re
    profile=(port/'renderer/race_fleet_registry.hpp').read_text()
    if not re.search(r'\{"'+re.escape(config['family'])+r'","'+re.escape(config['ps2_family'])+r'","'+re.escape(config['ps2_family'])+r'-CAR-FLEET.ps2model","'+car['source_sha256']+r'"',profile):
        raise ValueError('PS2 asset does not match the accepted renderer profile')
    registry=json.loads((ROOT/'research/r5v_a/final-vehicle-registry.json').read_text())['canonical_registry']
    original=[r for r in registry if r['internal_name'].lower()==config['family'].lower()]
    if len(original)!=1 or original[0]['numeric_id']!=config['car_id']:
        raise ValueError('Pilot CarID/family differs from the qualified original registration')
    native = parse_dx_bytes(native_raw)
    selected = [t['index'] for t in car['textures'] if (t['source'] or {}).get('path','').replace('\\','/').split('/')[-1].lower() in config['paint_textures']]
    if len(selected)!=len(config['paint_textures']):raise ValueError('Missing or ambiguous paint ownership')
    diagnostics=[t['index'] for t in car['textures'] if (t['source'] or {}).get('path','').replace('\\','/').split('/')[-1].lower() in config['diagnostic_textures']]
    witnesses = [uv_witness(asset_raw, car, native, i) for i in selected+diagnostics]
    # Only the fully matched panels are admitted; seat06 stays original.
    # The receiving PS2 mesh must use only witnessed PC atlas coordinates.
    # Extra coordinates used only by the PC mesh do not become new PS2 faces.
    # Multiplicity/topology differences remain in the report, not a parity PASS.
    if not all(w['ps2_corners_with_pc_uv']==w['ps2_corners'] and w['ps2_corners']>0
               for w in witnesses[:len(selected)]):
        raise ValueError('The selected SeatBuggy panels are not UV compatible')
    xml = (Path(retail)/'DataGame/vehicles.xml').read_bytes()
    import xml.etree.ElementTree as ET
    stock={n.get('Name'):n.get('Value') for n in ET.fromstring(xml).iter('Value')}
    stock_refs={}
    for axle in ('Front','Rear'):
        key='Vehicles/'+config['family']+'/Suspension/'+axle+'/TyreType'
        if not stock.get(key):raise ValueError('Missing original Stock tire reference')
        stock_refs[axle.lower()]={'kind':'NATIVE_PASSTHROUGH','prefix':stock[key],'source_sha256':digest(xml),'evidence_key':key}
    tables = {config['alternative_tyre']: tyre_table(xml,config['alternative_tyre'])}
    output.mkdir(parents=True)
    source = output/'source'
    shutil.copytree(stage/'modernization/renderer',source/'renderer')
    shutil.copytree(port,source/'port')
    module = source/'setup'
    shutil.copytree(ROOT/'runtime_setup',module)
    (module/'setup_adapter.hpp').write_text(setup_adapter.header(adapter))
    assets = output/'VSETAssets';assets.mkdir()
    bindings = []
    for original in (car, complete):
        for texture in original['textures']:
            name = (texture['source'] or {}).get('path','').replace('\\','/').split('/')[-1].lower()
            if name not in config['paint_textures']:
                continue
            pc_path = Path(retail)/'DataGx/Vehicles'/config['family']/(name[:-4]+'.dxt')
            pc_raw = pc_path.read_bytes();pc = parse_dxt_bytes(pc_raw)
            w,h = texture['width'],texture['height']
            if (w,h) != (pc.width,pc.height):
                raise ValueError('Panel texture dimensions differ')
            # PS2 private renderer uses 1-v; native PC atlas stored rows require
            # one explicit inversion for the same source UV. Alpha stays PS2.
            derived = transfer_rgb_rows(texture['_bgra'],pc.bgra,w,h,flip_rows=True)
            base_hash, alt_hash = digest(texture['_bgra']), digest(derived)
            for sha, raw in ((base_hash,texture['_bgra']),(alt_hash,derived)):
                p=assets/(sha+'.bgra')
                if p.exists() and p.read_bytes()!=raw:raise ValueError('Hash collision')
                if not p.exists():p.write_bytes(raw)
            bindings.append({'index':texture['index'],'width':w,'height':h,
                             'base_path':'VSETAssets/'+base_hash+'.bgra','base_sha':base_hash,
                             'alternate_path':'VSETAssets/'+alt_hash+'.bgra','alternate_sha':alt_hash,
                             'pc_source_sha256':digest(pc_raw),'ps2_source':texture['source'],
                             'transform':'flip stored PC rows; RGB only; retain every PS2 alpha sample'})
    unique = list({(b['index'],b['base_sha']):b for b in bindings}.values())
    # The actual pilot consumes the same reusable preset contract as Workshop.
    # DXT here is a normalized BGRA carrier, not a claim of original MR ownership.
    from master_rallye.addon_sdk import vehicle_setup as setup
    contract_root=output/'setup-contract';(contract_root/'textures').mkdir(parents=True)
    alternatives={b['base_sha']:output/b['alternate_path'] for b in unique}
    livery_rows=[]
    for preset_id,label,alternate in (('original',config['livery_default'],False),('pc-panels',config['livery_alternative'],True)):
        owned=[]
        for draw_index,draw in enumerate(car['draws']):
            for slot,index in enumerate(draw['textures']):
                if index==0xffffffff:continue
                texture=car['textures'][index];pixels=texture['_bgra']
                if alternate and texture['bgra_sha256'] in alternatives:pixels=alternatives[texture['bgra_sha256']].read_bytes()
                carrier=struct.pack('<5I',0xfeed,0,0,texture['width'],texture['height'])+pixels
                pin=digest(carrier);relative='textures/'+pin+'.dxt';path=contract_root/relative
                if not path.exists():path.write_bytes(carrier)
                owned.append({'material':f'draw-{draw_index}-node-{draw["node"]}','slot':slot,
                              'path':relative,'sha256':pin,'alpha_sha256':digest(pixels[3::4])})
        livery_rows.append({'id':preset_id,'label':label,'source':{'classification':'RECONSTRUCTED' if alternate else 'ORIGINAL',
                            'version':'PS2 original pixel carrier' if not alternate else 'PC sponsor pixels on UV-witnessed PS2 panels; source alpha retained',
                            'sha256':car['source_sha256']},'geometry_sha256':car['geometry_sha256'],
                            'textures':owned,'carsheet':None,'smallcarsheet':None})
    tyre_source={'classification':'ORIGINAL','version':'Qualified retail PC references/tables, not PS2 physics','sha256':digest(xml)}
    tyre_rows=[{'id':'stock','label':'Stock (unchanged retail profile)','source':tyre_source,**stock_refs},
               {'id':config['alternative_tyre'],'label':'Retail '+config['alternative_tyre'],'source':tyre_source,
                'front':tables[config['alternative_tyre']],'rear':tables[config['alternative_tyre']]}]
    preset_manifest={'schema':setup.VERSION,'vehicle':{'id':config['identity'],'car_id':config['car_id'],'geometry_sha256':car['geometry_sha256']},
                     'defaults':{'livery':livery_rows[config['default_livery']]['id'],'tyre':tyre_rows[config['default_tyre']]['id']},
                     'liveries':livery_rows,'tyres':tyre_rows,
                     'scope':{'mode':'quick_race','participant':'human_player_1','application':'before_vehicle_creation'}}
    setup.validate(preset_manifest,root=contract_root);setup.verify_tyre_sources(preset_manifest,xml)
    (contract_root/'vehicle-setup.json').write_bytes(setup.canonical_json(preset_manifest))
    from PIL import Image, ImageDraw
    preview_rows=list({b['base_sha']:b for b in unique}.values())
    preview=Image.new('RGB',(780,190*len(preview_rows)),(38,42,48));draw=ImageDraw.Draw(preview)
    for row,b in enumerate(preview_rows):
        for col,key in enumerate(('base_path','alternate_path')):
            image=Image.frombytes('RGBA',(b['width'],b['height']),(output/b[key]).read_bytes(),'raw','BGRA').convert('RGB')
            image.thumbnail((370,150));preview.paste(image,(10+col*390,30+row*190))
            draw.text((10+col*390,8+row*190),('PS2 original' if col==0 else 'PC panel RGB, PS2 alpha')+' / slot '+str(b['index']),fill='white')
    preview.save(output/'livery-panels.png')
    contract=digest(json.dumps({'manifest_sha256':digest(setup.canonical_json(preset_manifest)),'config':config,'car':car['source_sha256'],'complete':complete['source_sha256'],
                               'bindings':unique,'tyres':tables},sort_keys=True).encode())
    definitions = ',\n'.join('{'+str(b['index'])+','+str(b['width'])+','+str(b['height'])+','+
                      ','.join(json.dumps(b[k]) for k in ('base_path','base_sha','alternate_path','alternate_sha'))+'}' for b in unique)
    header = '''#pragma once
namespace mrsetup::package {
inline constexpr unsigned car_id=21;
inline constexpr char family[]="SeatBuggy",identity[]="mr-seatbuggy-ps2-v1";
inline constexpr wchar_t identity_w[]=L"mr-seatbuggy-ps2-v1";
inline constexpr char livery_default[]="PS2 original",livery_alternative[]="PC sponsor panels (reconstructed)";
inline constexpr char tyre_default_label[]="Stock (retail harddirt)",tyre_alternative_label[]="Retail gravel (complete original table)";
inline constexpr char alternative_tyre[]="gravel";
inline constexpr char contract[]="CONTRACT_HASH";
inline constexpr wchar_t contract_w[]=L"CONTRACT_HASH";
inline constexpr unsigned default_livery=DEFAULT_LIVERY,default_tyre=DEFAULT_TYRE;
struct Binding {unsigned index,width,height;const char *base_path,*base_sha,*alternate_path,*alternate_sha;};
inline constexpr Binding bindings[]={BINDINGS};
inline constexpr unsigned binding_count=sizeof(bindings)/sizeof(bindings[0]);
}
'''.replace('BINDINGS',definitions)
    header=header.replace('CONTRACT_HASH',contract).replace('DEFAULT_LIVERY',str(config['default_livery'])).replace('DEFAULT_TYRE',str(config['default_tyre']))
    header=header.replace('car_id=21','car_id='+str(config['car_id']))
    header=header.replace('"SeatBuggy"',json.dumps(config['family'])).replace('"mr-seatbuggy-ps2-v1"',json.dumps(config['identity']))
    header=header.replace('"PS2 original"',json.dumps(config['livery_default'])).replace('"PC sponsor panels (reconstructed)"',json.dumps(config['livery_alternative']))
    header=header.replace('"gravel"',json.dumps(config['alternative_tyre']))
    header=header.replace('"Stock (retail harddirt)"','"Stock (unchanged retail profile)"')
    header=header.replace('"Retail gravel (complete original table)"',json.dumps('Retail '+config['alternative_tyre']+' (complete original table)'))
    (module/'setup_package.hpp').write_text(header)
    renderer = source/'renderer'
    replace_once(renderer/'src/forwarders.cpp','HRESULT STDMETHODCALLTYPE Device8::EndScene() {',
                 'HRESULT STDMETHODCALLTYPE Device8::EndScene() {\n mrsetup::frame(*real_);')
    text=(renderer/'src/forwarders.cpp').read_text();(renderer/'src/forwarders.cpp').write_text('#include "setup_runtime.hpp"\n'+text)
    model=source/'port/renderer/frontend_model.cpp'
    replace_once(model,'#include "frontend_model.hpp"','#include "frontend_model.hpp"\n#include "setup_runtime.hpp"')
    # The private candidate enables a fleet path only for the configured pilot.
    # Other vehicles retain Stock when this flag was disabled in the owner INI.
    replace_once(model,'if(!fleet_enabled()||transaction.pending())return false;',
                 'if(!mrsetup::pilot_family_allowed(profile.family))return false;if(!fleet_enabled()||transaction.pending())return false;')
    replace_once(model,'if(!car_fleet_enabled()||i>=std::size(kRaceFleetProfiles)',
                 'if(i<std::size(kRaceFleetProfiles)&&!mrsetup::pilot_family_allowed(kRaceFleetProfiles[i].family))return false;if(!car_fleet_enabled()||i>=std::size(kRaceFleetProfiles)')
    replace_once(model,'#include "setup_runtime.hpp"','#include "setup_runtime.hpp"\n#include "setup_package.hpp"')
    replace_once(source/'port/renderer/frontend_model.hpp',' float source_radius_sq_=0;', ' unsigned setup_revision_=0;\n float source_radius_sq_=0;')
    replace_once(model,'if(!requested())return false;if(textures_.size()==asset_.textures.size())return true;',
        'if(!requested())return false;auto setup=mrsetup::revision(profile_?profile_->family:nullptr);if(setup!=setup_revision_){if(states_pending())return false;for(auto* t:textures_)if(t)t->Release();textures_.clear();setup_revision_=setup;}if(textures_.size()==asset_.textures.size())return true;')
    replace_once(model,'const auto& t=asset_.textures[i];if(FAILED(n.CreateTexture',
        'auto t=asset_.textures[i];mrsetup::pixels(profile_?profile_->family:nullptr,unsigned(i),t.width,t.height,asset_.textures[i].pixels.data(),t.pixels.data(),unsigned(t.pixels.size()*4));if(FAILED(n.CreateTexture')
    with (renderer/'CMakeLists.txt').open('a') as f:
        f.write('\ntarget_sources(proxy_core PRIVATE "'+(module/'setup_runtime.cpp').as_posix()+'")\n'+
                'target_include_directories(proxy_core PRIVATE "'+module.as_posix()+'")\n'+
                'target_link_libraries(proxy_core PUBLIC winmm)\n')
        f.write('add_executable(mr_vehicle_setup_tests "'+(module/'setup_runtime_tests.cpp').as_posix()+'")\n'+
                'target_include_directories(mr_vehicle_setup_tests PRIVATE include vendor/d3d8 "'+module.as_posix()+'")\n'+
                'target_link_libraries(mr_vehicle_setup_tests PRIVATE bcrypt user32 winmm)\n')
    result={'schema':'v-set1-private-build/1','config':config,'config_sha256':digest(config_raw),'contract_sha256':contract,'native_adapter':adapter_proof,'upstream_report_sha256':digest((upstream/'dist/current/build-report.json').read_bytes()),
            'upstream_source_verified':verified,'source':str(source),'uv_witnesses':witnesses,
            'livery_bindings':unique,'tyres':tables,'stock_tyre_references':stock_refs,'native_gameplay':'NOT_TESTED',
            'menu':'Owned in-process modal from native gearbox setup F6; windowed only',
            'scope':'Quick Race human1; no new CarID or source/installed Proxy changes'}
    (output/'preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def build(output):
    output=Path(output).resolve();source=output/'source'
    configure=['cmake','-S',str(source/'renderer'),'-B',str(output/'build'),'-G','Visual Studio 18 2026','-A','Win32',
               '-DMRR_ENABLE_PS2_PORT=ON','-DMRR_PS2_PORT_ROOT='+str(source/'port'),'-DBUILD_TESTING=ON']
    for command in (configure,['cmake','--build',str(output/'build'),'--config','Release','--parallel','2']):
        subprocess.run(command,check=True)


def package_candidate(output, baseline, game_root, ps2_assets, *, delivery_name='delivery'):
    """Reuse the sealed 33-car bundle; only a tiny private EXE/DLL host is new."""
    output=Path(output).resolve();baseline=Path(baseline).resolve();game_root=Path(game_root).resolve()
    dll=output/'build/Release/d3d8.dll'
    if not dll.is_file() or not (baseline/'runtime/runtime-profile.json').is_file():
        raise ValueError('A compiled module and accepted sealed roster candidate are required')
    if delivery_name not in ('delivery','delivery-final'):raise ValueError('Invalid owned delivery name')
    delivery=output/delivery_name
    if delivery.exists():raise ValueError('Delivery must be fresh')
    original_exe=game_root/'MRallye.exe'
    if not original_exe.is_file():raise ValueError('Missing original retail executable')
    # Verify the inherited resources and version adapter BEFORE copying anything.
    verifier=baseline/'launcher/mr-runtime-launcher.exe'
    check=subprocess.run([str(verifier),'--verify',str(original_exe),str(baseline/'runtime')],capture_output=True,text=True)
    if check.returncode:raise ValueError('Accepted baseline preflight failed: '+check.stdout+check.stderr)
    delivery.mkdir();host=delivery/'host';host.mkdir()
    shutil.copyfile(original_exe,host/'MRallye.exe');shutil.copyfile(dll,host/'d3d8.dll')
    # No installed wrapper is changed. Other same-name wrappers are never adopted
    # implicitly: their known F3 conflicts remain a separate composition gate.
    conflicts=[name for name in ('dinput8.dll','dsound.dll','ddraw.dll','winmm.dll') if (game_root/name).exists()]
    if conflicts:raise ValueError('Separate wrapper composition required: '+str(conflicts))
    shutil.copytree(output/'VSETAssets',host/'VSETAssets')
    (host/'VSET1.ini').write_text('[VehicleSetup]\nEnabled=1\n',encoding='utf-8')
    shutil.copyfile(game_root/'MRRRenderer.ini',host/'MRRRenderer.ini')
    ini=(game_root/'PS2Port.ini').read_text(encoding='utf-8-sig')
    def setting(text,key,value):
        import re
        pattern=re.compile(r'^'+re.escape(key)+r'=.*$',re.M)
        if len(pattern.findall(text))!=1:raise ValueError('Ambiguous/missing PS2 setting '+key)
        return pattern.sub(lambda _:key+'='+str(value),text)
    # Narrow fleet admission in this private build keeps all other families on
    # their accepted native renderer; do not disable an already-enabled fleet.
    for key in ('RaceFleet','FrontendModel'):
        import re
        if not re.search(r'^'+key+r'=0\s*$',ini,re.M):
            raise ValueError('Pilot-only package requires an accepted Stock fleet baseline')
    ini=setting(ini,'RaceFleet',1);ini=setting(ini,'FrontendModel',2)
    ini=setting(ini,'PS2FleetAllCars',1)
    for key in ('RaceModelAssetDirectory','FrontendModelAssetDirectory'):
        ini=setting(ini,key,str(Path(ps2_assets).resolve()))
    (host/'PS2Port.ini').write_text(ini,encoding='utf-8')
    # Immutable source assets share NTFS storage. Mutable player/options files
    # receive independent copies. Game writes cannot modify the accepted saves.
    links=[];copies=[]
    def clone(source,destination):
        p=Path(source)
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('Linked baseline input')
        if p.name.lower() in ('options.xml','playerstate.xml'):
            shutil.copyfile(source,destination);copies.append(str(p));return str(destination)
        os.link(source,destination);links.append(str(p));return str(destination)
    shutil.copytree(baseline/'runtime',delivery/'runtime',copy_function=clone)
    shutil.copytree(baseline/'launcher',delivery/'launcher',copy_function=shutil.copyfile)
    launch='@echo off\r\nif not exist "%~dp0host\\VSET1.ini" (\r\n echo Missing VSET1.ini. Restore the package marker; disable with Enabled=0 instead.\r\n pause\r\n exit /b 1\r\n)\r\necho V-SET1: Quick Race / SCHLESSER BUGGY 1997 / Vehicle Setup gearbox page / F6\r\necho Private windowed pilot; installed game and accepted roster stay unchanged.\r\n"%~dp0launcher\\mr-runtime-launcher.exe" --integrated "%~dp0host\\MRallye.exe" "%~dp0runtime"\r\nif errorlevel 1 pause\r\n'
    (delivery/'Launch-V-SET1.cmd').write_bytes(launch.encode())
    check=subprocess.run([str(delivery/'launcher/mr-runtime-launcher.exe'),'--verify-launch-environment',str(host/'MRallye.exe'),str(delivery/'runtime')],capture_output=True,text=True)
    (delivery/'preflight.txt').write_text(check.stdout+check.stderr)
    if check.returncode:raise ValueError('Private host preflight failed: '+check.stdout+check.stderr)
    result={'launch':str(delivery/'Launch-V-SET1.cmd'),'baseline_verification':check.stdout,
            'original_exe_sha256':digest(original_exe.read_bytes()),'host_exe_sha256':digest((host/'MRallye.exe').read_bytes()),
            'private_proxy_sha256':digest(dll.read_bytes()),'immutable_hardlinks':len(links),'independent_mutable_copies':copies,
            'installed_files_written':[],'new_car_ids':[],'owner_gameplay':'NOT_TESTED'}
    (delivery/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--upstream',type=Path,required=True)
    parser.add_argument('--ps2-assets',type=Path,required=True)
    parser.add_argument('--retail',type=Path,required=True)
    parser.add_argument('--build',action='store_true')
    parser.add_argument('--vehicle-config',type=Path)
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--game-root',type=Path)
    args=parser.parse_args();prepare(args.output,args.upstream,args.ps2_assets,args.retail,args.vehicle_config)
    if args.build:build(args.output)
    if args.candidate or args.game_root:
        if not args.candidate or not args.game_root or not args.build:parser.error('Candidate packaging requires --build, --candidate and --game-root')
        package_candidate(args.output,args.candidate,args.game_root,args.ps2_assets)
