import json,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
class Evidence(unittest.TestCase):
 def test_current_textureless_layout(self):
  j=json.loads((HERE/'icecream-current-proof.json').read_text());self.assertEqual((j['fvf'],j['stream0']['stride'],j['source_record']),(0x42,16,3));self.assertEqual(j['hresult'],0);self.assertEqual(j['earlier_seen_mask']^(2**23-1),1<<3)
 def test_original_callback_words(self):
  j=json.loads((HERE/'material-original-words.json').read_text());r={int(x['va'],16):int(x['word'],16) for x in j['instructions']}
  for a,w in ((0x39177c,0x1060005f),(0x3ade84,0xae220028),(0x3ae000,0xac640028),(0x3ae008,0xac64002c),(0x371648,0xae0200dc)):self.assertEqual(r[a],w)
 def test_modes_and_primary(self):
  rows=json.loads((HERE/'seven-material-gaps.json').read_text());r=[x for x in rows if x['family'] in ('TATA','KIASPORTAGE')];self.assertEqual(len(r),2)
  for x in r:self.assertEqual(x['mode'],3);self.assertEqual([s['slot'] for s in x['texture_slots']],[1])
if __name__=='__main__':unittest.main()
