"""Bounded same-session evidence replay; generated raw bytes stay ignored."""
from pathlib import Path
import json,struct,hashlib
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[1]
LOGS=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs')
def sha(b):return hashlib.sha256(b).hexdigest()
def decode(d):
 vb=bytes.fromhex(d['vertex_hex']);ib=bytes.fromhex(d['index_hex'])
 if d['fvf']!=0x102 or d['stride']!=20 or len(vb)!=640 or len(ib)!=192:raise ValueError('unsupported bounded glow layout')
 points=list(struct.iter_unpack('<5f',vb));indices=[x[0]-d['min'] for x in struct.iter_unpack('<H',ib)]
 if any(x<0 or x>=32 for x in indices):raise ValueError('index out of source range')
 return vb,ib,sha(b''.join(struct.pack('<2f',*p[3:]) for p in points)+struct.pack('<96I',*indices))
def main():
 rows=[]
 for frame in (1226,2800):
  f=LOGS/f'race-fleet-9516-d1-f{frame}.jsonl';expected='cff245814a8ea15e8aa080f5c5d851ef98c1d4ef3a2291a72e2b395514d81b62' if frame==1226 else '80e7cbaecb5205a65809c3372db71f8b3f9746d22eae9ec565eea14f61c5b017'
  assert sha(f.read_bytes())==expected
  d=next(d for d in map(json.loads,f.read_text().splitlines()) if d['type']=='kia_glow_source_capture');vb,ib,signature=decode(d)
  assert d['owner_verified'] and signature=='4a075be51521d4e13fceefe349870b474996abfb90ea3a3b957b449b755c1c43'
  binary=struct.pack('<4I',d['fvf'],d['stride'],d['min'],d['format'])+vb+ib
  (PORT/'.assets/vehicles'/f'kia-glow-{frame}.bin').write_bytes(binary)
  rows.append({'frame':frame,'fixture_sha256':sha(binary),'source_sidecar_sha256':expected,'normalized_uv_indices':signature,'owner_verified':True,'private_tree':d['private_tree']})
 (HERE/'replay-manifest.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
if __name__=='__main__':main()
