"""Build R-AI1.2 x86 research DLL and native policy tests with installed MSVC."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from r_ai1_2_randomizer import build, bridge_ranges, ignored_output, sha256, REPOSITORY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--challenge-preview",action="store_true")
    a=p.parse_args();output=ignored_output(a.output);output.mkdir(parents=True,exist_ok=True)
    data=a.source.read_bytes()
    if a.challenge_preview:
        from r_ai1_2a_preview import build as candidate_build, preview_ranges
    else: candidate_build=build
    candidates=[candidate_build(data,five) for five in (False,True)]
    for five,(binary,manifest) in zip((False,True),candidates):
        dest=output/("five" if five else "four");dest.mkdir(exist_ok=True)
        (dest/"MRallye.exe").write_bytes(binary)
        (dest/"patch-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    # Live pinning of all policy bridge ranges, plus immutable builder entries.
    pins=[r for r in bridge_ranges() if r["va"] is not None]
    if a.challenge_preview:pins.extend(r for r in preview_ranges() if r["va"] is not None)
    for address in (0x458090,0x451DD0,0x45ABC0,0x44FEC0):
        pins.append({"va":address,"replacement":data[address-0x400000:address-0x400000+7]})
    text=['#pragma once',f'#define MR_FOUR_SHA "{candidates[0][1]["output_sha256"]}"',
          f'#define MR_FIVE_SHA "{candidates[1][1]["output_sha256"]}"',
          'struct MemoryPin {unsigned address,size;const unsigned char* bytes;};']
    for n,row in enumerate(pins):
        text.append(f'const unsigned char pin{n}[]={{'+','.join(str(b) for b in row["replacement"])+'};')
    text.append('const MemoryPin MR_MEMORY_PINS[]={'+','.join(
        '{'+f'{row["va"]},{len(row["replacement"])},pin{n}'+'}' for n,row in enumerate(pins))+'};')
    text.append(f'const unsigned MR_MEMORY_PIN_COUNT={len(pins)};')
    (output/"profiles.h").write_text('\n'.join(text)+'\n')
    program_files=os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)")
    finder=Path(program_files)/"Microsoft Visual Studio/Installer/vswhere.exe"
    root=subprocess.check_output([str(finder),"-latest","-products","*","-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],text=True).strip()
    vcvars=Path(root)/"VC/Auxiliary/Build/vcvarsall.bat"
    batch=output/"compiler-env.cmd"
    batch.write_text(f'@call "{vcvars}" x86 >nul\n@if errorlevel 1 exit /b 1\n@set\n')
    env_result=subprocess.run(["cmd.exe","/d","/c",str(batch)],capture_output=True,text=True)
    if env_result.returncode:raise RuntimeError(env_result.stdout+env_result.stderr)
    env=dict(os.environ)
    for line in env_result.stdout.splitlines():
        key,sep,value=line.partition("=")
        if sep and key:env[key]=value
    # The native command runner receives argument arrays, never constructed shell code.
    def run(args):
        r=subprocess.run(args,env=env,cwd=REPOSITORY,text=True,capture_output=True)
        with (output/"build.log").open("a",encoding="utf-8") as log:log.write(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        return r.stdout
    tool=Path(env["VCToolsInstallDir"])/"bin/Hostx64/x86"
    (output/"build.log").write_text("")
    run([str(tool/"cl.exe"),"/nologo","/c","/O2","/MT","/W4","/WX","/std:c++17",
         "/I"+str(output),"/Fo"+str(output/"runtime.obj"),str(REPOSITORY/("src/native/challenge_preview/runtime.cpp" if a.challenge_preview else "src/native/randomizer/runtime.cpp"))])
    run([str(tool/"link.exe"),"/nologo","/DLL","/MACHINE:X86","/INCREMENTAL:NO","/Brepro",
         "/OPT:REF","/OPT:ICF","/DEF:"+str(REPOSITORY/"src/native/randomizer/exports.def"),
         "/OUT:"+str(output/"MRallyeRandomizer.dll"),str(output/"runtime.obj"),"kernel32.lib","advapi32.lib"])
    run([str(tool/"cl.exe"),"/nologo","/O2","/MT","/W4","/WX","/std:c++17",
         "/Fo"+str(output/"policy-test.obj"),"/Fe"+str(output/"policy-test.exe"),
         str(REPOSITORY/"tests/native/randomizer_policy.cpp"),"/link","/INCREMENTAL:NO","/Brepro"])
    result=run([str(output/"policy-test.exe"),str(output/"MRallyeRandomizer.dll")])
    native=json.loads(result.strip().splitlines()[-1])
    (output/"native-policy-tests.json").write_text(json.dumps(native,indent=2)+"\n")
    preview_tests=None
    if a.challenge_preview:
        run([str(tool/"cl.exe"),"/nologo","/O2","/MT","/W4","/WX","/std:c++17",
             "/Fo"+str(output/"preview-test.obj"),"/Fe"+str(output/"preview-test.exe"),
             str(REPOSITORY/"tests/native/challenge_preview.cpp"),"/link","/INCREMENTAL:NO","/Brepro"])
        preview_tests=json.loads(run([str(output/"preview-test.exe")]).strip().splitlines()[-1])
        (output/"native-preview-tests.json").write_text(json.dumps(preview_tests,indent=2)+"\n")
    dll=output/"MRallyeRandomizer.dll"
    source_files=list((REPOSITORY/"src/native/randomizer").iterdir())
    if a.challenge_preview:source_files.extend((REPOSITORY/"src/native/challenge_preview").iterdir())
    report={"phase":"R-AI1.2a" if a.challenge_preview else "R-AI1.2","implementation_version":1,"module_sha256":sha256(dll.read_bytes()),
        "module_size":dll.stat().st_size,"compiler":env["VCToolsVersion"].strip("\\/"),
        "source_hashes":{str(file.relative_to(REPOSITORY)).replace("\\","/"):sha256(file.read_bytes())
                         for file in sorted(source_files)},
        "supported_profiles":[m for _,m in candidates],"native_policy_tests":native,
        "runtime_game_test":False}
    (output/"module-manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    if a.challenge_preview:
        report['native_preview_tests']=preview_tests
        (output/"module-manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    for variant in ("four","five"):
        dest=output/variant
        shutil.copyfile(dll,dest/dll.name)
        shutil.copyfile(output/"module-manifest.json",dest/"module-manifest.json")
        config=dest/"MRallyeRandomizer.ini"
        if not config.exists():
            shutil.copyfile(REPOSITORY/"research/r-ai1-2/MRallyeRandomizer.example.ini",config)
    for name in ("MRallyeRandomizer.example.ini","MRallyeRandomizer.stock.ini"):
        shutil.copyfile(REPOSITORY/"research/r-ai1-2"/name,output/name)
    print(json.dumps({k:v for k,v in report.items() if k!="supported_profiles"},indent=2))


if __name__=="__main__":main()
