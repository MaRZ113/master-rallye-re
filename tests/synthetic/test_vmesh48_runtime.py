"""Coverage/reflection separation, lamp welding, stock tyres and private decals."""
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from tools import vmesh_geometry as geo,vmesh_materials as vm,vmesh_lod0 as lod,vmesh_wheels as wh,vmesh_surface_repair as sr,vmesh_decal_authoring as da
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt,decode_rgba_pixels,PNG_ROWS_FLIP_VERTICAL
from master_rallye.topology_writer import source_geometry
from tests.synthetic.test_vmesh_geometry import DONOR_DIR,HAVE_DONOR,_png
from tests.synthetic.test_vmesh_lod0 import write_assets
from tests.synthetic.test_vmesh_materials import SPECIAL,RESERVED


@unittest.skipUnless(HAVE_DONOR,'retail donor unavailable')
class NormalizationTests(unittest.TestCase):
    def test_mask_coverage_255_and_helper_brightness_are_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);gt=geo.parse_gt_full(write_assets(p))
            (p/'paint.png').write_bytes(_png(8,8,lambda x,y:(30,50,200,0 if x>4 else 65 if x==0 else 255)))
            cl=lod.Lod0Classifier(gt['faces'],gt['textures']);donor={n:(DONOR_DIR/n).read_bytes() for n in ('car.dx','complete.dx')}
            plan=vm.MaterialPlan(gt['faces'],gt['textures'],cl,1,donor,DONOR_DIR,SPECIAL,RESERVED,
                                 structural_coverage=True,reflective_paint_masks=True,reflection_in_helpers=True)
            images=plan.pool_images();masks=[p for p in plan.pools if p.pass_=='reflective_cutout'];self.assertTrue(masks)
            for pool in masks:self.assertEqual(set(images[pool.name+'.dxt'][2][3::4]),{0,255})
            edits,report=vm.normalize_environment_helpers(plan,donor,DONOR_DIR)
            self.assertIn(report['canonical_helper']+'.dxt',edits)
            self.assertTrue(all(row['brightness_scale']==.58 for row in report['edits']))
            source=parse_dxt(DONOR_DIR/(report['canonical_helper']+'.dxt'));px=decode_rgba_pixels(source,PNG_ROWS_FLIP_VERTICAL)
            actual=edits[report['canonical_helper']+'.dxt'][2]
            for i in range(0,len(px),4):
                for k in range(3):self.assertLessEqual(abs(actual[i+k]-px[i+k]*148/255),1)

    def test_paint_control_alpha_palette_is_conservative(self):
        import gtmat
        def tex(clear=(0,23,65),mid=65):
            return gtmat.GtTexture(_png(8,8,lambda x,y: (*clear,0) if x<2 else (8,8,8,mid) if x==2 else (0,27,69,255)))
        self.assertEqual(vm.paint_control_alpha_evidence(tex())['zero_alpha_texels_restored'],16)
        self.assertIsNone(vm.paint_control_alpha_evidence(tex(mid=255)))
        self.assertIsNone(vm.paint_control_alpha_evidence(tex(clear=(0,0,0))))
        self.assertIsNone(vm.paint_control_alpha_evidence(tex(clear=(0,4,26))))

    def test_priority_decals_get_largest_non_environment_atlas(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);gt=geo.parse_gt_full(write_assets(p));(p/'paint.png').write_bytes(_png(8,8,lambda x,y:(180,200,20,0 if x>4 else 255)))
            cl=lod.Lod0Classifier(gt['faces'],gt['textures']);donor={n:(DONOR_DIR/n).read_bytes() for n in ('car.dx','complete.dx')}
            plan=vm.MaterialPlan(gt['faces'],gt['textures'],cl,1,donor,DONOR_DIR,SPECIAL,RESERVED,
                                 structural_coverage=True,decal_priority=True)
            decals=[p for p in plan.pools if p.pass_=='decal_cutout'];self.assertTrue(decals)
            self.assertEqual(max(p.width for p in decals),128)
            for p in decals:self.assertFalse(parse_dx_bytes(donor['car.dx']).physical_draws[p.draws['car.dx']].unknown_0x24&4)

    def test_tread_preserved_and_source_alpha_darkens_solid_spoke_gaps(self):
        data,report=wh.convert((DONOR_DIR/'wheel.dx').read_bytes(),rim_draw=3,rim_ratio=.8)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'rim.png';p.write_bytes(_png(16,16,lambda x,y:(100,90,50,255 if x<8 else 0)))
            images,r=wh.texture_images(data,DONOR_DIR,p,report,preserve_tyre=True,dark_spoke_gaps=True)
            self.assertNotIn('merctread-tga.dxt',images)
            w,h,px=images['nevwheel-tga.dxt'];i=(h//2*w+3*w//4)*4
            self.assertEqual(px[i:i+4],bytes((9,10,12,0)))
            self.assertEqual(parse_dx_bytes(data).physical_draws[3].flags_0x20[0],0)

    def test_glass_shared_edges_use_identical_vertices(self):
        source=(DONOR_DIR/'car.dx').read_bytes();old=source_geometry(parse_dx_bytes(source))[35]
        ps=[(0,0,0),(1,0,0),(0,1,0),(1,1,0)]
        def tri(ids,n):return [(ps[i],n,(i,0),(0,0)) for i in ids]
        faces=[('lamp','lens',tri((0,1,2),(0,0,1))),('lamp','lens',tri((1,3,2),(.1,0,.99))),
               ('part_reflection','none',tri((0,1,2),(0,0,1))),('part_reflection','none',tri((1,3,2),(.1,0,.99)))]
        class Classifier:
            z_front=0.;length=5.;lamp_objects={'lamp'}
            def _decide(self,o,m):return ('head_lamp' if o=='lamp' else 'exclude','test')
        plan=SimpleNamespace(_cls={},lamp_glass_uv=(.5,.5),decal_materials=set())
        data,report=sr.repair(source,faces,Classifier(),plan,lambda p:p,[],glass_draw=35,weld_lenses=True)
        new=source_geometry(parse_dx_bytes(data))[35]
        self.assertEqual(len(new.vertices)-len(old.vertices),4)
        self.assertTrue(report['lamp_glass']['shared_vertices'])
        for v in new.vertices[len(old.vertices):]:self.assertAlmostEqual(math.sqrt(sum(x*x for x in v.normal)),1,places=5)

    def test_planar_recess_gets_bounded_collar(self):
        source=(DONOR_DIR/'car.dx').read_bytes();ps=[(-.4,0,0),(.4,0,0),(-.4,.2,0),(.4,.2,0)]
        faces=[('panel','black',[(ps[i],(0,0,1),(i,0),(0,0)) for i in ids]) for ids in ((0,1,2),(1,3,2))]
        faces.append(('body','black',[(p,(0,0,1),(i,0),(0,0)) for i,p in enumerate(((-1,0,2),(1,0,2),(0,1,2)))]))
        rear=[(-.3,.2,4.8),(.3,.2,4.8),(-.3,.4,4.8),(.3,.4,4.8),(-.3,.2,4.7),(-.3,.4,4.7)]
        for ids in ((0,1,2),(1,3,2),(0,2,4),(2,5,4)):
            faces.append(('rearbox','black',[(rear[i],(0,0,1),(i,0),(0,0)) for i in ids]))
        class Classifier:
            z_front=0.;length=5.;lamp_objects=set()
            def _decide(self,o,m):return ('black','test')
        tex=SimpleNamespace(mean_color=lambda:((10,10,10),1))
        plan=SimpleNamespace(_cls={i:('black','opaque') for i in range(len(faces))},lamp_glass_uv=None,decal_materials=set(),textures={'black':tex})
        data,r=sr.repair(source,faces,Classifier(),plan,lambda p:p,[],close_recesses=True)
        self.assertEqual(len(r['recess_collars']),2)
        self.assertEqual(sum(p['rear'] for p in r['recess_collars']),1)
        self.assertEqual(r['recess_collars'][0]['padding_m'],.025)

    def test_private_rear_decal_binding_has_explicit_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);old=p/'old.png';old.write_bytes(_png(1,1,lambda x,y:(0,20,100,0)))
            new=p/'new.png';new.write_bytes(_png(8,8,lambda x,y:(160,200,40,255)))
            points=[(-.3,.5,2),(.3,.5,2),(0,.8,2)]
            gt={'faces':[('rear','placeholder',[(q,None,(i,0),(0,0)) for i,q in enumerate(points)])],'textures':{'placeholder':old}}
            class Classifier:
                z_front=-2.;length=4.
                def _decide(self,o,m):return ('paint','test')
            r=da.bind_rear_placeholder(gt,Classifier(),new)
            self.assertEqual(gt['textures']['placeholder'],new)
            self.assertNotEqual(r['original_texture_sha256'],r['authored_texture_sha256'])


if __name__=='__main__':unittest.main()
