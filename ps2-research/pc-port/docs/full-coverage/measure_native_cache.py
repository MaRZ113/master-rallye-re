"""Measure existing private-input native tests; never opens or samples the game."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import time

PORT = Path(__file__).resolve().parents[2]


class Counters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in ('peak_working', 'working', 'peak_paged',
        'paged', 'peak_nonpaged', 'nonpaged', 'pagefile', 'peak_pagefile')]


def main():
    env = os.environ.copy()
    for key, filename in (('MRR_GRASS_TEST_ASSET', 'Turkey3Grass.ps2grass'),
                          ('MRR_SHRUB_TEST_ASSET', 'Turkey3Shrubs.ps2grass')):
        env[key] = str(PORT/'.assets/grass'/filename)
    env['MRR_GRASS_MULTI_DIRECTORY'] = str(PORT/'.assets/grass')
    api = ctypes.WinDLL('psapi', use_last_error=True).GetProcessMemoryInfo
    api.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    api.restype = wintypes.BOOL
    start = time.perf_counter()
    proc = subprocess.Popen([str(PORT/'.build/ps2-enabled/Release/ps2_grass_pilot_tests.exe')],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peak = 0
    while proc.poll() is None:
        value = Counters();value.cb = ctypes.sizeof(value)
        if api(wintypes.HANDLE(int(proc._handle)), ctypes.byref(value), value.cb):
            peak = max(peak, value.peak_working)
        time.sleep(.01)
    stdout, stderr = proc.communicate()
    report = {'schema_version': 1, 'evidence': 'NATIVE_TEST_PERFORMANCE_NOT_GAME_FPS',
              'elapsed_seconds': time.perf_counter()-start, 'sampled_peak_working_set_bytes': peak,
              'returncode': proc.returncode, 'stdout': stdout.decode(), 'stderr': stderr.decode(),
              'scope': 'All72 assets, category isolation,36course switches andReset in native mocks',
              'runtime_menu_race_fps': 'PENDING_USER', 'per_frame_disk_reads': 0}
    Path(__file__).with_name('native-cache-performance.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if proc.returncode:
        raise RuntimeError('Native cache test failed')


if __name__ == '__main__':
    main()
