import copy
import unittest
import tempfile
from pathlib import Path
from master_rallye.course_registry import validate_manifest,storage_layout,resource_path,identity_contract


class CourseRegistryTests(unittest.TestCase):
    def setUp(self):
        self.base=[{'id':i,'scene':f'DataScene/RaceTest/R{i}.xml','native_fields':[i,0,0,0,0,0,0,0xffffffff,0xffffffff]} for i in range(39)]
        self.doc={'schema':'mr-course-registry/1','vehicle_count':35,'courses':[{'key':'test:geometry','folder':'DataGx/Course/Test','model':'DataGx/Course/Test/Test.dx'}],
                  'races':[{**copy.deepcopy(r),'course':'test:geometry','icont':'DataScene/ICont/Test.sfl'} for r in self.base]}

    def test_shared_layout_and_arithmetic(self):
        self.assertEqual(storage_layout(26,39)['allocation_size'],0xc00)
        self.assertEqual(storage_layout(35,39)['race_base'],0x720)
        for count in (127,128,254,255,256,257,513):
            self.assertEqual(storage_layout(35,count)['allocation_size'],0x720+44*count)
        self.assertEqual(storage_layout(35,128)['race_lifecycle_encoding'],'push-imm32-required')
        with self.assertRaises(ValueError):storage_layout(35,1<<31)

    def test_preserve_and_share_geometry(self):
        d=validate_manifest(self.doc,self.base)
        self.assertEqual(len(d['courses']),1)
        self.assertFalse(d['runtime_qualified'])
        self.doc['races'][0]['native_fields'][1]=1
        with self.assertRaises(ValueError):validate_manifest(self.doc,self.base)

    def test_missing_and_duplicate_identity(self):
        self.doc['races'][-1]['id']=0
        with self.assertRaises(ValueError):validate_manifest(self.doc,self.base)
        self.doc['races'][-1]['id']=38;self.doc['races'][-1]['course']='missing'
        with self.assertRaises(ValueError):validate_manifest(self.doc,self.base)

    def test_dont_enable_unimplemented_stage_routes(self):
        self.doc['competitions']=[{'key':'test:new','races':[0,1],'runtime_enabled':True}]
        with self.assertRaises(ValueError):validate_manifest(self.doc,self.base)

    def test_portable_paths_and_artwork_independence(self):
        for p in ('../test','/test','C:/test','A\\B','A//../B'):
            with self.assertRaises(ValueError):resource_path(p)
        a=validate_manifest(self.doc,self.base);b=copy.deepcopy(a);b['artwork']='paint.png'
        self.assertEqual(identity_contract(a),identity_contract(b))

    def test_resource_bindings_are_not_just_existing_filenames(self):
        from tools.course_capacity_audit import check_resources
        catalog=validate_manifest(self.doc,self.base);catalog['races']=catalog['races'][:1]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('DataScene/RaceTest/R0.xml','DataScene/RaceTest/R0.hnt','DataScene/ICont/Test.sfl','DataGx/Course/Test/Test.dx'):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
            scene=root/'DataScene/RaceTest/R0.xml'
            xml='<Scene><Egg Name="landscape"><Value Name="en3d Model Name" Value="Course/Test/Test"/></Egg><Value Name="AI DataSet Name" Value="ICont/Test"/></Scene>'
            scene.write_text(xml);check_resources(catalog,root)
            scene.write_text(xml.replace('ICont/Test','ICont/Other'))
            with self.assertRaisesRegex(ValueError,'Scene/AI'):check_resources(catalog,root)
            scene.write_text(xml);(root/'DataGx/Course/Test/Test.dx').unlink()
            with self.assertRaisesRegex(ValueError,'Missing catalog'):check_resources(catalog,root)
