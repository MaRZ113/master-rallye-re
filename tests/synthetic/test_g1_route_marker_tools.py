from __future__ import annotations

import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src", ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402
from g1_course_marker_analysis import _nearest_segment, _race_geometry  # noqa: E402
from g1_route_limit_probe import (  # noqa: E402
    ProbeError,
    _assert_output_path,
    _make_expected,
    _marker_pos_spans,
    _print_output_locations,
    resolve_output_paths,
    sha256,
    DEFAULT_OUTPUT_ROOT,
)


def _marker(name: str, index: int, position, direction=(1.0, 0.0, 0.0)):
    return SimpleNamespace(position=position, direction=direction, index_in_list=index)


def _probe_source() -> bytes:
    lists = []
    for name, count in (
        ("RaceLine", 269), ("LeftInnerLimit", 101), ("LeftOuterLimit", 61),
        ("RightInnerLimit", 1), ("RightOuterLimit", 1), ("Cameras", 1),
    ):
        markers = []
        for index in range(count):
            markers.append(
                '<Marker No="%d"><Value Name="Marker Type" Type="String" Value="route" />'
                '<Value Name="Marker Pos" Type="Vector3" Value="%.2f 2.0 %.2f" />'
                '<Value Name="Marker Dir" Type="Vector3" Value="1 0 0" /></Marker>'
                % (index, index + 0.25, index + 0.75)
            )
        lists.append(f'<List Name="{name}">' + "".join(markers) + "</List>")
    return ("<?xml version='1.0'?>\n<Scene><MarkerLists>" + "".join(lists) +
            "</MarkerLists><Unknown Value='preserve'/></Scene>\n").encode("ascii")


class G1RaceLineAnalysisTests(unittest.TestCase):
    def test_marker_parser_preserves_list_and_source_order_pos_dir(self):
        source = b"""<Scene><MarkerLists>
        <List Name='RaceLine'>
          <Marker No='a'><Value Name='Marker Pos' Type='Vector3' Value='10 20 30'/><Value Name='Marker Dir' Type='Vector3' Value='1 0 0'/></Marker>
          <Marker No='b'><Value Name='Marker Pos' Type='Vector3' Value='40 50 60'/><Value Name='Marker Dir' Type='Vector3' Value='0 0 -1'/></Marker>
        </List>
        <List Name='LeftInnerLimit'><Marker><Value Name='Marker Pos' Type='Vector3' Value='1 2 3'/><Value Name='Marker Dir' Type='Vector3' Value='0 1 0'/></Marker></List>
        </MarkerLists></Scene>"""
        document = parse_course_xml_bytes(source, "synthetic-g1.xml")
        race, limits = document.marker_lists
        self.assertEqual((race.name, race.ordinal), ("RaceLine", 0))
        self.assertEqual([marker.index_in_list for marker in race.markers], [0, 1])
        self.assertEqual([marker.position for marker in race.markers], [(10.0, 20.0, 30.0), (40.0, 50.0, 60.0)])
        self.assertEqual([marker.direction for marker in race.markers], [(1.0, 0.0, 0.0), (0.0, 0.0, -1.0)])
        self.assertEqual((limits.name, limits.ordinal, limits.markers[0].index_in_list), ("LeftInnerLimit", 1, 0))
        self.assertEqual(limits.markers[0].direction, (0.0, 1.0, 0.0))

    def test_forward_backward_and_central_tangents_are_distinct(self):
        markers = [
            _marker("RaceLine", 0, (0.0, 0.0, 0.0)),
            _marker("RaceLine", 1, (10.0, 0.0, 0.0)),
            _marker("RaceLine", 2, (20.0, 0.0, 0.0)),
        ]
        geometry = _race_geometry(markers)
        samples = geometry["_direction_alignment_samples"]
        self.assertEqual(samples["forward_3d"], [1.0, 1.0])
        self.assertEqual(samples["backward_3d"], [-1.0, -1.0])
        self.assertEqual(samples["central_3d"], [1.0])
        self.assertEqual(samples["forward_xz"], [1.0, 1.0])
        self.assertEqual(samples["backward_xz"], [-1.0, -1.0])

    def test_nearest_route_segment_returns_source_order_progress_and_side(self):
        route = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]
        mapped = _nearest_segment((5.0, 2.0, 4.0), route)
        self.assertEqual(mapped["segment_index"], 0)
        self.assertAlmostEqual(mapped["segment_t"], 0.5)
        self.assertAlmostEqual(mapped["progress"], 0.25)
        self.assertAlmostEqual(mapped["distance_xz"], 4.0)
        self.assertAlmostEqual(mapped["distance_3d"], (20.0 ** 0.5))
        self.assertEqual(mapped["side_sign"], 1)


class G1ProbeGuardTests(unittest.TestCase):
    def test_probe_changes_only_predeclared_marker_positions(self):
        source = _probe_source()
        output, edits = _make_expected(source, "raceline", expected_sha256=sha256(source))
        self.assertEqual([item["marker_index"] for item in edits], [265, 266, 267, 268])
        before = parse_course_xml_bytes(source)
        after = parse_course_xml_bytes(output)
        before_route = before.marker_lists[0].markers
        after_route = after.marker_lists[0].markers
        self.assertEqual(len(before_route), len(after_route))
        for index, (old, new) in enumerate(zip(before_route, after_route)):
            self.assertEqual(old.direction, new.direction)
            self.assertEqual(old.record.value("Marker Type"), new.record.value("Marker Type"))
            if index in {265, 266, 267, 268}:
                self.assertNotEqual(old.position, new.position)
                self.assertAlmostEqual(new.position[0] - old.position[0], -36.239355, places=5)
                self.assertAlmostEqual(new.position[1], old.position[1])
                self.assertAlmostEqual(new.position[2] - old.position[2], 16.932487, places=5)
            else:
                self.assertEqual(old.position, new.position)
        self.assertEqual(before.marker_lists[1], after.marker_lists[1])
        self.assertTrue(output.startswith(b"<?xml version='1.0'?>\n"))
        self.assertIn(b"<Unknown Value='preserve'/>", output)

    def test_probe_refuses_source_hash_mismatch_and_duplicate_list_identity(self):
        source = _probe_source()
        with self.assertRaises(ProbeError):
            _make_expected(source, "raceline", expected_sha256="0" * 64)
        duplicate = source.replace(b"</MarkerLists>", b'<List Name="RaceLine"></List></MarkerLists>')
        with self.assertRaises(ProbeError):
            _marker_pos_spans(duplicate, "RaceLine", 0)

    def test_probe_output_must_be_new_and_inside_explicit_research_output_root(self):
        with tempfile.TemporaryDirectory(prefix=".test-research-output-", dir=ROOT) as directory:
            root = Path(directory)
            source = root / "France1.xml"
            output = root / "g1" / "probes" / "France1_outerlimit_58-60.xml"
            _assert_output_path(output, source, root)
            with self.assertRaises(ProbeError):
                _assert_output_path(root / "g1" / "candidate.xml", source, root)
            with self.assertRaises(ProbeError):
                _assert_output_path(source, source, root)

    def test_research_output_roots_cannot_escape_the_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ProbeError, "must be inside the repository"):
                resolve_output_paths("outerlimit", output_root=Path(directory) / "outside")

    def test_outerlimit_probe_changes_only_three_predeclared_pos_fields(self):
        source = _probe_source()
        output, edits = _make_expected(source, "outerlimit", expected_sha256=sha256(source))
        self.assertEqual([item["marker_index"] for item in edits], [58, 59, 60])
        self.assertEqual({tuple(item["byte_range"]) for item in edits}.__len__(), 3)
        before = parse_course_xml_bytes(source)
        after = parse_course_xml_bytes(output)
        lists_before = {item.name: item for item in before.marker_lists}
        lists_after = {item.name: item for item in after.marker_lists}
        self.assertEqual(set(lists_before), set(lists_after))
        for name in set(lists_before) - {"LeftOuterLimit"}:
            before_markers = lists_before[name].markers
            after_markers = lists_after[name].markers
            self.assertEqual(len(before_markers), len(after_markers), name)
            self.assertEqual(
                [(item.position, item.direction, item.record.value("Marker Type")) for item in before_markers],
                [(item.position, item.direction, item.record.value("Marker Type")) for item in after_markers],
                name,
            )
        old_outer = lists_before["LeftOuterLimit"].markers
        new_outer = lists_after["LeftOuterLimit"].markers
        self.assertEqual(len(old_outer), len(new_outer))
        for index, (old, new) in enumerate(zip(old_outer, new_outer)):
            self.assertEqual(old.direction, new.direction)
            if index in {58, 59, 60}:
                self.assertAlmostEqual(new.position[0] - old.position[0], -33.453008, places=5)
                self.assertEqual(new.position[1], old.position[1])
                self.assertAlmostEqual(new.position[2] - old.position[2], -21.929346, places=5)
            else:
                self.assertEqual(old.position, new.position)
        self.assertEqual(output.count(b"<"), source.count(b"<"))

    def test_output_root_defaults_and_explicit_override_are_absolute_and_printed(self):
        default_root, default_candidate, _default_manifest = resolve_output_paths("outerlimit")
        self.assertEqual(default_root, DEFAULT_OUTPUT_ROOT.resolve())
        self.assertEqual(default_root, (ROOT / "research-output").resolve())
        self.assertEqual(default_candidate.parent, (DEFAULT_OUTPUT_ROOT / "g1" / "probes").resolve())
        with tempfile.TemporaryDirectory(prefix=".test-research-output-", dir=ROOT) as directory:
            root = Path(directory) / "custom-output"
            resolved, candidate, manifest = resolve_output_paths("outerlimit", output_root=root)
            self.assertEqual(resolved, root.resolve())
            self.assertEqual(candidate, (root / "g1" / "probes" / "France1_outerlimit_58-60.xml").resolve())
            self.assertEqual(manifest, candidate.with_suffix(candidate.suffix + ".manifest.json"))
            output = StringIO()
            with redirect_stdout(output):
                _print_output_locations(resolved, candidate, manifest)
            printed = output.getvalue()
            self.assertIn(str(resolved), printed)
            self.assertIn(str(candidate), printed)
            self.assertIn(str(manifest), printed)

    def test_raceline_and_first_limit_runtime_results_are_not_misclassified(self):
        results = (ROOT / "research" / "g1" / "runtime-results.md").read_text(encoding="utf-8")
        self.assertIn("CONFIRMED_BY_RUNTIME_EDIT", results)
        self.assertIn("NO_OBSERVABLE_AI_STEERING_CHANGE_IN_THIS_PROBE", results)
        self.assertIn("INCONCLUSIVE_RUNTIME_PROBE", results)


if __name__ == "__main__":
    unittest.main()
