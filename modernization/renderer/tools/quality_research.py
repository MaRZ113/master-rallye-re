"""Deterministic, hash-gated read-only R-GFX5 input/cave/capture audit.

Never executes a patcher, applies patches, or writes game files. Capstone only
decodes the reference cave; the bounded evaluator accepts CMP and branches.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from verify_proxy import PE

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
REFERENCE = 'bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6'
PATCHER = 'e0de5489b3b512d174024397eac0d54dc2afd8f3f2c13933a0c3881f75860814'
FREEZE = '6719605fb97b59f6d11a480bf8b6e6f223c726cfff1b656862fd2a9640b02b1b'
FREEZE_CONTEXT = bytes.fromhex('85ff75118b4424108b4e1850e8152f0a00ff44241484db')
UI_CONTEXT = bytes.fromhex('d987b8000000d86030d9c0d8c9d9c2d8cb')
BASE = 0x6ac444
TARGETS = {0x68dfb8: 1, 0x68dfc6: -1, 0x68dfd2: 0}

def read_locked(path, expected):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise ValueError('Exact input SHA256 mismatch: '+str(path))
    return data

def output_guard(path):
    result = Path(path).resolve()
    if not (result.is_relative_to(ROOT/'research/r-gfx5') or result.is_relative_to(ROOT/'.analysis/r-gfx5')):
        raise ValueError('R-GFX5 output boundary')
    return result

def signed_bits(value):
    return struct.unpack('<i', struct.pack('<f', value))[0]

def instructions(code, base):
    import capstone
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    cs.detail = True
    rows = {}
    for i in cs.disasm(code, base):
        if i.mnemonic == 'cmp' and i.operands[0].type == capstone.CS_OP_MEM and i.operands[0].mem.base == capstone.x86.X86_REG_EAX and i.operands[0].mem.disp in (0x30,0x34,0x38) and i.operands[1].type == capstone.CS_OP_IMM:
            immediate = i.operands[1].imm & 0xffffffff
            rows[i.address] = (i.size,'cmp',i.operands[0].mem.disp,immediate)
        elif i.mnemonic in ('jmp','je','jne','jl','jg') and i.operands[0].type == capstone.CS_OP_IMM:
            rows[i.address] = (i.size,i.mnemonic,int(i.operands[0].imm),0)
        else:
            raise ValueError('Unreviewed cave instruction: '+i.mnemonic+' '+i.op_str)
    if sum(row[0] for row in rows.values()) != len(code):
        raise ValueError('Undecoded cave suffix')
    return rows

def evaluate(rows, x, y, z=0, base=BASE, targets=TARGETS):
    pc = base; compare = 0
    for _ in range(256):
        if pc in targets:
            return targets[pc]
        if pc not in rows:
            raise ValueError('Cave branch leaves reviewed instruction range')
        size, op, a, b = rows[pc];pc += size
        if op == 'cmp':
            immediate = b if b < 0x80000000 else b-0x100000000
            compare = signed_bits({0x30:x,0x34:y,0x38:z}[a])-immediate
        elif op == 'jmp' or op == 'je' and compare == 0 or op == 'jne' and compare != 0 or op == 'jl' and compare < 0 or op == 'jg' and compare > 0:
            pc = a
        elif op not in ('je','jne','jl','jg'):
            raise ValueError('Unsupported evaluator instruction')
    raise ValueError('Cave exceeds bounded instruction budget')

def recover_rules(rows):
    xs=set();ys=set()
    for _,op,a,b in rows.values():
        if op == 'cmp' and a in (0x30,0x34):
            (xs if a==0x30 else ys).add(struct.unpack('<f',struct.pack('<I',b))[0])
    points=[]
    for x in sorted(xs):
        for y in sorted(ys):
            direction=evaluate(rows,x,y)
            if direction and not (25<=x<=106 and (19<=y<100 or 259<=y<340)):
                points.append([x,y,direction])
    return points

def capture_audit(path):
    data=Path(path).read_bytes();records=[json.loads(line) for line in data.decode('utf-8-sig').splitlines() if line.strip()]
    if not records or records[0].get('exe_sha256')!=TARGET:
        raise ValueError('Capture exact-build identity mismatch')
    presents=[r for r in records if r.get('method')=='Present']
    clears=[r for r in records if r.get('method')=='Clear']
    return {'name':Path(path).name,'sha256':hashlib.sha256(data).hexdigest(),'present_count':len(presents),'all_present_arguments_null':bool(presents) and all(not any(r['arguments'][:4]) for r in presents),'clear_count':len(clears),'full_color_depth_clears':sum(r['arguments'][0]==0 and r['arguments'][2]&3==3 for r in clears),'complete':records[-1].get('complete',False),'evidence_grade':'OBSERVED_IN_EXISTING_RUNTIME_CAPTURE'}

def research(retail, reference, patcher, freeze, captures=()):
    raw=read_locked(retail,TARGET);old=read_locked(reference,REFERENCE);tool=read_locked(patcher,PATCHER);script=read_locked(freeze,FREEZE)
    exe=PE(raw);ref=PE(old)
    if exe.take(exe.offset(0x1b015a),len(FREEZE_CONTEXT))!=FREEZE_CONTEXT:
        raise ValueError('Pristine freeze context mismatch')
    if exe.take(exe.offset(0x109a1b),len(UI_CONTEXT))!=UI_CONTEXT:
        raise ValueError('Pristine UI context mismatch')
    rows=instructions(ref.take(ref.offset(BASE-ref.image_base,0x39f),0x39f),BASE)
    return {'inputs':[{'name':Path(path).name,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)} for path,data in [(retail,raw),(reference,old),(patcher,tool),(freeze,script)]],
            'pristine_image_base':exe.image_base,'freeze':{'va':'0x005b015c','rva':'0x001b015c','file_offset':exe.offset(0x1b015c),'context_hex':FREEZE_CONTEXT.hex(),'branch_target_before':'0x005b016f','branch_target_after':'0x005b015e','render_call_va':'0x005b0166','render_owner_va':'0x00653080','reference_file_offset':'0x0024a1bc','reference_va':hex(ref.image_base+0x24a1bc),'evidence_grade':'CONFIRMED_BY_EXE'},
            'ui_sort':{'va':'0x00509a21','rva':'0x00109a21','context_hex':UI_CONTEXT.hex(),'overwritten_instructions':['FSUB dword [EAX+0x30]','FLD ST(0)'],'evidence_grade':'CONFIRMED_BY_EXE'},
            'reference_cave':{'va':hex(BASE),'rva':hex(BASE-ref.image_base),'instruction_count':len(rows),'point_rules':recover_rules(rows),'z_required':0,'left_bands':{'x_inclusive':[25,106],'y_half_open':[[19,100],[259,340]]},'evidence_grade':'CONFIRMED_BY_REFERENCE_EXE'},
            'captures':[capture_audit(p) for p in captures],'inputs_executed':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('retail','reference','patcher','freeze'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--captures',type=Path,nargs='*',default=[])
    p.add_argument('--output',type=output_guard,required=True)
    a=p.parse_args();result=research(a.retail,a.reference,a.patcher,a.freeze,a.captures)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
