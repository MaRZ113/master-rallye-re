from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / "tools"))

from r5t_d0_race_logic import _distance, _egg_dict, _retail_corpus_summary  # noqa: E402
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402


class R5TD0SpatialAnalysisTests(unittest.TestCase):
    def test_xz_distance_uses_world_horizontal_axes_and_ignores_height(self):
        self.assertEqual(_distance((0.0, 100.0, 0.0), (3.0, -100.0, 4.0), 2), 5.0)
        self.assertGreater(_distance((0.0, 100.0, 0.0), (3.0, -100.0, 4.0)), 200.0)

    def test_split_report_retains_raw_egg_ai_and_component_fields(self):
        xml = (
            b'<Scene><EggLists_Version4><List Name="SplitTimes"><Egg Name="SplitTime0" Custom="raw">'
            b'<Value Name="en3d Matrix" Type="Matrix" Row0="1 0 0 0" Row1="0 1 0 0" '
            b'Row2="0 0 1 0" Row3="1 2 3 1" />'
            b'<Value Name="Egg Extra" Type="String" Value="egg-raw" />'
            b'<AI_List><AI No="7" Custom="ai-raw"><Value Name="AI Name" Type="String" Value="split" />'
            b'<gaRaceSplitTimeAI Raw="component-raw"><Value Name="Split Time ID" Type="Int" Value="0" />'
            b'<Value Name="Radius" Type="Float" Value="21" />'
            b'<Value Name="ExtraTime" Type="Float" Value="77.5" />'
            b'<Value Name="Future" Type="String" Value="future-value" Extra="future-meta" />'
            b'</gaRaceSplitTimeAI></AI></AI_List></Egg></List></EggLists_Version4></Scene>'
        )
        egg = parse_course_xml_bytes(xml).split_time_eggs[0]
        report = _egg_dict(egg)
        self.assertEqual(report["attributes"]["Custom"], "raw")
        self.assertEqual(report["values"][1]["value"], "egg-raw")
        ai = report["ai_objects"][0]
        self.assertEqual(ai["attributes"]["Custom"], "ai-raw")
        component = ai["components"][0]
        self.assertEqual(component["attributes"]["Raw"], "component-raw")
        future = next(value for value in component["values"] if value["name"] == "Future")
        self.assertEqual(future["value"], "future-value")
        self.assertEqual(future["attributes"]["Extra"], "future-meta")

    def test_corpus_counts_split_components_independently_from_egg_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "component-only.xml").write_text(
                '<Scene><gaRaceSplitTimeAI><Value Name="Split Time ID" Type="Int" Value="4" />'
                '<Value Name="Radius" Type="Float" Value="17" />'
                '<Value Name="ExtraTime" Type="Float" Value="60" />'
                '</gaRaceSplitTimeAI></Scene>',
                encoding="utf-8",
            )
            summary = _retail_corpus_summary(root)
        self.assertEqual(summary["xml_files_with_split_time_ai"], 1)
        self.assertEqual(summary["split_time_component_count_distribution"], {"1": 1})
        self.assertEqual(summary["split_time_egg_count_distribution"], {"0": 1})
        self.assertEqual(summary["radius_range"], [17.0, 17.0])


if __name__ == "__main__":
    unittest.main()
