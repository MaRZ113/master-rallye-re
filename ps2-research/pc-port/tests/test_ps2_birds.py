"""COURSE-ALIVE2 source contracts and (when the private inputs exist) the full automatic verification."""
import subprocess
import sys
import unittest
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
PATCH = (PORT / 'overlay/patches/0001-renderer-integration.patch').read_text(encoding='utf-8')
GENERATOR = (PORT / 'overlay/patches/0002-interface-generator.patch').read_text(encoding='utf-8')
CORE = (PORT / 'renderer/ps2_birds.hpp').read_text(encoding='utf-8')
PILOT = (PORT / 'renderer/ps2_birds_pilot.cpp').read_text(encoding='utf-8')
NATIVE = (PORT / 'renderer/ps2_birds_native_integration.hpp').read_text(encoding='utf-8')


class BirdContracts(unittest.TestCase):
    def test_core_is_portable(self):
        includes = sorted(line for line in CORE.splitlines() if line.startswith('#include'))
        self.assertEqual(includes, sorted(['#include <array>', '#include <cmath>', '#include <cstddef>', '#include <cstdint>', '#include <vector>']))
        for token in ('kPool = 16', 'kSeed = 12345', 'kScale = 0.1f', 'return config_.gate() || (ignore_gate_ && config_.flight_present);',
                      '* 48271u', '* 3399u', 'pending_.insert(pending_.begin(), e)', 'pending_.back()', 'free_.back()'):
            self.assertIn(token, CORE, token)

    def test_every_native_seam_is_wired(self):
        for call in ('birdsintegration::observe_transform', 'birdsintegration::before_ui', 'birdsintegration::repair',
                     'birds()->before_reset()', 'birds()->after_reset', 'birds()->shutdown()', 'birds.initialize(*real_)',
                     '"${MRR_PS2_PORT_ROOT}/renderer/ps2_birds_pilot.cpp"', 'ps2_birds_contracts'):
            self.assertIn(call, PATCH, call)
        self.assertEqual(PATCH.count('birdsintegration::observe_world_draw'), 4)
        self.assertEqual(GENERATOR.count('birds()->proof'), 3)
        # birds are drawn after the spline objects (transparent last)
        self.assertLess(PATCH.index('splineintegration::before_ui'), PATCH.index('birdsintegration::before_ui'))

    def test_material_is_the_ps2_sprite_state(self):
        self.assertIn('CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,TRUE,', NATIVE)   # no Z write, clamp, blend
        self.assertIn('read_pause_menu_state_readonly()', NATIVE)

    def test_stock_default(self):
        self.assertIn('read_int(L"PS2Birds",0,', PILOT)
        ini = (PORT / 'PS2Port.ini.example').read_text(encoding='utf-8')
        for key in ('\nPS2Birds=0\n', '\nPS2BirdsIgnoreListGate=0\n', '\nPS2BirdsStockCourses=0\n'):
            self.assertIn(key, ini)

    def test_full_verification(self):
        asset = PORT / '.assets/course/PS2Birds.ps2bird'
        exe = PORT / '.build/ps2-enabled/Release/ps2_birds_tests.exe'
        if not asset.exists() or not exe.exists() or not Path('D:/Game/Master Rallye PS2/TNG.000').exists():
            self.skipTest('NOT_PERFORMED: private asset, built test binary or PS2 corpus missing')
        r = subprocess.run([sys.executable, str(PORT / 'tools/verify_ps2_birds.py')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-4000:] + r.stderr[-4000:])


if __name__ == '__main__':
    unittest.main()
