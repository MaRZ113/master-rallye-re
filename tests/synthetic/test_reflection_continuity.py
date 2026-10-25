"""Own generated topology; no game assets."""
import unittest,copy,tempfile
from pathlib import Path
from master_rallye.addon_sdk.reflection_continuity import audit
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from tests.synthetic.test_gt4_material_pipeline import scene
from tests.synthetic.test_gt4_material_pipeline import draws
from build_gt4_vehicle import compile_draws
from master_rallye.dxt import parse_dxt_bytes


class ContinuityTests(unittest.TestCase):
    def model(self,second_environment=False):
        template,_=scene()
        def geometry(points):
            return DrawGeometry(tuple(CompiledVertex(p,(0.,0.,1.),b'\xff'*4,((0.,0.),)) for p in points),((0,1,2),))
        return write_scene_dx(template,[
            ScenePart(geometry([(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]),('own','env','Null'),environment=True),
            ScenePart(geometry([(1.,0.,0.),(1.,1.,0.),(0.,1.,0.)]),('own','env' if second_environment else 'Null','Null'),environment=second_environment)])

    def test_detects_neighboring_mismatch_without_assigning_materials(self):
        data=self.model();r=audit(data,eligible_draws=[0,1]);self.assertEqual(r['neighbor_pairs'],1)
        self.assertEqual(r['warnings'][0]['draws'],[0,1]);self.assertAlmostEqual(r['reflected_area_m2'],.5)
        self.assertAlmostEqual(r['unreflected_area_m2'],.5)
        self.assertEqual(audit(data,eligible_draws=[0])['warnings'],[])
        self.assertEqual(audit(self.model(True),eligible_draws=[0,1])['warnings'],[])

    def test_rejects_unknown_selection_and_unbounded_tolerance(self):
        for tol in [0,float('nan'),1]:
            with self.assertRaises(ValueError):audit(self.model(),tolerance_m=tol)
        with self.assertRaises(ValueError):audit(self.model(),eligible_draws=[50])

    def test_binary_alpha_fallback_is_explicit_and_fail_closed(self):
        draw,_=draws([0]+[128]*15);draw['packet']=0;draw['gif']['blend']=True;draw['state']['alpha_test']=False
        policy={'binary_cutout_surfaces':[{'shape':7,'packets':[0],'role':'explicit diagnostic'}]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);baseline,_=compile_draws([draw],root);self.assertTrue(baseline[0].alpha);self.assertFalse(baseline[0].alpha_test)
            candidate,records=compile_draws([draw],root,material_policy=policy)
            self.assertTrue(candidate[0].alpha_test);self.assertTrue(records[0]['binary_cutout_approximation'])
            self.assertEqual(candidate[0].geometry,baseline[0].geometry)
            tex=parse_dxt_bytes((root/(candidate[0].textures[0]+'.dxt')).read_bytes());self.assertEqual(set(tex.bgra[3::4]),{0,255})
            for kind in ['partial_texture','partial_vertex','no_depth','missing']:
                bad=copy.deepcopy(draw)
                if kind=='partial_texture':bad['texture']['rgba_ps2']=bytes((100,120,140,64))*16
                elif kind=='partial_vertex':bad['vertices'][0]['rgba_ps2']=(128,128,128,64)
                elif kind=='no_depth':bad['state']['depth_write']=False
                else:bad['packet']=1
                with self.assertRaisesRegex(ValueError,'binary cutout'):compile_draws([bad],root,material_policy=policy)


if __name__=='__main__':unittest.main()
