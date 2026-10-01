from __future__ import annotations

import sys
import tempfile
import unittest
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "tools" / "scanner"
if str(SCANNER) not in sys.path:
    sys.path.insert(0, str(SCANNER))

from r_dev1_config_inventory import inventory_corpora, render_markdown


class DevelopmentConfigInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_tracks_load_order_values_and_present_editor_files(self):
        self.write(
            "demo-8.4.1/DataGame/Game.xml",
            '<Game><Broker><Value Name="Load/Dev" Type="XmlFilename" Value="Dev" />'
            '<Value Name="Load/Editors" Type="XmlFilename" Value="Editors" />'
            '<Value Name="Unrelated/Example" Type="Bool" Value="False" />'
            "</Broker></Game>",
        )
        self.write(
            "demo-8.4.1/DataGame/dev.xml",
            '<Game><Broker><Value Name="Menues/Enabled" Type="Bool" Value="True" '
            'SaveOptions="False" SavePlayerState="False" /></Broker></Game>',
        )
        self.write("demo-8.4.1/DataGame/Editors.xml", "<Game><Broker /></Game>")
        self.write("demo-8.4.1/DataEditors/Help.txt", "synthetic only")

        report = inventory_corpora(self.root)
        build = report["builds"]["8.4.1"]
        self.assertEqual(
            [item["key"] for item in build["game_xml_load_order"]],
            ["Load/Dev", "Load/Editors"],
        )
        self.assertTrue(all(item["exists"] for item in build["game_xml_load_order"]))
        self.assertEqual(build["game_xml_load_order"][0]["file"], "DataGame/Dev.xml")
        self.assertEqual(build["game_xml_load_order"][0]["resolved_path"], "DataGame/dev.xml")
        self.assertEqual(
            build["game_xml_load_order"][0]["lookup_model"],
            "case-insensitive Windows filename semantics",
        )
        self.assertEqual(build["development_values"][0]["value"], "True")
        source = build["configs"]["Game"]
        self.assertEqual(source["build"], "8.4.1")
        self.assertEqual(source["corpus_identity"], "demo-8.4.1")
        self.assertEqual(source["source_relative_path"], "demo-8.4.1/DataGame/Game.xml")
        payload = (self.root / source["source_relative_path"]).read_bytes()
        self.assertEqual(source["source_size_bytes"], len(payload))
        self.assertEqual(source["source_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertTrue(build["dataeditors_directory_present"])
        editor_file = build["dataeditors_files"][0]
        self.assertEqual(editor_file["path"], "DataEditors/Help.txt")
        self.assertEqual(editor_file["size"], len(b"synthetic only"))
        self.assertEqual(
            editor_file["sha256"], hashlib.sha256(b"synthetic only").hexdigest()
        )
        self.assertEqual(editor_file["referenced_editor"], None)
        self.assertEqual(
            editor_file["content_classification"], "human-readable text candidate"
        )
        self.assertEqual(
            [value["name"] for value in build["configs"]["Game"]["values"]],
            ["Load/Dev", "Load/Editors"],
        )

    def test_retail_archive_root_is_kept_separate_from_demo_root(self):
        self.write(
            "retail/Data.sma_unpacked/DataGame/Game.xml",
            '<Game><Broker><Value Name="Load/Dev" Type="XmlFilename" Value="Dev" />'
            "</Broker></Game>",
        )
        self.write(
            "retail/Data.sma_unpacked/DataGame/dev.xml",
            '<Game><Broker><Value Name="DebugWindow/Enabled" Type="Bool" Value="False" />'
            "</Broker></Game>",
        )
        report = inventory_corpora(self.root)
        build = report["builds"]["retail"]
        self.assertEqual(
            build["configs"]["Game"]["path"],
            "Data.sma_unpacked/DataGame/Game.xml",
        )
        self.assertTrue(build["game_xml_load_order"][0]["exists"])
        self.assertEqual(
            build["game_xml_load_order"][0]["resolved_path"],
            "Data.sma_unpacked/DataGame/dev.xml",
        )
        self.assertEqual(build["development_values"][0]["name"], "DebugWindow/Enabled")

    def test_missing_or_malformed_files_are_reported_without_aborting(self):
        self.write("demo-9.3.1/DataGame/Game.xml", "<Game><Broker>")
        report = inventory_corpora(self.root)
        build = report["builds"]["9.3.1"]
        self.assertEqual(build["configs"]["Game"]["status"], "error")
        self.assertEqual(build["configs"]["dev"]["status"], "missing")
        self.assertEqual(build["game_xml_load_order"], [])

    def test_markdown_labels_values_as_corpus_observations(self):
        report = inventory_corpora(self.root)
        rendered = render_markdown(report)
        self.assertIn("not compiled fallbacks or effective runtime values", rendered)
        self.assertIn("## retail", rendered)


if __name__ == "__main__":
    unittest.main()
