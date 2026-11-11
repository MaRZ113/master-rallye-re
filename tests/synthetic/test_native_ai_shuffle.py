"""Original retail Sattolo execution explains last-item starvation on rebuild."""
import random,struct,unittest
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX

class NativeShuffle(unittest.TestCase):
    def test_last_source_cannot_be_first_popped(self):
        p=Path(__file__).resolve().parents[3]/'corpora/retail/MRallye.exe'
        raw=p.read_bytes();code=raw[0x50580:0x505e8]
        self.assertEqual(code[:4],bytes.fromhex('8b442408'))
        choices=set();ids=[7,8,9,10,11,12,13,27,28,29,30,31,33,34]
        for seed in range(256):
            rng=random.Random(seed);u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x450000,4096);u.mem_write(0x450580,code)
            u.mem_map(0x5c3000,4096);u.mem_map(0x1000000,65536);u.mem_map(0x2000000,4096)
            u.mem_write(0x2000000,struct.pack('<14I',*ids));sp=0x1008000;u.reg_write(UC_X86_REG_ESP,sp);u.mem_write(sp,struct.pack('<3I',0x450600,0x2000000,0x2000000+56))
            def rand(uc,at,size,user):
                if at==0x5c37b8:
                    stack=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',uc.mem_read(stack,4))[0]
                    uc.reg_write(UC_X86_REG_EAX,rng.randrange(32768));uc.reg_write(UC_X86_REG_ESP,stack+4);uc.reg_write(UC_X86_REG_EIP,ret)
            u.hook_add(UC_HOOK_CODE,rand);u.emu_start(0x450580,0x450600,count=20000)
            choices.add(struct.unpack('<I',u.mem_read(0x2000000+52,4))[0])
        self.assertNotIn(34,choices);self.assertIn(33,choices);self.assertEqual(len(choices),13)

if __name__=='__main__':unittest.main()
