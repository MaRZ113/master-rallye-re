"""Source-qualified native UI regression; no proprietary fixture is distributed."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from extra_options_resources import native_setup_page


class NativeSetupPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path('D:/Game/Master Rallye Pristine/Data.sma_unpacked/DataScene/FrontendScreens/VehicleSetup4.xml')
        if not cls.source.is_file():raise unittest.SkipTest('owner-local native Gearbox template unavailable')
        cls.raw=cls.source.read_bytes()

    def test_native_component_ownership_and_navigation(self):
        page=ET.fromstring(native_setup_page(self.raw))
        components={}
        for egg in page.findall('.//Egg'):
            for ai in egg.findall('./AI_List/AI'):
                for component in list(ai)[1:]:
                    id_=component.find("Value[@Name='Button ID']")
                    if id_ is not None:
                        number=int(id_.get('Value'))
                        # Stock labels and their slider share focus ID 2.
                        if number>=5:self.assertNotIn(number,components)
                        components[number]=component
        self.assertEqual(set(components),set(range(1,10)))
        for number in range(5,10):
            for key in ('Up Path','Down Path'):
                value=components[number].find("Value[@Name='%s']"%key)
                self.assertEqual(value.get('Type'),'Int')
                self.assertIn(int(value.get('Value')),components)
        self.assertEqual(components[7].find("Value[@Name='Down Path']").get('Value'),'8')
        self.assertEqual(components[8].find("Value[@Name='Down Path']").get('Value'),'9')
        for key in ('Paint','Tire'):
            arrows=page.findall(".//Value[@Name='Arrow Status*'][@Value='Frontend/ExtraOptions/%sRightArrow']"%key)
            self.assertEqual(len(arrows),1)

    def test_stock_font_labels_and_separate_draft_actions(self):
        page=ET.fromstring(native_setup_page(self.raw))
        for name,text in [('ExtraPaint','PAINT / LIVERY'),('ExtraTires','TIRES'),('ExtraApply','APPLY'),('ExtraCancel','CANCEL'),('ExtraDefaults','DEFAULTS')]:
            egg=page.find(".//Egg[@Name='%s']"%name)
            self.assertEqual(egg.find(".//enUITextButtonAI/Value[@Name='Text String']").get('Value'),text)
        self.assertEqual(native_setup_page(self.raw),native_setup_page(self.raw))

    def test_action_controls_are_enlarged_without_moving_gearbox(self):
        page=ET.fromstring(native_setup_page(self.raw))
        for name in ('ExtraApply','ExtraCancel','ExtraDefaults'):
            matrix=page.find(".//Egg[@Name='%s']/Value[@Name='en2d Matrix']"%name)
            self.assertEqual(float(matrix.get('Row0').split()[0]), .62)
        gearbox=page.find(".//Egg[@Name='GearType']/Value[@Name='en2d Matrix']")
        self.assertEqual(gearbox.get('Row3'), '40.00 277.00 0.00 1.00')

    def test_unrelated_scene_is_rejected(self):
        with self.assertRaises(ValueError):native_setup_page(b'<Scene/>')


if __name__=='__main__':unittest.main()
