"""COURSE-RENDER-FIX1 source contracts, analyzer behaviour and the recorded evidence."""
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
RENDERER = PORT / 'renderer'
PATCH = (PORT / 'overlay/patches/0001-renderer-integration.patch').read_text(encoding='utf-8')


def read(name):
    return (RENDERER / name).read_text(encoding='utf-8')


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, PORT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class SourceContracts(unittest.TestCase):
    def test_patch_hooks(self):
        for token in ('reflectionintegration::note_draw(*this,count,min_index,vertices);', 'reflectionintegration::before_ui(*this,ui_callsite)',
                      '#include "reflection_timing_native.hpp"', 'add_test(NAME ps2_diag_contracts COMMAND ps2_diag_tests)'):
            self.assertEqual(PATCH.count(token), 1, token)
        self.assertEqual(PATCH.count('reflectionintegration::note_result('), 8)
        # the hooks stay in the PS2-only block
        self.assertLess(PATCH.index('reflectionintegration::note_draw'), PATCH.index('lampintegration::draw'))

    def test_baseline_lock_pins_the_patch(self):
        import hashlib
        lock = json.loads((PORT / 'overlay/baseline-lock.json').read_text(encoding='utf-8'))
        sha = hashlib.sha256((PORT / 'overlay/patches/0001-renderer-integration.patch').read_bytes()).hexdigest()
        self.assertEqual(lock['patches']['0001-renderer-integration.patch']['sha256'], sha)

    def test_detail_layers_never_latch_on_a_frame_condition(self):
        for name in ('grass_native_integration.hpp', 'grass_split_native.hpp'):
            text = read(name)
            self.assertNotIn('disable(failure)', text, name)
            self.assertIn('p->proof.clear();', text, name)
        spline = read('spline_objects_native_integration.hpp')
        self.assertNotIn('spline_world_vertices_nonfinite', spline)
        self.assertIn('world_vertices_nonfinite', spline)
        # device-level failures still switch the layer off (and are logged by the disable log)
        self.assertIn('native_grass_preview_draw_failed', read('grass_native_integration.hpp'))
        self.assertIn('native_spline_objects_draw_failed', spline)

    def test_race_observer_registries_are_not_bounded_by_the_string_pool_size(self):
        # The game string pool grows with every course loaded in a session (scene ids above 32000 after about fifteen new
        # courses). A 32768 bound made it unreadable, poisoned the race certificate permanently and switched every PS2 effect off.
        self.assertEqual(PATCH.count('constexpr uint32_t kRaceRegistryLimit=1u<<20;'), 1)
        self.assertEqual(PATCH.count('kRaceRegistryLimit,begin,count'), 3)
        self.assertFalse([l for l in PATCH.splitlines() if l.startswith('+') and '32768,begin' in l])
        participants = read('fleet_participants.hpp')
        self.assertNotIn('32768', participants)
        self.assertIn('vector(m,registry,1u<<20,begin,count)', participants)

    def test_car_is_excluded_from_its_own_late_reflection(self):
        exclusion = read('reflection_exclusion.hpp')
        for line in exclusion.splitlines():
            if line.startswith('#include'):
                self.assertTrue(re.match(r'#include <[a-z_]+>$', line), line)
        timing = read('reflection_timing_native.hpp')
        self.assertIn('D3DTSS_TCI_CAMERASPACENORMAL', timing)          # the draws that sample the environment target
        self.assertIn('publish_car_mask(d, *p, frame);', timing)
        self.assertLess(timing.index('publish_car_mask(d, *p, frame);'), timing.index('capture.capture_late('))
        capture = read('reflection_capture.cpp')
        self.assertIn('draw_exclusion(native,env)', capture)
        self.assertIn('late&&!debug_pattern_', capture)               # the in-frame capture (no car yet) is untouched
        self.assertIn('L"ReflectionExcludeCar",1', read('reflection_pilot.cpp'))
        self.assertIn('ReflectionExcludeCar=1', (PORT / 'PS2Port.ini.example').read_text(encoding='utf-8'))

    def test_order_records_only_for_reported_captures(self):
        timing = read('reflection_timing_native.hpp')
        self.assertIn('decision().stage_next()', timing)
        self.assertIn('bool stage_next() const noexcept', read('ps2_diag.hpp'))

    def test_every_disable_is_recorded(self):
        for name, token in (('reflection_pilot.hpp', '"reflection"'), ('grass_pilot.hpp', 'disable_log().note('),
                            ('spline_objects.hpp', '"spline"'), ('ps2_water_pilot.hpp', '"water"'), ('course_objects.hpp', '"course_objects"'),
                            ('ground_detail.hpp', '"ground_detail"'), ('frontend_model.hpp', '"model"')):
            text = read(name)
            self.assertIn('ps2diag::disable_log().note(', text, name)
            self.assertIn(token, text, name)
        ext = read('ps2_port_extension.cpp')
        self.assertIn('ps2_effect_disabled', ext)
        self.assertIn('drain_disables();', ext)

    def test_capture_timing_contract(self):
        capture = read('reflection_capture.cpp')
        header = read('reflection_capture.hpp')
        self.assertIn('HRESULT capture_late(', header)
        self.assertIn('has_ready(frame+1)', capture)
        self.assertIn('msaa_resolve_latched_', capture)
        # the original in-frame path is untouched: same checks in the same order
        self.assertLess(capture.index('if(permanently_unsupported_)return status_.capture_hr;'), capture.index('ready_=false;attempted_=true;attempted_frame_=frame;'))
        timing = read('reflection_timing_native.hpp')
        self.assertIn('capture.capture_late(', timing)
        self.assertIn('last_frame == frame', timing)          # once per frame
        # the diagnostics readbacks stay out of the capture and out of the pilot (existing no-readback policy tests)
        for name, forbidden_tokens in (('reflection_capture.cpp', ('LockRect(', 'CreateImageSurface(', 'GetRenderTargetData')),
                                       ('reflection_pilot.cpp', ('CreateImageSurface(', 'GetRenderTargetData', 'CopyRects('))):
            text = read(name)
            for forbidden in forbidden_tokens:
                self.assertFalse(forbidden in text, f'{forbidden} in {name}')
        includers = [p.name for p in RENDERER.glob('*') if p.suffix in ('.hpp', '.cpp') and '#include "reflection_inspect.hpp"' in p.read_text(encoding='utf-8')]
        self.assertEqual(includers, ['reflection_timing_native.hpp'])
        self.assertIn('capture.set_inspector(inspector());', timing)
        pilot = read('reflection_pilot.cpp')
        self.assertIn('L"ReflectionCaptureTiming",L"auto"', pilot)
        self.assertIn('L"ReflectionStageDiag",0', pilot)

    def test_defaults_in_the_example_ini(self):
        ini = (PORT / 'PS2Port.ini.example').read_text(encoding='utf-8')
        self.assertIn('\nReflectionCaptureTiming=auto', ini)
        self.assertIn('\nReflectionStageDiag=0', ini)
        self.assertIn('; RaceLedger=1', ini)                  # commented: the default follows Diagnostics
        ext = read('ps2_port_extension.cpp')
        self.assertIn('L"RaceLedger", diagnostics_ ? 1 : 0', ext)

    def test_portable_core_has_no_platform_dependency(self):
        core = read('ps2_diag.hpp')
        for line in core.splitlines():
            if line.startswith('#include'):
                self.assertTrue(re.match(r'#include <[a-z_]+>$', line), line)
        self.assertNotIn('windows.h', core.lower())
        self.assertNotIn('d3d8', core.lower())


def synthetic_stream(races, lose_after=None, lose_effect='grass', disable_at=None):
    records = [{'type': 'ps2_diag_session', 'schema': 1}]
    courses = ['RaceTest/SpainS2', 'RaceTest/Italy3', 'RaceTest/Turkey3']
    for i in range(races):
        course = courses[i % 3]
        gen = 6 + i * 7
        seq = i + 1
        records.append({'type': 'ps2_race_start', 'seq': seq, 'course': course, 'race_generation': gen})
        grass = {'drawn': 900} if not (lose_after is not None and i >= lose_after and lose_effect == 'grass') else {'gate': 40}
        effects = {
            'grass': grass,
            'spline': {'drawn': 800} if course == 'RaceTest/SpainS2' else {'stock_pc_course_no_loose_course_dx': 800},
            'reflection_capture': {'inframe_ready': 900},
            'hud': {'ps2_hud_damage_drawn': 300, 'no_pc_damage_row_this_frame': 5},
        }
        if course != 'RaceTest/Italy3':
            effects['water'] = {'replaced': 700}
        records.append({'type': 'ps2_race_summary', 'seq': seq, 'course': course, 'race_generation': gen, 'owner_lifetime': seq,
                        'frames': 900, 'end_reason': 'new_race', 'epoch': {'request_generation': gen + 1, 'successful_generation': gen + 1},
                        'effects': effects,
                        'state': {'resources': {'tracked': 400 + 20 * i, 'serial': 1500 + 100 * i},
                                  'grass': {'requested': True, 'active': True, 'blocked': False, 'reason': 'ok'},
                                  'spline': {'requested': True, 'active': True, 'blocked': False, 'reason': 'ok'},
                                  'water': {'requested': True, 'active': True, 'blocked': False, 'reason': 'ok'},
                                  'reflection': {'requested': True, 'active': True}}})
        if disable_at == i:
            records.append({'type': 'ps2_effect_disabled', 'effect': 'grass', 'reason': 'native_grass_preview_draw_failed', 'race_generation': gen, 'course': course})
    return records


class Analyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool('analyze_race_lifecycle')

    def codes(self, result):
        return sorted({(f['code'], f.get('effect')) for f in result['findings']})

    def test_healthy_cycles_have_no_findings(self):
        result = self.tool.analyze(synthetic_stream(14))
        self.assertEqual(len(result['races']), 14)
        self.assertEqual(result['findings'], [])
        self.assertEqual(result['races'][0]['draws']['grass'], 900)
        # intentional off is recognised, not reported
        stock = next(r for r in result['races'] if r['course'] == 'RaceTest/Italy3')
        self.assertEqual(stock['draws']['spline'], 0)
        self.assertEqual(stock['intentional']['spline'], 800)

    def test_an_effect_that_stops_after_several_cycles_is_found(self):
        result = self.tool.analyze(synthetic_stream(14, lose_after=6))
        lost = [f for f in result['findings'] if f['code'] == 'EFFECT_LOST' and f['effect'] == 'grass']
        self.assertGreaterEqual(len(lost), 6)
        self.assertEqual(min(f['race_seq'] for f in lost), 7)
        # the same effect is fine on every earlier race
        self.assertTrue(all(f['race_seq'] >= 7 for f in lost))

    def test_disable_events_and_resource_growth_are_findings(self):
        records = synthetic_stream(12, disable_at=4)
        result = self.tool.analyze(records)
        self.assertIn(('DISABLED', 'grass'), self.codes(result))
        records = synthetic_stream(12)
        for r in records:
            if r.get('type') == 'ps2_race_summary' and r['seq'] == 8:
                r['state']['resources']['tracked'] += 5000
        self.assertIn(('RESOURCE_GROWTH', None), self.codes(self.tool.analyze(records)))

    def test_generation_and_closure_checks(self):
        records = synthetic_stream(4)
        summaries = [r for r in records if r.get('type') == 'ps2_race_summary']
        summaries[1]['race_generation'] = 3                                  # the second race no longer increases
        result = self.tool.analyze(records)
        self.assertTrue(any(f['code'] == 'GENERATION_ORDER' and f['race_seq'] == 2 for f in result['findings']))
        records = synthetic_stream(3)
        records.append({'type': 'ps2_race_start', 'seq': 99, 'course': 'RaceTest/SpainS2', 'race_generation': 80})
        self.assertIn(('RACE_NOT_CLOSED', None), self.codes(self.tool.analyze(records)))
        records = synthetic_stream(3)
        for r in records:
            if r.get('type') == 'ps2_race_summary':
                r['epoch']['successful_generation'] += 1
        self.assertIn(('GENERATION_ORDER', None), self.codes(self.tool.analyze(records)))

    def test_reflection_verdict(self):
        stage = {'type': 'ps2_reflection_stage', 'race_generation': 6, 'course': 'RaceTest/SpainS2', 'frame': 356, 'ordinal': 1, 'late': False,
                 'timing': 'auto', 'timing_now': 'inframe', 'world_incomplete': True, 'bottom_third': {'black': 1.0}, 'source': {'black': 0.4},
                 'dynamic': {'mean': [60, 60, 60]}, 'env': {'hash': 'abcd'}, 'served': {'frame_count': 9}, 'readback_ok': True, 'png': 'x.png', 'reason': 'mixed_source_ready'}
        order = {'type': 'ps2_reflection_order', 'frame': 356, 'late': False,
                 'before_capture': {'draws': 59, 'triangles': 7979, 'fvf': {'258': [2, 376], '322': [57, 7603]}},
                 'frame_total': {'draws': 156, 'triangles': 14200, 'fvf': {'258': [2, 376], '322': [57, 7603], '578': [36, 5739], '594': [5, 476]}}}
        result = self.tool.analyze(synthetic_stream(2) + [stage, order])
        self.assertIn(('REFLECTION_WORLD_INCOMPLETE', None), self.codes(result))
        o = result['reflection']['orders'][0]
        self.assertEqual((o['ground_triangles_before'], o['ground_triangles_total']), (0, 6215))
        late = dict(stage, late=True, world_incomplete=False, bottom_third={'black': 0.0}, ordinal=2)
        result = self.tool.analyze(synthetic_stream(2) + [late])
        self.assertNotIn('REFLECTION_WORLD_INCOMPLETE', [f['code'] for f in result['findings']])
        text = self.tool.markdown(result)
        self.assertIn('## Reflection stage reports', text)

    def test_cli_exit_codes_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            good = tmp / 'good.jsonl'
            good.write_text('\n'.join(json.dumps(r) for r in synthetic_stream(13)) + '\nnot json\n', encoding='utf-8')
            r = subprocess.run([sys.executable, str(PORT / 'tools/analyze_race_lifecycle.py'), '--diag', str(good), '--md', str(tmp / 'r.md'),
                                '--json', str(tmp / 'r.json'), '--min-races', '12'], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            data = json.loads((tmp / 'r.json').read_text(encoding='utf-8'))
            self.assertEqual(data['unparsable_lines'], 1)
            self.assertIn('| 13 |', (tmp / 'r.md').read_text(encoding='utf-8'))
            r = subprocess.run([sys.executable, str(PORT / 'tools/analyze_race_lifecycle.py'), '--diag', str(good), '--min-races', '20'],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)


class CyclePlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool('race_cycle_plan')

    def test_plan_covers_converted_and_control_courses(self):
        plan = self.tool.build_plan(14)
        self.assertEqual(len(plan), 14)
        courses = [p['course'] for p in plan]
        self.assertGreaterEqual(courses.count('RaceTest/SpainS2'), 3)
        self.assertGreaterEqual(courses.count('RaceTest/Turkey3'), 3)
        self.assertIn('stock', {p['kind'] for p in plan})
        with self.assertRaises(SystemExit):
            self.tool.build_plan(11)

    def test_check_matches_order_and_length(self):
        plan = self.tool.build_plan(12)
        records = [{'type': 'ps2_race_summary', 'course': p['course'], 'race_generation': 6 + 7 * i, 'frames': 900} for i, p in enumerate(plan)]
        self.assertEqual(self.tool.check(plan, records), [])
        records[3]['course'] = 'RaceTest/Italy3'
        records[5]['frames'] = 100
        problems = self.tool.check(plan, records)
        self.assertEqual(len(problems), 2)
        self.assertTrue(self.tool.check(plan, records[:9]))


class RecordedEvidence(unittest.TestCase):
    """The offline proof for the black SpainS2 reflection (docs/course-render-fix1/evidence)."""

    def setUp(self):
        self.data = json.loads((PORT / 'docs/course-render-fix1/evidence/evidence.json').read_text(encoding='utf-8'))

    def test_framebuffer_term_of_the_screenshot_is_empty_below_the_horizon(self):
        env = self.data['env_arithmetic']
        self.assertEqual(env['empty_framebuffer_term_rows'], [0, 19])
        self.assertEqual(env['first_lit_row'], 24)
        for band in env['bands'][:5]:
            self.assertTrue(all(abs(v) < 1.0 for v in band['framebuffer_term_mean']), band)
        for band in env['bands'][6:]:
            self.assertTrue(all(v > 60 for v in band['framebuffer_term_mean']), band)

    def test_converted_course_draws_the_terrain_after_the_car_stock_courses_before(self):
        order = self.data['draw_order']
        converted = order['spains2_converted']
        self.assertEqual(converted['ground_class_triangles_before_first_car_draw'], 0)
        self.assertGreater(converted['ground_class_triangles_total'], 6000)
        self.assertGreaterEqual(converted['ground_class_draws_after_first_car_draw'], 36)
        stock = [v for k, v in order.items() if k.startswith('stock_')]
        self.assertGreaterEqual(len(stock), 4)
        for item in stock:
            self.assertEqual(item['ground_class_fraction_before_first_car_draw'], 1.0, item['capture'])
            self.assertEqual(item['ground_class_draws_after_first_car_draw'], 0)


if __name__ == '__main__':
    unittest.main()
