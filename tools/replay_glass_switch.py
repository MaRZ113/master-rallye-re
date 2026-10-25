"""Replay the original retail front-window increment and switch helpers.

Native source instructions, synthetic controller arrays, no game process.
Requires private exact retail EXE and optional local Unicorn.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from vehicle_damage_native import RETAIL_SHA256
import j2_frontend_reentry as j2


def replay(exe):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ESI,UC_X86_REG_EBX,UC_X86_REG_EIP
    if hashlib.sha256(exe).hexdigest()!=RETAIL_SHA256:raise ValueError('Unqualified native executable')
    _,sections=j2.addon_runtime._pe_sections(exe);u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
    for s in sections:u.mem_write(0x400000+s['rva'],exe[s['raw_offset']:s['raw_offset']+s['raw_size']])
    u.mem_map(0x2000000,0x10000)
    controller,owner,values,maxima,stack=0x2000000,0x2001000,0x2002000,0x2002100,0x200e000
    # Layout verified by exact 004D3C30 / 004D3C50 instructions.
    u.mem_write(controller+4,struct.pack('<I',values));u.mem_write(controller+0x14,struct.pack('<I',maxima));u.mem_write(controller+0x20,struct.pack('<I',4))
    u.mem_write(values,struct.pack('<4I',1,1,1,1));u.mem_write(maxima,struct.pack('<4I',2,2,2,2))
    u.mem_write(owner+0x34,struct.pack('<I',1));u.mem_write(owner+0x4c,struct.pack('<I',2))
    states=[]
    for _ in range(3):
        u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ESI,controller);u.reg_write(UC_X86_REG_EBX,owner)
        # Start after impact-side/threshold classification; stop before sound
        # dispatch. The actual increment, setter, bound check and counter run.
        u.emu_start(0x4c4878,0x4c48ab,count=1000)
        if u.reg_read(UC_X86_REG_EIP)!=0x4c48ab or u.reg_read(UC_X86_REG_ESP)!=stack:raise ValueError('Native switch replay ABI failed')
        states.append(list(struct.unpack('<4I',u.mem_read(values,16))))
    if states!=[[1,2,1,1]]*3:raise ValueError('Unexpected native per-pane transition')
    return {'status':'PASS_ORIGINAL_NATIVE_SWITCH_CPU_REPLAY','exe_sha256':RETAIL_SHA256,'entry':'0x004c4878','stop':'0x004c48ab','get':'0x004d3c30','set':'0x004d3c50','states_rear_front_left_right':states,'other_panes_unchanged':True,'third_state_rejected_for_two_case_source':True,'boundary':'isolated native CPU fragment; impact classification, geometry submission and actual gameplay are not emulated'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(replay(a.exe.read_bytes()),indent=2)+'\n')
