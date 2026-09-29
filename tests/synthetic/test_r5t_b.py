from __future__ import annotations

import struct
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.course_diff import (
    _classify_cook_field,
    compare_course_cook_sets,
    diff_course_trees,
)
from master_rallye.course_gxm import (
    parse_course_gxm_bytes,
    parse_course_gxm_float3_pool_bytes,
    parse_course_gxm_object_table_bytes,
)
from master_rallye.course_source import parse_course_txt_bytes
from master_rallye.course_xml import parse_course_xml_bytes
from master_rallye.dx import MAGIC
from master_rallye.errors import BoundsError, FormatError


def _course_record():
    texture = b"track-tga"
    record = bytearray(struct.pack("<7If4BI", 2, 0, 2, 0, 3, 1, 0, 1.0, 0, 0, 0, 1, 5))
    record += struct.pack("<I", 1)
    record += struct.pack("<I", len(texture)) + texture
    record += struct.pack("<I", 0)
    return bytes(record)


def _synthetic_course_dx():
    points = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    blob = bytearray(struct.pack("<4I", MAGIC, 135, 1337, len(points)))
    for point in points:
        blob += struct.pack("<3f", *point)
    for _ in points:
        blob += struct.pack("<3f", 0.0, 0.0, 1.0)
    blob += bytes((10, 20, 30, 255)) * len(points)
    blob += struct.pack("<I", 1)
    for uv in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)):
        blob += struct.pack("<2f", *uv)
    blob += struct.pack("<I3H", 3, 0, 1, 2)
    blob += struct.pack("<2I", 1, 1)
    blob += _course_record()
    blob += struct.pack("<I", 100) + b"opaque synthetic BSP"
    return bytes(blob)


def _course_txt(mesh_size: int, add_startline: bool) -> bytes:
    helper = "  moUnknown(Name [$startline])\n" if add_startline else ""
    text = (
        "moModel(Name [Model])\n"
        "Materials(Size 1)\n"
        "{\n"
        "    Material number [ 0] has name [road]\n"
        "      Texture [ 0] HasAlpha [No] UsesAlpha [No] IsNoise [No] Name[road.tga]\n"
        "}\n"
        "  moUnknown(Name [$bsp])\n"
        "  {\n"
        f"    moMesh(Name [Surface $landdb] Index 0 Size {mesh_size})\n"
        "  }\n"
        f"{helper}"
    )
    return text.encode("latin-1")


def _synthetic_course_gxm(txt_data: bytes, bank_byte: int = 0) -> bytes:
    from master_rallye.course_source import parse_course_txt_bytes

    document = parse_course_txt_bytes(txt_data, "synthetic.txt")
    child_counts = {node.node_id: 0 for node in document.nodes}
    for node in document.nodes:
        if node.parent_id is not None:
            child_counts[node.parent_id] += 1
    root = document.nodes[0]
    table = bytearray(struct.pack("<H", len(root.name.encode("latin-1"))))
    table += root.name.encode("latin-1")
    for node in document.nodes[1:]:
        is_mesh = node.class_name.casefold() == "momesh"
        table += struct.pack("<BBH", 1 if is_mesh else 3, 1, 0 if is_mesh else child_counts[node.node_id])
        if is_mesh:
            table += struct.pack("<II", node.mesh_index, node.mesh_size)
        encoded_name = node.name.encode("latin-1")
        table += struct.pack("<H", len(encoded_name)) + encoded_name
    header = struct.pack("<8I", 0x000F0302, 0, 1, 1, 3, 1, 1, 0)
    return header + bytes([bank_byte]) * 16 + bytes(table)


class R5TCourseGxmPrefixTests(unittest.TestCase):
    def test_counted_opaque_bank_boundary_and_truncated_input(self):
        header = struct.pack("<8I", 0x000F0302, 0, 2, 1, 6, 4, 2, 1)
        records = bytes(range(32))
        tail = struct.pack("<H", 3) + b"abc"
        parsed = parse_course_gxm_bytes(header + records + tail, "synthetic.gxm")
        self.assertEqual(parsed.record_count, 2)
        self.assertEqual(parsed.record_offset, 32)
        self.assertEqual(parsed.record_end, 64)
        self.assertEqual(parsed.opaque_records, records)
        self.assertEqual(parsed.opaque_tail, tail)
        with self.assertRaises(BoundsError):
            parse_course_gxm_bytes(header + records[:-1])

    def test_rejects_unreasonable_count(self):
        header = struct.pack("<8I", 1, 0, 4_000_001, 0, 0, 0, 0, 0)
        with self.assertRaises(FormatError):
            parse_course_gxm_bytes(header)

    def test_exact_object_table_matches_paired_txt_hierarchy_and_spans(self):
        txt = (
            b"moModel(Name [Model])\n"
            b"  moUnknown(Name [$bsp])\n"
            b"  {\n"
            b"    moMesh(Name [surface] Index 12 Size 24)\n"
            b"  }\n"
        )
        document = parse_course_txt_bytes(txt, "synthetic.txt")
        table = parse_course_gxm_object_table_bytes(_synthetic_course_gxm(txt), document)
        self.assertEqual(table.root_name, "Model")
        self.assertEqual(table.table_offset, 48)
        self.assertEqual([node.name for node in table.nodes], ["Model", "$bsp", "surface"])
        self.assertEqual(table.nodes[1].child_count, 1)
        self.assertEqual((table.nodes[2].mesh_index, table.nodes[2].mesh_size), (12, 24))
        with self.assertRaises(BoundsError):
            parse_course_gxm_object_table_bytes(_synthetic_course_gxm(txt)[:-1], document)

    def test_bounded_float3_pool_preserves_raw_points_and_rejects_nonfinite_data(self):
        txt = b"moModel(Name [Model])\n  moMesh(Name [startpoint] Index 0 Size 1)\n"
        document = parse_course_txt_bytes(txt, "synthetic.txt")
        base = _synthetic_course_gxm(txt)
        table_bytes = base[48:]
        points = struct.pack("<9f", 1.0, 2.0, 3.0, -4.0, 5.5, 6.0, 7.0, 8.0, 9.0)
        header = struct.pack("<8I", 0x000F0302, 0, 1, 1, 3, 1, 1, 3)
        data = header + bytes(16) + points + table_bytes
        table = parse_course_gxm_object_table_bytes(data, document)
        pool = parse_course_gxm_float3_pool_bytes(data, table)
        self.assertEqual(pool.offset, 48)
        self.assertEqual(pool.count, 3)
        self.assertEqual(pool.points[1], (-4.0, 5.5, 6.0))
        self.assertEqual(pool.raw, points)

        bad_points = struct.pack("<3f", 1.0, float("nan"), 3.0)
        bad_header = struct.pack("<8I", 0x000F0302, 0, 1, 1, 3, 1, 1, 1)
        bad_data = bad_header + bytes(16) + bad_points + table_bytes
        bad_table = parse_course_gxm_object_table_bytes(bad_data, document)
        with self.assertRaisesRegex(FormatError, "non-finite"):
            parse_course_gxm_float3_pool_bytes(bad_data, bad_table)


class R5TCourseTxtTreeTests(unittest.TestCase):
    def test_preserves_exact_names_parentage_and_mesh_ranges(self):
        data = (
            b"moModel(Name [Model])\n"
            b"  moUnknown(Name [$bsp])\n"
            b"  {\n"
            b"    moUnknown(Name [$nodraw])\n"
            b"    {\n"
            b"      moMesh(Name [Surface $landdb] Index 8 Size 24)\n"
            b"    }\n"
            b"  }\n"
            b"  moMesh(Name [raceline] Index 32 Size 6)\n"
        )
        doc = parse_course_txt_bytes(data, "course.txt")
        self.assertEqual(doc.unparsed_node_lines, ())
        root, bsp, nodraw, surface, raceline = doc.nodes
        self.assertEqual(root.name, "Model")
        self.assertEqual(bsp.name, "$bsp")
        self.assertEqual(nodraw.parent_id, bsp.node_id)
        self.assertEqual(surface.parent_id, nodraw.node_id)
        self.assertEqual((surface.mesh_index, surface.mesh_size), (8, 24))
        self.assertEqual(surface.name, "Surface $landdb")
        self.assertIn("$landdb", surface.literal_tokens)
        self.assertEqual(raceline.name, "raceline")
        self.assertIn("raceline", raceline.literal_tokens)


class R5TCourseXmlTests(unittest.TestCase):
    def test_extracts_explicit_marker_and_split_time_values(self):
        data = (
            b'<Scene><Marker No="7">'
            b'<Value Name="Marker Type" Type="String" Value="markers\\green_marker" />'
            b'<Value Name="Marker Pos" Type="Vector3" Value="1.5 2 -3" />'
            b'<Value Name="Marker Dir" Type="Vector3" Value="1 0 0" />'
            b'</Marker><gaRaceSplitTimeAI><Value Name="Split Time ID" Type="Int" Value="2" />'
            b'</gaRaceSplitTimeAI></Scene>'
        )
        document = parse_course_xml_bytes(data, "synthetic.xml")
        self.assertEqual(document.root_tag, "Scene")
        self.assertEqual(document.markers[0].marker_no, "7")
        self.assertEqual(document.markers[0].position, (1.5, 2.0, -3.0))
        self.assertEqual(document.markers[0].direction, (1.0, 0.0, 0.0))
        self.assertEqual(document.split_time_records[0].value("Split Time ID").value, "2")

    def test_preserves_bad_or_incomplete_marker_as_issue_and_rejects_bad_xml(self):
        document = parse_course_xml_bytes(
            b'<Scene><Marker No="1"><Value Name="Marker Pos" Type="Vector3" Value="1 1e999 3" /></Marker></Scene>'
        )
        self.assertIsNone(document.markers[0].position)
        self.assertTrue(any("non-finite" in issue for issue in document.markers[0].issues))
        with self.assertRaises(FormatError):
            parse_course_xml_bytes(b"<Scene>")

    def test_preserves_marker_list_hierarchy_order_and_start_finish_groups(self):
        data = (
            b'<Scene><MarkerLists>'
            b'<List Name="StartArea"><Marker No="4">'
            b'<Value Name="Marker Pos" Type="Vector3" Value="1 2 3" Extra="kept" />'
            b'<Value Name="Marker Dir" Type="Vector3" Value="0 0 1" />'
            b'</Marker><Marker No="5"><Value Name="Marker Pos" Type="Vector3" Value="4 5 6" />'
            b'</Marker></List>'
            b'<List Name="FinishArea"><Marker No="0"><Value Name="Marker Pos" Type="Vector3" Value="7 8 9" />'
            b'</Marker></List></MarkerLists></Scene>'
        )
        document = parse_course_xml_bytes(data, "hierarchy.xml")
        self.assertEqual([item.name for item in document.marker_lists], ["StartArea", "FinishArea"])
        start = document.marker_list("StartArea")
        finish = document.marker_list("FinishArea")
        self.assertEqual([item.marker_no for item in start.markers], ["4", "5"])
        self.assertEqual([item.index_in_list for item in start.markers], [0, 1])
        self.assertEqual([item.marker_list_ordinal for item in start.markers], [0, 0])
        self.assertEqual(start.markers[0].position, (1.0, 2.0, 3.0))
        self.assertEqual(start.markers[0].direction, (0.0, 0.0, 1.0))
        self.assertEqual(dict(start.markers[0].record.value("Marker Pos").attributes)["Extra"], "kept")
        self.assertEqual(finish.markers[0].position, (7.0, 8.0, 9.0))
        self.assertTrue(start.markers[0].record.xml_path.endswith("Marker[@No='4']"))
        self.assertEqual(document.root.tag, "Scene")
        self.assertEqual(document.root.children[0].children[0].attribute("Name"), "StartArea")

    def test_duplicate_marker_list_names_keep_distinct_ordinals_and_local_indices(self):
        data = (
            b'<Scene><MarkerLists><List Name="Repeated">'
            b'<Marker No="a"><Value Name="Marker Pos" Type="Vector3" Value="1 2 3" /></Marker>'
            b'</List><List Name="Repeated">'
            b'<Marker No="b"><Value Name="Marker Pos" Type="Vector3" Value="4 5 6" /></Marker>'
            b'</List></MarkerLists></Scene>'
        )
        document = parse_course_xml_bytes(data, "duplicate-lists.xml")
        self.assertEqual([item.name for item in document.marker_lists], ["Repeated", "Repeated"])
        self.assertEqual([item.ordinal for item in document.marker_lists], [0, 1])
        self.assertEqual([len(item.markers) for item in document.marker_lists], [1, 1])
        self.assertEqual([item.markers[0].marker_list_ordinal for item in document.marker_lists], [0, 1])
        self.assertEqual([item.markers[0].index_in_list for item in document.marker_lists], [0, 0])

    def test_extracts_split_egg_matrix_ai_fields_and_source_order(self):
        data = (
            b'<Scene><EggLists_Version4><List Name="SplitTimes">'
            b'<Egg Name="SplitTime0"><Value Name="en3d Model Name" Type="String" Value="test\\arrow" />'
            b'<Value Name="Egg Custom Field" Type="String" Value="keep-egg" Extra="egg-meta" />'
            b'<Value Name="en3d Matrix" Type="Matrix" Row0="1 0 0 0" Row1="0 1 0 0" '
            b'Row2="0 0 1 0" Row3="10 20 30 1" />'
            b'<AI_List><AI No="0" Extra="ai-meta"><Value Name="AI Name" Type="String" Value="gaRaceSplitTimeAI" />'
            b'<Value Name="AI Custom Field" Type="String" Value="keep-ai" />'
            b'<gaRaceSplitTimeAI><Value Name="Split Time ID" Type="Int" Value="0" />'
            b'<Value Name="Radius" Type="Float" Value="21.00000" />'
            b'<Value Name="ExtraTime" Type="Float" Value="77.50000" />'
            b'<Value Name="Component Custom Field" Type="String" Value="keep-component" Extra="component-meta" />'
            b'</gaRaceSplitTimeAI></AI></AI_List></Egg>'
            b'<Egg Name="SplitTime1"><AI_List><AI No="0"><Value Name="AI Name" Type="String" Value="gaRaceSplitTimeAI" />'
            b'<gaRaceSplitTimeAI><Value Name="Split Time ID" Type="Int" Value="1" /></gaRaceSplitTimeAI>'
            b'</AI></AI_List></Egg></List></EggLists_Version4></Scene>'
        )
        document = parse_course_xml_bytes(data, "split.xml")
        self.assertEqual([egg.name for egg in document.split_time_eggs], ["SplitTime0", "SplitTime1"])
        first = document.split_time_eggs[0]
        self.assertEqual((first.list_name, first.index_in_list), ("SplitTimes", 0))
        self.assertEqual(first.model_name, "test\\arrow")
        self.assertEqual(first.matrix().position, (10.0, 20.0, 30.0))
        self.assertEqual(first.matrix().row(0), (1.0, 0.0, 0.0, 0.0))
        self.assertEqual(dict(first.matrix().attributes)["Row3"], "10 20 30 1")
        self.assertEqual(first.values[1].name, "Egg Custom Field")
        self.assertEqual(dict(first.values[1].attributes)["Extra"], "egg-meta")
        component = first.split_time_component
        self.assertEqual(component.value("Split Time ID").value, "0")
        self.assertEqual(component.value("Radius").value, "21.00000")
        self.assertEqual(component.value("ExtraTime").value, "77.50000")
        self.assertEqual(first.ai_objects[0].ai_no, "0")
        self.assertEqual(first.ai_objects[0].ai_name, "gaRaceSplitTimeAI")
        self.assertEqual(dict(first.ai_objects[0].attributes)["Extra"], "ai-meta")
        self.assertEqual(first.ai_objects[0].values[1].value, "keep-ai")
        self.assertEqual(component.value("Component Custom Field").value, "keep-component")
        self.assertEqual(dict(component.value("Component Custom Field").attributes)["Extra"], "component-meta")
        self.assertEqual(document.split_time_eggs[1].split_time_component.value("Split Time ID").value, "1")
        self.assertEqual(document.split_time_records[0].egg_name, "SplitTime0")
        self.assertTrue(document.split_time_records[0].xml_path.endswith("gaRaceSplitTimeAI[0]"))

    def test_malformed_optional_matrix_and_absent_optional_fields_are_preserved(self):
        document = parse_course_xml_bytes(
            b'<Scene><EggLists_Version4><List Name="SplitTimes"><Egg Name="SplitTime0">'
            b'<Value Name="en3d Matrix" Type="Matrix" Row3="1 bad 3 1" />'
            b'<AI_List><AI No="0"><Value Name="AI Name" Type="String" Value="gaRaceSplitTimeAI" />'
            b'<gaRaceSplitTimeAI><Value Name="Split Time ID" Type="Int" Value="0" /></gaRaceSplitTimeAI>'
            b'</AI></AI_List></Egg></List></EggLists_Version4></Scene>'
        )
        egg = document.split_time_eggs[0]
        self.assertIsNone(egg.matrix().position)
        self.assertTrue(egg.matrix().issues)
        self.assertIsNone(egg.split_time_component.value("Radius"))
        self.assertEqual(egg.split_time_component.value("Split Time ID").value, "0")


class R5TCourseDiffTests(unittest.TestCase):
    def test_semantic_diff_reports_dx_txt_sfl_xml_hnt_and_gxm_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / "base"
            modified = root / "modified"
            for folder in (base, modified):
                (folder / "DataGx" / "Course" / "France1").mkdir(parents=True)
            rel = Path("DataGx/Course/France1")

            dx = _synthetic_course_dx()
            changed_dx = bytearray(dx)
            struct.pack_into("<f", changed_dx, 16, 0.25)
            (base / rel / "france1.dx").write_bytes(dx)
            (modified / rel / "france1.dx").write_bytes(changed_dx)

            base_txt = _course_txt(3, False)
            modified_txt = _course_txt(6, True)
            (base / rel / "France1.txt").write_bytes(base_txt)
            (modified / rel / "France1.txt").write_bytes(modified_txt)
            (base / rel / "France1.gxm").write_bytes(_synthetic_course_gxm(base_txt))
            (modified / rel / "France1.gxm").write_bytes(_synthetic_course_gxm(modified_txt, 1))

            sfl_header = struct.pack("<fIIff", 3.0, 2, 2, -10.0, 4.0)
            (base / "France1.sfl").write_bytes(sfl_header + bytes((0, 1, 2, 3)))
            (modified / "France1.sfl").write_bytes(sfl_header + bytes((0, 1, 2, 4)))
            (base / "France1.xml").write_text('<Scene><Marker x="0" y="2" /></Scene>', encoding="utf-8")
            (modified / "France1.xml").write_text('<Scene><Marker x="1" y="2" /></Scene>', encoding="utf-8")
            (base / "France1.hnt").write_text("Model [course\\france1\\france1]\nTexture [course\\france1\\road-tga]\n", encoding="latin-1")
            (modified / "France1.hnt").write_text("Model [course\\france1\\france1]\nTexture [course\\france1\\road2-tga]\n", encoding="latin-1")
            (base / rel / "road.dxt").write_bytes(b"before")
            (modified / rel / "road.dxt").write_bytes(b"after")

            report = diff_course_trees(base, modified)
            files = {item["path"].casefold(): item for item in report["files"]}
            self.assertEqual(report["summary"]["changed_file_count"], 7)
            dx_diff = files["datagx/course/france1/france1.dx"]["semantic_diff"]
            self.assertIn("render_hashes", dx_diff["changed_fields"])
            self.assertEqual(
                files["datagx/course/france1/france1.dx"]["base"]["semantics"]["trailing"]["tag100"]["sha256"],
                files["datagx/course/france1/france1.dx"]["modified"]["semantics"]["trailing"]["tag100"]["sha256"],
            )
            txt_diff = files["datagx/course/france1/france1.txt"]["semantic_diff"]
            self.assertTrue(txt_diff["nodes"]["added"])
            sfl_diff = files["france1.sfl"]["semantic_diff"]
            self.assertEqual(sfl_diff["changed_cell_count"], 1)
            self.assertEqual(sfl_diff["changed_cell_bounds"], [1, 1, 1, 1])
            xml_diff = files["france1.xml"]["semantic_diff"]
            self.assertEqual(xml_diff["changed_elements"][0]["modified"]["attributes"]["x"], "1")
            hnt_diff = files["france1.hnt"]["semantic_diff"]
            self.assertEqual(len(hnt_diff["added"]), 1)
            gxm_diff = files["datagx/course/france1/france1.gxm"]["semantic_diff"]
            self.assertIn("object_table", gxm_diff["changed_fields"])


class R5TCourseCookSetTests(unittest.TestCase):
    @staticmethod
    def _write_run(root: Path, position_x: float) -> Path:
        course = root / "course"
        course.mkdir(parents=True)
        dx = bytearray(_synthetic_course_dx())
        struct.pack_into("<f", dx, 16, position_x)
        (course / "track.dx").write_bytes(dx)
        return course

    def test_field_classifier_separates_natural_variance_from_stable_effect(self):
        self.assertEqual(_classify_cook_field({"0", "1"}, {"1"}), "BASELINE_VARIABLE")
        self.assertEqual(_classify_cook_field({"0", "1"}, {"2"}), "MODIFICATION_STABLE")
        self.assertEqual(_classify_cook_field({"0"}, {"1", "2"}), "MODIFICATION_VARIABLE")
        self.assertEqual(_classify_cook_field({"0"}, {"0"}), "UNCHANGED")

    def test_repeated_cooks_report_variable_and_stable_dx_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = [
                self._write_run(root / "baseline" / f"run-{index}", value)
                for index, value in enumerate((0.0, 0.25, 0.0), start=1)
            ]
            modified = [
                self._write_run(root / "modified" / f"run-{index}", 0.5)
                for index in range(1, 4)
            ]
            report = compare_course_cook_sets(baseline, modified)
            self.assertEqual(report["summary"]["baseline_run_count"], 3)
            self.assertEqual(report["summary"]["modified_run_count"], 3)
            self.assertGreater(report["summary"]["unchanged_field_count"], 0)
            by_field = {item["field"]: item for item in report["fields"]}
            position_hash = "semantic[track.dx].render_hashes.positions"
            self.assertEqual(by_field[position_hash]["classification"], "MODIFICATION_STABLE")
            tag_hash = "semantic[track.dx].trailing.tag100.sha256"
            self.assertEqual(by_field[tag_hash]["classification"], "UNCHANGED")
            self.assertEqual(
                report["summary"]["modification_stable_field_count"] > 0,
                True,
            )

    def test_three_run_minimum_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            two = [
                self._write_run(root / "run" / f"run-{index}", 0.0)
                for index in range(1, 3)
            ]
            with self.assertRaisesRegex(ValueError, "at least 3 runs"):
                compare_course_cook_sets(two, two)

    def test_two_run_followup_can_be_requested_explicitly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = [
                self._write_run(root / "baseline" / f"run-{index}", 0.0)
                for index in range(1, 3)
            ]
            modified = [
                self._write_run(root / "modified" / f"run-{index}", 0.5)
                for index in range(1, 3)
            ]
            report = compare_course_cook_sets(baseline, modified, minimum_runs=2)
            self.assertEqual(report["minimum_runs_per_cohort"], 2)
            self.assertEqual(report["summary"]["baseline_run_count"], 2)
            self.assertEqual(report["summary"]["modified_run_count"], 2)

    def test_source_input_difference_is_not_counted_as_compiled_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base_txt = _course_txt(3, False)
            baseline = []
            modified = []
            for index in range(1, 4):
                base_run = self._write_run(root / "baseline" / f"run-{index}", 0.0)
                mod_run = self._write_run(root / "modified" / f"run-{index}", 0.0)
                for run, bank_byte in ((base_run, 0), (mod_run, 1)):
                    (run / "track.txt").write_bytes(base_txt)
                    (run / "track.gxm").write_bytes(_synthetic_course_gxm(base_txt, bank_byte))
                baseline.append(base_run)
                modified.append(mod_run)
            report = compare_course_cook_sets(baseline, modified)
            self.assertEqual(report["summary"]["compiled_stable_effect_field_count"], 0)
            self.assertGreater(
                report["summary"]["field_counts_by_resource_role"]["source_input"]["MODIFICATION_STABLE"],
                0,
            )

    def test_cohort_rejects_runs_with_different_input_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = []
            modified = []
            for index, source_hash in enumerate(("a", "a", "b"), start=1):
                course = self._write_run(root / "baseline" / f"run-{index}", 0.0)
                (course.parent / "run.json").write_text(
                    json.dumps({"input_manifest": {"track.gxm": {"sha256": source_hash}}}),
                    encoding="utf-8",
                )
                baseline.append(course)
            for index in range(1, 4):
                course = self._write_run(root / "modified" / f"run-{index}", 0.5)
                (course.parent / "run.json").write_text(
                    json.dumps({"input_manifest": {"track.gxm": {"sha256": "c"}}}),
                    encoding="utf-8",
                )
                modified.append(course)
            with self.assertRaisesRegex(ValueError, "baseline cohort source input hashes differ"):
                compare_course_cook_sets(baseline, modified)


if __name__ == "__main__":
    unittest.main()
