"""Cross-check bounded EER exports with explicit Rabbitizer R5900 decoding."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import rabbitizer

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
spec=importlib.util.spec_from_file_location('canonical_elf_verifier',ROOT/'ps2-research/revalidation2/tools/verify_r5900_revalidation2.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def main():
    b=Path('D:/Game/Master Rallye PS2/SLES_509.06').read_bytes()
    digest=hashlib.sha256(b).hexdigest()
    if digest!=v.EXPECTED_ELF_SHA256:raise ValueError('Canonical ELF mismatch')
    elf=v.parse_elf32_le(b)
    raw=(ROOT/'ps2-research/data/vehicle-model-port1/vehicle-format-probe.txt').read_text()
    if 'LANGUAGE\tr5900:LE:32:default' not in raw:raise ValueError('Wrong EER language')
    # Compact windows expose dispatch, reads, write ownership and child wrapper.
    ranges=[(0x38fe68,0x38fe70),(0x38ff18,0x38ff28),(0x38ff88,0x38ff8c),
        (0x3947d0,0x394828),(0x39482c,0x394868),(0x394870,0x3948d4),
        (0x3a5c6c,0x3a5c74),(0x3a5c9c,0x3a5ca4),
        (0x2444e0,0x244508),(0x392728,0x392778),(0x392814,0x392858),
        (0x1a0824,0x1a0858),(0x1a08d4,0x1a094c),(0x1d77a0,0x1d77f0)]
    checked=0;rows=[]
    for m in re.finditer(r'^INS\t([0-9a-f]+)\t([0-9a-f]+)\t([^\r\n]+)',raw,re.M):
        va=int(m[1],16);data=bytes.fromhex(m[2]);o=v.va_to_offset(va,4,elf['load_segments'])
        if b[o:o+4]!=data:raise ValueError('Original instruction mismatch '+hex(va))
        word=struct.unpack('<I',data)[0]
        instr=rabbitizer.Instruction(word,va,rabbitizer.InstrCategory.R5900)
        checked+=1
        if any(lo<=va<=hi for lo,hi in ranges):rows.append({'va':hex(va),'file_offset':o,
            'bytes_hex':data.hex(),'word':hex(word),'ghidra':m[3],'rabbitizer':instr.disassemble()})
    strings={}
    for va in (0x4879c0,0x4879c8,0x487a18,0x472498,0x4724b0,0x4724b8,0x479ff8,0x47a000):
        o=v.va_to_offset(va,1,elf['load_segments'])
        strings[hex(va)]=b[o:b.index(b'\0',o)].decode('ascii')
    roles={0x38fac0:'Top-level PSM records;102 ->3947b0;continue tag loop',
        0x3900f0:'539 visual source vertices;calls391d38 once root',
        0x391d38:'Recursive visual tags;7 named child registry and8 selector wrapper',
        0x3946e0:'101 convex auxiliary;reject wheel model names',
        0x3947b0:'102 two-float cylinder auxiliary;assign model+38 only for wheel',
        0x2444e0:'74-byte cylinder object constructor;default+14=.4,+18=.2',
        0x3a5c60:'a0 cylinder,+14=f12',0x3a5c90:'a0 cylinder,+18=f12',
        0x1a07e0:'blight named child lookup;retains model and lookup index',
        0x1a08c0:'Controller/<EggName> source+8->+24 >.1 selects blight2 else1',
        0x1a0960:'gaSFXCoordinator constructor;negative neighboring-class control',
        0x1d76d0:'Resolve named current-model option index through native virtual+24',
        0x1d77a0:'Bounds-checked current-model option array write',
        0x26c1b0:'Source geometry/color helper;blight token references not proven brake switch'}
    funcs=[{'entry':hex(int(m[1],16)),'end_inclusive':hex(int(m[2],16)),
        'role':roles[int(m[1],16)],'bounds_provenance':'Existing EER database;alloriginalinstructionbyteschecked'}
        for m in re.finditer(r'^FUNCTION ([0-9a-f]+)\.\.([0-9a-f]+)',raw,re.M)]
    old=json.loads((ROOT/'ps2-research/pc-port/docs/coverage-followup/body-lights/r5900-byte-evidence.json').read_text())
    lamp_rows=[]
    for row in old['instruction_samples']:
        va=int(row['va'],16)
        if 0x391c24<=va<=0x391cec:
            o=v.va_to_offset(va,4,elf['load_segments']);word=struct.unpack_from('<I',b,o)[0]
            if word!=int(row['word'],16):raise ValueError('Frozenlampwordchanged')
            lamp_rows.append({'va':hex(va),'word':hex(word),'bytes_hex':b[o:o+4].hex(),
                'rabbitizer':rabbitizer.Instruction(word,va,rabbitizer.InstrCategory.R5900).disassemble()})
    out={'schema_version':1,'elf_sha256':digest,'elf_size':len(b),
        'ghidra_language':'r5900:LE:32:default','decoder':'Rabbitizer InstrCategory.R5900',
        'evidence_grade':'CONFIRMED_BY_EXE','word_correspondence_checked':checked,
        'instructions':rows,'functions':funcs,'strings':strings,
        'lamp_original_words_rechecked':lamp_rows,
        'raw_export':'IGNORED_LOCAL_data/vehicle-model-port1/vehicle-format-probe.txt',
        'limitations':['No live model selection or GS capture','Cylinder physical semantics notportedinthisphase',
            'EER pseudocode may reorder MIPS float argument declarations;actuala0/f12assemblyprevails']}
    (HERE/'r5900-format-evidence.json').write_text(json.dumps(out,indent=2)+'\n')
    print('checked original R5900 words',checked,'compact probes',len(rows),'lamp probes',len(lamp_rows))


if __name__=='__main__':main()
