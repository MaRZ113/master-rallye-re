"""Exercise production SDK snapshot/readback over multiple mutable pages."""
import argparse
import shutil
import subprocess
from pathlib import Path
from build_r_mod1_candidate import compiler_environment,locate_toolchain
from build_extra_options_candidate import ROOT
from extra_options_sdk_binding import render_header


def test(output,native_plan):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(native_plan,output/'native_plan.hpp')
    proposal={'schema':'extra-options-sdk-binding/1','runtime_qualified':False,
              'sdk_checks':[{'rva':0,'expected_hex':'4d5a'}],
              'challenge':[{'id':identity,'rva':0,'expected_mapped_hex':'8bbc38e0060000'}
                           for identity in ('challenge-preview-identity','challenge-race-consume')]}
    plan={'code_symbols':{'challenge_preview':0x70002800,'challenge_consumer':0x70002a80}}
    extension={'address':0x10000000,'size':24576,'code_sha256':'0'*64,
               'writable_ranges':[{'offset':4096,'size':4096},{'offset':16384,'size':4096}]}
    (output/'extra_sdk_profile.hpp').write_text(render_header(proposal,plan,extension))
    vc,msvc=locate_toolchain();env=compiler_environment(vc,'x64_x86');exe=output/'sdk_regions.exe'
    subprocess.run([str(msvc/'bin/Hostx64/x86/cl.exe'),'/nologo','/MT','/EHsc','/std:c++17','/W4','/WX','/O2',
                    '/I'+str(output),str(ROOT/'tests/rmod1/extra_sdk_regions_tests.cpp'),
                    '/link','/DYNAMICBASE:NO','user32.lib','bcrypt.lib','/OUT:'+str(exe)],cwd=output,env=env,check=True)
    result=subprocess.run([str(exe)],capture_output=True,text=True)
    (output/'result.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('SDK regions test failed: '+str(result.returncode)+' '+result.stderr)
    print(result.stdout.strip())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--native-plan',type=Path,required=True)
    a=p.parse_args();test(a.output,a.native_plan)
