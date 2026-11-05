import importlib.util,json,tempfile,unittest
from pathlib import Path
PORT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('region_authoring',PORT/'tools/atmosphere_regions.py');regions=importlib.util.module_from_spec(spec);spec.loader.exec_module(regions)
class RegionalAuthoring(unittest.TestCase):
    def test_country_context_and_ambiguous_layouts(self):
        names=['France','Italy','Turkey','Spain']
        for folder,expected in [('France_S1','France'),('invspaingx','Spain'),('track01',None),('invturkey','Turkey')]:self.assertEqual(regions.infer_region([folder],names),expected)
        self.assertIsNone(regions.infer_region(['France1','Turkey2'],names));self.assertIsNone(regions.infer_region(['France1','Unknown'],names))
    def test_export_is_data_only_and_preserves_unmodified_sky(self):
        presets=json.loads((PORT/'config/atmosphere28/presets.json').read_text())
        bindings={'bindings':[{'scene':'FranceS1','folders':['France_S1']},{'scene':'CustomMix','folders':['France1','Italy1']}]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=regions.export(bindings,presets,root/'gt3');self.assertEqual(r['counts'],{'France':1,'Base fallback':1});self.assertFalse(r['geometry_hash_allowlist'])
            self.assertNotIn('CustomMix=',(root/'gt3/regions.ini').read_text());self.assertTrue(all(x['settings']['SkyPreset']=='3' for x in presets['regions'].values()))
            regions.export(bindings,presets,root/'stock',True);self.assertIn('SkyPreset=1',(root/'stock/regions.ini').read_text())
            with self.assertRaises(ValueError):regions.export(bindings,presets,root/'gt3')
    def test_no_unsafe_or_duplicate_scene_binding(self):
        presets=json.loads((PORT/'config/atmosphere28/presets.json').read_text())
        for rows in [[{'scene':'../Turkey2','folders':['Turkey2']}],[{'scene':'France1','folders':['France1']},{'scene':'FRANCE1','folders':['France1']}]]:
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):regions.export({'bindings':rows},presets,Path(tmp)/'out')
