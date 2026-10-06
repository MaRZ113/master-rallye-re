from __future__ import annotations

import hashlib
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import prepare_vehicle_unlock_overlay as overlay


def _value(name: str, value: str, kind: str = "String") -> str:
    return f'<Value Name="{name}" Type="{kind}" Value="{value}"/>'


def _locked_id3_template() -> str:
    return """      <Egg Name="T1_Car4">
        <Value Name="en2d Image Bank Index" Type="Int" Value="27"/>
        <AI_List>
          <AI No="0">
            <Value Name="AI Name" Type="String" Value="gaFrontendDisablerAI"/>
            <gaFrontendDisablerAI>
              <Value Name="Broker Value1*" Type="String" Value="Progress/UnlockedCars/T1CupCar1"/>
              <Value Name="Broker Value2*" Type="String" Value="Progress/Cheats/UnlockCars"/>
              <Value Name="Broker Value3*" Type="String" Value="Progress/Cheats/UnlockAll"/>
              <Value Name="True Value" Type="Int" Value="27"/>
              <Value Name="False Value" Type="Int" Value="15"/>
            </gaFrontendDisablerAI>
          </AI>
          <AI No="1"><Value Name="AI Name" Type="String" Value="Null"/></AI>
          <AI No="2">
            <Value Name="AI Name" Type="String" Value="gaFrontendXYButtonAI"/>
            <gaFrontendXYButtonAI>
              <Value Name="Button ID" Type="Int" Value="1"/>
              <Value Name="X ID" Type="Int" Value="3"/>
              <Value Name="Y ID" Type="Int" Value="0"/>
              <Value Name="XPos*" Type="String" Value="Frontend/VehicleSelect/Button3XPos"/>
              <Value Name="Enabled" Type="Bool" Value="True"/>
            </gaFrontendXYButtonAI>
          </AI>
          <AI No="3">
            <Value Name="AI Name" Type="String" Value="gaFrontendButtonUnlockerAI"/>
            <gaFrontendButtonUnlockerAI>
              <Value Name="Unlock 1*" Type="String" Value="Progress/UnlockedCars/T1CupCar1"/>
              <Value Name="1 OR 2" Type="Bool" Value="True"/>
              <Value Name="Unlock 2*" Type="String" Value="Progress/Cheats/UnlockCars"/>
              <Value Name="Control AI ID" Type="Int" Value="2"/>
              <Value Name="1?2 OR 3" Type="Bool" Value="True"/>
              <Value Name="Unlock 3*" Type="String" Value="Progress/Cheats/UnlockAll"/>
            </gaFrontendButtonUnlockerAI>
          </AI>
        </AI_List>
      </Egg>"""


def _scene_fixture() -> bytes:
    widgets = []
    for index in range(1, 8):
        widgets.append(_locked_id3_template() if index == 4 else
                       f'      <Egg Name="T1_Car{index}"><Value Name="fixture" Type="Int" Value="{index}"/></Egg>')
    text = "<Scene>\r\n  <EggLists_Version4>\r\n    <List Name=\"cars\">\r\n"
    text += "\r\n".join(widgets)
    text += "\r\n    </List>\r\n  </EggLists_Version4>\r\n</Scene>\r\n"
    return text.encode("utf-8")


def _slot(output_bytes: bytes) -> ET.Element:
    root = ET.fromstring(output_bytes.decode("utf-8-sig"))
    matches = [node for node in root.findall("./EggLists_Version4/List/Egg")
               if node.get("Name") == "T1_Car8"]
    if len(matches) != 1:
        raise AssertionError("expected one generated T1_Car8")
    return matches[0]


def _ai_body(slot: ET.Element, ai_no: str, name: str) -> ET.Element:
    matches = [node for node in slot.findall("./AI_List/AI") if node.get("No") == ai_no]
    if len(matches) != 1:
        raise AssertionError(f"missing AI {ai_no}")
    body = matches[0].find("./" + name)
    if body is None:
        raise AssertionError(f"missing {name}")
    return body


def _values(body: ET.Element) -> dict[str, str]:
    return {node.get("Name", ""): node.get("Value", "") for node in body.findall("./Value")}


class VehicleUnlockOverlayTests(unittest.TestCase):
    def test_overlay_output_requires_known_ignored_research_root(self) -> None:
        self.assertTrue(overlay._is_research_output(Path(".research-output/overlay.xml")))
        self.assertTrue(overlay._is_research_output(Path("research-output/overlay.xml")))
        self.assertFalse(overlay._is_research_output(Path("overlay.xml")))

    def test_clone_preserves_stock_unlocker_and_changes_only_id26_slot_fields(self) -> None:
        source = _scene_fixture()
        output, manifest = overlay.build_overlay_bytes(
            source, expected_source_sha256=hashlib.sha256(source).hexdigest())
        self.assertNotEqual(output, source)
        self.assertEqual(manifest["status"], "READY_FOR_HUMAN_RUNTIME")
        self.assertEqual(manifest["change"]["physical_vehicle_id"], 26)
        self.assertEqual(manifest["change"]["class_local_index"], 7)
        self.assertEqual(manifest["audit"]["source_mutated"], False)
        self.assertEqual(manifest["audit"]["physical_vehicle_id_rewritten"], False)

        slot = _slot(output)
        self.assertEqual(slot.find('./Value[@Name="en2d Image Bank Index"]').get("Value"), "3")
        disabler = _values(_ai_body(slot, "0", "gaFrontendDisablerAI"))
        self.assertEqual(disabler["True Value"], "3")
        self.assertEqual(disabler["False Value"], "15")
        button = _values(_ai_body(slot, "2", "gaFrontendXYButtonAI"))
        self.assertEqual(button["X ID"], "7")
        self.assertEqual(button["XPos*"], "Frontend/VehicleSelect/Button7XPos")
        unlocker = _values(_ai_body(slot, "3", "gaFrontendButtonUnlockerAI"))
        self.assertEqual(unlocker["Control AI ID"], "2")
        self.assertEqual(unlocker["Unlock 1*"], "Progress/UnlockedCars/T1CupCar1")
        self.assertEqual(unlocker["Unlock 2*"], "Progress/Cheats/UnlockCars")
        self.assertEqual(unlocker["Unlock 3*"], "Progress/Cheats/UnlockAll")

    def test_native_gate_configuration_selects_locked_and_unlocked_states(self) -> None:
        source = _scene_fixture()
        output, _manifest = overlay.build_overlay_bytes(
            source, expected_source_sha256=hashlib.sha256(source).hexdigest())
        slot = _slot(output)
        disabler = _values(_ai_body(slot, "0", "gaFrontendDisablerAI"))
        unlocker = _values(_ai_body(slot, "3", "gaFrontendButtonUnlockerAI"))

        def state(progress: bool, unlock_cars: bool, unlock_all: bool) -> tuple[bool, int]:
            # Mirrors the audited stock OR gates consumed by DisablerAI and
            # ButtonUnlockerAI, whose Control AI ID points at the XY button.
            available = ((progress or unlock_cars) or unlock_all)
            frame = int(disabler["True Value"] if available else disabler["False Value"])
            return available, frame

        self.assertEqual(state(False, False, False), (False, 15))
        self.assertEqual(state(True, False, False), (True, 3))
        self.assertEqual(state(False, True, False), (True, 3))
        self.assertEqual(state(False, False, True), (True, 3))
        self.assertEqual(unlocker["1 OR 2"], "True")
        self.assertEqual(unlocker["1?2 OR 3"], "True")
        self.assertEqual(unlocker["Control AI ID"], "2")

    def test_overlay_diff_is_only_one_appended_slot_and_source_slots_are_unchanged(self) -> None:
        source = _scene_fixture()
        output, _manifest = overlay.build_overlay_bytes(
            source, expected_source_sha256=hashlib.sha256(source).hexdigest())
        source_text = source.decode("utf-8")
        output_text = output.decode("utf-8")
        start, end = overlay._egg_span(output_text, "T1_Car8")
        newline = "\r\n"
        self.assertEqual(output_text[:start] + output_text[end + len(newline):], source_text)
        self.assertIn('<Egg Name="T1_Car4">', output_text)
        self.assertIn('<Egg Name="T1_Car7">', output_text)

    def test_production_source_hash_is_pinned_and_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(overlay.OverlayError, "unsupported Vehicle Select source SHA256"):
            overlay.build_overlay_bytes(_scene_fixture())

    def test_stock_t1_car4_template_must_keep_the_audited_unlocker(self) -> None:
        text = _scene_fixture().decode("utf-8")
        text = text.replace('Value="Progress/UnlockedCars/T1CupCar1"',
                            'Value="Progress/UnlockedCars/T1CupCar2"', 1)
        data = text.encode("utf-8")
        with self.assertRaisesRegex(overlay.OverlayError, "unsupported Vehicle Select source SHA256"):
            overlay.build_overlay_bytes(data)
        with self.assertRaisesRegex(overlay.OverlayError, "stock ID3 disabler"):
            overlay.build_overlay_bytes(data, expected_source_sha256=hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
