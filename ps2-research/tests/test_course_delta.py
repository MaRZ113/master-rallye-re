"""Synthetic survey boundaries: identity, provenance and conservative metrics."""
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import course_delta as c


def scene_xml(model='course/Italy_S1/Italy_S1', row3='10 20 30 1',
              points=('10 0 0', '0 1 20')):
    markers = ''.join(
        f'<Marker No="{i}"><Value Name="Marker Pos" Type="Vector3" Value="{p}"/></Marker>'
        for i, p in enumerate(points))
    return (f'<Scene><EggLists_Version4><List Name="landscape"><Egg Name="landscape">'
            f'<Value Name="Use en2d" Type="Bool" Value="False"/>'
            f'<Value Name="en3d Visible" Type="Bool" Value="True"/>'
            f'<Value Name="en3d Model Name" Type="String" Value="{model}"/>'
            f'<Value Name="en3d Matrix" Type="Matrix" Row0="1 0 0 0" '
            f'Row1="0 1 0 0" Row2="0 0 1 0" Row3="{row3}"/>'
            f'<AI_List><AI No="0"><Value Name="AI Name" Type="String" Value="Null"/></AI></AI_List>'
            f'</Egg></List></EggLists_Version4><MarkerLists><List Name="RaceLine">'
            f'{markers}</List></MarkerLists></Scene>').encode('ascii')


def pairing_scene(source, model, points):
    """Semantic fixtures use independently hashed ordered XYZ, not filenames."""
    return {'source': source, 'landscape': model,
            'marker_lists': {'RaceLine': {'count': len(points),
                'ordered_xyz_f32_sha256': c.signature(points)}},
            '_route_points': points}


class SignatureTests(unittest.TestCase):
    def test_ordered_float32_xyz_digest(self):
        points = [(10, 0, 0), (0.1, -4, 20)]
        expected = hashlib.sha256(struct.pack('<6f', 10, 0, 0, 0.1, -4, 20)).hexdigest()
        self.assertEqual(c.signature(points), expected)
        self.assertNotEqual(c.signature(points), c.signature(points[::-1]))

    def test_missing_nonfinite_and_unrepresentable_points_rejected(self):
        for point in [None, (1, 2), (math.nan, 0, 0), (0, math.inf, 0), (1e300, 0, 0)]:
            with self.subTest(point=point), self.assertRaises(c.t.FormatError):
                c.signature([point])


class SceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sdk_root = Path(os.environ.get('MASTER_RALLYE_COURSE_SDK',
                                      str(ROOT.parent.parent / 'master-rallye-re-course')))
        if not (sdk_root / 'src' / 'master_rallye' / 'course_xml.py').is_file():
            raise unittest.SkipTest('Read-only Course SDK reference unavailable')
        cls.sdk = c.sdk_modules(sdk_root)[0]

    def test_model_identity_normalization_and_null_owner(self):
        summary, rows = c.parse_scene(scene_xml(), 'synthetic.xml', self.sdk)
        self.assertEqual(summary['landscape'], 'course\\italy_s1\\italy_s1')
        self.assertEqual(rows[0]['owners'], [])
        self.assertEqual(rows[0]['position'], [10, 20, 30])
        self.assertEqual(summary['authored_visible_model_references'], 1)

    def test_null_reference_never_becomes_visible_instance(self):
        for value in ['Null', '(null)', '']:
            with self.subTest(value=value):
                summary, rows = c.parse_scene(scene_xml(model=value), 'null.xml', self.sdk)
                self.assertIsNone(rows[0]['model'])
                self.assertFalse(rows[0]['authored_visible'])
                self.assertEqual(summary['authored_visible_model_references'], 0)

    def test_source_order_preserved_in_route_signature(self):
        a, _ = c.parse_scene(scene_xml(points=('10 0 0', '0 1 20')), 'a.xml', self.sdk)
        b, _ = c.parse_scene(scene_xml(points=('0 1 20', '10 0 0')), 'b.xml', self.sdk)
        self.assertEqual(a['marker_lists']['RaceLine']['count'], 2)
        self.assertNotEqual(a['marker_lists']['RaceLine'], b['marker_lists']['RaceLine'])

    def test_malformed_root_and_declarations_rejected(self):
        for data in [b'<Scene>', b'<Other/>', b'',
                     b'<!DOCTYPE Scene><Scene/>',
                     b'<!DOCTYPE Scene [<!ENTITY x "hello">]><Scene/>']:
            with self.subTest(data=data), self.assertRaises(c.t.FormatError):
                c.parse_scene(data, 'bad.xml', self.sdk)

    def test_matrix_nonfinite_and_incomplete_rejected(self):
        for row3 in ['nan 0 0 1', '1e3000 0 0 1', '1 2 3', 'inf 0 0 1']:
            with self.subTest(row3=row3), self.assertRaises(c.t.FormatError):
                c.parse_scene(scene_xml(row3=row3), 'badmatrix.xml', self.sdk)
        missing = scene_xml().replace(b'Row2="0 0 1 0" ', b'')
        with self.assertRaises(c.t.FormatError):
            c.parse_scene(missing, 'missingrow.xml', self.sdk)

    def test_missing_nonfinite_marker_and_duplicate_lists_rejected(self):
        for data in [scene_xml(points=('0 0 0', 'nan 1 2')),
                     scene_xml(points=('0 0 0', '1 2')),
                     scene_xml().replace(b'</MarkerLists>', b'<List Name="RaceLine"/></MarkerLists>')]:
            with self.subTest(data=data), self.assertRaises(c.t.FormatError):
                c.parse_scene(data, 'badmarker.xml', self.sdk)


class PairingTests(unittest.TestCase):
    def test_exporter_alias_requires_ordered_spatial_evidence(self):
        points = [(x * 20, x % 3, x * 7) for x in range(25)]
        ps2 = pairing_scene('PS2/Italy1.xml', 'course\\italy1\\italy1', points + [(500, 0, 175), (520, 1, 182)])
        pc = pairing_scene('PC/Italy1.xml', 'course\\italy1\\track01', points)
        pair = c.pair_courses([ps2], [pc])[0]
        self.assertEqual(pair['confidence'], 'STRONG')
        self.assertTrue(pair['landscape_alias_from_spatial_evidence'])
        self.assertEqual(pair['ordered_spatial_check']['max_distance'], 0)

    def test_same_filename_different_landscape_cannot_pair(self):
        points = [(0, 0, 0), (10, 0, 0)]
        ps2 = pairing_scene('PS2/ItalyS1.xml', 'course\\italy_s1\\italy_s1', points)
        pc = pairing_scene('PC/ItalyS1.xml', 'course\\turkey1\\turkey1', points)
        pair = c.pair_courses([ps2], [pc])[0]
        self.assertEqual(pair['confidence'], 'UNPAIRED')
        self.assertIsNone(pair['pc'])

    def test_unique_internal_identity_and_ordered_route_allow_exact_pair(self):
        points = [(0, 0, 0), (10, 0, 0)]
        ps2 = pairing_scene('PS2/A.xml', 'course\\france1\\france1', points)
        pc = pairing_scene('PC/B.xml', 'course\\france1\\france1', points)
        pair = c.pair_courses([ps2], [pc])[0]
        self.assertEqual(pair['confidence'], 'EXACT')
        self.assertEqual(pair['pc'], 'PC/B.xml')

    def test_duplicate_exact_candidates_remain_unpaired(self):
        points = [(0, 0, 0), (10, 0, 0)]
        ps2 = pairing_scene('PS2/A.xml', 'course\\france1\\france1', points)
        a = pairing_scene('PC/A.xml', ps2['landscape'], points)
        b = pairing_scene('PC/B.xml', ps2['landscape'], points)
        pair = c.pair_courses([ps2], [a, b])[0]
        self.assertEqual(pair['confidence'], 'UNPAIRED')
        self.assertIsNone(pair['pc'])

    def test_same_count_distant_geometry_is_not_strong(self):
        ps2 = pairing_scene('PS2/A.xml', 'course\\france1\\france1',
                            [(x * 20, 0, 0) for x in range(20)])
        pc = pairing_scene('PC/B.xml', ps2['landscape'],
                           [(10000 + x * 20, 0, 0) for x in range(20)])
        self.assertEqual(c.pair_courses([ps2], [pc])[0]['confidence'], 'TENTATIVE')

    def test_changed_route_order_cannot_be_exact(self):
        points = [(x * 20, 0, 0) for x in range(20)]
        ps2 = pairing_scene('PS2/A.xml', 'course\\france1\\france1', points)
        pc = pairing_scene('PC/B.xml', ps2['landscape'], points[::-1])
        self.assertNotEqual(c.pair_courses([ps2], [pc])[0]['confidence'], 'EXACT')


class MaterialEvidenceTests(unittest.TestCase):
    def test_raw_occurrences_do_not_claim_draw_or_instance_counts(self):
        data = b'\x00$detail(grass) $shader(tree)\x00$detail(grass)\x00'
        result = c.material_strings(data)
        self.assertEqual(result['directive_occurrences']['$detail(grass)'], 2)
        self.assertIn('NOT material/draw/instance counts', result['metric'])
        self.assertNotIn('instance_count', result)
        self.assertNotIn('material_count', result)


class CompiledCorpusTests(unittest.TestCase):
    def test_pc_water_is_compiled_content_and_turkey3_negative_is_bounded(self):
        pc = Path(os.environ.get('MASTER_RALLYE_PC_INPUT', str(ROOT.parent.parent / 'corpora' / 'retail' / 'Data.sma_unpacked')))
        sdk = Path(os.environ.get('MASTER_RALLYE_COURSE_SDK', str(ROOT.parent.parent / 'master-rallye-re-course')))
        if not (pc / 'DataGx' / 'Course' / 'Turkey3').is_dir() or not sdk.is_dir():
            self.skipTest('Canonical PC corpus / SDK unavailable')
        c.sdk_modules(sdk)
        rows = c.pc_compiled_water(pc)
        self.assertEqual([len(r['water_related_draws']) for r in rows], [16, 10, 0, 0])
        self.assertTrue(all(r['complete_disjoint_render_validated'] for r in rows))
        self.assertEqual(rows[-1]['draw_count'], 939)
        self.assertEqual(rows[-1]['sha256'], '724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8')


class OutputAndCacheTests(unittest.TestCase):
    def test_output_must_remain_inside_phase_and_not_overwrite_input(self):
        self.assertEqual(c.output_path(ROOT / 'cdelta1', 'synthetic.json'),
                         (ROOT / 'cdelta1' / 'synthetic.json').resolve())
        for folder, name in [(ROOT / 'ui2', 'wrong-phase.json'),
                             (ROOT / 'cdelta1', '../../escaped.json')]:
            with self.subTest(folder=folder, name=name), self.assertRaises(c.t.FormatError):
                c.output_path(folder, name)
        protected = ROOT / 'cdelta1' / 'synthetic-source.json'
        with self.assertRaises(c.t.FormatError):
            c.output_path(protected.parent, protected.name, [protected])

    def test_cache_revalidates_stored_and_payload_bytes(self):
        scratch = ROOT / 'data' / 'cdelta1'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='synthetic-cache-', dir=scratch) as tmp:
            temp = Path(tmp).resolve()
            self.assertTrue(temp.is_relative_to(scratch.resolve()))
            inputs, cache = temp / 'inputs', temp / 'cache'
            inputs.mkdir()
            payload = b'<Scene/>'
            (inputs / 'TNG.000').write_bytes(b'xx' + payload + b'yy')
            entry = {'path': '\\TNG\\SYNTHETIC\\SCENE.XML', 'offset': 2,
                     'stored_size': len(payload), 'kind': 'file', 'storage_codec': 'raw',
                     'directory_size_0x08': len(payload)}
            extracted = c.t.extraction_path(cache, entry['path'])
            extracted.parent.mkdir(parents=True)
            extracted.write_bytes(payload)
            provenance = {'path': entry['path'], 'offset': 2,
                          'stored_size': len(payload),
                          'stored_sha256': hashlib.sha256(payload).hexdigest(),
                          'payload_sha256': hashlib.sha256(payload).hexdigest()}
            sidecar = extracted.with_name(extracted.name + '.provenance.json')
            sidecar.write_text(json.dumps(provenance), encoding='utf-8')
            self.assertEqual(c.read_cached(entry, inputs, cache)[0], payload)
            extracted.write_bytes(b'<Other/>')
            with self.assertRaises(c.t.FormatError):
                c.read_cached(entry, inputs, cache)
            # Coherent cache+sidecar edits still cannot impersonate source.
            forged = dict(provenance)
            forged['payload_sha256'] = hashlib.sha256(b'<Other/>').hexdigest()
            sidecar.write_text(json.dumps(forged), encoding='utf-8')
            with self.assertRaises(c.t.FormatError):
                c.read_cached(entry, inputs, cache)
            sidecar.write_text(json.dumps(provenance), encoding='utf-8')
            extracted.write_bytes(payload)
            (inputs / 'TNG.000').write_bytes(b'xx' + b'<Other/>' + b'yy')
            with self.assertRaises(c.t.FormatError):
                c.read_cached(entry, inputs, cache)
            sidecar.write_text('{bad json', encoding='utf-8')
            with self.assertRaises(ValueError):
                c.read_cached(entry, inputs, cache)


if __name__ == '__main__':
    unittest.main()
