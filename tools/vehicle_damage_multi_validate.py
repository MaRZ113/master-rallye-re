"""Bounded CPU replay of shared damage dispatch; never gameplay evidence."""
import argparse,hashlib,json,struct
from pathlib import Path
from master_rallye.dx import parse_dx_bytes
import vehicle_damage_native as native


def replay(models, current_data, *, mismatch=None, native_success=True):
    """Synthetic deformation service isolates dispatch, ABI and alpha ownership."""
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_PROT_READ,UC_PROT_EXEC
    from unicorn.x86_const import UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EAX as EAX,UC_X86_REG_EBX as EBX,UC_X86_REG_ESI as ESI,UC_X86_REG_EDI as EDI,UC_X86_REG_EBP as EBP,UC_X86_REG_EIP as EIP
    blob,policy=native.payload_models(models);m=parse_dx_bytes(current_data);n=m.vertex_count
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(native.PAYLOAD_VA,policy.get('allocation_size',65536));u.mem_write(native.PAYLOAD_VA,blob);u.mem_protect(native.PAYLOAD_VA,policy.get('allocation_size',65536),UC_PROT_READ|UC_PROT_EXEC)
    u.mem_map(0x580000,0x20000);u.mem_write(native.DAMAGE_NATIVE_VA,bytes.fromhex('b801000000c21000' if native_success else '31c0c21000'))
    u.mem_map(0x2000000,0x1000000)
    orig=0x2000100;cfg=0x2000300;current=0x2000400;descriptor=0x2000500
    xyz=0x2100000;uv=0x2400000;source_colours=0x2600000;dest_colours=0x2800000
    positions=b''.join(struct.pack('<3f',*p) for p in m.vertices.positions);uvs=b''.join(struct.pack('<2f',*p) for p in m.uv_sets[0].values)
    u.mem_write(orig+4,struct.pack('<II',xyz,xyz+len(positions)));u.mem_write(xyz,positions)
    u.mem_write(orig+0x34,struct.pack('<II',descriptor,descriptor+16));u.mem_write(descriptor+4,struct.pack('<II',uv,uv+len(uvs)));u.mem_write(uv,uvs)
    u.mem_write(orig+0x24,struct.pack('<II',source_colours,source_colours+n*4));u.mem_write(source_colours,m.vertices.colors)
    u.mem_write(cfg+0xc,struct.pack('<I',current));u.mem_write(current+4,struct.pack('<II',dest_colours,dest_colours+n*4))
    if mismatch=='uv':u.mem_write(uv,struct.pack('<f',m.uv_sets[0].values[0][0]+.125))
    if mismatch=='positions':u.mem_write(xyz,struct.pack('<f',m.vertices.positions[0][0]+.125))
    if mismatch=='position_length':u.mem_write(orig+8,struct.pack('<I',xyz+len(positions)-12))
    if mismatch=='uv_length':u.mem_write(descriptor+8,struct.pack('<I',uv+len(uvs)-8))
    if mismatch=='source_colour_length':u.mem_write(orig+0x28,struct.pack('<I',source_colours+n*4-4))
    if mismatch=='target_colour_length':u.mem_write(current+8,struct.pack('<I',dest_colours+n*4-4))
    damaged=bytes((v//2 if i%4!=3 else 7) for i,v in enumerate(m.vertices.colors));calls=[]
    def hook(uc,address,size,user):
        if address==native.DAMAGE_NATIVE_VA:
            calls.append(address);uc.mem_write(dest_colours,damaged)
    u.hook_add(UC_HOOK_CODE,hook)
    stop=0x2001000;stack=0x2ffffe0;u.mem_write(stack,struct.pack('<5I',stop,orig,0,0,0));u.reg_write(ESP,stack);u.reg_write(ECX,cfg)
    saved={EBX:0x12345678,ESI:0x23456789,EDI:0x3456789a,EBP:0x456789ab}
    for reg,value in saved.items():u.reg_write(reg,value)
    u.emu_start(native.PAYLOAD_VA,stop,count=20000000)
    if u.reg_read(EIP)!=stop or u.reg_read(ESP)!=stack+20 or any(u.reg_read(r)!=v for r,v in saved.items()):raise ValueError('damage dispatch ABI failure')
    result=bytes(u.mem_read(dest_colours,n*4));mask=bytes.fromhex(native.alpha_ownership(current_data)['mask_hex'])
    expected=bytearray(damaged)
    if mismatch is None and native_success:
        for i,keep in enumerate(mask):
            if keep:expected[i*4+3]=m.vertices.colors[i*4+3]
    if result!=bytes(expected) or len(calls)!=1:raise ValueError('damage dispatch ownership or native call count failure')
    return {'native_calls':len(calls),'abi':'PASS','coverage':'PASS','mismatch':mismatch,'native_success':native_success,'model_sha256':hashlib.sha256(current_data).hexdigest()}


def validate(models):
    checks=[]
    for data in models:
        checks += [replay(models,data),replay(models,data,native_success=False)]
        checks += [replay(models,data,mismatch=kind) for kind in ('uv','positions','position_length','uv_length','source_colour_length','target_colour_length')]
    blob,policy=native.payload_models(models)
    return {'status':'PASS_MULTI_MODEL_DAMAGE_DISPATCH_CPU_REPLAY','checks':checks,'payload_size':len(blob),'policy':policy,'boundary':'isolated CPU, synthetic native deformer service, RX payload and unmapped null page; no gameplay qualification','runtime_qualified':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',type=Path,action='append',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    report=validate([p.read_bytes() for p in args.model]);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
