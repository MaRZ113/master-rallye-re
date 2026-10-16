"""Ghidra-EER / Rabbitizer original byte audit, fixed registry and mode21 case."""
from pathlib import Path
import hashlib,json,struct,re,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'ps2-research/revalidation2/tools'))
import verify_r5900_revalidation2 as v
import rabbitizer
SHA='b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2'
def main():
 b=Path('D:/Game/Master Rallye PS2/SLES_509.06').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
 elf=v.parse_elf32_le(b)
 def off(a):return v.va_to_offset(a,4,elf['load_segments'])
 def word(a):return struct.unpack_from('<I',b,off(a))[0]
 raw=(ROOT/'ps2-research/data/revalidation2/frontend-continuity2.txt').read_text();checked=0
 for m in re.finditer(r'^INS\t([0-9a-f]+)\t([0-9a-f]+)\t',raw,re.M):
  a=int(m[1],16);assert b[off(a):off(a)+4]==bytes.fromhex(m[2]);assert rabbitizer.Instruction(word(a),a,rabbitizer.InstrCategory.R5900).isValid();checked+=1
 refs=[int(x,16) for x in re.findall(r'^REF\t3ada88\t([0-9a-f]+)\tUNCONDITIONAL_CALL$',raw,re.M)]
 constructors=[]
 for a in refs:
  w1,w2=word(a-24),word(a-20);assert w1==0x3c050048 and w2>>16==0x24a5
  lo=w2&65535;lo=lo-65536 if lo&32768 else lo;address=0x480000+lo
  name=b[off(address):off(address)+100].split(b'\0')[0].decode('ascii');constructors.append({'base_constructor_call':hex(a),'literal_va':hex(address),'name':name})
 assert len(constructors)==29 and not {'crashiny','carbrakelight','carbrakelights'}&{r['name'] for r in constructors}
 rows=[]
 for begin,end in ((0x314b30,0x314e28),(0x315114,0x3151d0),(0x3151d0,0x315580),(0x3ae150,0x3ae250),(0x391774,0x3918b8),(0x3a6e14,0x3a6e78)):
  for a in range(begin,end,4):
   ins=rabbitizer.Instruction(word(a),a,rabbitizer.InstrCategory.R5900);assert ins.isValid();rows.append({'va':hex(a),'offset':off(a),'word':hex(word(a)),'r5900':str(ins)})
 assert word(0x4850c0+21*4)==0x3151d0
 assert word(0x4850c0+5*4)==0x314b30
 result={'elf_sha256':SHA,'ghidra_processor':'r5900:LE:32:default','ghidra_export_sha256':hashlib.sha256(raw.encode()).hexdigest(),'independent_ghidra_words_checked':checked,'registry_constructor_names':constructors,'mode21_jump':{'table':'0x4850c0','index':21,'target':'0x3151d0'},'instructions':rows,'boundary':'Static fixed original registry; no injected modules or live PS2 pixel equivalence asserted.'}
 (HERE/'original-material-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'checked':checked,'constructors':len(constructors),'mode21case_words':(0x315580-0x3151d0)//4}))
if __name__=='__main__':main()
