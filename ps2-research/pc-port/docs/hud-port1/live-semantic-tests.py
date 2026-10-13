import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location('hud_live', Path(__file__).with_name('live-semantic-probe.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Memory:
    def __init__(self):
        self.data = {}; self.changed = False
    def put(self, address, *values):
        self.data[address] = struct.pack('<' + 'I' * len(values), *values)
    def read(self, address, size):
        raw = self.data.get(address)
        if raw is None or len(raw) != size:
            raise m.probe.ProbeError('Synthetic unreadable pointer')
        if self.changed and address == 0x10004:
            self.data[address] = struct.pack('<4I', 0, 0, 0, 0)
        return raw

class LiveSemanticTests(unittest.TestCase):
    def fixture(self):
        memory = Memory()
        memory.put(0x10004, 0x20000, 0, 0, 0)
        memory.put(0x20000, m.VTABLE)
        memory.put(0x1004C, 0x30000)
        memory.put(0x30008, 0x40000)
        memory.put(0x30068, 1)
        return memory, {0x10000: {'identity': (0x30000, 0x40000, 1, 3), 'draws': []}}
    def test_exact_class_candidate(self):
        memory, selected = self.fixture()
        candidates = m.observe(memory, selected)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['slot'], 0)
    def test_different_class_rejected(self):
        memory, selected = self.fixture(); memory.put(0x20000, 0x690000)
        self.assertEqual(m.observe(memory, selected), [])
    def test_changed_owner_rejected(self):
        memory, selected = self.fixture(); memory.changed = True
        with self.assertRaises(m.probe.ProbeError): m.observe(memory, selected)
    def test_changed_packet_rejected(self):
        memory, selected = self.fixture(); memory.put(0x1004C, 0x30004)
        with self.assertRaises(m.probe.ProbeError): m.observe(memory, selected)
    def test_unknown_storage_rejected(self):
        memory, selected = self.fixture(); memory.put(0x30008, 0x50000)
        with self.assertRaises(m.probe.ProbeError): m.observe(memory, selected)
    def test_multiple_class_candidates_rejected(self):
        memory, selected = self.fixture()
        memory.put(0x10004, 0x20000, 0x20004, 0, 0); memory.put(0x20004, m.VTABLE)
        with self.assertRaises(m.probe.ProbeError): m.observe(memory, selected)
    def frame_fixture(self):
        draw = dict(identity_status='validated_current', identity_field_mask=31, frame=9,
                    race_lifecycle_generation=2, draw_callsite_rva=0x16D7C4, fvf=0x142,
                    forwarded=True, suppressed=False, native_entity_pointer=0x10000,
                    native_packet_pointer=0x30000, observed_packet_pointer=0x30000,
                    point_storage=0x30054, content_storage=0x40000, packet_mode=1, ui_epoch=3)
        ownership = dict(complete=True, overflow=False, record_drops=0, draw_records=[draw])
        return [dict(type='frame_begin', exe_sha256=m.probe.EXE_SHA, frame=9, device=1,
                     ui_margins={'ui_ownership_probe': ownership}),
                dict(type='race_epoch_snapshot', live_certificate_valid=True, frame=9,
                     race_lifecycle_generation=2)]
    def test_current_complete_roster(self):
        self.assertEqual(len(m.roster(self.frame_fixture(), 1)[2]), 1)
    def test_stale_generation(self):
        rows = self.frame_fixture(); rows[1]['race_lifecycle_generation'] = 3
        with self.assertRaises(m.probe.ProbeError): m.roster(rows, 1)
    def test_suppressed_hud(self):
        rows = self.frame_fixture(); rows[0]['ui_margins']['ui_ownership_probe']['draw_records'][0]['suppressed'] = True
        with self.assertRaises(m.probe.ProbeError): m.roster(rows, 1)
    def test_overflow_capture(self):
        rows = self.frame_fixture(); rows[0]['ui_margins']['ui_ownership_probe']['overflow'] = True
        with self.assertRaises(m.probe.ProbeError): m.roster(rows, 1)
    def test_unknown_race_context(self):
        rows = self.frame_fixture(); rows[1]['live_certificate_valid'] = False
        with self.assertRaises(m.probe.ProbeError): m.roster(rows, 1)
    def test_missing_complete_frame(self):
        with self.assertRaises(m.probe.ProbeError): m.roster([], 1)
    def test_wrong_executable(self):
        with self.assertRaises(m.probe.ProbeError): m.roster([{'type':'frame_begin', 'exe_sha256':'wrong'}], 1)

if __name__ == '__main__':
    unittest.main()
