"""WATER1 recovered contracts; synthetic fixtures are not runtime evidence."""
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import water_runtime as w
import tngtool as t


def fixture(control=0, opaque=0x7fc00000):
    points = [(0., 2., 0.), (0., 2., 2.), (2., 2., 0.), (2., 2., 2.),
              (4., 2., 0.), (4., 2., 2.), (6., 2., 0.)]
    data = bytearray(struct.pack('<3I4fI', 0xd00d, 2, 0x539, 0, 0, 0, 100, len(points)))
    for i, point in enumerate(points):
        data.extend(struct.pack('<3fII4f4f', 0, 1, 0, control if i == 2 else 0,
                                0xffffffff, 0, 0, 0, 0, *point, 1))

    def string(text):
        encoded = text.encode('ascii')
        return struct.pack('<IH', len(encoded), len(encoded))+encoded if encoded else struct.pack('<I', 0)

    def mesh(name, first, count):
        return (struct.pack('<3I', 2, 0, 3)+b'\1\0\0\0'+string('Course/SYNTHETIC/water-tga')+
                b'\0\0'+string(name)+struct.pack('<2I4BI', 0, 0, 0, 0, 0, 0, opaque)+
                struct.pack('<3IBfI', 1, first, count, 0, 1., 0))

    data.extend(struct.pack('<2I', 1, 2))
    data.extend(mesh('water $surfacetype(water) $shader(puddle)', 0, 4))
    data.extend(mesh('ground $shader(ground)', 4, 3))
    data.extend(struct.pack('<I', 100))
    return bytes(data)


class DirectiveTests(unittest.TestCase):
    def test_actual_modes_and_original_alias_spelling(self):
        for name, mode in [('water', 10), ('puddle', 9), ('waterfall', 19), ('waterall', 19)]:
            with self.subTest(name=name):
                result = w.shader_contract('$shader('+name+')')
                self.assertEqual(result['water_mode'], mode)
                self.assertEqual(result['authored_shader'], name)

    def test_first_property_search_then_interner_case_fold(self):
        self.assertEqual(w.shader_contract('$shader(PUDDLE) $shader(water)')['water_mode'], 9)
        self.assertIsNone(w.shader_contract('$SHADER(puddle)')['water_mode'])
        self.assertEqual(w.shader_contract('$shaderExtra(water)')['water_mode'], 10)

    def test_unknown_and_whitespace_are_not_silently_corrected(self):
        for name in ['$shader(waterfal)', '$shader( water)', '$shader(water )', '$shader(']:
            result = w.shader_contract(name)
            self.assertIsNone(result['water_mode'])
            self.assertIsNotNone(result['fallback'])

    def test_surface_type_and_scroll_do_not_select_visual_shader(self):
        result = w.shader_contract('$surfacetype(water) $scroll(v,+1)')
        self.assertIsNone(result['water_mode'])
        self.assertTrue(result['scroll_v_plus1_present'])
        self.assertEqual(result['scroll_token_consumer'], 'NOT_FOUND_IN_TRACED_WATER_PATH')


class VisualTests(unittest.TestCase):
    def test_material_is_attached_to_real_visual_strips(self):
        scene = w.decode_scene(fixture())
        report, triangles = w.inspect_scene(scene, 'SYNTHETIC', 'SYNTHETIC')
        self.assertEqual(len(scene.meshes), 2)
        self.assertEqual(len(report['water_groups']), 1)
        self.assertEqual(len(triangles), 2)
        self.assertEqual(report['water_geometry']['surface_area'], 4.)
        self.assertEqual(report['water_geometry']['bounds']['min'], [0., 2., 0.])
        self.assertEqual(report['water_groups'][0]['geometry_kind'], 'VISUAL_SOURCE_STRIP')
        self.assertNotIn('spatial_representation', report)
        self.assertEqual(report['runtime_validation'], 'NOT_PERFORMED')

    def test_newest_vertex_control_bit_suppresses_only_its_triangle(self):
        scene = w.decode_scene(fixture(control=1))
        triangles, counts = w.mesh_triangles(scene, scene.meshes[0])
        self.assertEqual(len(triangles), 1)
        self.assertEqual(counts['suppressed_triples'], 1)
        scene = w.decode_scene(fixture(control=2))
        self.assertEqual(len(w.mesh_triangles(scene, scene.meshes[0])[0]), 2)

    def test_opaque_mesh_word_is_not_a_position_or_guessed_float(self):
        scene = w.decode_scene(fixture())
        self.assertEqual(scene.meshes[0]['word70_unknown'], '0x7fc00000')
        self.assertEqual(scene.position(0), (0., 2., 0.))

    def test_boolean_reader_matches_original_nonzero_semantics(self):
        self.assertTrue(w.Reader(b'\xff', 0).boolean())
        self.assertFalse(w.Reader(b'\0', 0).boolean())

    def test_truncation_unknown_nodes_and_end_marker_fail_closed(self):
        data = fixture()
        for cut in [0, 31, 100, len(data)-1]:
            with self.subTest(cut=cut), self.assertRaises(t.FormatError):
                w.decode_scene(data[:cut])
        for at, value in [(0, 0), (28, 0xffffffff), (32+7*52, 9), (len(data)-4, 104)]:
            damaged = bytearray(data)
            struct.pack_into('<I', damaged, at, value)
            with self.subTest(at=at), self.assertRaises(t.FormatError):
                w.decode_scene(damaged)

    def test_string_lengths_embedded_nul_and_vertex_ranges_fail_closed(self):
        data = bytearray(fixture())
        offset = data.index(b'Course/')
        struct.pack_into('<H', data, offset-2, 1)
        with self.assertRaises(t.FormatError): w.decode_scene(data)
        data = bytearray(fixture())
        data[offset] = 0
        with self.assertRaises(t.FormatError): w.decode_scene(data)
        scene = w.decode_scene(fixture())
        data = bytearray(fixture())
        struct.pack_into('<I', data, scene.meshes[0]['strips'][0]['offset'], 7)
        with self.assertRaises(t.FormatError): w.decode_scene(data)

    def test_nonfinite_actual_coordinate_fails_on_geometry_access(self):
        data = bytearray(fixture())
        struct.pack_into('<f', data, 32+36, math.nan)
        scene = w.decode_scene(data)
        with self.assertRaises(t.FormatError): w.inspect_scene(scene, 'SYNTHETIC', 'SYNTHETIC')

    def test_shared_edges_define_components_not_shared_points(self):
        a = ((0., 0., 0.), (0., 0., 1.), (1., 0., 0.))
        b = ((1., 0., 0.), (0., 0., 1.), (1., 0., 1.))
        c = ((1., 0., 1.), (2., 0., 1.), (2., 0., 2.))
        metrics = w.geometry_metrics([a, b, c])
        self.assertEqual(metrics['components'], 2)
        self.assertEqual(metrics['component_sizes'], [2, 1])

    def test_hash_identifiers_and_output_are_deterministic(self):
        scene = w.decode_scene(fixture())
        a, _ = w.inspect_scene(scene, 'SYNTHETIC', 'SYNTHETIC')
        b, _ = w.inspect_scene(scene, 'SYNTHETIC', 'SYNTHETIC')
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertTrue(a['water_groups'][0]['stable_id'].startswith(t.sha(fixture())[:16]))


class ComparisonTests(unittest.TestCase):
    TRIANGLE = ((0., 2., 0.), (0., 2., 2.), (2., 2., 0.))

    def test_permutation_precision_and_neighbor_cell_boundary(self):
        shifted = tuple(tuple(x+.0005 for x in p) for p in reversed(self.TRIANGLE))
        report = w.match_geometry([self.TRIANGLE], [(shifted, 7)], shifted)
        self.assertEqual(report['triangle_matches'], 1)
        self.assertEqual(report['matched_pc_draws'], {7: 1})
        self.assertEqual(report['water_vertices_matching_pc'], 3)

    def test_all_pc_draws_are_searched_without_material_name_filter(self):
        report = w.match_geometry([self.TRIANGLE], [(self.TRIANGLE, 999)], self.TRIANGLE)
        self.assertEqual(report['triangle_matches'], 1)
        self.assertEqual(report['matched_pc_draws'], {999: 1})

    def test_different_tessellation_can_be_coplanar_without_triangle_match(self):
        pc = ((-2., 2., -2.), (-2., 2., 5.), (5., 2., -2.))
        report = w.match_geometry([self.TRIANGLE], [(pc, 1)], pc, heights=True)
        self.assertEqual(report['triangle_matches'], 0)
        self.assertEqual(report['centroid_height']['coplanar_with_any_pc_triangle'], 1)

    def test_horizontal_height_and_absence_are_separate_from_visibility(self):
        pc = tuple((x, y-3, z) for x, y, z in self.TRIANGLE)
        report = w.match_geometry([self.TRIANGLE], [(pc, 1)], pc, heights=True)
        self.assertEqual(report['triangle_matches'], 0)
        self.assertEqual(report['centroid_height']['min_signed_nearest'], 3.)
        self.assertEqual(report['runtime_visibility'], 'UNKNOWN')

    def test_tolerances_and_degenerate_projection(self):
        for tolerance in [0, -1, math.inf, math.nan, .02]:
            with self.assertRaises(t.FormatError): w.match_geometry([], [], [], tolerance=tolerance)
        self.assertIsNone(w.height_at(((0, 0, 0), (0, 1, 0), (0, 2, 0)), 0, 0))


class RenderTests(unittest.TestCase):
    def test_original_alpha_selectors_are_different_equations(self):
        self.assertEqual(w.alpha_fields(0x44), {'A': 0, 'B': 1, 'C': 0, 'D': 1, 'FIX': 0})
        self.assertEqual(w.alpha_fields((56 << 32)|0x68), {'A': 0, 'B': 2, 'C': 2, 'D': 1, 'FIX': 56})

    def test_state_contract_keeps_inherited_zte_and_runtime_unknown(self):
        contract = w.render_contract()
        self.assertEqual(contract['modes']['puddle']['secondary']['TCC'], 0)
        self.assertEqual(contract['modes']['water']['secondary']['TCC'], 1)
        self.assertEqual(contract['modes']['puddle']['primary']['ZTE'], 'INHERITED')
        self.assertEqual(contract['runtime_validation'], 'NOT_PERFORMED')

    def test_waterfall_uv_counter_units_pause_and_float32(self):
        a = w.waterfall_uv(0, 20., 20., .25)
        self.assertEqual(a['primary_uv'], [.25, -6.])
        b = w.waterfall_uv(15, 20., 20., .25)
        self.assertAlmostEqual(b['primary_uv'][1], -5.8, places=5)
        self.assertAlmostEqual(b['secondary_uv'][1], -5.6, places=5)
        self.assertEqual(w.waterfall_uv(999, 20., 20., .25, previous_phase=.1, paused=True)['primary_uv'], b['primary_uv'])
        self.assertEqual(b['counter_units'], 'UNKNOWN')
        with self.assertRaises(t.FormatError): w.waterfall_uv(-1, 0., 0., 0.)

    def test_output_path_cannot_escape_ignored_data_root(self):
        with self.assertRaises(t.FormatError): w.local_output(w.ROOT/'water1'/'original-geometry.json')
        with self.assertRaises(t.FormatError): w.local_output(w.ROOT/'data'/'water1'/'..'/'outside.json')
        self.assertEqual(w.local_output(w.ROOT/'data'/'water1'/'test.json').name, 'test.json')

    def test_existing_hard_link_cannot_overwrite_its_source(self):
        scratch = w.ROOT/'data'/'water1'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            source, output = Path(folder)/'source', Path(folder)/'output'
            source.write_bytes(b'SYNTHETIC original input')
            os.link(source, output)
            with self.assertRaises(t.FormatError): w.local_output(output)
            self.assertEqual(source.read_bytes(), b'SYNTHETIC original input')


class OriginalCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not root:
            raise unittest.SkipTest('Original corpus requires MASTER_RALLYE_PS2_INPUT')
        cls.root = Path(root)
        w.verify_inputs(cls.root)
        cls.manifest, _ = t.load_pak(cls.root/'TNG.PAK')

    def test_named_original_visual_groups_and_independent_spatial_boundary(self):
        expected = {'TURKEY3': (17, 745), 'FRANCE1': (16, 3586), 'ITALY_S1': (10, 1329),
                    'TURKEY1': (0, 0), 'SPAIN_S2': (33, 2058)}
        for course, (groups, triangles) in expected.items():
            with self.subTest(course=course):
                suffix = (course+'/'+course+'.PSM').replace('/', chr(92))
                entry = next(r for r in self.manifest['entries'] if r['path'].endswith(suffix))
                payload, _ = t.read_payload(entry, self.root/'TNG.000')
                scene = w.decode_scene(payload)
                report, faces = w.inspect_scene(scene, course, entry['path'])
                spatial = w.d.decode_landscape(payload)
                self.assertEqual(spatial.proxy_offset, scene.end+4)
                self.assertEqual((len(report['water_groups']), len(faces)), (groups, triangles))
                if course == 'TURKEY3':
                    self.assertEqual(report['water_groups'][0]['material_offset'], 3429472)
                    self.assertEqual(payload[3429472:3429472+len(report['water_groups'][0]['material'])].decode(),
                                     'water $surfacetype(water) $shader(puddle)')

    def test_instruction_evidence_matches_canonical_words(self):
        binary = (self.root/'SLES_509.06').read_bytes()
        inventory = json.loads((w.ROOT/'water1'/'elf-functions.json').read_text())
        for function in inventory['functions']:
            for probe in function['instruction_evidence']:
                address = int(probe['va'], 16)
                self.assertEqual(struct.unpack_from('<I', binary, address-0xff000)[0],
                                 int(probe['original_word'], 16), hex(address))

    def test_original_pc_controls_and_turkey3_full_draw_search(self):
        pc_root, sdk_root = os.environ.get('MASTER_RALLYE_PC_INPUT'), os.environ.get('MASTER_RALLYE_COURSE_SDK')
        if not pc_root or not sdk_root:
            self.skipTest('PC comparison requires MASTER_RALLYE_PC_INPUT and MASTER_RALLYE_COURSE_SDK')
        for course, expected in [('FRANCE1', 3586), ('ITALY_S1', 1329), ('TURKEY3', 0)]:
            with self.subTest(course=course):
                entry = next(r for r in self.manifest['entries'] if r['path'].endswith(course+'.PSM'))
                payload, _ = t.read_payload(entry, self.root/'TNG.000')
                scene = w.decode_scene(payload)
                _, triangles = w.inspect_scene(scene, course, entry['path'])
                rows, points, pc = w.load_pc(Path(pc_root), Path(sdk_root), course)
                report = w.match_geometry(triangles, rows, points, heights=course == 'TURKEY3')
                self.assertEqual(report['triangle_matches'], expected)
                if course == 'TURKEY3':
                    self.assertEqual((pc['draws'], pc['vertices'], pc['triangles']), (939, 54589, 42237))
                    self.assertEqual(pc['dx_sha256'], '724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8')
                    self.assertEqual(report['centroid_height']['coplanar_with_any_pc_triangle'], 0)


if __name__ == '__main__':
    unittest.main()
