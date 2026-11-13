"""Bounded static QTO v7 inspection and OBJ export. Material/draw semantics remain provisional."""
import argparse, json, math, struct
from pathlib import Path

def parse(path):
 b=path.read_bytes()
 if len(b)<32:raise ValueError('short header')
 ver,sub,ng,nt,nv,ni,na,unknown=struct.unpack_from('<8I',b)
 if (ver,sub)!=(7,2) or ng>1000 or nt>1000 or nv>65535 or ni>10000000:raise ValueError('unsupported header')
 off=32+ng*57
 if off>len(b):raise ValueError('group table out of bounds')
 groups=[]
 for i in range(ng):
  p=32+i*57; draw_id,texture_index,unknown2,material_flags=struct.unpack_from('<4I',b,p); start,count,ntri=struct.unpack_from('<III',b,p+17); end=start+count
  if nt and texture_index>=nt: raise ValueError('texture index outside texture table')
  if start>end or end>ni or start%3 or end%3 or ntri*3!=end-start:raise ValueError('invalid draw index range')
  groups.append({'start':start,'end':end,'triangles':ntri,'draw_id':draw_id,'texture_index':texture_index if nt else None,'unknown_word_2':unknown2,'material_flags_raw':material_flags,'raw_hex':b[p:p+57].hex()})
 intervals=sorted((g['start'],g['end']) for g in groups)
 cursor=0
 for start,end in intervals:
  if start!=cursor:raise ValueError('draw ranges overlap or leave a gap')
  cursor=end
 if cursor!=ni:raise ValueError('draw ranges do not cover index buffer')
 names=[]
 for _ in range(nt):
  end=b.find(b'\0',off)
  if end<0:raise ValueError('unterminated name')
  names.append(b[off:end].decode('ascii'));off=end+1
 if off+nv*64+ni*2+na*2!=len(b):raise ValueError('unexpected array layout')
 verts=[]
 for i in range(nv):
  at=off+i*64; pos=struct.unpack_from('<3f',b,at);normal=struct.unpack_from('<3f',b,at+28);uv=struct.unpack_from('<2f',b,at+48)
  if not all(math.isfinite(x) for x in (*pos,*normal,*uv)):raise ValueError('non-finite vertex')
  verts.append((pos,normal,uv))
 idx=struct.unpack_from(f'<{ni}H',b,off+nv*64)
 if idx and max(idx)>=nv:raise ValueError('index outside vertex buffer')
 return {'version':[ver,sub],'groups':groups,'textures':names,'vertex_count':nv,'index_count':ni,'aux_u16_count':na,'vertex_offset':off,'vertices':verts,'indices':idx}

def main():
 a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('--obj',type=Path);args=a.parse_args();d=parse(args.source)
 print(json.dumps({k:v for k,v in d.items() if k not in ('vertices','indices')},indent=2))
 if args.obj:
  with args.obj.open('w',encoding='utf8',newline='\n') as out:
   out.write('# Provisional raw QTO coordinates; material and runtime parity unverified\n')
   for p,n,uv in d['vertices']:out.write('v %.9g %.9g %.9g\n'%p)
   for p,n,uv in d['vertices']:out.write('vt %.9g %.9g\n'%uv)
   for p,n,uv in d['vertices']:out.write('vn %.9g %.9g %.9g\n'%n)
   for i,g in enumerate(d['groups']):
    out.write(f'g draw_{i}\n')
    for j in range(g['start'],g['end'],3):
     t=[x+1 for x in d['indices'][j:j+3]];out.write('f '+' '.join(f'{k}/{k}/{k}' for k in t)+'\n')
if __name__=='__main__':main()
