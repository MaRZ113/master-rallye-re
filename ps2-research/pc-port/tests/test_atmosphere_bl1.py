import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PORT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('atmosphere_bl1_audit',PORT/'tools/analyze_atmosphere_bl1.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class LogAuditTests(unittest.TestCase):
    def test_malformed_json_is_reported_with_exact_line_and_valid_records_survive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'session-test.jsonl').write_text('\n'.join([
                json.dumps({'type':'frame_summary','frame':540}),
                '{"type":"freecam_window_input","activation_result":inactive}',
                json.dumps({'type':'atmosphere_sky_selection','requested':3,'original':0,'effective':0,'reason':'network_players_record_unready_or_wrong_type'}),
                json.dumps({'type':'resource_create','method':'CreateTexture','frame':593,'serial':747,'arguments':[256,256,0,0,21]})
            ]))
            r=audit.analyze(p)['sessions'][0]
            self.assertEqual([x['line'] for x in r['invalid_json']],[2])
            self.assertEqual(r['atmosphere_events'][0]['preceding_summary_frame'],540)
            self.assertEqual(r['textures_256'][0]['serial'],747)
    def test_capture_keeps_sky_resource_serial_and_complete_marker(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'frame-test.jsonl').write_text('\n'.join(map(json.dumps,[
                {'type':'draw','arguments':[4,0,134,0,196],'state':{'vertex_shader':258,'textures':[{'last_creation_serial':747}]}},
                {'type':'draw','arguments':[4,0,20,0,8],'state':{'render_states':{'28':1,'34':0xffdddbdb}}},
                {'type':'frame_end','complete':True,'dropped_records':0}
            ])))
            r=audit.analyze(p)['captures'][0]
            self.assertEqual(r['sky_draws'][0]['texture']['last_creation_serial'],747)
            self.assertEqual(r['world_fog_colors'],['0xFFDDDBDB'])
            self.assertTrue(r['end']['complete'])
if __name__=='__main__':unittest.main()
