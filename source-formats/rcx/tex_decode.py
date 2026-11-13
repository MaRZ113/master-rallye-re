"""Bounded reader for the observed RCX TEX version 1 variants."""
import argparse,hashlib,json,struct
from pathlib import Path
from PIL import Image
MAGIC=0x0da7adde
FORMATS={21:'A8R8G8B8',22:'X8R8G8B8',0x31545844:'DXT1',0x33545844:'DXT3'}
def decode(data):
 if len(data)<24:raise ValueError('truncated TEX header')
 magic,version,w,h,fmt,levels=struct.unpack_from('<6I',data)
 if magic!=MAGIC or version!=1 or fmt not in FORMATS:raise ValueError('unsupported TEX')
 if not (1<=w<=4096 and 1<=h<=4096 and 1<=levels<=1+max(w,h).bit_length()-1):raise ValueError('invalid texture dimensions or mip count')
 width,height=w,h;pos=24;mips=[]
 for level in range(levels):
  size=width*height*4 if fmt in (21,22) else max(1,(width+3)//4)*max(1,(height+3)//4)*(8 if fmt==0x31545844 else 16)
  if pos+size>len(data):raise ValueError('truncated mip')
  raw=data[pos:pos+size]
  if fmt in (21,22):
   rgba=bytearray(Image.frombytes('RGBA',(width,height),raw,'raw','BGRA').tobytes())
   if fmt==22:rgba[3::4]=b'\xff'*(width*height)
   rgba=bytes(rgba)
  else:rgba=Image.frombytes('RGBA',(width,height),raw,'bcn',(1,'DXT1') if fmt==0x31545844 else (2,'DXT3')).tobytes()
  mips.append({'width':width,'height':height,'offset':pos,'size':size,'rgba':rgba});pos+=size;width=max(1,width//2);height=max(1,height//2)
 if pos!=len(data):raise ValueError('unexpected trailing texture bytes')
 return {'width':w,'height':h,'format':FORMATS[fmt],'format_raw':fmt,'mip_count':levels,'mips':mips}
def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('png',type=Path);a=p.parse_args()
 output=a.png.resolve();root=Path(__file__).resolve().parent
 if output==root or not output.is_relative_to(root):raise ValueError('output outside research directory')
 d=decode(a.source.read_bytes());m=d['mips'][0];Image.frombytes('RGBA',(d['width'],d['height']),m['rgba']).save(output)
 print(json.dumps({'format':d['format'],'width':d['width'],'height':d['height'],'mip_count':d['mip_count'],'rgba_sha256':hashlib.sha256(m['rgba']).hexdigest()}))
if __name__=='__main__':main()
