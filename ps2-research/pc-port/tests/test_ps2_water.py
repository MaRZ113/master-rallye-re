"""COURSE-WATER1 source contracts and (when the private asset and the built test binary exist) the bit-for-bit comparison
of the C++ water core with tools/ps2_water_model.py over every vertex of the 36-course asset."""
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PORT / 'tools'))
import ps2_water_model as wm  # noqa: E402

PATCH = (PORT / 'overlay/patches/0001-renderer-integration.patch').read_text(encoding='utf-8')
CORE = (PORT / 'renderer/ps2_water.hpp').read_text(encoding='utf-8')
PILOT = (PORT / 'renderer/ps2_water_pilot.hpp').read_text(encoding='utf-8')
NATIVE = (PORT / 'renderer/ps2_water_native.hpp').read_text(encoding='utf-8')
OBJECTS = (PORT / 'renderer/course_objects_native_integration.hpp').read_text(encoding='utf-8')
ASSET = PORT / '.assets/course/PS2Water.ps2wtr'
EXE = PORT / '.build/ps2-enabled/Release/ps2_water_tests.exe'
COUNTERS = (0, 7615, 11056, 12287, 123457)
BASIS = ((0.75341, 0.19122), (0.00022, -0.95678), (-0.65726, 0.21924))


def read_asset(data):
    magic, version, textures, courses, keys, parts, vertices, _ = struct.unpack_from('<8s7I', data, 0)
    assert magic == b'PS2WTR01' and version == 1
    at = 36
    for _ in range(textures):
        w, h = struct.unpack_from('<2I', data, at)
        at += 8 + 4 * w * h
    at += courses * 60 + keys * 48
    part_rows = [struct.unpack_from('<6If', data, at + 28 * i) for i in range(parts)]
    at += parts * 28
    verts = [struct.unpack_from('<3f3f2f4B4f', data, at + 52 * i) for i in range(vertices)]
    assert at + 52 * vertices == len(data)
    return part_rows, verts


def gs_byte(b):
    return min(255, ((b >> 1) * 255 + 64) // 128)


def expected(part_rows, verts, counter):
    t = wm.phase(counter)
    for mode, _, _, _, first, count, first_y in part_rows:
        for v in verts[first:first + count]:
            pos, nrm, uv, rgba, water = v[0:3], v[3:6], v[6:8], v[8:12], v[12:16]
            if mode == 9:
                uvs = wm.puddle_uv(pos, nrm, t, BASIS)
            elif mode == 10:
                uvs = water
            else:
                p, s = wm.waterfall_v(pos[1], first_y, t)
                uvs = (uv[0], p, uv[0], s)
            color = (gs_byte(rgba[3]) << 24) | (gs_byte(rgba[0]) << 16) | (gs_byte(rgba[1]) << 8) | gs_byte(rgba[2])
            yield struct.pack('<4fI', *uvs, color)


class PS2WaterContracts(unittest.TestCase):
    def test_core_is_portable(self):
        includes = sorted(line for line in CORE.splitlines() if line.startswith('#include'))
        self.assertEqual(includes, sorted(['#include <algorithm>', '#include <array>', '#include <cmath>', '#include <cstddef>',
                                           '#include <cstdint>', '#include <cstring>', '#include <string>', '#include <string_view>',
                                           '#include <vector>']))
        for text in ('kPhaseDivisor = 150.f', 'kCountsPerSecond = 50.0', '0x40c90fdbu', 'z * 0.05f + w.b * 0.05f', 'x * 0.01f + w.a * 0.05f'):
            self.assertIn(text, CORE)

    def test_every_native_seam_is_wired(self):
        for call in ('waterintegration::draw(*this,type,min_index,vertices,start,count,pc)', 'waterintegration::repair(*this)',
                     'water()->before_reset()', 'water()->after_reset', 'water()->shutdown()', 'water.initialize(*real_)',
                     'ps2_water_contracts', '#include "ps2_water_native.hpp"'):
            self.assertIn(call, PATCH, call)
        self.assertEqual(PATCH.count('waterintegration::repair(*this)'), 2)
        # The water hook runs before every other replacement of course draws except the brake lamp (car only).
        self.assertLess(PATCH.index('waterintegration::draw('), PATCH.index('groundintegration::draw('))

    def test_stock_default_and_single_path(self):
        self.assertIn('read_int(L"PS2Water",0,', PILOT)
        ini = (PORT / 'PS2Port.ini.example').read_text(encoding='utf-8')
        self.assertIn('\nPS2Water=0\n', ini)
        # One rendering path: a matched native draw is not submitted; the PS2OBJ01 puddle preview yields to PS2Water.
        self.assertIn('return {true,S_OK};', NATIVE)
        self.assertIn('superseded_by_ps2_water', OBJECTS)
        self.assertIn('kPS2WaterArtifactSha', PILOT)

    def test_model_reference_values(self):
        self.assertEqual(wm.inline_int(-0.5), 0)
        self.assertEqual(wm.inline_int(-1.5), -2)
        self.assertEqual(wm.weight_byte(0.0), 2)
        self.assertEqual(wm.weight_byte(1000.0), 254)
        self.assertEqual(wm.weight_byte(0.5), int(wm.f32(wm.f32(1.0 - wm.f32(1.0 / 2.0)) * 255.0)))

    def test_cpp_equals_model_bit_for_bit(self):
        if not ASSET.exists() or not EXE.exists():
            self.skipTest('NOT_PERFORMED: private asset or built test binary missing')
        data = ASSET.read_bytes()
        part_rows, verts = read_asset(data)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'dump.bin'
            r = subprocess.run([str(EXE), '--dump', str(ASSET), str(out)] + [str(c) for c in COUNTERS], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            got = out.read_bytes()
        want = b''.join(b for c in COUNTERS for b in expected(part_rows, verts, c))
        self.assertEqual(len(got), len(want))
        mismatches = sum(1 for i in range(0, len(want), 20) if got[i:i + 20] != want[i:i + 20])
        self.assertEqual(mismatches, 0, f'{mismatches} of {len(want) // 20} vertex records differ')


if __name__ == '__main__':
    unittest.main()
