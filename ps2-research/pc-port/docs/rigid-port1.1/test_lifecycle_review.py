"""Synthetic offline review tests, no native process or proprietary fixture."""
import copy
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[2] / "tools/rigid_lifecycle_review.py"
spec = importlib.util.spec_from_file_location("lifecycle_review", path)
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


def synthetic():
    header = {"event":"header", "schema":"mrr-rigid-readonly-v1", "engine_calls":False,
              "process_writes":False, "process":{"sha256":r.EXE_SHA, "image_base":0x400000}}
    result = [header]
    for index,count in enumerate((0,1,0,1,0)):
        instance = {"instance":0x10000+index*0x100, "body":0x20000+index*0x100,
                    "egg_name_id":55, "status":"READ_SNAPSHOT_NOT_ATOMIC",
                    "native_nonvehicle_position":[1.,2.,3.]}
        result.append({"event":"snapshot", "sequence":index, "monotonic_seconds":index*.1,
            "status":"READ_SNAPSHOT_NOT_ATOMIC", "read_bytes":156,
            "native_instance_vector_count":count, "selected_count":count,
            "instances":[instance] if count else [], "selection_truncated":False})
    return result


class ReviewTests(unittest.TestCase):
    def test_membership_is_not_destruction_or_contact(self):
        result = r.summarize(synthetic())
        self.assertEqual([x['native_count'] for x in result['vector_membership_changes']],[0,1,0,1,0])
        self.assertEqual(result['native_destruction'],'UNKNOWN')
        self.assertEqual(result['vehicle_contact'],'NOT_PROVED')
        self.assertEqual(result['physics_thread'],'UNKNOWN')
        self.assertTrue(all(x['runtime_role']=='UNKNOWN' for x in result['observed_pointer_pairs']))

    def test_exact_identity_and_readonly_header_required(self):
        for key,value in (("engine_calls",True),("process_writes",True),("schema","unknown")):
            rows=synthetic();rows[0][key]=value
            with self.assertRaises(ValueError):r.summarize(rows)
        rows=synthetic();rows[0]['process']['sha256']='00'*32
        with self.assertRaises(ValueError):r.summarize(rows)

    def test_invalid_sequence_time_budget_and_count(self):
        for key,value in (("sequence",99),("monotonic_seconds",float('nan')),
                          ("monotonic_seconds",62),("read_bytes",65537),("selected_count",2)):
            rows=synthetic();rows[1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.summarize(rows)

    def test_failed_read_does_not_create_empty_scene_claim(self):
        rows=synthetic();rows[3]={'event':'snapshot','sequence':2,'monotonic_seconds':.2,
                               'status':'FAILED_CLOSED','read_bytes':4}
        result=r.summarize(rows)
        self.assertEqual(result['status_counts']['FAILED_CLOSED'],1)
        self.assertNotIn(2,[x['sequence'] for x in result['vector_membership_changes']])

    def test_repeated_pointer_is_not_generation_proof(self):
        rows=synthetic();rows[4]['instances'][0]=copy.deepcopy(rows[2]['instances'][0])
        result=r.summarize(rows)
        self.assertEqual(len(result['observed_pointer_pairs']),1)
        self.assertEqual(result['observed_pointer_pairs'][0]['pointer_generation'],'NOT_ESTABLISHED')

    def test_nonfinite_position_rejected(self):
        rows=synthetic();rows[2]['instances'][0]['native_nonvehicle_position'][0]=float('inf')
        with self.assertRaises(ValueError):r.summarize(rows)

    def test_deterministic_and_bounded(self):
        rows=synthetic();self.assertEqual(r.summarize(rows),r.summarize(rows))
        with self.assertRaises(ValueError):r.summarize([rows[0]]*1202)

    def test_debugger_join_requires_exact_instance_body_pair(self):
        passive=r.summarize(synthetic());p=passive['observed_pointer_pairs'][0]
        text=f"RIGID_PROBE event=instance_clone_enter tid=1234 ip=00621220 ecx={p['instance']:X} arg0=30000 hit=1\n"
        text+=f"RIGID_PROBE event=body_bind_enter tid=1234 ip=00621310 ecx={p['instance']:X} arg0={p['body']:X} hit=1\n"
        result=r.summarize_debugger(text,passive)
        self.assertTrue(result['clone_body_passive_links'][0]['exact_passive_pointer_pair_match'])
        self.assertEqual(result['native_prop_admission'],'NOT_PROVED')
        self.assertTrue(result['target_body_destruction'].startswith('NOT_PROVED'))
        changed=text.replace(f"arg0={p['body']:X}","arg0=50000")
        self.assertFalse(r.summarize_debugger(changed,passive)['clone_body_passive_links'][0]['exact_passive_pointer_pair_match'])

    def test_independent_hit_counters_not_paired_by_equal_hits(self):
        text="RIGID_PROBE event=instance_cache_clear_enter tid=1234 ip=0056FCE0 ecx=30000 hit=1\n"
        text+="RIGID_PROBE event=physics_update_enter tid=1234 ip=0043F2C0 ecx=40000 hit=1\n"
        text+="RIGID_PROBE event=instance_cache_clear_enter tid=1234 ip=0056FCE0 ecx=30000 hit=2\n"
        result=r.summarize_debugger(text,r.summarize(synthetic()))
        self.assertEqual(result['update_followed_by_clear_observations'][0]['clear_line'],3)
        with self.assertRaises(ValueError):r.summarize_debugger(text.replace('hit=2','hit=17'),r.summarize(synthetic()))


if __name__=='__main__':unittest.main()
