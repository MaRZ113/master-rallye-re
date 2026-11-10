"""Preservation, transaction, provenance and actual BSP partition tests."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(Path(__file__).parent)]
from master_rallye.course_studio import CourseStudio, bsp_ray_intervals, exact_path
from master_rallye.course_bsp import Node, Leaf, encode_tag100
from master_rallye.course_tag100 import parse_course_tag100_bytes
from test_r5t_a import synthetic_course_dx
from test_course_race_authoring import g1_marker_source


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / 'original'
        self.folder = self.root / 'DataGx/Course/Example'
        self.folder.mkdir(parents=True)
        self.source = self.root / 'DataScene/RaceTest/Example.xml'
        self.source.parent.mkdir(parents=True)
        xml = g1_marker_source().replace(b'</EggLists_Version4>', b'<List Name="landscape"><Egg Name="landscape"><Value Name="en3d Model Name" Value="Course\\Example\\track"/></Egg></List><List Name="AI"><Egg Name="AI"><Value Name="AI DataSet Name" Value="ICont/Example"/></Egg></List></EggLists_Version4>')
        self.source.write_bytes(xml)
        bsp = encode_tag100(Node((0, 1, 0, 0), 0, Leaf(True), Leaf(False)))
        dx = synthetic_course_dx(); dx = dx[:dx.index(struct.pack('<I',100), 350)] + bsp
        (self.folder / 'track.dx').write_bytes(dx)
        (self.folder / 'opaque.bin').write_bytes(b'unknown original bytes')
        self.source.with_suffix('.hnt').write_bytes(b'Model [Course\\Example\\track]\r\n# unknown line\r\n')
        sfl = self.root / 'DataScene/ICont/Example.sfl'; sfl.parent.mkdir(parents=True)
        self.sfl = sfl
        sfl.write_bytes(struct.pack('<fIIff', 1, 2, 2, 0, 0) + bytes([0,1,2,3]))

    def tearDown(self): self.temp.cleanup()

    def session(self): return CourseStudio(self.source)

    def test_exact_paths_and_traversal(self):
        self.assertEqual(exact_path(self.root, 'datagx/course/example/track.dx'), (self.folder/'track.dx').resolve())
        with self.assertRaises(ValueError): exact_path(self.root, '../track.dx')

    def test_bsp_solid_empty_and_reverse_ray(self):
        bsp = parse_course_tag100_bytes(encode_tag100(Node((0,1,0,-2),0,Leaf(True),Leaf(False))))
        spans = bsp_ray_intervals(bsp,(0,0,0),(0,1,0),-10,10)
        self.assertEqual([(lo,hi,solid) for lo,hi,solid,_ in spans], [(-10,2,True),(2,10,False)])
        spans = bsp_ray_intervals(bsp,(0,0,0),(0,-1,0),-10,10)
        self.assertEqual([(lo,hi,solid) for lo,hi,solid,_ in spans], [(-10,-2,False),(-2,10,True)])

    def test_visual_patch_preserves_every_other_byte(self):
        session=self.session(); model=session.project.render._parsed_model
        before=session.project.resources.render_dx.read_bytes(); points=list(model.vertices.positions);points[0]=(0.25,0,0)
        session.set_visual_positions(points); after=session.geometry;at=model.vertices.position_offset
        self.assertEqual(before[:at],after[:at]);self.assertEqual(before[at+12:],after[at+12:])
        with self.assertRaises(ValueError): session.set_visual_positions(points[:-1])

    def test_source_and_output_protection(self):
        session=self.session()
        (self.folder/'opaque.bin').write_bytes(b'other work')
        self.assertTrue(any(f.severity=='ERROR' and 'changed' in f.message for f in session.validate()))
        with self.assertRaises(ValueError):session.export(self.base/'out')

    def test_template_texture_staging_preserves_header(self):
        texture=self.folder/'sample.dxt';header=struct.pack('<5I',0xFEED,4,123,1,1)
        texture.write_bytes(header+b'\0\0\0\xff');session=self.session()
        draft=self.base/'draft.dxt';draft.write_bytes(header+b'\x10\x20\x30\xff')
        session.stage_texture(texture,draft);session.export(self.base/'texture-out')
        self.assertEqual(texture.read_bytes(),header+b'\0\0\0\xff')
        self.assertEqual((self.base/'texture-out/resource-root/DataGx/Course/Example/sample.dxt').read_bytes(),draft.read_bytes())
        draft.write_bytes(struct.pack('<5I',0xFEED,4,124,1,1)+b'\0\0\0\xff')
        with self.assertRaises(ValueError):session.stage_texture(texture,draft)

    def test_new_registry_race_never_overrides_original_model(self):
        (self.folder/'sample.dxt').write_bytes(struct.pack('<5I',0xFEED,4,0,1,1)+b'\0\0\0\xff')
        self.source.with_suffix('.hnt').write_bytes(self.source.with_suffix('.hnt').read_bytes()+b'Texture [Course\\Example\\sample]\r\n')
        session=self.session();before=session.project.resources.render_dx.read_bytes()
        points=list(session.project.render.positions);points[0]=(0.25,0,0);session.set_visual_positions(points)
        session.editor.set_start_marker(0,(5,1,2))
        races=[dict(id=i,course='stock',scene='DataScene/RaceTest/Example.xml',icont='DataScene/ICont/Example.sfl',native_fields=[i]+[0]*8) for i in range(39)]
        doc=dict(schema='mr-course-registry/1',vehicle_count=26,courses=[dict(key='stock',folder='DataGx/Course/Example',model='DataGx/Course/Example/track.dx')],races=races)
        session.export(self.base/'registry',registry=doc,template_race_id=0,name='NewCourse')
        staged=self.base/'registry/resource-root'
        self.assertEqual((staged/'DataGx/Course/Example/track.dx').read_bytes(),before)
        self.assertNotEqual((staged/'DataGx/Course/NewCourse/track.dx').read_bytes(),before)
        self.assertEqual((staged/'DataScene/RaceTest/Example.xml').read_bytes(),self.source.read_bytes())
        catalog=json.loads((self.base/'registry/courses.json').read_text())
        self.assertEqual(catalog['races'][:39],races);self.assertEqual(catalog['races'][-1]['id'],39)
        overrides=json.loads((self.base/'registry/resource-overrides.json').read_text())
        self.assertTrue(all(key not in session.files for key in overrides))
        self.assertIn(b'Texture [Course\\NewCourse\\sample]',(staged/'DataScene/RaceTest/NewCourse.hnt').read_bytes())
        reopened=CourseStudio(self.base/'registry/course-studio.json')
        reopened.editor_routes=[dict(name='Free line',role='AI_PROPOSAL',paths=[[(0,0,0),(2,0,2)]],native_export=False)]
        reopened.export(self.base/'registry-again')
        saved=json.loads((self.base/'registry-again/courses.json').read_text())
        self.assertEqual(saved,catalog)
        again=CourseStudio(self.base/'registry-again/course-studio.json')
        self.assertEqual(again.race_id,39);self.assertEqual(again.editor_routes[0]['name'],'Free line')
        self.assertTrue(json.loads((self.base/'registry-again/resource-overrides.json').read_text()))

    def test_roundtrip_reproducible_and_unknown_preserved(self):
        session=self.session()
        errors=[f for f in session.validate() if f.severity=='ERROR']
        self.assertFalse(errors,errors)
        session.editor.set_start_marker(0,(0.5,1,2))
        first=session.export(self.base/'one');second=session.export(self.base/'two')
        self.assertEqual(first,second)
        self.assertEqual((self.base/'one/resource-root/DataGx/Course/Example/opaque.bin').read_bytes(),b'unknown original bytes')
        reopened=CourseStudio(self.base/'one/course-studio.json')
        self.assertEqual(reopened.project.race_logic.start_area.positions[0],(0.5,1,2))
        self.assertIn(b'UnknownNode', reopened.project.resources.race_test_xml.read_bytes())
        with self.assertRaises(FileExistsError):session.export(self.base/'one')
        with self.assertRaises(ValueError):session.export(self.root/'new')


if __name__ == '__main__': unittest.main()
