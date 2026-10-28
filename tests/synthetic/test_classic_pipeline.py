"""Source-scoped Classic stage tests, without proprietary fixtures."""
import copy,tempfile,unittest
from pathlib import Path
from master_rallye.classic_style import convert,digest
from tests.synthetic.test_workshop import family

class SemanticClassicTests(unittest.TestCase):
    def fixture(self,root):
        root=root/'source';family(root);resources={p.name:p.read_bytes()for p in root.iterdir()if p.suffix in ('.dx','.dxt')}
        recipe={'version':2,'source_format':'GT3 ModelSet1','source_identity':{'source_sha256':'synthetic'},'class_reference':{'class':'T2','evidence':'synthetic reference only'},'source_models':{n:digest(v)for n,v in resources.items()},'stock_wheel_sha256':digest(resources['wheel.dx']),'stock_brake_sha256':digest(resources['car.dx']),'roles':[],'limitations':['Synthetic stage test; no runtime claim']}
        return resources,recipe
    def test_unknown_roles_preserved_and_source_is_immutable(self):
        with tempfile.TemporaryDirectory()as t:
            r,p=self.fixture(Path(t));before=copy.deepcopy(r);out,audit,maps=convert(r,p,r['wheel.dx'],r['car.dx'])
            self.assertEqual(out,r);self.assertEqual(r,before);self.assertFalse(audit['runtime_qualified']);self.assertEqual(audit['before'],audit['after'])
            self.assertEqual(maps['car.dx'],{0:0})
            self.assertEqual(convert(r,p,r['wheel.dx'],r['car.dx'])[1],audit)
    def test_missing_approval_rejects_destructive_operation(self):
        with tempfile.TemporaryDirectory()as t:
            r,p=self.fixture(Path(t));p['omit_decal_draws']={'car.dx':[0]}
            with self.assertRaisesRegex(ValueError,'semantic roles'):convert(r,p,r['wheel.dx'],r['car.dx'])
            p['roles']=[{'resource':'car.dx','draw':0,'role':'glass','evidence':'synthetic glass approval'}]
            with self.assertRaisesRegex(ValueError,'semantic roles'):convert(r,p,r['wheel.dx'],r['car.dx'])
    def test_drift_unpinned_texture_and_unknown_stages_fail_closed(self):
        with tempfile.TemporaryDirectory()as t:
            r,p=self.fixture(Path(t));p['source_models']['car.dx']='0'*64
            with self.assertRaisesRegex(ValueError,'immutable'):convert(r,p,r['wheel.dx'],r['car.dx'])
            p['source_models']['car.dx']=digest(r['car.dx']);del p['source_models']['base-tga.dxt']
            with self.assertRaisesRegex(ValueError,'identities incomplete'):convert(r,p,r['wheel.dx'],r['car.dx'])
            p['experimental_decimate_everything']=True
            with self.assertRaisesRegex(ValueError,'Unknown semantic'):convert(r,p,r['wheel.dx'],r['car.dx'])

if __name__=='__main__':unittest.main()
