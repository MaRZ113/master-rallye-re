"""Hash-locked original PS2 Kia ON asset. No game files are changed."""
from pathlib import Path
import importlib.util,json,struct,hashlib
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[1]
def main():
 spec=importlib.util.spec_from_file_location('kia_color_source',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
 pack,_=a.t.load_pak(a.PS2/'TNG.PAK');entry=next(e for e in pack['entries'] if e.get('path','').upper().endswith('KIASPORTAGE\\CAR.PSM'));raw,_=a.t.read_payload(entry,a.PS2/'TNG.000')
 assert a.sha(raw)=='b4afabfab7437eae01ee72ca424beb90967c7b849cebdb9cf94e104560be33ce'
 scene=a.r.decode_vehicle(raw);results=[]
 for mesh in scene.meshes:
  if mesh['path'] not in ('root.25.1.0','root.25.1.1'):continue
  row={k:mesh[k] for k in ('path','material','textures')};row['rgba_words']=sorted({struct.unpack_from('<I',raw,32+i*52+16)[0] for s in mesh['strips'] for i in range(s['start'],s['start']+s['count'])});row['resources']=[]
  for tx in mesh['textures']:
   key=a.t.logical_path('\\TNG\\DATAPSM\\'+tx['name']+'.GXI').upper();e=next((e for e in pack['entries'] if e.get('path','').upper()==key),None)
   if not e:raise ValueError('Missing original source texture')
   data,_=a.t.read_payload(e,a.PS2/'TNG.000');colors=list(struct.iter_unpack('4B',data[8:]));row['resources'].append({'path':e['path'],'sha256':a.sha(data),'bytes':len(data),'channel_ranges':[(min(c[i] for c in colors),max(c[i] for c in colors)) for i in range(4)],'center':colors[len(colors)//2]});(PORT/'.assets/vehicles'/('KIA-'+key.split('\\')[-1])).write_bytes(data)
  results.append(row)
 assert results[0]['resources'][0]['sha256']=='fd4c121f962ef4e9ee7491666c71b65db008d6ca276d9188881c0b35c7846131'
 (HERE/'ps2-color-source.json').write_text(json.dumps(results,indent=2)+'\n');print('Kia PS2 ON RGB/alpha and glow resources verified')
if __name__=='__main__':main()
