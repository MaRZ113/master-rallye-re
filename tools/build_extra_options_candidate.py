"""Build one private Extra Options candidate on the installed G1 / SDK33 base."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from build_extra_sdk_binding import build as build_proxy
from build_r_mod1_candidate import compiler_environment, locate_toolchain

ROOT=Path(__file__).resolve().parents[1]
SDK=ROOT.parent/'master-rallye-re-vehicles'
GENERAL=ROOT.parent/'master-rallye-re-general/ps2-research/pc-port'
GAME=Path('D:/Game/Master Rallye Pristine')
BASE=SDK/'.research-output/vehicles/v-def4-1/delivery-final/32/workshop/builds/first/candidate'
RETAIL=ROOT.parent/'corpora/retail/MRallye.exe'
GHOST_FRONTEND=ROOT.parent/'DataScene/FrontendScreens/QuickModeSelect.xml'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def package_header(sdk_runtime=None):
    manifest=json.loads((ROOT/'research/extra-set1/vehicles.json').read_text())
    previous=SDK/'.research-output/vehicles/v-set1/pilot-07'
    evidence=json.loads((previous/'preparation.json').read_text())
    bindings=evidence['livery_bindings']
    rows=[]
    for v in manifest['vehicles']:
        if not 1<=len(v['labels'])<=3 or not 0<=v['native_paint']<len(v['labels']):raise ValueError('invalid appearance count or native index')
        labels=v['labels']+['']*(3-len(v['labels']))
        kind_ids={'PC_BUNDLE':1,'PS2_BUNDLE':2,'PS2_PC_TEXTURES':3}
        kinds=v.get('kinds',[])
        if len(kinds)!=len(v['labels']) or any(k not in kind_ids for k in kinds):raise ValueError('each appearance needs an explicit supported kind')
        if kinds[v['native_paint']]!='PC_BUNDLE':raise ValueError('native appearance must select PC_BUNDLE')
        codes=[kind_ids[k] for k in kinds]+[0]*(3-len(kinds))
        rows.append('{%d,%s,%d,%d,{%s},{%s}},'%(v['id'],json.dumps(v['family']),len(v['labels']),v['native_paint'],','.join(map(json.dumps,labels)),','.join(map(str,codes))))
    br=[]
    for b in bindings:
        br.append('{%d,%d,%d,%s,%s},'%(b['index'],b['width'],b['height'],json.dumps(b['base_path']),json.dumps(b['alternate_path'])))
    sys.path.insert(0,str(ROOT/'.research-output/extra-set1/python-tools'))
    import pefile
    pe=pefile.PE(str(RETAIL))
    apis=[]
    for va in [0x4d0580,0x4d8ec0,0x4d6760,0x4d6520,0x4d8000,0x4d85f0,0x4d8880,0x4d11d0,0x407b30,0x5c1cb4,0x5b4c00,
               0x4d6650,0x4d6fb0,0x45a3c0,0x4ada50,0x4ac660,0x4b0af0,0x4b0630,0x525a80,0x525800]:
        apis.append('{0x%x,{%s}},'%(va,','.join('0x%02x'%b for b in pe.get_data(va-0x400000,8))))
    runtime=Path(sdk_runtime) if sdk_runtime is not None else BASE/'runtime'
    plan=json.loads((runtime/'addon-plan.json').read_text())
    native=json.loads((runtime/'native-patch-manifest.json').read_text())
    sdk_rows=[]
    modes=['quick_race','rallye_cup','master_rallye','invitation','challenge']
    for item in plan['addons']:
        mask=sum((1<<i) for i,m in enumerate(modes) if item['ai_eligibility'].get(m,{}).get('enabled',False))
        sdk_rows.append('{%d,%d,%d},'%(item['physical_id'],['T1','T2','T3'].index(item['vehicle_class']),mask))
    layout=plan['registry_layout']
    human_offset=layout['race_test_base']+layout['race_test_stride']-8
    header=('#pragma once\n#include <cstring>\n#include <array>\n#include "sdk_roster_abi.hpp"\nnamespace extra_package {\n'
            'struct Vehicle {int id;const char* family;unsigned paint_count,native_paint;const char* paint_labels[3];unsigned paint_kinds[3];};\n'
            'inline constexpr Vehicle vehicles[]={'+''.join(rows)+'};\n'
            'inline bool family_enabled(const char* family){for(const auto& v:vehicles)if(!_stricmp(v.family,family))return true;return false;}\n'
            'struct Binding {unsigned index,width,height;const char* original;const char* derived;};\n'
            'inline constexpr Binding bindings[]={'+''.join(br)+'};\n'
            'inline constexpr unsigned binding_count=sizeof(bindings)/sizeof(bindings[0]);\n}\n')
    header=header[:-2]+'inline constexpr rmod1::SdkVehicleV1 sdk_vehicles[]={'+''.join(sdk_rows)+'};\ninline constexpr unsigned challenge_human_offset='+str(human_offset)+';\nstruct API {uintptr_t va;std::array<unsigned char,8> bytes;};\ninline constexpr API apis[]={'+''.join(apis)+'};\n}\n'
    return header,previous,manifest


def graphics_inputs():
    """Current reviewed inputs, never a persistent staging snapshot."""
    repo=GENERAL.parents[1]
    paths=[GENERAL/'overlay/build_overlay.py',GENERAL/'overlay/baseline-lock.json']
    paths+=list((GENERAL/'overlay/patches').glob('*.patch'))
    for folder in ('renderer','tests'):
        paths += [p for p in (GENERAL/folder).rglob('*') if p.is_file() and p.suffix in ('.cpp','.hpp','.py','.def')]
    return {'general_head': subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
            'files': {str(p.relative_to(repo)).replace(chr(92),'/'):sha(p) for p in sorted(paths)}}


def stage_graphics(out):
    # Capture identities only. The canonical overlay assembles fresh immutable
    # renderer + current port inputs and owns staging/build validation.
    source=out/'graphics-source';source.mkdir()
    (source/'inputs.json').write_text(json.dumps(graphics_inputs(),indent=2)+'\n')
    return source


def build_graphics(out):
    snapshot=json.loads((out/'graphics-source/inputs.json').read_text())
    if snapshot!=graphics_inputs():raise ValueError('graphics inputs changed after source capture')
    with (out/'graphics-build.log').open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,str(GENERAL/'overlay/build_overlay.py')],cwd=GENERAL.parents[1],
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    if snapshot!=graphics_inputs():raise ValueError('graphics inputs changed during build')
    report_path=GENERAL/'dist/current/build-report.json'
    report=json.loads(report_path.read_text())
    for relative,digest in report['ps2_source_sha256'].items():
        if digest!=sha(GENERAL/relative):raise ValueError('compiled port input differs: '+relative)
    built=GENERAL.parents[1]/report['builds']['ps2-enabled']['dll']
    if sha(built)!=report['builds']['ps2-enabled']['dll_sha256']:raise ValueError('built renderer hash mismatch')
    shutil.copyfile(built,out/'d3d8.dll')
    shutil.copyfile(report_path,out/'graphics-build-manifest.json')
    shutil.copyfile(GENERAL/'.build/logs/ps2-enabled-ctest.log',out/'graphics-tests.log')


def package(out):
    sys.path.insert(0,str(SDK/'tools'))
    import addon_runtime
    from build_runtime_launcher import build_launcher
    delivery=SDK/'.research-output/vehicles/extra-set2'/out.name
    if delivery.exists():raise ValueError('private delivery already exists')
    # Verify the accepted bundle before deriving only the native frontend XML.
    original_check=subprocess.run([str(BASE/'launcher/mr-runtime-launcher.exe'),'--verify',str(RETAIL),str(BASE/'runtime')],capture_output=True,text=True,check=True)
    delivery.mkdir(parents=True);host=delivery/'host';host.mkdir()
    def clone(src,dst):
        source=Path(src)
        if 'resource-root' in source.parts and source.name.lower() not in ('playerstate.xml','options.xml'):
            os.link(src,dst)
        else:shutil.copyfile(src,dst)
        return dst
    bundle=delivery/'runtime';shutil.copytree(BASE/'runtime',bundle,copy_function=clone)
    sys.path.insert(0,str(SDK/'src'))
    # EXTRA-SET2: GENERAL tyre row + Vehicle Select MODEL row; GEARBOX stays stock.
    # Ghost Mode needs the GHOST panel QuickModeSelect.xml (GHOST1 G4.1, owner-confirmed).
    import extra_set2_frontend,extra_set2_resources
    pages=extra_set2_frontend.build(GAME/'Data.sma_unpacked',bundle/'resource-root')
    pages['DataScene/FrontendScreens/QuickModeSelect.xml']=GHOST_FRONTEND.read_bytes()
    extension=extra_set2_resources.extend_bundle(bundle,pages,stock_archive=ROOT.parent/'Data.sma',
                                                 stock_loose=ROOT.parent/'Data.sma_unpacked',sdk_tools=addon_runtime)
    def verify():
        if (bundle/'native-patch-manifest.json').read_bytes()!=(BASE/'runtime/native-patch-manifest.json').read_bytes():raise ValueError('roster plan changed')
        if (bundle/'native-extension.bin').read_bytes()!=(BASE/'runtime/native-extension.bin').read_bytes():raise ValueError('SDK code changed')
        manifest=json.loads((bundle/'resource-manifest.json').read_text())
        for r in manifest['resources']:
            p=bundle/'resource-root'/r['path']
            if p.stat().st_size!=r['size'] or sha(p)!=r['sha256']:raise ValueError('derived resource mismatch '+r['path'])
        return {'status':'PASS_STATIC_COLLECTION_RUNTIME_BUNDLE','runtime_qualified':False}
    build_launcher(bundle=bundle,output=delivery/'launcher',retail_exe=RETAIL,bundle_verifier=verify,sdk_binding_input=True)
    for src,name in [(RETAIL,'MRallye.exe'),(out/'proxy/dinput8.dll','dinput8.dll'),(out/'d3d8.dll','d3d8.dll'),(out/'core/MRallyeRandomizerRuntime.dll','MRallyeRandomizerRuntime.dll')]:
        shutil.copyfile(src,host/name)
    _,previous,_=package_header();shutil.copytree(previous/'VSETAssets',host/'VSETAssets')
    for name in ('MRallyeRandomizer.ini','MRRRenderer.ini','PS2Port.ini'):shutil.copyfile(GAME/name,host/name)
    renderer=(host/'MRRRenderer.ini').read_text(encoding='utf-8-sig')
    import re
    renderer=re.sub(r'(?ms)(\[Display\]\r?\n(?:(?!\n\[).)*?^Mode=)\d+',r'\g<1>2',renderer)
    (host/'MRRRenderer.ini').write_text(renderer,encoding='utf-8')
    # Preserve the owner's legacy Randomizer INI byte-for-byte. A documented
    # comparison profile can be selected explicitly, not silently migrated.
    text=(host/'PS2Port.ini').read_text(encoding='utf-8-sig')
    for key,folder in [('RaceModelAssetDirectory','PS2Vehicles'),('FrontendModelAssetDirectory','PS2Vehicles'),('PS2HudAssetDir','PS2Hud'),('GrassAssetDirectory','PS2Grass')]:
        text=re.sub(r'(?m)^'+key+r'=.*$',lambda _:key+'='+str(GAME/folder),text)
    text=re.sub(r'(?m)^BrakeGlowAsset=.*$',lambda _:'BrakeGlowAsset='+str(GAME/'PS2Grass/PS2BrakeGlow.gxi'),text)
    text=re.sub(r'(?m)^GroundDetailAsset=.*$',lambda _:'GroundDetailAsset='+str(GAME/'PS2Grass/PS2GroundNoise.gxi'),text)
    # Like the other PS2 assets, the environment map belongs to the original
    # local asset directory, not the isolated candidate's empty host folder.
    text=re.sub(r'(?m)^ReflectionSourceGXI=.*$',lambda _:'ReflectionSourceGXI='+str(GAME/'PS2Grass/PS2EnvSource64x64.gxi'),text)
    (host/'PS2Port.ini').write_text(text,encoding='utf-8')
    (host/'MRallyeExtraOptions.ini').write_text('[General]\nConfigVersion=1\n\n[Customization]\nEnabled=1\nLiveries=1\nTires=1\n'
                                                '\n[Ghost]\nEnabled=1\nWithOpponents=0\nRecordAllModes=0\nUseAlphaModel=1\n\n[Difficulty]\nLevels=5\n')
    launch='@echo off\r\n"%~dp0launcher\\mr-runtime-launcher.exe" --integrated "%~dp0host\\MRallye.exe" "%~dp0runtime"\r\nif errorlevel 1 pause\r\n'
    (delivery/'Launch-Extra-Options.cmd').write_bytes(launch.encode('ascii'))
    check=subprocess.run([str(delivery/'launcher/mr-runtime-launcher.exe'),'--preflight-sdk-binding',str(host/'MRallye.exe'),str(bundle)],capture_output=True,text=True)
    (delivery/'preflight.log').write_text(check.stdout+check.stderr)
    if check.returncode:raise ValueError('suspended preflight failed')
    report={'status':'OWNER_TEST_CANDIDATE','g1_runtime_unchanged':sha(host/'MRallyeRandomizerRuntime.dll')==sha(GAME/'MRallyeRandomizerRuntime.dll'),
            'legacy_ini_unchanged':(host/'MRallyeRandomizer.ini').read_bytes()==(GAME/'MRallyeRandomizer.ini').read_bytes(),
            'source_sdk_preflight':original_check.stdout,'extension':extension,'installed_files_written':[],
            'launch':str(delivery/'Launch-Extra-Options.cmd'),'owner_gameplay':'PENDING'}
    (delivery/'candidate.json').write_text(json.dumps(report,indent=2)+'\n')
    return delivery


def build(name, *, graphics=True):
    if not name.replace('-','').isalnum():raise ValueError('simple candidate name required')
    out=ROOT/'.research-output/extra-set1'/name
    if out.exists():raise ValueError('use a fresh candidate name')
    out.mkdir(parents=True)
    released=ROOT/'.research-output/r-mod3/g1/first-integrated-candidate-g1/package'
    # Qualification evidence only: identify the actual installed G1, not F3.
    baseline={n:{'installed':sha(GAME/n),'g1_package':sha(released/n)} for n in ('dinput8.dll','MRallyeRandomizerRuntime.dll')}
    installed_g1_identified=all(x['installed']==x['g1_package'] for x in baseline.values())
    header,previous,manifest=package_header()
    core=build_core(out)
    proof=build_proxy(out/'proxy',RETAIL,BASE/'runtime/native-patch-manifest.json',core,SDK,
                      checkpoint='g1',extra_header=header)
    stage_graphics(out)
    if graphics:build_graphics(out)
    (out/'integration.json').write_text(json.dumps({'g1':baseline,'installed_g1_identified':installed_g1_identified,
                                                  'proxy':proof,'visual_manifest':manifest},indent=2)+'\n')
    return out


def build_core(out):
    work=out/'core';work.mkdir()
    definition=work/'runtime.def'
    definition.write_text((ROOT/'src/native/rmod1/runtime_core.def').read_text().rstrip()+'\n    MRRegisterSdkRosterV1=_MRRegisterSdkRosterV1@4\n')
    vcvars,msvc=locate_toolchain();env=compiler_environment(vcvars,'x64_x86')
    dll=work/'MRallyeRandomizerRuntime.dll'
    subprocess.run([str(msvc/'bin/Hostx64/x86/cl.exe'),'/nologo','/LD','/MT','/EHsc','/std:c++17','/W4','/WX','/Brepro','/O2','/DNDEBUG',
                    '/DRMOD_EXTRA_OPTIONS=1','/DRMOD3_G1_DUPLICATE_REPEAT_FALLBACK=1',str(ROOT/'src/native/rmod1/runtime_core.cpp'),
                    '/link','/DEF:'+str(definition),'user32.lib','advapi32.lib','/Brepro','/OUT:'+str(dll)],cwd=work,env=env,check=True)
    return dll


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    parser.add_argument('--no-graphics-build',action='store_true')
    parser.add_argument('--package',action='store_true')
    args=parser.parse_args();out=build(args.name,graphics=not args.no_graphics_build)
    print(package(out) if args.package else out)
