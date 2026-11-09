"""Execute complete native class-pool loops with emitted SDK hooks, no game."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import j2_frontend_reentry as j2

def validate(bundle,source):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EAX as AX
    bundle=Path(bundle);rp=json.loads((bundle/'runtime-profile.json').read_text());plan=json.loads((bundle/'addon-plan.json').read_text())
    _,image,_=j2._parse_and_reconstruct(Path(source).read_bytes(),(bundle/'native-patch-ops.rvp').read_bytes())
    _,sections=j2.addon_runtime._pe_sections(image);blob=(bundle/'native-extension.bin').read_bytes();checks=[]
    for cls,entry,stock in [('T1',0x458127,list(range(7))),('T2',0x45816c,list(range(7,14))),('T3',0x4581b9,list(range(14,21)))]:
        eligible=stock+[r['physical_id'] for r in plan['addons'] if r['vehicle_class']==cls and r['ai_eligibility']['quick_race']['enabled']]
        for humans in ((-1,-1),(eligible[-1],-1),(eligible[-1],eligible[0])):
            u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
            for section in sections:u.mem_write(0x400000+section['rva'],image[section['raw_offset']:section['raw_offset']+section['raw_size']])
            u.mem_map(0x10000000,rp['native_extension']['allocation_size']);u.mem_write(0x10000000,blob)
            u.mem_map(0x1000000,65536);sp=0x1008000;u.reg_write(SP,sp)
            u.mem_write(sp+0x90,struct.pack('<2i',*humans));found=[]
            def callback(uc,at,size,user):
                if at not in (0x411c90,0x414920,0x4b0310,0x4afb70):return
                cur=uc.reg_read(SP);ret=struct.unpack('<I',uc.mem_read(cur,4))[0];cleanup=0
                if at in (0x411c90,0x414920):
                    cleanup=12 if at==0x411c90 else 8
                    ptr=struct.unpack('<I',uc.mem_read(cur+cleanup,4))[0]
                    found.append(struct.unpack('<I',uc.mem_read(ptr,4))[0])
                elif at==0x4b0310:cleanup=4
                uc.reg_write(AX,0);uc.reg_write(SP,cur+4+cleanup);uc.reg_write(IP,ret)
            u.hook_add(UC_HOOK_CODE,callback);u.emu_start(entry,0x4582d5,count=200000)
            expected=[i for i in eligible if i not in humans]
            if found!=expected:raise ValueError(f'{cls} native pool differs: {found} vs {expected}')
            if u.reg_read(SP)!=sp:raise ValueError('Native AI pool stack mismatch')
            checks.append({'class':cls,'excluded_humans':humans,'physical_ids':found})
    return {'status':'PASS_NATIVE_AI_POOL_LOOPS','checks':checks,'boundary':'Actual retail instructions and SDK detours; native vector insertion/progress services mocked; no game or Randomizer policy callback execution'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate(a.bundle,a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
