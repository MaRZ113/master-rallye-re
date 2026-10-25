import copy,tempfile,unittest
from pathlib import Path
from master_rallye.addon_sdk.gt4_layered import opaque_layered_surfaces
from tests.synthetic.test_gt4_material_pipeline import draws


class LayeredTests(unittest.TestCase):
    def fixture(self):
        base,env=draws([128]*16);base.update(packet=0);base['gif']['blend']=True;base['state'].update(alpha_test=False,fbmask=0xff000000,cull=False)
        for d in [base,*env]:d['texture'] and d['texture']['registers'].update(width=4,height=4,min_u=0,max_u=3,min_v=0,max_v=3)
        for e in env:e['state']['date']=False
        alpha=copy.deepcopy(base);alpha['state'].update(fbmask=0xffffff,depth_write=False);alpha['gif']['blend']=False
        alpha['source_shape']=8;alpha['texture']['rgba_ps2']=bytes([100,120,140,40])*16
        for i,e in enumerate(env):e.update(source_shape=9,packet=i)
        return [base,alpha,*env],[{'shape':7,'packets':[0],'role':'fixture opaque frame'}]

    def test_alpha_only_weight_is_not_source_opacity(self):
        ds,p=self.fixture();out=opaque_layered_surfaces(ds,p);surface=out[0]
        self.assertFalse(surface['gif']['blend']);self.assertEqual(set(surface['texture']['rgba_ps2'][3::4]),{40})
        self.assertEqual(surface['vertices'],ds[0]['vertices']);self.assertEqual(surface['triangles'],ds[0]['triangles'])
        self.assertIn('_mr_paint_reflection',surface)

    def test_ambiguous_missing_or_uv_mismatch_fail_closed(self):
        for mutation in ('duplicate','missing','uv'):
            ds,p=self.fixture()
            if mutation=='duplicate':ds.append(copy.deepcopy(ds[1]))
            if mutation=='missing':ds.pop()
            if mutation=='uv':ds[1]['vertices'][0]['uv']=(.1,.2)
            with self.assertRaises(ValueError):opaque_layered_surfaces(ds,p)

    def test_source_cull_disable_creates_independent_backfaces(self):
        from build_gt4_vehicle import compile_draws
        ds,_=self.fixture();d=ds[0];d['gif']['blend']=False;d['state'].update(fbmask=0,cull=False)
        with tempfile.TemporaryDirectory() as td:
            a,_=compile_draws([d],Path(td));b,r=compile_draws([d],Path(td),material_policy={'source_backfaces':True})
            self.assertEqual(len(b[0].geometry.triangles),2*len(a[0].geometry.triangles));self.assertTrue(r[0]['source_cull_backfaces'])
            count=len(a[0].geometry.vertices);self.assertEqual(b[0].geometry.triangles[-1],tuple(v+count for v in reversed(a[0].geometry.triangles[-1])))
