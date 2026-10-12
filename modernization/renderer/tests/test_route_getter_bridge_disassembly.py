import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "modernization" / "renderer" / ".build-msvc" / "Release"
DLL = BUILD / "d3d8.dll"
MAP = BUILD / "d3d8.map"
IMAGE_BASE = 0x10000000


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def parse_image(data):
    if data[:2] != b"MZ":
        raise AssertionError("missing DOS header")
    pe = u32(data, 0x3C)
    if data[pe:pe + 4] != b"PE\0\0":
        raise AssertionError("missing PE signature")
    machine = u16(data, pe + 4)
    optional_size = u16(data, pe + 20)
    optional = pe + 24
    if u16(data, optional) != 0x010B:
        raise AssertionError("proxy is not PE32")
    image_base = u32(data, optional + 28)
    section_table = optional + optional_size
    sections = []
    for index in range(u16(data, pe + 6)):
        offset = section_table + index * 40
        name = data[offset:offset + 8].split(b"\0", 1)[0].decode("ascii")
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", data, offset + 8)
        sections.append((name, rva, virtual_size, raw_offset, raw_size))

    def read_va(va, length):
        rva = va - image_base
        for name, section_rva, _, raw_offset, raw_size in sections:
            if name == ".text" and section_rva <= rva and rva + length <= section_rva + raw_size:
                offset = raw_offset + rva - section_rva
                return data[offset:offset + length]
        raise AssertionError(f"VA 0x{va:08X} is outside file-backed .text")

    return machine, image_base, read_va


def map_symbol_va(map_text, symbol):
    pattern = re.compile(
        rf"^\s*0001:[0-9a-fA-F]+\s+_{re.escape(symbol)}\s+([0-9a-fA-F]{{8}})(?:\s|$)",
        re.MULTILINE,
    )
    match = pattern.search(map_text)
    if not match:
        raise AssertionError(f"{symbol} missing from linker map")
    return int(match.group(1), 16)


class BuiltRouteGetterBridgeDisassembly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DLL.is_file() or not MAP.is_file():
            raise unittest.SkipTest("build the Win32 Release proxy before disassembly validation")
        cls.image = DLL.read_bytes()
        cls.map_text = MAP.read_text(errors="replace")
        cls.machine, cls.image_base, read_va = parse_image(cls.image)
        cls.read_va = staticmethod(read_va)
        cls.bridge_va = map_symbol_va(cls.map_text, "physics_probe_route_getter_bridge")
        cls.observer_va = map_symbol_va(cls.map_text, "physics_probe_route_after_getter")

    def test_production_bridge_is_pe32_i386_at_expected_base(self):
        self.assertEqual(self.machine, 0x014C)
        self.assertEqual(self.image_base, IMAGE_BASE)

    def test_production_bridge_forwards_argument_preserves_result_and_returns_ret4(self):
        # push [esp+4]; mov eax, retail target; call eax; pushfd; pushad;
        # pass saved ESI (the recovery manager) and saved EAX (route object)
        # to the observer; restore native state; ret 4.
        prefix = bytes.fromhex(
            "FF 74 24 04 B8 20 4D 4E 00 FF D0 9C 60 "
            "8B 44 24 1C 8B 54 24 04 52 50 E8"
        )
        tail = bytes.fromhex("83 C4 08 61 9D C2 04 00")
        code = self.read_va(self.bridge_va, len(prefix) + 4 + len(tail))
        self.assertEqual(code[:len(prefix)], prefix)
        self.assertEqual(code[-len(tail):], tail)
        displacement = struct.unpack_from("<i", code, len(prefix))[0]
        observer_call_next = self.bridge_va + len(prefix) + 4
        self.assertEqual(observer_call_next + displacement, self.observer_va)

    def test_clear_bridges_preserve_registers_flags_and_replay_exact_stores(self):
        legacy_observer=map_symbol_va(self.map_text,"physics_probe_clear_writer_observe")
        observer=map_symbol_va(self.map_text,"physics_probe_transaction_observe")
        cases={
            "clear_gate":(0x4CCC70,"9c 60 8b 44 24 1c 6a 00 50 68 70 cc 4c 00 e8","8b 40 08 c6 40 33 00"),
            "clear_recovery":(0x4CD1A1,"9c 60 8b 44 24 1c 6a 00 50 68 a1 d1 4c 00 e8","8b 48 08 c6 41 33 00"),
            "clear_timer":(0x4CD1DE,"9c 60 8b 44 24 1c 8b 54 24 18 52 50 68 de d1 4c 00 e8","8b 40 08 88 48 33"),
            "publish":(0x4CCFF1,"","c6 45 33 01 8b 4e 1c"),
            "matrix_complete":(0x4CD131,"","8b 4e 3c 8b d3 03 d1"),
            "input_flag":(0x591345,"","88 50 33 8b 41 2c"),
            "restore_flag":(0x4CB62A,"","88 46 33"),
        }
        for name,(site,prefix,replay) in cases.items():
            with self.subTest(writer=name):
                va=map_symbol_va(self.map_text,f"physics_probe_{name}_bridge")
                position=va
                if prefix:
                    prefix=bytes.fromhex(prefix)
                    self.assertEqual(self.read_va(position,len(prefix)),prefix)
                    position+=len(prefix)
                    displacement=struct.unpack("<i",self.read_va(position,4))[0]
                    self.assertEqual(position+4+displacement,legacy_observer)
                    position+=4
                    tail=bytes.fromhex("83 c4 0c 61 9d")
                    self.assertEqual(self.read_va(position,len(tail)),tail);position+=len(tail)
                for after in [0,1]:
                    prefix=bytes.fromhex("9c 60 8b c4 6a")+bytes([after,0x68])+struct.pack("<I",site)+bytes.fromhex("50 e8")
                    self.assertEqual(self.read_va(position,len(prefix)),prefix);position+=len(prefix)
                    displacement=struct.unpack("<i",self.read_va(position,4))[0]
                    self.assertEqual(position+4+displacement,observer);position+=4
                    tail=bytes.fromhex("83 c4 0c 61 9d")
                    self.assertEqual(self.read_va(position,len(tail)),tail);position+=len(tail)
                    if not after:
                        raw=bytes.fromhex(replay)
                        self.assertEqual(self.read_va(position,len(raw)),raw);position+=len(raw)
                if name=="restore_flag":
                    self.assertEqual(self.read_va(position,6),bytes.fromhex("ff 74 24 04 ff 15"));position+=6
                    slot=struct.unpack("<I",self.read_va(position,4))[0];position+=4
                    # The only relocated native call forwards one original stack argument, then ret4.
                    from importlib.util import spec_from_file_location,module_from_spec
                    spec=spec_from_file_location("verify_proxy",ROOT/"modernization/renderer/tools/verify_proxy.py")
                    module=module_from_spec(spec);spec.loader.exec_module(module)
                    pe=module.PE(self.image)
                    self.assertEqual(pe.u32(pe.offset(slot-self.image_base,4)),0x004D0580)
                    self.assertEqual(self.read_va(position,3),bytes.fromhex("c2 04 00"))
                else:self.assertEqual(self.read_va(position,1),b"\xc3")


if __name__ == "__main__":
    unittest.main()
