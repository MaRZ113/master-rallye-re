import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analyze_vehicle_draws import reflection_audit,semantic_report,canonical_semantic_words

class LearnedSemanticCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        digest=hashlib.sha256((ROOT/'.build-msvc/Release/reflection_tests.exe').read_bytes()).hexdigest()
        cls.captures=[]
        for p in (ROOT/'.build-msvc/Release/MRRRenderer/logs').glob('frame*.jsonl'):
            with p.open(encoding='utf-8') as stream:header=json.loads(stream.readline())
            if header.get('proxy_version')!='R-GFX5-5' or header.get('exe_sha256')!=digest:continue
            rows=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
            if rows[0].get('proxy_version')=='R-GFX5-5' and rows[0].get('exe_sha256')==digest and any(d.get('vehicle_semantic_source')=='learned_signature' for d in rows):cls.captures.append(rows)
        if not cls.captures:raise AssertionError('Run current native lost-constellation integration first')
    def test_learned_modified_without_live_identity(self):
        for rows in self.captures:
            draws=[d for d in rows if d.get('vehicle_semantic_source')=='learned_signature']
            self.assertEqual(len(draws),2)
            for d in draws:
                self.assertTrue(d['reflection_eligible']);self.assertTrue(d['reflection_modified']);self.assertTrue(d['native_restore_success'])
                self.assertEqual(d['object_constellation_id'],0);self.assertNotEqual(d['object_class_at_draw'],'VEHICLE_BODY')
                self.assertTrue(d['semantic_signature_id']);self.assertEqual(d['semantic_signature_state'],'PROVEN_VEHICLE_BODY_ENV')
                self.assertEqual(len(canonical_semantic_words(d)),53)
            summary=next(r['classifier'] for r in rows if r.get('type')=='frame_summary')
            self.assertEqual(summary['vehicle_constellations'],0);self.assertEqual(summary['learned_vehicle_body_signatures'],2)
            self.assertEqual(summary['learned_signature_reflection_draws'],2);self.assertEqual(summary['live_constellation_reflection_draws'],0)
            self.assertEqual(reflection_audit(rows,True)['status'],'AUTOMATED_TRACE_PASS')
    def test_hud_and_wheels_stay_stock(self):
        for rows in self.captures:
            for d in rows:
                if d.get('type')=='draw' and (not d['race_context'] or d['state']['vertex_shader']==0x112):
                    self.assertFalse(d['reflection_modified']);self.assertFalse(d['reflection_eligible']);self.assertEqual(d['vehicle_semantic_source'],'none')
    def test_missing_or_corrupt_origin_fails_closed(self):
        base=self.captures[0]
        rows=[r for r in base if r.get('type')!='vehicle_semantic_signature']
        self.assertEqual(reflection_audit(rows,True)['status'],'FAIL')
        for key,value in [('origin_reason_mask',0),('origin_wheel_track_ids',[1,2,3,3]),('origin_grace_frames',1),('semantic_signature_state','UNKNOWN_SIGNATURE'),('learned_epoch',999),('learned_frame',999999),('resource_generations',[0,0,0,0])]:
            rows=copy.deepcopy(base)
            for r in rows:
                if r.get('type')=='vehicle_semantic_signature':r[key]=value
            self.assertEqual(reflection_audit(rows,True)['status'],'FAIL',key)
    def test_current_signature_and_material_must_match(self):
        base=self.captures[0]
        for mutation in ('range','generation','key','alpha','stock_tci','signature_hash'):
            rows=copy.deepcopy(base)
            for d in rows:
                if d.get('vehicle_semantic_source')!='learned_signature':continue
                if mutation=='range':d['arguments'][3]+=1
                elif mutation=='generation':d['state']['streams'][0]['last_creation_serial']+=1
                elif mutation=='key':d['semantic_signature_id']=999
                elif mutation=='alpha':d['state']['render_states']['27']=1
                elif mutation=='stock_tci':d['requested_stage1_tci']=0x30001
                elif mutation=='signature_hash':d['geometry_signature']+=1
            self.assertEqual(reflection_audit(rows,True)['status'],'FAIL',mutation)
        self.assertEqual(reflection_audit(base,False)['status'],'FAIL')
    def test_semantic_report_provenance(self):
        report=semantic_report(self.captures[0])
        self.assertEqual(len(report['proven_vehicle_body_signatures']),2)
        self.assertEqual(report['modified_provenance_counts'],{'learned_signature':2})
        self.assertGreater(report['draw_provenance_counts']['none'],0)

    def test_asset_proof_survives_unrelated_object_epoch_change(self):
        found=False
        for rows in self.captures:
            current=next(r['classifier']['epoch'] for r in rows if r.get('type')=='frame_summary')
            if any(r.get('type')=='vehicle_semantic_signature' and r['learned_epoch']<current for r in rows):
                found=True;self.assertEqual(reflection_audit(rows,True)['status'],'AUTOMATED_TRACE_PASS')
        self.assertTrue(found,'Native capture must exercise unrelated creation reuse/object epoch invalidation')
