"""Build a private, fail-closed F3/SDK binding DLL from verified local inputs."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_r_mod1_candidate import compiler_environment, locate_toolchain
from extra_options_sdk_binding import propose, render_header, write_proposal
from r_mod1_native_plan import (build_plan, public_plan, render_cpp_header,
                                make_challenge_preview_code, make_challenge_consumer_code)
from audit_dinput8_exports import audit


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(output, retail, sdk_manifest, runtime, sdk_root, *, checkpoint='f3', extra_header=None):
    output = Path(output).resolve()
    allowed = (ROOT / '.research-output/extra-set1').resolve()
    if not output.is_relative_to(allowed) or output == allowed or output.exists():
        raise ValueError('select a fresh private extra-set1 output directory')
    retail, sdk_manifest, runtime, sdk_root = map(Path, (retail, sdk_manifest, runtime, sdk_root))
    raw = retail.read_bytes()
    sdk = json.loads(sdk_manifest.read_text(encoding='utf-8'))
    plan = build_plan(raw, runtime.read_bytes(), checkpoint=checkpoint)
    public = public_plan(plan)
    # Reuse SDK's full file-backed preimage/overlap auditor before creating
    # any generated profile. It checks the current inputs, not filenames.
    sys.path.insert(0, str(sdk_root / 'tools'))
    spec = importlib.util.spec_from_file_location('sdk_composition_audit', sdk_root / 'tools/audit_runtime_composition.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    evidence = module.audit(raw, sdk, public)
    proposal = propose(sdk, public, make_challenge_preview_code(), make_challenge_consumer_code())
    if len(evidence['overlaps']) != 2 or len(proposal['sdk_checks']) < 1:
        raise ValueError('the verified SDK/F3 overlap set is not qualified')

    sdk_profile = json.loads((sdk_manifest.parent/'runtime-profile.json').read_text(encoding='utf-8'))
    ext = sdk_profile['native_extension']
    payload = (sdk_manifest.parent/'native-extension.bin').read_bytes()
    if len(payload) != ext['size'] or hashlib.sha256(payload).hexdigest() != ext['sha256']:
        raise ValueError('SDK extension payload differs from its existing runtime profile')
    ranges = ext.get('writable_ranges', [])
    if len(ranges) != 1:
        raise ValueError('SDK binding requires a single qualified writable region')
    rw = ranges[0]
    if (ext['address'] != 0x10000000 or ext['size'] > ext['allocation_size'] or
        rw['offset'] < 4096 or rw['size'] != 4096 or rw['offset'] + rw['size'] > len(payload)):
        raise ValueError('unsupported SDK extension layout')
    extension = {'address': ext['address'], 'size': ext['size'], 'rw_offset': rw['offset'],
                 'rw_size': rw['size'], 'code_sha256': hashlib.sha256(
                     payload[:rw['offset']] + payload[rw['offset']+rw['size']:]).hexdigest()}
    output.mkdir(parents=True)
    include = output / 'include'; include.mkdir()
    (include / 'native_plan.hpp').write_text(render_cpp_header(plan), encoding='ascii', newline='\n')
    (include / 'extra_sdk_profile.hpp').write_text(render_header(proposal, public, extension), encoding='ascii', newline='\n')
    if extra_header is not None:
        (include / 'extra_options_package.hpp').write_text(extra_header, encoding='ascii', newline='\n')
    proxy_def = output / 'extra_sdk_proxy.def'
    original_def = (ROOT/'src/native/rmod1/dinput8_proxy.def').read_text(encoding='ascii').rstrip()
    exports_extra = ('    MRExtraOptionsAbi=_MRExtraOptionsAbi@0 @8\n'
                     '    MRExtraVisualV1=_MRExtraVisualV1@12 @9\n'
                     '    MRExtraRevisionV1=_MRExtraRevisionV1@12 @10\n'
                     '    MRExtraTextureV1=_MRExtraTextureV1@36 @11\n'
                     '    MRExtraVisualV2=_MRExtraVisualV2@12 @12\n') if extra_header is not None else ''
    proxy_def.write_text(original_def + '\n    MRExtraSdkBindingAbi=_MRExtraSdkBindingAbi@0 @7\n' + exports_extra, encoding='ascii')
    write_proposal(output / 'binding-proposal.json', proposal)
    (output / 'preimage-audit.json').write_text(json.dumps(evidence, indent=2) + '\n')

    vcvars, msvc = locate_toolchain()
    env = compiler_environment(vcvars, 'x64_x86')
    compiler = msvc / 'bin/Hostx64/x86/cl.exe'
    dll = output / 'dinput8.dll'
    command = [str(compiler), '/nologo', '/LD', '/MT', '/EHsc', '/std:c++17', '/W4', '/WX',
               '/Brepro', '/O2', '/DNDEBUG', '/D_WIN32_WINNT=0x0601', '/DDIRECTINPUT_VERSION=0x0800',
               '/DRMOD_EXTRA_SDK_BINDING=1', '/I' + str(include), '/I' + str(ROOT/'src/native/rmod1'),
               str(ROOT/'src/native/rmod1/dinput8_proxy.cpp'), str(ROOT/'src/native/rmod1/rmod2_inprocess.cpp'),
               '/link', '/DEF:' + str(proxy_def),
               'bcrypt.lib', 'user32.lib', '/NOIMPLIB', '/Brepro', '/OUT:' + str(dll)]
    if extra_header is not None:
        command.insert(command.index('/link'), str(ROOT/'src/native/rmod1/extra_options_runtime.cpp'))
        command.insert(1, '/DRMOD_EXTRA_OPTIONS=1')
    subprocess.run(command, cwd=output, env=env, check=True)
    exports = audit(dll)
    if not exports.get('required_match') or exports['observed'].get('MRExtraSdkBindingAbi') != 7:
        raise ValueError('DirectInput export contract changed')
    result = {'schema': 'extra-options-sdk-binding-build/1', 'status': 'OFFLINE_ONLY',
              'sdk_manifest_sha256': sha(sdk_manifest), 'source_exe_sha256': sha(retail),
              'runtime_core_sha256': sha(runtime), 'private_dinput8_sha256': sha(dll),
              'sdk_operations_verified': len(proposal['sdk_checks']),
              'sdk_extension': extension,
              'composed_challenge_hooks': len(proposal['challenge']),
              'checkpoint': checkpoint, 'native_extra_options': extra_header is not None,
              'runtime_qualified': False, 'gameplay_qualified': False}
    (output / 'build-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'retail', 'sdk-manifest', 'runtime', 'sdk-root'):
        parser.add_argument('--' + name, type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(build(a.output, a.retail, a.sdk_manifest, a.runtime, a.sdk_root), indent=2))
