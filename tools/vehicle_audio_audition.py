#!/usr/bin/env python3
"""Offline native MR engine DSP audition using the user's exact original EXE.

Runs original x86 RPM normalization, engine-control mapping and PCM synthesis
in Unicorn. No DirectSound, game launch, modern shader/DSP or bundled native
code. This is an isolated audio diagnostic, not a physics or full mix simulator.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.audio_profile import decode_pcm,canonical_wav
from validate_vehicle_physics_forces import machine,ptr,f32,get
from build_vehicle_audio_candidate import load_stock_audio_profiles
from master_rallye.vehicle_physics_binding import parse_pe32_layout

def audition(exe,wav,*,stock_audio_profile_id,rpms,rev_limit=7000,seconds=1.):
    from unicorn.x86_const import UC_X86_REG_ECX as CX,UC_X86_REG_EAX as AX,UC_X86_REG_EBX as BX,UC_X86_REG_ESI as SI,UC_X86_REG_EBP as BP,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP
    if type(stock_audio_profile_id) is not int or not 0<=stock_audio_profile_id<=22:raise ValueError('ordinary stock tuning required')
    if type(rev_limit) not in (int,float) or not math.isfinite(rev_limit) or not 500<=rev_limit<=20000:raise ValueError('invalid audition rev limit')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not .01<=seconds<=3:raise ValueError('audition seconds outside0.01..3 guard')
    if not isinstance(rpms,list) or not 1<=len(rpms)<=8 or any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=30000 for x in rpms):raise ValueError('invalid bounded audition RPM list')
    samples,fmt=decode_pcm(wav)
    if fmt['sample_rate']!=48000 or fmt['channels']!=1 or fmt['bits_per_sample']!=16 or wav[:44]!=canonical_wav(samples)[:44] or len(samples)>192000:raise ValueError('audition requires compiled canonical mono16@48000 engine resource')
    matrix,rows=load_stock_audio_profiles();row=rows[stock_audio_profile_id];tables=matrix['curve_table_groups'][row['curve_group']]
    layout=parse_pe32_layout(exe);u=machine(exe);u.mem_map(0x3000000,0x200000)
    dsp=0x2008000;source=0x3000000;outbuf=0x3100000;public=0x2004000;actor=0x2000000;engine=0x2001000;control=0x2005000
    u.mem_write(source,struct.pack('<'+'h'*len(samples),*samples))
    # Run the original DSP constructor after its unrelated base-thread constructor.
    # The native remainder consumes saved ESI, return address, one device argument.
    sp=0x100e000;u.mem_write(sp,struct.pack('<3I',0,0x1002000,0));u.reg_write(SP,sp);u.reg_write(SI,dsp);u.emu_start(0x5a6d68,0x1002000,count=1000)
    if u.reg_read(IP)!=0x1002000:raise ValueError('native DSP constructor did not return')
    ptr(u,dsp+0x154,len(samples)*2);ptr(u,dsp+0x16c,source)
    table=b''
    for key,offset in [('first_va',0x5c),('second_va',0xd4)]:
        at=layout.va_to_file_offset(int(tables[key],16));part=exe[at:at+120];u.mem_write(dsp+offset,part);table+=part
    if hashlib.sha256(table).hexdigest()!=tables['sha256_concatenated']:raise ValueError('native synthesis table bytes differ')
    scalar=struct.unpack('<f',bytes.fromhex(row['sample_scalar_bits'])[::-1])[0]
    ptr(u,dsp+0x1d0,int(scalar*4096));ptr(u,actor+0x10,engine)
    rendered=[];diagnostics=[];nframes=round(seconds*48000)
    for rpm in rpms:
        # Original normalized RPM accessor; units cancel, as native omega/limit.
        f32(u,engine+0x28,rpm*.10471967);f32(u,engine+0x44,rev_limit*.10471967)
        sp=0x100e000;ptr(u,sp,0x1002000);u.reg_write(SP,sp);u.reg_write(CX,actor);u.emu_start(0x443900,0x1002000,count=1000)
        u.mem_write(0x1003000,bytes.fromhex('d91d00400002'));u.emu_start(0x1003000,0x1003006,count=1);ratio=get(u,public)
        if abs(ratio-max(0,min(1,rpm/rev_limit)))>1e-6:raise ValueError('native normalized RPM mismatch')
        f32(u,control+0x18,ratio)
        segment=[];coeff=[]
        for begin in range(0,nframes,960):
            # Execute original cubic control, original stock synthesis-table
            # interpretation, then raw PCM generator for a bounded20ms block.
            u.reg_write(BX,control);u.reg_write(SI,dsp);u.reg_write(BP,0x100d000);u.reg_write(SP,0x100c000)
            u.emu_start(0x5a78c4,0x5a7909,count=100000)
            if u.reg_read(IP)!=0x5a7909:raise ValueError('native audio control did not return')
            count=min(960,nframes-begin);sp=0x100e000;u.mem_write(sp,struct.pack('<3I',0x1002000,outbuf,count));u.reg_write(SP,sp);u.reg_write(CX,dsp)
            u.emu_start(0x5a7c30,0x1002000,count=count*1000+10000)
            if u.reg_read(IP)!=0x1002000:raise ValueError('native PCM generator budget exceeded')
            segment.extend(struct.unpack('<'+'h'*count,bytes(u.mem_read(outbuf,count*2))))
            coeff.append(struct.unpack('<I',bytes(u.mem_read(dsp+0x1a4,4)))[0])
        rendered+=segment
        diagnostics.append({'input_rpm':rpm,'rev_limit':rev_limit,'normalized_rpm':ratio,'frames':len(segment),'native_control_first':coeff[0],'native_control_last':coeff[-1],
            'peak_pcm16':max(abs(v) for v in segment),'rms_pcm16':math.sqrt(sum(v*v for v in segment)/len(segment)),
            'pcm_sha256':hashlib.sha256(struct.pack('<'+'h'*len(segment),*segment)).hexdigest()})
    report={'status':'PASS','exe_sha256':hashlib.sha256(exe).hexdigest(),'source_sha256':hashlib.sha256(wav).hexdigest(),'stock_audio_profile_id':stock_audio_profile_id,'sample_rate':48000,'segments':diagnostics,
        'native_routines':['00443900','005A6D68..005A6E6F','005A78C4..005A7909','005A7950','005A7EC0','005A7EF0','005A7C30'],
        'boundary':'Original local x86 DSP, fixed20ms control cadence and deterministic initial state. Omits DirectSound/thread timing, listener-distance/SFX volume, full race mix, shifts and physics response. Throttle is not an independent native engine layer; supply RPM sequences. This is not GT4 sound-bank playback or gameplay qualification.'}
    return canonical_wav(rendered),report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--resource',type=Path,required=True);p.add_argument('--stock-audio-profile-id',type=int,default=7);p.add_argument('--rpm',type=float,action='append',required=True);p.add_argument('--rev-limit',type=float,default=7000);p.add_argument('--seconds',type=float,default=1);p.add_argument('--output',type=Path,required=True);p.add_argument('--play',action='store_true');a=p.parse_args()
    data,report=audition(a.exe.read_bytes(),a.resource.read_bytes(),stock_audio_profile_id=a.stock_audio_profile_id,rpms=a.rpm,rev_limit=a.rev_limit,seconds=a.seconds)
    if a.output.exists():raise ValueError('audition output exists')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(data);a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if a.play:
        import winsound
        winsound.PlaySound(str(a.output.resolve()),winsound.SND_FILENAME)
