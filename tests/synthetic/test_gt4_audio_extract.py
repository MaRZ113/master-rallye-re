"""Synthetic only: no GT4 banks, rows or audio samples are bundled."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('gt4_audio_extract', ROOT / 'tools/gt4_audio_extract.py')
audio = importlib.util.module_from_spec(spec); spec.loader.exec_module(audio)


def block(header=12, flags=0, payload=0x21):
    return bytes([header, flags]) + bytes([payload]) * 14


def bank():
    body = block(flags=6) + block(flags=3)
    header = struct.pack('<4s11I', b'ENGN', 0, 64, 0, len(body), 64, 1, 48, 0, 0, 127, 127)
    return header + struct.pack('<6HI', 1000, 0, 32767, 123, 456, 0, 0) + body


def table(row_id, data):
    return struct.pack('<4sHHII', b'GTDB', 0, 0, 1, len(data)) + struct.pack('<II', row_id, 0) + data


def labels(row_id, label):
    text = label.encode() + b'\0'
    return struct.pack('<4sIII', b'GTID', 1, 0, 0) + struct.pack('<II', 0, row_id) + struct.pack('<H', len(text)) + text


class Gt4AudioExtractTests(unittest.TestCase):
    def test_source_key_mapping_not_same_named_engine_guess(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            generic = bytearray(24); struct.pack_into('<ii', generic, 0, 17, 36)
            parts = bytearray(208); struct.pack_into('<ii', parts, 88, 82, 12)
            engine = bytearray(113); struct.pack_into('<H', engine, 24, 9876)
            for name, rowid, raw in [('GENERIC_CAR', 3, generic), ('DEFAULT_PARTS', 17, parts), ('ENGINE', 82, engine)]:
                (p / (name + '.dbt')).write_bytes(table(rowid, raw))
            (p / 'GENERIC_CAR.idi').write_bytes(labels(3, 'synthetic_car'))
            result = audio.mapping(p, 'synthetic_car')
            self.assertEqual(result['sound_number'], 9876)
            self.assertEqual(result['rows']['ENGINE']['row_id'], 82)
            struct.pack_into('<i', parts, 92, 13)
            (p / 'DEFAULT_PARTS.dbt').write_bytes(table(17, parts))
            with self.assertRaisesRegex(ValueError, 'Engine reference'):
                audio.mapping(p, 'synthetic_car')

    def test_engn_structural_ranges_and_raw_words(self):
        result = audio.parse_engn(bank())
        self.assertEqual(result['entries'][0]['words_u16'], [1000, 0, 32767, 123, 456, 0])
        self.assertEqual(result['entries'][0]['loop_start_sample'], 0)
        self.assertEqual(result['entries'][0]['loop_end_sample'], 56)
        for offset, value in [(4, 1), (8, 48), (12, 1), (16, 31), (20, 32), (24, 99), (28, 32), (60, 1)]:
            altered = bytearray(bank()); struct.pack_into('<I', altered, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                audio.parse_engn(bytes(altered))

    def test_spu_sign_nibble_order_and_loop_flags(self):
        result = audio.decode_spu(block(flags=6, payload=0x8F) + block(flags=3, payload=0x21))
        self.assertEqual(result['samples'][:4], [-1, -8, -1, -8])
        self.assertEqual(result['samples'][-4:], [1, 2, 1, 2])
        self.assertEqual(result['loop_end_sample'], 56)
        result = audio.decode_spu(block(flags=1, payload=0))
        self.assertIsNone(result['loop_start_sample'])
        result = audio.decode_spu(block(flags=7, payload=0x77))
        self.assertEqual(result['samples'], [0] * 28)
        self.assertIsNone(result['loop_start_sample'])
        for invalid in [b'', b'bad', block(flags=0), block(flags=1) + block(flags=1),
                        block(header=0x50, flags=1), block(header=0x0D, flags=1),
                        block(flags=8), block(flags=6) + block(flags=1),
                        block(flags=6) + block(flags=6) + block(flags=3)]:
            with self.subTest(data=invalid[:2]), self.assertRaises(ValueError):
                audio.decode_spu(invalid)

    def test_predictor_and_saturation(self):
        data = block(header=0, payload=0x77) + block(header=0x10, flags=1, payload=0x77)
        decoded = audio.decode_spu(data)['samples']
        self.assertEqual(decoded[0], 28672)
        self.assertEqual(decoded[-1], 32767)

    def test_wav_loop_and_explicit_rate(self):
        raw = audio.pcm_wav([1, 2, 3, 4], 22050, (1, 4))
        self.assertEqual(raw[:4], b'RIFF')
        at = raw.index(b'smpl')
        self.assertEqual(struct.unpack_from('<II', raw, at + 8 + 36 + 8), (1, 3))
        for invalid in [0, 7999, 96001, True, 22050.0]:
            with self.assertRaises(ValueError): audio.pcm_wav([0], invalid)
        with self.assertRaises(ValueError): audio.pcm_wav([0], 22050, (0, 2))

    def test_extraction_is_lossless_nominal_rate_declared_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); source = p / 'synthetic.engn'; source.write_bytes(bank())
            out = p / 'out'; result = audio.extract(source, out, 22050)
            self.assertIn('not recovered', result['playback_rate_provenance'])
            self.assertEqual(source.read_bytes(), bank())
            with wave.open(str(out / 'table0-band00-loop.wav'), 'rb') as wav:
                self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()), (1, 2, 22050, 56))
                self.assertEqual(struct.unpack('<4h', wav.readframes(4)), (1, 2, 1, 2))
            self.assertEqual(json.loads((out / 'bank.json').read_text())['sha256'], audio.sha256(bank()))
            with self.assertRaises(ValueError): audio.extract(source, out, 22050)

    def test_native_pitch_requires_pinned_core_and_exact_instruction_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); core = p / 'synthetic.elf'
            raw = bytearray(0x6400); raw[:4] = b'\x7fELF'
            struct.pack_into('<I', raw, 28, 52); struct.pack_into('<H', raw, 44, 1)
            struct.pack_into('<8I', raw, 52, 1, 0x100, 0x532000, 0, 0x6300, 0x6300, 7, 4)
            for address, value in {0x532a84:'0800a38c',0x532a88:'0000a284',0x532a8c:'18186600',
                                   0x532a98:'1b006200',0x532b80:'06002585',0x538100:'9400a294'}.items():
                raw[0x100 + address - 0x532000:0x104 + address - 0x532000] = bytes.fromhex(value)
            core.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'CORE hash'): audio.pitch_core_evidence(core)
            original = audio.QUALIFIED_CORE_SHA256
            try:
                audio.QUALIFIED_CORE_SHA256 = audio.sha256(raw)
                source = bytearray(bank()); struct.pack_into('<I', source, 56, 1024)
                (p/'source.engn').write_bytes(source)
                report = audio.extract(p/'source.engn', p/'decoded', pitch_core=core)
                self.assertEqual(report['entries'][0]['sample_rate_hz'], 12000)
                self.assertEqual(report['entries'][0]['reference_rpm'], 1000)
                raw[0x100 + 0x532a84 - 0x532000] ^= 1; core.write_bytes(raw)
                audio.QUALIFIED_CORE_SHA256 = audio.sha256(raw)
                with self.assertRaisesRegex(ValueError, 'byte mismatch'): audio.pitch_core_evidence(core)
            finally:
                audio.QUALIFIED_CORE_SHA256 = original


if __name__ == '__main__': unittest.main()
