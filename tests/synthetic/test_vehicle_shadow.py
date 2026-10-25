"""Generated, proprietary-free source and admission controls for vehicle shadows."""
import copy
import hashlib
import struct
import sys
import unittest
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[2] / 'tools')]
from master_rallye.addon_sdk.vehicle_shadow import generate_profile, bind_profile, validate_profile, matches_binding, runtime_bounds
from tests.synthetic.test_library import synthetic_dx, simple_record
import vehicle_shadow_native as native


def fixture():
    positions = [(-1., 0., -2.), (1., 0., -2.), (1., 1., 2.), (-1., 1., 2.)]
    # Deliberately oversized donor metadata, kept byte-for-byte in the source.
    bounds = struct.pack('<I3ff3f3f', 1339, 0., .5, -.5, 4., -1.5, 0., -3., 1.5, 1., 2.)
    model = synthetic_dx(positions, [0, 1, 2, 0, 2, 3], [simple_record(0, 3, 0, 6, ('body',))], [(0, 0, 6)], trailing=bounds)
    texture = struct.pack('<5I', 0xfeed, 0, 0, 4, 4) + b''.join(bytes((0, 0, 0, 255 if x in (1, 2) and z in (1, 2) else 0)) for z in range(4) for x in range(4))
    return model, texture


class ShadowTests(unittest.TestCase):
    def test_native_layout_differs_from_serialized_footer(self):
        raw = struct.pack('<I10f', 1339, 1, 2, 3, 4, -1, -2, -3, 5, 6, 7)
        self.assertEqual(struct.unpack('<11f', runtime_bounds(raw)), (1, 2, 3, 4, 16, -1, -2, -3, 5, 6, 7))
        self.assertNotEqual(raw[4:], runtime_bounds(raw)[4:])

    def test_source_identity_and_explicit_body_footprint(self):
        model, texture = fixture(); before = hashlib.sha256(model).hexdigest()
        p = generate_profile(model, texture, 'Fixture', margin_x_m=0., margin_z_m=0.)
        b = bind_profile(p, model, texture)
        self.assertEqual(b['body_bounds_xz_m'], [[-1., -2.], [1., 2.]])
        self.assertEqual(b['generated_alpha_support_xz_m'], [[-1., -2.], [1., 2.]])
        self.assertEqual(b['generated_quad_size_xz_m'], [4., 8.])
        self.assertEqual(before, hashlib.sha256(model).hexdigest())
        self.assertFalse(b['runtime_qualified'])

    def test_scale_offset_and_margin_are_independent(self):
        model, texture = fixture()
        p = generate_profile(model, texture, 'Fixture', scale_x=.8, scale_z=.5, offset_x_m=.25, offset_z_m=.4, margin_x_m=.25, margin_z_m=.1)
        b = bind_profile(p, model, texture)
        self.assertEqual(b['generated_alpha_support_xz_m'][0][0], -.75)
        self.assertEqual(b['generated_alpha_support_xz_m'][1][0], 1.25)
        self.assertAlmostEqual(b['generated_alpha_support_xz_m'][0][1], -.65)
        self.assertAlmostEqual(b['generated_alpha_support_xz_m'][1][1], 1.45)

    def test_native_admission_full_resource_name_and_values(self):
        model, texture = fixture(); b = bind_profile(generate_profile(model, texture, 'Fixture'), model, texture)
        values = bytes.fromhex(b['native_bounds_values_hex'])
        self.assertTrue(matches_binding(b, 'Vehicles\\FIXTURE\\car', values))
        for name in ('vehicles/fixture/car2', 'vehicles/fixture/car\0suffix', 'vehicles/other/car', 'vehicles/fixture/wheel', 'vehicles/fixture/complete'):
            self.assertFalse(matches_binding(b, name, values))
        for i in range(44):
            wrong = bytearray(values); wrong[i] ^= 1
            self.assertFalse(matches_binding(b, 'vehicles/fixture/car', wrong))

    def test_rejects_unknown_controls_and_changed_sources(self):
        model, texture = fixture(); profile = generate_profile(model, texture, 'Fixture')
        for key, value in [('scale_z', 0.), ('scale_x', float('nan')), ('offset_z_m', 3.), ('alpha_threshold', True), ('margin_x_m', -1.), ('arbitrary_field', 1), ('runtime_family', '../Navara')]:
            p = copy.deepcopy(profile); p[key] = value
            with self.assertRaises(ValueError): validate_profile(p)
        with self.assertRaises(ValueError): bind_profile(profile, model + b'x', texture)
        with self.assertRaises(ValueError): bind_profile(profile, model, texture[:-1] + b'x')

    def test_native_wrapper_data_and_optional_noop(self):
        model, texture = fixture(); b = bind_profile(generate_profile(model, texture, 'Fixture'), model, texture)
        blob, labels = native.make_wrapper(0x10001000, [b])
        self.assertEqual(blob[labels['replacement0'] - 0x10001000:], bytes.fromhex(b['shadow_bounds_hex']))
        self.assertEqual(blob.count(b'vehicles/fixture/car\0'), 1)
        self.assertEqual(native.append_shadow(b'original', b'image', b'prefix', 0x10000000, [], 65536), (b'image', b'prefix', None))
        with self.assertRaises(ValueError): native.append_shadow(b'wrong', b'wrong', b'', 0x10000000, [b], 65536)


if __name__ == '__main__': unittest.main()
