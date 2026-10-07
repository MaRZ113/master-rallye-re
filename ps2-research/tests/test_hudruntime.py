"""Independent geometry, malformed input, and exact-build static evidence gates."""
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import hudruntime as h


def xml(points):
    markers = ''.join(f'<Marker No="{i}"><Value Name="Marker Pos" Type="Vector3" Value="{p}"/></Marker>'
                      for i, p in enumerate(points))
    return ('<Scene><MarkerLists><List Name="RaceLine">' + markers + '</List></MarkerLists></Scene>').encode()


class RouteTests(unittest.TestCase):
    def test_xml_order_and_float32(self):
        result = h.read_xml_route(xml(['10 0 20', '0.1 -4 -30']))
        self.assertEqual(result, [(10, 0, 20), (h.f32(.1), -4, -30)])

    def test_xml_never_sorts(self):
        with self.assertRaises(h.FormatError):
            h.read_xml_route(xml(['0 0 0', '1 2 3']).replace(b'No="0"', b'No="9"'))

    def test_missing_duplicate_and_short_list(self):
        for data in [b'<Scene/>', xml(['0 0 0']), xml(['0 0 0', '1 2 3']).replace(b'</MarkerLists>', b'<List Name="RaceLine"/></MarkerLists>')]:
            with self.subTest(data=data), self.assertRaises(h.FormatError):
                h.read_xml_route(data)

    def test_nonfinite_xml(self):
        for value in ['nan', 'inf', '-inf', '1e300', 'bad']:
            with self.subTest(value=value), self.assertRaises(h.FormatError):
                h.read_xml_route(xml(['0 0 0', value + ' 0 0']))

    def test_malformed_xml(self):
        for data in [b'<Scene>', b'<!DOCTYPE Scene><Scene/>', xml(['0 0 0', '1 2']), xml(['0 0 0', '1 2 3']).replace(b'Vector3', b'Vector2')]:
            with self.subTest(data=data), self.assertRaises(h.FormatError):
                h.read_xml_route(data)

    def test_memory_layout_ignores_other_fields(self):
        data = bytearray(b'\xff' * 160)
        struct.pack_into('<3f', data, 0x40, 2, 3, 4)
        struct.pack_into('<3f', data, 0x90, -5, -6, 7)
        self.assertEqual(h.read_memory_route(data, 0, 2), [(2, 3, 4), (-5, -6, 7)])

    def test_invalid_memory_offsets_counts_and_truncation(self):
        for offset, count in [(-4, 2), (1, 2), (164, 2), (0, -1), (0, 1), (0, 65537), (0, True), (4, 2)]:
            with self.subTest(offset=offset, count=count), self.assertRaises(h.FormatError):
                h.read_memory_route(bytes(160), offset, count)

    def test_memory_nonfinite(self):
        data = bytearray(160)
        struct.pack_into('<f', data, 0x40, math.nan)
        with self.assertRaises(h.FormatError):
            h.read_memory_route(data, 0, 2)

    def test_vector_pointer_resolution(self):
        data = bytearray(176)
        struct.pack_into('<3I', data, 0, 0x100010, 0x1000b0, 0x1000b0)
        struct.pack_into('<3f', data, 16 + 0x40, 1, 2, 3)
        self.assertEqual(h.read_memory_vector(data, 0, 0x100000)[0], (1, 2, 3))

    def test_vector_reversed_overflow_stride_and_header(self):
        for pointers in [(0x100010, 0x10000c, 0x1000b0), (0x100010, 0x1000b1, 0x1000b1), (0x100010, 0x1000b0, 0x100100), (0xff000, 0x1000b0, 0x1000b0)]:
            data = bytearray(176)
            struct.pack_into('<3I', data, 0, *pointers)
            with self.subTest(pointers=pointers), self.assertRaises(h.FormatError):
                h.read_memory_vector(data, 0, 0x100000)
        for offset, base in [(1, 0), (176, 0), (0, -1), (0, 0xffffffff)]:
            with self.subTest(offset=offset, base=base), self.assertRaises(h.FormatError):
                h.read_memory_vector(bytes(176), offset, base)


class MathTests(unittest.TestCase):
    def test_world_corners_center_and_interior(self):
        # Heading (0,1) gives identity XZ orientation, no bounds-based fitting.
        for point, expected in [((-100, -50), (-40, -20)), ((100, 50), (40, 20)), ((0, 0), (0, 0)), ((10, -20), (4, -8))]:
            actual = h.world_to_map(point, (0, 0), (0, 1))
            for a, b in zip(actual, expected):
                self.assertAlmostEqual(a, b, places=5)

    def test_player_translation_and_quarter_turn(self):
        self.assertEqual(h.world_to_map((10, 20), (10, 20), (1, 0)), (0, 0))
        x, y = h.world_to_map((20, 25), (10, 20), (1, 0))
        self.assertAlmostEqual(x, -2, places=6)
        self.assertAlmostEqual(y, 4, places=6)

    def test_invalid_heading_and_geometry(self):
        for point, heading in [((0, 0), (0, 0)), ((0, 0), (2, 0)), ((math.inf, 1), (0, 1))]:
            with self.subTest(point=point, heading=heading), self.assertRaises(h.FormatError):
                h.world_to_map(point, (0, 0), heading)

    def test_clip_inside_boundary_outside(self):
        self.assertEqual(h.clip_segment((-45, -43), (45, 43), 90, 86), ((-45, -43), (45, 43)))
        self.assertIsNone(h.clip_segment((-60, 1), (-50, 2), 90, 86))
        self.assertEqual(h.clip_segment((-100, 0), (100, 0), 90, 86), ((-45, 0), (45, 0)))

    def test_clip_vertical_diagonal_and_zero_length(self):
        self.assertEqual(h.clip_segment((0, -100), (0, 100), 90, 86), ((0, -43), (0, 43)))
        self.assertEqual(h.clip_segment((-100, -100), (100, 100), 90, 86), ((-43, -43), (43, 43)))
        self.assertEqual(h.clip_segment((0, 0), (0, 0), 90, 86), ((0, 0), (0, 0)))

    def test_clip_invalid_dimensions(self):
        for width, height in [(0, 86), (90, -1), (math.nan, 86)]:
            with self.subTest(width=width, height=height), self.assertRaises(h.FormatError):
                h.clip_segment((0, 0), (1, 1), width, height)

    def test_authored_quadrants_and_bias(self):
        for p, expected in [((22, 401), (21.5, 78.5)), ((494, 430), (493.5, 49.5)), ((50, 50), (49.5, 429.5)), ((557, 98), (556.5, 381.5)), ((320, 55), (319.5, 424.5))]:
            self.assertEqual(h.sprite_logical_point(p, (0, 0)), expected)

    def test_sprite_local_y_and_rect(self):
        self.assertEqual(h.sprite_logical_rect((557, 98), (-64, -63, 64, 65)), [492.5, 318.5, 620.5, 446.5])
        self.assertEqual(h.sprite_logical_point((0, 480), (10, 20)), (9.5, 19.5))

    def test_window_and_finish_bounds(self):
        points = [(i, 0, 0) for i in range(100)]
        report = h.reconstruct(points, (50, 0), (0, 1), 50, 99)
        self.assertEqual(report['segment_window'], [18, 82])
        self.assertEqual(h.reconstruct(points, (0, 0), (0, 1), -3, 99)['segment_window'], [0, 32])
        for finish in [-1, 100]:
            with self.assertRaises(h.FormatError):
                h.reconstruct(points, (0, 0), (0, 1), 50, finish)

    def test_center_player_opponent_and_no_bounds_fit(self):
        report = h.reconstruct([(0, 0, 0), (10, 0, 0), (10000, 0, 0)], (0, 0), (0, 1), 1, 2,
                               opponents=[(0, 0), (10000, 0)])
        self.assertEqual(report['player_foreground_xy'], [[69, 397], [74, 387], [79, 397]])
        self.assertEqual(len(report['opponents'][0]['foreground_segments']), 2)
        self.assertEqual(report['opponents'][1]['foreground_segments'], [])
        self.assertAlmostEqual(report['route_local_xy'][1][0], 4, places=6)
        self.assertIn('viewBox="0 0 640 480"', h.svg(report))

    def test_deterministic_json_and_bounds(self):
        args = ([(0, -1, 0), (2, 3, 4)], (0, 0), (0, 1), 0, 1)
        a, b = h.reconstruct(*args), h.reconstruct(*args)
        self.assertEqual(json.dumps(a, allow_nan=False), json.dumps(b, allow_nan=False))
        self.assertEqual(a['route_bounds'], {'min_xyz': [0, -1, 0], 'max_xyz': [2, 3, 4]})

    def test_visible_continuity_does_not_imply_one_runtime_batch(self):
        report = h.reconstruct([(0, 0, 0), (1, 0, 0), (2, 0, 0)], (0, 0), (0, 1), 0, 2)
        self.assertEqual(len(report['route_visual_strips']), 1)
        self.assertEqual(len(report['route_polyline_batches']), 2)
        self.assertTrue(all(len(batch) == 2 for batch in report['route_polyline_batches']))
        self.assertTrue(all(len(segment['xy']) == 2 for segment in report['route_clipped_segments']))

    def test_output_hygiene(self):
        for path in [ROOT / 'ui2' / 'route.json', ROOT / 'data' / '..' / 'route.json', ROOT / 'data']:
            with self.subTest(path=path), self.assertRaises(h.FormatError):
                h.local_output(path)
        path = ROOT / 'data' / 'synthetic-never-written.json'
        self.assertEqual(h.local_output(path), path.resolve())
        with self.assertRaises(h.FormatError):
            h.local_output(path, [path])


class MetadataTests(unittest.TestCase):
    def test_owner_resolution_and_roles(self):
        d = json.loads((ROOT / 'ui2' / 'elf-hud-functions.json').read_text())
        owner = d['owners']['gaHudAiMap']
        self.assertEqual(owner['constructor'], '0x00146118')
        self.assertEqual(owner['initialize'], '0x001461f8')
        self.assertEqual(owner['update'], '0x00147038')
        self.assertEqual(d['owner_factory']['clone'], '0x001fc4c0')
        self.assertIsNone(d['owners'].get('invented_owner'))

    def test_structures_cross_function_access(self):
        d = json.loads((ROOT / 'ui2' / 'hud-runtime-structures.json').read_text())
        layouts = {r['name']: r for r in d['structures']}
        self.assertEqual(layouts['gaHudAiMap']['size'], 0x8c)
        fields = {r['name']: r for r in layouts['gaHudAiMap']['fields']}
        self.assertEqual(fields['center_x']['offset'], 0x84)
        self.assertIn('0x00146960', fields['center_x']['accessors'])
        self.assertIn('0x00147038', fields['center_x']['accessors'])
        route = layouts['marker_record']
        self.assertEqual(route['size'], h.STRIDE)
        self.assertEqual(next(f for f in route['fields'] if f['name'] == 'position_xyzw')['offset'], h.POSITION_OFFSET)

    def test_no_fabricated_dynamic_rect(self):
        d = json.loads((ROOT / 'ui2' / 'hud-runtime-map.json').read_text())
        records = {r['authored_name']: r for r in d['elements']}
        self.assertIsNone(records['Map']['PSB_bank'])
        self.assertIsNone(records['GameTimer']['final_logical_rect'])
        self.assertEqual(records['SpeedDial']['conditional_logical_rect'], [492.5, 318.5, 620.5, 446.5])


class CorpusTests(unittest.TestCase):
    def test_exact_elf_vtable_and_scalar_constants(self):
        source = os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not source:
            self.skipTest('MASTER_RALLYE_PS2_INPUT not supplied')
        data = (Path(source) / 'SLES_509.06').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), h.ELF_SHA)
        self.assertEqual(struct.unpack_from('<I', data, 0x44cb00 - 0xff000 + 0x34)[0], 0x1461f8)
        self.assertEqual(struct.unpack_from('<I', data, 0x44cb00 - 0xff000 + 0x2c)[0], 0x147038)
        self.assertEqual(struct.unpack_from('<f', data, 0x40e5e8 - 0xff000)[0], h.SCALE)

    def test_exact_route_input(self):
        source = ROOT / 'data' / 'ui2' / 'ITALYS1.XML'
        if not source.exists():
            self.skipTest('Local extracted RaceTest XML unavailable')
        data = source.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), '56603a9b51f509032a3f15953f161eeaa25044b2c00b5988a73e0c2cbc9c9a92')
        self.assertEqual(len(h.read_xml_route(data)), 293)

    def test_original_route_and_vehicle_access_patterns(self):
        source = os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not source:
            self.skipTest('MASTER_RALLYE_PS2_INPUT not supplied')
        data = (Path(source) / 'SLES_509.06').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), h.ELF_SHA)
        words = [struct.unpack_from('<I', data, a - 0xff000)[0] for a in range(0x147038, 0x148800, 4)]
        float_load_offsets = {w & 0xffff for w in words if w >> 26 == 0x31}
        self.assertTrue({0x40, 0x48, 0xf0, 0xf8, 0x74, 0x78, 0x84, 0x88} <= float_load_offsets)
        # Vtable bytes establish lifecycle and renderer selection independently
        # of the generated report and the generic-MIPS decompiler's types.
        expected = {0x44cb00: (0x146960, 0x147038, 0x1461f8),
                    0x44c700: (0x14dfc0, 0x14e360, 0x14e250)}
        for table, targets in expected.items():
            self.assertEqual(tuple(struct.unpack_from('<I', data, table - 0xff000 + off)[0]
                                   for off in (0x24, 0x2c, 0x34)), targets)
        self.assertEqual(struct.unpack_from('<I', data, 0x485a00 - 0xff000 + 0xbc)[0], 0x32f498)


if __name__ == '__main__':
    unittest.main()
