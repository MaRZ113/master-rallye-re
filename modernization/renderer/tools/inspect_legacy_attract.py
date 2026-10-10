"""Exact-retail, read-only R-ATTR1 bytes/control-flow and startup verification."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from verify_proxy import PE

ROOT=Path(__file__).resolve().parents[1]
SHA='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
LOADING_RVA=0x64e40
PATCH_RVA=0x64f69
SUCCESS_RVA=0x64f46
REPLACEMENT=bytes.fromhex('e9d8ffffff')

def expected_loading():
    text=(ROOT/'include/legacy_attract_bytes.hpp').read_text()
    return bytes(int(v,16) for v in re.findall(r'0x([0-9a-f]{2})\b',text.split('[]={',1)[1]))

def inspect(blob):
    if hashlib.sha256(blob).hexdigest()!=SHA:
        raise ValueError('Not exact pristine retail')
    pe=PE(blob)
    if pe.machine!=0x14c or pe.image_base!=0x400000:
        raise ValueError('Incorrect PE identity')
    loading=blob[pe.offset(LOADING_RVA):pe.offset(LOADING_RVA)+374]
    if loading!=expected_loading():
        raise ValueError('Production Loading context differs from pristine')
    if loading[PATCH_RVA-LOADING_RVA:PATCH_RVA-LOADING_RVA+5]!=bytes.fromhex('68841f6b00'):
        raise ValueError('Original instruction is not the complete expected PUSH imm32')
    if PATCH_RVA+5+struct.unpack('<i',REPLACEMENT[1:])[0]!=SUCCESS_RVA:
        raise ValueError('Incorrect JMP target')
    checks=[(0x64f3a,bytes.fromhex('752d')),(0x64f44,bytes.fromhex('7e23')),
            (0x1d5244,bytes.fromhex('ff2514f46800')),
            (0x15905b,bytes.fromhex('e8e4c10700'))]
    for rva,code in checks:
        if blob[pe.offset(rva):pe.offset(rva)+len(code)]!=code:
            raise ValueError(f'Native branch/caller mismatch at RVA {rva:#x}')
    return {'phase':'R-ATTR1','build_sha256':SHA,'size':len(blob),'image_base':hex(pe.image_base),
            'loading_va':'0x00464E40','loading_rva':LOADING_RVA,'loading_size':374,
            'loading_sha256':hashlib.sha256(loading).hexdigest(),
            'patch_va':'0x00464F69','patch_rva':PATCH_RVA,'original':'68841f6b00',
            'replacement':REPLACEMENT.hex(),'instruction_length':5,
            'continuation_va':'0x00464F46','continuation_rva':SUCCESS_RVA,
            'factory_return_va':'0x00559060','factory_return_rva':0x159060,
            'idle_owner_va':'0x004655E0','idle_attract_setter_call_va':'0x004656B7',
            'idle_timer_branch_sha256':hashlib.sha256(blob[pe.offset(0x65694):pe.offset(0x656c6)]).hexdigest(),
            'evidence_grade':'CONFIRMED_BY_EXE','writes_performed':False,'runtime_status':'PENDING'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('binary',type=Path);a=ap.parse_args()
    print(json.dumps(inspect(a.binary.read_bytes()),indent=2))

if __name__=='__main__':main()
