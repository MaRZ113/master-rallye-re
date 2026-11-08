"""Exercise production native-menu callbacks with an instrumented Broker ABI."""
import argparse
import subprocess
from pathlib import Path
from build_r_mod1_candidate import compiler_environment,locate_toolchain
from build_extra_options_candidate import ROOT,package_header

def test(output, core=None):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    header,_,_=package_header();(output/'extra_options_package.hpp').write_text(header)
    vc,msvc=locate_toolchain();env=compiler_environment(vc,'x64_x86')
    exe=output/'extra_native_tests.exe'
    subprocess.run([str(msvc/'bin/Hostx64/x86/cl.exe'),'/nologo','/MT','/EHsc','/std:c++17','/W4','/WX','/O2',
                    '/I'+str(output),str(ROOT/'tests/rmod1/extra_native_tests.cpp'),'/link','user32.lib','/OUT:'+str(exe)],
                   cwd=output,env=env,check=True)
    state=output/'state';state.mkdir()
    result=subprocess.run([str(exe),str(state)],capture_output=True,text=True)
    (output/'result.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    print(result.stdout.strip())
    if core is not None:
        provider=output/'extra_roster_tests.exe'
        subprocess.run([str(msvc/'bin/Hostx64/x86/cl.exe'),'/nologo','/MT','/EHsc','/std:c++17','/W4','/WX','/O2',
                        str(ROOT/'tests/rmod1/extra_roster_tests.cpp'),'/link','/OUT:'+str(provider)],cwd=output,env=env,check=True)
        result=subprocess.run([str(provider),str(Path(core).resolve())],capture_output=True,text=True)
        (output/'provider-result.log').write_text(result.stdout+result.stderr)
        if result.returncode:raise RuntimeError('provider test failed '+str(result.returncode)+' '+result.stdout+result.stderr)
        print(result.stdout.strip())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--core',type=Path);a=p.parse_args();test(a.output,a.core)
