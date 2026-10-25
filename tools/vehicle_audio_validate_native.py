#!/usr/bin/env python3
"""Controlled x86 audio-name wrapper replay; no game or DirectSound launch."""
from __future__ import annotations
import argparse,copy,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from vehicle_audio_native import append_audio,INTERN,RACE_BROKER,CAR_ID,SITES
from validate_vehicle_physics_forces import machine,ptr
from master_rallye.vehicle_physics_binding import parse_pe32_layout

def replay(exe,profile,second_profile=None):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESI as SI,UC_X86_REG_EDI as DI,UC_X86_REG_EBX as BX,UC_X86_REG_EBP as BP,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EFLAGS as FL
    second=copy.deepcopy(second_profile) if second_profile is not None else copy.deepcopy(profile)
    if second_profile is None:second['physical_car_id']=profile['physical_car_id']+1;second['namespace']='second_probe'
    if second['stock_audio_profile_id']!=profile['stock_audio_profile_id']:raise ValueError('this callsite replay requires profiles sharing the selected native tuning case')
    site=SITES[profile['stock_audio_profile_id']]
    image,blob,report=append_audio(exe,exe,b'\x90'*32,0x10000000,[profile,second],65536)
    layout=parse_pe32_layout(exe);rows=[]
    # Native interner callsite input sequence is qualified in original bytes.
    # Different cases share exact push/lea/call structure but local offsets vary.
    start=site-9;off=layout.va_to_file_offset(start);original=exe[off:off+14]
    if original[0]!=0x68 or original[5:8]!=bytes.fromhex('8d4c24'):raise ValueError('audio pre-call shape differs')
    for slot in (0,1,7,31):
        for physical in sorted(set(range(28))|{profile['physical_car_id'],second['physical_car_id'],255}):
            u=machine(exe);u.mem_map(0x10000000,65536);u.mem_write(0x10000000,blob)
            u.mem_write(start,image[off:off+14]);base=0x100e000;obj=0x2000000;ptr(u,obj+0x54,slot)
            for reg,val in [(SP,base),(SI,obj),(DI,0x12345678),(BX,0x87654321),(BP,0x11223344),(AX,0x55667788),(DX,0x99887766),(FL,0x203)]:u.reg_write(reg,val)
            observed={}
            def hook(uc,address,size,data):
                sp=uc.reg_read(SP)
                if address==RACE_BROKER:
                    if struct.unpack('<I',bytes(uc.mem_read(sp+4,4)))[0]!=slot:raise ValueError('wrong race slot at broker')
                    uc.reg_write(AX,0x2004000);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef)
                    uc.reg_write(IP,struct.unpack('<I',bytes(uc.mem_read(sp,4)))[0]);uc.reg_write(SP,sp+4)
                elif address==CAR_ID:
                    if uc.reg_read(CX)!=0x2004000 or struct.unpack('<I',bytes(uc.mem_read(sp+4,4)))[0]!=slot:raise ValueError('wrong original getter ABI')
                    uc.reg_write(AX,physical);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef);uc.reg_write(FL,0x246)
                    uc.reg_write(IP,struct.unpack('<I',bytes(uc.mem_read(sp,4)))[0]);uc.reg_write(SP,sp+8)
                elif address==INTERN:
                    at=struct.unpack('<I',bytes(uc.mem_read(sp+4,4)))[0]
                    observed['path']=bytes(uc.mem_read(at,96)).split(b'\0',1)[0].decode('ascii')
                    uc.emu_stop()
            u.hook_add(UC_HOOK_CODE,hook);u.emu_start(start,0x1002000,count=10000)
            expected='vehicles/sdk/'+({profile['physical_car_id']:profile['namespace'],second['physical_car_id']:second['namespace']}[physical])+'/engine' if physical in (profile['physical_car_id'],second['physical_car_id']) else bytes(u.mem_read(struct.unpack_from('<I',original,1)[0],96)).split(b'\0',1)[0].decode('ascii')
            if observed.get('path')!=expected or u.reg_read(IP)!=INTERN or u.reg_read(SP)!=base-8:raise ValueError('audio path/stack mismatch')
            if [u.reg_read(x) for x in (SI,DI,BX,BP,DX,AX)]!=[obj,0x12345678,0x87654321,0x11223344,0x99887766,0x55667788] or u.reg_read(CX)!=base-4+original[8] or u.reg_read(FL)!=0x203:raise ValueError('audio register/flags preservation failed')
            rows.append({'slot':slot,'physical_car_id':physical,'engine_resource':expected})
    if blob[:32]!=b'\x90'*32:raise ValueError('existing extension prefix changed')
    try:append_audio(b'X'+exe[1:],exe,b'',0x10000000,[profile],65536)
    except ValueError:pass
    else:raise ValueError('foreign exe accepted')
    altered=bytearray(exe);altered[layout.va_to_file_offset(site)]=0x90
    try:append_audio(exe,bytes(altered),b'',0x10000000,[profile],65536)
    except ValueError:pass
    else:raise ValueError('changed parent callsite accepted')
    return {'status':'PASS','cases':rows,'binding':report,'evidence_boundary':'original push/LEA/CALL and generated wrapper execute in Unicorn; broker lookup/interner are typed stubs. No DirectSound/device audibility or actual race confirmation.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=replay(a.exe.read_bytes(),json.loads(a.profile.read_text(encoding='utf-8')));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
