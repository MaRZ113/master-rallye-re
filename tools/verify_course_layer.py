"""Unicorn check of the course registry layer (tools/course_layer.py) on a roster.mrvr.

  python tools/verify_course_layer.py <game folder>            (installed roster: MRMods/Vehicles/active)

Emulates the reconstructed EXE (retail + RVP operations) and the payload: forward and reverse menu maps for every
group/position including the category, the RaceSelect object size, the mode-list append (8 retail modes -> label and
flag; 7 -> nothing), the details wrapper (title of new races, category logo frame, mode right arrow) and the best-time
dispatch for retail IDs. Game helpers are stubs; Broker values are recorded, not stored.
"""
import json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_rebase import load
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EBX, UC_X86_REG_ESI

H = sys.argv[1]
exe = open(os.path.join(H, "MRallye.exe"), "rb").read()
raw, img = load(open(os.path.join(H, "MRMods", "Vehicles", "active", "roster.mrvr"), "rb").read(), exe)
cat = json.load(open(os.path.join(H, "MRMods", "Vehicles", "active", "catalog.json")))["courses"]
races = cat["races"]
# RCX-CAT2: one Quick Race mode per category (older catalogs: a single category)
CATS = cat["category"].get("categories") or [{"label": cat["category"]["label"], "logo_frame": cat["category"]["logo_frame"]}]
labels = [c["label"].encode() for c in CATS]
STOCK = [list(range(10, 13)), list(range(13, 16)), list(range(16, 19)), list(range(19, 22)), list(range(22, 25)),
         list(range(25, 36)), list(range(10)), list(range(36, 39))]
GROUPS = STOCK + [[r["id"] for r in races if r.get("category", 0) == k] for k in range(len(CATS))]
LAST = len(GROUPS) - 1

u = Uc(UC_ARCH_X86, UC_MODE_32)
u.mem_map(0x400000, 0x400000); u.mem_write(0x400000, bytes(img.recon[:0x300000]))
payload_base, payload_allocation = struct.unpack_from("<II", raw, 16)
if not len(img.payload) <= payload_allocation <= 64 * 1024 * 1024:
    raise ValueError("Invalid installed roster payload allocation")
u.mem_map(payload_base, (payload_allocation + 0xfff) & ~0xfff)
u.mem_write(payload_base, bytes(img.payload))
STACK, OBJ, LIST, STR = 0x2000000, 0x3000000, 0x3100000, 0x3200000
u.mem_map(STACK - 0x10000, 0x20000); u.mem_map(OBJ, 0x1000); u.mem_map(LIST, 0x1000); u.mem_map(STR, 0x1000)
calls = []
STUBS = {0x4D11D0: 4, 0x407B30: 12, 0x5B4C00: 0, 0x47ED10: 0, 0x4D0580: 4, 0x4D8EC0: 4, 0x4D8000: 4, 0x4D85F0: 4}


def hook(uc, addr, size, ud):
    if addr in STUBS:
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret, a1 = struct.unpack("<II", uc.mem_read(esp, 8))
        if addr in (0x4D11D0, 0x4D0580):
            s = bytes(uc.mem_read(a1, 64)).split(b"\0")[0]
            calls.append(("str" if addr == 0x4D11D0 else "id", s))
            if addr == 0x4D0580:
                uc.mem_write(uc.reg_read(UC_X86_REG_ECX), struct.pack("<I", a1))     # id slot = the C string address
        elif addr == 0x4D8EC0:
            key = struct.unpack("<I", uc.mem_read(a1, 4))[0]
            calls.append(("get", bytes(uc.mem_read(key, 64)).split(b"\0")[0]))
            uc.reg_write(UC_X86_REG_EAX, 0x4B0B0)
        elif addr == 0x4D8000:
            calls.append(("set_int", a1))
        elif addr == 0x4D85F0:
            calls.append(("set_str",))
        else:
            calls.append((hex(addr),))
        uc.reg_write(UC_X86_REG_ESP, esp + 4 + STUBS[addr]); uc.reg_write(UC_X86_REG_EIP, ret)


u.hook_add(UC_HOOK_CODE, hook)
rd = lambda off: struct.unpack("<I", u.mem_read(OBJ + off, 4))[0]
wr = lambda off, v: u.mem_write(OBJ + off, struct.pack("<I", v))
fail = []


def call(start, regs, args=(), stop=0xDEAD0000, count=20000):
    sp = STACK - 4 * (len(args) + 1)
    u.mem_write(sp, struct.pack("<I", stop) + b"".join(struct.pack("<I", a) for a in args))
    u.reg_write(UC_X86_REG_ESP, sp)
    for r, v in regs.items():
        u.reg_write(r, v)
    u.emu_start(start, stop, count=count)
    return u.reg_read(UC_X86_REG_ESP) - STACK


# object size of the RaceSelect factory
if bytes(img.recon[0x47E206 - 0x400000:0x47E208 - 0x400000]) != b"\x6a" + bytes([0x74 + 4 * len(CATS)]):
    fail.append("factory size")
if bytes(img.recon[0x53BA99 - 0x400000:0x53BA9D - 0x400000]) != struct.pack("<I", 96 << 20):
    fail.append("model cache budget")
# forward / reverse for every group and position
for g, rows in enumerate(GROUPS):
    for p, rid in enumerate(rows):
        wr(0x10, g); wr(0x14 + 4 * g, p)
        call(0x47F2B0, {UC_X86_REG_ECX: OBJ})
        if u.reg_read(UC_X86_REG_EAX) != rid:
            fail.append(f"forward g{g}p{p} -> {u.reg_read(UC_X86_REG_EAX)} want {rid}")
        wr(0x10, 99); wr(0x14 + 4 * g, 99)
        d = call(0x47F320, {UC_X86_REG_ECX: OBJ}, (rid,))
        if rd(0x10) != g or rd(0x14 + 4 * g) != p or d != 0:
            fail.append(f"reverse {rid}: g{rd(0x10)} p{rd(0x14 + 4 * g)} esp{d}")
for k in range(len(CATS)):
    if rd(0x74 + 4 * k) != len(GROUPS[8 + k]):
        fail.append(f"category {k} count +{0x74 + 4 * k:#x} = {rd(0x74 + 4 * k)}")
print("maps", sum(map(len, GROUPS)), "races; category counts", [rd(0x74 + 4 * k) for k in range(len(CATS))])
# mode list: 8 retail modes -> append; 7 -> nothing
for n, want in ((8, 1), (7, 0)):
    calls.clear(); wr(0x50, 0xCC)
    for k in range(len(CATS)):
        wr(0x34 + 4 * k, 0xEE)
    u.mem_write(LIST + 4, struct.pack("<II", 0x4000, 0x4000 + 4 * n))
    # Retail state at 0x47E605: the object is the local [esp+14h]; EBX holds it with BL overwritten by a bool.
    u.mem_write(STACK - 4 + 0x14, struct.pack("<I", OBJ))                       # call() puts ESP at STACK-4
    d = call(0x47E605, {UC_X86_REG_EBX: (OBJ & ~0xFF) | 1, UC_X86_REG_ESI: LIST}, stop=0x47E60A)
    pushed = struct.unpack("<I", u.mem_read(u.reg_read(UC_X86_REG_ESP), 4))[0]
    if u.reg_read(UC_X86_REG_EBX) != (OBJ & ~0xFF) | 1:
        fail.append("list hook did not preserve EBX")
    strs = [c[1] for c in calls if c[0] == "str"]
    print(f"list of {n}: flag {rd(0x50)} strings {strs} pushed {pushed:#x} esp {d}")
    if rd(0x50) != want or pushed != 0x6B70D4 or d != -8 or strs != (labels if want else []) or \
            (want and any(rd(0x34 + 4 * k) != 0 for k in range(len(CATS)))):
        fail.append(f"list {n}")
# details wrapper
cases = [(8 + k, 1, GROUPS[8 + k][0]) for k in range(len(CATS))] + [(7, 1, 36), (8, 0, GROUPS[8][0]), (0, 1, 10)]
for g, flag, rid in cases:
    wr(0x10, g); wr(0x50, flag); wr(0x14 + 4 * g, GROUPS[g].index(rid))
    calls.clear()
    d = call(0x47ED10 + 0, {UC_X86_REG_ECX: OBJ, UC_X86_REG_ESI: 0x5151}) if False else None
    # the three native callers now call the wrapper; find it through the first caller (0x47E9F3)
    rel = struct.unpack("<i", bytes(img.recon[0x47E9F4 - 0x400000:0x47E9F8 - 0x400000]))[0]
    wrapper = 0x47E9F8 + rel
    d = call(wrapper, {UC_X86_REG_ECX: OBJ, UC_X86_REG_ESI: 0x5151})
    sets = [c for c in calls if c[0] in ("get", "set_int", "set_str")]
    print(f"details g{g} flag{flag} race{rid}: {sets} esp {d} esi {u.reg_read(UC_X86_REG_ESI):#x}")
    want = []
    if rid >= 39:
        want += [("get", b"Frontend/RaceSelect/RaceName"), ("set_str",)]
    if flag:
        want += [("get", b"Frontend/RaceSelect/ModeRightArrow"), ("set_int", int(g < LAST))]
        if g >= 8:
            want += [("get", b"Frontend/RaceSelect/Logo"), ("set_int", CATS[g - 8]["logo_frame"])]
    if sets != want or d != 0 or u.reg_read(UC_X86_REG_ESI) != 0x5151:
        fail.append(f"details g{g} flag{flag}: {sets} != {want}")
print("FAIL", fail) if fail else print("PASS course layer emulation")
sys.exit(1 if fail else 0)
