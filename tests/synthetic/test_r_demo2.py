from __future__ import annotations

import struct
import unittest

from master_rallye.demo_dx import compare_demo_dx, inspect_demo_dx
from master_rallye.errors import FormatError
from tools.runtime.demo_procmon_extract import extract_events


def demo_dx(position_x: float = 1.0, *, local_index: int = 0,
            draw_word: int = 22) -> bytes:
    return (struct.pack('<4I', 0xD00D, 131, 1337, 1)
            + struct.pack('<3f', position_x, 0, 0)
            + struct.pack('<3f', 0, 0, 1)
            + bytes((255, 128, 0, 255))
            + struct.pack('<I', 0)  # no UV sets
            + struct.pack('<I3H', 3, local_index, 0, 0)
            + struct.pack('<2I', 1, draw_word)  # raw demo draw envelope
            + struct.pack('<5I', 1, 3, 0, 0, 0))


class DemoDxComparatorTests(unittest.TestCase):
    def test_byte_identity_and_float_drift(self):
        first = demo_dx()
        self.assertEqual(inspect_demo_dx(first).header, (0xD00D, 131, 1337, 1))
        self.assertEqual(compare_demo_dx(first, first)['verdict'], 'BYTE_IDENTICAL')
        changed = demo_dx(1.0000001192092896)
        report = compare_demo_dx(first, changed)
        self.assertEqual(report['verdict'], 'SEMANTICALLY_EQUIVALENT_WITH_FLOAT_DRIFT')
        self.assertEqual(report['positions']['changed_vertices'], 1)

    def test_topology_or_unknown_draw_change(self):
        first = demo_dx()
        self.assertEqual(compare_demo_dx(first, demo_dx(local_index=1))['verdict'],
                         'STRUCTURALLY_DIFFERENT')
        self.assertEqual(compare_demo_dx(first, demo_dx(draw_word=23))['verdict'],
                         'UNRESOLVED')
        self.assertEqual(compare_demo_dx(first, demo_dx(position_x=1.25))['verdict'],
                         'UNRESOLVED')

    def test_procmon_extract_exact_resource_and_pid(self):
        rows = ('Time of Day,Process Name,PID,Operation,Path,Result,Detail\n'
                '12:00:00,MRallye.exe,42,CreateFile,C:\\Scratch\\complete.gxm,SUCCESS,read\n'
                '12:00:01,MRallye.exe,42,WriteFile,C:\\Scratch\\complete.dx,SUCCESS,4096 bytes\n'
                '12:00:02,other.exe,42,ReadFile,C:\\Scratch\\complete.dx,SUCCESS,noise\n'
                '12:00:03,MRallye.exe,43,ReadFile,C:\\Scratch\\complete.dx,SUCCESS,other run\n')
        events = extract_events(rows, 'complete.', 42)
        self.assertEqual([event['operation'] for event in events], ['CreateFile', 'WriteFile'])
        self.assertEqual(events[1]['result'], 'SUCCESS')
        with self.assertRaises(ValueError):
            extract_events('Operation,Path\nReadFile,a\n', 'complete.')

    def test_fail_closed_on_unsupported_boundary(self):
        with self.assertRaises(FormatError):
            inspect_demo_dx(demo_dx()[:-4], 'truncated')


if __name__ == '__main__':
    unittest.main()
