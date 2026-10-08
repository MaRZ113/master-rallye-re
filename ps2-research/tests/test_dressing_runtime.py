"""DRESSING1 synthetic ownership invariants and optional canonical byte probes."""
import itertools
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import dressing_runtime as d
import geometry_delta as g

A = ((0., 0., 0.), (2., 0., 0.), (0., 0., 2.))
B = ((2., 0., 0.), (2., 0., 2.), (0., 0., 2.))
IDENTITY = [[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]


def face(name, points=A, indices=(0,1,2), group='synthetic'):
    return g.Face(name, group, tuple(points), indices)


class ComponentTests(unittest.TestCase):
    def test_source_indices_and_welded_edges_are_distinct(self):
        fs=[face('a'), face('b',B,(3,4,5))]
        self.assertEqual(len(d.components(fs,'source_index')),2)
        self.assertEqual(len(d.components(fs,'coordinate_edge')),1)

    def test_touching_vertex_is_not_whole_edge(self):
        other=(A[0],(-2.,0.,0.),(0.,0.,-2.))
        fs=[face('a'),face('b',other,(3,4,5))]
        self.assertEqual(len(d.components(fs,'coordinate_vertex')),1)
        self.assertEqual(len(d.components(fs,'coordinate_edge')),2)

    def test_disconnected_parts_do_not_acquire_instance_count(self):
        fs=[face('a'),face('b',tuple((x+10,y,z) for x,y,z in A),(3,4,5))]
        result=d.component_summary(fs,'coordinate_edge')
        self.assertEqual(result['count'],2)
        self.assertTrue(all(x['instance_count']=='UNKNOWN' for x in result['components']))

    def test_repeated_lod_geometry_and_helpers_are_retained(self):
        fs=[face('lod0'),face('lod1',A,(3,4,5),'alternative'),face('shadow',A,(6,7,8),'helper')]
        result=d.component_summary(fs,'coordinate_edge')['components'][0]
        self.assertEqual(result['source_faces'],3)
        self.assertEqual(len(result['groups']),3)
        self.assertEqual(result['identity'],'GEOMETRIC_COMPONENT')

    def test_degenerate_zero_edges_do_not_join_unrelated_faces(self):
        fs=[face('a',(A[0],)*3),face('b',(A[0],)*3,(3,4,5))]
        self.assertEqual(len(d.components(fs,'coordinate_edge')),2)

    def test_component_identifiers_survive_input_reordering(self):
        fs=[face('z'),face('a',B,(3,4,5))]
        for method in d.METHODS:
            a=d.component_summary(fs,method);b=d.component_summary(list(reversed(fs)),method)
            self.assertEqual(a,b)

    def test_rounding_sensitivity_is_explicit(self):
        shifted=tuple((x+.00002,y,z) for x,y,z in A)
        fs=[face('a'),face('b',shifted,(3,4,5))]
        self.assertEqual(len(d.components(fs,decimals=4)),1)
        self.assertEqual(len(d.components(fs,decimals=5)),2)

    def test_unknown_method_and_missing_indices_fail(self):
        with self.assertRaises(g.t.FormatError):d.components([face('a')],'objects')
        with self.assertRaises(g.t.FormatError):d.components([face('a',indices=())],'source_index')
        with self.assertRaises(g.t.FormatError):face('bad',((math.nan,0.,0.),A[1],A[2]))


class OwnershipTests(unittest.TestCase):
    def test_multiple_meshes_one_carrier_and_one_mesh_multiple_carriers(self):
        rows=[{'source':'synthetic','name':'one','meshes':['a','b'],'carrier_id':'entity1','matrix':IDENTITY},
              {'source':'synthetic','name':'two','meshes':['a'],'carrier_id':'entity2','matrix':IDENTITY}]
        result=d.authored_instances(rows)
        self.assertEqual(len(result),2)
        self.assertTrue(all(x['identity']=='INDEPENDENT_TRANSFORM_INSTANCE' for x in result))
        self.assertNotEqual(result[0]['reference_id'],result[1]['reference_id'])

    def test_duplicate_authored_references_are_not_deduplicated(self):
        row={'source':'synthetic','name':'duplicate','matrix':IDENTITY}
        result=d.authored_instances([row,row])
        self.assertEqual(len(result),2)
        self.assertNotEqual(result[0]['reference_id'],result[1]['reference_id'])
        self.assertTrue(all(x['identity']=='AUTHORED_SCENE_REFERENCE' for x in result))

    def test_missing_transform_and_baked_source_are_unknown(self):
        result=d.authored_instances([{'name':'baked mesh'},{'name':'spline','matrix':IDENTITY}])
        self.assertEqual(result[0]['transform_status'],'UNKNOWN')
        self.assertTrue(all(x['runtime_pose']=='UNKNOWN' and x['live_visible']=='UNKNOWN' for x in result))

    def test_mirror_singular_nonfinite(self):
        mirror=[r[:] for r in IDENTITY];mirror[0][0]=-1
        self.assertEqual(d.transform_status(mirror),'MIRRORED_AUTHORED_TRANSFORM')
        for v in (0.,math.inf,math.nan):
            bad=[r[:] for r in IDENTITY];bad[0][0]=v
            with self.assertRaises(g.t.FormatError):d.transform_status(bad)

    def test_hierarchy_preserves_source_offsets(self):
        nodes=[{'path':'root','tag':1,'offset':32,'children':2},
               {'path':'root.0','tag':5,'offset':40,'children':0},
               {'path':'root.1','tag':2,'offset':48,'children':0}]
        self.assertEqual(d.validate_hierarchy(nodes)['root.1']['offset'],48)
        for changed in (nodes+[nodes[-1]],nodes[1:],
                        [dict(nodes[0],children=1)]+nodes[1:],
                        [nodes[0],dict(nodes[1],path='root.0.0'),nodes[2]],
                        [dict(nodes[0],tag=99)]+nodes[1:]):
            with self.assertRaises(g.t.FormatError):d.validate_hierarchy(changed)

    def test_stable_source_identity_independent_of_material_label(self):
        self.assertEqual(d.stable_id('sha',64,'component'),d.stable_id('sha',64,'component'))
        self.assertNotEqual(d.stable_id('sha',64,'component'),d.stable_id('sha',65,'component'))


class ShapeTests(unittest.TestCase):
    def test_rotation_translation_and_permutations(self):
        source=[face('a'),face('b',B,(1,3,2))]
        def transform(p):x,y,z=p;return (z+100,y+5,-x+20)
        target=[face('pc'+str(i),tuple(transform(p) for p in tri),(i*3,i*3+1,i*3+2),'pc')
                for i,tri in enumerate((A,B))]
        result=d.rigid_shape_search(source,target,tolerance=.001)
        self.assertTrue(result['matches'])
        self.assertEqual(result['placement'],'UNKNOWN')
        self.assertTrue(all(x['transform_provenance'].startswith('FITTED_DIAGNOSTIC') for x in result['matches']))

    def test_uniform_scale_is_separate_from_unit_rigid(self):
        target=[face('pc',tuple((x*2,y*2,z*2) for x,y,z in A),'')]
        self.assertFalse(d.rigid_shape_search([face('a')],target)['matches'])
        self.assertTrue(d.rigid_shape_search([face('a')],target,scale_range=(.5,2.))['matches'])

    def test_partial_and_deformed_shapes_do_not_match(self):
        source=[face('a'),face('b',B,(1,3,2))]
        self.assertFalse(d.rigid_shape_search(source,[face('pc')])['matches'])
        self.assertFalse(d.rigid_shape_search([face('a')],[face('pc',((0.,0.,0.),(3.,0.,0.),(0.,0.,2.)))])['matches'])

    def test_degenerate_empty_and_budget_fail_closed(self):
        self.assertFalse(d.rigid_shape_search([],[])['matches'])
        self.assertTrue(d.rigid_shape_search([face('zero',(A[0],)*3)],[face('pc')])['degenerate'])
        with self.assertRaises(g.t.FormatError):d.rigid_shape_search([face('a')],[face('pc')],budget=1)


class SphereTests(unittest.TestCase):
    def evaluate(self,r=1.,center=(0.,0.,0.),range_value=None,planes=None):
        return d.sphere_eligibility(r,center,(0.,0.,0.),(0.,0.,-1.),planes or [(0.,0.,0.)]*4,range_value)

    def test_positive_radius_and_optional_range(self):
        self.assertTrue(self.evaluate()['eligible'])
        self.assertFalse(self.evaluate(r=0)['eligible'])
        self.assertTrue(self.evaluate(center=(5.,0.,0.),range_value=4.)['eligible'])
        self.assertEqual(self.evaluate(center=(5.01,0.,0.),range_value=4.)['reason'],'OUTSIDE_RANGE_PLUS_RADIUS')

    def test_side_planes_equality_rejects(self):
        planes=[(1.,0.,0.)]+[(0.,0.,0.)]*3
        self.assertTrue(self.evaluate(center=(.999,0.,0.),planes=planes)['eligible'])
        self.assertEqual(self.evaluate(center=(1.,0.,0.),planes=planes)['reason'],'OUTSIDE_SIDE_PLANE')

    def test_direction_bound_only_if_range_descriptor_exists(self):
        self.assertTrue(self.evaluate(center=(0.,0.,-2.))['eligible'])
        self.assertEqual(self.evaluate(center=(0.,0.,-2.),range_value=10.)['reason'],'BEHIND_DIRECTION_BOUNDARY')
        self.assertTrue(self.evaluate(center=(0.,0.,-1.),range_value=10.)['eligible'])

    def test_precision_and_nonfinite_fail_closed(self):
        self.assertEqual(self.evaluate()['precision'],'FLOAT32_RECONSTRUCTION')
        for value in (math.nan,math.inf,1e100):
            with self.assertRaises(g.t.FormatError):self.evaluate(r=value)


class OriginalDressing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        values=[os.environ.get(x) for x in ('MASTER_RALLYE_PS2_INPUT','MASTER_RALLYE_PC_INPUT','MASTER_RALLYE_COURSE_SDK')]
        if not all(values):raise unittest.SkipTest('DRESSING1 canonical PS2/PC/SDK external roots not supplied')
        cls.roots=list(map(Path,values))

    def test_four_candidate_original_bytes_and_decomposition(self):
        manifest,_=g.t.load_pak(self.roots[0]/'TNG.PAK');cache={}
        expected=[(256,16),(139,12),(113,7),(64,4)]
        frozen=json.loads((g.ROOT/'dressing1/novel-candidates.json').read_text())['candidates']
        for (course,offset,name),(count,components),card in zip(d.CANDIDATES,expected,frozen):
            with self.subTest(candidate=name):
                if course not in cache:
                    a,b,_=g.load_pair(*self.roots,course)
                    payload,_=d.payload_for(manifest,self.roots[0],a.source['path'])
                    cache[course]=(a,b,payload)
                a,b,payload=cache[course]
                self.assertEqual(struct.unpack_from('<I',payload,offset)[0],2)
                owner=next(x for x in a.groups.values() if x['node_offset']==offset)
                self.assertTrue(payload[owner['material_offset']:].startswith(owner['material'].encode('ascii')))
                gid=next(k for k,v in a.groups.items() if v['node_offset']==offset)
                fs=[f for f in a.faces if f.group==gid]
                self.assertEqual(len(fs),count);self.assertEqual(len(d.components(fs)),components)
                self.assertEqual(card['source_id'],gid)
                self.assertEqual(card['instance_count'],'UNKNOWN')
                self.assertEqual(card['shape']['bounds'],g.bounds(p for f in fs for p in f.points))

    def test_original_dispatch_and_sphere_instruction_words(self):
        data=(self.roots[0]/'SLES_509.06').read_bytes()
        self.assertEqual(g.t.sha(data),'b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2')
        words={0x488440+0x5c:0x003b93f0,0x488560+0x5c:0x003c1148,
               0x488078+0x5c:0x003b9258,0x3b95d4:0x0000102d,
               0x3b93ec:0x0080102d,0x200688:0x4600a036,0x3c1e6c:0xac470000}
        for va,expected in words.items():
            with self.subTest(va=hex(va)):
                self.assertEqual(struct.unpack_from('<I',data,va-0xff000)[0],expected)

    def test_geom1_source_totals_and_frozen_exact_results(self):
        frozen=json.loads((g.ROOT/'dressing1/geom1-preservation.json').read_text())
        for row in frozen:
            with self.subTest(course=row['course']):
                a,_,_=g.load_pair(*self.roots,row['course'])
                self.assertEqual(len(a.faces),row['source_faces'])
                self.assertEqual(row['exact_matches'],{'TURKEY3':36001,'FRANCE1':41620,'ITALY_S1':39682}[row['course']])

    def test_whole_boat_group_congruency_at_different_placement(self):
        a,b,_=g.load_pair(*self.roots,'TURKEY3')
        gid=next(k for k,v in a.groups.items() if v['node_offset']==3583641)
        fs=[f for f in a.faces if f.group==gid]
        target=[f for f in b.faces if b.groups[f.group]['draw_index'] in (96,263,825)]
        result=d.rigid_shape_search(fs,target,tolerance=.001)
        self.assertEqual(len(result['matches']),1)
        match=result['matches'][0]
        self.assertEqual(match['source_faces'],113)
        self.assertEqual([b.groups[k]['draw_index'] for k in match['target_groups']],[825])
        self.assertLess(match['maximum_corner_residual'],.000395)
        self.assertEqual(match['scale'],1.)
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(g.dot(match['rotation_rows'][i],match['rotation_rows'][j]),float(i==j),places=8)


if __name__=='__main__':unittest.main()
