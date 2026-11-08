import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from extra_options_sdk_binding import propose, render_header


def fixtures():
    sdk = {'operations': [
        {'name': 'first', 'rva': 103, 'expected_original_bytes': '7405', 'replacement_bytes': 'e006'},
        {'name': 'second', 'rva': 203, 'expected_original_bytes': '7405', 'replacement_bytes': 'e006'},
        {'name': 'other', 'rva': 300, 'expected_original_bytes': '11', 'replacement_bytes': '22'},
    ]}
    f3 = {'operations': [
        {'id': 'challenge-preview-identity', 'rva': 100, 'expected_original_hex': '8bbc3874050000', 'replacement_hex': 'e9010203049090'},
        {'id': 'challenge-race-consume', 'rva': 200, 'expected_original_hex': '8bbc3874050000', 'replacement_hex': 'e9050607089090'},
    ], 'code_symbols': {'challenge_preview': 0x70002800, 'challenge_consumer': 0x70002a80}}
    return sdk, f3, bytes.fromhex('8bbc38740500009c6090'), bytes.fromhex('8bbc38740500009c6091')


class BindingTests(unittest.TestCase):
    def test_only_relocated_instruction_changes(self):
        sdk, f3, a, b = fixtures()
        before = (copy.deepcopy(sdk), copy.deepcopy(f3), a, b)
        proposal = propose(sdk, f3, a, b)
        self.assertEqual((sdk, f3, a, b), before)
        self.assertFalse(proposal['runtime_qualified'])
        for row in proposal['challenge']:
            self.assertEqual(row['expected_mapped_hex'], '8bbc38e0060000')
            self.assertTrue(row['composed_stub_hex'].startswith('8bbc38e00600009c60'))
        self.assertEqual(len(proposal['sdk_checks']), 3)
        extension = {'address': 0x10000000, 'size': 8192, 'rw_offset': 4096, 'rw_size': 4096, 'code_sha256': '0'*64}
        self.assertIn('0x70002800u', render_header(proposal, f3, extension))

    def test_missing_or_unexpected_overlap_fails_closed(self):
        sdk, f3, a, b = fixtures()
        for mutate in (
            lambda p, q: p['operations'].pop(1),
            lambda p, q: p['operations'].append({'name': 'extra', 'rva': 100, 'expected_original_bytes': '8b', 'replacement_bytes': '90'}),
            lambda p, q: p['operations'][0].update(replacement_bytes='e106'),
            lambda p, q: q['operations'][0].update(expected_original_hex='8bbc3875050000'),
            lambda p, q: q['operations'].append(copy.deepcopy(q['operations'][0])),
        ):
            left, right = copy.deepcopy(sdk), copy.deepcopy(f3)
            mutate(left, right)
            with self.assertRaises(ValueError):
                propose(left, right, a, b)
        with self.assertRaises(ValueError):
            propose(sdk, f3, b'bad', b)

    def test_actual_accepted_roster_and_f3_if_available(self):
        sdk = ROOT.parent / 'master-rallye-re-vehicles/.research-output/vehicles/v-def4-1/delivery-final/32/workshop/builds/first/candidate/runtime/native-patch-manifest.json'
        f3 = ROOT / 'research/r-mod1/native-patch-plan-f3.json'
        if not sdk.is_file() or not f3.is_file():
            self.skipTest('private accepted roster/F3 plan unavailable')
        from r_mod1_native_plan import make_challenge_preview_code, make_challenge_consumer_code
        result = propose(json.loads(sdk.read_text()), json.loads(f3.read_text()),
                         make_challenge_preview_code(), make_challenge_consumer_code())
        self.assertEqual(len(result['sdk_checks']), 263)
        self.assertEqual(len(result['challenge']), 2)

    def test_actual_challenge_stubs_execute_relocated_load(self):
        try:
            from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
            from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP
        except ImportError:
            self.skipTest('Unicorn unavailable')
        from r_mod1_native_plan import (make_challenge_preview_code, make_challenge_consumer_code,
                                        CHALLENGE_PREVIEW_BASE, CHALLENGE_CONSUMER_BASE, CHALLENGE_GATE)
        sdk, f3, _, _ = fixtures()
        a, b = make_challenge_preview_code(), make_challenge_consumer_code()
        result = propose(sdk, f3, a, b)
        by_id = {row['id']: bytes.fromhex(row['composed_stub_hex']) for row in result['challenge']}
        for kind, entry, continuation in (('challenge-preview-identity', CHALLENGE_PREVIEW_BASE, 0x45ec3c),
                                           ('challenge-race-consume', CHALLENGE_CONSUMER_BASE, 0x450115)):
            for callback, expected in ((0xffffffff, 21), (7, 7)):
                with self.subTest(kind=kind, callback=callback):
                    machine = Uc(UC_ARCH_X86, UC_MODE_32)
                    for address, size in ((0x400000, 0x200000), (0x70000000, 0x10000),
                                          (0x18000000, 0x10000), (0x19000000, 0x10000), (0x1a000000, 0x10000)):
                        machine.mem_map(address, size)
                    machine.mem_write(entry, by_id[kind])
                    machine.mem_write(CHALLENGE_GATE, b'\xb8' + callback.to_bytes(4, 'little') + b'\xc2\x10\x00')
                    machine.mem_write(0x18000574, (3).to_bytes(4, 'little'))
                    machine.mem_write(0x180006e0, (21).to_bytes(4, 'little'))
                    machine.reg_write(UC_X86_REG_EAX, 0x18000000)
                    machine.reg_write(UC_X86_REG_EBX, 4)
                    machine.reg_write(UC_X86_REG_EDI, 0)
                    machine.reg_write(UC_X86_REG_ESI, 0x19000000)
                    machine.reg_write(UC_X86_REG_ESP, 0x1a00f000)
                    machine.emu_start(entry, continuation, count=200)
                    self.assertEqual(machine.reg_read(UC_X86_REG_EDI), expected)
                    self.assertEqual(machine.reg_read(UC_X86_REG_ESP), 0x1a00f000)


if __name__ == '__main__':
    unittest.main()
