"""Compact original-byte evidence checks; not native physics validation."""
import hashlib
import json
import os
from pathlib import Path
import struct
import unittest

EVIDENCE = json.loads(Path(__file__).with_name('admission-evidence.json').read_text())
PROBES = {p['role']: p for p in EVIDENCE['instruction_probes']}

def relative_call(probe):
    data = bytes.fromhex(probe['hex'])
    if len(data) != 5 or data[0] != 0xE8:
        raise ValueError('expected complete original CALL rel32')
    return int(probe['va'], 16) + 5 + struct.unpack_from('<i', data, 1)[0]

class AdmissionEvidenceTests(unittest.TestCase):
    def test_short_probes_are_self_consistent(self):
        for probe in PROBES.values():
            data = bytes.fromhex(probe['hex'])
            self.assertEqual(len(data), probe['length'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), probe['sha256'])
            self.assertLessEqual(len(data), 64)

    def test_loader_requires_pc_format(self):
        self.assertEqual(bytes.fromhex(PROBES['loader_magic']['hex']), bytes.fromhex('817c24180dd00000'))
        self.assertEqual(bytes.fromhex(PROBES['loader_revision']['hex']), bytes.fromhex('817c241c87000000'))
        self.assertEqual(bytes.fromhex(PROBES['extension']['hex']), b'.dx\0')
        self.assertNotEqual(EVIDENCE['format']['revision'], EVIDENCE['format']['ps2_psm_revision'])

    def test_selected_original_calls(self):
        self.assertEqual(relative_call(PROBES['cache_loader_call']), 0x551430)
        self.assertEqual(relative_call(PROBES['convex_reader_call']), 0x57CE60)
        self.assertEqual(relative_call(PROBES['body_admission_call']), 0x43E2A0)
        self.assertEqual(bytes.fromhex(PROBES['prototype_store']['hex']), bytes.fromhex('89700c'))

    def test_authored_hay_is_not_private_tumbleweed(self):
        self.assertEqual(bytes.fromhex(PROBES['stock_model']['hex']), b'Misc/Haybale/haybaletest\0')
        self.assertEqual(EVIDENCE['initializer']['private_model_parameter'], 'NOT_PROVED')
        self.assertNotEqual(EVIDENCE['initializer']['mass'], 5)
        self.assertEqual(bytes.fromhex(PROBES['factory_pointer']['hex']), struct.pack('<I', 0x4C9C60))

    def test_decision_retains_every_safety_blocker(self):
        self.assertEqual(EVIDENCE['decision'], 'NO_GO')
        self.assertEqual(EVIDENCE['runtime'], 'NOT_PERFORMED')
        self.assertEqual(EVIDENCE['isolated_authored_copy'], 'NOT_CREATED')
        self.assertEqual(len(EVIDENCE['functions']), 6)
        self.assertEqual(len(EVIDENCE['missing_contracts']), 6)

    def test_optional_original_executable(self):
        path = os.environ.get('MRR_ORIGINAL_EXE')
        if not path:
            self.skipTest('MRR_ORIGINAL_EXE not provided; compact evidence checks still run')
        data = Path(path).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), EVIDENCE['binary_sha256'])
        for probe in PROBES.values():
            offset = probe['file_offset']
            self.assertEqual(data[offset:offset+probe['length']], bytes.fromhex(probe['hex']))

if __name__ == '__main__':
    unittest.main()
