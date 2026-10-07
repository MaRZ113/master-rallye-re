import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analyze_vehicle_identity import summarize,compare,resource_family
from analyze_vehicle_draws import reflection_audit
from trace_common import TARGET_SHA

class IdentityEvidenceTests(unittest.TestCase):
    def test_unknown_incomplete_and_count_fail_closed(self):
        h={'type':'frame_begin','exe_sha256':TARGET_SHA};end={'type':'frame_end','complete':True,'truncated':False,'dropped_records':0,'draw_records':0}
        self.assertTrue(summarize([h,end])['exact_complete'])
        for rows in ([dict(h,exe_sha256='unknown'),end],[h,dict(end,truncated=True)],[h,dict(end,draw_records=1)],[h]):
            self.assertFalse(summarize(rows)['exact_complete']);self.assertEqual(summarize(rows)['groups'],[])
    def test_cli_output_stays_in_renderer_phase(self):
        result=subprocess.run([sys.executable,str(ROOT/'tools/analyze_vehicle_identity.py'),str(ROOT/'.analysis/absent-input.jsonl'),'--output',str(ROOT.parent/'forbidden-output.json')],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('Output must stay in renderer phase',result.stderr)
    def test_resource_family_ignores_material_preserves_generations(self):
        s={'streams':[{'last_creation_serial':1,'stride':36}],'indices':{'last_creation_serial':2},'vertex_shader':0x152,'textures':[{'last_creation_serial':3}]}
        a=resource_family(s);s['textures'][0]['last_creation_serial']=99;self.assertEqual(resource_family(s),a)
        s['indices']['last_creation_serial']=8;self.assertNotEqual(resource_family(s),a)
        s['indices']['last_creation_serial']=0;self.assertEqual(resource_family(s),0)
    def test_pair_requires_provenance_epoch_and_unique_track(self):
        x={'exact_complete':True,'header':{'proxy_sha256':'p','exe_sha256':TARGET_SHA,'device':1},'classifier':{'epoch':3},'groups':[{'track':7,'draws':[{'signature':1}]}]}
        y=copy.deepcopy(x);self.assertEqual(compare(x,y,7)['shared_signatures'],1)
        for changed in ('device','proxy_sha256'):
            y=copy.deepcopy(x);y['header'][changed]='different'
            with self.assertRaises(ValueError):compare(x,y,7)
        y=copy.deepcopy(x);y['classifier']['epoch']=4
        with self.assertRaises(ValueError):compare(x,y,7)
        with self.assertRaises(ValueError):compare(x,x,8)
    def test_native_replay_of_sampled_brake_and_stationary_data(self):
        evidence=json.loads((ROOT/'research/r-gfx4/continuation3-runtime-evidence.json').read_text(encoding='utf-8'));by={f['file']:f for f in evidence['frames']}
        def scene(frame):
            candidate=next(c for c in frame['structural_candidates'] if c['four_wheel_geometry']);tracks={candidate['chassis_track'],*candidate['wheel_tracks']}
            return [g for g in frame['groups'] if g['track'] in tracks]
        before=scene(by['brake-off-cam2.jsonl']);after=scene(by['brake-on-cam2.jsonl']);stationary=scene(by['onstart_race_restart.jsonl'])
        for frames in ([before]*5+[after]+[before],[stationary]*5):
            words=[str(len(frames))]
            for groups in frames:
                words.append(str(len(groups)))
                for g in groups:
                    words.extend(map(str,g['world']));words.append(str(len(g['draws'])))
                    for d in g['draws']:words.extend(str(d[k]) for k in ('signature','resource_family','fvf','reasons','triangles'))
            result=subprocess.run([str(ROOT/'.build-msvc/Release/identity_tests.exe'),'--replay'],input=' '.join(words)+'\n',capture_output=True,text=True,check=True)
            rows=[json.loads(x) for x in result.stdout.splitlines()]
            self.assertEqual(rows[3]['source'],'structural');self.assertGreater(rows[4]['eligible'],0)
            if len(rows)==7:
                self.assertEqual(rows[4]['constellation'],rows[5]['constellation']);self.assertEqual(rows[4]['track'],rows[5]['track']);self.assertEqual(rows[5]['source'],'retained');self.assertEqual(rows[5]['mutations'],1);self.assertGreater(rows[5]['eligible'],0)
                self.assertLess(rows[5]['eligible'],rows[4]['eligible'])
    def test_native_brake_capture_stock_layers_and_identity_fields(self):
        import hashlib
        release=ROOT/'.build-msvc/Release';digest=hashlib.sha256((release/'reflection_tests.exe').read_bytes()).hexdigest();verified=0
        for p in (release/'MRRRenderer/logs').glob('frame*.jsonl'):
            rows=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
            if rows[0].get('proxy_version')!='R-GFX5-1' or rows[0].get('exe_sha256')!=digest:continue
            draws=[d for d in rows if d.get('type')=='draw'];brakes=[d for d in draws if d.get('race_context') and d['state']['vertex_shader']==0x102]
            if not brakes:continue
            self.assertEqual(len(brakes),2)
            for d in brakes:
                self.assertEqual(d['object_class'],'VEHICLE_BODY');self.assertTrue(d['constellation_id']);self.assertFalse(d['reflection_eligible']);self.assertFalse(d['reflection_modified']);self.assertFalse(d['native_override_applied'])
            modified=[d for d in draws if d.get('native_override_applied')];self.assertTrue(modified)
            for d in modified:self.assertEqual(d['object_identity_source'],'retained');self.assertEqual(d['constellation_id'],brakes[0]['constellation_id'])
            self.assertEqual(reflection_audit(rows,True)['status'],'AUTOMATED_TRACE_PASS');verified+=1
        self.assertGreaterEqual(verified,2)
