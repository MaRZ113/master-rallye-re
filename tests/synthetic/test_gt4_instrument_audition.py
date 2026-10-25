import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from gt4_instrument_audition import inspect, extract


def fixture():
    raw = bytearray(272)
    raw[:4] = b'INST'
    struct.pack_into('<5I', raw, 4, 0, 256, 0, 16, 256)
    struct.pack_into('<3I', raw, 32, 224, 16, 0)
    raw[44:48] = b'SShd'
    struct.pack_into('<6i', raw, 48, 48, -1, -1, -1, -1, -1)
    struct.pack_into('<2h', raw, 80, 0, 8)
    raw[88:96] = bytes((0, 100, 0, 0, 0, 127, 0, 127))
    raw[96:100] = bytes((0, 127, 60, 0))
    raw[256:258] = bytes((12, 1))
    return raw


class InstrumentTests(unittest.TestCase):
    def test_recovered_record_and_pcm(self):
        entry = inspect(fixture())['entries'][0]
        self.assertEqual((entry['program'], entry['samples'], entry['encoded_bytes']), (0, 28, 16))
        self.assertEqual(entry['codec_status'], 'PCM_VALID')

    def test_incompatible_gt3_and_bad_pointer_rejected(self):
        raw = fixture(); raw[44:48] = b'xxxx'
        with self.assertRaises(ValueError): inspect(raw)
        raw = fixture(); struct.pack_into('<h', raw, 82, 32767)
        with self.assertRaises(ValueError): inspect(raw)

    def test_unsupported_ssa_accounted_not_exported(self):
        raw = fixture(); raw[101] = 255
        self.assertEqual(inspect(raw)['entries'][0]['codec_status'], 'UNSUPPORTED')
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / 'bank'; src.write_bytes(raw)
            with self.assertRaises(ValueError): extract(src, Path(folder) / 'bad.wav', 'program', 0, 0, 48000)

    def test_explicit_rate_export_provenance_no_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / 'bank'; src.write_bytes(fixture())
            out = Path(folder) / 'sample.wav'
            evidence = extract(src, out, 'program', 0, 0, 24000)
            self.assertTrue(out.read_bytes().startswith(b'RIFF'))
            self.assertIsNone(evidence['authentic_effect_identity'])
            self.assertEqual(json.loads(out.with_suffix('.json').read_text())['sample_rate'], 24000)
            with self.assertRaises(ValueError): extract(src, out, 'program', 0, 0, 24000)


if __name__ == '__main__': unittest.main()
