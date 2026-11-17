"""Course registry layer for a Vehicle Manager roster (roster.mrvr v1): new races in their own Quick Race category.

The COURSE-CAP2 native composition (master-rallye-re-course src/master_rallye/course_runtime.py append_native, owner
tested with StudioFranceEdit through the V-CAP launcher) is applied here to the roster image that the dinput8
VehicleRoster module installs, like tools/frontend_classes.py does for extra Vehicle Select classes. On top of CAP2:

  * a ninth Quick Race mode ("category") after the eight retail modes: RaceSelect object 0x74 -> 0x78 bytes
    (factory 0x47E1F0 PUSH 0x74), position[8] at +0x34 (unused gap in the retail object, contiguous with
    position[0..7] at +0x14), count[8] at +0x74; forward/reverse maps cover nine groups;
  * the mode list (Broker list Frontend/RaceSelect/RaceList, built in the screen init 0x47E2D0 with the object in EBX
    and the list in ESI) gets the category label at 0x47E605 only when all eight retail modes are present (the retail
    code uses the list position as the mode index); +0x50 (unused) of the object records whether it was appended;
  * the model cache budget (0x53BA96 MOV [edi+14h], 32 MB; the Invitation/CAP2 contract) is raised to 96 MB: imported
    open-terrain maps are larger than the retail stages and must not be evicted while the race loads;
  * the details publisher wrapper sets Frontend/RaceSelect/Logo to the category logo frame and recomputes
    Frontend/RaceSelect/ModeRightArrow (the retail one stops at mode 7).

New races are Quick Race only (CAP2 admission), keep their own best-time keys (Progress/BestTimes/CourseRegistryV1/<key>)
and own screenshot pairs. Retail race IDs 0..38, their scenes, menus, competitions and progress are unchanged.
"""
from __future__ import annotations

import copy
import json
import re
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

from roster_v4 import Image, Rvp
from frontend_classes import own, read_exe, IMAGE_BASE, PAYLOAD_VA

HERE = Path(__file__).resolve().parent
RETAIL_CATALOG = HERE / "evo2_tracks" / "retail_course_catalog.json"

STOCK_MENU = [list(range(10, 13)), list(range(13, 16)), list(range(16, 19)), list(range(19, 22)), list(range(22, 25)),
              list(range(25, 36)), list(range(10)), list(range(36, 39))]
STOCK_STAGES = [list(range(10, 13)), list(range(13, 16)), list(range(16, 19)), list(range(19, 22)),
                list(range(22, 25)), list(range(36, 39))]
GROUPS = 9                                   # 8 retail modes + the category (one category; see categories_of)
CATEGORY = 8                                 # first extra mode
MAX_CATEGORIES = 4                           # RCX-CAT2: position[8..11] = +0x34..+0x40 (unused), flag +0x50
REPEAT_DIR, REPEAT_NEXT = 0x44, 0x48         # RCX-CAT2: held-arrow repeat state in the RaceSelect object (unused fields)
REPEAT_HOOK = 0x47EA51                       # E8 -> 0x45D930: the screen's per-frame action poll (UI/Control)
ACTION_POLL = 0x45D930
IAT_GETASYNCKEYSTATE, IAT_GETTICKCOUNT = 0x68F308, 0x68F0D8
REPEAT_DELAY_MS, REPEAT_RATE_MS = 300, 50
REPEAT_COUNT = 0x4C                          # repeats since the press: acceleration (x2 after 4, x4 after 10)
RACE_STEP, UI_STATE, UI_ACTIVE = 0x47F440, 0x525A80, 0x525800
FACTORY_PUSH = 0x47E206                      # 6A 74
LIST_HOOK = 0x47E605                         # 68 D4 70 6B 00  push "Frontend/RaceSelect/RaceList"
LIST_RESUME = 0x47E60A
FLAG = 0x50                                  # object field: category appended
LOGO_KEY, RIGHT_ARROW_KEY = 0x6B7214, 0x6B71CC   # "Frontend/RaceSelect/Logo", ".../ModeRightArrow"
STRING_ID, BROKER_GET, BROKER_SET_INT = 0x4D0580, 0x4D8EC0, 0x4D8000
STRING_FROM_CSTR, LIST_INSERT, GAME_FREE = 0x4D11D0, 0x407B30, 0x5B4C00


class Emitter:
    """x86 rel32/imm32 emitter (the CAP2/V-CAP _CodeImage contract)."""

    def __init__(self, base_va: int):
        self.base_va, self.code, self.labels, self.rel32, self.imm32 = base_va, bytearray(), {}, [], []

    @property
    def va(self):
        return self.base_va + len(self.code)

    def emit(self, raw):
        self.code.extend(raw)

    def label(self, name):
        if name in self.labels:
            raise ValueError(f"duplicate label {name}")
        self.labels[name] = len(self.code)

    def align(self, n=16):
        while len(self.code) % n:
            self.emit(b"\x90")

    def _rel(self, opcode, target):
        self.emit(opcode + b"\0\0\0\0")
        self.rel32.append((len(self.code) - 4, len(self.code), target))

    def call(self, t): self._rel(b"\xe8", t)
    def jump(self, t): self._rel(b"\xe9", t)
    def jne(self, t): self._rel(b"\x0f\x85", t)
    def je(self, t): self._rel(b"\x0f\x84", t)
    def ja(self, t): self._rel(b"\x0f\x87", t)
    def jb(self, t): self._rel(b"\x0f\x82", t)
    def jae(self, t): self._rel(b"\x0f\x83", t)
    def jl(self, t): self._rel(b"\x0f\x8c", t)
    def jg(self, t): self._rel(b"\x0f\x8f", t)
    def js(self, t): self._rel(b"\x0f\x88", t)

    def push_literal(self, label):
        self.emit(b"\x68\0\0\0\0")
        self.imm32.append((len(self.code) - 4, label))

    def build(self) -> bytes:
        out = bytearray(self.code)
        for at, name in self.imm32:
            struct.pack_into("<I", out, at, self.base_va + self.labels[name])
        for at, nxt, target in self.rel32:
            tva = self.base_va + self.labels[target] if isinstance(target, str) else target
            struct.pack_into("<i", out, at, tva - (self.base_va + nxt))
        return bytes(out)


def u(n):
    return struct.pack("<I", n & 0xFFFFFFFF)


def storage(vehicle_count, race_count):
    base = 4 + vehicle_count * 52
    return base, base + race_count * 44


def categories_of(category: dict) -> list[dict]:
    """RCX-CAT2: {"categories": [{label, logo_frame}, ...], "flag_frame"} or the single-category form {label, logo_frame}."""
    cats = category.get("categories") or [{"label": category["label"], "logo_frame": category["logo_frame"]}]
    if not 1 <= len(cats) <= MAX_CATEGORIES:
        raise ValueError(f"1..{MAX_CATEGORIES} course categories supported, got {len(cats)}")
    return cats


def plan_catalog(new_races: list[dict], vehicle_count: int, categories: int = 1) -> dict:
    """Retail 39 + new races, each in its category group 8 + race["category"] (positions in the given order)."""
    retail = json.loads(RETAIL_CATALOG.read_text())
    races = copy.deepcopy(retail["races"])
    for k, r in enumerate(new_races):
        rid = 39 + k
        key = r["progress_key"]
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", key) or any(x.get("progress_key") == key for x in races[39:]):
            raise ValueError(f"race {r.get('title')}: invalid or duplicate progress key {key!r}")
        # The Race Select title font has capitals only: "Clashin Darroch" rendered as "C D" (owner, 2026-11-16).
        title = r["title"].upper()
        if not title or len(title) > 60 or not all(32 <= ord(c) < 127 for c in title):
            raise ValueError(f"race title must be 1..60 printable ASCII characters: {title!r}")
        fields = [rid, 0, 0, 0, 0, struct.unpack("<I", struct.pack("<f", float(r.get("distance_km", 5.0))))[0], 0,
                  0xFFFFFFFF, 0xFFFFFFFF]
        cat = int(r.get("category", 0))
        if not 0 <= cat < categories:
            raise ValueError(f"race {title}: category {cat} outside 0..{categories - 1}")
        races.append({"id": rid, "scene": r["scene"], "icont": r["icont"], "native_fields": fields, "title": title,
                      "progress_key": key, "screenshot_pair": int(r["screenshot_pair"]), "category": cat})
    menu = copy.deepcopy(STOCK_MENU) + [[r["id"] for r in races[39:] if r["category"] == k] for k in range(categories)]
    if any(not rows for rows in menu[8:]):
        raise ValueError("every course category needs at least one race")
    reverse = {i: (g, p) for g, rows in enumerate(menu) for p, i in enumerate(rows)}
    if sorted(reverse) != list(range(len(races))):
        raise ValueError("menu and registry are not bijective")
    base, size = storage(vehicle_count, len(races))
    return {"races": races, "menu_groups": menu, "reverse_menu": [reverse[i] for i in range(len(races))],
            "stage_schedules": copy.deepcopy(STOCK_STAGES),
            "layout": {"vehicle_count": vehicle_count, "race_count": len(races), "race_base": base, "allocation_size": size}}


def compose(img: Image, exe: bytes, catalog: dict, category: dict) -> dict:
    """CAP2 append_native + category, applied to the roster image. Returns a report."""
    layout = catalog["layout"]
    count, base = layout["race_count"], layout["race_base"]
    cats = categories_of(category)
    groups = CATEGORY + len(cats)                        # RCX-CAT2: one extra Quick Race mode per category
    if len(catalog["menu_groups"]) != groups:
        raise ValueError("catalog groups differ from the categories")
    while len(img.payload) % 16:
        img.payload.append(0)
    c = Emitter(PAYLOAD_VA + len(img.payload))
    work = bytearray(img.recon)
    ops = []

    def off(va, n):
        o = va - IMAGE_BASE
        if not 0x1000 <= o or o + n > 0x28E000 + 0x1000:
            raise ValueError(f"{va:#x} outside .text")
        return o

    def patch(va, before, after, name):
        o = off(va, len(before))
        if bytes(work[o:o + len(before)]) != before:
            raise ValueError(f"course hook preimage mismatch: {name} at {va:08x}: {bytes(work[o:o + len(before)]).hex()} != {before.hex()}")
        if len(before) != len(after):
            raise ValueError("fixed-width operation required")
        work[o:o + len(before)] = after
        ops.append({"name": name, "va": hex(va), "before": before.hex(), "after": after.hex()})

    def branch(va, target, opcode=0xE9):
        return bytes([opcode]) + struct.pack("<i", target - va - 5)

    hooks = []

    def hook(va, before, label):
        hooks.append((va, before, label))

    # ---- registry lifetime and records (CAP2) -----------------------------------------------------------------
    for name, va, cont, lea in [("construct", 0x458D0E, 0x458D16, b"\x8d\x8e"), ("destroy", 0x458E28, 0x458E30, b"\x8d\x86")]:
        c.label(name); c.emit(b"\x68" + u(count) + lea + u(base)); c.jump(cont)
        hook(va, b"\x6a\x27" + lea + u(base), name)
    c.label("unwind"); c.emit(b"\x68" + u(count) + b"\x6a\x2c\x8b\x45\xf0"); c.jump(0x6867B2)
    hook(0x6867AB, b"\x6a\x27\x6a\x2c\x8b\x45\xf0", "unwind")
    patch(0x45A3E0, u(storage(layout["vehicle_count"], 39)[1]), u(layout["allocation_size"]), "shared_allocation")
    c.label("initialize_additions"); c.call(0x45A330)
    for r in catalog["races"][39:]:
        f = r["native_fields"]
        for v in reversed(f[7:]):
            c.emit(b"\x68" + u(v))
        c.emit(b"\x51\x8b\xcc"); c.push_literal("scene_" + str(r["id"])); c.call(STRING_FROM_CSTR)
        for v in reversed(f[:7]):
            c.emit(b"\x68" + u(v))
        c.emit(b"\x8d\x8e" + u(base + r["id"] * 44)); c.call(0x45A330)
    c.jump(0x459FDC)
    hook(0x459FD7, branch(0x459FD7, 0x45A330, 0xE8), "initialize_additions")

    # ---- menu maps over nine groups ----------------------------------------------------------------------------
    c.label("menu_forward"); c.emit(b"\x8b\x41\x10\x83\xf8" + bytes([groups - 1])); c.ja("invalid")
    c.emit(b"\x8b\x54\x81\x14\x3b\x14\x85"); c.imm32.append((len(c.code), "menu_counts")); c.emit(b"\0" * 4)
    c.jae("invalid")
    c.emit(b"\x8b\x04\x85"); c.imm32.append((len(c.code), "menu_pointers")); c.emit(b"\0" * 4 + b"\x8b\x04\x90\xc3")
    hook(0x47F2B0, b"\x8b\x41\x10\x83\xf8\x07", "menu_forward")
    c.label("menu_reverse"); c.emit(b"\x8b\x44\x24\x04\x3d" + u(count)); c.jae("invalid")
    for g, rows in enumerate(catalog["menu_groups"]):
        if g >= len(STOCK_MENU) or rows != STOCK_MENU[g]:
            c.emit(b"\xc7\x81" + u(0x54 + g * 4) + u(len(rows)))          # count[g] (disp32: g >= 11 passes 0x7F)
    c.emit(b"\x8b\x14\x85"); c.imm32.append((len(c.code), "reverse_group")); c.emit(b"\0" * 4 + b"\x89\x51\x10\x8b\x04\x85")
    c.imm32.append((len(c.code), "reverse_local")); c.emit(b"\0" * 4 + b"\x89\x44\x91\x14\xc2\x04\x00")
    hook(0x47F320, b"\x8b\x44\x24\x04\x83\xf8\x0a", "menu_reverse")
    c.label("menu_position_bound"); c.emit(b"\x81\xfe" + u(max(map(len, catalog["menu_groups"])))); c.emit(b"\x0f\x8c")
    c.rel32.append((len(c.code), len(c.code) + 4, 0x47ECBA)); c.emit(b"\0" * 4); c.jump(0x47ED09)
    hook(0x47ED04, b"\x83\xfe\x0b\x7c\xb1", "menu_position_bound")
    c.label("menu_image_pair"); c.emit(b"\x8b\xac\x38" + u(base + 4) + b"\x83\xfb\x27"); c.jb("image_pair_done")
    c.emit(b"\x8b\x2c\x9d"); c.imm32.append((len(c.code), "image_pairs")); c.emit(b"\0" * 4)
    c.label("image_pair_done"); c.jump(0x47ED5A)
    hook(0x47ED53, b"\x8b\xac\x38" + u(base + 4), "menu_image_pair")

    # ---- best times of new races (CAP2) ------------------------------------------------------------------------
    cs = Cs(CS_ARCH_X86, CS_MODE_32)

    def clone_progress(start, size, label):
        c.align(); c.label(label); new = c.va
        raw = bytearray(exe[start - IMAGE_BASE:start - IMAGE_BASE + size])
        for ins in cs.disasm(bytes(raw), start):
            at = ins.address - start
            if ins.bytes[0] == 0xE8:
                target = ins.address + 5 + struct.unpack_from("<i", ins.bytes, 1)[0]
                struct.pack_into("<i", raw, at + 1, target - (new + at + 5))
        marker = u(0x6F6780)
        if raw.count(marker) != 1:
            raise ValueError("native progress table operand changed")
        at = raw.index(marker); raw[at:at + 4] = b"\0" * 4
        c.imm32.append((len(c.code) + at, "progress_keys")); c.emit(bytes(raw))
    for original, size, label in [(0x4B0000, 133, "get_race_best"), (0x4AFF80, 128, "set_race_best")]:
        c.label(label + "_dispatch"); c.emit(b"\x81\x7c\x24\x04" + u(39)); c.jb(original)
        c.emit(b"\x81\x7c\x24\x04" + u(count)); c.jae("invalid")
        if label == "get_race_best":
            # A key missing from the save reads as 0.0 (Broker creates it on demand): report "no time" (86400 s)
            # instead, so the first finish is stored as the record (CAP2 seeded the save for the same reason).
            c.emit(b"\xff\x74\x24\x04"); c.call(label)                                # push [esp+4]; call get
            c.emit(b"\x83\xec\x04\xd9\x14\x24\x83\x3c\x24\x00"); c.jne("best_keep")   # sub esp,4; fst [esp]; cmp [esp],0
            c.emit(b"\xdd\xd8\xd9\x05"); c.imm32.append((len(c.code), "no_time")); c.emit(b"\0" * 4)   # fstp st0; fld [no_time]
            c.label("best_keep"); c.emit(b"\x83\xc4\x04\xc2\x04\x00")                 # add esp,4; ret 4
        else:
            c.jump(label)
        clone_progress(original, size, label)
    for start, size in [(0x458870, 212), (0x449D40, 336), (0x4501D0, 311), (0x45B3F0, 288),
                        (0x45EB30, 1451), (0x460B50, 1734), (0x47ED10, 1387)]:
        for ins in cs.disasm(bytes(work[start - IMAGE_BASE:start - IMAGE_BASE + size]), start):
            if ins.bytes[0] != 0xE8:
                continue
            target = ins.address + 5 + struct.unpack_from("<i", ins.bytes, 1)[0]
            if target in (0x4B0000, 0x4AFF80):
                lbl = ("get" if target == 0x4B0000 else "set") + "_race_best_dispatch"
                hooks.append((ins.address, bytes(ins.bytes), ("call", lbl)))

    # ---- details: title of new races, category logo and mode arrow ----------------------------------------------
    c.label("publish_details"); c.emit(b"\x56\x8b\xf1\x83\xec\x08"); c.call(0x47ED10)
    c.emit(b"\x8b\xce"); c.call("menu_forward"); c.emit(b"\x83\xf8\x27"); c.jb("details_category")
    c.emit(b"\x8b\x04\x85"); c.imm32.append((len(c.code), "title_pointers")); c.emit(b"\0" * 4)
    c.emit(b"\x50\x8d\x4c\x24\x08"); c.call(STRING_ID)
    c.emit(b"\x68" + u(0x6B7230) + b"\x8d\x4c\x24\x04"); c.call(STRING_ID)
    c.emit(b"\x8d\x54\x24\x04\x8d\x04\x24\x52\x50"); c.call(BROKER_GET); c.emit(b"\x8b\xc8"); c.call(0x4D85F0)
    c.label("details_category")
    c.emit(b"\x83\x7e" + bytes([FLAG]) + b"\x01"); c.jne("details_done")             # cmp dword [esi+50],1
    # ModeRightArrow = mode < last mode
    c.emit(b"\x31\xc0\x83\x7e\x10" + bytes([groups - 1]) + b"\x0f\x9c\xc0")         # xor eax,eax; cmp [esi+10],last; setl al
    c.emit(b"\x50\x68" + u(RIGHT_ARROW_KEY) + b"\x8d\x4c\x24\x08"); c.call(STRING_ID)  # push eax; push key; lea ecx,[esp+8]
    c.emit(b"\x8d\x44\x24\x04\x50"); c.call(BROKER_GET); c.emit(b"\x8b\xc8"); c.call(BROKER_SET_INT)
    for k, cat in enumerate(cats):                                                   # category k = mode 8 + k: its logo
        c.emit(b"\x83\x7e\x10" + bytes([CATEGORY + k])); c.jne(f"details_logo_{k + 1}")
        c.emit(b"\x68" + u(int(cat["logo_frame"])) + b"\x68" + u(LOGO_KEY) + b"\x8d\x4c\x24\x08"); c.call(STRING_ID)
        c.emit(b"\x8d\x44\x24\x04\x50"); c.call(BROKER_GET); c.emit(b"\x8b\xc8"); c.call(BROKER_SET_INT)
        c.jump("details_done")
        c.label(f"details_logo_{k + 1}")
    c.label("details_done"); c.emit(b"\x83\xc4\x08\x5e\xc3")

    # ---- Quick Race flag icon (Frontend/QuickRace/FlagImageID) ---------------------------------------------------
    # 0x47A889 / 0x47B313: frame = race id, +1 from id 10 (flagsheet frame 10 is not a race icon). Retail frame 40 is
    # not a race icon either, so new races (id >= 39) map to their own appended icons: flag_frame + (id - 39).
    # Before this hook the Quick Race card showed the icon of the previous race for every new race.
    flag_base = int(category["flag_frame"])
    c.label("flag_frame"); c.emit(b"\x83\xfe\x27"); c.jb("flag_retail")             # cmp esi,39; jb retail
    c.emit(b"\x83\xee\x27\x81\xc6" + u(flag_base) + b"\xc3")                         # sub esi,39; add esi,base; ret
    c.label("flag_retail"); c.emit(b"\x83\xfe\x0a\x7c\x01\x46\xc3")                  # cmp esi,10; jl +1; inc esi; ret
    for va in (0x47A889, 0x47B313):
        hooks.append((va, b"\x83\xfe\x0a\x7c\x01\x46", ("call", "flag_frame")))
    calls = []
    for start, size in [(0x47E2D0, 1859), (0x47F3D0, 111), (0x47F440, 120)]:
        for ins in cs.disasm(bytes(work[start - IMAGE_BASE:start - IMAGE_BASE + size]), start):
            if ins.bytes[0] == 0xE8 and ins.address + 5 + struct.unpack_from("<i", ins.bytes, 1)[0] == 0x47ED10:
                calls.append(ins.address)
                hooks.append((ins.address, bytes(ins.bytes), ("call", "publish_details")))
    if len(calls) != 3:
        raise ValueError("native details caller coverage differs")

    # ---- admission (CAP2): new races are offline single-player Quick Race only ----------------------------------
    c.label("admit_selection"); c.call("menu_forward"); c.emit(b"\x83\xf8\x27"); c.jb("admission_return")
    c.emit(b"\x50"); c.call(0x4AE700); c.emit(b"\x8b\xc8"); c.call(0x4ADDB0); c.emit(b"\x84\xc0"); c.je("selection_denied")
    c.call(0x4AE700); c.emit(b"\x8b\xc8"); c.call(0x4AE2D0); c.emit(b"\x84\xc0"); c.jne("selection_denied")
    c.call(0x4ADA50); c.emit(b"\x8b\xc8"); c.call(0x4AD930); c.emit(b"\x84\xc0"); c.jne("selection_denied")
    c.emit(b"\x58"); c.label("admission_return"); c.emit(b"\xc3")
    c.label("selection_denied"); c.emit(b"\x83\xc4\x08\x6a\x30"); c.push_literal("admission_message")
    c.push_literal("admission_message"); c.emit(b"\x6a\x00\xff\x15" + u(0x68F2B4)); c.jump(0x47EC84)
    for va in (0x47EA6B, 0x47EA9D, 0x47EAF6):
        hooks.append((va, branch(va, 0x47F2B0, 0xE8), ("call", "admit_selection")))

    # ---- stage schedules (CAP2): retail cups / Invitation advance through explicit lists ------------------------
    c.label("lookup_stage"); c.emit(b"\x56\x57\x53\x8b\x44\x24\x10\x8b\x54\x24\x14\x3d" + u(len(catalog["stage_schedules"])))
    c.jae("stage_invalid")
    c.emit(b"\xbe"); c.imm32.append((len(c.code), "competitions")); c.emit(b"\0" * 4 + b"\x31\xdb")
    c.label("schedule_seek"); c.emit(b"\x39\xc3"); c.je("schedule_found"); c.emit(b"\x8b\x0e\x8d\x74\x8e\x04\x43"); c.jump("schedule_seek")
    c.label("schedule_found"); c.emit(b"\x8b\x3e\x83\xc6\x04\x31\xc0")
    c.label("stage_seek"); c.emit(b"\x39\xf8"); c.jae("stage_invalid")
    c.emit(b"\x3b\x14\x86"); c.je("stage_found"); c.emit(b"\x40"); c.jump("stage_seek")
    c.label("stage_found"); c.emit(b"\x8b\xcf\x8d\x58\x01\xba\xff\xff\xff\xff\x39\xfb"); c.jae("stage_return")
    c.emit(b"\x8b\x14\x9e"); c.label("stage_return"); c.emit(b"\xf8\x5b\x5f\x5e\xc2\x08\x00")
    c.label("stage_invalid"); c.emit(b"\xb8\xff\xff\xff\xff\x8b\xd0\xf9\x5b\x5f\x5e\xc2\x08\x00")
    c.label("cup_stage_index"); c.emit(b"\x53\x55\x50"); c.call("lookup_stage"); c.jb("invalid"); c.jump(0x45B1FF)
    hook(0x45B1FA, b"\x8b\xc5\x53\x2b\xc6", "cup_stage_index")
    c.label("cup_next_stage"); c.call(0x4AE700); c.emit(b"\x8b\xc8"); c.call(0x4AE620); c.emit(b"\x55\x50"); c.call("lookup_stage")
    c.jb("invalid"); c.emit(b"\x83\xfa\xff"); c.je(0x45B235); c.emit(b"\x8b\xea"); c.jump(0x45B39F)
    hook(0x45B22C, b"\x45\x3b\xef\x0f\x8e\x6a\x01\x00\x00", "cup_next_stage")

    # ---- model cache budget (retail 32 MB) -----------------------------------------------------------------------
    mb = int(category.get("model_cache_mb", 96))
    if not 32 <= mb <= 384:
        raise ValueError("model cache budget must be 32..384 MB")
    if mb != 32:
        patch(0x53BA99, u(32 << 20), u(mb << 20), "model_cache_budget")

    # ---- category: object size and mode list ---------------------------------------------------------------------
    patch(FACTORY_PUSH, b"\x6a\x74", b"\x6a" + bytes([0x74 + 4 * len(cats)]), "raceselect_object_size")   # count[8..] at +0x74..
    # At 0x47E605 EBX is NOT the screen object: the retail code reuses BL as a bool at 0x47E51F/0x47E5A4 (only the
    # low byte is overwritten). The object is the init's local at [esp+14h] (stored at 0x47E2EF with one push
    # outstanding; 0x47E633 reloads ESI from the same slot). Writing through EBX corrupted the heap next to the object
    # and left position[8]/flag uninitialised (owner: "invalid race/menu/stage index" on the first scroll).
    c.label("category_list")
    c.emit(b"\x53\x8b\x5c\x24\x18")                                                   # push ebx; mov ebx,[esp+18h]
    c.emit(b"\xc7\x43" + bytes([FLAG]) + u(0))                                        # mov dword [ebx+50],0
    c.emit(b"\xc7\x43" + bytes([REPEAT_DIR]) + u(0) + b"\xc7\x43" + bytes([REPEAT_NEXT]) + u(0) +
           b"\xc7\x43" + bytes([REPEAT_COUNT]) + u(0))                                   # repeat state
    c.emit(b"\x8b\x46\x08\x2b\x46\x04\x83\xf8\x20"); c.jne("category_list_done")     # 8 retail modes published?
    for k in range(len(cats)):                                                        # position[8 + k] = 0, label k
        c.emit(b"\xc7\x43" + bytes([0x14 + (CATEGORY + k) * 4]) + u(0))
        c.emit(b"\x83\xec\x04"); c.push_literal(f"category_label_{k}"); c.emit(b"\x8d\x4c\x24\x04"); c.call(STRING_FROM_CSTR)
        c.emit(bytes.fromhex("8b46088d0c24516a01508bce")); c.call(LIST_INSERT)
        c.emit(bytes.fromhex("ff3424")); c.call(GAME_FREE); c.emit(bytes.fromhex("83c408"))
    c.emit(b"\xc7\x43" + bytes([FLAG]) + u(1))
    c.label("category_list_done"); c.emit(b"\x5b\x68" + u(0x6B70D4)); c.jump(LIST_RESUME)   # pop ebx; push key
    hook(LIST_HOOK, b"\x68" + u(0x6B70D4), "category_list")

    # ---- held arrows repeat (RCX-CAT2, owner: long lists scroll slowly) -----------------------------------------
    # The screen polls one action per frame (0x45D930 -> UI/Control); a held key yields one press only. While the
    # poll is idle (-2..0) and Left/Right is held (GetAsyncKeyState), the poll returns that press again after
    # REPEAT_DELAY_MS and then every REPEAT_RATE_MS, so the native left/right cases (race or mode step, sound,
    # publish) run unchanged. -5 = left (previous), -4 = right (next). ESI = the RaceSelect object (callee-saved).
    c.label("race_repeat")
    c.emit(b"\xff\x74\x24\x04"); c.call(ACTION_POLL)                                 # push [esp+4]; call poll
    c.emit(b"\x83\xf8\xfb"); c.je("repeat_pressed"); c.emit(b"\x83\xf8\xfc"); c.je("repeat_pressed")
    c.emit(b"\x83\xf8\xfe"); c.jl("repeat_done"); c.emit(b"\x83\xf8\x00"); c.jg("repeat_done")
    c.emit(b"\x50")                                                                    # push eax (idle action)
    for vk, code in ((0x27, -4), (0x25, -5)):
        c.emit(b"\x6a" + bytes([vk]) + b"\xff\x15" + u(IAT_GETASYNCKEYSTATE) + b"\x66\xa9\x00\x80")
        c.emit(b"\xba" + u(code)); c.jne("repeat_held")                                # mov edx,code (flags kept)
    c.emit(b"\xc7\x46" + bytes([REPEAT_DIR]) + u(0) + b"\xc7\x46" + bytes([REPEAT_COUNT]) + u(0) + b"\x58\xc2\x04\x00")   # no arrow: reset
    c.label("repeat_held")
    c.emit(b"\x52\xff\x15" + u(IAT_GETTICKCOUNT) + b"\x5a")                           # push edx; GetTickCount; pop edx
    c.emit(b"\x39\x56" + bytes([REPEAT_DIR])); c.je("repeat_same")
    c.emit(b"\x89\x56" + bytes([REPEAT_DIR]) + b"\x05" + u(REPEAT_DELAY_MS) + b"\x89\x46" + bytes([REPEAT_NEXT]))
    c.emit(b"\xc7\x46" + bytes([REPEAT_COUNT]) + u(0) + b"\x58\xc2\x04\x00")
    c.label("repeat_same")
    c.emit(b"\x8b\xc8\x2b\x4e" + bytes([REPEAT_NEXT])); c.js("repeat_wait")          # now - next < 0: wait
    c.emit(b"\x83\xc0" + bytes([REPEAT_RATE_MS]) + b"\x89\x46" + bytes([REPEAT_NEXT]))
    c.emit(b"\xff\x46" + bytes([REPEAT_COUNT]) + b"\x83\x7e" + bytes([REPEAT_COUNT]) + b"\x04"); c.jl("repeat_fire")
    c.emit(b"\x52"); c.call(UI_STATE); c.emit(b"\x8b\xc8"); c.call(UI_ACTIVE); c.emit(b"\x83\xf8\x02"); c.jne("repeat_extra_done")
    for k in range(3):
        if k == 1:
            c.emit(b"\x83\x7e" + bytes([REPEAT_COUNT]) + b"\x0a"); c.jl("repeat_extra_done")
        c.emit(b"\x8b\x14\x24\x33\xc0\x83\xfa\xfb\x0f\x94\xc0\x50\x8b\xce"); c.call(RACE_STEP)   # left -> 1, right -> 0
    c.label("repeat_extra_done"); c.emit(b"\x5a")
    c.label("repeat_fire")
    c.emit(b"\x83\xc4\x04\x8b\xc2\xc2\x04\x00")                                       # drop idle; eax = press; ret 4
    c.label("repeat_wait"); c.emit(b"\x58\xc2\x04\x00")
    c.label("repeat_pressed")                                                          # a real press starts the delay
    c.emit(b"\x50\xff\x15" + u(IAT_GETTICKCOUNT) + b"\x05" + u(REPEAT_DELAY_MS) + b"\x89\x46" + bytes([REPEAT_NEXT]))
    c.emit(b"\x58\x89\x46" + bytes([REPEAT_DIR]) + b"\xc7\x46" + bytes([REPEAT_COUNT]) + u(0) + b"\xc2\x04\x00")
    c.label("repeat_done"); c.emit(b"\xc2\x04\x00")
    hooks.append((REPEAT_HOOK, branch(REPEAT_HOOK, ACTION_POLL, 0xE8), ("call", "race_repeat")))

    # ---- invalid index stop, data ------------------------------------------------------------------------------
    c.label("invalid"); c.emit(b"\x6a\x10"); c.push_literal("invalid_message"); c.push_literal("invalid_message")
    c.emit(b"\x6a\x00\xff\x15" + u(0x68F2B4) + b"\x6a\x01\xff\x15" + u(0x68F114) + b"\x0f\x0b")
    c.label("invalid_message"); c.emit(b"Course Registry: invalid race/menu/stage index. Stopped before resource or progress access.\0")
    c.label("admission_message"); c.emit(b"Course Registry: these races support offline single-player Quick Race only. Selection was not changed.\0")
    for k, cat in enumerate(cats):
        c.label(f"category_label_{k}"); c.emit(cat["label"].encode("ascii") + b"\0")
    c.align(4); c.label("no_time"); c.emit(struct.pack("<f", 86400.0))
    for r in catalog["races"][39:]:
        c.label("scene_" + str(r["id"])); c.emit(r["scene"].removeprefix("DataScene/").removesuffix(".xml").encode("ascii") + b"\0")
        c.label("progress_" + str(r["id"])); c.emit(("CourseRegistryV1/" + r["progress_key"]).encode("ascii") + b"\0")
        c.label("title_" + str(r["id"])); c.emit(r["title"].encode("ascii") + b"\0")
    c.align(4); c.label("menu_counts"); c.emit(b"".join(u(len(rows)) for rows in catalog["menu_groups"]))
    c.label("menu_pointers")
    for g in range(groups):
        c.imm32.append((len(c.code), "menu_" + str(g))); c.emit(b"\0" * 4)
    for g, rows in enumerate(catalog["menu_groups"]):
        c.label("menu_" + str(g)); c.emit(b"".join(u(i) for i in rows))
    for label, index in [("reverse_group", 0), ("reverse_local", 1)]:
        c.label(label); c.emit(b"".join(u(row[index]) for row in catalog["reverse_menu"]))
    c.label("image_pairs"); c.emit(b"".join(u(r["id"] if r["id"] < 39 else r["screenshot_pair"]) for r in catalog["races"]))
    c.label("progress_keys")
    for r in catalog["races"]:
        if r["id"] < 39:
            c.emit(u(0))
        else:
            c.imm32.append((len(c.code), "progress_" + str(r["id"]))); c.emit(b"\0" * 4)
    c.label("title_pointers")
    for r in catalog["races"]:
        if r["id"] < 39:
            c.emit(u(0))
        else:
            c.imm32.append((len(c.code), "title_" + str(r["id"]))); c.emit(b"\0" * 4)
    c.label("competitions")
    for stages in catalog["stage_schedules"]:
        c.emit(u(len(stages)) + b"".join(u(i) for i in stages))
    c.align(4); c.label("descriptor")
    c.emit(b"".join(u(i) for i in [int.from_bytes(b"MRCR", "little"), 1, 64, count, 44, layout["vehicle_count"], base,
                                    layout["allocation_size"], 0x45A3C0]))
    for label in ["menu_counts", "menu_pointers", "reverse_group", "reverse_local", "progress_keys", "competitions"]:
        c.imm32.append((len(c.code), label)); c.emit(b"\0" * 4)
    c.emit(u(len(catalog["stage_schedules"])))

    # place the payload, then write every hook through the roster image (exact-preimage operations)
    for va, before, label in hooks:
        if isinstance(label, tuple):
            target = c.base_va + c.labels[label[1]]
            patch(va, before, branch(va, target, 0xE8) + b"\x90" * (len(before) - 5), label[1] + "@" + hex(va))
        else:
            patch(va, before, branch(va, c.base_va + c.labels[label]) + b"\x90" * (len(before) - 5), label)
    blob = c.build()
    at = img.append(blob)
    if at != c.base_va:
        raise ValueError("payload placement moved")
    changed = [o for o in range(len(work)) if work[o] != img.recon[o]]
    runs, run = [], None
    for o in changed:
        if run and o == run[1]:
            run[1] = o + 1
        else:
            run = [o, o + 1]; runs.append(run)
    for a, b in runs:
        own(img, IMAGE_BASE + a, bytes(work[a:b]))
    return {"operations": ops, "payload_va": hex(c.base_va), "payload_bytes": len(blob),
            "entries": {k: hex(c.base_va + v) for k, v in c.labels.items() if not k.startswith(("scene_", "progress_", "title_"))},
            "layout": layout, "category": category, "races": [{k: r[k] for k in ("id", "title", "scene", "progress_key", "screenshot_pair", "category")}
                                                               for r in catalog["races"][39:]]}


def apply_native(v1: bytes, exe: bytes, writable, new_races: list[dict], category: dict) -> tuple[bytes, dict]:
    """roster.mrvr v1 -> v1 with the course registry layer (same container rules as frontend_classes.apply_native)."""
    rvp_off, rvp_size, ext_off, ext_size = struct.unpack_from("<4I", v1, 144)
    if rvp_off != 256 or ext_off != rvp_off + rvp_size or ext_off + ext_size != len(v1):
        raise ValueError("unexpected MRVR v1 layout")
    img = Image(v1[ext_off:], Rvp(v1[rvp_off:ext_off]), writable, exe)
    vehicle_count = struct.unpack_from("<I", v1, 168)[0]
    catalog = plan_catalog(new_races, vehicle_count, len(categories_of(category)))
    info = compose(img, exe, catalog, category)
    rvp = img.rvp.build()
    payload = bytes(img.payload)
    header = bytearray(v1[:256])
    if len(payload) > struct.unpack_from("<I", header, 20)[0]:
        raise ValueError(f"native payload {len(payload)} exceeds the roster allocation {struct.unpack_from('<I', header, 20)[0]}")
    struct.pack_into("<I", header, 24, len(payload))
    struct.pack_into("<4I", header, 144, 256, len(rvp), 256 + len(rvp), len(payload))
    from vehicle_roster_build import fnv64
    struct.pack_into("<Q", header, 160, fnv64(rvp + payload))
    return bytes(header) + rvp + payload, info
