"""Tests for the W2 render builder pieces and the tag1500 sector table."""
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_render as br  # noqa: E402
import material_map as mm  # noqa: E402
import tag1500_probe as tp  # noqa: E402
from master_rallye.course_render_writer import Container, Draw  # noqa: E402

RETAIL = Path('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Course/Turkey3/turkey3.dx')


class RuleTests(unittest.TestCase):
    def test_directives(self):
        d = mm.directives('$surfacetype(grass) $shader(ground) $clamp(u) $detail(shrubs)$grnd:grass_hardNoise Pass')
        self.assertEqual(d, {'surfacetype': 'yes', 'shader': 'ground', 'clamp': 'u'})
        self.assertEqual(mm.directives('TURshrub2 $alphatest() $shader(treeblend)'), {'alphatest': '', 'shader': 'treeblend'})

    def test_rule_table(self):
        f, p = br.rule_fields({'shader': 'ground', 'clamp': 'v'}, True, None)
        self.assertEqual((f['flags'], f['w14'], f['w24'], f['sorted']), ('00000101', 4, 11, False))
        f, _ = br.rule_fields({'shader': 'treeblend', 'alphatest': ''}, False, None)
        self.assertEqual((f['flags'], f['w14'], f['w24']), ('01010101', 1, 3))
        f, _ = br.rule_fields({'shader': 'wires', 'alphablend': '', 'clamp': 'v'}, False, None)
        self.assertEqual((f['flags'], f['w14'], f['w24'], f['sorted']), ('01000001', 4, 1, True))
        f, _ = br.rule_fields({'shader': 'metal'}, False, 'aluminium-tga')
        self.assertEqual(f['w24'], 7)
        f, _ = br.rule_fields({'shader': 'puddle'}, False, None)
        self.assertEqual((f['w18'], f['w24']), (1, 19))
        self.assertEqual(br.clamp_word({'clamp': 'uv'}), 0)

    def test_polygon_helpers(self):
        sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertTrue(br.point_in_polygon(5, 5, sq))
        self.assertFalse(br.point_in_polygon(11, 5, sq))
        self.assertAlmostEqual(br.dist_to_polygon(12, 5, sq), 2.0)

    def test_affine_fit(self):
        rows = [((u, v), (2 * u + 0.5 * v + 3, -u + 4 * v - 1)) for u in range(3) for v in range(3)]
        a = br._affine(rows)
        for got, want in zip(a, (2, 0.5, 3, -1, 4, -1)):
            self.assertAlmostEqual(got, want, places=6)
        self.assertIsNone(br._affine(rows[:3]))

    def test_widen_1339(self):
        raw = struct.pack('<I10f', 1339, 0, 5, 0, 10, -1, 0, -1, 1, 10, 1)
        same, changed = br.widen_1339(raw, [(0, 1, 0), (0, 9, 0)])
        self.assertFalse(changed)
        self.assertEqual(same, raw)
        out, changed = br.widen_1339(raw, [(0, -2, 0)])
        v = struct.unpack('<I10f', out)
        self.assertTrue(changed)
        self.assertEqual(v[6], -2.0)
        self.assertEqual(v[2], 4.0)

    def test_sort_container_structure(self):
        b = br.Builder.__new__(br.Builder)
        tris = []
        for k in range(20):   # two parallel strips of quads: the first triangle's plane separates them
            z = 0.0 if k < 10 else -5.0
            x = float(k % 10)
            tris.append([((x, 0, z), (0, 0, 1), b'\xff' * 4, (0, 0), (0, 0)), ((x + 1, 0, z), (0, 0, 1), b'\xff' * 4, (0, 0), (0, 0)),
                         ((x, 1, z), (0, 0, 1), b'\xff' * 4, (0, 0), (0, 0))])
        made = []

        def emit(tl, tt_, f):
            made.append(len(tl))
            return [Draw(0, 2, 0, 3 * len(tl), 1, 0, b'\0\0\x80?', bytes(4), 1, [b'w'])]
        c = br.Builder.sort_container(b, tris, ('w',), {'w14': 1, 'w18': 0, 'w24': 1, 'flags': '01000001'}, emit)
        self.assertEqual(c.tag, 5)
        self.assertEqual(c.children[0].tag, 6)
        g1, g2 = c.children[0].children
        self.assertEqual((g1.tag, g2.tag), (1, 1))
        self.assertEqual(sum(made), 20)


class SectorTests(unittest.TestCase):
    def test_parse_synthetic(self):
        raw = struct.pack('<2I', 1500, 2)
        raw += struct.pack('<I', 3) + b''.join(struct.pack('<6fI', x, 0, z, 0, .5, 0, 0xFFFFFFFF) for x, z in ((0, 0), (1, 0), (0, 1)))
        raw += struct.pack('<I2I', 2, 0, 1)
        raw += struct.pack('<I', 1) + struct.pack('<6fI', 2, 0, 2, 0, .5, 0, 0) + struct.pack('<II', 1, 1)
        ents, used = tp.parse(raw)
        self.assertEqual(used, len(raw))
        self.assertEqual(ents[0]['ids'], [0, 1])
        self.assertEqual(ents[1]['points'][0][6], 0)


@unittest.skipUnless(RETAIL.exists(), 'retail data not available')
class Turkey3Build(unittest.TestCase):
    def test_build_keeps_the_ps2_triangle_set(self):
        import course_config as cc
        course = cc.course('Turkey3')
        data, textures, rep = br.build(course, course.pc_dx.read_bytes())
        self.assertTrue(rep['triangle_multiset_equal_ps2'])
        self.assertTrue(rep['course_render_validated'])
        self.assertEqual(rep['unresolved_texture_slots'], {})
        self.assertEqual(rep['batches'], 220)
        self.assertEqual(set(textures), {'brickhouse-tga', 'caravan-tga', 'shrubtrig2-tga', 'water-tga'})
        self.assertGreater(rep.get('tri_two_sided_measured', 0), 0)       # shrubs, wires, fences get their reversed copy
        # PC uses the raw PS2 UV: every banner triangle has the PC handedness (negative UV determinant in wire order)
        from master_rallye.course_render_writer import CourseRender
        r = CourseRender.from_bytes(data)
        signs = set()
        for d in r.draws():
            if d.texture_tuple[0] in ('bagoo-tga', 'kaori-tga', 'go-tga'):
                for k in range(d.index_start, d.index_start + d.index_count, 3):
                    uv = [r.uv_sets[0][d.vertex_base + r.indices[k + j]] for j in range(3)]
                    signs.add((uv[1][0] - uv[0][0]) * (uv[2][1] - uv[0][1]) - (uv[1][1] - uv[0][1]) * (uv[2][0] - uv[0][0]) < 0)
        self.assertEqual(signs, {True})
        # default noise mode 'ps2': every PS2-only noise triangle gets the PS2 noise UV, none is dropped, and on the shared vertices it equals
        # the PC noise UV modulo 1
        self.assertGreater(rep.get('tri_noise_uv_ps2', 0), 0)
        self.assertEqual(rep.get('tri_noise_dropped_no_pc_uv', 0), 0)
        import math
        import ps2_mesh
        import material_map as mm
        b = br.Builder(course)
        checked = 0
        for m in b.scene.meshes:
            if not any('noise' in br.tex_stem(t['name']).lower() for t in m['textures']):
                continue
            for idx in ps2_mesh.mesh_triangles(b.scene, m)[:50]:
                hit = b.pc_tris.get(mm.key([b.scene.position(i) for i in idx]))
                if not hit or len(hit[2]) < 3 or hit[2][2] != 'noise-tga':
                    continue
                pc = {tuple(round(c, 3) for c in b.pc.positions[v]): b.pc.uv_sets[1][v] for v in hit[1]}
                for i in idx:
                    u = pc.get(tuple(round(c, 3) for c in b.scene.position(i)))
                    if u is None:
                        continue
                    n = ps2_mesh.noise_uv(b.payload, i)
                    for k in range(2):
                        d = (u[k] - n[k]) % 1.0
                        self.assertLess(min(d, 1 - d), 1e-3)
                    checked += 1
        self.assertGreater(checked, 1000)
        # winding: wherever PC has the triangle single-sided, the output has PC's corner order (the rock foot at 2817/-519 was flipped by the
        # normal rule and culled, owner's fourth and seventh tests)
        self.assertEqual(rep.get('tri_winding_from_pc'), 1)
        out = {}
        for d in r.draws():
            for k in range(d.index_start, d.index_start + d.index_count, 3):
                P = [r.positions[d.vertex_base + r.indices[k + j]] for j in range(3)]
                out.setdefault(mm.key(P), set()).add(br.cyc([br.rkey(p) for p in P]))
        missing = [k for k, o in b.pc_orient.items() if len(o) == 1 and k in out and not (o & out[k])]
        self.assertEqual(missing, [])
        foot = [(2817.51, 31.2, -517.89), (2817.59, 30.94, -521.23), (2818.69, 31.94, -521.77)]

        def near(k):
            return all(any(max(abs(a - b) for a, b in zip(p, q)) < 0.01 for p in k) for q in foot)
        self.assertEqual(sum(1 for k in out if near(k)), 1)


class TemplateTests(unittest.TestCase):
    def test_alpha_class(self):
        self.assertEqual(br.alpha_class('01010101'), 'test')
        self.assertEqual(br.alpha_class('00010101'), 'test')
        self.assertEqual(br.alpha_class('01000001'), 'blend')
        self.assertEqual(br.alpha_class('01000101'), 'blend')
        self.assertEqual(br.alpha_class('00000101'), 'opaque')
        self.assertEqual(br.alpha_class('00000001'), 'opaque')
        self.assertEqual(br.cyc([(2, 0, 0), (0, 0, 0), (1, 0, 0)]), ((0, 0, 0), (1, 0, 0), (2, 0, 0)))

    @unittest.skipUnless(RETAIL.exists(), 'retail data not available')
    def test_italyw2_alphatest_gate_keeps_alpha_test(self):
        # ItalyW2: the first PC draw with gate01 is opaque; the unmatched triangles of the PS2 `$alphatest` gate took it (owner's fence test)
        import course_config as cc
        import ps2_mesh
        from master_rallye.course_render_writer import CourseRender
        course = cc.course('ItalyW2')
        data, _, rep = br.build(course, course.pc_dx.read_bytes())
        b = br.Builder(course)
        alpha_keys = set()
        for m in b.scene.meshes:
            if 'alphatest' in mm.directives(m['material']):
                alpha_keys.update(mm.key([b.scene.position(i) for i in idx]) for idx in ps2_mesh.mesh_triangles(b.scene, m))
        r = CourseRender.from_bytes(data)
        wrong = 0
        seen = 0
        for d in r.draws():
            for k in range(d.index_start, d.index_start + d.index_count, 3):
                if mm.key([r.positions[d.vertex_base + r.indices[k + j]] for j in range(3)]) in alpha_keys:
                    seen += 1
                    wrong += br.alpha_class(d.flags_0x20.hex()) != 'test'
        self.assertGreater(seen, 1000)
        self.assertEqual(wrong, 0)


if __name__ == '__main__':
    unittest.main()
