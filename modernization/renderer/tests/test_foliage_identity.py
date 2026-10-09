import copy
import itertools
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import foliage_identity as f
from trace_common import read_jsonl


def fixture():
    hashes = sorted(f.face_hash(((i, 0, 0), (i+1, 0, 0), (i, 1, 0))) for i in range(24))
    hashes = sorted(hashes*2)
    source = {'schema': f.SCHEMA, 'course': 'FRANCE1', 'source': {'sha256': f.DX_SHA},
        'target_face_hashes': hashes, 'geometry_multiset_sha256': f.multiset_hash(hashes)}
    probe = {'schema': 'foliage-probe-v1', 'override_applied': False, 'identity': 'UNPROVEN',
        'reason': 'content_captured_identity_pending', 'face_hashes': hashes,
        'geometry_multiset_sha256': f.multiset_hash(hashes), 'vertex_generation': 1, 'index_generation': 2,
        'texture_generation': 3, 'vertex_unlock_hresult': 0, 'index_unlock_hresult': 0,
        'native_rs': {'15': 1, '14': 1}, 'native_tss': [{}, {}]}
    draw = {'type': 'draw', 'method': 'DrawIndexedPrimitive', 'draw_index': 911, 'sequence': 42,
        'frame': 7, 'arguments': [4, 200, 28, 900, 48], 'result': 0, 'ps2_foliage_probe': probe}
    records = [{'type': 'frame_begin', 'exe_sha256': f.TARGET_SHA, 'frame': 7}, draw,
        {'type': 'frame_end', 'frame': 7, 'complete': True, 'truncated': False}]
    return records, source


class FoliageIdentityTests(unittest.TestCase):
    def test_production_native_probe_capture(self):
        paths = []
        for path in (ROOT/'.build-msvc/Release/MRRRenderer/logs').glob('frame-*.jsonl'):
            with path.open(encoding='utf-8') as stream:
                header = json.loads(stream.readline())
            if header.get('exe_path', '').casefold().endswith('foliage_probe_tests.exe'):
                paths.append(path)
        if not paths:
            self.skipTest('Run tools/build.py first: synthetic native probe capture unavailable')
        records = read_jsonl(max(paths, key=lambda p: p.stat().st_mtime_ns))
        draw = next(r for r in records if r.get('type') == 'draw')
        probe = draw['ps2_foliage_probe']
        self.assertEqual(probe['face_hashes'], ['b2afe5ee233688b94630b58778b6b4e92c6af902cc9f61ae448b4bca1090420a'])
        self.assertEqual(probe['native_rs']['15'], 115)
        self.assertEqual(probe['vertex_diffuse_alpha_min'], 64)
        self.assertEqual(probe['vertex_diffuse_alpha_max'], 192)
        self.assertEqual(probe['native_material_diffuse_alpha'], .75)
        self.assertFalse(probe['override_applied'])
        self.assertEqual(draw['result'], 0x8876086c)  # Original D3DERR_INVALIDCALL from mock.
        self.assertEqual(records[0]['build'], 'UNKNOWN_BUILD')
        self.assertTrue(records[-1]['complete'])
    def test_independent_binary_fingerprint(self):
        # Independent SHA256 oracle over a literal synthetic little-endian word window.
        import hashlib
        raw = struct.pack('<9I', 0, 0, 0, 0, 0x3f800000, 0, 0x3f800000, 0, 0)
        expected = hashlib.sha256(raw).hexdigest()
        self.assertEqual(expected, 'b2afe5ee233688b94630b58778b6b4e92c6af902cc9f61ae448b4bca1090420a')
        self.assertEqual(f.face_hash(((0, 0, 0), (1, 0, 0), (0, 1, 0))), expected)

    def test_winding_vertex_order_and_negative_zero(self):
        points = ((0, -0.0, 0), (1, 0, 0), (0, 1, 0))
        self.assertEqual(len({f.face_hash(p) for p in itertools.permutations(points)}), 1)

    def test_float32_no_epsilon_matching(self):
        a = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
        b = ((0, 0, 0), (1.0001, 0, 0), (0, 1, 0))
        self.assertNotEqual(f.face_hash(a), f.face_hash(b))

    def test_reject_nonfinite_and_malformed_points(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                f.face_hash(((value, 0, 0), (1, 0, 0), (0, 1, 0)))
        with self.assertRaises(ValueError):
            f.face_hash(((0, 0), (1, 0), (0, 1)))

    def test_exact_content_is_not_activation(self):
        records, source = fixture()
        result = f.audit(records, source, 'FRANCE1')
        self.assertTrue(result['exact_build'] and result['complete_frame'])
        self.assertEqual(result['content_matches'][0]['relation'], 'EXACT_TARGET_CONTENT')
        self.assertEqual(result['content_matches'][0]['draw_index'], 911)  # Never assumes ordinal54.
        self.assertFalse(result['runtime_override_allowed'])
        self.assertEqual(result['status'], 'BLOCKED_ON_DRAW_IDENTITY')

    def test_missing_geometry_count_or_texture_never_match(self):
        records, source = fixture()
        records[1].pop('ps2_foliage_probe')
        records[1]['draw_index'] = 54
        records[1]['texture'] = 'bush01-tga'
        result = f.audit(records, source)
        self.assertFalse(result['content_matches'])
        self.assertEqual(result['identity'], 'TARGET_IDENTITY_NOT_FOUND')

    def test_same_count_other_geometry_rejected(self):
        records, source = fixture()
        p = records[1]['ps2_foliage_probe']
        p['face_hashes'] = [f.face_hash(((90, 0, 0), (91, 0, 0), (90, 1, 0)))]*48
        p['geometry_multiset_sha256'] = f.multiset_hash(p['face_hashes'])
        result = f.audit(records, source)
        self.assertFalse(result['content_matches'])
        self.assertEqual(result['nonmatching_content_controls'], 1)

    def test_split_subset_and_mixed_draw(self):
        records, source = fixture()
        p = records[1]['ps2_foliage_probe']
        p['face_hashes'] = p['face_hashes'][:12]
        records[1]['arguments'][4] = 12
        p['geometry_multiset_sha256'] = f.multiset_hash(p['face_hashes'])
        self.assertEqual(f.audit(records, source)['content_matches'][0]['relation'], 'TARGET_SUBSET')
        p['face_hashes'][0] = f.face_hash(((90, 0, 0), (91, 0, 0), (90, 1, 0)))
        p['geometry_multiset_sha256'] = f.multiset_hash(p['face_hashes'])
        self.assertEqual(f.audit(records, source)['content_matches'][0]['relation'], 'MIXED_TARGET_AND_OTHER_GEOMETRY')

    def test_unknown_build_course_incomplete_frame_fail_closed(self):
        records, source = fixture()
        for header, ending, course in (({}, {}, 'TURKEY3'), ({'exe_sha256': 'unknown'}, {}, 'FRANCE1'),
            ({}, {'truncated': True}, 'FRANCE1'), ({}, {'complete': False}, 'FRANCE1')):
            with self.subTest(header=header, ending=ending, course=course):
                r = copy.deepcopy(records);r[0].update(header);r[-1].update(ending)
                result = f.audit(r, source, course)
                self.assertFalse(result['runtime_override_allowed'])
                self.assertTrue(all(not c['override_allowed'] for c in result['content_matches']))

    def test_generation_hash_schema_or_draw_mismatch_rejected(self):
        records, source = fixture()
        for key, value in (('vertex_generation', 0), ('index_generation', 0),
            ('geometry_multiset_sha256', '0'*64), ('override_applied', True), ('index_unlock_hresult', 0x80004005)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                r = copy.deepcopy(records);r[1]['ps2_foliage_probe'][key] = value;f.audit(r, source)
        with self.assertRaises(ValueError):
            r = copy.deepcopy(records);r[1]['arguments'][4] = 24;f.audit(r, source)

    def test_wrong_source_or_multiplicity_rejected(self):
        records, source = fixture()
        for change in ({'schema': 'unknown'}, {'course': 'TURKEY3'}, {'source': {'sha256': 'unknown'}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                s = copy.deepcopy(source);s.update(change);f.audit(records, s)
        with self.assertRaises(ValueError):
            s = copy.deepcopy(source);s['target_face_hashes'] = s['target_face_hashes'][:24];f.audit(records, s)

    def test_ambiguous_multiple_draws_no_promotion(self):
        records, source = fixture();records.insert(2, copy.deepcopy(records[1]));records[2]['sequence'] += 1
        result = f.audit(records, source)
        self.assertEqual(len(result['content_matches']), 2)
        self.assertEqual(result['identity'], 'TARGET_IDENTITY_AMBIGUOUS')

    def test_deterministic_preserve_original_hresult(self):
        records, source = fixture();records[1]['result'] = 0x88761234
        before = copy.deepcopy(records)
        a = json.dumps(f.audit(records, source), sort_keys=True)
        self.assertEqual(a, json.dumps(f.audit(records, source), sort_keys=True))
        self.assertEqual(records, before)
        self.assertEqual(json.loads(a)['content_matches'][0]['draw_hresult'], 0x88761234)


if __name__ == '__main__':
    unittest.main()
