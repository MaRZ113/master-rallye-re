import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import replace
from master_rallye.dx import parse_dx_bytes
from master_rallye.texture_binding import binding_patch
from master_rallye.workshop.service import WorkshopProject
from tests.synthetic.test_workshop import family


class BindingTests(unittest.TestCase):
    def fixture(self,root):
        texture=family(root)
        alternate=bytearray(texture);alternate[20]=222
        (root/'next-tga.dxt').write_bytes(alternate)
        return texture,bytes(alternate)

    def test_exact_slot_bytes_only_shared_texture_not_other_draw(self):
        from tests.synthetic.test_library import simple_record,synthetic_dx,footer56
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';self.fixture(root)
            pts=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
            rec=simple_record(0,2,0,3,('base-tga','Null','Null'))
            raw=synthetic_dx(pts,[0,1,2],[rec,rec],[(0,0,3),(0,0,3)],trailing=footer56(pts))
            p=WorkshopProject.create(root,Path(td)/'workspace')
            output=binding_patch(raw,0,0,'next-tga',p.binding_texture)
            before,after=parse_dx_bytes(raw),parse_dx_bytes(output)
            self.assertEqual(after.physical_draws[0].texture_slots[0].value,'next-tga')
            self.assertEqual(after.physical_draws[1],before.physical_draws[1])
            s=before.physical_draws[0].texture_slots[0]
            self.assertEqual(raw[:s.data_offset],output[:s.data_offset]);self.assertEqual(raw[s.data_offset+len(s.raw):],output[s.data_offset+len(s.raw):])

    def test_history_reopen_and_addon_compile(self):
        from master_rallye.vehicle_project import VehicleProject,validate_vehicle
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);texture,alternate=self.fixture(r/'Navara');author=r/'author';author.mkdir()
            (author/'addon.json').write_text(json.dumps({'addon_id':'binding-test'}))
            (author/'vehicle-project.json').write_text(json.dumps({'vehicle_name':'Navara','source_vehicle_dir':str(r/'Navara'),'resources':{}}))
            p=WorkshopProject.create(author,r/'workspace');original=(p.assets/'car.dx').read_bytes()
            p.assign_existing_texture('car.dx',0,0,'next-tga');edited=(p.assets/'car.dx').read_bytes()
            self.assertNotEqual(original,edited)
            p=WorkshopProject(p.root);p.materialize();self.assertEqual((p.assets/'car.dx').read_bytes(),edited)
            compiled=validate_vehicle(VehicleProject.load(p.working/'vehicle-project.json'))['compiled'];self.assertEqual(compiled['car.dx'],edited)
            p.undo();self.assertEqual((p.assets/'car.dx').read_bytes(),original);p.redo();self.assertEqual((p.assets/'car.dx').read_bytes(),edited)
            p.restore();self.assertEqual((p.assets/'car.dx').read_bytes(),original)
            self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),texture);self.assertEqual((p.assets/'next-tga.dxt').read_bytes(),alternate)

    def test_rejections_leave_history_and_resources_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r/'source');p=WorkshopProject.create(r/'source',r/'workspace');state=p._state();raw=(p.assets/'car.dx').read_bytes()
            for slot,target in ((1,'next-tga'),(0,'../next-tga'),(0,'Null'),(0,'longer-name'),(0,'none-tga')):
                with self.assertRaises(ValueError):p.assign_existing_texture('car.dx',0,slot,target)
            altered=bytearray((p.assets/'next-tga.dxt').read_bytes());altered[23]^=1;(p.assets/'next-tga.dxt').write_bytes(altered)
            with self.assertRaisesRegex(ValueError,'alpha'):p.assign_existing_texture('car.dx',0,0,'next-tga')
            self.assertEqual(p._state(),state);self.assertEqual((p.assets/'car.dx').read_bytes(),raw)

    def test_aliased_descriptor_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r/'source');p=WorkshopProject.create(r/'source',r/'workspace');raw=(p.assets/'car.dx').read_bytes();m=parse_dx_bytes(raw)
            d=m.physical_draws[0];aliased=replace(d,draw_index=999)
            from types import SimpleNamespace
            m=SimpleNamespace(diagnostics=m.diagnostics,physical_draws=(d,aliased))
            with patch('master_rallye.texture_binding.parse_dx_bytes',return_value=m):
                with self.assertRaisesRegex(ValueError,'aliased'):binding_patch(raw,0,0,'next-tga',p.binding_texture)

    def test_offline_help_fallback_and_path_rejection(self):
        from master_rallye.workshop.help_view import load_topics
        root=Path(__file__).resolve().parents[2]/'docs/sdk/help'
        self.assertEqual(load_topics(root),load_topics(root,'ru'))
        self.assertGreaterEqual(len(load_topics(root)),6)
        with self.assertRaises(ValueError):load_topics(root,'../../')
