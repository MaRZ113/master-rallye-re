import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from master_rallye.dx import parse_dx_bytes
from master_rallye.surface_authoring import apply_surface_edits,surface_capabilities
from master_rallye.workshop.service import WorkshopProject
from tests.synthetic.test_workshop import family

class SurfaceAuthoringTests(unittest.TestCase):
    def test_disable_only_existing_environment_pass_preserves_ownership(self):
        from tests.synthetic.test_library import simple_record,synthetic_dx,footer56
        import struct
        points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)];record=bytearray(simple_record(0,2,0,3,('base-tga','base-tga','Null')));struct.pack_into('<I',record,36,7)
        raw=synthetic_dx(points,[0,1,2],[record],[(0,0,3)],trailing=footer56(points));before=parse_dx_bytes(raw)
        result=apply_surface_edits(raw,[{'draw_id':0,'disable_reflection':True}],source_sha256=hashlib.sha256(raw).hexdigest());after=parse_dx_bytes(result.data)
        self.assertEqual(after.physical_draws[0].unknown_0x24,3);self.assertEqual(before.vertices.colors,after.vertices.colors);self.assertEqual(before.physical_draws[0].texture_tuple,after.physical_draws[0].texture_tuple);self.assertEqual(before.physical_draws[0].flags_0x20,after.physical_draws[0].flags_0x20)

    def test_shared_vertex_conflict_is_not_silent_selective_editing(self):
        from tests.synthetic.test_library import simple_record,synthetic_dx,footer56
        points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
        record=bytearray(simple_record(0,2,0,3,('base-tga','Null','Null')));record[34]=1
        raw=synthetic_dx(points,[0,1,2],[record,record],[(0,0,3),(0,0,3)],trailing=footer56(points))
        caps=surface_capabilities(raw,0);self.assertEqual(caps['shared_vertex_draws'],[1]);self.assertFalse(caps['diffuse_rgb_editable'])
        with self.assertRaisesRegex(ValueError,'Shared vertex'):apply_surface_edits(raw,[{'draw_id':0,'rgb':[.1,1,1]}],source_sha256=hashlib.sha256(raw).hexdigest())

    def test_stock_scoped_override_and_zero_edit_restore(self):
        from master_rallye.addon_sdk import stock_project
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);family(r/'retail/DataGx/Vehicles/Megane');p=WorkshopProject.create(r/'retail',r/'workshop',kind='stock-new',family='Megane',car_id=18)
            p.edit_surface('complete.dx',0,rgb=[.1,.4,1]);report=stock_project.build(p.working,r/'edit');self.assertEqual(list(report['resources']),['DataGx/Vehicles/Megane/complete.dx'])
            p.undo();self.assertTrue(stock_project.build(p.working,r/'restored')['zero_edit'])

    def test_scoped_rgb_preserves_alpha_and_every_other_section(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);family(p/'source');raw=(p/'source/car.dx').read_bytes();source=parse_dx_bytes(raw)
            result=apply_surface_edits(raw,[{'draw_id':0,'rgb':[0,.5,1]}],source_sha256=hashlib.sha256(raw).hexdigest());m=parse_dx_bytes(result.data)
            self.assertEqual(m.vertices.colors[3::4],source.vertices.colors[3::4]);self.assertEqual(m.vertices.colors[0:3],bytes((source.vertices.colors[0],round(source.vertices.colors[1]*.5),0)))
            self.assertEqual(m.vertices.positions,source.vertices.positions);self.assertEqual(m.vertices.normals,source.vertices.normals);self.assertEqual(m.local_indices,source.local_indices);self.assertEqual(m.physical_draws,source.physical_draws)
            self.assertEqual(raw[:source.vertices.color_offset],result.data[:source.vertices.color_offset]);end=source.uv_count_offset;self.assertEqual(raw[end:],result.data[end:])

    def test_rejects_unsupported_flags_broken_pins_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);family(p/'source');raw=(p/'source/car.dx').read_bytes();pin=hashlib.sha256(raw).hexdigest()
            for recipe in ({'draw_id':0,'rgb':[float('nan'),1,1]},{'draw_id':0,'alpha':0},{'draw_id':99,'rgb':[1,1,1]},{'draw_id':0,'disable_reflection':True}):
                with self.assertRaises(ValueError):apply_surface_edits(raw,[recipe],source_sha256=pin)
            with self.assertRaises(ValueError):apply_surface_edits(raw,[],source_sha256='0'*64)

    def test_project_reopen_undo_redo_restore_preserves_textures(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);texture=family(r/'source');p=WorkshopProject.create(r/'source',r/'workshop');baseline=(p.assets/'car.dx').read_bytes()
            p.edit_surface('car.dx',0,rgb=[.1,.4,1]);edited=(p.assets/'car.dx').read_bytes();self.assertNotEqual(edited,baseline)
            p=WorkshopProject(p.root);p.materialize();self.assertEqual((p.assets/'car.dx').read_bytes(),edited);self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),texture)
            p.undo();self.assertEqual((p.assets/'car.dx').read_bytes(),baseline);p.redo();self.assertEqual((p.assets/'car.dx').read_bytes(),edited);p.restore();self.assertEqual((p.assets/'car.dx').read_bytes(),baseline)

    def test_addon_surface_edits_compile_through_shared_core(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);family(r/'Navara');source=r/'author';source.mkdir();(source/'addon.json').write_text(json.dumps({'addon_id':'surface-demo'}));(source/'vehicle-project.json').write_text(json.dumps({'vehicle_name':'Navara','source_vehicle_dir':str(r/'Navara'),'resources':{}}))
            p=WorkshopProject.create(source,r/'workshop');p.edit_surface('car.dx',0,rgb=[.1,.2,1]);p.validate()
            from master_rallye.vehicle_project import VehicleProject,validate_vehicle
            self.assertEqual(validate_vehicle(VehicleProject.load(p.working/'vehicle-project.json'))['compiled']['car.dx'],(p.assets/'car.dx').read_bytes())
            q=WorkshopProject.create(p.working,r/'second-workshop');q.edit_surface('car.dx',0,rgb=[.5,1,1])
            self.assertEqual(validate_vehicle(VehicleProject.load(q.working/'vehicle-project.json'))['compiled']['car.dx'],(q.assets/'car.dx').read_bytes())
            q.restore();self.assertEqual((q.assets/'car.dx').read_bytes(),(p.assets/'car.dx').read_bytes())
            p.restore();self.assertEqual(json.loads((p.working/'vehicle-project.json').read_text())['resources'],{})
