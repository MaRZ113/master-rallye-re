from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.course_sdk import (  # noqa: E402
    CONFIRMED_BY_DEBUGGER,
    CONFIRMED_BY_EXECUTABLE,
    CONFIRMED_BY_RUNTIME_EDIT,
    CourseTag100Region,
    build_course_race_logic,
    discover_course_resources,
    load_course_project,
)
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402
from master_rallye.dx_course import parse_course_dx_bytes  # noqa: E402
from master_rallye.errors import FormatError  # noqa: E402
from master_rallye.hnt import parse_hnt_bytes, resolve_hnt_entries  # noqa: E402
from master_rallye.sfl import parse_sfl_bytes  # noqa: E402
from test_r5t_a import synthetic_course_dx  # noqa: E402


def race_xml(companion_count: int = 2, *, malformed: bool = False, include_areas: bool = True) -> bytes:
    pieces = ["<Scene>"]
    if include_areas:
        pieces.append('<MarkerLists><List Name="StartArea">')
        for index, point in enumerate(((0, 1, 2), (2, 1, 2), (2, 1, 4), (0, 1, 4))):
            pieces.append(
                f'<Marker No="{index}"><Value Name="Marker Pos" Type="Vector3" Value="{point[0]} {point[1]} {point[2]}" />'
                f'<Value Name="Marker Dir" Type="Vector3" Value="1 0 0" /></Marker>'
            )
        pieces.append('</List><List Name="FinishArea">')
        for index in range(4):
            pieces.append(
                f'<Marker No="{index}"><Value Name="Marker Pos" Type="Vector3" Value="{index} 0 0" />'
                '<Value Name="Marker Dir" Type="Vector3" Value="0 0 1" /></Marker>'
            )
        pieces.append('</List></MarkerLists>')
    pieces.append('<EggLists_Version4><List Name="SplitTimes">')
    row = 'broken row' if malformed else '10 20 30 1'
    pieces.append(
        '<Egg Name="SplitTime0"><Value Name="en3d Matrix" Type="Matrix" '
        f'Row0="1 0 0 0" Row1="0 1 0 0" Row2="0 0 1 0" Row3="{row}" />'
        '<AI_List><AI No="0"><gaRaceSplitTimeAI>'
        '<Value Name="Split Time ID" Type="Int" Value="0" />'
        '<Value Name="Radius" Type="Float" Value="21" />'
        '<Value Name="ExtraTime" Type="Float" Value="77.5" />'
        '</gaRaceSplitTimeAI></AI></AI_List></Egg>'
    )
    for index in range(companion_count):
        pieces.append(
            f'<Egg Name="SplitTime0-{index}"><Value Name="en3d Model Name" Type="String" Value="checkpoint-{index}" />'
            '<Value Name="en3d Matrix" Type="Matrix" Row0="1 0 0 0" Row1="0 1 0 0" '
            f'Row2="0 0 1 0" Row3="{index} 2 3 1" /></Egg>'
        )
    # Prefix siblings from another split and unrelated names must not attach.
    pieces.append('<Egg Name="SplitTime00-0" />')
    pieces.append('<Egg Name="SplitTime0-extra" />')
    pieces.append('</List></EggLists_Version4></Scene>')
    return "".join(pieces).encode("utf-8")


class CourseSdkRaceLogicTests(unittest.TestCase):
    def test_areas_preserve_source_order_positions_and_known_roles(self):
        document = parse_course_xml_bytes(race_xml(), "France1.xml")
        model = build_course_race_logic(document, course_identity="France1")
        self.assertEqual(model.start_area.source_list_name, "StartArea")
        self.assertEqual([item.index_in_list for item in model.start_area.markers], [0, 1, 2, 3])
        self.assertEqual(model.start_area.positions[0], (0.0, 1.0, 2.0))
        self.assertEqual(model.start_area.centroid, (1.0, 1.0, 3.0))
        self.assertEqual(model.start_area.local_xz_bounds, (0.0, 2.0, 2.0, 4.0))
        self.assertIn(CONFIRMED_BY_RUNTIME_EDIT, model.start_area.evidence)
        self.assertEqual(model.finish_area.source_list_name, "FinishArea")
        self.assertEqual(model.finish_area.markers[3].index_in_list, 3)
        self.assertIn("not asserted exclusive", model.finish_area.semantic_role)
        self.assertFalse(hasattr(model.start_area, "car_slots"))

    def test_split_model_interprets_confirmed_fields_and_exact_companion_siblings(self):
        document = parse_course_xml_bytes(race_xml(), "France1.xml")
        split = build_course_race_logic(document, course_identity="France1").split_times[0]
        self.assertEqual(split.split_id, 0)
        self.assertEqual(split.center, (10.0, 20.0, 30.0))
        self.assertEqual(split.radius, 21.0)
        self.assertEqual(split.extra_time, 77.5)
        self.assertEqual(split.extra_time_semantics, "UNKNOWN")
        self.assertEqual(split.trigger_shape, "sphere")
        self.assertTrue(split.trigger_complete)
        self.assertEqual([item.name for item in split.companions], ["SplitTime0-0", "SplitTime0-1"])
        self.assertEqual(split.companions[0].model_name, "checkpoint-0")
        self.assertIn(CONFIRMED_BY_RUNTIME_EDIT, split.evidence_center)
        self.assertIn(CONFIRMED_BY_DEBUGGER, split.evidence_center)
        self.assertIn(CONFIRMED_BY_EXECUTABLE, split.evidence_radius)
        self.assertEqual(split.source_component.xml_path, document.split_time_eggs[0].split_time_component.xml_path)

    def test_shared_split_records_do_not_inherit_france1_runtime_edit_evidence(self):
        document = parse_course_xml_bytes(race_xml(companion_count=5), "Italy1.xml")
        split = build_course_race_logic(document, course_identity="Italy1").split_times[0]
        self.assertNotIn(CONFIRMED_BY_RUNTIME_EDIT, split.evidence_center)
        self.assertIn("INFERRED_FROM_SHARED_COMPONENT_STRUCTURE", split.evidence_center)
        self.assertEqual(len(split.companions), 5)

    def test_split_with_zero_visual_companions_is_valid(self):
        document = parse_course_xml_bytes(race_xml(companion_count=0), "France1.xml")
        split = build_course_race_logic(document, course_identity="France1").split_times[0]
        self.assertEqual(split.companions, ())
        self.assertTrue(split.trigger_complete)

    def test_missing_radius_and_invalid_matrix_are_explicitly_incomplete(self):
        xml = race_xml(malformed=True).replace(b'<Value Name="Radius" Type="Float" Value="21" />', b'')
        split = build_course_race_logic(parse_course_xml_bytes(xml)).split_times[0]
        self.assertIsNone(split.center)
        self.assertIsNone(split.radius)
        self.assertFalse(split.trigger_complete)
        self.assertTrue(any("Radius missing" in issue for issue in split.issues))
        self.assertTrue(any("Row3 missing or invalid" in issue for issue in split.issues))

    def test_absent_areas_and_xml_splits_are_valid_optional_state(self):
        model = build_course_race_logic(parse_course_xml_bytes(race_xml(include_areas=False)))
        self.assertIsNone(model.start_area)
        self.assertIsNone(model.finish_area)
        self.assertEqual(len(model.split_times), 1)
        empty = build_course_race_logic(parse_course_xml_bytes(b"<Scene />"))
        self.assertIsNone(empty.start_area)
        self.assertIsNone(empty.finish_area)
        self.assertEqual(empty.split_times, ())


class CourseSdkCompositionTests(unittest.TestCase):
    def test_course_sdk_types_and_source_readers_are_public(self):
        from master_rallye import (
            CourseProject,
            CourseRenderDraw,
            CourseRenderGroup,
            CourseResourcePaths,
            parse_course_gxm,
            parse_course_txt,
        )

        self.assertTrue(all((CourseProject, CourseRenderDraw, CourseRenderGroup,
                             CourseResourcePaths, parse_course_gxm, parse_course_txt)))

    def test_course_dx_public_view_uses_neutral_tag100_model(self):
        from master_rallye.course_sdk import _render_resource

        render = _render_resource(parse_course_dx_bytes(synthetic_course_dx()))
        self.assertIsInstance(render.tag100, CourseTag100Region)
        self.assertTrue(render.tag100.present)
        self.assertEqual(render.tag100.byte_size, len(b"\x64\x00\x00\x00synthetic BSP bytes"))
        self.assertEqual(render.tag100.semantics, "UNKNOWN")
        self.assertFalse(hasattr(render, "collision"))
        self.assertFalse(hasattr(render, "bsp"))

    def test_discovery_reports_ambiguous_dx_and_keeps_xml_package_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "A.dx").write_bytes(b"not parsed by discovery")
            (root / "B.dx").write_bytes(b"not parsed by discovery")
            (root / "France1.xml").write_bytes(race_xml())
            discovery = discover_course_resources(root / "France1.xml", search_roots=(root,))
            self.assertIsNone(discovery.render_dx)
            self.assertEqual(len(discovery.candidate_paths("render_dx")), 2)
            self.assertTrue(any("ambiguous render_dx" in item for item in discovery.diagnostics))
            project = load_course_project(root / "France1.xml", search_roots=(root,))
            self.assertIsNone(project.render)
            self.assertIsNotNone(project.race_logic)

    def test_hnt_resolution_and_sfl_structure_are_composed_without_semantic_guess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data_gx = root / "DataGx"
            target = data_gx / "Course" / "France1" / "track.dx"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"placeholder")
            (data_gx / "Course" / "France1" / "surface.dxt").write_bytes(b"placeholder")
            hnt_path = root / "France1.hnt"
            hnt_path.write_bytes(b"Model [Course\\France1\\track]\nTexture [Course\\France1\\surface]\n")
            sfl_path = root / "France1.sfl"
            sfl_path.write_bytes(struct.pack("<fIIff", 1.0, 2, 2, 0.0, 0.0) + bytes((0, 4, 4, 255)))
            xml_path = root / "France1.xml"
            xml_path.write_bytes(race_xml())
            document = parse_hnt_bytes(hnt_path.read_bytes())
            resolutions = resolve_hnt_entries(document, data_gx)
            self.assertEqual([item.status for item in resolutions], ["resolved", "resolved"])
            field = parse_sfl_bytes(sfl_path.read_bytes())
            self.assertEqual((field.header.width, field.header.height), (2, 2))
            self.assertEqual(field.value_counts, ((0, 1), (4, 2), (255, 1)))
            project = load_course_project(xml_path, search_roots=(root,))
            self.assertIsNotNone(project.dependencies)
            self.assertEqual([item.status for item in project.dependencies.entries], ["resolved", "resolved"])
            self.assertEqual([item.raw_line for item in project.dependencies.entries], [
                "Model [Course\\France1\\track]", "Texture [Course\\France1\\surface]",
            ])
            self.assertIsNotNone(project.sfl)
            self.assertEqual((project.sfl.width, project.sfl.height), (2, 2))
            self.assertEqual(project.sfl.semantics, "UNKNOWN")

    def test_txt_only_course_project_is_a_valid_partial_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            txt = root / "Italy1.txt"
            txt.write_text("moMesh(Name [root]) {\n}\n", encoding="latin-1")
            project = load_course_project(txt)
            self.assertEqual(project.identity, "Italy1")
            self.assertIsNone(project.render)
            self.assertIsNone(project.race_logic)
            self.assertIsNotNone(project.source_txt)

    def test_dx_only_course_project_keeps_render_without_fabricated_race_logic(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "track.dx"
            source.write_bytes(synthetic_course_dx())
            project = load_course_project(source)
            self.assertIsNotNone(project.render)
            self.assertEqual(project.render.revision, 135)
            self.assertEqual(len(project.render.draw_records), 2)
            self.assertIsNone(project.race_logic)
            self.assertIsNone(project.dependencies)

    def test_package_folder_matches_txt_by_unique_selected_model_stem(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "Italy1"
            folder.mkdir()
            (folder / "track01.dx").write_bytes(synthetic_course_dx())
            (folder / "track01.txt").write_text(
                "moMesh(Name [root]) {\n}\n", encoding="latin-1"
            )

            resources = discover_course_resources(folder)
            self.assertEqual(resources.render_dx, folder / "track01.dx")
            self.assertEqual(resources.source_txt, folder / "track01.txt")
            self.assertEqual(resources.candidate_paths("source_txt"), (folder / "track01.txt",))
            project = load_course_project(folder)
            self.assertIsNotNone(project.render)
            self.assertIsNotNone(project.source_txt)

    def test_hnt_model_reference_links_course_folder_to_differently_named_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp) / "Game"
            data_gx = game / "DataGx"
            course = data_gx / "Course" / "Italy_M1"
            course.mkdir(parents=True)
            (course / "italy_m1.dx").write_bytes(synthetic_course_dx())
            (course / "italy_m1.txt").write_text(
                "moMesh(Name [root]) {\n}\n", encoding="latin-1"
            )

            race_test = game / "DataScene" / "RaceTest"
            race_test.mkdir(parents=True)
            (race_test / "italyM1.xml").write_bytes(race_xml())
            (race_test / "italyM1.hnt").write_text(
                "Model [Course\\Italy_M1\\italy_m1]\n", encoding="latin-1"
            )
            icont = game / "DataScene" / "ICont"
            icont.mkdir(parents=True)
            (icont / "italyM1.sfl").write_bytes(
                struct.pack("<fIIff", 1.0, 1, 1, 0.0, 0.0) + bytes((127,))
            )

            project = load_course_project(course, search_roots=(race_test, icont))
            self.assertEqual(project.identity, "Italy_M1")
            self.assertEqual(project.resources.race_test_xml, race_test / "italyM1.xml")
            self.assertEqual(project.resources.hnt, race_test / "italyM1.hnt")
            self.assertEqual(project.resources.sfl, icont / "italyM1.sfl")
            self.assertIsNotNone(project.race_logic)
            self.assertIsNotNone(project.dependencies)
            self.assertEqual(project.dependencies.entries[0].status, "resolved")
            self.assertIsNotNone(project.sfl)

            alias_hnt = race_test / "ItalyM1Alias.hnt"
            alias_hnt.write_text(
                "Model [Course\\Italy_M1\\italy_m1]\n", encoding="latin-1"
            )
            ambiguous = discover_course_resources(course, search_roots=(race_test, icont))
            self.assertIsNone(ambiguous.hnt)
            self.assertEqual(len(ambiguous.candidate_paths("hnt")), 2)
            self.assertTrue(any("ambiguous HNT Model links" in item for item in ambiguous.diagnostics))


if __name__ == "__main__":
    unittest.main()
