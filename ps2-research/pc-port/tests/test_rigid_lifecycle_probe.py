"""Synthetic, corpus-independent tests; no game process is accessed."""
import importlib.util
from pathlib import Path
import struct
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/rigid_lifecycle_probe.py"
spec = importlib.util.spec_from_file_location("readonly_rigid_probe", SCRIPT)
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


class SyntheticMemory:
    def __init__(self):
        self.regions = {}
        self.reads = []
    def put(self, address, data):
        self.regions[address] = data
    def words(self, address, *values):
        self.put(address, struct.pack("<" + "I" * len(values), *values))
    def read(self, address, size):
        self.reads.append((address, size))
        for base, data in self.regions.items():
            if base <= address and address + size <= base + len(data):
                return data[address-base:address-base+size]
        raise OSError("Synthetic unmapped read")


def fixture(count=1):
    m = SyntheticMemory()
    m.words(p.HOLDER_VA, 0x10000)
    m.words(0x10008, 0x11000)
    m.words(0x11000, p.BACKEND_VTABLE)
    m.words(p.BACKEND_VTABLE + 0x30, 0x56FCE0)
    m.words(0x11014, 0x12000, 0x12000 + 4*count, 0x12000 + 4*count)
    m.words(0x12000, *(0x13000 + 0x100*n for n in range(count)))
    for n in range(count):
        m.words(0x13000 + 0x100*n, 0x15000, 0x16000, 0x17000, 0x18000, 7, 123, 0)
    m.words(0x18000, p.PROP_BODY_VTABLE)
    m.put(0x180A0, struct.pack("<7f", 1, 2, 3, 0, 0, 0, 1))
    m.words(0x181D0, 123, 0)
    return m


class ReadonlyRigidTests(unittest.TestCase):
    def test_known_layout_and_typed_body(self):
        m = fixture(); result = p.sample_backend(m)
        r = result["instances"][0]
        self.assertEqual([r[k] for k in ("representation_at_00", "representation_at_04", "base")],
                         [0x15000, 0x16000, 0x17000])
        self.assertEqual(r["body"], 0x18000)
        self.assertEqual(r["native_nonvehicle_position"], [1, 2, 3])
        self.assertEqual(result["vehicle_contact"], "NOT_PROVED")
        self.assertEqual(result["course_identity"], "UNKNOWN")
        self.assertLess(sum(size for _, size in m.reads), p.MAX_READ_BYTES)

    def test_uninitialized_owner_and_wrong_backend_fail_closed(self):
        m = SyntheticMemory(); m.words(p.HOLDER_VA, 0)
        self.assertEqual(p.sample_backend(m)["status"], "NOT_INITIALIZED")
        m = fixture(); m.words(0x11000, 0x692314)
        with self.assertRaisesRegex(p.ProbeError, "vtable"):
            p.sample_backend(m)

    def test_limits_and_invalid_vectors(self):
        for bounds in ((0x12000,0x11FFC,0x12004), (0x12000,0x12001,0x12004),
                       (0x12000,0x12008,0x12004), (0x12000,0x12004,0x12000+4*8193)):
            with self.assertRaises(p.ProbeError): p.vector_count(*bounds)
        self.assertEqual(p.vector_count(0,0,0),0)
        for maximum in (0,17):
            with self.assertRaises(p.ProbeError): p.sample_backend(fixture(), maximum)
        for address in (0,0x10001,0x80000000):
            with self.assertRaises(p.ProbeError): p.pointer(address)

    def test_loaded_vtable_slot_change_is_rejected(self):
        m = fixture(); m.words(p.BACKEND_VTABLE + 0x30,0x56FCE4)
        with self.assertRaisesRegex(p.ProbeError,"vtable slot"):
            p.sample_backend(m)

    def test_bounded_selection_is_not_complete_inventory(self):
        result = p.sample_backend(fixture(3), 2)
        self.assertEqual(result["native_instance_vector_count"], 3)
        self.assertEqual(result["selected_count"], 2)
        self.assertTrue(result["selection_truncated"])

    def test_other_body_and_unreadable_instances_are_not_guessed(self):
        m = fixture(); m.words(0x18000,0x123456)
        result = p.sample_backend(m)["instances"][0]
        self.assertNotIn("native_nonvehicle_position",result)
        self.assertEqual(result["body_state"],"UNDECODED_OTHER_BODY_TYPE")
        m = fixture(); del m.regions[0x13000]
        self.assertEqual(p.sample_backend(m)["instances"][0]["status"],"UNREADABLE_OR_CHANGED")

    def test_nonfinite_state_is_explicit_error(self):
        m = fixture(); m.put(0x180A0,struct.pack("<7f",float("nan"),2,3,0,0,0,1))
        result = p.sample_backend(m)["instances"][0]
        self.assertEqual(result["status"],"UNREADABLE_OR_CHANGED")
        self.assertNotIn("native_nonvehicle_position",result)

    def test_header_change_is_rejected(self):
        m = fixture(); original = m.read; reads = 0
        def racing(address,size):
            nonlocal reads
            if address == 0x11014:
                reads += 1
                if reads == 2: return struct.pack("<3I",0,0,0)
            return original(address,size)
        m.read = racing
        with self.assertRaisesRegex(p.ProbeError,"changed during read"):
            p.sample_backend(m)

    def test_pe_machine_magic_and_base(self):
        b = bytearray(512); b[:2] = b"MZ"; struct.pack_into("<I",b,0x3C,0x80)
        b[0x80:0x84] = b"PE\0\0"; struct.pack_into("<H",b,0x84,0x14C)
        struct.pack_into("<H",b,0x98,0x10B); struct.pack_into("<I",b,0xB4,0x400000)
        self.assertEqual(p.pe32_identity(b)["machine"],"i386")
        for offset,value,format_ in ((0x84,0x8664,"H"),(0x98,0x20B,"H"),(0xB4,0x500000,"I")):
            changed=bytearray(b); struct.pack_into("<"+format_,changed,offset,value)
            with self.assertRaises(p.ProbeError): p.pe32_identity(changed)
        with self.assertRaises(p.ProbeError): p.pe32_identity(b"MZ")

    def test_debug_recipe_is_deterministic_bounded_and_does_not_run(self):
        text = p.debugger_script(16)
        self.assertEqual(text,p.debugger_script(16))
        self.assertEqual(text.count("SetBreakpointLogCondition"),len(p.LOGPOINTS))
        self.assertIn("$breakpointcounter <= .16",text)
        self.assertIn("$breakpointcounter == .16",text)
        self.assertNotIn("SetBreakpointFastResume 0043F2C0, 1",text)
        commands=[line for line in text.splitlines() if not line.startswith("//")]
        self.assertFalse(any(line.split()[0] in ("run","call","mov","injectdll") for line in commands))
        self.assertEqual(p.PROCESS_ACCESS,0x1010)
        with self.assertRaises(p.ProbeError): p.debugger_script(65)


if __name__ == "__main__": unittest.main()
