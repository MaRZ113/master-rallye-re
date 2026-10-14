"""Independent canonical R5900 words, bounded material-default evidence."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import rabbitizer

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
spec=importlib.util.spec_from_file_location('elf_checks',ROOT/'ps2-research/revalidation2/tools/verify_r5900_revalidation2.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def main():
    data=Path('D:/Game/Master Rallye PS2/SLES_509.06').read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if digest!=v.EXPECTED_ELF_SHA256:raise ValueError('Wrong ELF')
    elf=v.parse_elf32_le(data)
    def offset(va):
        seg=[s for s in elf['load_segments'] if s['virtual_address']<=va< s['virtual_address']+s['file_size']]
        if len(seg)!=1:raise ValueError('Ambiguous ELF address')
        return seg[0]['file_offset']+va-seg[0]['virtual_address']
    text=(ROOT/'ps2-research/data/revalidation2/body-material-probe.txt').read_text()
    rows=[];checked=0
    selected={0x390cb0,0x390cb4,0x390cc8,0x39177c,0x391788,0x39178c,
              0x3917c0,0x3917c4,0x3917cc,0x3917d4,0x3917e0,0x3917e4,
              0x391808,0x391814,0x391818,0x391868,0x39186c,0x391870,
              0x39187c,0x391880,0x391894,0x391898,0x3918a8,
              0x391b68,0x391bc0,0x391be8,0x391c0c,0x391c58,0x391c74,
              0x3a6e10,0x3a6e18,0x3a6e24,0x3a6e2c,0x3a6e38,
              0x3ade7c,0x3ade80,0x3ade84,0x3ade88,0x3adebc,0x3adedc,
              0x3adf58,0x3adf88,0x3adfa4}
    selected.update(range(0x391c24,0x391cf0,4))
    for match in re.finditer(r'^INS\t([0-9a-f]+)\t([0-9a-f]+)\t([^\r\n]+)',text,re.M):
        va=int(match[1],16); raw=bytes.fromhex(match[2]);off=offset(va)
        if data[off:off+4]!=raw:raise ValueError('Ghidra bytes differ at '+hex(va))
        word=struct.unpack('<I',raw)[0]
        ins=rabbitizer.Instruction(word,va,rabbitizer.InstrCategory.R5900)
        checked+=1
        if va in selected:rows.append({'va':hex(va),'file_offset':off,'bytes_hex':raw.hex(),'word':hex(word),
                                      'ghidra':match[3], 'rabbitizer':ins.disassemble()})
    strings={}
    for va in (0x487440,0x487450,0x487470,0x487488,0x487958,0x487970):
        off=offset(va);strings[hex(va)]=data[off:data.index(b'\0',off)].decode('ascii')
    names=('carbrakelights','carbrakelight','brakelight','crashiny')
    absence={n:(n.encode()+b'\0' not in data) for n in names}
    result={'schema_version':1,'elf_sha256':digest,'ghidra_language':'r5900:LE:32:default',
            'decoder':'Rabbitizer InstrCategory.R5900','word_correspondence_checked':checked,
            'instruction_samples':rows,'strings':strings,'tokens_not_present_as_literal_c_strings':absence,
            'evidence_grade':'CONFIRMED_BY_EXE','scope':'Six bounded functions, byte correspondence; no live GS/frame proof',
            'unknowns':['Actual brake child selection and live native texture lifetime','Pixel appearance of authored perspex/lightshine sampling']}
    roles={0x391690:'Material generic mode setup, shader dispatch, post-shader lamp texture-name modes',
           0x3a6c58:'Interned shader registry lookup; unknown-name logging or virtual handler call',
           0x390f98:'One-time shader registration producer',0x3ade58:'carshiny mode3/resource override and color auxiliary',
           0x390a98:'Three boolean fields and text for one source texture map',
           0x390ba8:'Three map presence fields,20-byte map stride and material text loader'}
    result['functions']=[{'entry':hex(int(m[1],16)),'end_inclusive':hex(int(m[2],16)),
                         'size':int(m[2],16)-int(m[1],16)+1,'role':roles[int(m[1],16)],
                         'evidence_grade':'CONFIRMED_BY_EXE','boundary':'Ghidra database bounds, original words checked'}
                        for m in re.finditer(r'^FUNCTION ([0-9a-f]+)\.\.([0-9a-f]+)',text,re.M)]
    (HERE/'r5900-byte-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print('R5900 original word checks',checked,'samples',len(rows),'unknown strings absent',absence)


if __name__=='__main__':main()
