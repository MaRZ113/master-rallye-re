import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import r_ui1_opponents as u
from test_r_ai2_capacity import capture as five_capture, change


def menu(count=1):
    labels = ['"'+s+'"' for s in u.LABELS]
    return dict(kind='master-rallye-broker-dump-snapshot', schema_version=1,
                source=dict(image_sha256=u.CANDIDATE_SHA256, build_profile=u.PROFILE,
                            broker_dump_variant='native_hardened', freshness='post_baseline_complete_dump_proven',
                            label='ui-opponents-'+u.LABELS[count-1].lower()),
                entries=[dict(path='Frontend/QuickModeSelect/Mode', type='Int', value=1),
                         dict(path='Frontend/QuickModeSelect/NumOpponents', type='Int', value=count-1),
                         dict(path='Frontend/QuickModeSelect/NumOpponentsList', type='StringList', value=labels),
                         dict(path='Frontend/QuickModeSelect/NumOpponentsText', type='String', value=u.LABELS[count-1]),
                         dict(path='Frontend/QuickRace/NumOpponents', type='Int', value=2)])


def race(results=False):
    s = five_capture(results)
    s['source'].update(image_sha256=u.CANDIDATE_SHA256, build_profile=u.PROFILE,
                       label='ui-four-results' if results else 'ui-four-race')
    s['entries'].append(dict(path='Frontend/QuickRace/NumOpponents', type='Int', value=4))
    for n in range(5):
        for prefix in ('Vehicles','Physics'):
            s['entries'].append(dict(path=f'{prefix}/Car{n}/NamedState', type='Int', value=n))
    return s


class OpponentUI(unittest.TestCase):
    def test_seven_labels_numeric_mapping_and_stock_prefix(self):
        self.assertEqual(u.LABELS[:3], ('ONE','TWO','THREE'))
        self.assertEqual(len(u.LABELS), 7)
        self.assertEqual([u.ai_count(n) for n in range(7)], list(range(1,8)))
        self.assertEqual(u.ai_count(3),4); self.assertEqual(u.ai_count(6),7)

    def test_navigation_min_max_do_not_wrap_or_escape(self):
        for n in range(7):
            self.assertEqual(u.navigate(n,-1), n-1 if n else 0)
            self.assertEqual(u.navigate(n,1), n+1 if n<6 else 6)

    def test_invalid_index_types_and_direction_rejected(self):
        for n in (-1,7,False,True,1.0,'1'):
            with self.assertRaises(ValueError): u.ai_count(n)
        for direction in (0,2,True):
            with self.assertRaises(ValueError): u.navigate(1,direction)

    def test_patch_is_ui_and_hardening_only(self):
        rows=u.ranges()
        self.assertEqual(len(rows),9)
        self.assertEqual({r['va'] for r in rows if r['va'] not in (None,0x464F69,0x60201E,0x602153,0x68E2A0,0x68E2C0)},
                         {u.HOOK,u.CAVE,0x47A32C})
        self.assertFalse(any(0x47B780 <= (r['va'] or 0) < 0x47BA00 for r in rows))
        m=u.manifest(u.CANDIDATE_SHA256)
        for key in ('hidden_count_shim','randomizer_dependency','engine_arrays_changed','race_setup_changed'):
            self.assertFalse(m[key])
        self.assertEqual(m['loose_data'],[])

    def test_range_overlap_and_cave_bounds(self):
        rows=u.ranges()
        self.assertTrue(all(a['offset']+len(a['original']) <= b['offset'] for a,b in zip(rows,rows[1:])))
        self.assertLess(u.CAVE+len(u.list_code()),0x68F000)
        code=u.list_code()
        self.assertIn(u.ORIGINAL,code)
        self.assertIn(bytes.fromhex('83ff07'),code)

    def test_source_and_candidate_unknown_hash_fail_closed(self):
        for blob in (b'',bytes(u.RETAIL_SIZE)):
            with self.assertRaises(ValueError):u.build(blob)
            with self.assertRaises(ValueError):u.verify(blob)
            with self.assertRaises(ValueError):u.localization(blob)

    def test_expected_original_bytes_verified(self):
        for r in u.ranges():
            b=bytearray(r['offset']+len(r['original']));b[r['offset']:]=r['original'];b[r['offset']]^=1
            with self.assertRaisesRegex(ValueError,'original bytes'):
                u.apply_ranges(bytes(b),[r],u.sha256(b))

    def test_determinism_inverse_and_declared_ranges_only(self):
        rows=u.ranges();b=bytearray(u.RETAIL_SIZE)
        for r in rows:b[r['offset']:r['offset']+len(r['original'])]=r['original']
        source=bytes(b);out=u.apply_ranges(source,rows,u.sha256(source))
        self.assertEqual(out,u.apply_ranges(source,u.ranges(),u.sha256(source)))
        self.assertEqual(source,u.apply_ranges(out,[{**r,'original':r['replacement'],'replacement':r['original']} for r in rows],u.sha256(out)))
        allowed={n for r in rows for n in range(r['offset'],r['offset']+len(r['original']))}
        self.assertTrue(all(n in allowed for n,(a,b) in enumerate(zip(source,out)) if a!=b))

    def test_manifest_deterministic_and_human_menu_boundary(self):
        self.assertEqual(u.manifest(u.CANDIDATE_SHA256),u.manifest(u.CANDIDATE_SHA256))
        self.assertEqual(u.manifest(u.CANDIDATE_SHA256)['human_menu_only_ai'],[5,6,7])

    def test_each_menu_selection_evidence_only(self):
        for n in range(1,8):
            d=u.check_snapshot(menu(n),n)
            self.assertEqual(d['semantic_ai_count'],n);self.assertEqual(d['committed_count'],2)
            self.assertEqual(d['status'],'BROKER_FRONTEND_MATCH_ONLY');self.assertFalse(d['runtime_full_pass'])

    def test_localized_selected_label_match_not_english_parsing(self):
        s=menu(4)
        change(s,'Frontend/QuickModeSelect/NumOpponentsList',['"UN"','"DEUX"','"TROIS"','"QUATRE"','"CINQ"','"SIX"','"SEPT"'])
        change(s,'Frontend/QuickModeSelect/NumOpponentsText','QUATRE')
        self.assertEqual(u.check_snapshot(s,4)['semantic_ai_count'],4)

    def test_menu_mismatch_index_or_text_or_list_rejected(self):
        for path,value in (('Frontend/QuickModeSelect/NumOpponents',7),('Frontend/QuickModeSelect/NumOpponentsText','FOUR'),('Frontend/QuickModeSelect/NumOpponentsList',['"ONE"'])):
            s=menu();change(s,path,value)
            with self.assertRaises(ValueError):u.check_snapshot(s,1)

    def test_exact_capture_provenance_not_path_presence(self):
        for key,value in (('image_sha256','0'*64),('build_profile','stock'),('label','old'),('freshness','old')):
            s=menu();s['source'][key]=value
            with self.assertRaises(ValueError):u.check_snapshot(s,1)

    def test_four_race_and_results_evidence_only(self):
        for results in (False,True):
            d=u.check_snapshot(race(results),4,'results' if results else 'race')
            self.assertFalse(d['runtime_full_pass']);self.assertEqual(d['num_cars'],5)

    def test_higher_count_race_oracles_forbidden(self):
        for n in (5,6,7):
            with self.assertRaises(ValueError):u.check_snapshot(race(),n,'race')
        with self.assertRaises(ValueError):u.check_snapshot(menu(),True)

    def test_hidden_three_four_or_aliased_race_rejected(self):
        for path,value in (('Frontend/QuickRace/NumOpponents',3),('Race/NumCars',4),('Race/Car4/CarID',0),('Race/Car4/DriverID',0)):
            s=race();change(s,path,value)
            with self.assertRaises(ValueError):u.check_snapshot(s,4,'race')

    def test_results_missing_fifth_row_rejected(self):
        s=race(True);change(s,'Frontend/RaceResults/TimeList',['"01:00:00"']*4)
        with self.assertRaises(ValueError):u.check_snapshot(s,4,'results')


if __name__ == '__main__':unittest.main()
