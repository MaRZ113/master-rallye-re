from __future__ import annotations

import sys
import tempfile
import unittest
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
    sha256,
)


def _marker(name: str, index: int, position, direction=(1.0, 0.0, 0.0)):
    return SimpleNamespace(position=position, direction=direction, index_in_list=index)


def _probe_source() -> bytes:
    lists = []
    for name, count in (("RaceLine", 269), ("LeftInnerLimit", 101)):
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

    def test_probe_output_must_be_new_and_inside_research_output_probes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "France1.xml"
            output = root / "candidate.xml"
            with self.assertRaises(ProbeError):
                _assert_output_path(output, source)
            with self.assertRaises(ProbeError):
                _assert_output_path(source, source)


if __name__ == "__main__":
    unittest.main()
