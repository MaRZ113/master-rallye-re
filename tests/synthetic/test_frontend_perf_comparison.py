import json,tempfile,unittest
from pathlib import Path
from tools.vehicle_frontend_perf_native import STAGES,RETAIL_SHA256
from tools.compare_frontend_perf_captures import compare


class FrontendPerfComparisonTests(unittest.TestCase):
    def test_count_mismatch_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a.json';b=Path(td)/'b.json'
            def row(calls,time):return {'status':'CAPTURED_NATIVE_FRONTEND_COUNTERS','exe_sha256':RETAIL_SHA256,'label':'Lancer-reentry','interval_summary':[{'stage':r[0],'calls':calls,'total_ms':time} for r in STAGES]}
            a.write_text(json.dumps(row(80,4000)));b.write_text(json.dumps(row(40,40)));r=compare(a,b)
            self.assertFalse(r['stages'][0]['equal_call_counts']);self.assertIsNotNone(r['stages'][0]['comparison_caution']);self.assertAlmostEqual(r['stages'][0]['average_call_ratio_after_before'],.02)

    def test_wrong_target_and_labels_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a.json';b=Path(td)/'b.json';value={'status':'CAPTURED_NATIVE_FRONTEND_COUNTERS','exe_sha256':RETAIL_SHA256,'label':'Lancer-cold','interval_summary':[{'stage':r[0],'calls':1,'total_ms':1} for r in STAGES]}
            a.write_text(json.dumps(value));value['label']='Pajero-cold';b.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'labels'):compare(a,b)
            value['exe_sha256']='0'*64;b.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'unqualified'):compare(a,b)
