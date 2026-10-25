import copy,math,unittest
from master_rallye.addon_sdk.visibility_keepout import apply_keepouts,append_source_housings


def vertex(p):return {'position':p,'uv':(p[1],p[2]),'normal':(1.,0.,0.),'rgba_ps2':None}
def fixture():
    target={'source_shape':1,'packet':0,'issues':[],'vertices':[vertex(p) for p in [(0.5,-1.,-1.),(.5,2.,-1.),(.5,2.,2.),(.5,-1.,2.),(3.,0.,0.),(3.,1.,0.),(3.,0.,1.)]],'triangles':[(0,1,2),(0,2,3),(4,5,6)]}
    protect={'source_shape':2,'packet':0,'issues':[],'vertices':[vertex(p) for p in [(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]],'triangles':[(0,1,2),(0,3,1),(0,2,3),(1,3,2)]}
    policy=[{'source_sha256':'a'*64,'target':{'shape':1,'packet':0},'protect':{'shape':2,'packet':0},'role':'own synthetic overlapping surface fixture'}]
    return [target,protect],policy


class KeepoutTests(unittest.TestCase):
    def test_closed_source_box_subtraction_preserves_nonintersections_and_attributes(self):
        draws,policy=fixture();before=copy.deepcopy(draws);after,records=apply_keepouts(draws,policy,'a'*64)
        self.assertEqual(draws,before);self.assertEqual(after[1],before[1]);self.assertIn((4,5,6),after[0]['triangles'])
        area=0.
        for tri in after[0]['triangles']:
            vs=[after[0]['vertices'][i] for i in tri];ps=[v['position'] for v in vs];u=[ps[1][k]-ps[0][k] for k in range(3)];v=[ps[2][k]-ps[0][k] for k in range(3)];cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);area+=math.sqrt(sum(x*x for x in cross))/2
            centre=[sum(p[k] for p in ps)/3 for k in range(3)]
            self.assertFalse(all(1e-6<c<1-1e-6 for c in centre))
            for item in vs:self.assertEqual(item['uv'],(item['position'][1],item['position'][2]))
        self.assertAlmostEqual(area,8.5);self.assertEqual(records[0]['intersecting_source_triangles'],2)
        self.assertEqual(apply_keepouts(draws,policy,'a'*64),(after,records))

    def test_bad_source_selection_and_unclosed_volume_fail(self):
        draws,policy=fixture()
        with self.assertRaisesRegex(ValueError,'source pin'):apply_keepouts(draws,policy,'b'*64)
        wrong=copy.deepcopy(policy);wrong[0]['target']['shape']=50
        with self.assertRaisesRegex(ValueError,'uniquely'):apply_keepouts(draws,wrong,'a'*64)
        for v in draws[1]['vertices']:v['position']=(0.,v['position'][1],v['position'][2])
        with self.assertRaisesRegex(ValueError,'not closed'):apply_keepouts(draws,policy,'a'*64)


class HousingTests(unittest.TestCase):
    def test_source_bounds_generate_open_front_inward_box_and_preserve_source(self):
        draws,_=fixture();draws[1]['state']={};draws[1]['gif']={};before=copy.deepcopy(draws)
        policy=[{'source_sha256':'a'*64,'aperture':{'shape':1,'packet':0},'interior':{'shape':2,'packet':0},'front_axis':0,'front_sign':-1,'role':'own fixture explicit MR fallback'}]
        result,reports=append_source_housings(draws,policy,'a'*64)
        self.assertEqual(draws,before);self.assertEqual(result[:2],before);self.assertEqual(len(result[-1]['triangles']),20)
        self.assertEqual(result[-1]['component'],'derived_housing');self.assertIsNone(result[-1]['texture'])
        self.assertTrue(all(v['rgba_ps2']==(0,0,0,128) for v in result[-1]['vertices']))
        self.assertEqual(append_source_housings(draws,policy,'a'*64),(result,reports))
        caps=copy.deepcopy(policy);caps[0]['mode']='rear_cap'
        capped,cap_reports=append_source_housings(draws,caps,'a'*64)
        self.assertEqual(len(capped[-1]['triangles']),4)
        self.assertEqual(capped[:2],before)
        self.assertEqual(cap_reports[0]['mode'],'rear_cap')
        for tri in capped[-1]['triangles']:
            points=[capped[-1]['vertices'][i]['position'] for i in tri]
            self.assertEqual(len({p[0] for p in points}),1)
        wrong_mode=copy.deepcopy(policy);wrong_mode[0]['mode']='unknown'
        with self.assertRaisesRegex(ValueError,'declaration'):append_source_housings(draws,wrong_mode,'a'*64)
        with self.assertRaisesRegex(ValueError,'declaration'):append_source_housings(draws,policy,'b'*64)
        wrong=copy.deepcopy(policy);wrong[0]['aperture']['shape']=99
        with self.assertRaisesRegex(ValueError,'uniquely'):append_source_housings(draws,wrong,'a'*64)
        draws[1]['vertices'][0]['morph_target']={'position':(0,0,0)}
        with self.assertRaisesRegex(ValueError,'morph'):append_source_housings(draws,policy,'a'*64)

if __name__=='__main__':unittest.main()


