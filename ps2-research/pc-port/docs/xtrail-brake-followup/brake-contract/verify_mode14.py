from pathlib import Path
import hashlib,json,re,struct,importlib.util
import rabbitizer
ROOT=Path(__file__).resolve().parents[5]
spec=importlib.util.spec_from_file_location('ev',ROOT/'ps2-research/revalidation2/tools/verify_r5900_revalidation2.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
b=Path('D:/Game/Master Rallye PS2/SLES_509.06').read_bytes();assert hashlib.sha256(b).hexdigest()==ev.EXPECTED_ELF_SHA256
elf=ev.parse_elf32_le(b); raw=(ROOT/'ps2-research/data/xtrail-brake-next/mode-probe.txt').read_text();assert 'LANGUAGE\tr5900:LE:32:default' in raw
important={0x3126b8,0x3126c8,0x3126d0,0x3126d8,0x3126dc,0x313010,0x313044,0x3130ec,0x313114,0x313160,0x3131a0,0x313224,0x31322c,0x313248,0x31324c,0x313250,0x313254,0x313258,0x313260,0x313264,0x313268,0x31326c}
rows=[];checked=0
for m in re.finditer(r'^INS\t([0-9a-f]+)\t([0-9a-f]+)\t([^\r\n]+)',raw,re.M):
 va=int(m[1],16);o=ev.va_to_offset(va,4,elf['load_segments']);bs=bytes.fromhex(m[2]);assert b[o:o+4]==bs;checked+=1
 if va in important:rows.append({'va':hex(va),'file_offset':o,'bytes':bs.hex(),'word':hex(struct.unpack('<I',bs)[0]),'ghidra':m[3],'rabbitizer':rabbitizer.Instruction(struct.unpack('<I',bs)[0],va,rabbitizer.InstrCategory.R5900).disassemble()})
table=[]
for mode in (0,1,14):
 va=0x4850c0+mode*4;o=ev.va_to_offset(va,4,elf['load_segments']);table.append({'mode':mode,'table_va':hex(va),'file_offset':o,'original_word':hex(struct.unpack_from('<I',b,o)[0])})
x={'schema_version':1,'evidence_grade':'CONFIRMED_BY_EXE','canonical_elf_sha256':hashlib.sha256(b).hexdigest(),'ghidra_language':'r5900:LE:32:default','rabbitizer_category':'R5900','original_instruction_words_verified':checked,'function':'0x312610..0x316803','dispatch_table':table,'mode14':{'case_entry':'0x31300c','PRIM_forced':'0x5c = TRIANGLE_STRIP4,IIP1,TME1,ABE1,FGE0;AA1/FST/CTXT/FIX inherited','ALPHA':'low=0x29,FIX=128; A=Cd,B=0,C=FIX,D=Cs; Cout=Cd+Cs','ALPHA_mask':'FIX byte at0x42df04=0x80;lowbyte=0x29;unrelated bits preserved','TEX0':'TCC1 RGBA;TFX1 DECAL; descriptor fields inherited fromtexture setup','TEX1':'old & 0xfffff000ffe7fe1e | 0x120; LCM0,MMAG1,MMIN4,L0,K0; MXL and MTBA inherited','TEST':'old & 0xfffffffffff9c000 | 0x41000;ATE0,ZTST2 GEQUAL,ZTE/DATE inherited','ZBUF':'old & 0xfffffffeffffffff | 0x100000000;ZMSK1,format/base inherited','passes':'one primary geometry state setup; no mode14 secondary-environment activation inthiscase'},'important_original_instructions':rows,'limitations':['Static executable contract, notliveGS capture','Mode14 alpha does notscale colorblend;textureDECALalpha maystillfeed outputalpha','Exact PC live lamp owner/draw join notproven','PS2 andPC depth conventions cannotbe equated','Original authored glow mesh, notsynthetic screen halo']}
Path(__file__).with_name('mode14-gs-evidence.json').write_text(json.dumps(x,indent=2)+'\n');print(checked,len(rows),table)



