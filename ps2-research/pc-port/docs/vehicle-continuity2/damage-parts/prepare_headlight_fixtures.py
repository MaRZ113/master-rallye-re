"""Recreate the bounded local native replay; raw buffers remain ignored."""
from pathlib import Path
import json,struct,hashlib
HERE=Path(__file__).resolve().parent;PORT=HERE.parents[2]
def main():
 logs=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs');evidence=json.loads((HERE/'headlight-damage-evidence.json').read_text())['headlight'];out=bytearray(b'HEADL001'+struct.pack('<I',3))
 for item in evidence[:3]:
  raw=(logs/item['file']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=item['file_sha256']:raise ValueError('Capture drift '+item['file'])
  rows=[json.loads(x) for x in raw.splitlines()];r=next(x for x in rows if x.get('vertices')==22 and x.get('triangles')==18 and 'vertex_hex' in x);vb=bytes.fromhex(r['vertex_hex']);ib=bytes.fromhex(r['index_hex']);out+=struct.pack('<10I',r['fvf'],r['stride'],r['min'],r['vertices'],r['triangles'],r['index_format'],r['base'],len(vb),len(ib),r['private_tree'])+vb+ib
 target=PORT/'.assets/vehicles/headlight-damage-fixtures.bin';target.write_bytes(out);print(hashlib.sha256(out).hexdigest())
if __name__=='__main__':main()
