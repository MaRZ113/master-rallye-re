"""Build a standalone synthetic D3D8 capture probe in the existing build root."""
from pathlib import Path
import hashlib
import json
import subprocess

PORT = Path(__file__).resolve().parents[3]
ROOT = PORT.parents[1]


def main():
    renderer = PORT/'.staging/ps2-enabled/modernization/renderer'
    output = PORT/'.build/tmp'
    output.mkdir(exist_ok=True)
    vs = Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvarsall.bat')
    if not vs.is_file():
        raise RuntimeError('Expected installed Win32 MSVC environment is unavailable')
    source = Path(__file__).with_name('native-smoke.cpp')
    executable = output/'native-msaa-smoke.exe'
    includes = [renderer/'include', renderer/'vendor/d3d8', PORT/'renderer']
    command = f'call "{vs}" x86 >nul && cl /nologo /EHsc /std:c++17 /O2 '
    command += ' '.join(f'/I"{p}"' for p in includes)
    command += f' "{source}" "{PORT / "renderer/reflection_capture.cpp"}" /Fe:"{executable}" /link user32.lib uuid.lib'
    build = subprocess.run(['cmd.exe', '/d', '/q'], input=command+'\nexit /b %errorlevel%\n',
                           cwd=output, capture_output=True, text=True)
    (output/'native-msaa-smoke-build.log').write_text(build.stdout+build.stderr)
    build.check_returncode()
    probe = subprocess.run([str(executable)], cwd=output, capture_output=True, text=True, timeout=60)
    rows = [json.loads(line) for line in probe.stdout.splitlines() if line.startswith('{')]
    successful = [r for r in rows if r.get('capture_hr') == 0]
    for row in successful:
        if row['samples'] != row['actual_source_samples'] or row['readback_hr'] != 0:
            raise RuntimeError('Successful capture lacks exact sample count or output readback proof')
        reference = next(r for r in successful if r['samples'] == 0 and r['precision16'] == row['precision16'])
        if row['center_pixel_raw'] != reference['center_pixel_raw']:
            raise RuntimeError('Uniform synthetic resolved color differs from non-MSAA control')
    native_dll = Path('C:/Windows/SysWOW64/d3d8.dll')
    report = {'schema_version': 1, 'evidence': 'CONFIRMED_BY_NATIVE_API_NOT_GAME_RUNTIME',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
              'returncode': probe.returncode, 'stderr': probe.stderr, 'cases': rows,
              'native_d3d8_sha256': hashlib.sha256(native_dll.read_bytes()).hexdigest(),
              'successful_cases': len(successful),
              'output_color_matches_non_msaa_control': True if successful else None,
              'synthetic_input': True, 'game_access': False, 'hidden_own_window': True}
    Path(__file__).with_name('native-smoke-results.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    probe.check_returncode()


if __name__ == '__main__':
    main()
