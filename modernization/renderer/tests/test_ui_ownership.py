import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analyze_ui_ownership import analyze


def draw(entity,packet,identity=1,owner=None):
    return {
        'native_entity_pointer':entity,'native_packet_pointer':packet,
        'point_storage':packet+0x54,'content_storage':packet+0x1234,'packet_mode':1,
        'capture_local_identity_id':identity,'owner_mapping_status':'mapped' if owner else 'unmapped',
        'owner_name':owner,'draw_signature_status':'verified_ui_draw_signature',
    }


def write_frame(path,capture_id,records,*,complete=True,overflow=False,device=3,exe='exe',proxy='dll',pause_state=None):
    probe={
        'capture_id':capture_id,'complete':complete,'overflow':overflow,
        'unmapped':any(r.get('owner_mapping_status')!='mapped' for r in records),
        'coverage_status':'overflow' if overflow else 'complete' if complete else 'incomplete',
        'record_drops':1 if overflow else 0,'identity_registry_overflow':0,
        'draw_attempts':len(records)+(1 if overflow else 0),'draw_records':len(records),
        'owner_mapping_status':'unmapped','draw_records':records,
    }
    rows=[{'type':'frame_begin','device':device,'frame':1,'capture_id':capture_id,
           'exe_sha256':exe,'proxy_sha256':proxy,'ui_margins':{'ui_ownership_probe':probe}},
          {'type':'race_epoch_snapshot','pause_menu':{
              'available':pause_state is not None,'enabled':pause_state,
              'read_only':True,'source':'existing_typed_race_broker_reader',
              'status':'typed_bool_read_only' if pause_state is not None else 'missing_wrong_type_or_unreadable'}},
          {'type':'frame_end','complete':complete and not overflow}]
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')


class UiOwnershipAnalyzerTests(unittest.TestCase):
    def test_pair_distinguishes_shared_and_paused_only_without_semantic_claim(self):
        with tempfile.TemporaryDirectory() as d:
            normal=Path(d)/'normal.jsonl';paused=Path(d)/'paused.jsonl'
            write_frame(normal,'d3-f10',[draw(10,20),draw(11,21,2)])
            write_frame(paused,'d3-f11',[draw(10,20),draw(12,22,3)])
            report=analyze(normal,paused)
            self.assertEqual(report['status'],'READY_FOR_A3H_ANALYSIS')
            diff=report['raw_identity_comparison']
            self.assertEqual(len(diff['shared_raw_tuples']),1)
            self.assertEqual(len(diff['normal_only_raw_tuples']),1)
            self.assertEqual(len(diff['paused_only_raw_tuples']),1)
            self.assertFalse(report['semantic_pause_ownership_proven'])
            self.assertIn('does not prove PauseMenu',report['warning'])

    def test_same_session_hash_device_and_capture_end_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);normal=root/'normal.jsonl';paused=root/'paused.jsonl';session=root/'session.jsonl'
            write_frame(normal,'d3-f10',[draw(10,20)])
            write_frame(paused,'d3-f11',[draw(10,20)])
            session.write_text('\n'.join(json.dumps(r) for r in [
                {'type':'session','exe_sha256':'exe','proxy_sha256':'dll'},
                {'type':'ui_ownership_capture_end','capture_id':'d3-f10','complete':True},
                {'type':'ui_ownership_capture_end','capture_id':'d3-f11','complete':True},
            ])+'\n',encoding='utf-8')
            report=analyze(normal,paused,session)
            self.assertTrue(report['session_validation']['same_session_supported'])

    def test_overflow_downgrades_pair_status(self):
        with tempfile.TemporaryDirectory() as d:
            normal=Path(d)/'normal.jsonl';paused=Path(d)/'paused.jsonl'
            write_frame(normal,'d3-f10',[draw(10,20)],overflow=True)
            write_frame(paused,'d3-f11',[draw(10,20)])
            report=analyze(normal,paused)
            self.assertEqual(report['status'],'INCOMPLETE_CAPTURE')
            self.assertTrue(report['capture_pair']['normal']['health']['overflow'])

    def test_changed_packet_tuple_and_known_name_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as d:
            normal=Path(d)/'normal.jsonl';paused=Path(d)/'paused.jsonl'
            write_frame(normal,'d3-f10',[draw(10,20)])
            write_frame(paused,'d3-f11',[draw(10,30,1,'PauseMenuTiles')])
            report=analyze(normal,paused)
            self.assertEqual(report['owner_mapping']['known_owner_names'],['PauseMenuTiles'])
            self.assertEqual(report['owner_mapping']['status'],'mapped')
            self.assertEqual(len(report['raw_identity_comparison']['entities_with_changed_packet_identity_sets']),1)

    def test_typed_pause_signal_is_reported_without_promoting_owner_semantics(self):
        with tempfile.TemporaryDirectory() as d:
            normal=Path(d)/'normal.jsonl';paused=Path(d)/'paused.jsonl'
            write_frame(normal,'d3-f10',[draw(10,20)],pause_state=False)
            write_frame(paused,'d3-f11',[draw(10,20)],pause_state=True)
            report=analyze(normal,paused)
            signal=report['pause_state_signal']
            self.assertTrue(signal['normal_capture']['read_only'])
            self.assertFalse(signal['normal_capture']['enabled'])
            self.assertTrue(signal['paused_capture']['enabled'])
            self.assertTrue(signal['typed_values_differ'])
            self.assertFalse(report['semantic_pause_ownership_proven'])


if __name__=='__main__':
    unittest.main()
