from __future__ import annotations

import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src", ROOT / "tests" / "synthetic"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.coords import blender_position_to_source, position_to_blender  # noqa: E402
from master_rallye.course_race_authoring import (  # noqa: E402
    CourseRaceLogicAuthoring,
    _semantic_guard,
)
from master_rallye.errors import FormatError  # noqa: E402
from test_course_sdk import race_xml  # noqa: E402


def source_fixture(*, comments=True, split_row="10.000 20 30.0 1.0000"):
    xml = race_xml(companion_count=2)
    xml = xml.replace(b'Row3="10 20 30 1"', f'Row3="{split_row}"'.encode("ascii"))
    xml = xml.replace(b"</Scene>", b'<UnknownNode Raw="keep"><Value Name="Mystery" Type="String" Value="preserve" /></UnknownNode></Scene>')
    if comments:
        xml = xml.replace(b"<Scene>", b"<Scene><!-- inside root: preserve -->")
        xml = b"<?xml version='1.0' encoding='utf-8'?>\n<!-- before root -->\n" + xml + b"\n<!-- after root -->\n"
    return xml


class CourseRaceLogicAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.source = source_fixture()
        self.editor = CourseRaceLogicAuthoring(self.source, "France1.xml")

    def test_zero_edit_export_is_byte_identical_including_comments_and_declaration(self):
        output, report = self.editor.export()
        self.assertEqual(output, self.source)
        self.assertEqual(report.source_sha256, report.exported_sha256)
        self.assertEqual(report.changed_semantic_paths, ())
        self.assertTrue(report.unknown_content_preserved)

    def test_start_and_finish_marker_mutations_change_only_selected_positions(self):
        self.editor.set_start_marker(2, (12.5, 6.0, -3.25))
        self.editor.set_finish_marker(1, (100.0, 2.0, 9.0))
        output, report = self.editor.export()
        parsed = ET.fromstring(output)
        start = parsed.find("./MarkerLists/List[@Name='StartArea']")
        finish = parsed.find("./MarkerLists/List[@Name='FinishArea']")
        self.assertEqual(start.findall("Marker")[2].find("Value[@Name='Marker Pos']").get("Value"), "12.5 6 -3.25")
        self.assertEqual(finish.findall("Marker")[1].find("Value[@Name='Marker Pos']").get("Value"), "100 2 9")
        self.assertEqual(len(report.changes), 2)
        self.assertEqual(
            [item["semantic_role"] for item in report.changes],
            ["race.start.marker_position", "race.finish.marker_position"],
        )
        self.assertIn(b"<!-- before root -->", output)
        self.assertIn(b"<!-- inside root: preserve -->", output)
        self.assertIn(b"<!-- after root -->", output)
        self.assertIn(b'<UnknownNode Raw="keep"><Value Name="Mystery" Type="String" Value="preserve" /></UnknownNode>', output)
        self.assertEqual(parsed.find("./MarkerLists/List[@Name='StartArea']/Marker[2]/Value[@Name='Marker Dir']").get("Value"), "1 0 0")

    def test_split_center_edits_only_row3_xyz_and_preserves_w_and_other_records(self):
        split = self.editor.split_status[0]
        self.editor.set_split_center(split.identity, (-4.5, 70.0, 123.25))
        output, report = self.editor.export()
        self.assertIn(b'Row3="-4.5 70 123.25 1.0000"', output)
        self.assertIn(b'Row0="1 0 0 0" Row1="0 1 0 0" Row2="0 0 1 0"', output)
        self.assertIn(b'<Egg Name="SplitTime0-0">', output)
        self.assertIn(b'Value="77.5"', output)
        self.assertEqual(len(report.changes), 1)
        self.assertTrue(_semantic_guard(self.source, output, {
            next(item for item in self.editor._pending.values()).field.locator: {"Row3": "row3-xyz"}
        }))

    def test_visual_companion_edit_only_changes_its_row3_xyz_and_has_semantic_role(self):
        statuses = self.editor.visual_companion_status
        self.assertEqual(len(statuses), 2)
        self.assertTrue(all(item.supported for item in statuses))
        companion = statuses[1]
        split = self.editor.split_status[0]
        self.editor.set_split_visual_companion_position(
            split.identity, companion.source_identity, (12.5, -3.0, 44.25)
        )
        output, report = self.editor.export()
        self.assertIn(b'Name="SplitTime0-1"', output)
        self.assertIn(b'Row3="12.5 -3 44.25 1"', output)
        self.assertIn(b'Row0="1 0 0 0" Row1="0 1 0 0" Row2="0 0 1 0"', output)
        self.assertIn(b'<Egg Name="SplitTime0">', output)
        self.assertEqual(len(report.changes), 1)
        self.assertEqual(report.changes[0]["semantic_role"], "race.split.visual_companion_position")
        self.assertEqual(report.changed_semantic_paths, (companion.source_xml_path + "/Value[@Name='en3d Matrix']/@Row3[XYZ]",))
        self.assertEqual(report.changes[0]["old"], (1.0, 2.0, 3.0))
        self.assertEqual(report.changes[0]["new"], (12.5, -3.0, 44.25))

    def test_invalid_visual_companion_matrix_is_read_only(self):
        xml = self.source.replace(
            b'Row2="0 0 1 0" Row3="0 2 3 1"',
            b'Row2="0 0 1 0"',
            1,
        )
        editor = CourseRaceLogicAuthoring(xml, "missing-companion-row.xml")
        companion = next(item for item in editor.visual_companion_status if item.egg_name == "SplitTime0-0")
        self.assertFalse(companion.supported)
        with self.assertRaisesRegex(ValueError, "visual companion authoring is refused"):
            editor.set_split_visual_companion_position(
                companion.split_identity, companion.source_identity, (1, 2, 3)
            )

    def test_radius_and_id_mutations_leave_extra_time_and_sibling_eggs_untouched(self):
        split = self.editor.split_status[0]
        self.editor.set_split_radius(split.identity, 25.5)
        self.editor.set_split_id(split.identity, 7)
        output, report = self.editor.export()
        self.assertIn(b'Name="Split Time ID" Type="Int" Value="7"', output)
        self.assertIn(b'Name="Radius" Type="Float" Value="25.5"', output)
        self.assertIn(b'Name="ExtraTime" Type="Float" Value="77.5"', output)
        self.assertIn(b'<Egg Name="SplitTime0-1">', output)
        self.assertEqual(len(report.changes), 2)
        self.assertEqual(
            {item["semantic_role"] for item in report.changes},
            {"race.split.radius", "race.split.id"},
        )

    def test_reverting_to_original_values_restores_byte_identical_noop(self):
        self.editor.set_start_marker(0, (3.0, 4.0, 5.0))
        self.editor.set_start_marker(0, (0.0, 1.0, 2.0))
        self.editor.set_split_radius(self.editor.split_status[0].identity, 30.0)
        self.editor.set_split_radius(self.editor.split_status[0].identity, 21.0)
        self.assertEqual(self.editor.mutation_count, 0)
        self.assertEqual(self.editor.export()[0], self.source)

    def test_allowlist_guard_rejects_unrelated_xml_changes(self):
        unrelated = self.source.replace(b'Name="Marker Dir" Type="Vector3" Value="1 0 0"',
                                         b'Name="Marker Dir" Type="Vector3" Value="9 9 9"', 1)
        self.assertFalse(_semantic_guard(self.source, unrelated, {}))

    def test_missing_or_ambiguous_area_is_safely_refused(self):
        duplicate = self.source.replace(
            b'</List><List Name="FinishArea">',
            b'</List><List Name="StartArea"><Marker No="duplicate" /></List><List Name="FinishArea">',
            1,
        )
        editor = CourseRaceLogicAuthoring(duplicate, "ambiguous.xml")
        start = next(item for item in editor.area_status if item.name == "StartArea")
        self.assertFalse(start.supported)
        with self.assertRaisesRegex(ValueError, "StartArea authoring is refused"):
            editor.set_start_marker(0, (1, 2, 3))

        missing = CourseRaceLogicAuthoring(race_xml(include_areas=False), "missing.xml")
        with self.assertRaisesRegex(ValueError, "FinishArea authoring is refused"):
            missing.set_finish_marker(0, (1, 2, 3))

    def test_multiple_splits_keep_source_order_and_unique_identity(self):
        xml = race_xml(companion_count=0)
        first_start = xml.index(b'<Egg Name="SplitTime0">')
        first_end = xml.index(b'</Egg>', first_start) + len(b'</Egg>')
        duplicate = xml[first_start:first_end].replace(b"SplitTime0", b"SplitTime4").replace(
            b'Name="Split Time ID" Type="Int" Value="0"',
            b'Name="Split Time ID" Type="Int" Value="4"',
        )
        xml = xml.replace(b"</List></EggLists_Version4>", duplicate + b"</List></EggLists_Version4>")
        editor = CourseRaceLogicAuthoring(xml, "multi.xml")
        self.assertEqual([item.egg_name for item in editor.split_status], ["SplitTime0", "SplitTime4"])
        self.assertEqual(len({item.identity for item in editor.split_status}), 2)
        editor.set_split_id(editor.split_status[1].identity, 9)
        self.assertTrue(any("duplicate Split Time ID 9" in item for item in editor.validation_warnings()) is False)
        self.assertIn(b'Name="Split Time ID" Type="Int" Value="9"', editor.export()[0])

    def test_invalid_radius_positions_and_ids_are_rejected(self):
        identity = self.editor.split_status[0].identity
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(radius=value), self.assertRaises(ValueError):
                self.editor.set_split_radius(identity, value)
        for position in ((1, 2), (1, float("nan"), 3)):
            with self.subTest(position=position), self.assertRaises(ValueError):
                self.editor.set_split_center(identity, position)
        for split_id in (1.5, True, "2"):
            with self.subTest(split_id=split_id), self.assertRaises(ValueError):
                self.editor.set_split_id(identity, split_id)
        for split_id in (-(2 ** 31) - 1, 2 ** 31):
            with self.subTest(split_id=split_id), self.assertRaisesRegex(ValueError, "signed 32-bit"):
                self.editor.set_split_id(identity, split_id)

    def test_split_id_accepts_signed_int32_boundaries(self):
        identity = self.editor.split_status[0].identity
        for split_id in (-(2 ** 31), 2 ** 31 - 1):
            editor = CourseRaceLogicAuthoring(self.source, "France1.xml")
            editor.set_split_id(identity, split_id)
            output, report = editor.export()
            self.assertIn(f'Name="Split Time ID" Type="Int" Value="{split_id}"'.encode("ascii"), output)
            self.assertEqual(report.changes[0]["semantic_role"], "race.split.id")

    def test_duplicate_split_id_is_warned_not_renumbered(self):
        xml = race_xml(companion_count=0)
        first_start = xml.index(b'<Egg Name="SplitTime0">')
        first_end = xml.index(b'</Egg>', first_start) + len(b'</Egg>')
        duplicate = xml[first_start:first_end].replace(b"SplitTime0", b"SplitTime1")
        duplicate = duplicate.replace(b'Name="Split Time ID" Type="Int" Value="0"',
                                      b'Name="Split Time ID" Type="Int" Value="0"')
        xml = xml.replace(b"</List></EggLists_Version4>", duplicate + b"</List></EggLists_Version4>")
        editor = CourseRaceLogicAuthoring(xml, "duplicate-id.xml")
        self.assertTrue(any("duplicate Split Time ID 0" in item for item in editor.validation_warnings()))
        self.assertEqual([item.split_id for item in editor.split_status], [0, 0])

    def test_malformed_xml_is_rejected(self):
        with self.assertRaises(FormatError):
            CourseRaceLogicAuthoring(b"<Scene><broken></Scene>", "bad.xml")

    def test_write_is_new_file_only_and_manifest_contains_hashes_not_xml(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "France1.xml"
            output = Path(temporary) / "France1_edited.xml"
            source.write_bytes(self.source)
            editor = CourseRaceLogicAuthoring.from_path(source)
            editor.set_start_marker(0, (3, 1, 2))
            original = source.read_bytes()
            report = editor.write_export(output)
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(output.is_file())
            manifest = Path(str(output) + ".mr-race-edit.json")
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_xml_sha256"], report.source_sha256)
            self.assertEqual(payload["exported_xml_sha256"], report.exported_sha256)
            self.assertNotIn("<Scene", manifest.read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                editor.write_export(source)
            with self.assertRaises(FileExistsError):
                editor.write_export(output)

    def test_blender_coordinate_conversion_roundtrips_runtime_space(self):
        point = (-2470.51, 84.36, -110.63)
        self.assertEqual(blender_position_to_source(position_to_blender(point)), point)


if __name__ == "__main__":
    unittest.main()
