"""Read-only exact R5900 proof for bounded COMPLETE fixes; uses installed Rabbitizer."""
import hashlib,json,pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'ps2-research/revalidation2/tools'))
import verify_r5900_revalidation2 as v
import rabbitizer
SHA='b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2'
RANGES=((0x3916d0,0x391750),(0x391774,0x3918fc),(0x3ade58,0x3ae040),(0x3715b0,0x371654),(0x3a6c58,0x3a6eb0))
def main():
 b=pathlib.Path('D:/Game/Master Rallye PS2/SLES_509.06').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
 elf=v.parse_elf32_le(b);rows=[]
 for start,end in RANGES:
  for a in range(start,end,4):
   off=v.va_to_offset(a,4,elf['load_segments']);w=struct.unpack_from('<I',b,off)[0];i=rabbitizer.Instruction(w,a,rabbitizer.InstrCategory.R5900);assert i.isValid()
   rows.append({'va':hex(a),'offset':off,'word':hex(w),'r5900':str(i)})
 report={'elf_sha256':SHA,'architecture':'r5900:LE:32:default / Rabbitizer InstrCategory.R5900','instructions':rows,'evidence_boundary':'Original instruction words; no new live PS2 render claim.'}
 pathlib.Path(__file__).with_name('material-original-words.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
