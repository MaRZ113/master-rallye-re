"""Relocatable Broker/Debug layout locator for retail-family Master Rallye EXEs.

Fixed retail VAs break as soon as a mod shifts code (widescreen, localized or
older builds) or grows a section. This module finds every address Observatory
needs from code itself: masked byte signatures for function prologues plus the
cross-references between them (route case 2 -> accessor/walker, main command
switch case 0x27 -> Broker opener, logger -> active sink global, constructor ->
sink vtable).

The same functions run over a disk image (``MappedImage.from_pe``) and over the
live module read from process memory (``MappedImage.from_reader``), so in-memory
patches are judged by what actually executes. Results carry evidence per item;
a missing item disables only the capabilities that consume it.
"""
from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass, field
from typing import Any, Callable

LOCATOR_VERSION = "broker-locator-v1"

# Retail-pristine reference VAs, used only to name the stock layout in reports
# and to keep exact-VA walker variants (R-AI1 / J.1) reachable.
RETAIL_REFERENCE = {
    "debug_logger": 0x004D0620,
    "debug_sink_global": 0x006F7B7C,
    "debug_sink_ctor": 0x0064E4C0,
    "debug_sink_vtable": 0x0069CEA8,
    "broker_editor_dump_route": 0x0065EC40,
    "broker_singleton_accessor": 0x004D8EC0,
    "broker_manager_global": 0x006F9410,
    "native_dump_walker": 0x00601D00,
    "main_command_dispatch": 0x005B09D1,
    "broker_dump_case": 0x0065ECC1,
    "broker_editor_opener_case": 0x005B1097,
    "flow_builder_opener_case": 0x005B0FEE,
    "broker_editor_opener": 0x0065E990,
    "flow_builder_opener": 0x00662D90,
}
WALKER_LENGTH = 0x600
BROKER_EDITOR_COMMAND = 0x27
FLOW_BUILDER_COMMAND = 0x30
BROKER_DUMP_CASE = 2


def _sig(text: str) -> tuple[bytes, re.Pattern[bytes]]:
    parts = text.split()
    raw = bytes(0 if p == "??" else int(p, 16) for p in parts)
    rx = b"".join(b"." if p == "??" else re.escape(bytes([int(p, 16)])) for p in parts)
    return raw, re.compile(rx, re.S)


# Formatted logger: loads the active sink and its repeat count, formats, then
# dispatches through vtable +4. Sink global is the dword at +5.
SIG_LOGGER = _sig(
    "51 55 56 8B 35 ?? ?? ?? ?? 57 8B 3D ?? ?? ?? ?? 85 F6 89 7C 24 0C 0F 84 ?? ?? ?? ?? "
    "8B 4C 24 14 8D 44 24 18 50 51 68 ?? ?? ?? ?? E8 ?? ?? ?? ?? A0 ?? ?? ?? ?? 83 C4 0C 84 C0")
SIG_LOGGER_APPEND = _sig("8B 16 68 ?? ?? ?? ?? 8B CE FF 52 04")
# Debug sink constructor: secondary vtable, primary vtable (dword at +0x10).
SIG_SINK_CTOR = _sig(
    "53 56 8B F1 57 6A 04 C7 46 04 ?? ?? ?? ?? C7 06 ?? ?? ?? ?? C7 46 04 ?? ?? ?? ?? E8")
SIG_SINK_CTOR_BUFFER = _sig("68 00 08 00 00 89 7E 0C 89 5E 10 89 5E 14 E8 ?? ?? ?? ?? "
                            "8D 88 00 08 00 00 89 46 28 89 46 2C 89 4E 24")
# Broker Editor local WM_COMMAND dispatcher: switch on id <= 10 through a table.
SIG_BROKER_ROUTE = _sig(
    "83 EC 6C 8B 44 24 70 53 33 DB 56 83 F8 0A 57 8B F1 89 5C 24 0C 0F 87 ?? ?? ?? ?? "
    "FF 24 85 ?? ?? ?? ??")
# Route case 2: accessor() ; push eax ; lea ecx,[esp+80h] ; call walker
SIG_DUMP_CASE = _sig("E8 ?? ?? ?? ?? 50 8D 8C 24 80 00 00 00 E8 ?? ?? ?? ??")
SIG_ACCESSOR = _sig("A1 ?? ?? ?? ?? 83 EC 20 53 33 DB 3B C3 0F 85")
# Main window command switch: id <= 0x58 -> byte table -> jump table.
SIG_MAIN_SWITCH = _sig("83 FE 58 0F 87 ?? ?? ?? ?? 33 C0 8A 86 ?? ?? ?? ?? FF 24 85 ?? ?? ?? ??")
# Tool case body: app() ; esi=[eax+38h] ; app() ; eax=[eax+<slot>] ; push esi ; ecx=eax ; call opener
SIG_TOOL_CASE = _sig("E8 ?? ?? ?? ?? 8B 70 38 E8 ?? ?? ?? ?? 8B 40 ?? 56 8B C8 E8 ?? ?? ?? ??")
SIG_BROKER_OPENER = _sig(
    "83 EC 68 56 8B F1 8B 4E 08 8B 41 04 85 C0 74 0E E8 ?? ?? ?? ?? B0 01 5E 83 C4 68 C2 04 00")


@dataclass
class MappedImage:
    """Bytes addressed by RVA plus section metadata (disk- or memory-backed)."""

    image_base: int
    size_of_image: int
    sections: list[dict[str, Any]]
    data: bytes
    origin: str

    @classmethod
    def from_pe(cls, raw: bytes, pe: dict[str, Any]) -> "MappedImage":
        image = bytearray(pe["size_of_image"])
        for s in pe["sections"]:
            chunk = raw[s["raw_offset"]:s["raw_offset"] + min(s["raw_size"], s["virtual_size"] or s["raw_size"])]
            image[s["rva"]:s["rva"] + len(chunk)] = chunk
        return cls(pe["image_base"], pe["size_of_image"], pe["sections"], bytes(image), "disk")

    @classmethod
    def from_reader(cls, read_rva: Callable[[int, int], bytes], pe: dict[str, Any],
                    *, module_base: int) -> "MappedImage":
        image = bytearray(pe["size_of_image"])
        for s in pe["sections"]:
            span = max(s["virtual_size"], s["raw_size"]) if s["name"] != ".rsrc" else 0
            span = min(span, pe["size_of_image"] - s["rva"])
            if span > 0 and s["characteristics"] & 0x40000000:  # readable
                image[s["rva"]:s["rva"] + span] = read_rva(s["rva"], span)
        return cls(module_base, pe["size_of_image"], pe["sections"], bytes(image), "process")

    def section_of(self, rva: int, length: int = 1) -> dict[str, Any] | None:
        for s in self.sections:
            if s["rva"] <= rva and rva + length <= s["rva"] + max(s["virtual_size"], s["raw_size"]):
                return s
        return None

    def section_name(self, rva: int, length: int = 1) -> str | None:
        s = self.section_of(rva, length)
        return s["name"] if s else None

    def is_code(self, rva: int) -> bool:
        s = self.section_of(rva)
        return bool(s and s["characteristics"] & 0x20000000)

    def u32(self, rva: int) -> int:
        return struct.unpack_from("<I", self.data, rva)[0]

    def bytes_at(self, rva: int, length: int) -> bytes:
        if rva < 0 or rva + length > len(self.data):
            raise ValueError("read outside mapped image")
        return self.data[rva:rva + length]

    def va_to_rva(self, va: int) -> int | None:
        rva = va - self.image_base
        return rva if 0 <= rva < self.size_of_image else None

    def rel32_target(self, rva_of_e8: int) -> int:
        return rva_of_e8 + 5 + struct.unpack_from("<i", self.data, rva_of_e8 + 1)[0]

    def find(self, sig: tuple[bytes, re.Pattern[bytes]], *, code_only: bool = True) -> list[int]:
        hits: list[int] = []
        for s in self.sections:
            if code_only and not s["characteristics"] & 0x20000000:
                continue
            lo, hi = s["rva"], s["rva"] + max(s["virtual_size"], s["raw_size"])
            hits.extend(m.start() for m in sig[1].finditer(self.data, lo, hi))
        return hits

    def matches(self, sig: tuple[bytes, re.Pattern[bytes]], rva: int) -> bool:
        return bool(sig[1].match(self.data, rva))


@dataclass
class LocatedLayout:
    items: dict[str, int] = field(default_factory=dict)      # name -> RVA
    lengths: dict[str, int] = field(default_factory=dict)
    problems: dict[str, str] = field(default_factory=dict)   # name -> reason
    walker: dict[str, Any] = field(default_factory=dict)
    origin: str = "disk"

    def rva(self, name: str) -> int | None:
        return self.items.get(name)

    def capabilities(self) -> dict[str, Any]:
        has = lambda *names: all(n in self.items for n in names)
        broker_read = has("debug_sink_global", "debug_sink_vtable")
        native_dump = broker_read and has("broker_editor_dump_route", "broker_singleton_accessor",
                                          "native_dump_walker")
        variant = self.walker.get("variant", "unknown")
        return {
            "broker_read": broker_read,
            "native_dump": native_dump,
            "open_broker_editor": has("main_command_dispatch", "broker_editor_opener",
                                      "broker_editor_dump_route"),
            "flow_builder": has("main_command_dispatch", "flow_builder_opener"),
            "broker_capture_active_race": broker_read,
            "active_race_native_dump_safe": native_dump,
            "post_results_native_dump_safe": self.walker.get("post_results_safe"),
            "hardened_dump": bool(self.walker.get("hardened")),
            "broker_dump_variant": ("native_hardened" if self.walker.get("hardened") else
                                    "native_stock" if variant.startswith("native_stock") else "unknown"),
            "native_dump_walker_variant": variant,
            "native_dump_requires_confirmation": native_dump and variant == "unknown",
        }

    def report(self, image_base: int) -> dict[str, Any]:
        return {
            "locator_version": LOCATOR_VERSION,
            "origin": self.origin,
            "items": {n: {"rva": f"0x{r:06X}", "va": f"0x{image_base + r:08X}",
                          "relocated": RETAIL_REFERENCE.get(n) not in (None, image_base + r)}
                      for n, r in sorted(self.items.items())},
            "problems": dict(sorted(self.problems.items())),
            "walker": dict(self.walker),
            "capabilities": self.capabilities(),
        }


def _unique(image: MappedImage, sig, name: str, layout: LocatedLayout) -> int | None:
    hits = image.find(sig)
    if len(hits) == 1:
        return hits[0]
    layout.problems[name] = "signature not found" if not hits else f"signature ambiguous ({len(hits)} hits)"
    return None


def _data_pointer(image: MappedImage, va: int, name: str, layout: LocatedLayout,
                  *, want_code: bool = False) -> int | None:
    rva = image.va_to_rva(va)
    if rva is None:
        layout.problems[name] = f"pointer 0x{va:08X} outside the module image"
        return None
    if want_code != image.is_code(rva):
        layout.problems[name] = f"pointer 0x{va:08X} is in the wrong kind of section"
        return None
    return rva


def _locate_sink(image: MappedImage, layout: LocatedLayout) -> None:
    logger = _unique(image, SIG_LOGGER, "debug_logger", layout)
    if logger is not None:
        if not SIG_LOGGER_APPEND[1].search(image.data, logger, logger + 0x80):
            layout.problems["debug_logger"] = "logger does not dispatch through sink vtable +4"
        else:
            layout.items["debug_logger"] = logger
            layout.lengths["debug_logger"] = 0x50
            sink = _data_pointer(image, image.u32(logger + 5), "debug_sink_global", layout)
            if sink is not None:
                layout.items["debug_sink_global"] = sink
    ctor = _unique(image, SIG_SINK_CTOR, "debug_sink_ctor", layout)
    if ctor is not None:
        if not SIG_SINK_CTOR_BUFFER[1].search(image.data, ctor, ctor + 0xA0):
            layout.problems["debug_sink_ctor"] = "constructor buffer layout (+0x24/+0x28/+0x2C) differs"
            return
        layout.items["debug_sink_ctor"] = ctor
        layout.lengths["debug_sink_ctor"] = 0x98
        vt = _data_pointer(image, image.u32(ctor + 0x10), "debug_sink_vtable", layout)
        if vt is not None:
            # Slot 0 clear / slot 1 append must be code.
            slots = [image.va_to_rva(image.u32(vt + 4 * i)) for i in (0, 1)]
            if any(s is None or not image.is_code(s) for s in slots):
                layout.problems["debug_sink_vtable"] = "vtable slots 0/1 are not code"
            else:
                layout.items["debug_sink_vtable"] = vt
                layout.lengths["debug_sink_vtable"] = 0x20


def _locate_dump(image: MappedImage, layout: LocatedLayout) -> None:
    route = _unique(image, SIG_BROKER_ROUTE, "broker_editor_dump_route", layout)
    if route is None:
        return
    table = _data_pointer(image, image.u32(route + 0x1E), "broker_editor_dump_route", layout,
                          want_code=True)
    if table is None:
        return
    case = _data_pointer(image, image.u32(table + 4 * BROKER_DUMP_CASE), "broker_editor_dump_route",
                         layout, want_code=True)
    if case is None or not image.matches(SIG_DUMP_CASE, case):
        layout.problems["broker_editor_dump_route"] = "case 2 is not accessor -> Dump"
        return
    layout.items["broker_editor_dump_route"] = route
    layout.lengths["broker_editor_dump_route"] = 0x22
    layout.items["broker_dump_case"] = case
    layout.lengths["broker_dump_case"] = 0x12
    accessor = image.rel32_target(case)
    walker = image.rel32_target(case + 0x0D)
    if not image.is_code(accessor) or not image.matches(SIG_ACCESSOR, accessor):
        layout.problems["broker_singleton_accessor"] = "case 2 accessor prologue differs"
    else:
        layout.items["broker_singleton_accessor"] = accessor
        layout.lengths["broker_singleton_accessor"] = 0x0F
        manager = _data_pointer(image, image.u32(accessor + 1), "broker_manager_global", layout)
        if manager is not None:
            layout.items["broker_manager_global"] = manager
    if not image.is_code(walker) or not image.is_code(walker + WALKER_LENGTH - 1):
        layout.problems["native_dump_walker"] = "case 2 Dump target is not code"
    else:
        layout.items["native_dump_walker"] = walker
        layout.lengths["native_dump_walker"] = WALKER_LENGTH


def _locate_openers(image: MappedImage, layout: LocatedLayout) -> None:
    switch = _unique(image, SIG_MAIN_SWITCH, "main_command_dispatch", layout)
    if switch is None:
        return
    bytetab = _data_pointer(image, image.u32(switch + 0x0D), "main_command_dispatch", layout, want_code=True)
    jumptab = _data_pointer(image, image.u32(switch + 0x14), "main_command_dispatch", layout, want_code=True)
    if bytetab is None or jumptab is None:
        return
    layout.items["main_command_dispatch"] = switch
    layout.lengths["main_command_dispatch"] = 0x18

    def case_target(command: int) -> int | None:
        index = image.data[bytetab + command]
        return image.va_to_rva(image.u32(jumptab + 4 * index))

    for command, name, slot, verify in (
            (BROKER_EDITOR_COMMAND, "broker_editor_opener", 0x10, SIG_BROKER_OPENER),
            (FLOW_BUILDER_COMMAND, "flow_builder_opener", 0x08, None)):
        case = case_target(command)
        if case is None or not image.is_code(case) or not image.matches(SIG_TOOL_CASE, case):
            layout.problems[name] = f"main command 0x{command:02X} case is not the tool opener call"
            continue
        if image.data[case + 0x0F] != slot:
            layout.problems[name] = f"main command 0x{command:02X} opens a different application member"
            continue
        opener = image.rel32_target(case + 0x13)
        if not image.is_code(opener) or (verify is not None and not image.matches(verify, opener)):
            layout.problems[name] = f"command 0x{command:02X} opener prologue differs"
            continue
        layout.items[name] = opener
        layout.lengths[name] = 0x1E if verify is not None else 0x10
        layout.items[name + "_case"] = case
        layout.lengths[name + "_case"] = 0x18


def relocation_mask(code: bytes, image_base: int, size_of_image: int) -> bytearray:
    """Mark absolute image addresses and rel32 branch displacements in ``code``.

    Built from the stock reference only and applied to both sides, so a stray
    0xE8 inside some other operand cannot mask bytes on one side alone.
    """
    mask = bytearray(len(code))
    lo, hi = image_base, image_base + size_of_image
    for i in range(len(code) - 3):
        if lo <= struct.unpack_from("<I", code, i)[0] < hi:
            mask[i:i + 4] = b""
    for i in range(len(code) - 4):
        if code[i] in (0xE8, 0xE9):
            mask[i + 1:i + 5] = b""
        elif code[i] == 0x0F and 0x80 <= code[i + 1] <= 0x8F and i + 6 <= len(code):
            mask[i + 2:i + 6] = b""
    return mask


def equal_modulo_relocation(candidate: bytes, reference: bytes, mask: bytearray) -> bool:
    return len(candidate) == len(reference) and all(
        m or a == b for a, b, m in zip(candidate, reference, mask))


# Stock retail walker identity. The relocation ranges are byte offsets of the
# absolute addresses and branch displacements inside the 0x600-byte walker
# (derived from retail 00601D00 by ``relocation_mask``); zeroing them gives an
# address-independent identity, so a stock walker moved by a mod still matches.
STOCK_WALKER_SHA256 = "27a0c5e3329ea58c7f9d573b33d1f86feeb3d39eea28177ac4c13ce7392d7c53"
STOCK_WALKER_MASKED_SHA256 = "3edf5ca4aff1ef7be2013255456f424093285882dda377d555a2e2aeee57032b"
STOCK_WALKER_RELOCATIONS = [(52, 4), (61, 4), (84, 4), (93, 4), (99, 4), (104, 10), (120, 4), (132, 4), (152, 4), (163, 4), (175, 4), (181, 4), (204, 4), (210, 4), (233, 4), (239, 4), (263, 4), (268, 4), (279, 4), (284, 4), (327, 4), (350, 4), (355, 4), (379, 4), (386, 4), (394, 4), (400, 4), (405, 4), (413, 4), (436, 4), (442, 4), (447, 4), (455, 4), (473, 4), (479, 4), (484, 4), (492, 4), (504, 4), (510, 4), (515, 4), (525, 4), (536, 4), (551, 4), (592, 4), (597, 4), (614, 4), (626, 4), (633, 4), (641, 4), (647, 4), (652, 4), (660, 4), (672, 4), (679, 4), (687, 4), (693, 4), (698, 4), (706, 4), (718, 4), (725, 4), (733, 4), (739, 4), (744, 4), (752, 4), (767, 4), (773, 4), (778, 4), (784, 4), (794, 4), (810, 9), (834, 4), (839, 4), (846, 4), (851, 4), (862, 4), (874, 4), (916, 4), (922, 4), (927, 4), (935, 4), (947, 4), (980, 4), (986, 4), (991, 4), (999, 4), (1011, 4), (1035, 4), (1041, 4), (1046, 4), (1063, 4), (1069, 4), (1074, 4), (1086, 4), (1091, 4), (1103, 4), (1126, 4), (1148, 4), (1154, 4), (1159, 4), (1172, 4), (1189, 4), (1194, 4), (1199, 4), (1212, 4), (1217, 4), (1230, 4), (1235, 4), (1248, 4), (1253, 4), (1261, 4), (1266, 4), (1283, 4), (1288, 4), (1294, 4), (1303, 4), (1309, 4), (1314, 4), (1333, 4), (1338, 4), (1344, 4), (1354, 4), (1371, 4), (1377, 4), (1382, 4), (1400, 4), (1405, 4), (1412, 4), (1417, 4), (1458, 4), (1463, 4), (1469, 4), (1479, 4), (1496, 4), (1502, 4), (1507, 4), (1525, 4), (1530, 4)]


def masked_walker_sha256(code: bytes) -> str:
    masked = bytearray(code)
    for offset, length in STOCK_WALKER_RELOCATIONS:
        masked[offset:offset + length] = bytes(length)
    return hashlib.sha256(masked).hexdigest()


def classify_walker_code(code: bytes) -> dict[str, Any]:
    """Stock / relocated stock / unknown, from the walker bytes alone."""
    digest = hashlib.sha256(code).hexdigest()
    if digest == STOCK_WALKER_SHA256:
        return {"variant": "native_stock", "post_results_safe": False, "hardened": False,
                "walker_sha256": digest}
    if len(code) == WALKER_LENGTH and masked_walker_sha256(code) == STOCK_WALKER_MASKED_SHA256:
        return {"variant": "native_stock_relocated", "post_results_safe": False, "hardened": False,
                "walker_sha256": digest}
    return {"variant": "unknown", "post_results_safe": None, "hardened": False, "walker_sha256": digest}


def classify_walker(image: MappedImage, layout: LocatedLayout,
                    exact_classifier: Callable[[MappedImage, int], dict[str, Any] | None] | None = None) -> None:
    """Classify the located Dump walker; ``unknown`` asks, it does not block.

    ``exact_classifier`` recognizes audited hardened variants (R-AI1 inline,
    two-trampoline and J.1 stubs) that only exist at the retail VA.
    """
    walker = layout.rva("native_dump_walker")
    if walker is None:
        layout.walker = {"variant": "absent", "post_results_safe": None, "hardened": False}
        return
    result = classify_walker_code(image.bytes_at(walker, WALKER_LENGTH))
    if result["variant"] == "unknown" and exact_classifier is not None:
        exact = exact_classifier(image, walker)
        if exact:
            result.update(exact)
    layout.walker = result


def locate(image: MappedImage) -> LocatedLayout:
    layout = LocatedLayout(origin=image.origin)
    _locate_sink(image, layout)
    _locate_dump(image, layout)
    _locate_openers(image, layout)
    return layout


def fingerprints(image: MappedImage, layout: LocatedLayout) -> list[dict[str, Any]]:
    """Runtime anchors (name/rva/length/sha256/section) for located code/data."""
    rows = []
    for name, rva in sorted(layout.items.items()):
        length = layout.lengths.get(name)
        if not length:
            continue
        rows.append({"name": name, "rva": rva, "length": length,
                     "sha256": hashlib.sha256(image.bytes_at(rva, length)).hexdigest(),
                     "section": image.section_name(rva, length)})
    return rows
