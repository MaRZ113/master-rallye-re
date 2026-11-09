"""Prepare four private owner-test hosts; never install or run the game."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import addon_runtime as runtime
import addon_collection_runtime as collection


def sha(path):return runtime.sha256_file(path)


def package(candidate,extra,renderer_host):
    candidate=collection._safe_root(Path(candidate),'private registry candidate');extra=Path(extra);renderer_host=Path(renderer_host)
    if not candidate.is_relative_to((ROOT/'.research-output/vehicles/v-cap2').resolve()):raise ValueError('Private hosts must remain inside this V-CAP2 output root')
    profile=json.loads((candidate/'runtime/runtime-profile.json').read_text())
    config=json.loads((candidate/'registry-build.json').read_text())
    built=json.loads((extra/'capacity-build.json').read_text())
    if built['sdk_binding']['sdk_manifest_sha256']!=profile['native_patch_manifest_sha256']:raise ValueError('Extra Options was compiled for a different composite SDK')
    for name,digest in built['files'].items():
        if sha(extra/name)!=digest:raise ValueError('Extra Options compiled artifact changed')
    if any((candidate/name).exists() for name in ('host-sdk','host-input','host-renderer','host-both')):raise ValueError('Host outputs already exist')
    exe=Path(config['retail_exe'])
    if sha(exe)!=profile['retail_exe']['sha256']:raise ValueError('Source executable changed')
    rows={}
    for name in ('host-sdk','host-input','host-renderer','host-both'):
        host=candidate/name;host.mkdir();shutil.copyfile(exe,host/'MRallye.exe')
        if name in ('host-renderer','host-both'):
            for item in renderer_host.iterdir():
                if item.is_dir():
                    if item.name=='VSETAssets' and name=='host-renderer':continue
                    collection._safe_root(item,'accepted private Renderer assets')
                    shutil.copytree(item,host/item.name,ignore=shutil.ignore_patterns('*.log','logs','*.state.ini'))
                elif item.suffix.lower()=='.ini' and not item.name.endswith('.state.ini'):
                    shutil.copyfile(item,host/item.name)
            shutil.copyfile(renderer_host/'d3d8.dll',host/'d3d8.dll')
        if name in ('host-input','host-both'):
            shutil.copyfile(extra/'proxy/dinput8.dll',host/'dinput8.dll')
            shutil.copyfile(extra/'core/MRallyeRandomizerRuntime.dll',host/'MRallyeRandomizerRuntime.dll')
            for item in ('MRallyeExtraOptions.ini','MRallyeRandomizer.ini'):
                if (renderer_host/item).exists():shutil.copyfile(renderer_host/item,host/item)
            if not (host/'VSETAssets').exists() and (renderer_host/'VSETAssets').exists():shutil.copytree(renderer_host/'VSETAssets',host/'VSETAssets')
        rows[name]={p.name:sha(p) for p in host.iterdir() if p.is_file() and p.suffix.lower() in ('.exe','.dll')}
        command='@echo off\r\n"%~dp0launcher\\mr-runtime-launcher.exe" --integrated "%~dp0'+name+'\\MRallye.exe" "%~dp0runtime"\r\nif errorlevel 1 pause\r\n'
        (candidate/('Launch-'+name.removeprefix('host-')+'.cmd')).write_text(command,newline='')
    report={'schema':'mr-vehicle-registry-private-hosts/1','sdk_manifest_sha256':profile['native_patch_manifest_sha256'],'extra_options_build':str(extra.resolve()),'renderer_source_host':str(renderer_host.resolve()),'hosts':rows,'game_launched':False,'working_installations_modified':False,'qualification':'PREPARED_ONLY; run suspended preflights and owner gameplay separately'}
    (candidate/'private-hosts.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','extra','renderer-host'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(package(a.candidate,a.extra,a.renderer_host),indent=2))
