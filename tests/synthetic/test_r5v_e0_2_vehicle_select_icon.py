from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.prepare_vehicle_select_icon_overlay import DXT_MAGIC, OverlayError, generate_overlay


def _widget(name: str, local_index: int, row_id: int, frame: int, *, locked: bool = False) -> str:
    unlock_ai = """<AI No="3"><Value Name="AI Name" Type="String" Value="gaFrontendButtonUnlockerAI"/></AI>""" if locked else ""
    disabler_ai = """<AI No="0"><Value Name="AI Name" Type="String" Value="gaFrontendDisablerAI"/></AI>""" if locked else ""
    return f'''<Egg Name="{name}">
        <Value Name="en2d Model Name" Type="String" Value="frontend\\vehicleselect\\carsheet"/>
        <Value Name="en2d Matrix" Type="Matrix" Row3="340.00 309.00 0.00 1.00"/>
        <Value Name="en2d FileType" Type="Int" Value="1"/>
        <Value Name="en2d Image Bank Index" Type="Int" Value="{frame}"/>
        <AI_List>
          {disabler_ai}
          <AI No="2">
            <Value Name="AI Name" Type="String" Value="gaFrontendXYButtonAI"/>
            <gaFrontendXYButtonAI>
              <Value Name="Button ID" Type="Int" Value="1"/>
              <Value Name="X ID" Type="Int" Value="{local_index}"/>
              <Value Name="Y ID" Type="Int" Value="{row_id}"/>
              <Value Name="XPos*" Type="String" Value="Frontend/VehicleSelect/Button{local_index}XPos"/>
            </gaFrontendXYButtonAI>
          </AI>
          {unlock_ai}
        </AI_List>
      </Egg>'''


def _scene(class_counts: dict[str, int], *, locked_template: bool = False) -> str:
    entries: list[str] = []
    rows = {"T1": 0, "T2": 1, "T3": 2}
    frames = {"T1": 3, "T2": 23, "T3": 6}
    for class_name, count in class_counts.items():
        for local_index in range(count):
            locked = locked_template and class_name == "T3" and local_index == 0
            entries.append(_widget(
                f"{class_name}_Car{local_index + 1}", local_index, rows[class_name], frames[class_name], locked=locked
            ))
    return "<Scene>\r\n<EggLists_Version4>\r\n<List Name=\"VehicleSelectScreen\"/>\r\n<List Name=\"cars\">\r\n" + "\r\n".join(entries) + "\r\n</List>\r\n</EggLists_Version4>\r\n</Scene>\r\n"


def _dxt(path: Path) -> None:
    path.write_bytes(struct.pack("<5I", DXT_MAGIC, 0, 0, 2, 2) + bytes(16))


class VehicleSelectIconOverlayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.asset_root = self.root / "assets"
        self.asset_root.mkdir()
        (self.asset_root / "carsheet.dxb").write_bytes(b"synthetic bank")
        for index in range(32):
            _dxt(self.asset_root / f"carsheet_{index:03d}_000.dxt")
        self.output_root = self.root / "research-output" / "case"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_inputs(
        self,
        class_counts: dict[str, int],
        slots: list[dict[str, object]],
        *,
        position_count: int = 12,
        class_mappings: dict[str, dict[str, int]] | None = None,
        locked_template: bool = False,
    ) -> tuple[Path, Path]:
        source_text = _scene(class_counts, locked_template=locked_template)
        source = self.root / "VehicleSelect.xml"
        source.write_bytes(source_text.encode("utf-8"))
        manifest = self.root / "icon-mapping.json"
        profile = {
            "schema_version": 2,
            "source_scene_sha256": hashlib.sha256(source.read_bytes()).hexdigest().upper(),
            "image_bank": {
                "scene_name": "frontend\\vehicleselect\\carsheet",
                "container": "carsheet.dxb",
                "frame_pattern": "carsheet_{index:03d}_000.dxt",
                "frame_count": 32,
                "file_type": "1",
            },
            "class_mappings": class_mappings or {
                "T1": {"vehicle_id_base": 0, "row_id": 0},
                "T2": {"vehicle_id_base": 7, "row_id": 1},
                "T3": {"vehicle_id_base": 14, "row_id": 2},
            },
            "layout_position_properties": [
                f"Frontend/VehicleSelect/Button{index}XPos" for index in range(position_count)
            ],
            "slots": slots,
        }
        manifest.write_text(json.dumps(profile), encoding="utf-8")
        return source, manifest

    def _generate(self, source: Path, manifest: Path, name: str = "VehicleSelect.xml") -> dict[str, object]:
        return generate_overlay(source, self.output_root / name, self.asset_root, manifest)

    def test_retail_t3_car12_clones_diagnostic_astero_frame_and_local_binding(self) -> None:
        source, manifest = self._write_inputs(
            {"T3": 11},
            [{"class": "T3", "local_index": 11, "vehicle_id": 25, "template_widget": "T3_Car1", "frame_index": 5}],
        )
        original = source.read_bytes()
        result = self._generate(source, manifest)
        generated = Path(str(result["output_scene"]))
        output = generated.read_bytes()
        self.assertEqual(result["status"], "GENERATED")
        additions = result["additions"]
        assert isinstance(additions, list)
        self.assertEqual(additions[0]["frame_sha256"], hashlib.sha256((self.asset_root / "carsheet_005_000.dxt").read_bytes()).hexdigest().upper())
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), hashlib.sha256(original).digest())
        self.assertEqual(output.replace(_widget("T3_Car12", 11, 2, 5).encode() + b"\r\n", b"", 1), original)
        tree = ET.parse(generated).getroot()
        target = next(node for node in tree.iter("Egg") if node.get("Name") == "T3_Car12")
        values = {node.get("Name"): node.attrib for node in target.findall("./Value")}
        self.assertEqual(values["en2d Image Bank Index"]["Value"], "5")
        self.assertEqual(values["en2d Matrix"]["Row3"], "340.00 309.00 0.00 1.00")
        xy = target.find("./AI_List/AI/gaFrontendXYButtonAI")
        assert xy is not None
        button = {node.get("Name"): node.get("Value") for node in xy.findall("./Value")}
        self.assertEqual(button["X ID"], "11")
        self.assertEqual(button["Y ID"], "2")
        self.assertEqual(button["XPos*"], "Frontend/VehicleSelect/Button11XPos")
        self.assertEqual([node.get("Name") for node in target.findall("./AI_List/AI/Value[@Name='AI Name']") if node.get("Value") in {"gaFrontendDisablerAI", "gaFrontendButtonUnlockerAI"}], [])

    def test_generic_manifest_can_append_t1_t2_and_future_t3_widgets(self) -> None:
        # Synthetic future mapping only. It proves the tool is not T3_Car12-specific;
        # it does not assert that retail currently supports these registry IDs.
        mappings = {
            "T1": {"vehicle_id_base": 0, "row_id": 0},
            "T2": {"vehicle_id_base": 8, "row_id": 1},
            "T3": {"vehicle_id_base": 16, "row_id": 2},
        }
        slots = [
            {"class": "T1", "local_index": 7, "vehicle_id": 7, "template_widget": "T1_Car1", "frame_index": 5},
            {"class": "T2", "local_index": 7, "vehicle_id": 15, "template_widget": "T2_Car1", "frame_index": 6},
            {"class": "T3", "local_index": 11, "vehicle_id": 27, "template_widget": "T3_Car1", "frame_index": 7},
            {"class": "T3", "local_index": 12, "vehicle_id": 28, "template_widget": "T3_Car1", "frame_index": 8},
        ]
        source, manifest = self._write_inputs({"T1": 7, "T2": 7, "T3": 11}, slots, position_count=13, class_mappings=mappings)
        result = self._generate(source, manifest)
        tree = ET.parse(str(result["output_scene"])).getroot()
        names = {node.get("Name") for node in tree.iter("Egg")}
        self.assertTrue({"T1_Car8", "T2_Car8", "T3_Car12", "T3_Car13"}.issubset(names))
        self.assertEqual(len(result["additions"]), 4)  # type: ignore[arg-type]

    def test_retail_profile_rejects_t3_car13_without_button12_evidence(self) -> None:
        source, manifest = self._write_inputs(
            {"T3": 11},
            [{"class": "T3", "local_index": 12, "vehicle_id": 26, "template_widget": "T3_Car1", "frame_index": 5}],
            position_count=12,
        )
        with self.assertRaisesRegex(OverlayError, "no verified layout position"):
            self._generate(source, manifest)

    def test_rejects_inconsistent_vehicle_id(self) -> None:
        source, manifest = self._write_inputs(
            {"T3": 11},
            [{"class": "T3", "local_index": 11, "vehicle_id": 24, "template_widget": "T3_Car1", "frame_index": 5}],
        )
        with self.assertRaisesRegex(OverlayError, "class-base/local-index"):
            self._generate(source, manifest)

    def test_rejects_unproven_locked_template(self) -> None:
        source, manifest = self._write_inputs(
            {"T3": 11},
            [{"class": "T3", "local_index": 11, "vehicle_id": 25, "template_widget": "T3_Car1", "frame_index": 5}],
            locked_template=True,
        )
        with self.assertRaisesRegex(OverlayError, "lock/unlock behavior"):
            self._generate(source, manifest)

    def test_rejects_bad_frame_and_source_hash(self) -> None:
        source, manifest = self._write_inputs(
            {"T3": 11},
            [{"class": "T3", "local_index": 11, "vehicle_id": 25, "template_widget": "T3_Car1", "frame_index": 32}],
        )
        with self.assertRaisesRegex(OverlayError, "frame_index"):
            self._generate(source, manifest)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["source_scene_sha256"] = "0" * 64
        manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(OverlayError, "SHA-256 mismatch"):
            self._generate(source, manifest)

    def test_rejects_invalid_indexed_image_bytes(self) -> None:
        source, manifest = self._write_inputs(
            {"T3": 11},
            [{"class": "T3", "local_index": 11, "vehicle_id": 25, "template_widget": "T3_Car1", "frame_index": 5}],
        )
        (self.asset_root / "carsheet_005_000.dxt").write_bytes(b"not a DXT image")
        with self.assertRaisesRegex(OverlayError, "shorter than its DXT header"):
            self._generate(source, manifest)

    def test_output_is_idempotent_and_conflicting_output_is_preserved(self) -> None:
        source, manifest = self._write_inputs(
            {"T3": 11},
            [{"class": "T3", "local_index": 11, "vehicle_id": 25, "template_widget": "T3_Car1", "frame_index": 5}],
        )
        first = self._generate(source, manifest)
        second = self._generate(source, manifest)
        self.assertEqual(first["status"], "GENERATED")
        self.assertEqual(second["status"], "ALREADY_PRESENT")
        output = Path(str(first["output_scene"]))
        output.write_bytes(b"preserve conflicting output")
        with self.assertRaisesRegex(OverlayError, "refusing to overwrite"):
            self._generate(source, manifest)
        self.assertEqual(output.read_bytes(), b"preserve conflicting output")


if __name__ == "__main__":
    unittest.main()
