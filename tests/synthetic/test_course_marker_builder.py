import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(Path(__file__).parent)]
from master_rallye.course_marker_builder import add_split,remove_split,place_area,reorder_split_ids
from master_rallye.course_race_authoring import CourseRaceLogicAuthoring
from test_course_race_authoring import source_fixture


class BuilderTests(unittest.TestCase):
    def test_add_remove_is_exact_inverse_and_sphere_center_is_real(self):
        raw=source_fixture();added,audit=add_split(raw,(100,200,300),radius=50)
        editor=CourseRaceLogicAuthoring(added)
        self.assertEqual(len(editor.split_status),2)
        new=editor.split_status[-1]
        self.assertEqual(new.center,(100,200,300));self.assertEqual(new.radius,50);self.assertEqual(new.split_id,1)
        self.assertEqual(new.extra_time_raw,editor.split_status[0].extra_time_raw)
        self.assertIn(b'<UnknownNode Raw="keep">',added)
        removed,_=remove_split(added,1)
        # Only insertion whitespace remains; all old element bytes survive.
        self.assertEqual(removed.replace(b'\n',b''),raw.replace(b'\n',b''))
        self.assertEqual(audit['runtime'],'REQUIRES_OWNER_TEST')

    def test_area_updates_only_known_values(self):
        raw=source_fixture();output,_=place_area(raw,'StartArea',(50,2,30),half_width=10,half_depth=5)
        editor=CourseRaceLogicAuthoring(output)
        self.assertEqual(editor.area_status[0].positions[0],(40,2,25))
        self.assertIn(b'<!-- before root -->',output);self.assertIn(b'<UnknownNode Raw="keep">',output)
        self.assertIn(b'Name="Marker Dir" Type="Vector3" Value="1 0 0"',output)

    def test_ids_reorder_without_reordering_eggs(self):
        raw,_=add_split(source_fixture(),(1,2,3))
        editor=CourseRaceLogicAuthoring(raw);editor.set_split_id(editor.split_status[-1].identity,7)
        output,_=reorder_split_ids(editor.export()[0])
        self.assertEqual([s.split_id for s in CourseRaceLogicAuthoring(output).split_status],[0,1])


if __name__=='__main__':unittest.main()
