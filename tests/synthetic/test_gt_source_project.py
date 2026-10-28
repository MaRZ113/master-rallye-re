"""Source-selection persistence/history; compiler seams use synthetic fixtures."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from master_rallye.gt_source_project import GTSourceProject
from master_rallye.gt3_vehicle import digest
from tests.synthetic.test_workshop import family

class SourceProjectTests(unittest.TestCase):
    def test_auto_creation_requires_exact_source_and_original_colour_tables(self):
        from master_rallye.addon_sdk.gt3_scene import GT3_CORE_SHA256
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);source,donor,profile,db,strings,identity,output=self.fixture(root)
            report={'schema':'gt-garage-inventory/1','catalogs':{'us':{'vehicles':[{'car_key':'0x1','model_code':'test','association_status':'PASS','association_evidence':{'model_key':'0x2'}}]}},'members':{'cars/day/test':{'status':'PASS','sha256':digest(source.read_bytes())}},'source':{'sha256':'a'*64,'edition_files':{'CORE.GT3':{'sha256':GT3_CORE_SHA256}}},'colour_sources':{'catalog':{'decoded_sha256':digest(db.read_bytes())},'strings':{'decoded_sha256':digest(strings.read_bytes())}}}
            path=root/'inventory.json';path.write_text(json.dumps(report))
            with patch('master_rallye.gt_auto_profile.derive',return_value=(profile,{'fit':'explicit approximation'}))as derive,patch.object(GTSourceProject,'create')as create:
                p=GTSourceProject.create_auto(source,donor,path,'us','0x1',db,strings,identity,output,render_ui=None)
                self.assertEqual(p,create.return_value);self.assertEqual(derive.call_args.kwargs['model_key'],'0x2')
                with self.assertRaisesRegex(ValueError,'Exact source catalog'):GTSourceProject.create_auto(source,donor,path,'us','0x9',db,strings,identity,output,render_ui=None)
                source.write_bytes(b'wrong model')
                with self.assertRaisesRegex(ValueError,'hash mismatch'):GTSourceProject.create_auto(source,donor,path,'us','0x1',db,strings,identity,output,render_ui=None)
                source.write_bytes(b'synthetic-model');db.write_bytes(b'wrong colours')
                with self.assertRaisesRegex(ValueError,'color tables'):GTSourceProject.create_auto(source,donor,path,'us','0x1',db,strings,identity,output,render_ui=None)
                self.assertEqual(derive.call_count,1)

    def fixture(self,root):
        source=root/'source.bin';source.write_bytes(b'synthetic-model')
        db=root/'colours.db';db.write_bytes(b'synthetic-db');strings=root/'strings';strings.write_bytes(b'synthetic-names')
        return source,root/'donor',{'source_sha256':digest(source.read_bytes()),'model_key':'0x1'},db,strings,{'name':'Synthetic','family':'Fixture','manufacturer':'Fixture','model':'Fixture'},root/'project'

    def test_selection_reopen_undo_redo_restore_and_independent_manual_state(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);args=self.fixture(root)
            def compile(source,donor,profile,output,**kwargs):
                output.mkdir(parents=True);(output/'conversion-report.json').write_text(json.dumps({'colour':kwargs['colour']}))
            def author(candidate,donor,profile,output,**kwargs):family(output);return output
            def colour(c,key,i,model):return {'source_index':i,'latin_name':['Silver','Blue'][i]}
            with patch('master_rallye.gt_source_project.inspect_car',return_value={'body':{'source_colourway_count':2}}),patch('master_rallye.gt_source_project.catalog',return_value={}),patch('master_rallye.gt_source_project.select',side_effect=colour),patch('master_rallye.gt_source_project.build',side_effect=compile)as builder,patch('master_rallye.gt_source_project.prepare',side_effect=author):
                p=GTSourceProject.create(*args,render_ui=None);first=p.current();first.data['manual-test']='preserve';first.save()
                second=p.choose(1,render_ui=None);self.assertNotEqual(first.root,second.root);self.assertNotIn('manual-test',second.data)
                p=GTSourceProject(p.root);self.assertEqual(p.data['selected'],1);self.assertEqual(p.step().data['manual-test'],'preserve');self.assertEqual(p.data['selected'],0)
                p.step(True);self.assertEqual(p.data['selected'],1);p.restore();self.assertEqual(p.data['selected'],0);p.choose(1,render_ui=None)
                self.assertEqual(builder.call_count,2);self.assertEqual(args[0].read_bytes(),b'synthetic-model')
                with self.assertRaisesRegex(ValueError,'outside catalog'):p.choose(-1,render_ui=None)
                (p.root/'inputs/model.bin').write_bytes(b'drift')
                with self.assertRaisesRegex(ValueError,'immutable'):GTSourceProject(p.root)

    def test_bad_source_and_identity_fail_before_build(self):
        with tempfile.TemporaryDirectory()as t:
            args=list(self.fixture(Path(t)));args[2]['source_sha256']='0'*64
            with patch('master_rallye.gt_source_project.inspect_car',return_value={'body':{}}):
                with self.assertRaisesRegex(ValueError,'identity mismatch'):GTSourceProject.create(*args,render_ui=None)
            self.assertFalse(args[-1].exists())

if __name__=='__main__':unittest.main()
