import json,struct,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from tools.vehicle_frontend_perf_native import STAGES,STATE_BYTES,COUNTER_STRIDE
from tools.vehicle_frontend_perf_capture import decode,difference,find_binding,verify_decoder,DECODER_CALL,ORIGINAL_DECODER
from tools.vehicle_frontend_complexity import analyze_model,analyze_renderer_log
from test_library import simple_record,synthetic_dx,footer56
from tools.capture_frontend_performance import running_game_pid,output_name


class FrontendPerfCaptureTests(unittest.TestCase):
    def binding(self):return {'state_va':0x10024e00,'state_bytes':STATE_BYTES,'counter_stride':COUNTER_STRIDE,'stages':[{'name':r[0]} for r in STAGES]}

    def test_decode_deltas_and_busy_rejection(self):
        binding=self.binding();raw=struct.pack('<IIQQQ',0,2,500,400,100)*len(STAGES);rows=decode(raw,binding,1000)
        self.assertEqual(rows[0]['total_ms'],500);self.assertEqual(find_binding({'outer':binding})['decoder_path']['mode'],'original_scalar')
        final=decode(struct.pack('<IIQQQ',0,3,900,400,400)*len(STAGES),binding,1000)
        self.assertEqual(difference(rows,final)[0]['average_ms'],400)
        with self.assertRaises(ValueError):decode(struct.pack('<IIQQQ',1,2,500,400,100)*len(STAGES),binding,1000)
        with self.assertRaises(ValueError):difference(final,rows)

    def test_renderer_log_coverage_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'log.jsonl';path.write_text(json.dumps({'type':'resource_create','frame':7,'method':'CreateTexture','arguments':[8,4],'creation_caller':{'address':0x5589d0}})+'\nBAD\n')
            report=analyze_renderer_log(path);self.assertEqual(report['malformed_lines'],1);self.assertEqual(report['resource_frames'][0]['texture_source_bytes'],128)

    def test_model_static_inventory_preserves_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)];path=Path(td)/'complete.dx'
            path.write_bytes(synthetic_dx(points,[0,1,2],[simple_record(0,2,0,3)],[(0,0,3)],trailing=footer56(points)))
            (path.parent/'synthetic-tga.dxt').write_bytes(struct.pack('<5I',0xfeed,0,0,8,4)+bytes(128))
            report=analyze_model(path);self.assertEqual(report['unique_textures'],1);self.assertEqual(report['native_source_charge_bytes'],128);self.assertIn('not original native',report['boundary'])

    def test_auto_pid_and_safe_unique_output(self):
        from types import SimpleNamespace
        with patch('tools.capture_frontend_performance.subprocess.run',return_value=SimpleNamespace(stdout='1234\n')):self.assertEqual(running_game_pid(),1234)
        with patch('tools.capture_frontend_performance.subprocess.run',return_value=SimpleNamespace(stdout='1234\n5678\n')):
            with self.assertRaisesRegex(ValueError,'exactly one'):running_game_pid()
        self.assertTrue(output_name('Lancer','warm').endswith('-lancer-warm.json'))
        with self.assertRaises(ValueError):output_name('../Lancer','warm')

    def test_decoder_hook_distinguishes_identical_profiler_prefix(self):
        base=find_binding({'outer':self.binding()});fast=find_binding({'outer':self.binding(),'frontend_bulk_read':{'entry_va':0x10025da0}})
        def bytes_for(target):return b'\xe8'+struct.pack('<i',target-DECODER_CALL-5)
        self.assertTrue(verify_decoder(lambda at,size:bytes_for(ORIGINAL_DECODER),base)['verified'])
        self.assertEqual(verify_decoder(lambda at,size:bytes_for(0x10025da0),fast)['mode'],'canonical_loose_bulk')
        with self.assertRaisesRegex(ValueError,'does not match'):verify_decoder(lambda at,size:bytes_for(ORIGINAL_DECODER),fast)
        with self.assertRaisesRegex(ValueError,'does not match'):verify_decoder(lambda at,size:bytes_for(0x10025da0),base)
