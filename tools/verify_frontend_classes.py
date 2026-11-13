"""Unicorn check of an installed roster's extra Vehicle Select classes (tools/frontend_classes.py).

Usage: python tools/verify_frontend_classes.py <game folder>. Emulates the reconstructed EXE (retail + roster RVP
operations) and the roster payload: constructor counts/selections, forward and reverse maps for every class position,
and the class-list append (label, published count, stack balance; nothing when only one class is published).
Game helpers (string ctor, list insert, free) are stubs; the Broker tail of the reverse map is not executed.
"""
import json,os,sys,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from roster_rebase import load
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
H=sys.argv[1]
exe=open(os.path.join(H,"MRallye.exe"),"rb").read()
raw,img=load(open(os.path.join(H,"MRMods","Vehicles","active","roster.mrvr"),"rb").read(),exe)
u=Uc(UC_ARCH_X86,UC_MODE_32)
u.mem_map(0x400000,0x400000);u.mem_write(0x400000,bytes(img.recon[:0x300000]))
u.mem_map(0x10000000,0x100000);u.mem_write(0x10000000,bytes(img.payload))
STACK,OBJ,LIST=0x2000000,0x3000000,0x3100000
u.mem_map(STACK-0x10000,0x20000);u.mem_map(OBJ,0x1000);u.mem_map(LIST,0x1000)
calls=[]
STUBS={0x4D11D0:4,0x407B30:12,0x5B4C00:0}   # string ctor (thiscall 1 arg), list insert (thiscall 3), free (cdecl)
def hook(uc,addr,size,ud):
    if addr in STUBS:
        esp=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack("<I",uc.mem_read(esp,4))[0]
        if addr==0x4D11D0:
            p=struct.unpack("<I",uc.mem_read(esp+4,4))[0];s=bytes(uc.mem_read(p,32)).split(b"\0")[0];calls.append(("str",s))
        else: calls.append((hex(addr),))
        uc.reg_write(UC_X86_REG_ESP,esp+4+STUBS[addr]);uc.reg_write(UC_X86_REG_EIP,ret)
u.hook_add(UC_HOOK_CODE,hook)
def run(start,stop,regs):
    u.reg_write(UC_X86_REG_ESP,STACK)
    u.mem_write(STACK,struct.pack("<I",0xDEAD0000))
    for r,v in regs.items(): u.reg_write(r,v)
    u.emu_start(start,stop,count=5000)
    return u.reg_read(UC_X86_REG_ESP)
rd=lambda off:struct.unpack("<I",u.mem_read(OBJ+off,4))[0]
fail=[]
import json
cat=json.load(open(os.path.join(H,"MRMods","Vehicles","active","catalog.json")))
fc=cat["frontend_classes"]["classes"];order=cat["frontend_classes"]["order"]
# 1) constructor body from 0x480a39 (after arg store) through the stubs to the end at 0x480a70
u.mem_write(OBJ,b"\xcc"*0x100)
run(0x480a39,0x480a70,{UC_X86_REG_ESI:OBJ})
n=len(order);sel=[rd(0x34+4*k) for k in range(n)];cnt=[rd(0x54+4*k) for k in range(n)]
print("ctor sel",sel,"count",cnt)
if sel!=[0]*n or cnt!=[len(fc[c]) for c in order]: fail.append("ctor")

# 2) forward map for every class/selection
FWD=0x481e20;REV=0x481e50
for k,c in enumerate(order):
    for i,pid in enumerate(fc[c]):
        u.mem_write(OBJ+0x10,struct.pack("<I",k));u.mem_write(OBJ+0x34+4*k,struct.pack("<I",i))
        run(FWD,0xDEAD0000,{UC_X86_REG_ECX:OBJ})
        got=u.reg_read(UC_X86_REG_EAX)
        if got!=pid: fail.append(f"fwd {c}[{i}]={got} want {pid}")
        # reverse: push id
        u.mem_write(OBJ+0x10,struct.pack("<I",9));u.mem_write(OBJ+0x34+4*k,struct.pack("<I",99))
        u.reg_write(UC_X86_REG_ESP,STACK-4);u.mem_write(STACK-4,struct.pack("<II",0xDEAD0000,pid))
        u.reg_write(UC_X86_REG_ECX,OBJ);u.reg_write(UC_X86_REG_ESI,0x5555);u.emu_start(REV,0x481e89,count=500)
        esp=u.reg_read(UC_X86_REG_ESP);saved=struct.unpack('<I',u.mem_read(esp,4))[0]
        if rd(0x10)!=k or rd(0x34+4*k)!=i or esp!=STACK-8 or saved!=0x5555 or u.reg_read(UC_X86_REG_ESI)!=OBJ: fail.append(f"rev {pid}: cls {rd(0x10)} sel {rd(0x34+4*k)} esp {esp-STACK} esi {u.reg_read(UC_X86_REG_ESI):#x}")
# out of range forward
u.mem_write(OBJ+0x10,struct.pack("<I",3));u.mem_write(OBJ+0x40,struct.pack("<I",3));run(FWD,0xDEAD0000,{UC_X86_REG_ECX:OBJ})
if u.reg_read(UC_X86_REG_EAX)!=0xFFFFFFFF: fail.append("fwd out of range")
print("maps checked",sum(len(v) for v in fc.values()))
# 3) class list hook at 0x481152 with +0x30==3 and ==1
for published,want in ((3,n),(1,1)):
    calls.clear();u.mem_write(OBJ+0x30,struct.pack("<I",published));u.mem_write(LIST+8,struct.pack("<I",0x777))
    esp=run(0x481152,0x68efa0,{UC_X86_REG_EDI:OBJ,UC_X86_REG_ESI:LIST})
    print("list published",published,"->",rd(0x30),"calls",calls,"esp delta",esp-STACK)
    if rd(0x30)!=want or esp!=STACK or (published==3 and [c[1] for c in calls if c[0]=="str"]!=[l.encode() for l in cat["frontend_classes"]["labels"]]) or (published==1 and calls): fail.append(f"list {published}")
print("FAIL",fail) if fail else print("PASS frontend class emulation")
sys.exit(1 if fail else 0)
