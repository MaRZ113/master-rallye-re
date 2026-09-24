"""Synthetic checks for R5V-A metadata discovery, without game data."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "scanner"))

from r5v_a_inventory import inventory
from r5v_a_exe_registry import records


class RegistryInventoryTests(unittest.TestCase):
    def test_unknown_exe_is_rejected_before_disassembly(self):
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "MRallye.exe"
            exe.write_bytes(b"synthetic, not a verified build")
            with self.assertRaisesRegex(ValueError, "hash does not match"):
                records(exe, "final", Path(temp) / "missing-objdump")

    def test_nested_archive_metadata_keeps_xml_order_separate_from_folders(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            packed = source / "Data.sma_unpacked"
            game = packed / "DataGame"
            scene = packed / "DataScene" / "RaceTest"
            vehicles = packed / "DataGx" / "Vehicles"
            for folder in (game, scene, vehicles / "Alpha", vehicles / "Zulu"):
                folder.mkdir(parents=True)
            (game / "vehicles.xml").write_text(
                '<Game><Broker>'
                '<Value Name="Vehicles/Zulu/Engine/RevLimit" Value="1"/>'
                '<Value Name="Vehicles/Tyres/gravel0/PeakMu" Value="1"/>'
                '<Value Name="Vehicles/Alpha/Engine/RevLimit" Value="2"/>'
                '</Broker></Game>', encoding="utf-8"
            )
            (game / "frontend.xml").write_text(
                '<Game><Broker><Value Name="Frontend/QuickRace/Car0" '
                'Value="3" SavePlayerState="True"/></Broker></Game>', encoding="utf-8"
            )
            (scene / "Test.xml").write_text(
                '<Scene><Value Name="Car Name" Value="Zulu"/></Scene>', encoding="utf-8"
            )
            (vehicles / "Zulu" / "car.dx").write_bytes(b"synthetic")
            result = inventory(source, "synthetic")
            self.assertEqual(
                [x["name"] for x in result["physics_sections_xml_order_not_registry_order"]],
                ["Zulu", "Alpha"],
            )
            self.assertEqual(
                [x["name"] for x in result["vehicle_folders_not_registry_order"]],
                ["Alpha", "Zulu"],
            )
            self.assertEqual(result["frontend_state"][0]["value"], "3")
            self.assertEqual(result["scene_car_name_refs"],
                             [{"path": "RaceTest/Test.xml", "name": "Zulu"}])
            self.assertIsNone(result["hashes"]["MRallye.exe"])


if __name__ == "__main__":
    unittest.main()