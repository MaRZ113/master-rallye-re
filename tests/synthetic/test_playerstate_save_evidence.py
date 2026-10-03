"""Synthetic evidence tooling tests; none claims a game persistence round trip."""
import importlib.util
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('playerstate_save_evidence', ROOT/'tools/scanner/playerstate_save_evidence.py')
evidence_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence_tool)


def image():
    data = bytearray(0x400)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 0x80)
    data[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<HH', data, 0x84, 0x14c, 1)
    struct.pack_into('<H', data, 0x94, 0xe0)
    struct.pack_into('<H', data, 0x98, 0x10b)
    struct.pack_into('<I', data, 0xb4, 0x400000)
    section = 0x178
    struct.pack_into('<III', data, section+12, 0x1000, 0x200, 0x200)
    struct.pack_into('<I', data, section+36, 0x20000000)
    return data


class PlayerStateEvidenceTests(unittest.TestCase):
    def test_file_backed_va_mapping(self):
        base, sections = evidence_tool.image_layout(image())
        self.assertEqual(base, 0x400000)
        self.assertEqual(evidence_tool.va_offset(0x401010, sections, 5), 0x210)
        with self.assertRaises(ValueError):
            evidence_tool.va_offset(0x4011ff, sections, 2)

    def test_truncated_section_fails(self):
        with self.assertRaises(ValueError):
            evidence_tool.image_layout(image()[:0x300])

    def test_direct_call_census_is_executable_section_only(self):
        data = image()
        data[0x210] = 0xe8
        struct.pack_into('<i', data, 0x211, 0x402000-0x401015)
        _, sections = evidence_tool.image_layout(data)
        self.assertEqual(evidence_tool.direct_calls(data, sections, 0x402000), {0x401010})
        sections = [(va, offset, length, False) for va, offset, length, _ in sections]
        self.assertEqual(evidence_tool.direct_calls(data, sections, 0x402000), set())

    def test_census_counts_and_historical_boundary_correction(self):
        evidence = json.loads(evidence_tool.EVIDENCE.read_text(encoding='utf-8'))
        rows = {row['call_va']: row for row in evidence['calls']}
        self.assertEqual(len(rows), 26)
        self.assertEqual(sum(row['mode'] == 3 for row in rows.values()), 20)
        self.assertEqual(rows['005B0505']['mode'], 2)
        self.assertEqual(rows['005B0505']['owner_va'], '005B03D0')
        self.assertEqual(rows['005B0526']['mode'], 3)

    def test_runtime_and_planned_evidence_are_separate(self):
        evidence = json.loads(evidence_tool.EVIDENCE.read_text(encoding='utf-8'))
        self.assertFalse(evidence['u3']['full_pass'])
        self.assertEqual(evidence['u3']['automatic_persistence'], 'NOT_OBSERVED')
        self.assertFalse(evidence['player_name']['selector_is_edited_text'])
        self.assertFalse(evidence['shutdown']['dedicated_playerstate_save'])
        self.assertTrue((evidence_tool.EVIDENCE.parent/evidence['next_test']).is_file())
