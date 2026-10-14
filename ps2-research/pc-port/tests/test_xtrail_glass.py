from pathlib import Path
import json, struct, unittest
PORT=Path(__file__).resolve().parents[1]
class GlassSourceEvidence(unittest.TestCase):
 def test_exact_separate_owner(self):
  d=json.loads((PORT/'docs/xtrail-lights-model/glass-source.json').read_text());old=json.loads((PORT/'docs/xtrail-fidelity/wheel-glass/source-evidence.json').read_text())
  self.assertEqual(d['source_owner'],'root.19');self.assertEqual(d['source_faces'],18);self.assertEqual(d['source_vertices'],22)
  self.assertEqual(old['models'][0]['draws'][10]['categories'],{'GLASS_DISTINCT_FROM_BODY_ENVIRONMENT':18})
 def test_private_layout(self):
  d=json.loads((PORT/'docs/xtrail-lights-model/glass-source.json').read_text());self.assertEqual(struct.calcsize('<8s4I')+22*struct.calcsize('<32s3f2fI3f2fI')+d['primary']['size']+d['highlight']['size'],d['asset_size'])
 def test_static_source_and_alpha(self):
  d=json.loads((PORT/'docs/xtrail-lights-model/glass-source.json').read_text());self.assertEqual((d['primary']['width'],d['highlight']['width']),(16,32));self.assertEqual((d['primary']['alpha_min'],d['primary']['alpha_max']),(7,138));self.assertEqual(d['highlight']['alpha_min'],255);self.assertEqual(d['runtime_validation'],'NOT_PERFORMED')
 def test_brake_not_glass(self):
  d=json.loads((PORT/'docs/vehicle-model-port1/ps2-format-lights/lights-contract.json').read_text());x=next(x for x in d['families'] if x['family']=='XTRAIL');self.assertEqual([r['final_mode'] for r in x['light_meshes']],[1,14]);self.assertEqual([r['source_faces'] for r in x['light_meshes']],[6,22]);self.assertTrue(all(r['selector']==2 for r in x['light_meshes']))
if __name__=='__main__':unittest.main()
