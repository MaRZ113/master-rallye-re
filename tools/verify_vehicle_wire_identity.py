"""Verify paired native identity fields and optional standalone ghost headers.

Hashes record provenance; exact mapped instruction bytes verify the reference sites.
No game process or installed file is modified.
"""
import argparse,hashlib,json,struct
from pathlib import Path

SHA='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
def read_u32(raw,offset):return struct.unpack_from('<I',raw,offset)[0]
def va_offset(raw,va):
 pe=read_u32(raw,0x3c);sections=struct.unpack_from('<H',raw,pe+6)[0];optional=struct.unpack_from('<H',raw,pe+20)[0]
 image_base=read_u32(raw,pe+24+28);table=pe+24+optional
 for i in range(sections):
  p=table+40*i;size,rva,rawsize,off=struct.unpack_from('<IIII',raw,p+8)
  if rva<=va-image_base<rva+rawsize:return off+va-image_base-rva
 raise ValueError(hex(va))
def inspect(exe,ghosts):
 raw=exe.read_bytes();actual_sha=hashlib.sha256(raw).hexdigest()
 expected={0x481c68:'e8b3010000',0x481c6d:'50',0x481c75:'e8c6bb0200',0x481c7a:'e8814afbff',0x43440f:'e8ac950700',0x434414:'894530',0x434450:'8a4530',0x434453:'884605',0x433f9f:'33d2',0x433fa5:'8a5605',0x433fae:'89542428',0x43415a:'8b4c2428',0x434161:'898804080000',0x4ad9c1:'685c576e00',0x4ad9db:'e8808d0200',0x4bcc90:'6a04',0x4bcc99:'e862700100',0x4bccb3:'e848700100',0x4bcf25:'6a04',0x4bcf2a:'e8816e0100',0x4bcf51:'e82a27f5ff'}
 verified=[]
 for va,h in expected.items():
  off=va_offset(raw,va);found=raw[off:off+len(bytes.fromhex(h))].hex()
  if found!=h:raise ValueError('Original wire instruction differs at '+hex(va)+': '+found)
  verified.append({'va':f'{va:08X}','file_offset':off,'bytes':h})
 samples=[]
 for p in sorted(ghosts.glob('*.ghost')):
  g=p.read_bytes();magic,ver,size=struct.unpack_from('<III',g)
  if (magic,ver)!=(0xab59d02e,3) or size!=len(g)-12:raise ValueError('Unsupported ghost header: '+p.name)
  o=17+4*g[16];n=read_u32(g,o);o+=4;family=g[o:o+n].decode('latin1');o+=n;n=read_u32(g,o);o+=4;race=g[o:o+n].decode('latin1');o+=n
  samples.append({'file':p.name,'sha256':hashlib.sha256(g).hexdigest(),'bytes':len(g),'family':family,'race':race,'post_string_u32':list(struct.unpack_from('<8I',g,o))})
 return {'source_sha256':actual_sha,'reference_sha256':SHA,'reference_identity_matches':actual_sha==SHA,'verified_original_instructions':verified,'network':{'selectedCar_packet_offset':5,'width_bits':8,'receiver_signed':False,'representable_values':[0,255],'global_engine_maximum_established':False},'ghost_v3_samples':samples,'limits':'Static paired network selectedCar field and ghost header inspection only; no network/gameplay/file-writer execution.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,required=True);p.add_argument('--ghosts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=inspect(a.exe,a.ghosts);a.output.write_text(json.dumps(r,indent=2)+'\n');print('PASS_ORIGINAL_WIRE_HEADER_EVIDENCE')
