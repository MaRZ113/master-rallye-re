import json
from pathlib import Path
import unittest

HERE=Path(__file__).parent


class BodyLightAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((HERE/'source-joins.json').read_text())
        cls.evidence=json.loads((HERE/'r5900-byte-evidence.json').read_text())

    def test_independent_original_r5900_words(self):
        self.assertEqual(self.evidence['ghidra_language'],'r5900:LE:32:default')
        self.assertEqual(self.evidence['word_correspondence_checked'],1308)
        rows={int(x['va'],16):x for x in self.evidence['instruction_samples']}
        self.assertEqual(rows[0x391c54]['word'],'0x2403000e')
        self.assertEqual(rows[0x391cc0]['word'],'0x24030001')
        self.assertEqual(self.evidence['strings']['0x487958'],'breaklightsonglow-')
        self.assertTrue(all(self.evidence['tokens_not_present_as_literal_c_strings'].values()))

    def test_real_brake_on_and_glow_are_not_carshiny(self):
        families=self.report['brake_family_inventory']
        self.assertEqual(len(families),29)
        meshes=[m for v in families for m in v.get('light_meshes',[])]
        self.assertEqual(len(meshes),60)
        glow=[m for m in meshes if m['post_shader_texture_override']=='BREAKLIGHTSONGLOW_PRIMARY_SUBSTRING']
        on=[m for m in meshes if m['post_shader_texture_override']=='BREAKLIGHTSON_PRIMARY_SUBSTRING']
        self.assertEqual(len(glow),28);self.assertEqual(len(on),28)
        self.assertTrue(all(m['final_mode_in_loader']==14 for m in glow))
        self.assertTrue(all(m['final_mode_in_loader']==1 for m in on))

    def test_remaining_mixed_material_draws_fail_whole_carshiny(self):
        cases={(v['vehicle'],d['draw']):d for v in self.report['remaining_families'] for d in v['draws']}
        for key, shaders in [(('Xtrail',1),{'carshiny','carflat'}),(('ChevyBlazer',7),{'carshiny','carglass'}),
                             (('Forester',9),{'carshiny',None})]:
            d=cases[key]
            self.assertFalse(d['already_registered'])
            self.assertEqual(d['unmatched_faces'],0)
            self.assertEqual({m['mesh']['contract']['interned_shader'] for m in d['material_matches']},shaders)
        for key,missing in [(('LandCruiser',8),25),(('LandCruiser',9),104),(('Bruno',4),3),(('SeatBuggy',7),4)]:
            self.assertEqual(cases[key]['unmatched_faces'],missing)
            self.assertFalse(cases[key]['already_registered'])

    def test_generic_mode_preserves_authored_map(self):
        v=next(v for v in self.report['remaining_families'] if v['vehicle']=='Forester')
        rear=next(d for d in v['draws'] if d['draw']==9)
        untagged=next(m['mesh'] for m in rear['material_matches'] if m['mesh']['contract']['mode'] is None)
        self.assertEqual(untagged['final_mode_in_loader'],3)
        self.assertEqual(untagged['fallback_secondary'],'AUTHORED_MAP_RETAINED_NOT_RENDERTARGET_OVERRIDE')
        self.assertEqual(untagged['texture_slots'][1],'whitepaint-tga')


if __name__=='__main__':unittest.main()
