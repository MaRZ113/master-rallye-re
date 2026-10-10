"""Build/test the Win32 proxy; normalize case-duplicate Windows environment keys."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def normalized_environment(environment):
    return {key.upper(): value for key, value in environment.items()}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cmake', default=shutil.which('cmake') or 'cmake')
    ap.add_argument('--generator', default='Visual Studio 18 2026')
    ap.add_argument('--build-dir', type=Path, default=ROOT/'.build-msvc')
    ap.add_argument('--diagnostic-no-message-hooks', action='store_true', help='R-OBS1 isolation DLL only, not a shipping INI feature')
    a = ap.parse_args()
    out = a.build_dir.resolve()
    if not out.is_relative_to(ROOT) or not out.name.startswith('.build'):
        raise ValueError('Build directory must be an ignored .build* inside this phase')
    env = normalized_environment(os.environ)
    commands = [[a.cmake,'-S',str(ROOT),'-B',str(out),'-G',a.generator,'-A','Win32','-DBUILD_TESTING=ON',
                 '-DMRR_DIAGNOSTIC_NO_MESSAGE_HOOKS='+('ON' if a.diagnostic_no_message_hooks else 'OFF')],
                [a.cmake,'--build',str(out),'--config','Release','--parallel','4'],
                [a.cmake,'--build',str(out),'--config','Release','--target','RUN_TESTS']]
    for cmd in commands:
        subprocess.run(cmd, env=env, check=True)

if __name__ == '__main__':
    main()
