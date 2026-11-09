"""Execute the actual SDK33 fallback and new x86 routes, without a game."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from build_sdk_capacity_profile import load_parent
import sdk_capacity_native as native
import sdk_registry_routes as routes
import j2_frontend_reentry as j2

PARENT = ROOT.parent / 'master-rallye-re-vehicles/.research-output/vehicles/extra-set2/extra-set2-03/runtime'
SOURCE = ROOT.parent / 'MRallye.exe'


@unittest.skipUnless((PARENT / 'addon-plan.json').is_file() and SOURCE.is_file(), 'Accepted local SDK33 fixture unavailable')
class NativeRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from unicorn import Uc
        except ImportError:
            raise unittest.SkipTest('Unicorn unavailable')
        cls.source = SOURCE.read_bytes()
        cls.parent_image, cls.parent_blob, _ = load_parent(cls.source, PARENT)
        cls.plan = json.loads((PARENT / 'addon-plan.json').read_text())
        cls.rows = []
        for i, kind in [(33, 'T1'), (127, 'T2'), (128, 'T2'), (254, 'T3'), (255, 'T3'), (256, 'T3'), (512, 'T3')]:
            row = copy.deepcopy(next(r for r in cls.plan['addons'] if r['vehicle_class'] == kind))
            row['physical_id'] = i
            row['addon_id'] = 'route-test-' + str(i)
            row['class_local_index'] = i
            row['identity'] = {k: 'RouteCar' + str(i) for k in row['identity']}
            row['identity']['physics_family'] = 'Vehicles/RouteCar' + str(i)
            row['assets']['model_package_root'] = 'DataGx/Vehicles/RouteCar' + str(i)
            row['frontend']['manufacturer'] = 'Route'
            row['frontend']['model'] = str(i)
            row['frontend']['combined'] = 'Route ' + str(i)
            row['unlock'] = {'policy': 'mirror_stock_unlock', 'stock_vehicle_id': 10}
            row['results']['display_name'] = 'Result ' + str(i)
            if i in (255, 512):
                row['ai_eligibility']['invitation'] = {'enabled': False, 'reason': 'CPU test exclusion'}
            if i == 256:
                row['ai_eligibility']['rallye_cup'] = {'enabled': False, 'reason': 'CPU test exclusion'}
            cls.rows.append(row)
        cls.image, cls.blob, cls.report = routes.append_routes(cls.source, cls.parent_image, cls.parent_blob,
                                                             cls.plan, cls.rows, allocation_size=1048576)

    def machine(self):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
        from unicorn.x86_const import UC_X86_REG_ESP as ESP
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x400000)
        _, sections = j2.addon_runtime._pe_sections(self.image)
        for s in sections:
            u.mem_write(0x400000 + s['rva'], self.image[s['raw_offset']:s['raw_offset'] + s['raw_size']])
        u.mem_map(0x10000000, 1048576)
        u.mem_write(0x10000000, self.blob)
        u.mem_map(0x1000000, 0x20000)
        u.reg_write(ESP, 0x100fff0)
        u.mem_write(0x100fff0, struct.pack('<I', 0x1001000))
        return u

    def test_no_registry_mapping_lifetime_or_parent_payload_changes(self):
        forbidden = {0x458d3f, 0x481e20, 0x481e50, 0x458cf3, 0x458e45, 0x686795, 0x4819a4}
        self.assertFalse(forbidden.intersection(op['virtual_address'] for op in self.report['operations']))
        self.assertEqual(self.blob[:len(self.parent_blob)], self.parent_blob)
        self.assertEqual({p['parent_terminal'] for p in self.report['ai_pools']}, {27, 32, 33})
        for pool in self.report['ai_pools']:
            self.assertNotIn(pool['mode'], ('challenge', 'practice'))

    def test_audio_calls_parent_once_preserving_thiscall_stack_for_wide_ids(self):
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_ECX as ECX, UC_X86_REG_EDX as EDX, UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP
        pe = native.registry.parse_pe(self.source)
        parent = native.branch_target(self.parent_image, pe, native.i0.AUDIO_PROFILE_CALL_VA, 0xe8)
        for physical in [0, 32, 33, 127, 128, 254, 255, 256, 512]:
            u = self.machine()
            u.mem_write(0x100fff4, struct.pack('<I', 0x3000000))
            calls = []
            def stub(uc, address, size, data):
                if address != parent:
                    return
                calls.append(address)
                sp = uc.reg_read(ESP)
                uc.reg_write(EAX, physical)
                uc.reg_write(ECX, 2)
                uc.reg_write(EDX, 0xbad)
                uc.reg_write(EIP, struct.unpack('<I', uc.mem_read(sp, 4))[0])
                uc.reg_write(ESP, sp + 8)
            u.hook_add(UC_HOOK_CODE, stub)
            u.emu_start(self.report['entries']['audio'], 0x1001000, count=10000)
            row = next((r for r in self.rows if r['physical_id'] == physical), None)
            self.assertEqual(u.reg_read(EAX), row['audio']['stock_audio_profile_id'] if row else physical)
            self.assertEqual(len(calls), 1)
            self.assertEqual(u.reg_read(ESP), 0x100fff8)

    def test_native_ai_fallback_increment_once_and_per_mode_eligibility(self):
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_ESI as ESI, UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP
        for pool in self.report['ai_pools']:
            cls = pool['vehicle_class']
            mode = pool['mode']
            expected = [r['physical_id'] for r in self.plan['addons'] + self.rows
                        if r['vehicle_class'] == cls and r['ai_eligibility'][mode]['enabled']]
            for race_type in ([6, 8] if cls == 'T3' and mode in ('rallye_cup', 'invitation') else [None]):
                actual_mode = {6: 'rallye_cup', 8: 'invitation'}.get(race_type, mode)
                expected = [r['physical_id'] for r in self.plan['addons'] + self.rows
                            if r['vehicle_class'] == cls and r['ai_eligibility'][actual_mode]['enabled']]
                u = self.machine()
                selected = []
                # T1/T2 displaced INC belongs to native body; T3 helper owns INC.
                u.reg_write(ESI, {'T1': 7, 'T2': 14, 'T3': 20}[cls])
                def callback(uc, address, size, data):
                    if address in (0x4ada50, 0x4abe90):
                        sp = uc.reg_read(ESP)
                        uc.reg_write(EAX, race_type if address == 0x4abe90 else 0x2000000)
                        uc.reg_write(EIP, struct.unpack('<I', uc.mem_read(sp, 4))[0])
                        uc.reg_write(ESP, sp + 4)
                    elif address == pool['reentry_va'] or (cls == 'T1' and address == {'rallye_cup': 0x45acef, 'master_rallye': 0x451eb4}.get(mode)):
                        selected.append(uc.reg_read(ESI))
                        if cls != 'T3':
                            uc.reg_write(ESI, uc.reg_read(ESI) + 1)
                        uc.reg_write(EIP, pool['hook_va'])
                    elif address == pool['exit_va']:
                        uc.emu_stop()
                u.hook_add(UC_HOOK_CODE, callback)
                u.emu_start(pool['hook_va'], 0x1001000, count=100000)
                self.assertEqual(selected, expected, (cls, mode, race_type))
                self.assertEqual(u.reg_read(ESI), {'T1': 7, 'T2': 14, 'T3': 21}[cls])
                self.assertEqual(u.reg_read(EIP), pool['exit_va'])

    def test_generic_display_and_results_use_full_physical_id(self):
        from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_EDI as EDI, UC_X86_REG_ESI as ESI
        for row in self.rows:
            u = self.machine()
            u.reg_write(EDI, row['physical_id'])
            u.emu_start(0x481a0e, 0x481a18, count=10000)
            self.assertEqual(bytes(u.mem_read(u.reg_read(EAX), 6)), b'Route\0')
            u = self.machine()
            # The original Results prefix: MOV ECX,[ESI+EBP*4]; MOV EDX,[EAX]; MOV ECX,[ECX+8].
            from unicorn.x86_const import UC_X86_REG_EBP as EBP
            u.reg_write(ESI, 0x1002000)
            u.reg_write(EBP, 0)
            u.reg_write(EAX, 0x1002100)
            u.mem_write(0x1002000, struct.pack('<I', 0x1002200))
            u.mem_write(0x1002208, struct.pack('<I', row['physical_id']))
            u.emu_start(native.i0.natural.RESULTS_NAME_HOOK_VA, native.i0.natural.RESULTS_AFTER_LOOKUP_VA, count=10000)
            expected = row['results']['display_name'].encode() + b'\0'
            self.assertEqual(bytes(u.mem_read(u.reg_read(EAX), len(expected))), expected)

    def test_unlock_oracle_uses_selected_record_and_preserves_stack(self):
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_EAX as EAX, UC_X86_REG_ECX as ECX, UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP, UC_X86_REG_EBX as EBX
        for row in self.rows:
            u = self.machine()
            u.reg_write(ECX, 0x1002000)
            u.mem_write(0x1002004, struct.pack('<I', row['physical_id']))
            calls = []
            def oracle(uc, address, size, data):
                if address != 0x45a150:
                    return
                calls.append(struct.unpack('<2I', uc.mem_read(uc.reg_read(ECX), 8)))
                sp = uc.reg_read(ESP)
                uc.reg_write(EAX, 1)
                uc.reg_write(ECX, 2)
                uc.reg_write(EIP, struct.unpack('<I', uc.mem_read(sp, 4))[0])
                uc.reg_write(ESP, sp + 4)
            u.hook_add(UC_HOOK_CODE, oracle)
            u.emu_start(self.report['entries']['unlock'], 0x1001000, count=10000)
            self.assertEqual(calls, [(0, 10)])
            self.assertEqual(u.reg_read(ECX), 0x1002000)
            self.assertEqual(u.reg_read(ESP), 0x100fff4)
            self.assertEqual(u.reg_read(EAX), 1)
            u = self.machine()
            u.reg_write(EAX, row['physical_id'] - 3)
            u.emu_start(self.report['entries']['locked'], 0x481b49, count=10000)
            self.assertEqual(u.reg_read(EBX), 12)


if __name__ == '__main__':
    unittest.main()
