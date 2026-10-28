"""Geometry conservation and fail-closed semantic aperture authoring."""
from dataclasses import replace
import math
import unittest
from unittest.mock import patch
from master_rallye.semantic_aperture import partition,compose_ledger
from master_rallye.fourrunner_visual_kit import box,options,apply
from master_rallye.topology_writer import CompiledVertex,DrawGeometry


class SemanticApertureTests(unittest.TestCase):
    def setUp(self):
        self.g=DrawGeometry(tuple(CompiledVertex((x,y,0.),(0.,0.,1.),bytes([10,20,30,255]),((x,y),(x*2,y*3)),i)
             for i,(x,y)in enumerate(((0.,0.),(2.,0.),(0.,2.)))),((0,1,2),))
        self.mask=[(.25,.25),(1.,.25),(1.,1.),(.25,1.)]

    def test_cut_conserves_area_winding_all_channels_and_source_barycentrics(self):
        before=repr(self.g);inside,outside,ledger=partition(self.g,[0],self.mask,uv_layer=0)
        def area(g):
            return sum(((g.vertices[b].position[0]-g.vertices[a].position[0])*(g.vertices[c].position[1]-g.vertices[a].position[1])-
                        (g.vertices[b].position[1]-g.vertices[a].position[1])*(g.vertices[c].position[0]-g.vertices[a].position[0]))/2 for a,b,c in g.triangles)
        self.assertAlmostEqual(area(inside)+area(outside),2.)
        self.assertAlmostEqual(area(inside),.75*.75)
        for side,g in (('inside',inside),('outside',outside)):
            for t,row in zip(g.triangles,ledger[side]):
                self.assertEqual(row['source_triangle'],0)
                for i,w in zip(t,row['barycentric']):
                    v=g.vertices[i];self.assertAlmostEqual(sum(w),1.)
                    self.assertEqual(v.position,tuple(sum(w[j]*self.g.vertices[j].position[k]for j in range(3))for k in range(3)))
                    self.assertEqual(v.uvs[1],(v.position[0]*2,v.position[1]*3))
                    self.assertEqual(v.color,bytes([10,20,30,255]));self.assertEqual(v.normal,(0.,0.,1.))
        self.assertEqual(before,repr(self.g))

    def test_outside_selection_is_exact_and_cut_is_deterministic(self):
        a=partition(self.g,[],self.mask,axes=(0,1));self.assertFalse(a[0].triangles)
        self.assertEqual(a[1].vertices,self.g.vertices)
        self.assertEqual(a,partition(self.g,[],self.mask,axes=(0,1)))
        self.assertEqual(partition(self.g,[0],self.mask,uv_layer=0),partition(self.g,[0],self.mask,uv_layer=0))

    def test_invalid_or_ambiguous_inputs_rejected(self):
        invalid=[{'uv_layer':0,'axes':(0,1)},{},{'axes':(0,0)},{'uv_layer':-1},{'uv_layer':3}]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):partition(self.g,[0],self.mask,**kwargs)
        for ids in ([1],[0,0],[-1]):
            with self.assertRaises(ValueError):partition(self.g,ids,self.mask,uv_layer=0)
        for polygon in ([(0,0)]*3,[(0,0),(1,1),(0,1),(1,0)],[(math.nan,0),(1,0),(0,1)]):
            with self.assertRaises(ValueError):partition(self.g,[0],polygon,uv_layer=0)
        with self.assertRaises(ValueError):partition(replace(self.g,triangles=((0,1,3),)),[0],self.mask,uv_layer=0)

    def test_resource_budgets_fail_before_unbounded_output(self):
        with patch('master_rallye.semantic_aperture.MAX_TRIANGLES',0),self.assertRaisesRegex(ValueError,'input budget'):
            partition(self.g,[0],self.mask,uv_layer=0)

    def test_chained_cut_retains_original_triangle_identity_and_barycentrics(self):
        a,b,first=partition(self.g,[0],self.mask,uv_layer=0)
        a2,b2,second=partition(b,range(len(b.triangles)),[(0.,0.),(.2,0.),(.2,2.),(0.,2.)],axes=(0,1))
        composed=compose_ledger(second['inside'],first['outside'])
        for tri,row in zip(a2.triangles,composed):
            self.assertEqual(row['source_triangle'],0)
            for i,w in zip(tri,row['barycentric']):
                for k in range(3):self.assertAlmostEqual(a2.vertices[i].position[k],sum(w[j]*self.g.vertices[j].position[k]for j in range(3)))

    def test_structure_is_closed_outward_and_has_no_blend_or_environment(self):
        part=box((-.1,-.2,-.3),(.1,.2,.3),'dark');g=part.geometry
        self.assertEqual(len(g.triangles),12);self.assertFalse(part.alpha);self.assertFalse(part.environment)
        for a,b,c in g.triangles:
            p,q,r=[g.vertices[i].position for i in (a,b,c)];u=[q[k]-p[k]for k in range(3)];v=[r[k]-p[k]for k in range(3)]
            n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            self.assertGreater(sum(n[k]*g.vertices[a].normal[k]for k in range(3)),0.)

    def test_optional_kit_off_changes_nothing_and_unknown_options_fail_closed(self):
        self.assertFalse(any(options(None).values()))
        for value in ({'guess_axles':True},{'cabin':1}):
            with self.assertRaises(ValueError):options(value)
        from master_rallye.scene_dx_writer import ScenePart
        p=ScenePart(self.g,('diffuse','Null','Null'))
        parts,core,report=apply([p],{'report':{'source_scene_sha256':'test'}},None,None,None,None,{'body_partition_ledger':[]})
        self.assertEqual(parts,[p]);self.assertEqual(core,[0]);self.assertFalse(report['components'])
        from master_rallye.fourrunner_semantics import author_apertures
        with self.assertRaisesRegex(ValueError,'exact reviewed source scene'):
            author_apertures({'report':{'body_draws':[],'source_scene_sha256':'unreviewed'}})
        with patch('master_rallye.semantic_aperture.MAX_OUTPUT_TRIANGLES',1),self.assertRaisesRegex(ValueError,'output budget'):
            partition(self.g,[0],self.mask,uv_layer=0)
