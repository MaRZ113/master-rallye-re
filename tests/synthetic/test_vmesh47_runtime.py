"""Reflective masks, constant black closures and coordinated tyre profile."""
import math
import tempfile
import unittest
from pathlib import Path
from tools import vmesh_geometry as geo,vmesh_materials as vm,vmesh_lod0 as lod,vmesh_wheels as wh,vmesh_surface_repair as sr
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import CompiledVertex,DrawGeometry,rebuild_topology,source_geometry
from tests.synthetic.test_vmesh_geometry import DONOR_DIR,HAVE_DONOR,_png
from tests.synthetic.test_vmesh_lod0 import write_assets
from tests.synthetic.test_vmesh_materials import SPECIAL,RESERVED


@unittest.skipUnless(HAVE_DONOR,'retail donor unavailable')
class NewPolicyTests(unittest.TestCase):
    def test_reflective_paint_mask_keeps_real_helper_and_valid_test_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);obj=write_assets(p);gt=geo.parse_gt_full(obj)
            (p/'paint.png').write_bytes(_png(8,8,lambda x,y:(30,50,200,255 if x<4 else 0)))
            cl=lod.Lod0Classifier(gt['faces'],gt['textures'])
            donor={n:(DONOR_DIR/n).read_bytes() for n in ('car.dx','complete.dx')}
            plan=vm.MaterialPlan(gt['faces'],gt['textures'],cl,1,donor,DONOR_DIR,SPECIAL,RESERVED,
                                 structural_coverage=True,reflective_paint_masks=True)
            masks=[pool for pool in plan.pools if pool.pass_=='reflective_cutout']
            self.assertTrue(masks)
            images=plan.pool_images()
            for pool in masks:
                self.assertTrue(pool.alpha_test)
                self.assertTrue(parse_dx_bytes(donor['car.dx']).physical_draws[pool.draws['car.dx']].unknown_0x24&4)
                self.assertEqual(set(images[pool.name+'.dxt'][2][3::4]),{0,148})
                self.assertTrue(plan.alpha_toggles['car.dx'][pool.draws['car.dx']])
                self.assertTrue(plan.alpha_test_toggles['car.dx'][pool.draws['car.dx']])

    def test_constant_zero_black_is_retained_but_paint_clear_stays_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);gt=geo.parse_gt_full(write_assets(p))
            tri=gt['faces'][0][2];f=p/'black.png';f.write_bytes(_png(1,1,lambda x,y:(0,0,0,0)))
            gt['textures']['Mat6_Constant']=f;gt['textures']['Mat1_Clear']=f
            gt['faces'] += [('solid','Mat6_Constant',tri),('overlay','Mat1_Clear',tri)]
            cl=lod.Lod0Classifier(gt['faces'],gt['textures']);donor={n:(DONOR_DIR/n).read_bytes() for n in ('car.dx','complete.dx')}
            cl.lamp_objects.add('solid')
            plan=vm.MaterialPlan(gt['faces'],gt['textures'],cl,1,donor,DONOR_DIR,SPECIAL,RESERVED,
                                 structural_coverage=True,solid_black_swatches=True,lamp_glass=True)
            self.assertEqual(plan.textures['Mat6_Constant'].alpha,bytes([255]))
            self.assertEqual(plan.textures['Mat1_Clear'].alpha,bytes([0]))
            self.assertEqual(plan.routes[len(gt['faces'])-2][0],'head_lamp')
            self.assertIsNotNone(plan.lamp_glass_uv)
            self.assertNotIn(-1,plan.routes)
            glass=next(p for p in plan.pools if p.role=='glass')
            self.assertFalse(getattr(glass,'alpha_test',False))
            self.assertIn(67,plan.pool_images()[glass.name+'.dxt'][2][3::4])

    def test_profile_ratio_and_tread_material_are_coordinated(self):
        donor=(DONOR_DIR/'wheel.dx').read_bytes()
        data,r=wh.convert(donor,rim_draw=3,rim_ratio=.8)
        self.assertAlmostEqual(r['rim_radius']/r['tyre_radius'],.8)
        old,new=parse_dx_bytes(donor),parse_dx_bytes(data)
        self.assertAlmostEqual(max(abs(p[0]) for p in new.vertices.positions),max(abs(p[0]) for p in old.vertices.positions),places=6)
        self.assertAlmostEqual(max(math.hypot(*p[1:]) for p in new.vertices.positions),r['tyre_radius'],places=6)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'disc.png';p.write_bytes(_png(32,32,lambda x,y:(110,100,50,255)))
            images,report=wh.texture_images(data,DONOR_DIR,p,r)
            self.assertIn('merctread-tga.dxt',images)
            self.assertTrue(all(a==0 for a in images['merctread-tga.dxt'][2][3::4]))
        with self.assertRaises(ValueError):wh.convert(donor,rim_draw=3,rim_ratio=.99)

    def test_only_bounded_paired_edges_are_bridged(self):
        source=(DONOR_DIR/'car.dx').read_bytes()
        def run(gap):
            ps=[[(0,0,0),(1,0,0),(0,-.1,0)],[(0,gap,0),(1,gap,0),(1,gap+.1,0)]]
            edits={d:DrawGeometry(tuple(CompiledVertex(p,(0,0,1),bytes([255]*4),((0,0),)) for p in pts),((0,1,2),)) for d,pts in zip((4,5),ps)}
            data=rebuild_topology(source,edits,bounds_mode='recompute').data
            faces=[('a','paint',[(p,None,(i,0),(0,0)) for i,p in enumerate(pts)]) for pts in ps]
            class Classifier:
                z_front=0.;length=5.
                def _decide(self,o,m):return ('paint','test')
            class Plan:_cls={0:('paint','opaque'),1:('paint','opaque')}
            result,report=sr.repair(data,faces,Classifier(),Plan(),lambda p:p,[{'face':i,'draw':d,'tri':0} for i,d in enumerate((4,5))])
            for d in (4,5):self.assertEqual(source_geometry(parse_dx_bytes(result))[d],source_geometry(parse_dx_bytes(data))[d])
            return report
        self.assertTrue(run(.01)['bridges'])
        self.assertFalse(run(.04)['bridges'])


if __name__=='__main__':unittest.main()
