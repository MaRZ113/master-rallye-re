"""Proprietary-fixture-free generated x86 guard/ABI replay."""
import struct,unittest
from tools.vehicle_camera_native import make_payload,NATIVE,NAME,BROKER,CAR_ID


def execute(name='Car0',physical=28,model='vehicles/lancer/car',broker=True):
 from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
 from unicorn.x86_const import UC_X86_REG_EAX as AX,UC_X86_REG_ECX as CX,UC_X86_REG_EDX as DX,UC_X86_REG_ESP as SP,UC_X86_REG_EIP as IP,UC_X86_REG_EDI as DI,UC_X86_REG_EBX as BX,UC_X86_REG_ESI as SI,UC_X86_REG_EBP as BP,UC_X86_REG_EFLAGS as FL
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for base,size in ((0x400000,0x400000),(0x10000000,65536),(0x2000000,65536)):u.mem_map(base,size)
 original=struct.pack('<11f',0,0,0,3,9,-1,-1,-3,1,1,3);replacement=struct.pack('<11f',0,0,0,3,9,-1,-.5,-2,1,.5,2)
 binding={'car_id':28,'model_resource':'vehicles/lancer/car','native_bounds_values_hex':original.hex(),'camera_bounds_hex':replacement.hex()}
 u.mem_write(0x10000000,make_payload(0x10000000,[binding]));node=0x2000000;entity=0x2001000;box=0x2002000;names=0x2003000;stack=0x200f000;stop=0x2004000
 u.mem_write(box,original);u.mem_write(names,name.encode()+b'\0');u.mem_write(names+128,model.encode()+b'\0');u.mem_write(stack,struct.pack('<I',stop));u.mem_write(0x6f6594,struct.pack('<I',int(broker)))
 slots=[];calls=[]
 def hook(uc,address,size,data):
  if address not in (NATIVE,NAME,BROKER,CAR_ID):return
  sp=uc.reg_read(SP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0];pop=0
  if address==NATIVE:calls.append(address);value=box;uc.reg_write(FL,0x246)
  elif address==NAME:value=names if uc.reg_read(CX)==entity+0x5c else names+128
  elif address==BROKER:value=0x2005000
  else:slots.append(struct.unpack('<I',uc.mem_read(sp+4,4))[0]);value=physical;pop=4
  uc.reg_write(AX,value);uc.reg_write(CX,0xdead);uc.reg_write(DX,0xbeef);uc.reg_write(SP,sp+4+pop);uc.reg_write(IP,ret)
 u.hook_add(UC_HOOK_CODE,hook)
 saved={DI:entity,BX:0x1111,SI:0x2222,BP:0x3333}
 for reg,value in saved.items():u.reg_write(reg,value)
 u.reg_write(CX,node);u.reg_write(SP,stack);u.emu_start(0x10000000,stop,count=10000)
 if len(calls)!=1 or u.reg_read(SP)!=stack+4 or any(u.reg_read(r)!=v for r,v in saved.items()) or u.reg_read(FL)!=0x246 or (u.reg_read(CX),u.reg_read(DX))!=(0xdead,0xbeef) or bytes(u.mem_read(box,44))!=original:raise AssertionError('native ABI/source state changed')
 return bytes(u.mem_read(u.reg_read(AX),44))==replacement,slots


class CameraNativeTests(unittest.TestCase):
 def test_selected_and_shared_model_other_id(self):
  self.assertEqual(execute(),(True,[0]));self.assertEqual(execute(physical=27),(False,[0]))
 def test_target_and_lifetime_fallbacks(self):
  for name in ('Car00','Car64','Car-1','Car','Replay0','Car1x'):
   self.assertEqual(execute(name=name),(False,[]))
  self.assertEqual(execute(name='Car63'),(True,[63]));self.assertEqual(execute(broker=False),(False,[]))
 def test_model_resource_guard(self):self.assertEqual(execute(model='vehicles/other/car'),(False,[]))
