import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from quality_research import (ROOT as TOOL_ROOT, TARGET, read_locked, output_guard,
    instructions, evaluate, signed_bits, capture_audit, FREEZE_CONTEXT, UI_CONTEXT)
from reference_ghidra import PATCHER_SHA
from trace_common import read_jsonl
from audit_quality_runtime import display_lifecycle

class QualityResearchTests(unittest.TestCase):
    def current_native_session(self):
        release=ROOT/'.build-msvc/Release'
        sha=hashlib.sha256((release/'quality_tests.exe').read_bytes()).hexdigest()
        matching=[]
        for path in (release/'MRRRenderer/logs').glob('session*.jsonl'):
            with path.open(encoding='utf-8-sig') as f:
                head=json.loads(f.readline())
            if head.get('exe_sha256')==sha and head.get('proxy_version')=='R-GFX5-8':
                matching.append(path)
        self.assertTrue(matching,'Run current native suites before Python')
        # Anchor IDs are session-local. Repeated identical native builds must
        # not merge separate lifetimes just because the executable hash matches.
        latest=max(matching,key=lambda p:(p.stat().st_mtime_ns,p.name))
        return read_jsonl(latest)

    def test_standard_hook_free_source_and_binary(self):
        source='\n'.join(p.read_text() for p in (ROOT/'src').glob('*.cpp'))
        for api in ('SetWindowsHookEx','UnhookWindowsHookEx','CallNextHookEx'):
            self.assertNotIn(api,source)
        self.assertNotIn('MRR_DIAGNOSTIC_NO_MESSAGE_HOOKS',(ROOT/'CMakeLists.txt').read_text())
        self.assertNotIn('--diagnostic-no-message-hooks',(ROOT/'tools/build.py').read_text())
        binary=(ROOT/'.build-msvc/Release/d3d8.dll').read_bytes()
        for name in (b'SetWindowsHookExW',b'SetWindowsHookExA',b'UnhookWindowsHookEx',b'CallNextHookEx'):
            self.assertNotIn(name+b'\x00',binary)
        self.assertIn(b'legacy_loading_attract_guard',binary)
        rows=[r['descriptor'] for r in self.current_native_session() if r.get('type')=='standard_hook_free_contract']
        self.assertEqual({r['display_effective'] for r in rows},{'Stock','Windowed','Borderless'})
        for r in rows:
            self.assertFalse(r['thread_message_hooks_enabled'])
            self.assertFalse(r['cursor_watch_installed'])
            self.assertEqual(r['display_watch'],'disabled_by_standard_policy')
            self.assertEqual(r['cursor_handling'],'present_polling_and_shutdown')
            self.assertEqual(r['window_message_telemetry'],'unavailable_hooks_retired')
            self.assertEqual(r['display_window_message_records'],0)

    def test_windowed_startup_axis_admission_trace(self):
        rows=self.current_native_session()
        candidates=[r for r in rows if r.get('type')=='windowed_resize_admission' and
                    (r.get('configured_initial_width'),r.get('configured_initial_height'))==(1280,720) and
                    (r.get('requested',{}).get('width'),r.get('requested',{}).get('height'))==(1447,720)]
        self.assertTrue(candidates)
        for r in candidates:
            self.assertEqual(r['decision'],'accepted_hwnd_client_change')
            self.assertTrue(r['initial_window_commit_complete'])
            self.assertTrue(r['resize_corroborated_by_hwnd'])
            self.assertEqual((r['normalized_logical']['width'],r['normalized_logical']['height']),(1447,720))
            self.assertEqual((r['effective_backbuffer_width'],r['effective_backbuffer_height']),(1447,720))

    def test_hidden_hwnd_nested_reset_without_message_hooks(self):
        rows=self.current_native_session()
        start=next(i for i,r in enumerate(rows) if r.get('type')=='display_contract_begin')
        end=next(i for i,r in enumerate(rows) if i>start and r.get('type')=='display_contract_end')
        nested=rows[start+1:end]
        size=[r for r in nested if r.get('type')=='display_window_message' and r.get('message')=='WM_SIZE']
        self.assertEqual(size,[]) # Retired hooks produce no fabricated pre/post records.
        ready=next(r for r in nested if r.get('type')=='display_reset_readiness')
        result=next(r for r in nested if r.get('type')=='display_native_attempt' and r.get('operation')=='Reset')
        self.assertLess(ready['event_sequence'],result['event_sequence'])
        self.assertEqual(ready['cooperative_hresult'],0x88760868)
        self.assertEqual(result['hresult'],0x88760868)
        self.assertEqual((result['sent']['width'],result['sent']['height'],result['sent']['windowed']),(640,480,0))
        self.assertEqual(result['successful_reset_epoch'],0)
        self.assertEqual(ready['window_context']['game_window_owner']['reason'],'unsupported_build')
        self.assertFalse(ready['window_context']['window_commit_in_progress'])
        self.assertEqual(ready['policy'],'diagnostic_only_no_retry_no_hresult_translation')

    def test_exclusive_diagnostic_cycles_and_budget(self):
        rows=self.current_native_session()
        diagnostic=display_lifecycle(rows)
        self.assertTrue(diagnostic['event_sequence_order_valid'])
        self.assertEqual(diagnostic['runtime_fix_verdict'],'UNKNOWN_HUMAN_REQUIRED')
        self.assertGreaterEqual(len(diagnostic['observed_reset_while_device_lost']),4)
        self.assertFalse(any(r.get('type') in ('display_window_message','display_message_budget_exhausted') for r in rows))
        loss=[r for r in rows if r.get('type')=='display_native_attempt' and r.get('operation')=='Reset' and
              r.get('hresult')==0x88760868 and r.get('requested',{}).get('width')==624]
        self.assertEqual(len(loss),3)
        device=loss[0]['device_lifetime_id']
        calls=[r for r in rows if r.get('type')=='display_native_attempt' and r.get('operation')=='Reset' and r.get('device_lifetime_id')==device]
        self.assertEqual([r['successful_reset_epoch'] for r in calls],[1,1,2,2,3,3,4,4,4])
        self.assertEqual([r['hresult'] for r in calls][-2:],[0x8876086c,0x80004005])
        self.assertTrue(all((r['sent']['width'],r['sent']['height'],r['sent']['windowed'])==(640,480,0) for r in calls))

    def test_audit_does_not_pair_stale_or_other_device_readiness(self):
        missing=[dict(type='display_reset_readiness',cooperative_hresult=0x88760868),
                 dict(type='display_native_attempt',operation='Reset',hresult=0)]
        self.assertEqual(display_lifecycle(missing)['observed_reset_while_device_lost'],[])
        self.assertIsNone(display_lifecycle(missing)['event_sequence_order_valid'])
        rows=[dict(type='display_reset_readiness',device_lifetime_id=1,cooperative_hresult=0x88760868,event_sequence=1),
              dict(type='display_native_attempt',operation='Reset',device_lifetime_id=2,hresult=0,event_sequence=2),
              dict(type='display_native_begin',operation='Reset',device_lifetime_id=1,event_sequence=3),
              dict(type='display_native_attempt',operation='Reset',device_lifetime_id=1,hresult=0,event_sequence=4)]
        self.assertEqual(display_lifecycle(rows)['observed_reset_while_device_lost'],[])
        rows[-1]['event_sequence']=5
        rows.insert(3,dict(type='display_reset_readiness',device_lifetime_id=1,cooperative_hresult=0x88760868,event_sequence=4))
        paired=display_lifecycle(rows)['observed_reset_while_device_lost']
        self.assertEqual(len(paired),1)
        self.assertEqual(paired[0]['native_hresult'],0) # The native result is data, never rewritten by the auditor.

    def test_deferred_messages_preserve_observation_order(self):
        rows=[dict(type='display_native_begin',event_sequence=2),
              dict(type='display_native_attempt',event_sequence=3),
              dict(type='display_window_message',event_sequence=1,device_lifetime_id=1,telemetry_deferred=True),
              dict(type='display_window_message',event_sequence=4,device_lifetime_id=1,telemetry_deferred=True)]
        report=display_lifecycle(rows)
        self.assertTrue(report['event_sequence_order_valid'])
        self.assertFalse(report['physical_write_order_valid'])
        rows[-1]['event_sequence']=1
        self.assertFalse(display_lifecycle(rows)['event_sequence_order_valid'])
        rows[-1]['event_sequence']=0
        self.assertFalse(display_lifecycle(rows)['event_sequence_order_valid'])
        rows[-1]['event_sequence']=4;rows[0]['event_sequence']=5
        self.assertFalse(display_lifecycle(rows)['event_sequence_order_valid'])

    def test_native_windowed_maximize_restore_telemetry(self):
        events=[r for r in self.current_native_session() if r.get('type')=='window_state_transition']
        maximized=[r for r in events if r.get('window_state')=='maximized']
        self.assertGreaterEqual(len(maximized),4)
        by_device={}
        for r in events:by_device.setdefault(r['device_lifetime_id'],[]).append(r)
        for device_events in by_device.values():
            for i,r in enumerate(device_events):
                if r['window_state']!='maximized':continue
                self.assertEqual(r['actual_client'],r['effective_backbuffer'])
                prior=[x for x in device_events[:i] if x['window_state']=='normal']
                self.assertTrue(prior)
                self.assertEqual(r['normal_target'],prior[-1]['normal_target'])
        self.assertTrue(any(any([r['window_state'] for r in group[i:i+3]]==['normal','maximized','normal'] for i in range(len(group)-2)) for group in by_device.values()))

    def test_native_consumer_anchor_provenance_preserves_animation(self):
        rows=[r for r in self.current_native_session() if r.get('type')=='ui_packet_lifetime' and r.get('event')=='consume']
        new=next(r for r in rows if r.get('anchor_new') and r.get('engine_x')==565)
        # Synthetic contracts create independent UiMargins instances in one
        # session. IDs are registry-local; do not merge their capture lifetimes.
        retained=[r for r in rows if r.get('anchor_id')==new['anchor_id'] and r.get('first_frame')==new['first_frame'] and r.get('entity')==new['entity'] and r.get('anchor_retained') and r.get('current_rule_match')==0]
        self.assertEqual(new['anchor_source'],'exact_historical_rule')
        self.assertEqual([r['engine_x'] for r in retained],[562,558])
        for r in retained:
            self.assertEqual(r['anchor_direction'],'right')
            self.assertEqual(r['anchor_source'],'retained_identity')
            self.assertAlmostEqual(r['effective_x']-r['engine_x'],new['effective_x']-new['engine_x'],places=3)
        duplicate=next(r for r in rows if r.get('anchor_id')==new['anchor_id'] and r.get('frame')==new['frame'] and not r.get('anchor_new'))
        self.assertFalse(duplicate['shifted']);self.assertEqual(duplicate['effective_x'],new['effective_x'])
        center=next(r for r in rows if r.get('engine_x')==300 and r.get('anchor_direction')=='none')
        self.assertEqual(center['effective_x'],300);self.assertEqual(center['anchor_id'],0)

    def test_native_short_grace_preserves_dynamic_coordinate(self):
        rows=self.current_native_session()
        retained=[r for r in rows if r.get('type')=='ui_packet_lifetime' and r.get('anchor_grace_retained')]
        self.assertTrue(retained)
        r=next(r for r in retained if r['engine_x']==550)
        self.assertEqual(r['anchor_direction'],'right')
        self.assertEqual(r['anchor_source'],'retained_identity')
        self.assertEqual(r['current_rule_match'],0)
        self.assertAlmostEqual(r['effective_x']-r['engine_x'],106.667,places=2)
        self.assertEqual(r['group_owner_status'],'not_proven')
        self.assertIsNone(r['group_id']);self.assertIsNone(r['group_direction'])

    def test_native_candidate_conflict_never_creates_group_inheritance(self):
        rows=self.current_native_session()
        candidates=[c for r in rows if r.get('type')=='ui_group_candidates' for c in r['candidates']]
        conflict=next(c for c in candidates if c['kind']=='content_storage' and c['strong_rule_conflict'])
        self.assertEqual(conflict['observed_member_count'],3)
        self.assertEqual(len(set(conflict['member_packet_ids'])),3)
        self.assertIsNone(conflict['group_id']);self.assertIsNone(conflict['group_direction'])
        center=next(r for r in rows if r.get('type')=='ui_packet_lifetime' and r.get('candidate_group_ids',{}).get('content_storage')==conflict['candidate_id'] and r.get('engine_x')==300)
        self.assertEqual(center['anchor_direction'],'none');self.assertEqual(center['effective_x'],300)

    def test_native_render_local_ui_coordinates_and_restore(self):
        records=[r for r in self.current_native_session() if r.get('type')=='ui_render_local']
        self.assertTrue(records)
        # The production wrapper contract injects one real restoration failure.
        self.assertEqual([r['restore_hresult'] for r in records if r['restore_hresult']],[0x88760868])
        self.assertGreaterEqual(sum(r['restore_hresult']==0 for r in records),8)
        for r in records:
            self.assertEqual(r['persistent_packet_writes'],0)
            self.assertEqual(r['override_path'],'draw_local_native_world_copy')
            self.assertAlmostEqual(r['effective_render_x']-r['native_world_x'],r['margin'],places=2)
        self.assertTrue(any(r['half_extra']==547 and r['effective_render_x']==1112 for r in records))

    def test_r_ui1_packet_to_draw_capture_is_bounded_and_fail_closed(self):
        rows=[r for r in self.current_native_session() if r.get('type')=='ui_packet_lifetime' and r.get('event')=='consume']
        self.assertTrue(rows)
        self.assertTrue(all(len(r.get('draw_observations',[]))<=8 for r in rows))
        capped=next(r for r in rows if r.get('draw_observations_dropped')==2)
        self.assertEqual(len(capped['draw_observations']),8)
        card=next(r for r in rows if r.get('engine_x')==375 and r.get('anchor_direction')=='left' and
                  r.get('current_rule_match')==0 and r.get('anchor_source')=='retained_identity')
        draw=next(d for d in card['draw_observations'] if d.get('caller_rva')==0x0016d7c4)
        self.assertEqual(card['screen_owner_status'],'not_proven')
        self.assertEqual(card['carousel_owner_status'],'not_proven')
        self.assertFalse(card['selection_state_read'])
        self.assertEqual(draw['fvf_value'],0x142)
        self.assertAlmostEqual(draw['margin_requested'],-106.6667,places=3)
        self.assertAlmostEqual(draw['margin_applied'],-106.6667,places=3)
        self.assertAlmostEqual(draw['native_world_x'],375,places=3)
        self.assertAlmostEqual(draw['effective_world_x'],268.3333,places=3)
        self.assertTrue(draw['restore_requested_original_exact'])
        self.assertTrue(draw['restore_succeeded'])
        self.assertFalse(draw['restore_readback_performed'])

    def test_r_ui1_final_row_policy_emits_actual_source_coordinate_decision(self):
        rows=self.current_native_session()
        packets=[r for r in rows if r.get('type')=='ui_packet_lifetime']
        matches=[(r,d) for r in packets for d in r.get('draw_observations',[]) if d.get('row_card_match')]
        self.assertTrue(matches,'Current native wrapper must emit real positive row decisions')
        self.assertTrue(any(r['anchor_direction']=='left' and d['margin_requested']<0 for r,d in matches))
        self.assertTrue(any(r['anchor_direction']=='none' and d['margin_requested']==0 for r,d in matches))
        for packet,draw in matches:
            self.assertEqual(packet['packet_mode'],1)
            self.assertAlmostEqual(draw['packet_y'],309,places=3)
            self.assertEqual((draw['caller_rva'],draw['fvf_value'],draw['primitive_type'],draw['primitive_count']),
                             (0x0016d7c4,0x142,4,1))
            self.assertTrue(draw['scene_context_frontend_allowed'])
            self.assertEqual(draw['carousel_row_reason'],'verified_card_row')
            self.assertEqual(draw['carousel_render_policy'],'source_coordinates')
            self.assertEqual(draw['margin_effective_request'],0)
            self.assertEqual(draw['margin_applied'],0)
            self.assertFalse(draw['temporary_set_attempted'])
            self.assertFalse(draw['restore_attempted'])
            self.assertEqual(packet['persistent_packet_writes'],0)
        local=[r for r in rows if r.get('type')=='ui_render_local' and r.get('device_id')==9901]
        pair=[r for r in local if r.get('row_card_match')]
        self.assertEqual(len(pair),2) # Both subdraws share the zero-margin rule.
        self.assertEqual([r['draw_hresult'] for r in pair],[0x80004005,0])
        for r in pair:
            self.assertEqual(r['effective_render_x'],r['native_world_x'])
            self.assertEqual(r['margin_effective_request'],0)
        border=next(r for r in local if r['native_y']==304)
        self.assertFalse(border['row_card_match'])
        self.assertEqual(border['carousel_row_reason'],'outside_card_row')
        self.assertEqual(border['effective_render_x'],371)

    def test_r_ui1_d2_f10_rearms_and_promotes_only_drawn_packets(self):
        rows=self.current_native_session()
        starts=[r for r in rows if r.get('type')=='ui_diagnostic_capture_start' and r.get('capture_id')]
        ends=[r for r in rows if r.get('type')=='ui_diagnostic_capture_end' and r.get('capture_id')]
        by_device={}
        for r in starts:by_device.setdefault(r['device_id'],set()).add(r['capture_id'])
        device=next((d for d,ids in by_device.items() if len(ids)>=2 and
                     sum(r.get('device_id')==d and r.get('reason')=='present' and r.get('promoted_packet_records',0)>0 for r in ends)>=2),None)
        self.assertIsNotNone(device,'same-device repeated F10 captures must each emit packet evidence')
        device_ends=[r for r in ends if r['device_id']==device and r.get('reason')=='present' and r.get('promoted_packet_records',0)>0]
        self.assertGreaterEqual(len(device_ends),2)
        self.assertEqual(len({r['capture_id'] for r in device_ends}),len(device_ends))
        self.assertTrue(all(r['capture_record_budget_limit']==256 and r['capture_records_emitted']>0 for r in device_ends))
        frame_summaries={r['capture_id']:r for r in rows if r.get('type')=='frame_summary' and r.get('capture_id')}
        self.assertTrue(all(r['capture_id'] in frame_summaries for r in device_ends))
        self.assertTrue(all(frame_summaries[r['capture_id']]['ui_margins']['capture_id']==r['capture_id'] for r in device_ends))
        self.assertTrue(all(frame_summaries[r['capture_id']]['frame']==r['trace_frame'] for r in device_ends))
        # The same-device pair proves re-arming; the independent native
        # carousel stress capture proves non-drawing admission and both strata.
        self.assertTrue(any(r.get('packet_consumers_without_relevant_draw',0)>0 for r in ends))
        self.assertTrue(any(r.get('promoted_adjusted_packets',0)>0 and r.get('promoted_unadjusted_packets',0)>0 for r in ends))
        for end in device_ends:
            packets=[r for r in rows if r.get('type')=='ui_packet_lifetime' and r.get('capture_id')==end['capture_id']]
            self.assertEqual(len(packets),end['capture_records_emitted'])
            self.assertTrue(all(r.get('trace_frame')==end['trace_frame'] and r.get('capture_frame_index')==end['trace_frame']-end['start_frame'] for r in packets))
            self.assertTrue(all(r.get('draw_observations') for r in packets))
            self.assertTrue(all(d.get('diagnostic_relevant') for r in packets for d in r['draw_observations']))
            self.assertLessEqual(end['draw_observations_captured'],64*8)

    def test_native_exclusive_mode_ownership_and_bounded_rejection(self):
        rows=self.current_native_session()
        calls=[r for r in rows if r.get('type')=='display_native_attempt' and r.get('display_requested')=='ExclusiveFullscreen']
        self.assertTrue(calls)
        successful=[r for r in calls if r['hresult']==0]
        self.assertTrue(successful)
        for r in successful:
            self.assertEqual(r['sent']['windowed'],0)
            self.assertEqual(r['returned']['windowed'],0)
            self.assertEqual(r['display_effective'],'ExclusiveFullscreen')
            self.assertEqual(r['sent']['interval'],0)
        followup=[r for r in successful if r['operation']=='Reset' and r['requested']['width']==656]
        self.assertGreaterEqual(len(followup),2)
        for r in followup:
            self.assertEqual((r['sent']['width'],r['sent']['height']),(640,480))
        rejected=[r for r in calls if r['operation'].endswith('validation_rejected')]
        self.assertGreaterEqual(len(rejected),4)
        self.assertTrue(all(r['hresult']==0x8876086a for r in rejected))
        self.assertTrue(any(r['sent']['multisample']==4 for r in successful))
        self.assertTrue(any(r['sent']['multisample']==0 for r in successful))
        coop=[r for r in rows if r.get('type')=='display_cooperative_transition' and r['display']=='ExclusiveFullscreen']
        self.assertEqual([r['hresult'] for r in coop],[0,0x88760868,0x88760869,0])

    def test_production_ui_draw_capture_has_native_only_world_pair(self):
        release=ROOT/'.build-msvc/Release'
        sha=hashlib.sha256((release/'quality_tests.exe').read_bytes()).hexdigest()
        matches=[]
        for path in (release/'MRRRenderer/logs').glob('frame*.jsonl'):
            with path.open(encoding='utf-8-sig') as f: head=json.loads(f.readline())
            if head.get('exe_sha256')==sha and head.get('proxy_version')=='R-GFX5-8':
                rows=read_jsonl(path)
                if any(r.get('type')=='draw' and r.get('feature_mask',0)&128 for r in rows):matches.append((path.stat().st_mtime_ns,rows))
        self.assertTrue(matches)
        # Select the focused production-wrapper capture; later F10 captures
        # intentionally exercise additional UI/failure paths on that device.
        focused=[m for m in matches if len([r for r in m[1] if r.get('type')=='draw'])==8]
        self.assertTrue(focused)
        rows=max(focused,key=lambda r:r[0])[1]
        self.assertTrue(rows[-1]['complete']);self.assertFalse(rows[-1]['truncated'])
        draws=[r for r in rows if r.get('type')=='draw']
        self.assertEqual(len(draws),8)
        self.assertEqual(draws[0]['caller']['return_rva'],0x16d7c4)
        original=draws[0]['state']['matrices']['256']
        self.assertEqual(original['values'][12],565)
        self.assertEqual(draws[0]['effective_state']['world_translation_x'],1112)
        self.assertTrue(all(r['effective_state']['world_translation_x']==565 and not r['feature_mask']&128 for r in draws[1:]))
        overrides=[r for r in rows if r.get('native_only') and r.get('method')=='SetTransform' and r.get('feature_mask',0)&128]
        self.assertEqual(len(overrides),2)
        self.assertEqual(overrides[1]['effective_payload_bits'],original['bits'])
        self.assertLess(overrides[0]['sequence'],draws[0]['sequence'])
        self.assertLess(draws[0]['sequence'],overrides[1]['sequence'])
        self.assertLess(overrides[1]['sequence'],draws[1]['sequence'])

    def test_old_restore_risk_is_labeled_synthetic_not_runtime(self):
        proof=json.loads((ROOT/'research/r-gfx5/legacy-restore-diagnostics.json').read_text())
        self.assertEqual(proof['diagnostic_build'],'instrumented R-GFX5-5; NOT_DEPLOYED')
        self.assertEqual(proof['outcomes']['evidence'],'SYNTHETIC_NOT_GAME_RUNTIME')
        self.assertTrue(proof['outcomes']['engine_y_rewrite_left_offset_resident'])
        for name in ('restore_exact','restore_skip_owner_replaced','restore_skip_mode_changed','restore_skip_storage_changed','restore_skip_engine_xyz_changed','restore_read_failed'):
            self.assertEqual(proof['outcomes'][name],1)

    def test_canonical_numeric_ini_vertical_selectors(self):
        import configparser
        selectors={'Display.Mode':4,'Display.AutoHideCursor':2,'Widescreen.InterfaceMode':3,
                   'Filtering.AnisotropicFiltering':2,'AntiAliasing.Mode':2,'Camera.GameplayFOV':2,
                   'Shadows.Mode':2,'VehicleReflections.Mode':2,'Compatibility.MenuFreezeFix':2,
                   'Trace.Enabled':2,'Trace.FrameSummaries':2}
        for file in [ROOT/'MRRRenderer.ini.example',ROOT/'research/r-gfx5/stock-plus.ini']:
            text=file.read_text(encoding='utf-8');parser=configparser.ConfigParser();parser.read_string(text)
            self.assertNotRegex(text,r'(?im)^\w+\s*=\s*(true|false|yes|no)\s*$')
            lines=text.splitlines()
            for full,options in selectors.items():
                section,key=full.split('.');value=parser[section][key]
                self.assertTrue(value.isdigit());self.assertLess(int(value),options)
                start=lines.index('['+section+']');index=next(i for i in range(start+1,len(lines)) if lines[i].startswith(key+'='))
                comments=[];i=index-1
                while i>start and lines[i].startswith(';'):comments.insert(0,lines[i]);i-=1
                mappings=[l for l in comments if re.match(r'; \d+ = ',l)]
                self.assertEqual([int(re.match(r'; (\d+) = ',l)[1]) for l in mappings],list(range(options)))
                for line in mappings:self.assertNotRegex(line,r',|\|')
            self.assertIn('PreserveMargins v2 is runtime-confirmed',text)
        preset=configparser.ConfigParser();preset.read(ROOT/'research/r-gfx5/stock-plus.ini')
        self.assertEqual(preset['Widescreen']['InterfaceMode'],'1')
        self.assertEqual(preset['Compatibility']['MenuFreezeFix'],'1')

    def test_identity_and_output_guard(self):
        self.assertEqual(ROOT,TOOL_ROOT)
        self.assertEqual(output_guard(ROOT/'research/r-gfx5/result.json'),ROOT/'research/r-gfx5/result.json')
        for outside in [ROOT/'src/result.json', ROOT.parent/'input/result.json']:
            with self.assertRaises(ValueError):output_guard(outside)
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'input';f.write_bytes(b'synthetic')
            self.assertEqual(read_locked(f,hashlib.sha256(b'synthetic').hexdigest()),b'synthetic')
            with self.assertRaises(ValueError):read_locked(f,TARGET)
    def test_cave_evaluator_synthetic_cmp_and_branch(self):
        # cmp [eax+30], 565.0; je positive; jmp neutral. No game bytes needed.
        base=0x1000;code=bytes.fromhex('81783000400d447405e901000000')
        rows=instructions(code,base)
        self.assertEqual(evaluate(rows,565,75,base=base,targets={0x100e:1,0x100f:0}),1)
        self.assertEqual(evaluate(rows,20,75,base=base,targets={0x100e:1,0x100f:0}),0)
    def test_unknown_instruction_and_bounds_fail_closed(self):
        with self.assertRaises(ValueError):instructions(b'\x90',0x1000)
        with self.assertRaises(ValueError):evaluate({0x1000:(2,'jmp',0x1000,0)},1,1,base=0x1000,targets={})
        with self.assertRaises(ValueError):evaluate({},1,1,base=0x1000,targets={})
    def test_capture_present_and_clear_semantics(self):
        rows=[{'type':'frame_begin','exe_sha256':TARGET},
              {'type':'event','method':'Present','arguments':[0]*8},
              {'type':'event','method':'Clear','arguments':[0,0,3,0,0,0,0,0]},
              {'type':'frame_end','complete':True}]
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'fixture.jsonl';f.write_text('\n'.join(map(json.dumps,rows)))
            report=capture_audit(f);self.assertTrue(report['all_present_arguments_null']);self.assertEqual(report['full_color_depth_clears'],1)
            rows[1]['arguments'][0]=1;f.write_text('\n'.join(map(json.dumps,rows)));self.assertFalse(capture_audit(f)['all_present_arguments_null'])
            rows[0]['exe_sha256']='unknown';f.write_text('\n'.join(map(json.dumps,rows)))
            with self.assertRaises(ValueError):capture_audit(f)
    def test_reference_hash_rejected_before_ghidra(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.analysis') as tmp:
            f=Path(tmp)/'synthetic.bin';f.write_bytes(b'not a patcher')
            out=Path(tmp)/'output'
            command=[sys.executable,str(ROOT/'tools/reference_ghidra.py'),'--install',tmp,'--binary',str(f),'--java',tmp,'--output',str(out)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('Not the supplied widescreen reference patcher',result.stderr);self.assertFalse(out.exists())
    def test_curated_rules_match_native_header(self):
        report=json.loads((ROOT/'research/r-gfx5/input-evidence.json').read_text())
        rules=json.loads((ROOT/'research/r-gfx5/margin-rules.json').read_text())['point_rules']
        self.assertEqual(rules,report['reference_cave']['point_rules']);self.assertEqual(len(rules),51)
        header=(ROOT/'include/margin_rules.hpp').read_text()
        native=[[float(x),float(y),int(d)] for x,y,d in re.findall(r'\{(\d+)\.f,(\d+)\.f,(-?1)\}',header)]
        self.assertEqual(native,rules)
        self.assertEqual(report['inputs'][2]['sha256'],PATCHER_SHA)
    def test_pristine_signatures_match_native(self):
        def constants(file,name):
            text=(ROOT/'include'/file).read_text();body=re.search(name+r'\[\]=\{([^}]+)',text).group(1)
            return bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]+)',body))
        self.assertEqual(constants('menu_freeze.hpp','FREEZE_CONTEXT'),FREEZE_CONTEXT)
        report=json.loads((ROOT/'research/r-gfx5/input-evidence.json').read_text());self.assertEqual(bytes.fromhex(report['ui_sort']['context_hex']),UI_CONTEXT)
    def test_native_quality_capture_is_physical_and_virtualized(self):
        release=ROOT/'.build-msvc/Release';exe=release/'quality_tests.exe'
        self.assertTrue(exe.exists(),'Build the native suites first')
        sha=hashlib.sha256(exe.read_bytes()).hexdigest();frames=[]
        for path in (release/'MRRRenderer/logs').glob('frame*.jsonl'):
            with path.open() as f:
                head=json.loads(f.readline())
            if head.get('exe_sha256')==sha and head.get('proxy_version')=='R-GFX5-8':frames.append(read_jsonl(path))
        self.assertTrue(frames,'Native production wrapper must emit its positive capture')
        frame=next(f for f in reversed(frames) if (f[0]['quality'].get('effective') or {}).get('multisample')==4);self.assertTrue(frame[-1]['complete']);self.assertFalse(frame[-1]['truncated'])
        pp=frame[0]['quality']['effective'];self.assertEqual((pp['width'],pp['height'],pp['multisample'],pp['swap_effect']),(1920,1080,4,1))
        for name in ('physical_backbuffer','physical_depth'):
            surface=frame[0]['quality'][name];self.assertEqual((surface['width'],surface['height'],surface['multisample']),(1920,1080,4))
        draws=[r for r in frame if r.get('type')=='draw'];self.assertEqual(len(draws),2)
        self.assertEqual(draws[0]['state']['viewport'][:4],[0,0,640,480])
        self.assertEqual(draws[0]['effective_state']['viewport'][:4],[0,0,1920,1080])
        self.assertEqual(draws[1]['effective_state']['viewport'][:4],[960,540,960,540])

if __name__=='__main__':unittest.main()
