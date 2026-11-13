"""Extra Vehicle Select classes (frontend only) for a Vehicle Manager roster, e.g. "4X4 EVO".

The native registry (MRVC) keeps its three race classes: a vehicle of an extra class stays a record of its MRVC class
(the race class, opponents, Results, save guard and the loader see nothing new). Only Vehicle Select gets a fourth
(fifth, ...) class row. Research: master-rallye-re-vclass docs/sdk/NEW_CLASS_RESEARCH.md (CLASS-T4); this is the same
layer ported onto the V-CAP roster, with the class maps in the payload instead of the SDK33 caves.

gaFEScreenVehicleSelectAI (vtable 0x690B08) is a 0x34-byte heap object: +0x10 class, +0x14 selection[3],
+0x20 count[3], +0x2C PlayerID, +0x30 number of published classes. The arrays move to +0x34 selection[8] and
+0x54 count[8] in a 0x74-byte object (both allocation sites), every indexed or fixed use is rewritten (DISPLACEMENTS,
the same set a full scan of the screen code and the roster caves finds), and:

  * the payload gets frontend class maps: per class the ordered physical IDs (MRVC lists minus the extra-class IDs,
    then the extra classes) and per ID the reverse (class, local) pair; new forward/reverse map functions read them,
    and the EXE entries 0x481E20 / 0x481E50 jump there instead of to the MRVC-based payload maps;
  * the constructor tail (0x68E643, after the T1/T2 count stub) sets selection 0 and the count of every extra class;
    the base T1/T2/T3 counts become the frontend counts;
  * the class list (0x481152, before VehicleList is published) appends each extra label through the game's own
    string constructor 0x4D11D0 / list insert 0x407B30 / free 0x5B4C00, only when all three retail classes are
    published (+0x30 == 3: quick race paths; championships lock the class and never show it);
  * the Vehicle Select scene moves the extra-class widgets to their own row (Y ID = class index).
"""
from __future__ import annotations
import re, struct
from roster_v4 import Image, Rvp, egg_span, set_value, CLASSES

IMAGE_BASE, PAYLOAD_VA = 0x400000, 0x10000000
SEL, CNT, MAX_CLASSES, OBJECT_SIZE = 0x34, 0x54, 8, 0x74
ALLOCATIONS = (0x480A97, 0x401BE3)                       # PUSH 0x34 imm8 operand
# (instruction VA, offset of its displacement byte): selection[] / count[] uses.
DISPLACEMENTS = (
    (0x480A41, 2), (0x480A44, 2), (0x480A47, 2),             # ctor: selection[0..2] = 0
    (0x68E635, 2), (0x68E63C, 2), (0x480A62, 2),             # ctor: count T1/T2 (G.1 stub), T3
    (0x480BE4, 3), (0x68EFD9, 3),                            # XValue publication (retail, J.2 re-entry)
    (0x481902, 3), (0x481965, 3), (0x481C92, 3), (0x481CC0, 3), (0x481CC4, 3),
    (0x481F5E, 3), (0x481F79, 3), (0x481F7D, 3), (0x481F84, 3), (0x481F88, 3),
    (0x481FA4, 3), (0x481FA8, 3),                            # publisher, arrows, carousel
    (0x481E31, 2), (0x481E38, 2), (0x481E3F, 2),             # retail forward map (unreachable: entry jumps out)
    (0x481E63, 2), (0x481E77, 2), (0x481E86, 2),             # retail reverse map (unreachable)
)
FORWARD, REVERSE, REVERSE_TAIL = 0x481E20, 0x481E50, 0x481E89
CTOR_TAIL, CTOR_RESUME = 0x68E643, 0x480A55
CLASS_LIST = 0x481152
STRING_FROM_CSTR, LIST_INSERT, GAME_FREE = 0x4D11D0, 0x407B30, 0x5B4C00
COUNT_SITES = {"T1": 0x68E638, "T2": 0x68E63F, "T3": 0x480A65}   # imm32 of mov [esi+cnt],imm


def relocate(disp: int) -> int:
    if 0x14 <= disp < 0x20:
        return disp - 0x14 + SEL
    if 0x20 <= disp < 0x2C:
        return disp - 0x20 + CNT
    raise ValueError(f"{disp:#x} is not a Vehicle Select class array field")


def own(img: Image, va: int, data: bytes):
    """Write EXE bytes byte by byte: inside an owned RVP operation the operation changes; an unowned byte that must
    change becomes part of a new exact-preimage operation over untouched retail .text (file offset == RVA)."""
    run = None
    def flush():
        nonlocal run
        if run:
            rva, buf = run
            run = None
            if not 0x1000 <= rva < 0x28E000 or img.recon[rva:rva + len(buf)] != img.exe[rva:rva + len(buf)]:
                raise ValueError(f"{rva + IMAGE_BASE:#x}: not untouched .text")
            img.rvp.ops.append({"fo": rva, "rva": rva, "len": len(buf), "flags": 0, "page": 1,
                                "before": img.exe[rva:rva + len(buf)], "after": bytearray(buf)})
            img.recon[rva:rva + len(buf)] = buf
    for i, byte in enumerate(data):
        rva = va - IMAGE_BASE + i
        op = next((o for o in img.rvp.ops if o["flags"] != 1 and o["rva"] <= rva < o["rva"] + o["len"]), None)
        if op:
            flush()
            op["after"][rva - op["rva"]] = byte
            img.recon[op["fo"] + rva - op["rva"]] = byte
        elif img.recon[rva] != byte:
            if run and run[0] + len(run[1]) == rva:
                run[1].append(byte)
            else:
                flush()
                run = (rva, bytearray([byte]))
        else:
            flush()
    flush()


def read_exe(img: Image, va: int, n: int) -> bytes:
    return bytes(img.recon[va - IMAGE_BASE:va - IMAGE_BASE + n])


def jmp_target(img: Image, va: int) -> int:
    b = read_exe(img, va, 5)
    if b[0] != 0xE9:
        raise ValueError(f"expected JMP at {va:#x}")
    return va + 5 + struct.unpack("<i", b[1:])[0]


def rel32(at: int, target: int) -> bytes:
    return struct.pack("<i", target - (at + 5))


class Code:
    def __init__(self, img: Image):
        self.img, self.buf, self.fix = img, bytearray(), []

    def emit(self, raw: bytes):
        self.buf += raw

    def branch(self, opcode: bytes, target: int):        # call/jmp rel32 to an absolute VA, fixed after placement
        self.buf += opcode
        self.fix.append((len(self.buf), target))
        self.buf += b"\0\0\0\0"

    def place(self) -> int:
        va = self.img.append(bytes(self.buf))
        for end_of_opcode, target in self.fix:
            at = va - PAYLOAD_VA + end_of_opcode
            struct.pack_into("<i", self.img.payload, at, target - (va + end_of_opcode + 4))
        return va


def plan_classes(mrvc: dict, extra: list[dict]) -> tuple[list[str], dict]:
    if not extra:
        raise ValueError("no extra classes")
    if len(extra) > MAX_CLASSES - 3:
        raise ValueError(f"at most {MAX_CLASSES - 3} extra classes")
    taken, out = set(), {}
    for k, cls in enumerate(extra):
        ids = [int(i) for i in cls["ids"]]
        if not ids or len(set(ids)) != len(ids) or taken & set(ids):
            raise ValueError(f"extra class {cls['label']}: empty or overlapping IDs")
        if not all(any(i in mrvc[c] for c in CLASSES) for i in ids):
            raise ValueError(f"extra class {cls['label']}: IDs must be offered by an MRVC class")
        if not re.fullmatch(r"[A-Z0-9 ()\-]{1,24}", cls["label"]):
            raise ValueError(f"extra class label {cls['label']!r}: A-Z, 0-9, space, ()- only")
        taken |= set(ids)
    order = list(CLASSES) + [f"X{k}" for k in range(len(extra))]
    for c in CLASSES:
        out[c] = [i for i in mrvc[c] if i not in taken]
        if not out[c]:
            raise ValueError(f"{c} would be empty")
    for k, cls in enumerate(extra):
        out[f"X{k}"] = [int(i) for i in cls["ids"]]
    return order, out


def apply_native(v1: bytes, exe: bytes, writable, mrvc: dict, extra: list[dict]) -> tuple[bytes, dict]:
    """roster.mrvr v1 (classes already rebuilt) -> v1 with the extra Vehicle Select classes."""
    order, frontend = plan_classes(mrvc, extra)
    rvp_off, rvp_size, ext_off, ext_size = struct.unpack_from("<4I", v1, 144)
    if rvp_off != 256 or ext_off != rvp_off + rvp_size or ext_off + ext_size != len(v1):
        raise ValueError("unexpected MRVR v1 layout")
    img = Image(v1[ext_off:], Rvp(v1[rvp_off:ext_off]), writable, exe)
    count = struct.unpack_from("<I", v1, 168)[0]

    # Object size and every class-array displacement.
    for va in ALLOCATIONS:
        if read_exe(img, va - 1, 2) != b"\x6a\x34":
            raise ValueError(f"allocation PUSH 0x34 expected at {va - 1:#x}")
        own(img, va, bytes([OBJECT_SIZE]))
    for va, at in DISPLACEMENTS:
        disp = read_exe(img, va + at, 1)[0]
        own(img, va + at, bytes([relocate(disp)]))

    # Base frontend counts (the MRVC counts include the extra-class IDs).
    for c, site in COUNT_SITES.items():
        if struct.unpack("<I", read_exe(img, site, 4))[0] != len(mrvc[c]):
            raise ValueError(f"{c} count owner at {site:#x} differs from the MRVC count")
        own(img, site, struct.pack("<I", len(frontend[c])))

    # Frontend class maps.
    n = len(order)
    tables = []
    for c in order:
        tables.append(img.append(struct.pack(f"<{len(frontend[c])}I", *frontend[c])))
    counts_va = img.append(struct.pack(f"<{n}I", *[len(frontend[c]) for c in order]))
    tables_va = img.append(struct.pack(f"<{n}I", *tables))
    reverse = {p: (k, i) for k, c in enumerate(order) for i, p in enumerate(frontend[c])}
    rc_va = img.append(struct.pack(f"<{count}I", *[reverse.get(p, (0, 0))[0] for p in range(count)]))
    rl_va = img.append(struct.pack(f"<{count}I", *[reverse.get(p, (0, 0))[1] for p in range(count)]))

    # forward (thiscall): physical ID of the current class/selection, -1 when out of range.
    f = Code(img)
    f.emit(b"\x8b\x41\x10" + b"\x83\xf8" + bytes([n]) + b"\x73\x18")                 # mov eax,[ecx+10]; cmp eax,n; jae fail
    f.emit(b"\x8b\x54\x81" + bytes([SEL]))                                            # mov edx,[ecx+eax*4+SEL]
    f.emit(b"\x3b\x14\x85" + struct.pack("<I", counts_va) + b"\x73\x0b")              # cmp edx,[eax*4+counts]; jae fail
    f.emit(b"\x8b\x04\x85" + struct.pack("<I", tables_va))                            # mov eax,[eax*4+tables]
    f.emit(b"\x8b\x04\x90\xc3")                                                       # mov eax,[eax+edx*4]; ret
    f.emit(b"\xb8\xff\xff\xff\xff\xc3")                                               # fail: mov eax,-1; ret
    forward_va = f.place()
    # reverse (thiscall, 1 arg = physical ID): class and selection of that ID, then the retail tail (pop esi; ret 4).
    r = Code(img)
    r.emit(b"\x8b\x44\x24\x04" + b"\x3d" + struct.pack("<I", count) + b"\x73\x1d")   # mov eax,[esp+4]; cmp eax,count; jae out
    r.emit(b"\x56\x8b\xf1")                                                           # push esi; mov esi,ecx
    r.emit(b"\x8b\x14\x85" + struct.pack("<I", rc_va))                                # mov edx,[eax*4+rc]
    r.emit(b"\x89\x56\x10")                                                           # mov [esi+10],edx
    r.emit(b"\x8b\x04\x85" + struct.pack("<I", rl_va))                                # mov eax,[eax*4+rl]
    r.emit(b"\x89\x44\x96" + bytes([SEL]))                                            # mov [esi+edx*4+SEL],eax
    r.branch(b"\xe9", REVERSE_TAIL)
    r.emit(b"\xc2\x04\x00")                                                           # out: ret 4
    reverse_va = r.place()
    for entry, target in ((FORWARD, forward_va), (REVERSE, reverse_va)):
        old = jmp_target(img, entry)
        if not PAYLOAD_VA <= old < PAYLOAD_VA + ext_size:
            raise ValueError(f"{entry:#x} does not enter the roster payload")
        own(img, entry + 1, rel32(entry, target))

    # Constructor tail: selection/count of every extra class.
    resume = jmp_target(img, CTOR_TAIL)
    if resume != CTOR_RESUME:
        raise ValueError("constructor stub tail changed")
    c = Code(img)
    for k in range(3, n):
        c.emit(b"\xc7\x46" + bytes([SEL + 4 * k]) + struct.pack("<I", 0))
        c.emit(b"\xc7\x46" + bytes([CNT + 4 * k]) + struct.pack("<I", len(frontend[order[k]])))
    c.branch(b"\xe9", CTOR_RESUME)
    own(img, CTOR_TAIL + 1, rel32(CTOR_TAIL, c.place()))

    # Class list: append the labels when T1..T3 are all published.
    labels = [img.append(cls["label"].encode("ascii") + b"\0") for cls in extra]
    previous = jmp_target(img, CLASS_LIST)
    lst = Code(img)
    lst.emit(b"\x83\x7f\x30\x03")                                                     # cmp dword [edi+30],3
    lst.emit(b"\x0f\x85"); skip_at = len(lst.buf); lst.emit(b"\0\0\0\0")             # jne skip
    for label in labels:
        lst.emit(b"\x83\xec\x04" + b"\x68" + struct.pack("<I", label) + b"\x8d\x4c\x24\x04")
        lst.branch(b"\xe8", STRING_FROM_CSTR)
        lst.emit(bytes.fromhex("8b46088d0c24516a01508bce"))
        lst.branch(b"\xe8", LIST_INSERT)
        lst.emit(bytes.fromhex("ff3424"))
        lst.branch(b"\xe8", GAME_FREE)
        lst.emit(bytes.fromhex("83c408"))
    lst.emit(b"\xc7\x47\x30" + struct.pack("<I", n))                                  # mov dword [edi+30],n
    struct.pack_into("<i", lst.buf, skip_at, len(lst.buf) - (skip_at + 4))
    lst.branch(b"\xe9", previous)
    own(img, CLASS_LIST + 1, rel32(CLASS_LIST, lst.place()))

    # Selection publisher bound = the largest frontend class.
    bound = max(len(mrvc[c]) for c in CLASSES)
    hits = [m.start() for m in re.finditer(rb"\x81\xfe" + struct.pack("<I", bound) + rb"\x0f\x8c", bytes(img.payload))]
    if len(hits) != 1:
        raise ValueError("selection publisher bound not found exactly once")
    img.payload[hits[0] + 2:hits[0] + 6] = struct.pack("<I", max(len(v) for v in frontend.values()))

    rvp = img.rvp.build()
    payload = bytes(img.payload)
    header = bytearray(v1[:256])
    if len(payload) > struct.unpack_from("<I", header, 20)[0]:
        raise ValueError("native payload exceeds the roster allocation")
    struct.pack_into("<I", header, 24, len(payload))
    struct.pack_into("<4I", header, 144, 256, len(rvp), 256 + len(rvp), len(payload))
    from vehicle_roster_build import fnv64
    struct.pack_into("<Q", header, 160, fnv64(rvp + payload))
    return bytes(header) + rvp + payload, {"order": order, "classes": frontend,
                                           "labels": [c["label"] for c in extra],
                                           "maps": {"forward": hex(forward_va), "reverse": hex(reverse_va)}}


def apply_scene(xml: str, mrvc: dict, info: dict) -> str:
    """Vehicle Select widgets: base classes keep their own order without the extra IDs; extra-class widgets get their
    own row (Y ID = class index) and names T<4+k>_Car<n>."""
    order, frontend = info["order"], info["classes"]
    blocks, spans = {}, []
    for c in CLASSES:
        for n, physical in enumerate(mrvc[c]):
            a, b = egg_span(xml, f"{c}_Car{n + 1}")
            blocks[physical] = (c, xml[a:b])
            spans.append((a, b))
    first, last = min(a for a, _ in spans), max(b for _, b in spans)
    between = xml[first:last]
    for a, b in sorted(spans, reverse=True):
        between = between[:a - first] + between[b - first:]
    if between.strip():
        raise ValueError("carousel widgets are not contiguous in VehicleSelect.xml")
    out = []
    for k, c in enumerate(order):
        name = c if c in CLASSES else f"T{4 + int(c[1:])}"
        for n, physical in enumerate(frontend[c]):
            block = blocks[physical][1]
            block = re.sub(r'(<Egg Name=")T\d+_Car\d+(">)', lambda m: m[1] + f"{name}_Car{n + 1}" + m[2], block, count=1)
            block = set_value(block, "X ID", str(n))
            block = set_value(block, "Y ID", str(k))
            block = re.sub(r"Frontend/VehicleSelect/Button\d+XPos", f"Frontend/VehicleSelect/Button{n}XPos", block)
            out.append(block)
    sep = xml[spans[0][1]:spans[1][0]] if len(spans) > 1 else "\n"
    return xml[:first] + sep.join(out) + xml[last:]
