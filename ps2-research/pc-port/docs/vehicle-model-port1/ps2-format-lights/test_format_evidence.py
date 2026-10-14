from pathlib import Path
import json
import unittest

HERE=Path(__file__).resolve().parent


class ByteAndOwnershipEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe=json.loads((HERE/'r5900-format-evidence.json').read_text())
        cls.lamps=json.loads((HERE/'lights-contract.json').read_text())

    def test_canonical_r5900_correspondence(self):
        self.assertEqual(self.probe['elf_sha256'],'b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2')
        self.assertEqual(self.probe['ghidra_language'],'r5900:LE:32:default')
        self.assertEqual(self.probe['decoder'],'Rabbitizer InstrCategory.R5900')
        self.assertGreaterEqual(self.probe['word_correspondence_checked'],2032)

    def test_102_is_cylinder_not_lod(self):
        self.assertEqual(self.probe['strings']['0x4879c0'],'wheel')
        self.assertIn('cylinder',self.probe['strings']['0x487a18'])
        rows={r['va']:r for r in self.probe['instructions']}
        self.assertEqual(rows['0x38ff1c']['word'],'0xc0e51ec')
        self.assertEqual(rows['0x3a5c74']['word'],'0xe4400014')
        self.assertEqual(rows['0x3a5ca4']['word'],'0xe4400018')

    def test_exact_source_spelling_and_no_shader_alias(self):
        self.assertEqual(self.lamps['material_classifier']['post_shader_priority'][0]['original_primary_substring'],'breaklightsonglow-')
        self.assertEqual(self.lamps['material_classifier']['post_shader_priority'][1]['original_primary_substring'],'breaklightson-')
        self.assertTrue(self.lamps['material_classifier']['unknown_names_not_silently_aliased'])

    def test_lamp_states_are_named_selectors_not_child_ordinals(self):
        for family in self.lamps['families']:
            for mesh in family.get('light_meshes',[]):
                if mesh['final_mode'] in (1,14):self.assertEqual(mesh['selector'],2)
        self.assertEqual(self.lamps['mode_record_counts'],{'1':28,'14':28,'3':4})
        self.assertEqual(self.lamps['owner_update']['threshold_word'],'0x3dcccccd')

    def test_no_live_gs_or_pc_claim(self):
        self.assertEqual(self.lamps['gs_and_runtime_status'],'UNKNOWN')
        self.assertGreaterEqual(len(self.lamps['missing_interfaces']),5)
        self.assertEqual(self.probe['strings']['0x472498'],'gaSFXBrakeLights')


if __name__=='__main__':unittest.main()
