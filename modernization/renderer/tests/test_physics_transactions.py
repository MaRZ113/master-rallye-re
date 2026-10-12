import copy
import importlib.util
from pathlib import Path
import unittest

TOOL=Path(__file__).resolve().parents[1]/"tools/analyze_physics_transactions.py"
spec=importlib.util.spec_from_file_location("physics_transactions",TOOL)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Transactions(unittest.TestCase):
    def fixture(self):
        rows=[{"type":"physics_probe_setup","installed":True,"exact_retail_build":True},
            {"type":"physics_probe_summary","patch_restored":True,"counts":{}},
            {"type":"physics_probe_transaction_summary","important_overflow":0,"diagnostic_overflow":0,"pairing_failures":0,"unknown_transitions":0,"zero_stores_suppressed":522}]
        for i,(kind,site,b,a) in enumerate([
            ("flag_store","0x004CCFF1",0,1),("matrix_complete","0x004CD131",1,1),
            ("controller_consumption","0x00443827",1,1),("flag_store","0x00591345",1,0),
            ("controller_consumption","0x00443827",0,0)],1):
            rows.append(dict(type="physics_probe_transaction_event",event_sequence=i,reset_transaction_candidate_id=1,
                event_kind=kind,native_callsite=site,store_completion_observed=True,store_result_matches_operand=True,native_store_value=a,flag_value_before=b,flag_value_after=a,qpc_timestamp=i*100,qpc_after=i*100+5,
                race_generation=7,owner_lifetime=1,controller_identity="0x02CDEF30",controller_identity_generation=1,
                controller_backing_pointer="0x02D04168",reset_manager_identity="0x11223344",participant_index=0,
                thread_id=123,current_human_candidate=True,race_context_valid=True,observation_readable=True,
                unknown_transition_before=False,transform_bits=["0x00000000"]*16,transform_bits_before=["0x00000000"]*16,
                transform_digest="digest"))
        return rows
    def good(self,rows): return module.audit(rows)["status"]=="STOCK_TRANSACTION_CORRELATED"
    def test_complete_observed_interval_never_authorizes_teleport(self):
        report=module.audit(self.fixture());self.assertTrue(self.good(self.fixture()))
        self.assertFalse(report["one_shot_guaranteed"]);self.assertFalse(report["teleport_authorized_by_this_report"])
    def test_old_log_clear_before_consumer_is_not_correlated(self):
        rows=self.fixture();rows[6]["qpc_timestamp"]=50;rows[6]["qpc_after"]=55;self.assertFalse(self.good(rows))
    def test_duplicate_consumption_counted_not_single_use(self):
        rows=self.fixture();extra=copy.deepcopy(rows[5]);extra.update(event_sequence=4,qpc_timestamp=350,qpc_after=355)
        for row in rows[6:]:row["event_sequence"]+=1
        rows.append(extra);report=module.audit(rows);self.assertTrue(self.good(rows));self.assertTrue(report["transactions"][0]["repeated_application_observed"])
    def test_two_publication_intervals_cannot_share_clear(self):
        rows=self.fixture();rows[6]["reset_transaction_candidate_id"]=2;self.assertFalse(self.good(rows))
    def test_repeated_publication_same_id_is_not_complete(self):
        rows=self.fixture();rows.append(copy.deepcopy(rows[3]));self.assertFalse(self.good(rows))
    def test_matrix_mismatch(self):
        rows=self.fixture();rows[5]["transform_bits_before"][0]="0xFFFFFFFF";self.assertFalse(self.good(rows))
    def test_missing_clear(self):
        rows=self.fixture();del rows[6];self.assertFalse(self.good(rows))
    def test_cross_thread_is_unproved(self):
        rows=self.fixture();rows[6]["thread_id"]=999;self.assertFalse(self.good(rows))
    def test_race_or_pointer_reuse(self):
        for key,value in [("race_generation",8),("owner_lifetime",2),("controller_identity_generation",2),("controller_backing_pointer","0x99887766")]:
            rows=self.fixture();rows[5][key]=value;self.assertFalse(self.good(rows))
    def test_every_loss_and_unknown_transition_fails_closed(self):
        for key in ["important_overflow","diagnostic_overflow","pairing_failures","unknown_transitions","in_flight_store_observations"]:
            rows=self.fixture();rows[2][key]=1;self.assertFalse(self.good(rows))
        rows=self.fixture();rows[5]["unknown_transition_before"]=True;self.assertFalse(self.good(rows))
    def test_stale_owner_invalid_context_and_partial_install(self):
        for key in ["current_human_candidate","race_context_valid","observation_readable"]:
            rows=self.fixture();rows[5][key]=False;self.assertFalse(self.good(rows))
        for index,key in [(0,"installed"),(0,"exact_retail_build"),(1,"patch_restored")]:
            rows=self.fixture();rows[index][key]=False;self.assertFalse(self.good(rows))
    def test_pause_does_not_authorize_writes(self):
        rows=self.fixture()
        for row in rows[3:]:row["pause_state"]="paused"
        self.assertTrue(self.good(rows));self.assertFalse(module.audit(rows)["teleport_authorized_by_this_report"])
    def test_native_manager_and_participant_contract(self):
        for key,value in [("reset_manager_identity","0x55667788"),("participant_index",None),("participant_index",8)]:
            rows=self.fixture();rows[4][key]=value;self.assertFalse(self.good(rows))
    def test_unknown_unpublished_interval(self):
        rows=self.fixture()
        for row in rows[3:]:row["reset_transaction_candidate_id"]=0
        self.assertFalse(self.good(rows));self.assertEqual(len(module.audit(rows)["unattributed_event_sequences"]),5)
if __name__=="__main__":unittest.main()
