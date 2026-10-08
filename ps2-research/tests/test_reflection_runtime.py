"""REFL1 synthetic and independent corpus checks; no emulator PASS implied."""
import copy
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import reflection_runtime as r
import tngtool as t
import water_runtime as w

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = [[1., 0., 0., 0.], [0., 1., 0., 0.],
            [0., 0., 1., 0.], [0., 0., 0., 1.]]


def synthetic_vehicle():
    # Independent byte construction, not serialization by the decoder under test.
    data = bytearray(struct.pack('<3I4fI', 0xd00d, 2, 0x539, 0, 0, 0, 5, 3))
    for point in [(0., 0., 0.), (0., 0., 1.), (1., 0., 0.)]:
        data.extend(struct.pack('<3fII4f4f', 0, 1, 0, 0, 0xffffffff,
                                0, 0, 0, 0, *point, 1))

    def string(text):
        b = text.encode('ascii')
        return struct.pack('<IH', len(b), len(b))+b

    data.extend(struct.pack('<2I', 1, 1))
    data.extend(struct.pack('<2I', 7, 4)+b'Body'+struct.pack('<2I', 7, 1))
    data.extend(struct.pack('<3I', 8, 3, 1))
    data.extend(struct.pack('<3I', 2, 0, 3)+b'\1\0\0\0'+string('SYNTHETIC/paint'))
    data.extend(b'\0\0'+string('$shader(carshiny)'))
    data.extend(struct.pack('<2I4BI', 0, 0, 0, 0, 1, 1, 0x3f000000))
    data.extend(struct.pack('<3IBfI', 1, 0, 3, 0, 1., 0))
    data.extend(struct.pack('<I', 101))
    return bytes(data)


class MaterialTests(unittest.TestCase):
    def test_exact_shader_search_and_interner(self):
        self.assertEqual(r.material_contract('$shader(CarShiny)')['mode'], 3)
        self.assertIsNone(r.material_contract('$SHADER(carshiny)')['mode'])
        self.assertIsNone(r.material_contract('$shader(crashiny)')['mode'])
        self.assertIsNone(r.material_contract('$shader(carshiny )')['mode'])
        self.assertEqual(r.material_contract('$shader(carflat) $shader(carshiny)')['mode'], 1)

    def test_resource_replacement_is_not_authored_chrome_selection(self):
        result = r.material_contract('$shader(carshiny)', 'commontextures\\chrome-tga')
        self.assertEqual(result['effective_secondary'], r.TARGET)
        self.assertEqual(result['authored_secondary'], 'commontextures\\chrome-tga')
        self.assertEqual(r.material_contract('$shader(carglass)', 'glass')['effective_secondary'], r.WINDSCREEN)

    def test_literal_rubber_substring_exception(self):
        for name in ('rubber', 'commontextures\\rubber-tga', 'pretendrubbersuffix'):
            result = r.material_contract('$shader(carshiny)', name)
            self.assertEqual(result['effective_secondary'], name)
            self.assertTrue(result['rubber_substring_preserved'])
        self.assertEqual(r.material_contract('$shader(carshiny)', 'RUBBER')['effective_secondary'], r.TARGET)
        self.assertEqual(r.material_contract('$shader(carglow)', 'rubber')['effective_secondary'], r.TARGET)

    def test_nonreflective_control_and_untraced_modes_are_separate(self):
        self.assertIsNone(r.material_contract('$shader(carflat)')['environment_selector'])
        self.assertEqual(r.material_contract('$shader(carflat)')['mode'], 1)
        self.assertEqual(r.material_contract('$shader(caralpha)')['mode'], 2)
        self.assertEqual(r.material_contract('$shader(carsglass)')['mode'], 20)
        self.assertEqual(r.material_contract('$shader(carbrakelights)')['evidence_grade'], 'UNKNOWN')


class VehicleTests(unittest.TestCase):
    def test_raw_name_is_not_general_serialized_string_or_transform(self):
        scene = r.decode_vehicle(synthetic_vehicle())
        self.assertEqual(scene.extra_nodes[0]['name'], 'Body')
        self.assertEqual(scene.extra_nodes[0]['name_index'], 7)
        self.assertEqual(scene.extra_nodes[1]['selector'], 3)
        self.assertEqual(scene.meshes[0]['path'], 'root.0.0.0')
        self.assertEqual(scene.position(2), (1., 0., 0.))
        report = r.inspect_vehicle(synthetic_vehicle(), 'SYNTHETIC', 'SYNTHETIC')
        self.assertEqual(report['groups'][0]['metrics']['triangles'], 1)
        self.assertEqual(report['groups'][0]['normal_length_range'], [1., 1.])
        self.assertEqual(report['runtime_validation'], 'NOT_PERFORMED')

    def test_landscape_default_remains_strict(self):
        with self.assertRaises(t.FormatError):
            w.decode_scene(synthetic_vehicle())
        b = bytearray(synthetic_vehicle())
        struct.pack_into('<I', b, len(b)-4, 100)
        with self.assertRaises(t.FormatError): r.decode_vehicle(b)

    def test_bad_tag_name_and_truncated_payload_fail_closed(self):
        b = bytearray(synthetic_vehicle())
        b[b.index(b'Body')] = 0
        with self.assertRaises(t.FormatError): r.decode_vehicle(b)
        b = bytearray(synthetic_vehicle())
        struct.pack_into('<I', b, 32+3*52+8, 9)
        with self.assertRaises(t.FormatError): r.decode_vehicle(b)
        for length in (10, 200, len(b)-1):
            with self.subTest(length=length), self.assertRaises(t.FormatError):
                r.decode_vehicle(synthetic_vehicle()[:length])

    def test_output_cannot_escape_ignored_research_directory(self):
        with self.assertRaises(t.FormatError):
            r.local_output(ROOT/'refl1'/'not-a-diagnostic.json')


class MathTests(unittest.TestCase):
    def evaluate(self, normal, object0=IDENTITY, object1=IDENTITY,
                 view0=IDENTITY, view1=IDENTITY, weight=0.):
        return r.coordinates(normal, object0, object1, view0, view1, weight, (.25, .75))

    def test_normal_axes_and_unchanged_base_uv(self):
        for normal, uv in [([1, 0, 0], [1., .5]), ([0, 1, 0], [.5, 0.]),
                           ([0, 0, 1], [.5, .5]), ([-1, 0, 0], [0., .5])]:
            with self.subTest(normal=normal):
                result = self.evaluate(normal)
                self.assertEqual(result['environment_uv'], uv)
                self.assertEqual(result['base_uv'], [.25, .75])
                self.assertEqual(result['input_provenance'], 'SYNTHETIC_INPUT')

    def test_vehicle_yaw_and_camera_rotation_have_independent_inputs(self):
        yaw = [[0., 0., -1., 0.], [0., 1., 0., 0.],
               [1., 0., 0., 0.], [0., 0., 0., 1.]]
        view = [[0., 1., 0., 0.], [-1., 0., 0., 0.],
                [0., 0., 1., 0.], [0., 0., 0., 1.]]
        self.assertEqual(self.evaluate([0, 0, 1], yaw, yaw)['environment_uv'], [1., .5])
        self.assertEqual(self.evaluate([1, 0, 0], view0=view, view1=view)['environment_uv'], [.5, 0.])

    def test_affine_translation_does_not_enter_normal_equation(self):
        a, b = copy.deepcopy(IDENTITY), copy.deepcopy(IDENTITY)
        a[3][:3], b[3][:3] = [123., -456., 789.], [800., 900., 1000.]
        self.assertEqual(self.evaluate([1, 1, 0], a, a, b, b)['environment_uv'], [1., 0.])

    def test_lerp_is_not_matrix_composition(self):
        other = copy.deepcopy(IDENTITY)
        other[0][0] = 3.
        self.assertEqual(self.evaluate([1, 0, 0], IDENTITY, other, weight=.5)['environment_uv'], [1.5, .5])
        self.assertEqual(self.evaluate([1, 0, 0], IDENTITY, other, weight=1.)['environment_uv'], [2., .5])

    def test_no_silent_normalization_or_clamping(self):
        self.assertEqual(self.evaluate([2, 0, 0])['environment_uv'], [1.5, .5])
        with self.assertRaises(ValueError): self.evaluate([math.nan, 0, 0])
        with self.assertRaises(ValueError): self.evaluate([1, 0])
        with self.assertRaises(ValueError): self.evaluate([1, 0, 0], weight=1.1)

    def test_body_color_uses_local_y_and_explicit_cvt_rounding(self):
        for normal, gray in [([0, 0, 0], 102), ([0, 1, 0], 159), ([0, -1, 0], 45),
                             ([0, 10, 0], 254), ([0, -10, 0], 2)]:
            self.assertEqual(r.body_color(normal, 'nearest_even')['source_rgba8'], [gray]*3+[254])
        self.assertEqual(r.body_color([0, -1, 0], 'toward_zero')['source_rgba8'][0], 44)
        with self.assertRaises(ValueError): r.body_color([0, 1, 0], 'unspecified')


class EvidenceTests(unittest.TestCase):
    def test_gs_equations_use_fix_not_texture_alpha(self):
        for word, fields in [(0x8000000029, (1, 2, 2, 0, 128)),
                             (0x6000000068, (0, 2, 2, 1, 96)),
                             (0x50000000a8, (0, 2, 2, 2, 80)),
                             (0x3000000068, (0, 2, 2, 1, 48))]:
            result = r.blend_contract(word)
            self.assertEqual(tuple(result[x] for x in ('A', 'B', 'C', 'D', 'FIX')), fields)
            self.assertNotIn('As', result['equation'])

    def test_compact_contract_and_fixtures_are_self_contained(self):
        contract = r.render_contract()
        self.assertEqual(contract['runtime_validation'], 'NOT_PERFORMED')
        self.assertEqual(contract['environment_source']['classification'], 'MIXED_STATIC_AND_FRAMEBUFFER')
        self.assertEqual(len(r.resource_inventory()['resources']), 9)
        report = self._case_evidence()
        self.assertEqual([x['mesh_count'] for x in report['vehicles']], [31, 31])

    def _case_evidence(self):
        return json.loads((ROOT/'refl1'/'vehicle-evidence.json').read_text())

    def test_deterministic_math_json(self):
        inputs = ([1, 0, 0], IDENTITY, IDENTITY, IDENTITY, IDENTITY, 0.)
        self.assertEqual(json.dumps(r.coordinates(*inputs), sort_keys=True),
                         json.dumps(r.coordinates(*inputs), sort_keys=True))


class OriginalCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not value:
            raise unittest.SkipTest('Canonical external PS2 corpus not supplied')
        cls.source = Path(value)
        w.verify_inputs(cls.source)
        cls.manifest, _ = t.load_pak(cls.source/'TNG.PAK')

    def test_vehicle_mesh_offsets_against_original_bytes_and_frozen_counts(self):
        facts = json.loads((ROOT/'refl1'/'vehicle-evidence.json').read_text())
        for case in facts['vehicles']:
            entry = next(x for x in self.manifest['entries'] if x['path'] == case['resource'])
            payload, _ = t.read_payload(entry, self.source/'TNG.000')
            self.assertEqual(t.sha(payload), case['decoded_sha256'])
            result = r.inspect_vehicle(payload, case['model'], case['resource'])
            self.assertEqual(result['shader_counts'], case['shader_counts'])
            self.assertEqual(result['visual_tree_end'], case['visual_tree_end'])
            for group in case['selected_groups']:
                with self.subTest(model=case['model'], path=group['path']):
                    at = group['material_offset']
                    self.assertTrue(payload[at:].startswith(group['material'].encode('ascii')))
                    self.assertEqual(struct.unpack_from('<I', payload, group['node_offset'])[0], 2)
                    observed = next(g for g in result['groups'] if g['path'] == group['path'])
                    self.assertEqual(observed['metrics']['triangles'], group['metrics']['triangles'])

    def test_original_instruction_words_and_vu_pairs(self):
        binary = (self.source/'SLES_509.06').read_bytes()
        facts = json.loads((ROOT/'refl1'/'elf-functions.json').read_text())
        for probe in facts['independent_probes']:
            with self.subTest(va=probe['va']):
                self.assertEqual(struct.unpack_from('<I', binary, int(probe['va'], 16)-0xff000)[0],
                                 int(probe['original_word'], 16))

    def test_resources_with_existing_gxi_decoder(self):
        result = r.inspect_resources(self.source)
        self.assertEqual(len(result['resources']), 9)
        env = next(x for x in result['resources'] if x['path'].endswith('ENVSOURCE64X64.GXI'))
        self.assertEqual((env['gxi']['width'], env['gxi']['height']), (64, 64))
        self.assertEqual(env['gxi']['alpha_unique_count'], 2)


if __name__ == '__main__':
    unittest.main()
