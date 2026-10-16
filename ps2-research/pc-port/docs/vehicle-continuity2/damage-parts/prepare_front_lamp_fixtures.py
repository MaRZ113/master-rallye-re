from pathlib import Path
import json,struct,hashlib
HERE=Path(__file__).resolve().parent;PORT=HERE.parents[2]
def main():
 logs=Path('D:/Game/Master Rallye Pristine/MRRRenderer/logs');out=bytearray(b'FRONT001'+struct.pack('<I',4));manifest=[]
 for frame in (3221,10314):
  file=logs/('race-damage-13624-d1-f%d.jsonl'%frame);raw=file.read_bytes();rows=[json.loads(x) for x in raw.splitlines()];manifest.append({'file':file.name,'sha256':hashlib.sha256(raw).hexdigest()})
  for part,n,f in ((1,30,28),(2,18,14)):
   r=next(x for x in rows if x.get('vertices')==n and x.get('triangles')==f and x.get('owner_context') and 'vertex_hex'in x);vb=bytes.fromhex(r['vertex_hex']);ib=bytes.fromhex(r['index_hex']);out+=struct.pack('<11I',part,r['fvf'],r['stride'],r['min'],r['vertices'],r['triangles'],r['index_format'],r['base'],len(vb),len(ib),r['private_tree'])+vb+ib
 target=PORT/'.assets/vehicles/front-lamp-damage-fixtures.bin';target.write_bytes(out);(HERE/'front-lamp-fixture-manifest.json').write_text(json.dumps({'captures':manifest,'fixture_sha256':hashlib.sha256(out).hexdigest()},indent=2)+'\n')
 print(hashlib.sha256(out).hexdigest())
if __name__=='__main__':main()
