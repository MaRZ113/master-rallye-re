"""Synthetic geometry invariants plus optional independent canonical anchors."""
import itertools
import json
import math
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import geometry_delta as g

A=((0.,0.,0.),(2.,0.,0.),(0.,0.,2.))
B=((2.,0.,0.),(2.,0.,2.),(0.,0.,2.))


def face(name,points): return g.Face(name,'group',tuple(points))
def match(a,b,profile='baseline'):
    return g.direction_match([face('a'+str(i),t) for i,t in enumerate(a)],
                             [face('b'+str(i),t) for i,t in enumerate(b)],g.PROFILES[profile],'PS2_EXTRA_VISUAL_SOURCE')[0]


class MatchTests(unittest.TestCase):
    def test_permutations_and_winding_preserved(self):
        for p in itertools.permutations(A):
            with self.subTest(p=p):
                row=match([A],[p])[0]
                self.assertEqual(row['geometry_relation'],'EXACT_TRIANGLE_MATCH')
                self.assertEqual(row['maximum_corner_error'],0.)
                self.assertIn(row['raw_order_parity'],(0,1))

    def test_changed_diagonal_is_same_surface(self):
        other=[(A[0],A[1],B[1]),(A[0],B[1],A[2])]
        for row in match([A,B],other):
            self.assertEqual(row['geometry_relation'],'SAME_SURFACE_DIFFERENT_TRIANGULATION')
            self.assertAlmostEqual(row['coverage'],1.)
        self.assertTrue(all(x['coverage']==1. for x in match(other,[A,B])))

    def test_four_triangle_fan_and_t_junction(self):
        center=(1.,0.,1.);corners=[A[0],A[1],B[1],A[2]]
        fan=[(corners[i],corners[(i+1)%4],center) for i in range(4)]
        self.assertTrue(all(x['coverage']==1. for x in match([A,B],fan)))
        split=[(A[0],A[1],center),(A[0],center,A[2])]
        self.assertEqual(match([A],split)[0]['geometry_relation'],'SAME_SURFACE_DIFFERENT_TRIANGULATION')

    def test_duplicate_covers_do_not_inflate_union(self):
        half=(A[0],(1.,0.,0.),A[2])
        self.assertAlmostEqual(g.union_coverage(A,[half,half]),.5)
        row=match([A],[half,half])[0]
        self.assertEqual(row['geometry_relation'],'PARTIAL_SURFACE_OVERLAP')
        self.assertAlmostEqual(row['coverage'],.5)
        self.assertEqual(match([A],[A,A])[0]['correspondence_multiplicity'],2)

    def test_parallel_surfaces_not_equivalent(self):
        for y in (.002,.5,2.):
            other=[tuple((x,y,z) for x,_,z in A)]
            row=match([A],other)[0]
            self.assertNotIn(row['geometry_relation'],('EXACT_TRIANGLE_MATCH','SAME_SURFACE_DIFFERENT_TRIANGULATION'))
            self.assertEqual(row['coverage'],0.)
        self.assertEqual(match([A],[tuple((x,2.,z) for x,_,z in A)])[0]['geometry_relation'],'PS2_EXTRA_VISUAL_SOURCE')

    def test_disjoint_shifted_and_partial_surfaces(self):
        shifted=tuple((x+10,y,z) for x,y,z in A)
        self.assertEqual(match([A],[shifted])[0]['geometry_relation'],'PS2_EXTRA_VISUAL_SOURCE')
        partly=tuple((x+1,y,z) for x,y,z in A)
        row=match([A],[partly])[0]
        self.assertEqual(row['geometry_relation'],'PARTIAL_SURFACE_OVERLAP')
        self.assertAlmostEqual(row['coverage'],.25)

    def test_degenerate_tiny_and_nonfinite(self):
        for tri in [(A[0],A[0],A[1]),((0.,0.,0.),(1e-5,0.,0.),(0.,0.,1e-5))]:
            self.assertEqual(match([tri],[A])[0]['geometry_relation'],'DIAGNOSTIC_DEGENERATE')
        with self.assertRaises(g.t.FormatError): face('bad',((math.nan,0,0),A[1],A[2]))
        with self.assertRaises(g.t.FormatError): g.SpatialIndex([face('a',A)],cell=math.inf)

    def test_mirror_and_vertical_plane(self):
        mirrored=tuple((-x,y,z) for x,y,z in A)
        self.assertNotEqual(match([A],[mirrored])[0]['geometry_relation'],'EXACT_TRIANGLE_MATCH')
        upright=tuple((x,z,0.) for x,_,z in A)
        half=tuple((x,z,0.) for x,_,z in (A[0],(1.,0.,0.),A[2]))
        self.assertAlmostEqual(g.union_coverage(upright,[half]),.5)

    def test_numeric_boundary_and_sensitivity(self):
        shifted=tuple((x+.0005,y,z) for x,y,z in A)
        self.assertEqual(match([A],[shifted])[0]['geometry_relation'],'EXACT_TRIANGLE_MATCH')
        self.assertNotEqual(match([A],[shifted],'strict')[0]['geometry_relation'],'EXACT_TRIANGLE_MATCH')
        shifted=tuple((x,y+.005,z) for x,y,z in A)
        self.assertNotEqual(match([A],[shifted])[0]['geometry_relation'],'EXACT_TRIANGLE_MATCH')
        self.assertEqual(match([A],[shifted],'relaxed')[0]['geometry_relation'],'EXACT_TRIANGLE_MATCH')

    def test_plane_gate_prevents_crossed_surface_false_union(self):
        sloped=(A[0],(2.,1.,0.),A[2])
        row=match([A],[sloped])[0]
        self.assertEqual(row['coverage'],0.)

    def test_index_budget_fail_closed(self):
        with self.assertRaises(g.t.FormatError):g.SpatialIndex([face('a',A)],cell=.001,max_cells=10)
        with self.assertRaises(g.t.FormatError):g.local_output(Path('ps2-research/geom1/mesh.obj'))

    def test_material_independent_of_geometry_and_ambiguity(self):
        p={'textures':['course/foo/water-tga'],'material':'water $shader(puddle)'}
        q={'textures':['water-tga','Null','Null'],'materials':['water $shader(water)']}
        self.assertEqual(g.material_relation(p,q),'DIFFERENT_SHADER_SEMANTICS')
        q['materials'].append('other $shader(water)')
        self.assertEqual(g.material_relation(p,q),'UNRESOLVED_MATERIAL_MAPPING')
        q['textures'][0]='rock-tga'
        self.assertEqual(g.material_relation(p,q),'DIFFERENT_TEXTURE_BINDING')

    def test_repeatable_relations_and_stable_source_ids(self):
        self.assertEqual(json.dumps(match([A,B],[A,B]),sort_keys=True),json.dumps(match([A,B],[A,B]),sort_keys=True))
        self.assertEqual(match([A],[A])[0]['source'],match([A],[A],'strict')[0]['source'])
        self.assertEqual(g.vertex_agreement([A[0],A[0]],A,.001)['source_unique_numeric_positions'],1)

    def test_signed_zero_bitwise_is_not_numeric_equality(self):
        result=g.vertex_agreement([(0.,0.,0.),(-0.,0.,0.)],[(0.,0.,0.)],.001)
        self.assertEqual(result['source_unique_numeric_positions'],1)
        self.assertEqual(result['source_unique_bitwise_positions'],2)
        self.assertEqual(result['bitwise_float32_matches'],1)

    def test_transform_cannot_be_fitted_to_force_equivalence(self):
        m=[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
        g.require_identity_transform(m)
        m[3][0]=2.
        with self.assertRaises(g.t.FormatError):g.require_identity_transform(m)

    def test_standalone_terminator_does_not_relax_landscape_reader(self):
        from test_reflection_runtime import synthetic_vehicle
        import struct
        data=bytearray(synthetic_vehicle())
        struct.pack_into('<I',data,len(data)-4,0xffffffff)
        # It contains tag7/8: standalone GEOM1 reader must still reject them.
        with self.assertRaises(g.t.FormatError):g.ps2_adapter(bytes(data),'SYNTHETIC',standalone=True)
        with self.assertRaises(g.t.FormatError):g.w.decode_scene(bytes(data))


class OriginalAnchors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        values=[os.environ.get(x) for x in ('MASTER_RALLYE_PS2_INPUT','MASTER_RALLYE_PC_INPUT','MASTER_RALLYE_COURSE_SDK')]
        if not all(values):raise unittest.SkipTest('GEOM1 canonical PS2/PC/SDK external roots not supplied')
        cls.roots=list(map(Path,values))
        g.w.verify_inputs(cls.roots[0])

    def test_standalone_dinghy_original_boundary(self):
        import struct
        manifest,_=g.t.load_pak(self.roots[0]/'TNG.PAK')
        hashes=[]
        for name in ('BLUEDINGHY','REDDINGHY'):
            entry=next(e for e in manifest['entries'] if e['path'].endswith('DINGHYS\\'+name+'.PSM'))
            payload,_=g.t.read_payload(entry,self.roots[0]/'TNG.000')
            self.assertEqual(len(payload),3420)
            self.assertEqual(struct.unpack_from('<I',payload,3416)[0],0xffffffff)
            scene=g.ps2_adapter(payload,entry['path'],standalone=True)
            self.assertEqual(len(scene.faces),24)
            hashes.append(g.t.sha(b''.join(struct.pack('<3f',*p) for p in scene.positions)))
            with self.assertRaises(g.t.FormatError):g.ps2_adapter(payload,entry['path'])
            with self.assertRaises(g.t.FormatError):g.ps2_adapter(payload+b'\0',entry['path'],standalone=True)
        self.assertEqual(*hashes)

    def test_water_and_nonwater_original_anchors(self):
        expected={'TURKEY3':(745,0),'FRANCE1':(3586,3586),'ITALY_S1':(1329,1329)}
        for course,(count,hits) in expected.items():
            with self.subTest(course=course):
                a,b,align=g.load_pair(*self.roots,course)
                water=[f.points for f in a.faces if g.w.shader_contract(a.groups[f.group]['material'])['water_mode'] is not None and g.w.area_normal(f.points)[0]>g.AREA_EPSILON]
                pc=[(f.points,b.groups[f.group]['draw_index']) for f in b.faces]
                result=g.w.match_geometry(water,pc,b.positions,a.positions)
                self.assertEqual(len(water),count)
                self.assertEqual(result['triangle_matches'],hits)
                # An ordinary group selected by its original texture/owner offset
                # in frozen GEOM1 metadata, independently of water filtering.
                anchor=json.loads((g.ROOT/'geom1'/'nonwater-anchors.json').read_text())[course]
                group=next(k for k,v in a.groups.items() if v['node_offset']==anchor['ps2_node_offset'])
                rows,_=g.direction_match([f for f in a.faces if f.group==group],b.faces,g.PROFILES['baseline'],'PS2_EXTRA_VISUAL_SOURCE')
                self.assertEqual(sum(r['geometry_relation']=='EXACT_TRIANGLE_MATCH' for r in rows),anchor['exact_faces'])
                self.assertEqual(align['transform'],'IDENTITY_IN_SOURCE_FRAME; NO_FIT')
                # Independent original-byte probes, not coordinates obtained from
                # the new adapters. Verify tag/material and both position banks.
                import struct
                manifest,_=g.t.load_pak(self.roots[0]/'TNG.PAK')
                entry=next(e for e in manifest['entries'] if e['path']==a.source['path'])
                payload,_=g.t.read_payload(entry,self.roots[0]/'TNG.000')
                self.assertEqual(struct.unpack_from('<I',payload,anchor['ps2_node_offset'])[0],2)
                self.assertTrue(payload[anchor['material_offset']:].startswith(anchor['material'].encode('ascii')))
                raw_pc=(self.roots[1]/b.source['path']).read_bytes()
                direct_a=tuple(struct.unpack_from('<3f',payload,32+52*i+36) for i in anchor['ps2_source_vertex_indices'])
                direct_b=tuple(struct.unpack_from('<3f',raw_pc,anchor['pc_position_array_offset']+12*i) for i in anchor['pc_source_vertex_indices'])
                self.assertAlmostEqual(g.w.corner_error(direct_a,direct_b),anchor['sample_corner_error'])


if __name__=='__main__':unittest.main()
