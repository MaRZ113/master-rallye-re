from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/scanner"))
from broker_xml_inventory import inspect_xml


class XmlMetadataTests(unittest.TestCase):
    def inspect(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.xml"
            path.write_text(text, encoding="utf-8")
            return inspect_xml(path)

    def test_values_not_exported_types_and_order_preserved(self):
        result = self.inspect('<Game><Broker><Value Name="Test/X" Type="Int" Value="PRIVATE" SaveOptions="True" SavePlayerState="False"/><Value Type="FutureType" Name="Test/X" Value="SECRET"/></Broker></Game>')
        self.assertEqual(result["duplicate_path_count"], 1)
        self.assertEqual(result["type_counts"], {"FutureType": 1, "Int": 1})
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("SECRET", str(result))
        self.assertEqual(len(result["attribute_orders"]), 2)

    def test_xmldata_and_xmlfilename_inspected_without_payload(self):
        result = self.inspect('<Game><Broker><Value Name="Test/Object" Type="XmlData" XmlData="Synthetic"><Synthetic Secret="PRIVATE"/></Value><Value Name="Load/Test" Type="XmlFilename" Value="test"/></Broker></Game>')
        self.assertEqual(result["type_counts"], {"XmlData": 1, "XmlFilename": 1})
        self.assertNotIn("PRIVATE", str(result))

    def test_malformed_and_entity_fail(self):
        with self.assertRaises(ET.ParseError):
            self.inspect('<Game>')
        with self.assertRaises(ValueError):
            self.inspect('<!DOCTYPE Game [<!ENTITY v "x">]><Game/>')


if __name__ == "__main__":
    unittest.main()
