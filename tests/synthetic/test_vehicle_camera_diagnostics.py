from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from vehicle_camera_diagnostics import extent_terms, camera_settings, verify


class CameraDiagnosticTests(unittest.TestCase):
    def test_native_extent_terms_do_not_depend_on_origin(self):
        a = extent_terms((-1, -.2, -2), (1, 1.3, 2.5))
        b = extent_terms((2, 2.8, 1), (4, 4.3, 5.5))
        self.assertEqual(a['half_length_m'], 2.25)
        self.assertAlmostEqual(a['height_m'], 1.5)
        self.assertAlmostEqual(a['height_m'], b['height_m'])

    def test_invalid_bounds_and_executable_rejected(self):
        for lo, hi in [((0, 0, 0), (0, -1, 0)), ((0, 0, 0), (0, float('nan'), 0)), ((0,), (0,))]:
            with self.assertRaises(ValueError): extent_terms(lo, hi)
        with self.assertRaises(ValueError): verify(b'not the original EXE')

    def test_native_setup_inventory_and_duplicate_rejection(self):
        raw = b'<Game><Broker><Value Name="Camera/Setup"><gaCameraManagerParams><Value Name="FollowCamera 0  Dist Up" Type="Float" Value="0.65"/></gaCameraManagerParams></Value></Broker></Game>'
        self.assertEqual(camera_settings(raw)['Camera/Setup']['FollowCamera 0  Dist Up']['value'], '0.65')
        with self.assertRaises(ValueError): camera_settings(raw.replace(b'</gaCameraManagerParams>', b'<Value Name="FollowCamera 0  Dist Up"/></gaCameraManagerParams>'))
        with self.assertRaises(ValueError): camera_settings(b'<!DOCTYPE x><Game/>')


if __name__ == '__main__': unittest.main()
