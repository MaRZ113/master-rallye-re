import json
import struct
import unittest
import audit_trio as a


def fixture():
    points = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)]
    vb = b''.join(struct.pack('<3fI2f', *p, 0xffffffff, 0., 1.) for p in points)
    ib = struct.pack('<3H', 7, 8, 9)
    row = dict(node=0, mesh=0x10000, material_vector=0x20000, material=0x30000,
               fvf=0x142, stride=24, vertices=3, triangles=1, min=7, index_format=101,
               vb_generation=1, ib_generation=2, vb_revision=3, ib_revision=4,
               offset=0, vertex_bytes=len(vb), index_bytes=len(ib))
    metadata = dict(schema=1, family='KiaSportage', exe_sha256=a.EXE, proxy_sha256='a' * 64,
                    instance=0x40000, packet=0x50000, model=0x60000, frame=3,
                    private_tree=False, world_le_hex=struct.pack('<16f', *([1., 0., 0., 0.] * 4)).hex(),
                    records=[row])
    return metadata, vb + ib


def pack(metadata, raw):
    encoded = json.dumps(metadata).encode()
    return b'FDCAR001' + struct.pack('<II', len(encoded), len(raw)) + encoded + raw


class CaptureAuditTests(unittest.TestCase):
    def test_exact_normalized_stream_and_positions(self):
        metadata, raw = fixture()
        parsed, rows = a.parse_bytes(pack(metadata, raw))
        self.assertEqual(rows[0]['positions'], [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)])
        uv = b''.join(struct.pack('<2f', 0., 1.) for _ in range(3))
        self.assertEqual(rows[0]['uv_winding'], a.sha(uv + struct.pack('<3I', 0, 1, 2)))
        self.assertFalse(parsed['private_tree'])

    def test_fail_closed_malformed_capture(self):
        metadata, raw = fixture()
        data = pack(metadata, raw)
        for bad in (data[:-1], data + b'\0', b'X' + data[1:]):
            with self.assertRaises(ValueError):
                a.parse_bytes(bad)
        for key, value in (('offset', 1), ('stride', 36), ('index_format', 0), ('vb_revision', 0)):
            m, r = fixture()
            m['records'][0][key] = value
            with self.assertRaises(ValueError):
                a.parse_bytes(pack(m, r))
        with self.assertRaises(ValueError):
            a.parse_bytes(pack(metadata, raw[:-6] + struct.pack('<3H', 6, 8, 9)))
        m, r = fixture()
        m['records'].append(dict(m['records'][0]))
        with self.assertRaises(ValueError):
            a.parse_bytes(pack(m, r + r))

    def test_duplicate_json_and_nonfinite_rejected(self):
        metadata, raw = fixture()
        encoded = json.dumps(metadata).encode().replace(b'"schema": 1', b'"schema": 1,"schema": 1')
        data = b'FDCAR001' + struct.pack('<II', len(encoded), len(raw)) + encoded + raw
        with self.assertRaises(ValueError):
            a.parse_bytes(data)
        invalid = bytearray(raw)
        struct.pack_into('<f', invalid, 0, float('nan'))
        with self.assertRaises(ValueError):
            a.parse_bytes(pack(metadata, invalid))

    def test_material_entry_is_exact_word_not_assumed_pointer(self):
        metadata, raw = fixture()
        for token in (0, 1, 0xffffffff):
            metadata['records'][0]['material'] = token
            _, rows = a.parse_bytes(pack(metadata, raw))
            self.assertEqual(rows[0]['material'], token)
        metadata['records'][0]['material_vector'] = 1
        with self.assertRaises(ValueError):
            a.parse_bytes(pack(metadata, raw))

    def test_candidate_consensus_and_explicit_static(self):
        healthy = [dict(positions=[(0., 0., 0.), (1., 0., 0.)])]
        current = [dict(positions=[(0., 0., .2), (1., 0., .2)])]
        mapping = [dict(vertex=0, candidates=[[0, 0], [0, 1]]), dict(vertex=1, candidates=[])]
        result = a.delta_consensus(mapping, {1}, healthy, current)
        self.assertTrue(result['agreement_pass'])
        self.assertEqual(result['moved_private_vertices'], 1)
        current[0]['positions'][1] = (1., 0., .3)
        self.assertFalse(a.delta_consensus(mapping, {1}, healthy, current)['agreement_pass'])
        with self.assertRaises(ValueError):
            a.delta_consensus(mapping, set(), healthy, current)

    def test_shared_material_ambiguous_uv_requires_exact_healthy_positions(self):
        profiles = [dict(vertices=19, faces=29, native_uv_winding_sha256='u',
                         ordered_position_sha256=value) for value in ('first', 'second')]
        rows = [dict(vertices=19, triangles=29, uv_winding='u', ordered_xyz=value,
                     material_vector=0x20000, material=7, mesh=0x10000 + i * 4)
                for i, value in enumerate(('first', 'second'))]
        healthy = a.join_sources(dict(records=rows), profiles)
        self.assertEqual(a.join_sources(dict(records=rows[::-1]), profiles, healthy), rows)
        # Changing both ambiguous position identities cannot be authorized by
        # shared material, source counts, node order or UV alone.
        changed = [dict(row, ordered_xyz='changed' + str(i)) for i, row in enumerate(rows)]
        with self.assertRaisesRegex(ValueError, 'Missing/ambiguous source slot'):
            a.join_sources(dict(records=changed), profiles, healthy)


if __name__ == '__main__':
    unittest.main()
