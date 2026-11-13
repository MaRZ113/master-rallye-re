"""Synthetic checks of the Brake Glow-ON module (tools/brake_lamps): no Master Rallye bytes, no SDK.

Run: py -3.11 -m unittest tests.synthetic.test_brake_lamps
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / 'tools') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tools'))

import numpy as np  # noqa: E402

from brake_lamps import analysis, build, spec  # noqa: E402
from brake_lamps.geometry import Mesh, closest_on_mesh, merge, ray_hits, samples, view_directions  # noqa: E402


def grid(nx, ny, w, h, z_of, x0=0.0, y0=0.0):
    """Patch facing -Z (the car rear), z = z_of(x, y)."""
    pos = [(x0 + w * i / nx, y0 + h * j / ny, z_of(x0 + w * i / nx, y0 + h * j / ny)) for j in range(ny + 1) for i in range(nx + 1)]
    tri = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            b, c, d = a + 1, a + nx + 2, a + nx + 1
            tri += [(a, c, b), (a, d, c)]
    return Mesh.of(pos, tri)


def curved(x, y):
    """Convex lens bulging toward -Z by 12 mm at its centre (lens centre x=0.8, y=0.6)."""
    return -2.0 - .012 * max(0.0, 1 - ((x - .8) / .08) ** 2 - ((y - .6) / .06) ** 2)


class Geometry(unittest.TestCase):
    def test_ray_hits_first_surface_both_windings(self):
        quad = Mesh.of([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [(0, 1, 2), (0, 2, 3)])
        t = ray_hits(np.array([[0, 0, 1.0], [0, 0, -1.0], [5, 5, 1.0]]), np.array([0, 0, -1.0]), quad)
        self.assertAlmostEqual(t[0], 1.0)
        self.assertTrue(math.isinf(t[1]))   # surface behind the ray origin
        self.assertTrue(math.isinf(t[2]))   # outside the quad
        flipped = Mesh(quad.positions, quad.triangles[:, [0, 2, 1]])
        self.assertAlmostEqual(ray_hits(np.array([[0, 0, 1.0]]), np.array([0, 0, -1.0]), flipped)[0], 1.0)

    def test_closest_point_regions(self):
        tri = Mesh.of([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
        pts = np.array([[.2, .2, 1], [2, -1, 0], [-1, -1, 0], [.8, .8, 0]])
        c, _, d = closest_on_mesh(pts, tri)
        np.testing.assert_allclose(c[0], [.2, .2, 0], atol=1e-9)
        np.testing.assert_allclose(c[1], [1, 0, 0], atol=1e-9)
        np.testing.assert_allclose(c[2], [0, 0, 0], atol=1e-9)
        np.testing.assert_allclose(c[3], [.5, .5, 0], atol=1e-9)
        self.assertAlmostEqual(d[0], 1.0)

    def test_views_are_unit_and_rear_facing(self):
        v = view_directions()
        self.assertEqual(len(v), 8)
        for d in v.values():
            self.assertAlmostEqual(float(np.linalg.norm(d)), 1.0)
            self.assertLess(d[2], 0)

    def test_boundary_loop_of_grid(self):
        loops = build.boundary_loops(grid(3, 2, .3, .2, lambda x, y: 0.0))
        self.assertEqual(len(loops), 1)
        self.assertEqual(len(loops[0]), 10)


class Fit(unittest.TestCase):
    def setUp(self):
        self.lens = grid(8, 6, .16, .12, curved, .72, .54)
        # Body panel around the lens, flush with the lens rim (z = -2.0), with a hole where the lens is.
        body = grid(10, 10, .5, .4, lambda x, y: -2.0, .55, .4)
        c = body.corners().mean(axis=1)
        keep = ~((abs(c[:, 0] - .8) < .085) & (abs(c[:, 1] - .6) < .065))
        self.body = Mesh(body.positions, body.triangles[keep])
        self.frame = build.Frame.of(self.lens)

    def test_frame_outward_is_rear(self):
        self.assertLess(self.frame.normal[2], -.99)
        self.assertGreater(self.frame.u[0], .99)

    def test_flat_layer_sinks_into_curved_lens(self):
        """The fault being fixed: a flat layer pinned to the lens rim lies behind the bulging glass."""
        flat = grid(8, 6, .16, .12, lambda x, y: -2.001, .72, .54)
        vis, raw = analysis.layer_visibility(flat, merge([self.lens, self.body]))
        self.assertGreater(vis['rear']['hidden_fraction'], .3)
        self.assertGreater(raw['rear_depth'].max(), .005)

    def test_from_glass_project_fit_is_visible(self):
        core, halo = build.from_glass(self.lens, self.frame, 1.0)
        c, h = build.fit_layers(core, halo, self.lens, self.body, self.frame, {'mode': 'project', 'max_edge_m': .02}, .0015, exact_core=True)
        checks = build.check_layers(c, h, self.lens, merge([self.lens, self.body]), self.frame)
        self.assertEqual(checks['buried'], 0)
        self.assertEqual(checks['core']['rear_hidden'], 0.0)
        self.assertEqual(checks['halo']['rear_hidden'], 0.0)
        off = checks['core']['lens_offset_mm']
        self.assertGreaterEqual(off['min'], 1.0)
        self.assertLessEqual(off['max'], 3.0)
        # UVs: core planar 0..1, halo ring outside the core.
        self.assertAlmostEqual(float(c.uvs.min()), 0.0); self.assertAlmostEqual(float(c.uvs.max()), 1.0)
        self.assertGreater(np.ptp(h.positions[:, 0]), np.ptp(c.positions[:, 0]))

    def test_donor_project_and_shrinkwrap(self):
        donor = grid(2, 1, .3, .2, lambda x, y: 0.0)
        core = build.Layer(donor.positions, donor.positions[:, :2] / [.3, .2], donor.triangles)
        ring = grid(2, 1, .4, .3, lambda x, y: 0.0, -.05, -.05)
        glow = build.Layer(ring.positions, ring.positions[:, :2], ring.triangles)
        for mode in ('project', 'shrinkwrap', 'plane'):
            c, g = build.place_donor(core.copy(), glow.copy(), self.lens, self.frame, 1.0)
            c, g = build.fit_layers(c, g, self.lens, self.body, self.frame, {'mode': mode, 'max_edge_m': .01}, .0015)
            checks = build.check_layers(c, g, self.lens, merge([self.lens, self.body]), self.frame)
            self.assertEqual(checks['buried'], 0, mode)
            self.assertEqual(checks['core']['rear_hidden'], 0.0, mode)

    def test_halo_does_not_hang_over_a_raised_panel(self):
        wall = grid(2, 2, .1, .4, lambda x, y: -2.0 - (x - .9) * 2, .9, .4)   # panel rising toward -Z right of the lens
        core, halo = build.from_glass(self.lens, self.frame, 1.0)
        c, h = build.fit_layers(core, halo, self.lens, merge([self.body, wall]), self.frame, {'mode': 'project', 'max_edge_m': .02}, .0015, exact_core=True)
        rise = (self.frame.local(h.positions)[:, 2]).max()
        self.assertLess(rise, .045)   # lift clamp keeps the ring near the lens

    def test_mirror(self):
        core, _ = build.from_glass(self.lens, self.frame, 1.0)
        m = build.mirror_layer(core)
        np.testing.assert_allclose(m.positions[:, 0], -core.positions[:, 0])

    def test_subdivide_bounds_edges(self):
        big = build.Layer(np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0.0]]), np.array([[0, 0], [1, 0], [0, 1.0]]), np.array([[0, 1, 2]]))
        s = build.subdivide(big, .2, limit=12)
        e = np.linalg.norm(s.positions[s.triangles] - s.positions[s.triangles[:, [1, 2, 0]]], axis=2)
        self.assertLessEqual(e.max(), .2 + 1e-9)
        np.testing.assert_allclose(s.uvs, s.positions[:, :2])


class Spec(unittest.TestCase):
    FACE = '0123456789abcdef'

    def base(self, **lamp):
        return {'family': 'Demo', 'lamps': [{'id': 'left', 'lens': {'faces': [self.FACE]}, **lamp}]}

    def test_defaults_filled(self):
        s = spec.normalise(self.base())
        l = s['lamps'][0]
        self.assertEqual(l['source']['kind'], 'from_glass')
        self.assertEqual(l['fit']['mode'], 'project')
        self.assertEqual(l['fit']['offset_mm'], 1.5)
        self.assertEqual(l['lens']['draw'], 'blight')
        self.assertEqual(l['depth']['halo'], 'native')

    def test_partial_override_keeps_defaults(self):
        l = spec.normalise(self.base(fit={'offset_mm': 2.5}))['lamps'][0]
        self.assertEqual(l['fit'], {'mode': 'project', 'offset_mm': 2.5, 'max_offset_mm': 3.0, 'max_edge_m': .02, 'halo_max_edge_m': .03})

    def test_rejections(self):
        bad = [self.base(fit={'mode': 'magic'}), self.base(fit={'offset_mm': 9}), self.base(source={'kind': 'ps2'}),
               self.base(halo={'color': [300, 0, 0]}), self.base(depth={'halo': 'always'}), self.base(body='XBOX'),
               {'family': 'Bad Name', 'lamps': [{'lens': {'faces': [self.FACE]}}]}, {'family': 'Demo', 'lamps': []},
               self.base(lens={'faces': ['xyz']}), self.base(transform={'scale': [9, 1, 1]})]
        for b in bad:
            with self.assertRaises(spec.SpecError, msg=str(b)):
                spec.normalise(b)

    def test_mirror_reference(self):
        s = spec.normalise({'family': 'Demo', 'lamps': [{'id': 'right', 'lens': {'faces': [self.FACE]}}, {'id': 'left', 'mirror': {'of': 'right'}}]})
        self.assertEqual(s['lamps'][1]['mirror'], {'of': 'right'})
        with self.assertRaises(spec.SpecError):
            spec.normalise({'family': 'Demo', 'lamps': [{'id': 'left', 'mirror': {'of': 'nobody'}}]})

    def test_custom_source_for_importers(self):
        mesh = {'positions': [[0, 0, 0], [1, 0, 0], [0, 1, 0]], 'uvs': [[0, 0], [1, 0], [0, 1]], 'triangles': [[0, 1, 2]]}
        s = spec.normalise(self.base(source={'kind': 'custom', 'core': mesh, 'glow': mesh}, lens={'draw': 'any', 'faces': [self.FACE]}))
        self.assertEqual(s['lamps'][0]['lens']['draw'], 'any')


class Preview(unittest.TestCase):
    def test_gxi_decode(self):
        from brake_lamps.preview import gxi_bgra
        data = bytes(8) + bytes([10, 20, 30, 40]) * 256
        w, h, px = gxi_bgra(data)
        self.assertEqual((w, h, px[:4]), (16, 16, bytes([30, 20, 10, 40])))
        self.assertEqual(gxi_bgra(data, opaque=True)[2][3], 255)

    def test_scene_encoding(self):
        from brake_lamps.preview import Scene, Camera
        s = Scene()
        t = s.texture('t', 1, 1, b'\0\0\xff\xff')
        s.draw([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [0xffffffff] * 3, [(0, 0)] * 3, [(0, 1, 2)], texture=t)
        blob = s.encode(Camera((0, 0, -5), (0, 0, 0)))
        self.assertEqual(blob[:4], b'MRLP')
        # header, camera (9f + fov/near/far), clear/counts, texture (w,h + 1 px), draw states, counts, 3 vertices, 3 indices
        self.assertEqual(len(blob), 16 + 48 + 12 + 12 + 28 + 8 + 3 * 24 + 12)


if __name__ == '__main__':
    unittest.main()
