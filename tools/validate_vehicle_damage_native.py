"""Replay original damage instructions and the SDK alpha bridge in Unicorn.

Requires user-supplied exact retail EXE/model and optional Unicorn/Capstone.
This is isolated CPU evidence, never a live race or GPU parity claim.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
import vehicle_damage_native as native
import j2_frontend_reentry as j2


def execute(exe,model_data,impacts,*,adapted,wrong_uv=False):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP,UC_X86_REG_EAX as EAX,UC_X86_REG_EBX as EBX,UC_X86_REG_ESI as ESI,UC_X86_REG_EDI as EDI,UC_X86_REG_EBP as EBP
    if hashlib.sha256(exe).hexdigest()!=native.RETAIL_SHA256:raise ValueError('unqualified executable')
    m=parse_dx_bytes(model_data);n=m.vertex_count;blob,policy=native.payload(model_data)
    _,sections=j2.addon_runtime._pe_sections(exe);u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
    for s in sections:u.mem_write(0x400000+s['rva'],exe[s['raw_offset']:s['raw_offset']+s['raw_size']])
    u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x600000);u.mem_map(native.PAYLOAD_VA,policy.get("allocation_size",65536));u.mem_write(native.PAYLOAD_VA,blob)
    cfg=0x2000000;orig=0x2001000;current=0x2001100;uvdesc=0x2002000;resource=0x2004000;impact_list=0x2004200;event=0x2005000
    positions=b''.join(struct.pack('<3f',*p) for p in m.vertices.positions);uvs=b''.join(struct.pack('<2f',*p) for p in m.uv_sets[0].values)
    for model,xyz,colour in [(orig,0x2100000,0x2300000),(current,0x2200000,0x2380000)]:
        u.mem_write(model+4,struct.pack('<II',xyz,xyz+n*12));u.mem_write(xyz,positions)
        u.mem_write(model+0x24,struct.pack('<II',colour,colour+n*4));u.mem_write(colour,m.vertices.colors)
    u.mem_write(orig+0x34,struct.pack('<II',uvdesc,uvdesc+16));u.mem_write(uvdesc+4,struct.pack('<II',0x2400000,0x2400000+n*8));u.mem_write(0x2400000,uvs)
    if wrong_uv:u.mem_write(0x2400000,struct.pack('<f',m.uv_sets[0].values[0][0]+.125))
    u.mem_write(resource+0x14,struct.pack('<I',current));u.mem_write(impact_list+4,struct.pack('<II',event,event+36))
    # Exact original constructor defaults at 00589110, with all three native
    # features enabled: positions, RGB darkening, reflection alpha fading.
    u.mem_write(cfg+0x14,struct.pack('<6I',0x3d23d70b,0x3e4ccccd,0x3e23d70b,0x40800000,0x3f000000,0x41000000))
    u.mem_write(cfg+0x2c,b'\x01\x01\x01');u.mem_write(0x1002000,bytes.fromhex('dbe3'))
    returns=[]
    for impact in impacts:
        u.emu_start(0x1002000,0x1002002,count=1)
        u.mem_write(event,struct.pack('<8fI',*impact['point'],*impact['direction'],impact.get('speed',8.),impact.get('scale',1.),0))
        u.mem_write(0x100fff0,struct.pack('<5I',0x1001000,orig,resource,impact_list,0))
        u.reg_write(ESP,0x100fff0);u.reg_write(ECX,cfg)
        saved={EBX:0x12345678,ESI:0x23456789,EDI:0x3456789a,EBP:0x456789ab}
        for reg,value in saved.items():u.reg_write(reg,value)
        u.emu_start(native.PAYLOAD_VA if adapted else native.DAMAGE_NATIVE_VA,0x1001000,count=8000000)
        if u.reg_read(EIP)!=0x1001000 or u.reg_read(ESP)!=0x1010004:raise ValueError('damage ABI did not return/clean arguments')
        if any(u.reg_read(reg)!=value for reg,value in saved.items()):raise ValueError('callee-saved register corruption')
        returns.append(u.reg_read(EAX)&255)
    return {'positions':bytes(u.mem_read(0x2200000,n*12)),'colours':bytes(u.mem_read(0x2380000,n*4)),'returns':returns,'policy':policy}


def validate(exe,model_data):
    m=parse_dx_bytes(model_data);ps=m.vertices.positions
    # Deterministic synthetic rear/side impacts. They are not a reconstruction
    # of the user's exact driving, speed, collision times or physics settings.
    lo=[min(p[k] for p in ps) for k in range(3)];hi=[max(p[k] for p in ps) for k in range(3)]
    targets=[(hi[0],lo[1]+.3*(hi[1]-lo[1]),lo[2]+.25*(hi[2]-lo[2])),
             (lo[0],lo[1]+.3*(hi[1]-lo[1]),lo[2]+.25*(hi[2]-lo[2])),
             ((lo[0]+hi[0])/2,lo[1]+.35*(hi[1]-lo[1]),lo[2])]
    points=[min(ps,key=lambda p:math.dist(p,t)) for t in targets]
    impacts=[{'point':p,'direction':[(-.7 if p[0]>0 else .7),.1,.6],'speed':8.,'scale':1.} for p in points for _ in range(12)]
    original=execute(exe,model_data,impacts,adapted=False);adapted=execute(exe,model_data,impacts,adapted=True)
    if original['positions']!=adapted['positions'] or original['returns']!=adapted['returns']:raise ValueError('adapter changed native deformation or return values')
    if original['colours'][0::4]!=adapted['colours'][0::4] or original['colours'][1::4]!=adapted['colours'][1::4] or original['colours'][2::4]!=adapted['colours'][2::4]:raise ValueError('adapter changed native RGB darkening')
    mask=bytes.fromhex(adapted['policy']['mask_hex']);before=original['colours'][3::4];after=adapted['colours'][3::4];source=m.vertices.colors[3::4]
    if any(after[i]!=(source[i] if keep else before[i]) for i,keep in enumerate(mask)):raise ValueError('alpha ownership mismatch')
    unknown=execute(exe,model_data,impacts,adapted=True,wrong_uv=True)
    control=execute(exe,model_data,impacts,adapted=False,wrong_uv=True)
    if unknown['positions']!=control['positions'] or unknown['colours']!=control['colours']:raise ValueError('unrecognized UV identity was modified')
    damaged=list(struct.iter_unpack('<3f',original['positions']));groups={}
    for i,p in enumerate(ps):groups.setdefault(p,[]).append(i)
    split=sum(len(g)>1 and len({damaged[i] for i in g})>1 for g in groups.values())
    return {'status':'PASS_ORIGINAL_NATIVE_DAMAGE_AND_ADAPTER_CPU_REPLAY','boundary':'isolated Unicorn, original native instructions and synthetic native arrays/impacts; not gameplay or captured GPU buffers',
        'model_sha256':hashlib.sha256(model_data).hexdigest(),'native_exe_sha256':hashlib.sha256(exe).hexdigest(),
        'impacts':impacts,'positions_identical_to_native':True,'rgb_identical_to_native':True,'unknown_model_passes_through':True,
        'callee_saved_registers_and_stack':'PASS','exact_source_position_groups_split':split,
        'coverage_vertices_losing_alpha_without_adapter':sum(bool(keep) and a!=s for keep,a,s in zip(mask,before,source)),
        'coverage_vertices_losing_alpha_with_adapter':sum(bool(keep) and a!=s for keep,a,s in zip(mask,after,source)),
        'opaque_reflection_alpha_preserved_as_native':True,'policy':adapted['policy'],'runtime_qualified':False},original,adapted


def diagnostic_dx(model_data,state):
    """Materialize only actual CPU replay positions/colours for GPU inspection.

    Textures, UVs, topology and materials stay untouched. Caller supplies the
    private texture directory; this function is not an asset redistribution.
    """
    m=parse_dx_bytes(model_data);result=bytearray(model_data)
    for name,start,size in [('positions',m.vertices.position_offset,m.vertex_count*12),
                            ('colours',m.vertices.color_offset,m.vertex_count*4)]:
        if len(state[name])!=size:raise ValueError('diagnostic buffer length mismatch')
        result[start:start+size]=state[name]
    if not parse_dx_bytes(bytes(result)).diagnostics.validated:raise ValueError('invalid replay diagnostic DX')
    return bytes(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--diagnostic-dir',type=Path,help='optional private output; supply original textures separately')
    a=p.parse_args();data=a.model.read_bytes();report,control,adapted=validate(a.exe.read_bytes(),data)
    if a.diagnostic_dir:
        a.diagnostic_dir.mkdir(parents=True,exist_ok=True)
        for name,state in [('native-damaged.dx',control),('adapted-damaged.dx',adapted)]:
            (a.diagnostic_dir/name).write_bytes(diagnostic_dx(data,state))
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('impacts','policy')},indent=2))
