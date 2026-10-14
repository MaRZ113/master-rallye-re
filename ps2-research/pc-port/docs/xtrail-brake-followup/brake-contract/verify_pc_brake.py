from pathlib import Path
import hashlib,json,re,struct
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
p=Path('D:/Game/Master Rallye Pristine/MRallye.exe');b=p.read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha=='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
pe=struct.unpack_from('<I',b,60)[0];num=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0];base=struct.unpack_from('<I',b,pe+52)[0]
sections=[struct.unpack_from('<4I',b,pe+24+opt+i*40+8) for i in range(num)]
def offset(va,n):
 rva=va-base
 for vs,sv,sz,fo in sections:
  if sv<=rva and rva+n<=sv+sz:return fo+rva-sv
 raise ValueError('VA not original raw bytes')
raw=(ROOT/'ps2-research/data/xtrail-brake-next/pc-update.txt').read_text();rows=[]
for m in re.finditer(r'^INS\t([0-9a-f]+)\t([0-9a-f]+)\t([^\r\n]+)',raw,re.M):
 va=int(m[1],16);bs=bytes.fromhex(m[2]);o=offset(va,len(bs));assert b[o:o+len(bs)]==bs;rows.append({'va':hex(va),'file_offset':o,'bytes':bs.hex(),'ghidra_x86':m[3]})
threshold_va=0x68f974;t=struct.unpack_from('<I',b,offset(threshold_va,4))[0];assert t==0x3dcccccd
vtable=[{'va':hex(0x691488+i*4),'value':hex(struct.unpack_from('<I',b,offset(0x691488+i*4,4))[0])} for i in range(6)]
rea=json.loads((HERE/'pc-rea-evidence.json').read_text());assert all(q['subject_sha256']==sha for q in rea['queries'])
for q in rea['queries']:
 for line in q['assembly']:
  assert re.match(r'^0x[0-9a-f]+:',line)
x={'schema_version':1,'evidence_grade':'CONFIRMED_BY_EXE','canonical_pc_sha256':sha,'image_base':hex(base),'class_string':{'va':'0x6e7350','value':'gaSFXBrakeLights','constructor':'0x4ca040','vtable':'0x691488','vtable_words':vtable},'init':'0x4ca110 stores Egg+50->+18 model into AI+18; blight lookup ->AI+14;Controller/<EggName> key','update':{'bounds':'0x4ca1d0..0x4ca23e','broker_calls':['0x4d8ec0','0x4d6fb0'],'field':'result+8 pointer -> float32+24','threshold_va':hex(threshold_va),'threshold_word':hex(t),'rule':'ordered source >float32(.1): selector2;otherwise1;unord also1','writer':'0x4d3c50','writer_bounds':'index>=0 &&index<model+20 count &&value>=0 &&value<=max array model+14[index]','writer_destination':'model+4 values[index]','engine_owned_state':True},'update_original_byte_windows':rows,'limitations':['REA default Ghidra analysis omitted update entry: explicit invalid_request at0x4ca1d0','Fallback imports original PC x86 inignored scratch and disassembles only exact vtable update target','Function execution/livecurrentmodel/native lamp draw identity remains NOT_PERFORMED','No port Broker reads or controller hooking authorized bystaticproof alone'],'safe_next_route':'Use original PC blight on/glow conditional emission; match original compiledgeometry+UV/currentnative generations; never invent statefrombrake keypress'}
(HERE/'pc-brake-contract.json').write_text(json.dumps(x,indent=2)+'\n');print('PC original update instructions verified',len(rows))
