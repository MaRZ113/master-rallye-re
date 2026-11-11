"""Exercise the compiled binding helpers in an owned Windows x86 process."""
import argparse
import subprocess
from pathlib import Path
from build_r_mod1_candidate import locate_toolchain, compiler_environment

ROOT = Path(__file__).resolve().parents[1]


def test(build, sdk_bundle):
    build = Path(build).resolve()
    allowed = (ROOT/'.research-output/extra-set1').resolve()
    if not build.is_relative_to(allowed) or not (build/'dinput8.dll').is_file():
        raise ValueError('select a completed private extra-set1 build')
    out = build/'validation'
    if out.exists():
        raise ValueError('validation output already exists')
    out.mkdir()
    include = out/'include'; include.mkdir()
    native = (build/'include/native_plan.hpp').read_text()
    profile = (build/'include/extra_sdk_profile.hpp').read_text()
    if native.count('kImageBase = 0x00400000u') != 1 or profile.count('extension_va = 0x10000000u') != 1:
        raise ValueError('test relocation markers differ')
    (include/'native_plan.hpp').write_text(native.replace('kImageBase = 0x00400000u', 'kImageBase = 0x20000000u'))
    (include/'extra_sdk_profile.hpp').write_text(profile.replace('extension_va = 0x10000000u', 'extension_va = 0x30000000u'))
    vc, msvc = locate_toolchain(); env = compiler_environment(vc, 'x64_x86')
    compiler = msvc/'bin/Hostx64/x86/cl.exe'
    common = [str(compiler), '/nologo', '/MT', '/EHsc', '/std:c++17', '/W4', '/WX', '/O2',
              '/D_WIN32_WINNT=0x0601', '/I'+str(include), '/I'+str(ROOT/'src/native/rmod1')]
    profile_exe = out/'profile-harness.exe'
    subprocess.run(common + [str(ROOT/'tests/rmod1/extra_sdk_profile_harness.cpp'), '/link',
                   'bcrypt.lib', 'user32.lib', '/BASE:0x14000000', '/DYNAMICBASE:NO', '/FIXED',
                   '/OUT:'+str(profile_exe)], cwd=out, env=env, check=True)
    subprocess.run([str(profile_exe), str(Path(sdk_bundle).resolve()/'native-extension.bin')],
                   cwd=out, check=True)
    forward_exe = out/'forward-harness.exe'
    subprocess.run(common + ['/DDIRECTINPUT_VERSION=0x0800', str(ROOT/'tests/rmod1/dinput8_forward_harness.cpp'),
                   '/link', '/SUBSYSTEM:CONSOLE', '/OUT:'+str(forward_exe)], cwd=out, env=env, check=True)
    p = subprocess.run([str(forward_exe), str(build/'dinput8.dll')], cwd=out, capture_output=True, text=True, check=True)
    (out/'forwarding.log').write_text(p.stdout+p.stderr)
    if 'DINPUT8_FORWARD_PASS' not in p.stdout:
        raise ValueError('DirectInput forwarding harness did not report success')
    print(p.stdout.strip())


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--sdk-bundle', type=Path, required=True)
    a = p.parse_args(); test(a.build, a.sdk_bundle)
