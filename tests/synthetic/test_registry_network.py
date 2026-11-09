"""CPU-level proof that unsupported CarIDs cannot reach retail byte/send paths."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import sdk_registry_network as network
from build_sdk_capacity_profile import load_parent
import j2_frontend_reentry as j2

PARENT = ROOT.parent / 'master-rallye-re-vehicles/.research-output/vehicles/extra-set2/extra-set2-03/runtime'
SOURCE = ROOT.parent / 'MRallye.exe'


@unittest.skipUnless((PARENT / 'addon-plan.json').is_file() and SOURCE.is_file(), 'Accepted local SDK33 unavailable')
class NetworkGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import unicorn
        except ImportError:
            raise unittest.SkipTest('Unicorn unavailable')
        cls.source = SOURCE.read_bytes()
        parent_image, cls.parent_blob, _ = load_parent(cls.source, PARENT)
        cls.image, cls.blob, cls.report = network.append_network_guard(cls.source, parent_image,
                                                                      cls.parent_blob, allocation_size=1048576)

    def machine(self):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
        from unicorn.x86_const import UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP, UC_X86_REG_EAX as EAX, UC_X86_REG_ECX as ECX
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x400000)
        _, sections = j2.addon_runtime._pe_sections(self.image)
        for s in sections:
            u.mem_write(0x400000 + s['rva'], self.image[s['raw_offset']:s['raw_offset'] + s['raw_size']])
        u.mem_map(network.BASE, 1048576)
        u.mem_write(network.BASE, self.blob)
        u.mem_protect(network.BASE, 1048576, UC_PROT_READ | UC_PROT_EXEC)
        state = self.report['writable_ranges'][0]
        u.mem_protect(network.BASE + state['offset'], state['size'], UC_PROT_READ | UC_PROT_WRITE)
        u.mem_map(0x1000000, 0x20000)
        calls = []
        def logger(uc, address, size, data):
            if address == network.LOGGER:
                sp = uc.reg_read(ESP)
                args = struct.unpack('<3I', uc.mem_read(sp, 12))
                calls.append(args[2])
                self.assertIn(b'NETWORK BLOCKED', bytes(uc.mem_read(args[1], 80)))
                uc.reg_write(EAX, 0xbad)
                uc.reg_write(ECX, 2)
                uc.reg_write(ESP, sp + 4)
                uc.reg_write(EIP, args[0])
        u.hook_add(UC_HOOK_CODE, logger)
        return u, calls

    def packet(self, u, physical):
        from unicorn.x86_const import UC_X86_REG_ESP as ESP, UC_X86_REG_EBP as EBP, UC_X86_REG_ESI as ESI
        u.reg_write(ESP, 0x100fe00)
        u.reg_write(EBP, 0x1002000)
        u.reg_write(ESI, 0x1003000)
        u.mem_write(0x1002030, struct.pack('<I', physical & 0xffffffff))
        u.mem_write(0x1003000, b'\xa5' * 64)
        u.mem_write(0x100fe00, struct.pack('<4I', 0x11111111, 0x22222222, 0x33333333, 0x44444444) + bytes(32) +
                    struct.pack('<4I', 0x1001000, 0, 0, 0))

    def test_packet_preserves_stock_boundary_and_inactive_sentinel(self):
        from unicorn.x86_const import UC_X86_REG_EIP as EIP, UC_X86_REG_ESP as ESP, UC_X86_REG_EAX as EAX
        for physical in [0, 32, 33, 127, 128, 254, -1]:
            u, calls = self.machine()
            self.packet(u, physical)
            u.reg_write(EAX, 0xabcdef12)
            u.emu_start(network.WRITER, network.WRITER + 6, count=10000)
            self.assertEqual(u.reg_read(EIP), network.WRITER + 6)
            self.assertEqual(u.mem_read(0x1003005, 1)[0], physical & 255)
            self.assertEqual(u.reg_read(EAX), 0xabcdef00 | (physical & 255))
            self.assertEqual(u.reg_read(ESP), 0x100fe00)
            self.assertEqual(calls, [])

    def test_packet_blocks_full_width_ids_without_touching_wire_or_losing_stack(self):
        from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_EBX as EBX, UC_X86_REG_EBP as EBP, UC_X86_REG_ESI as ESI, UC_X86_REG_EDI as EDI, UC_X86_REG_ESP as ESP
        for physical in [255, 256, 511, 512, 4096, 0x7ffffffe, -2]:
            u, calls = self.machine()
            self.packet(u, physical)
            u.emu_start(network.WRITER, 0x1001000, count=10000)
            self.assertEqual(u.reg_read(EAX), 0)
            self.assertEqual(bytes(u.mem_read(0x1003000, 64)), b'\xa5' * 64)
            self.assertEqual([u.reg_read(r) for r in (EDI, ESI, EBP, EBX)], [0x11111111, 0x22222222, 0x33333333, 0x44444444])
            self.assertEqual(u.reg_read(ESP), 0x100fe40)
            self.assertEqual(calls, [physical & 0xffffffff])

    def test_sender_drops_empty_or_unsupported_packets_before_native_backend(self):
        from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_EBX as EBX, UC_X86_REG_ECX as ECX, UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP
        for physical, length in [(255, 100), (256, 100), (4096, 100), (0, 0), (-1, 0), (-2, 100)]:
            u, calls = self.machine()
            u.reg_write(ECX, 0x1002000)
            u.reg_write(ESP, 0x100fe00)
            u.reg_write(EBX, 0xfeed)
            u.mem_write(0x1002030, struct.pack('<I', physical & 0xffffffff))
            u.mem_write(0x100fe00, struct.pack('<5I', 0x1001000, 0x56ce, 0x1003000, length, 0))
            u.emu_start(network.SENDER, 0x1001000, count=10000)
            self.assertEqual(u.reg_read(EAX), 0)
            self.assertEqual(u.reg_read(EBX), 0xfeed)
            self.assertEqual(u.reg_read(ESP), 0x100fe14)
            self.assertEqual(u.reg_read(EIP), 0x1001000)

    def test_sender_keeps_stock_prologue_for_0_to_254_and_minus_one(self):
        from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_EBX as EBX, UC_X86_REG_ECX as ECX, UC_X86_REG_ESP as ESP
        for physical in [0, 33, 127, 128, 254, -1]:
            u, calls = self.machine()
            u.reg_write(ECX, 0x1002000)
            u.reg_write(ESP, 0x100fe00)
            u.reg_write(EBX, 0xfeed)
            u.mem_write(0x1002030, struct.pack('<I', physical & 0xffffffff))
            u.mem_write(0x100fe00, struct.pack('<5I', 0x1001000, 0x56ce, 0x1003000, 40, 0))
            u.emu_start(network.SENDER, network.SENDER + 5, count=10000)
            self.assertEqual(u.reg_read(EAX), 0x1003000)
            self.assertEqual(u.reg_read(ESP), 0x100fdfc)
            self.assertEqual(struct.unpack('<I', u.mem_read(u.reg_read(ESP), 4))[0], 0xfeed)
            self.assertEqual(calls, [])

    def test_diagnostic_once_per_invalid_selection_and_rw_page_isolated(self):
        u, calls = self.machine()
        for physical in [256, 256, 512, 512, 254, 512]:
            self.packet(u, physical)
            u.emu_start(network.WRITER, network.WRITER + 6 if physical == 254 else 0x1001000, count=10000)
        self.assertEqual(calls, [256, 512, 512])
        state = self.report['writable_ranges'][0]
        self.assertEqual(state['offset'] % 4096, 0)
        self.assertEqual(state['size'], 4096)
        self.assertLess(self.report['entries']['diagnostic'], network.BASE + state['offset'])
        self.assertEqual(len(self.blob), state['offset'] + 4096)
        self.assertEqual(self.blob[:len(self.parent_blob)], self.parent_blob)


if __name__ == '__main__':
    unittest.main()
