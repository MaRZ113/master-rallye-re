"""Compile and execute the production registry/AI callback without a game."""
import argparse,subprocess
from pathlib import Path
from build_r_mod1_candidate import ROOT,compiler_environment,locate_toolchain

def test(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    vc,msvc=locate_toolchain();env=compiler_environment(vc,'x64_x86');exe=output/'registry_ai_tests.exe'
    subprocess.run([str(msvc/'bin/Hostx64/x86/cl.exe'),'/nologo','/MT','/EHsc','/std:c++17','/W4','/WX','/O2',str(ROOT/'tests/rmod1/registry_ai_pool_tests.cpp'),'/link','user32.lib','advapi32.lib','/OUT:'+str(exe)],cwd=output,env=env,check=True)
    result=subprocess.run([str(exe)],capture_output=True,text=True)
    (output/'result.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('Registry AI test failed: '+str(result.returncode)+' '+result.stderr)
    print(result.stdout.strip())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();test(a.output)
