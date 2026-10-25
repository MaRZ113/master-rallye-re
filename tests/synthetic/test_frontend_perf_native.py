"""No proprietary fixtures: exact generated wrapper ABI/counter CPU replay."""
import struct,unittest
from tools.vehicle_frontend_perf_native import wrapper,STAGES,STATE_BYTES


def execute(argc,*,gpu=False):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_PROT_READ,UC_PROT_EXEC
    from unicorn.x86_const import UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_EBX as BX,UC_X86_REG_ESI as SI,UC_X86_REG_EDI as DI,UC_X86_REG_EBP as BP,UC_X86_REG_EFLAGS as FL
    u=Uc(UC_ARCH_X86,UC_MODE_32);entry=0x10000000;target=0x4000000;clock=0x3000000;state=0x2000000;stack=0x100f000;stop=0x1001000
    for at,size in ((entry,4096),(target,4096),(clock,4096),(state,4096),(0x1000000,65536),(0x68f000,4096)):u.mem_map(at,size)
    u.mem_write(entry,wrapper(entry,target,argc,state,gpu=gpu));u.mem_protect(entry,4096,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_write(0x68f228,struct.pack('<I',clock));u.mem_write(state+0x150,struct.pack('<I',target))
    u.mem_write(target,b'\xc2'+struct.pack('<H',argc*4));calls=[];ticks=[100,300,500,550,1000,1400]
    def word(at):return struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
    def ret(pop):sp=u.reg_read(SP);u.reg_write(IP,word(sp));u.reg_write(SP,sp+4+pop)
    def hook(uc,address,size,data):
        sp=uc.reg_read(SP)
        if address==clock:
            value=ticks.pop(0);uc.mem_write(word(sp+4),struct.pack('<Q',value));uc.reg_write(AX,1);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef);ret(4)
        if address==target:
            if [word(sp+4+i*4) for i in range(argc)]!=list(range(11,11+argc)):raise ValueError('copied argument mismatch')
            if uc.reg_read(CX)!=0x778899:raise ValueError('this/volatile input lost')
            calls.append(address);uc.reg_write(AX,0x80004005);uc.reg_write(CX,0x123);uc.reg_write(DX,0x456);uc.reg_write(FL,0x246)
    u.hook_add(UC_HOOK_CODE,hook)
    for i in range(3):
        u.mem_write(stack,struct.pack('<'+str(argc+1)+'I',stop,*range(11,11+argc)));u.reg_write(SP,stack);u.reg_write(CX,0x778899);u.reg_write(DX,state+0x100)
        saved={BX:0x1111,SI:0x2222,DI:0x3333,BP:0x4444}
        for r,v in saved.items():u.reg_write(r,v)
        u.emu_start(entry,stop,count=10000)
        if u.reg_read(SP)!=stack+4+argc*4 or any(u.reg_read(r)!=v for r,v in saved.items()):raise ValueError('wrapper ABI changed')
        if (u.reg_read(AX),u.reg_read(CX),u.reg_read(DX))!=(0x80004005,0x123,0x456):raise ValueError('return registers changed')
        if gpu:
            if not u.reg_read(FL)&0x80 or u.reg_read(FL)&0x40:raise ValueError('displaced GPU result TEST lost')
        elif u.reg_read(FL)!=0x246:raise ValueError('callee flags changed')
    lock,count,total,maximum,last=struct.unpack('<IIQQQ',bytes(u.mem_read(state,32)))
    if (lock,count,total,maximum,last)!=(0,3,650,400,400) or len(calls)!=3:raise ValueError('QPC counter mismatch')
    return count


class FrontendPerfNativeTests(unittest.TestCase):
    def test_direct_wrapper_argcounts_registers_flags_and_timing(self):
        for argc in (0,1,2,4,10):self.assertEqual(execute(argc),3)

    def test_gpu_indirect_call_and_displaced_test(self):self.assertEqual(execute(8,gpu=True),3)

    def test_budget(self):self.assertEqual(STATE_BYTES,288);self.assertEqual(len(STAGES),9)
