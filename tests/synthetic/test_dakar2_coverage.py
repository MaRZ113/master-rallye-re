"""Source-free regressions for original Dakar2 coverage state and addressing."""
import copy
import unittest
from master_rallye.source_adapters.dakar2_coverage import alpha_rule, texture_addressing, trace_alpha


class CoverageTests(unittest.TestCase):
    def test_hir_kind_is_not_sequential_node_id(self):
        self.assertTrue(alpha_rule(4, 0x08000000)['explicit_cutout'])
        self.assertFalse(alpha_rule(0, 0x08000000)['explicit_cutout'])
        self.assertFalse(alpha_rule(8, 0x08000000)['explicit_cutout'])
        self.assertTrue(alpha_rule(0, 0x18000000)['explicit_cutout'])

    def test_first_pass_truck_wheels_do_not_gain_cutout_from_kind(self):
        self.assertFalse(alpha_rule(4, 0)['explicit_cutout'])
        self.assertEqual(alpha_rule(4, 0)['draw_alpha'], 'INHERITED')

    def test_second_pass_reset_prevents_wheel_cutout_leaking_to_glass(self):
        nodes=[{'id':'wheel','source_kind':1,'source_lod_flags':0x08000000},
               {'id':'window','source_kind':0,'source_lod_flags':0x08000000}]
        rows=trace_alpha(nodes,incoming_enabled=False,effective_reference=100)
        self.assertEqual((rows[0]['enabled'],rows[0]['comparison'],rows[0]['reference']),(True,'GREATER',100))
        self.assertEqual((rows[1]['enabled'],rows[1]['comparison'],rows[1]['reference']),(False,'ALWAYS',0))

    def test_runtime_entry_state_and_reference_cannot_be_silently_defaulted(self):
        for enabled in (None,0,1,'UNKNOWN'):
            with self.assertRaises(ValueError):trace_alpha([],incoming_enabled=enabled,effective_reference=100)
        for reference in (None,-1,256,100.,True):
            with self.assertRaises(ValueError):trace_alpha([],incoming_enabled=False,effective_reference=reference)
        rows=trace_alpha([{'id':'first','source_kind':0,'source_lod_flags':0}],
                         incoming_enabled=True,effective_reference=100)
        self.assertEqual(rows[0]['comparison'],'INHERITED');self.assertIsNone(rows[0]['reference'])
        rows=trace_alpha([{'id':'first','source_kind':0,'source_lod_flags':0}],
                         incoming_enabled=False,effective_reference=100)
        self.assertEqual(rows[0]['comparison'],'INHERITED');self.assertIsNone(rows[0]['reference'])

    def test_original_four_address_combinations_preserve_aux_flags(self):
        for flags,pair in [(0,(3,3)),(1,(1,3)),(2,(3,1)),(3,(1,1)),(7,(1,1))]:
            result=texture_addressing(flags)
            self.assertEqual((result['u'],result['v']),pair)
            self.assertEqual(result['source_flags'],flags)
            self.assertEqual(result['uninterpreted_flags'],flags&~3)

    def test_source_rules_immutable_and_bounded(self):
        nodes=[{'id':'wheel','source_kind':1,'source_lod_flags':0x08000000}];before=copy.deepcopy(nodes)
        self.assertEqual(trace_alpha(nodes,incoming_enabled=False,effective_reference=100),
                         trace_alpha(nodes,incoming_enabled=False,effective_reference=100))
        self.assertEqual(nodes,before)
        with self.assertRaises(ValueError):trace_alpha(nodes*2,incoming_enabled=False,effective_reference=100)
        with self.assertRaises(ValueError):trace_alpha(nodes*257,incoming_enabled=False,effective_reference=100)
        for value in (True,-1,1<<32,None):
            with self.assertRaises(ValueError):texture_addressing(value)
            with self.assertRaises(ValueError):alpha_rule(value,0)


if __name__ == '__main__':unittest.main()
