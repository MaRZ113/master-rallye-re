import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parent
class SourceEvidence(unittest.TestCase):
 def test_glow_fade_is_rgb_not_alpha(self):
  a=json.loads((ROOT/'glow-source/source-audit.json').read_text())
  p=a['ps2_texture']; c=a['pc_texture']
  self.assertEqual((p['width'],p['height'],p['size']),(16,16,1032))
  self.assertEqual((p['alpha_min'],p['alpha_max']),(0,0))
  self.assertEqual(p['stats']['first_last_pixels'],[[0,0,0,0],[0,0,0,0]])
  self.assertGreater(p['stats']['rgb_nonzero_when_alpha_zero'],0)
  self.assertEqual(c['stats']['ranges'][0],[255,255])
  self.assertEqual(c['stats']['ranges'][3],[0,249])
 def test_geometry_uv_match(self):
  a=json.loads((ROOT/'glow-source/source-audit.json').read_text())
  self.assertEqual(a['max_uv_error'],0)
  self.assertLessEqual(a['max_normal_error'],1.2e-7)
 def test_damage_key_is_unique_family_not_runtime_confirmation(self):
  a=json.loads((ROOT/'damage-source.json').read_text())
  self.assertEqual({r['path'].split('\\')[0] for r in a['negative_search_78_files']},{'Terrano'})
  self.assertEqual((a['vertices'],a['triangles']),(330,324))
  self.assertEqual(a['runtime'],'PENDING_NEW_UPLOAD_KEY_CONFIRMATION')
if __name__=='__main__':unittest.main()
