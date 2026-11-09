"""The actual optional G1 pool callback wrapper preserves native frame ABI."""
import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import r_mod1_native_plan as plan

class RegistrySelector(unittest.TestCase):
    def test_all_native_owners_active_and_stock(self):
        from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_PROT_READ,UC_PROT_EXEC
        from unicorn.x86_const import UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESI as SI,UC_X86_REG_EFLAGS as FLAGS
        for number,base in enumerate((plan.SELECTOR_BASE,plan.MASTER_SELECTOR_BASE,plan.CUP_SELECTOR_BASE)):
            for marker in (0,-1,-2):
                spec=dict(plan.randomizer.SPECS[number],base=base,registry_pool=True)
                if number==0:spec['duplicate_repeat_fallback']=True
                code,labels=plan.make_rmod1_selector(spec)
                self.assertLess(len(code),0x300)
                u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(plan.CODE_BASE,65536);u.mem_write(base,code);u.mem_protect(plan.CODE_BASE,65536,UC_PROT_READ|UC_PROT_EXEC)
                u.mem_map(plan.DATA_BASE,65536);u.mem_map(0x1000000,65536);u.mem_map(0x71000000,4096)
                u.mem_write(plan.SLOT_REGISTRY_POOL,struct.pack('<I',0x71000000))
                sp=0x1008000;u.reg_write(SP,sp)
                u.mem_write(sp+spec['marker'],struct.pack('<i',marker));u.mem_write(sp+spec['cls'],struct.pack('<I',1))
                saved={AX:0x1234,CX:0x2222,DX:0x3333,SI:0x4444,FLAGS:0x202}
                for reg,value in saved.items():u.reg_write(reg,value)
                calls=[]
                def callback(uc,at,size,user):
                    if at!=0x71000000:return
                    cur=uc.reg_read(SP);ret,hint,cls,vector=struct.unpack('<4I',uc.mem_read(cur,16))
                    self.assertEqual((hint,cls,vector),(spec['hint'],1,sp+spec['primary']))
                    calls.append(at)
                    for reg in (AX,CX,DX):uc.reg_write(reg,0xdeadbeef)
                    uc.reg_write(FLAGS,0x246);uc.reg_write(SP,cur+16);uc.reg_write(IP,ret)
                u.hook_add(UC_HOOK_CODE,callback);u.emu_start(labels['pool_end'],labels['unfiltered_pool_end'],count=200)
                self.assertEqual(len(calls),int(marker!=0));self.assertEqual(u.reg_read(SP),sp)
                for reg,value in saved.items():self.assertEqual(u.reg_read(reg),value)

if __name__=='__main__':unittest.main()
