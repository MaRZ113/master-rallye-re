"""Synthetic format/codec tests; no Gran Turismo fixtures bundled."""
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from gt3_sound_lab import (_strings, _tables, decode_sample, inspect_bank, vehicle_mapping,
                           unpack_core, _pitch_word, _engn_pitch_word, _qualified_native_core)


def frames(loop=False, tail=True):
    data = bytes(16) + bytes([12, 6 if loop else 4]) + bytes([0x11] * 14)
    data += bytes([12, 3 if loop else 1]) + bytes(14)
    return data + (bytes.fromhex('0007' + '77' * 14) if tail else b'')


def engn(loop=False):
    data = frames(loop)
    raw = bytearray(64)
    raw[:4] = b'ENGN'
    struct.pack_into('<5I', raw, 4, 0, 64, 0, len(data), 64)
    struct.pack_into('<4I', raw, 24, 1, 48, 0, 0)
    struct.pack_into('<6HI', raw, 48, 800, 0, 800, 3741, 1633, 0, 0)
    return raw + data


def inst(loop=True, header_padding=4):
    data = frames(loop, False)
    raw = bytearray(76 + header_padding)
    raw[:4] = b'INST'
    struct.pack_into('<5I', raw, 4, 0, 76, 0, len(data), len(raw))
    struct.pack_into('<4I', raw, 24, 1, 40, 1, 64)
    raw[56:58] = bytes([60, 60])
    struct.pack_into('<I', raw, 64, 68)
    raw[68:72] = bytes([1, 64, 0, 64])
    raw[72] = 0
    return raw + data


class GT3SoundLabTests(unittest.TestCase):
    def test_pitch_octaves_rounding_and_unsigned_multiply(self):
        table = [16384] * 384
        self.assertEqual(_pitch_word(table, 60 << 8, 60 << 8), 4096)
        self.assertEqual(_pitch_word(table, 72 << 8, 60 << 8), 8192)
        self.assertEqual(_pitch_word(table, 48 << 8, 60 << 8), 2048)
        self.assertEqual(_engn_pitch_word(800, 1633, 800), 1633)
        self.assertEqual(_engn_pitch_word(800, 1633, 1600), 3266)
        self.assertEqual(_engn_pitch_word(800, 0, 800), 1)
        self.assertEqual(_engn_pitch_word(1, 0xffffffff, 2), 65534)
        with self.assertRaisesRegex(ValueError, 'zero'):
            _engn_pitch_word(0, 1, 800)

    def test_native_evidence_rejects_changed_source_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed_core.gt3'
            path.write_bytes(b'\x01\x01' + bytes(200))
            with self.assertRaisesRegex(ValueError, 'unqualified original GT3 CORE SHA256'):
                _qualified_native_core(path)

    def test_core_reconstruction_preserves_segment_addresses_and_bytes(self):
        payload = bytes(range(32))
        inflated = struct.pack('<H', 128) + bytes(128) + struct.pack('<H', 128) + bytes([1] * 128)
        inflated += struct.pack('<4I', 1, 0x100008, 0x100000, len(payload)) + payload
        compressed = zlib.compressobj(wbits=-15)
        packed = b'\x01\x01' + struct.pack('<I', len(inflated)) + compressed.compress(inflated) + compressed.flush()
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / 'core.gt3', Path(directory) / 'out.elf'
            source.write_bytes(packed)
            report = unpack_core(source, target)
            elf = target.read_bytes()
            self.assertEqual(elf[:4], b'\x7fELF')
            self.assertEqual(struct.unpack_from('<I', elf, 24)[0], 0x100008)
            self.assertEqual(report['rsa_status'], 'PRESENT_NOT_AUTHENTICATED')
            self.assertEqual(elf[4096:], payload)
            self.assertEqual(report['segments'][0]['inflated_offset'], 276)
            with self.assertRaisesRegex(ValueError, 'new reconstructed'):
                unpack_core(source, target)
            source.write_bytes(packed[:-2])
            with self.assertRaisesRegex(ValueError, 'inflate size/end'):
                unpack_core(source, Path(directory) / 'truncated.elf')

    def test_engn_one_shot_start_marker_is_not_loop(self):
        raw = engn()
        report = inspect_bank(raw)
        row = report['entries'][0]
        self.assertEqual(row['encoded_bytes'], 48)
        self.assertEqual(row['allocated_bytes'], 64)
        self.assertEqual(row['padding_bytes'], 16)
        self.assertEqual(row['samples'], 84)
        self.assertEqual(row['loop_start_marker_sample'], 28)
        self.assertIsNone(row['loop_start_sample'])
        self.assertIsNone(row['loop_end_sample'])
        pcm = decode_sample(raw, row)
        self.assertEqual(pcm, [0] * 28 + [1] * 28 + [0] * 28)

    def test_inst_program_voice_and_loop(self):
        report = inspect_bank(inst())
        row = report['entries'][0]
        self.assertEqual(report['programs'][0]['voice_indices'], [0])
        self.assertEqual(row['entry_id'], 'voice:0')
        self.assertEqual(row['sample_file_offset'], 80)
        self.assertEqual(row['loop_start_sample'], 28)
        self.assertEqual(row['loop_end_sample'], 84)
        self.assertEqual(row['note_window_raw'], [60, 60])

    def test_inst_ssa_scale_eight_and_alias(self):
        raw = bytearray(128)
        raw[:4] = b'INST'
        sample = frames(True, False)
        # Three voices, two samples, program indices [0,1,2].
        struct.pack_into('<5I', raw, 4, 0, 124, 0, len(sample) * 2, 128)
        struct.pack_into('<4I', raw, 24, 3, 40, 1, 112)
        struct.pack_into('<I', raw, 64, len(sample) // 8)
        struct.pack_into('<I', raw, 88, len(sample) // 8)
        struct.pack_into('<I', raw, 112, 116)
        raw[116:123] = bytes([3, 64, 0, 64, 0, 1, 2])
        report = inspect_bank(raw + sample * 2)
        self.assertEqual(report['unique_samples'], 2)
        rows = report['entries']
        self.assertEqual(rows[1]['sample_file_offset'], 176)
        self.assertEqual(rows[1]['encoded_sha256'], rows[2]['encoded_sha256'])

    def test_reject_malformed_program_and_unknown_format(self):
        raw = inst()
        raw[72] = 1
        with self.assertRaisesRegex(ValueError, 'voice/padding'):
            inspect_bank(raw)
        with self.assertRaisesRegex(ValueError, 'bounded GT3'):
            inspect_bank(b'JAM ' + bytes(100))

    def test_reject_stream_corruption_and_unexplained_tail(self):
        raw = engn()
        raw[64 + 16] = 0x50
        with self.assertRaisesRegex(ValueError, 'SPU frame'):
            inspect_bank(raw)
        raw = engn()
        raw[-1] = 0
        with self.assertRaisesRegex(ValueError, 'trailer'):
            inspect_bank(raw)
        raw = engn(True)
        raw[64 + 17] = 2
        with self.assertRaisesRegex(ValueError, 'without start'):
            inspect_bank(raw)

    def test_reject_out_of_range_ssa(self):
        raw = inst()
        struct.pack_into('<I', raw, 40, 0x1000)
        with self.assertRaisesRegex(ValueError, 'SSA outside'):
            inspect_bank(raw)

    def test_stdb_ascii_and_bounded_unknown_multibyte(self):
        raw = bytearray(b'STDB' + struct.pack('<IhhI', 1, -1, 0, 25))
        raw += struct.pack('<I', 20) + struct.pack('<H', 3) + b'A\x81B'
        self.assertEqual(_strings(raw), ['A\\x81B'])
        struct.pack_into('<I', raw, 16, 100)
        with self.assertRaisesRegex(ValueError, 'outside'):
            _strings(raw)

    def test_gtar_table_sizes_and_eof_checked(self):
        head = 168
        raw = bytearray(b'GTAR' + struct.pack('<3I', 36, head, 7))
        raw += struct.pack('<37I', *[i * 16 for i in range(37)])
        raw += bytes(head - len(raw))
        for i in range(36):
            raw += b'GTDT' + struct.pack('<HhHHI', 2087, i, 0, 8, 16)
        report = _tables(raw)
        self.assertEqual(len(report), 36)
        self.assertEqual(report[30]['row_size'], 8)
        raw[-1] = 1
        with self.assertRaisesRegex(ValueError, 'GTDT layout'):
            _tables(raw)

    def test_vehicle_mapping_follows_keys_with_shared_engine(self):
        def stdb(strings):
            head = 16 + len(strings) * 4
            pointers, body = [], bytearray()
            for value in strings:
                data = value.encode('ascii')
                pointers.append(head + len(body))
                body += struct.pack('<H', len(data)) + data
            return b'STDB' + struct.pack('<IhhI', len(strings), 1, 0, head + len(body)) + struct.pack('<' + 'I' * len(strings), *pointers) + body
        engines = []
        for key, owner, sound in ((0x201, 0x101, 21801), (0x202, 0x100, 22601)):
            row = bytearray(88)
            struct.pack_into('<QQ', row, 0, key, owner)
            struct.pack_into('<H', row, 22, sound)
            engines.append(row)
        cars = []
        for index, key, engine in ((0, 0x100, 0x202), (1, 0x101, 0x201), (2, 0x102, 0x202)):
            row = bytearray(264)
            struct.pack_into('<Q', row, 0, key)
            struct.pack_into('<Q', row, 56, engine)
            struct.pack_into('<3H', row, 228, 0, 1, index)
            struct.pack_into('<H', row, 260, 2)
            cars.append(row)
        blocks = []
        for i in range(36):
            rows = engines if i == 6 else cars if i == 30 else []
            size = 88 if i == 6 else 264 if i == 30 else 8
            payload = b''.join(rows)
            blocks.append(b'GTDT' + struct.pack('<HhHHI', 2087, i, len(rows), size, 16 + len(payload)) + payload)
        pointers = [0]
        for block in blocks:
            pointers.append(pointers[-1] + len(block))
        database = b'GTAR' + struct.pack('<3I', 36, 168, 7) + struct.pack('<37I', *pointers) + bytes(4) + b''.join(blocks)
        members = {'paramdb': database, '.id_db_str': stdb(['alpha', 'beta', 'shared', 'engine_b', 'engine_a']),
                   'paramstr': stdb(['alpha', 'beta', 'shared']), 'paramunistr': stdb(['Car', 'Name', 'Maker']),
                   '.id_db_idx': b'IDDB' + struct.pack('<I', 5) + b''.join(struct.pack('<Qq', k, j) for j, k in enumerate((0x100, 0x101, 0x102, 0x201, 0x202)))}
        def member(volume, name):
            data = members[name.split('/')[1].removesuffix('_us.db')]
            return data, {'path': name}
        with patch('gt3_sound_lab.read_member', side_effect=member):
            result = vehicle_mapping(Path('synthetic.vol'))
        self.assertEqual([r['sound_number'] for r in result['vehicles']], [22601, 21801, 22601])
        self.assertFalse(result['vehicles'][2]['engine_owner_matches_car'])
        self.assertEqual(result['vehicles'][2]['engine_owner_label'], 'alpha')


if __name__ == '__main__':
    unittest.main()
