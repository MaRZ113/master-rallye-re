"""Read-only x86 class-publisher research; never patches a game or builds a roster."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]


def inspect(executable):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX as EAX,UC_X86_REG_ECX as ECX,UC_X86_REG_ESP as ESP,UC_X86_REG_EIP as EIP
    import addon_runtime
    raw=Path(executable).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!='bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4':raise ValueError('Unknown retail executable')
    pe,sections=addon_runtime._pe_sections(raw)
    def machine():
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
        for s in sections:u.mem_write(0x400000+s['rva'],raw[s['raw_offset']:s['raw_offset']+s['raw_size']])
        u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x20000);u.reg_write(ESP,0x100fff0);u.mem_write(0x100fff0,struct.pack('<II',0x1001000,0));u.reg_write(ECX,0x2000000);return u
    def ret(u,args=0,result=0):
        sp=u.reg_read(ESP);pc=struct.unpack('<I',u.mem_read(sp,4))[0];u.reg_write(ESP,sp+4+args);u.reg_write(EAX,result);u.reg_write(EIP,pc)
    def run(u,address):
        u.emu_start(address,0x1001000,count=10000)
        if u.reg_read(EIP)!=0x1001000:raise ValueError('Native helper did not return')
    publisher=[]
    for bound in (12,13,16):
        u=machine();original=bytes(u.mem_read(0x4819a4,5));assert original==bytes.fromhex('83fe0c7cb1')
        # Controlled hypothetical instruction in an emulator-private memory map.
        # This is NOT an SDK runtime hook, supported roster, or retail file edit.
        if bound!=12:u.mem_write(0x4819a6,bytes([bound]))
        keys=[]
        def hook(u,address,size,data):
            if address==0x5c20ba:
                sp=u.reg_read(ESP);buffer,fmt,index=struct.unpack('<III',u.mem_read(sp+4,12));keys.append(index);format_text=bytes(u.mem_read(fmt,128)).split(b'\0',1)[0].decode('ascii');text=(format_text%index).encode()+b'\0';assert len(text)<=64;u.mem_write(buffer,text);ret(u)
            elif address==0x4d0580:ret(u,4)
            elif address==0x4d8ec0:ret(u,8,result=0x2001000)
            elif address==0x4d8000:ret(u)
        u.hook_add(UC_HOOK_CODE,hook);run(u,0x481950);assert keys==list(range(bound));publisher.append({'bound':bound,'emulated_keys':keys,'only_hypothesis':bound!=12})
    navigation=[]
    for cls in range(3):
        for selected in (11,12):
            u=machine();u.mem_write(0x2000010,struct.pack('<I',cls));u.mem_write(0x2000014+4*cls,struct.pack('<I',selected));u.mem_write(0x2000020+4*cls,struct.pack('<I',13))
            def hook(u,address,size,data):
                if address in (0x4ae700,0x4adc30,0x481950,0x4819b0,0x481df0):ret(u)
            u.hook_add(UC_HOOK_CODE,hook);run(u,0x481f50);value=struct.unpack('<I',u.mem_read(0x2000014+4*cls,4))[0];assert value==12;navigation.append({'class':cls,'count':13,'before':selected,'after':value})
    return {'status':'PASS_CLASS_HELPER_RESEARCH','exe_sha256':digest,'publisher_original_va':'004819A4','publisher_original_bytes':'83fe0c7cb1','publisher':publisher,'native_count_driven_navigation':navigation,'gameplay_qualified_records':30,'runtime_candidate_modified':False,'limits':'Emulated position-key publication and navigation only. No UI node/frame allocation, T3 registry/AI/save/roster proof, full game, or universal capacity claim.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();report=inspect(a.exe);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
