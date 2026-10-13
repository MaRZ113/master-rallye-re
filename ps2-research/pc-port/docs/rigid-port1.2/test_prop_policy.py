"""Synthetic diagnostic-policy tests, not an engine or ownership test."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('prop_policy',Path(__file__).with_name('prop-logpoint-policy.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class PolicyTests(unittest.TestCase):
    def test_discovery_exact_original_class(self):
        script=p.discovery()
        self.assertIn('004C9CF0',script);self.assertIn('[ecx] == 00691470',script)
        self.assertIn('egg={p:[esp+4]}',script)
        self.assertNotIn('$breakpointcounter',script)

    def test_selected_filters_each_owner_not_global_ordinals(self):
        script=p.selected(0x10000,0x20000,0x30000,0x40000)
        self.assertIn('ecx == 00010000',script)
        self.assertIn('ecx == 00020000',script)
        self.assertIn('[esp+28] == 00010000',script)
        self.assertIn('[esp+4] == 00040000',script)
        self.assertNotIn('$breakpointcounter',script)
        self.assertNotIn('draw_sequence',script)

    def test_frontend_hits_do_not_spend_matched_budget(self):
        # Independent policy oracle: only true identity increments custom count.
        matching=0
        for is_target in ([False]*500)+[True,True,True]:
            if is_target and matching<2:matching+=1
        self.assertEqual(matching,2)
        script=p.point(0x4F5840,'retire','ecx == 00010000','',2)
        condition=next(x for x in script if x.startswith('SetBreakpointCommandCondition'))
        self.assertIn('ecx == 00010000',condition)
        self.assertIn('$rp12_retire_matches < .2',condition)

    def test_only_debugger_variables_are_written(self):
        script=p.selected(0x10000,0x20000,0x30000,0x40000)
        for line in script.splitlines():
            if line.startswith('mov '):self.assertTrue(line.startswith('mov $rp12_'))
            if line.startswith('SetBreakpointCommand '):self.assertIn('"mov $rp12_',line)
        self.assertFalse(any(line.startswith(('run','call','injectdll','mov ecx','mov [')) for line in script.splitlines()))

    def test_bad_and_missing_pointer_cannot_generate_selected_recipe(self):
        for invalid in (0,0x10001,0x80000000,None):
            with self.assertRaises(ValueError):p.selected(invalid,0x20000,0x30000,0x40000)

    def test_deterministic_output_and_no_spawn_mode(self):
        self.assertEqual(p.discovery(),p.discovery())
        self.assertEqual(p.selected(0x10000,0x20000,0x30000,0x40000),p.selected(0x10000,0x20000,0x30000,0x40000))
        self.assertNotIn('Spawn',p.discovery())


if __name__=='__main__':unittest.main()
