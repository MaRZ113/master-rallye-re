"""COURSE-ALIVE1 source contracts and (when the private inputs exist) the full automatic verification."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
PATCH = (PORT / 'overlay/patches/0001-renderer-integration.patch').read_text(encoding='utf-8')
GENERATOR = (PORT / 'overlay/patches/0002-interface-generator.patch').read_text(encoding='utf-8')
CORE = (PORT / 'renderer/ps2_spline_motion.hpp').read_text(encoding='utf-8')
NATIVE = (PORT / 'renderer/spline_objects_native_integration.hpp').read_text(encoding='utf-8')
PILOT = (PORT / 'renderer/spline_objects.cpp').read_text(encoding='utf-8')


class SplineObjectsContracts(unittest.TestCase):
    def test_core_is_portable(self):
        # The controller must not depend on D3D, Windows or the modernization proxy.
        includes = [line for line in CORE.splitlines() if line.startswith('#include')]
        self.assertEqual(sorted(includes), sorted(['#include <array>', '#include <cmath>', '#include <cstddef>', '#include <cstdint>',
                                                   '#include <cstring>', '#include <optional>', '#include <vector>']))
        self.assertIn('kTickIncrement = 1.f / 30.f', CORE)
        self.assertIn('kTicksPerSecond = 50.0', CORE)
        self.assertIn('return {Vec3{f[2], f[1], -f[0]}, up, f, position};', CORE)

    def test_every_native_seam_is_wired(self):
        for call in ('splineintegration::observe_transform', 'splineintegration::before_ui', 'splineintegration::repair',
                     'spline_objects()->before_reset()', 'spline_objects()->after_reset', 'spline_objects()->shutdown()',
                     'splines.initialize(*real_)', '"${MRR_PS2_PORT_ROOT}/renderer/spline_objects.cpp"', 'ps2_spline_objects_contracts'):
            self.assertIn(call, PATCH, call)
        self.assertEqual(PATCH.count('splineintegration::observe_world_draw'), 3)
        # Proof resets in the generated forwarders come from the generator patch.
        self.assertEqual(GENERATOR.count('spline_objects()->proof'), 3)

    def test_stock_default_and_ini(self):
        self.assertIn('read_int(L"SplineObjects",0,', PILOT)
        ini = (PORT / 'PS2Port.ini.example').read_text(encoding='utf-8')
        self.assertIn('\nSplineObjects=0\n', ini)

    def test_course_guard_and_pause(self):
        self.assertIn('spline_course_guard', PILOT)
        self.assertIn('read_pause_menu_state_readonly()', NATIVE)
        self.assertIn('resolve_id(base,"Car0",car0_)', NATIVE)

    def test_full_verification(self):
        asset = PORT / '.assets/course/PS2SplineObjects.ps2spl'
        exe = PORT / '.build/ps2-enabled/Release/ps2_spline_objects_tests.exe'
        if not asset.exists() or not exe.exists() or not Path('D:/Game/Master Rallye PS2/TNG.000').exists():
            self.skipTest('NOT_PERFORMED: private asset, built test binary or PS2 corpus missing')
        r = subprocess.run([sys.executable, str(PORT / 'tools/verify_spline_objects.py')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-4000:] + r.stderr[-4000:])


if __name__ == '__main__':
    unittest.main()
