"""Focused source contract checks; no rendering/runtime claims."""
from pathlib import Path
import hashlib,json,struct,unittest,importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('car',HERE/'convert_car.py');car=importlib.util.module_from_spec(spec);spec.loader.exec_module(car)
class AssetContract(unittest.TestCase):
 def test_independent_source(self):
  m=json.loads((HERE/'conversion-evidence.json').read_text());self.assertEqual(m['source_sha256'],car.SOURCE);self.assertNotEqual(car.SOURCE,car.c.XTRAIL_SHA)
 def test_unconditional_selection(self):
  m=json.loads((HERE/'conversion-evidence.json').read_text());self.assertEqual([r['path'] for r in m['meshes']],['root.'+str(i) for i in range(20)]);self.assertEqual(len(m['excluded_conditional_meshes']),11)
 def test_wheels_not_chassis(self):
  m=json.loads((HERE/'wheel-inventory.json').read_text());self.assertEqual(m['vertices'],300);self.assertEqual(sum(r['faces'] for r in m['meshes']),252);self.assertEqual(m['trailer']['tag'],102);self.assertFalse(m['extra_nodes'])
 def test_default_original_texture(self):
  m=json.loads((HERE/'conversion-evidence.json').read_text());a=m['meshes'][18];self.assertEqual(a['mode'],0);self.assertEqual(m['texture_upload'][a['texture_indices'][0]]['sha256'],car.c.DEFAULT_SHA)
 def test_private_reproducibility(self):
  original=Path('D:/Game/Master Rallye PS2/TNG.PAK')
  if not original.exists():self.skipTest('Canonical original inputs unavailable')
  data,meta=car.convert(original.parent);self.assertEqual(hashlib.sha256(data).hexdigest(),'a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac');self.assertEqual(meta['faces'],1980)
if __name__=='__main__':unittest.main()
