import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from gt_sound_jam import inspect, extract, resolve_events
from gt_sound_native_evidence import Elf32Image, qualify_core


def bank(mode=0xffffffff):
    raw = bytearray(256)
    raw[:4] = b'INST'
    struct.pack_into('<5I', raw, 4, 0, 224, 0, 32, 224)
    struct.pack_into('<3I', raw, 32, 192, 32, 0)
    raw[44:48] = b'SShd'
    struct.pack_into('<6i', raw, 48, 128, -1, -1, -1, -1, -1)
    struct.pack_into('<I', raw, 156, mode)
    struct.pack_into('<HH', raw, 160, 0, 4)
    raw[164:172] = bytes.fromhex('007f40000c7f000a')
    raw[172:188] = bytes.fromhex('007f3c0000000000ff80d05f7f400c7f')
    raw[224] = 12
    raw[225] = 1
    raw[240] = 12
    raw[241] = 1
    return raw


class JamTests(unittest.TestCase):
    def test_native_shift_switch_changes_source_offset(self):
        raw = bank()
        struct.pack_into('<H', raw, 178, 2)
        a = inspect(raw)
        self.assertEqual((a['ssa_address_shift'], a['entries'][0]['sample_file_offset']), (3, 240))
        struct.pack_into('<I', raw, 156, 0)
        b = inspect(raw)
        self.assertEqual(b['ssa_address_shift'], 4)
        self.assertEqual(b['entries'][0]['codec_status'], 'UNSUPPORTED')

    def test_direct_first_split_and_gaps(self):
        report = inspect(bank())
        events = resolve_events({3: report}, {'direct': 0x0300007f, 'missing': 0x0300013c,
                                            'sequence': 0x0301003c, 'bank': 0x0100003c})
        self.assertEqual([e['status'] for e in events], ['STATIC_DIRECT_FIRST_SPLIT', 'DIRECT_PROGRAM_ABSENT',
                                                      'SE_SEQUENCE_ROUTING_UNSUPPORTED', 'BANK_NOT_SUPPLIED'])
        self.assertEqual(events[0]['selection']['split'], 0)
        self.assertIsNone(events[0]['authentic_effect_identity'])

    def test_nominal_export_provenance_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.ins'
            output = Path(directory) / 'out.wav'
            source.write_bytes(bank())
            evidence = extract(source, output, 'program', 0, 0, 24000)
            self.assertEqual(output.read_bytes()[:4], b'RIFF')
            self.assertFalse(evidence['native_semantics']['runtime_pairing_confirmed'])
            self.assertIsNone(json.loads(output.with_suffix('.json').read_text())['authentic_effect_identity'])
            with self.assertRaisesRegex(ValueError, 'new WAV'):
                extract(source, output, 'program', 0, 0, 24000)
            with self.assertRaises(ValueError):
                extract(source, Path(directory) / 'bad.wav', 'program', 0, 0, None)

    def test_bad_header_and_pointer_rejected(self):
        for mutate in (lambda b: b.__setitem__(44, 0), lambda b: struct.pack_into('<i', b, 48, 0x100000)):
            raw = bank()
            mutate(raw)
            with self.assertRaises(ValueError):
                inspect(raw)

    def test_elf_mapping_and_foreign_hash(self):
        raw = bytearray(128)
        raw[:7] = b'\x7fELF\x01\x01\x01'
        struct.pack_into('<H', raw, 18, 8)
        struct.pack_into('<I', raw, 28, 52)
        struct.pack_into('<HH', raw, 42, 32, 1)
        struct.pack_into('<8I', raw, 52, 1, 100, 0x100000, 0, 4, 8, 5, 16)
        image = Elf32Image(raw)
        self.assertEqual(image.offset(0x100001, 3), 101)
        with self.assertRaises(ValueError):
            image.offset(0x100004, 1)
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            qualify_core(raw)


if __name__ == '__main__':
    unittest.main()
