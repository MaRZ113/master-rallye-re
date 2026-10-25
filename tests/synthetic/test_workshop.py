import json
import struct
import tempfile
import unittest
from pathlib import Path
from master_rallye.workshop.service import WorkshopProject
from master_rallye.dxt import parse_dxt_bytes,encode_png
from tests.synthetic.test_library import simple_record,synthetic_dx,footer56

def family(root):
    root.mkdir(parents=True)
    points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
    record=bytearray(simple_record(0,2,0,3,('base-tga','Null','Null')))
    record[32:36]=bytes([0,0,1,1]);struct.pack_into('<I',record,36,3)
    raw=synthetic_dx(points,[0,1,2],[record],[(0,0,3)],trailing=footer56(points))
    for name in ('car.dx','complete.dx','wheel.dx'):(root/name).write_bytes(raw)
    texture=struct.pack('<5I',0xfeed,1,0,2,2)+bytes([50,100,200,128,20,60,80,255,40,50,60,0,70,80,90,64])
    (root/'base-tga.dxt').write_bytes(texture)
    return texture

class WorkshopTests(unittest.TestCase):
    def test_future_metadata_cannot_claim_native_execution(self):
        from master_rallye.workshop.adapters import validate_extensions,FORMATS
        self.assertTrue(any(f['id']=='mr-feed-bgra' for f in FORMATS))
        self.assertEqual(validate_extensions({'glass_panes':[{'id':'front','status':'PLANNED','data':{}}]})['glass_panes'][0]['id'],'front')
        for value in ({'fake_native':[]},{'glass_panes':[{'id':'front','status':'GAMEPLAY-VERIFIED','data':{}}]}):
            with self.assertRaises(ValueError):validate_extensions(value)
    def test_addon_png_override_uses_real_sdk_edit_contract(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);raw=family(r/'Navara');source=r/'author';source.mkdir()
            spec={'vehicle_name':'Navara','source_vehicle_dir':str(r/'Navara'),'resources':{},'texture_edits':{},'texture_replacements':{}}
            (source/'vehicle-project.json').write_text(json.dumps(spec));(source/'addon.json').write_text(json.dumps({'addon_id':'synthetic-workshop'}))
            p=WorkshopProject.create(source,r/'workshop');p.tint('base-tga.dxt',[.1,.5,1])
            self.assertEqual(p.validate()['status'],'PASS')
            from master_rallye.vehicle_project import VehicleProject,validate_vehicle
            compiled=validate_vehicle(VehicleProject.load(p.working/'vehicle-project.json'))['compiled']
            self.assertEqual(compiled['base-tga.dxt'],(p.assets/'base-tga.dxt').read_bytes())
            self.assertEqual(json.loads((source/'vehicle-project.json').read_text()),spec)
            p.restore();self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),raw)
            (r/'Navara/base-tga.dxt').write_bytes(b'drift')
            with self.assertRaisesRegex(ValueError,'Original author input'):p.verify_inputs()
    def test_non_destructive_edit_save_reload_restore_and_undo(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);original=family(r/'source');p=WorkshopProject.create(r/'source',r/'project')
            p.tint('base-tga.dxt',[.2,.4,1.]);first=(p.assets/'base-tga.dxt').read_bytes()
            self.assertNotEqual(first,original);self.assertEqual(first[23::4],original[23::4])
            self.assertEqual((r/'source/base-tga.dxt').read_bytes(),original)
            p.tint('base-tga.dxt',[1,.1,.1]);p.undo();self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),first)
            q=WorkshopProject(p.root);q.materialize();self.assertEqual((q.assets/'base-tga.dxt').read_bytes(),first)
            q.restore();self.assertEqual((q.assets/'base-tga.dxt').read_bytes(),original)
            self.assertEqual(q.validate()['status'],'PASS')

    def test_stock_real_core_zero_edit_and_changed_only(self):
        from master_rallye.addon_sdk.stock_project import build
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);original=family(r/'retail/DataGx/Vehicles/Megane')
            p=WorkshopProject.create(r/'retail',r/'workspace',kind='stock-new',family='Megane',car_id=18)
            self.assertTrue(build(p.working,r/'zero')['zero_edit'])
            p.tint('base-tga.dxt',[.1,.2,1]);m=build(p.working,r/'changed')
            self.assertEqual(list(m['resources']),['DataGx/Vehicles/Megane/base-tga.dxt'])
            self.assertEqual((r/'retail/DataGx/Vehicles/Megane/base-tga.dxt').read_bytes(),original)
            p.restore();self.assertTrue(build(p.working,r/'reset')['zero_edit'])

    def test_open_existing_stock_texture_edits_keeps_them(self):
        from master_rallye.addon_sdk.stock_project import create
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);original=family(r/'retail/DataGx/Vehicles/Megane');create(r/'retail',r/'stock','Megane',18)
            path=r/'stock/resources/DataGx/Vehicles/Megane/base-tga.dxt';edited=original[:20]+b'\x22'*16;path.write_bytes(edited)
            p=WorkshopProject.create(r/'stock',r/'workshop');self.assertEqual((p.assets/path.name).read_bytes(),edited)
            p.restore();self.assertEqual((p.assets/path.name).read_bytes(),original)

    def test_inspection_reports_actual_draws_textures(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);family(r/'source');p=WorkshopProject.create(r/'source',r/'project');info=p.inspect()
            self.assertEqual(info['vertices'],3);self.assertEqual(len(info['draws']),1)
            self.assertEqual(info['textures'][0]['width'],2);self.assertIn('approximation',info['preview'])

    def test_invalid_edits_and_input_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);family(r/'source');p=WorkshopProject.create(r/'source',r/'project')
            for values in ([float('nan'),1,1],[3,1,1],[True,1,1]):
                with self.assertRaises(ValueError):p.tint('base-tga.dxt',values)
            with self.assertRaises(ValueError):p.tint('../x.dxt',[1,1,1])
            (p.baseline/'base-tga.dxt').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):p.materialize()

    def test_png_replacement_orientation_and_size(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);raw=family(r/'source');p=WorkshopProject.create(r/'source',r/'project');image=r/'input.png';image.write_bytes(encode_png(parse_dxt_bytes(raw)))
            p.replace_png('base-tga.dxt',image);self.assertEqual((p.assets/'base-tga.dxt').read_bytes()[20:],raw[20:])
            wrong=struct.pack('<5I',0xfeed,1,0,1,1)+b'\xff'*4;image.write_bytes(encode_png(parse_dxt_bytes(wrong)))
            with self.assertRaises(ValueError):p.replace_png('base-tga.dxt',image)

    def test_source_destination_and_unsupported_stock(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);family(r/'source')
            with self.assertRaises(ValueError):WorkshopProject.create(r/'source',r/'source/project')
            with self.assertRaises(ValueError):WorkshopProject.create(r/'source',r/'wrong',kind='stock-new',family='Megane',car_id=0)

    def test_asset_only_build_discloses_non_installable(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);family(r/'source');p=WorkshopProject.create(r/'source',r/'project')
            result=p.build(r/'output',sdk_root=r);self.assertFalse(result['runtime_installable'])
            self.assertEqual((r/'output/assets/car.dx').read_bytes(),(r/'source/car.dx').read_bytes())

    def test_bmp_capture_conversion_is_bounded(self):
        from master_rallye.workshop.gui import bmp_png
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'s.bmp';p.write_bytes(b'bad')
            with self.assertRaises((ValueError,struct.error)):bmp_png(p)
