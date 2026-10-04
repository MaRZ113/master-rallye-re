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
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402
from master_rallye.course_race_authoring import (  # noqa: E402
    CourseRaceLogicAuthoring,
    G1_MARKER_LISTS,
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


def g1_marker_source():
    lists = []
    definitions = (
        ("RaceLine", 0.0),
        ("LeftInnerLimit", 4.0),
        ("LeftOuterLimit", 8.0),
        ("RightInnerLimit", -4.0),
        ("RightOuterLimit", -8.0),
    )
    for name, z in definitions:
        markers = []
        for index, x in enumerate((0.0, 10.0, 20.0)):
            markers.append(
                f'<Marker No="{index}" custom="keep-{name}-{index}">'
                f'<Value Name="Marker Pos" Type="Vector3" Value="{x:g} 0 {z:g}" />'
                '<Value Name="Marker Dir" Type="Vector3" Value="0 0 1" />'
                f'<Value Name="Private Field" Type="String" Value="preserve-{name}-{index}" />'
                '</Marker>'
            )
        lists.append(f'<List Name="{name}">' + "".join(markers) + "</List>")
    source = source_fixture(comments=False)
    return source.replace(b"</List></MarkerLists>", ("</List>" + "".join(lists) + "</MarkerLists>").encode("ascii"), 1)


def g1_corridor_source(*, route_count, limit_count, inner_z, outer_z):
    """Build a straight source-order route with symmetric synthetic limits."""
    lists = []
    for name, count, z in (
        ("RaceLine", route_count, 0.0),
        ("LeftInnerLimit", limit_count, inner_z),
        ("LeftOuterLimit", limit_count, outer_z),
        ("RightInnerLimit", limit_count, -inner_z),
        ("RightOuterLimit", limit_count, -outer_z),
    ):
        markers = []
        for index in range(count):
            x = index * 10.0 if name == "RaceLine" else index * (route_count - 1) * 10.0 / max(1, limit_count - 1)
            markers.append(
                f'<Marker No="{index}"><Value Name="Marker Pos" Type="Vector3" Value="{x:g} 0 {z:g}" />'
                '<Value Name="Marker Dir" Type="Vector3" Value="0 0 1" /></Marker>'
            )
        lists.append(f'<List Name="{name}">' + "".join(markers) + "</List>")
    return ("<Scene><MarkerLists>" + "".join(lists) + "</MarkerLists></Scene>").encode("ascii")


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

    def test_route_limit_and_camera_marker_lists_remain_outside_stable_writer(self):
        extra = (
            b'<MarkerLists>'
            b'<List Name="RaceLine"><Marker><Value Name="Marker Pos" Type="Vector3" Value="1 2 3" /></Marker></List>'
            b'<List Name="LeftInnerLimit"><Marker><Value Name="Marker Pos" Type="Vector3" Value="4 5 6" /></Marker></List>'
            b'<List Name="LeftOuterLimit"><Marker><Value Name="Marker Pos" Type="Vector3" Value="7 8 9" /></Marker></List>'
            b'<List Name="RightInnerLimit"><Marker><Value Name="Marker Pos" Type="Vector3" Value="10 11 12" /></Marker></List>'
            b'<List Name="RightOuterLimit"><Marker><Value Name="Marker Pos" Type="Vector3" Value="13 14 15" /></Marker></List>'
            b'<List Name="Cameras"><Marker><Value Name="Marker Pos" Type="Vector3" Value="16 17 18" /></Marker></List>'
            b'</MarkerLists>'
        )
        source = source_fixture(comments=False).replace(b"</Scene>", extra + b"</Scene>")
        output, report = CourseRaceLogicAuthoring(source, "g1-read-only.xml").export()
        self.assertEqual(output, source)
        self.assertEqual(report.changes, ())
        self.assertEqual(report.changed_semantic_paths, ())

    def test_g1_pos_authoring_is_bounded_to_five_existing_marker_lists(self):
        source = g1_marker_source()
        editor = CourseRaceLogicAuthoring(source, "g1-authoring.xml")
        self.assertEqual(tuple(item.name for item in editor.marker_list_status), G1_MARKER_LISTS)
        self.assertTrue(all(item.present and item.supported and item.marker_count == 3
                            for item in editor.marker_list_status))
        edits = {
            "RaceLine": (10.0, 2.0, 1.0),
            "LeftInnerLimit": (10.0, 2.0, 5.0),
            "LeftOuterLimit": (10.0, 2.0, 9.0),
            "RightInnerLimit": (10.0, 2.0, -3.0),
            "RightOuterLimit": (10.0, 2.0, -7.0),
        }
        for list_name, position in edits.items():
            editor.set_marker_position(list_name, 1, position)
        output, report = editor.export()
        before = parse_course_xml_bytes(source, "g1-authoring.xml")
        after = parse_course_xml_bytes(output, "g1-authoring.xml")
        before_lists = {item.name: item for item in before.marker_lists}
        after_lists = {item.name: item for item in after.marker_lists}
        self.assertEqual([item.name for item in before.marker_lists], [item.name for item in after.marker_lists])
        self.assertEqual(len(report.changes), 5)
        self.assertEqual({item["marker_list"] for item in report.changes}, set(G1_MARKER_LISTS))
        self.assertEqual({item["marker_index"] for item in report.changes}, {1})
        self.assertEqual(
            {item["semantic_role"] for item in report.changes},
            {
                "race.route.raceline.marker_position",
                "race.limit.left_inner.marker_position",
                "race.limit.left_outer.marker_position",
                "race.limit.right_inner.marker_position",
                "race.limit.right_outer.marker_position",
            },
        )
        self.assertTrue(all(item["marker_count_unchanged"] and item["source_order_unchanged"]
                            for item in report.to_dict()["marker_list_invariants"]))
        for name in G1_MARKER_LISTS:
            old = before_lists[name].markers
            new = after_lists[name].markers
            self.assertEqual(len(old), len(new), name)
            for index, (old_marker, new_marker) in enumerate(zip(old, new)):
                expected = edits[name] if index == 1 else old_marker.position
                self.assertEqual(new_marker.position, expected, (name, index))
                self.assertEqual(new_marker.direction, old_marker.direction, (name, index))
                self.assertEqual(new_marker.record.value("Private Field"), old_marker.record.value("Private Field"))
                self.assertEqual(dict(new_marker.record.attributes), dict(old_marker.record.attributes))

    def test_g1_noop_is_byte_identical_and_camera_or_other_lists_are_not_writable(self):
        source = g1_marker_source()
        editor = CourseRaceLogicAuthoring(source, "g1-noop.xml")
        output, report = editor.export()
        self.assertEqual(output, source)
        self.assertEqual(report.changes, ())
        with self.assertRaisesRegex(ValueError, "does not support"):
            editor.set_marker_position("Cameras", 0, (1, 2, 3))
        with self.assertRaisesRegex(ValueError, "does not support"):
            editor.set_marker_position("UnknownList", 0, (1, 2, 3))

    def test_g1_refuses_missing_or_duplicate_lists_without_expanding_the_guard(self):
        source = g1_marker_source()
        start = source.index(b'<List Name="RaceLine">')
        end = source.index(b'</List>', start)
        segment = source[start:end]
        segment = segment.replace(b'Name="Marker Pos"', b'Name="Position"', 1)
        missing_value = source[:start] + segment + source[end:]
        missing_editor = CourseRaceLogicAuthoring(missing_value, "missing-pos.xml")
        race_status = next(item for item in missing_editor.marker_list_status if item.name == "RaceLine")
        self.assertFalse(race_status.supported)
        with self.assertRaisesRegex(ValueError, "RaceLine authoring is refused"):
            missing_editor.set_marker_position("RaceLine", 0, (1, 2, 3))

        duplicate = source.replace(
            b'</List></MarkerLists>', b'</List><List Name="RaceLine"></List></MarkerLists>', 1
        )
        duplicate_editor = CourseRaceLogicAuthoring(duplicate, "duplicate-list.xml")
        duplicate_status = next(item for item in duplicate_editor.marker_list_status if item.name == "RaceLine")
        self.assertFalse(duplicate_status.supported)
        with self.assertRaisesRegex(ValueError, "RaceLine authoring is refused"):
            duplicate_editor.set_marker_position("RaceLine", 0, (1, 2, 3))

    def test_g1_position_validation_and_semantic_diff_guard_preserve_topology(self):
        source = g1_marker_source()
        editor = CourseRaceLogicAuthoring(source, "g1-validation.xml")
        for position in ((1.0, 2.0), (1.0, float("nan"), 3.0), (1.0, float("inf"), 3.0)):
            with self.subTest(position=position), self.assertRaises(ValueError):
                editor.set_marker_position("RaceLine", 0, position)
        with self.assertRaises(ValueError):
            editor.set_marker_position("RaceLine", True, (1, 2, 3))
        editor.set_marker_position("RaceLine", 1, (10, 0, 1))
        output, _report = editor.export()
        malformed_topology = output.replace(b'<Marker No="2"', b'<Marker No="9"', 1)
        masks = {
            mutation.field.locator: {mutation.field.attribute: mutation.field.mode}
            for mutation in editor._pending.values()
        }
        self.assertFalse(_semantic_guard(source, malformed_topology, masks))

    def test_position_float_serialization_roundtrips_world_coordinate_precision(self):
        source = g1_marker_source()
        editor = CourseRaceLogicAuthoring(source, "g1-float-precision.xml")
        editor.set_marker_position("RaceLine", 0, (-2469.939355, -18.1, 926.482487))
        output, report = editor.export()
        self.assertIn(b'Value="-2469.939355 -18.100000 926.482487"', output)
        self.assertEqual(report.changes[0]["new"], (-2469.939355, -18.1, 926.482487))

    def test_g1_outer_limit_geometry_warnings_do_not_crash_on_nested_progress_match(self):
        source = g1_marker_source()
        editor = CourseRaceLogicAuthoring(source, "g1-limit-warning.xml")
        editor.set_marker_position("LeftOuterLimit", 1, (10.0, 0.0, 1.0))
        output, report = editor.export()
        self.assertNotEqual(output, source)
        self.assertTrue(all(isinstance(item, str) for item in report.warnings))

    def test_limit_confidence_threshold_uses_limit_sample_population(self):
        # Four valid limit samples must not be suppressed because the route is
        # twenty points long (the old threshold incorrectly demanded five).
        source = g1_corridor_source(route_count=20, limit_count=4, inner_z=4.0, outer_z=8.0)
        editor = CourseRaceLogicAuthoring(source, "g1-short-corridor.xml")
        editor.set_marker_position("LeftOuterLimit", 1, (63.333333, 0.0, -8.0))
        _output, report = editor.export()
        self.assertTrue(any("crosses the list's baseline RaceLine-side polarity" in warning
                            for warning in report.warnings))

    def test_outer_inner_order_compares_absolute_signed_offsets(self):
        # This side of the route has negative signed offsets. An outer sample
        # farther from the route than its inner sample must not warn as nearer.
        source = g1_corridor_source(route_count=3, limit_count=3, inner_z=-4.0, outer_z=-8.0)
        editor = CourseRaceLogicAuthoring(source, "g1-negative-side-corridor.xml")
        editor.set_marker_position("LeftOuterLimit", 1, (10.0, 0.0, -8.25))
        _output, report = editor.export()
        self.assertFalse(any("is closer to RaceLine than the nearest-progress LeftInnerLimit sample" in warning
                             for warning in report.warnings))

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
