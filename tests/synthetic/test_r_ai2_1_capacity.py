import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import r_ai2_1_capacity as c
from r_ai2_1_course_start import inspect_xml

def sample(n,results=False):
    v={'Race/NumCars':n,'Race/NumPlayers':1,'Race/NumNetworkPlayers':0,'Race/Type':2,'Race/FinishingType':0,'Race/AttractMode':False,'Race/NetworkSyncActive':False,'Race/GhostPlayback':False,'Frontend/QuickRace/Track':10,'Frontend/QuickRace/Ghost':0}
    canaries=json.loads((c.REPOSITORY/'research/r-ai1-1/vehicle-physics-canaries.json').read_text())['vehicles']
    for slot,id in enumerate(c.ROSTER[:n]):
        vehicle=c.stock_map()[id]
        for k,value in dict(CarID=id,CarClass=vehicle['class'],DriverID=30 if slot==0 else slot-1,PlayerType=1 if slot==0 else 2,CarType=vehicle['family'],WheelType=vehicle['family']).items():v[f'Race/Car{slot}/'+k]=value
        for prefix in ('Physics','Controller','Network'):v[f'{prefix}/Car{slot}/SyntheticState']=True
        for suffix,value in next(r['values'] for r in canaries if r['id']==id).items():v[f'Vehicles/Car{slot}/'+suffix]=value
    if results:
        for suffix,value in dict(PositionList=[f'"{i}"' for i in range(1,n+1)],NameList=['"DRIVER"']*n,TimeList=['"01:00:00"']*n).items():v['Frontend/RaceResults/'+suffix]=value
        registry=json.loads((c.REPOSITORY/'research/r5v_a/final-vehicle-registry.json').read_text())
        images={r['index']:r['raw_numeric_arguments_push_order'][0] for r in registry['executable_registry']['records']}
        for i in range(8):v[f'Frontend/RaceResults/Car{i}']=images[c.ROSTER[i]] if i<n else 12
        for i in range(n):v.update({f'RaceData/Competitor{i}/RacePosition':i+1,f'RaceData/Competitor{i}/RaceTime':60.+i})
    return dict(kind='master-rallye-broker-dump-snapshot',schema_version=1,source=dict(image_sha256=c.PROFILE_SHA256[n],build_profile=c.profile(n),broker_dump_variant='native_hardened',label={6:'six',7:'seven',8:'eight'}[n]+('-results' if results else '-race'),freshness='post_baseline_complete_dump_proven'),entries=[dict(path=k,value=value,type='StringList' if isinstance(value,list) else 'Synthetic') for k,value in v.items()])

class CapacityTests(unittest.TestCase):
    def test_totals_bounded(self):
        for n in (0,5,9,True):
            with self.assertRaises(ValueError):c.ranges(n)
    def test_unique_stock_roster(self):
        self.assertEqual(len(set(c.ROSTER)),8)
        self.assertEqual({c.stock_map()[i]['class'] for i in c.ROSTER},{0,1,2})
        self.assertTrue(all(i in range(25) for i in c.ROSTER))
    def test_three_is_only_hidden_trigger(self):
        state=dict(opponents=3,mode=2,split=False,ghost=0,player=0,track=10)
        for n in c.TOTALS:
            self.assertEqual(c.effective_opponents(n,**state),n-1)
            for key,value in (('opponents',2),('mode',1),('ghost',1),('split',True),('track',9),('player',1)):
                changed={**state,key:value};self.assertEqual(c.effective_opponents(n,**changed),changed['opponents'])
    def test_nonoverlap_and_hardening(self):
        for n in c.TOTALS:
            r=c.ranges(n)
            for a,b in zip(r,r[1:]):self.assertLessEqual(a['offset']+len(a['original']),b['offset'])
            new={x['offset']:x for x in r}
            for row in c.hardening_ranges():
                if row['va'] is not None:self.assertEqual(row,new[row['offset']])
    def test_source_and_output_reject_unknown(self):
        for n in c.TOTALS:
            with self.assertRaises(ValueError):c.build(bytes(c.RETAIL_SIZE),n)
            with self.assertRaises(ValueError):c.verify(bytes(c.RETAIL_SIZE),n)
    def test_original_bytes_fail_closed(self):
        b=b'abcd'
        with self.assertRaises(ValueError):c.apply_ranges(b,[dict(offset=0,original=b'X',replacement=b'Y')],c.sha256(b))
    def test_manifest_deterministic(self):
        for n in c.TOTALS:
            m=c.manifest(n,c.PROFILE_SHA256[n]);self.assertEqual(m,c.manifest(n,c.PROFILE_SHA256[n]));self.assertFalse(m['ui_changes']);self.assertFalse(m['randomizer_dependency']);self.assertEqual(len(m['roster']),n)
    def test_race_match_is_not_actor_proof(self):
        for n in c.TOTALS:
            r=c.check_snapshot(sample(n),n);self.assertFalse(r['runtime_full_pass']);self.assertEqual(len(r['participants']),n)
    def test_results_exact_n(self):
        for n in c.TOTALS:self.assertEqual(len(c.check_snapshot(sample(n,True),n,True)['result_lists']['PositionList']),n)
    def test_wrong_count_rejected(self):
        j=sample(8);next(r for r in j['entries'] if r['path']=='Race/NumCars')['value']=7
        with self.assertRaises(ValueError):c.check_snapshot(j,8)
    def test_car7_alias_rejected(self):
        j=sample(8);next(r for r in j['entries'] if r['path']=='Race/Car7/CarID')['value']=15
        with self.assertRaises(ValueError):c.check_snapshot(j,8)
    def test_highest_physics_missing_rejected(self):
        j=sample(8);j['entries']=[r for r in j['entries'] if not r['path'].startswith('Physics/Car7/')]
        with self.assertRaises(ValueError):c.check_snapshot(j,8)
    def test_wrong_competitor_position_rejected(self):
        j=sample(8,True);next(r for r in j['entries'] if r['path']=='RaceData/Competitor7/RacePosition')['value']=1
        with self.assertRaises(ValueError):c.check_snapshot(j,8,True)
    def test_wrong_image_rejected(self):
        j=sample(8,True);next(r for r in j['entries'] if r['path']=='Frontend/RaceResults/Car7')['value']=12
        with self.assertRaises(ValueError):c.check_snapshot(j,8,True)
    def test_stale_capture_rejected(self):
        j=sample(6);j['source']['freshness']='old'
        with self.assertRaises(ValueError):c.check_snapshot(j,6)
    def test_corpus_eight_templates_dynamic_start(self):
        eggs=''.join(f'<Egg Name="Car{i}"><Value Value="gaBootAICar"/></Egg>' for i in range(8))
        markers='<Marker><Value Name="Marker Pos" Value="0 0 0"/></Marker><Marker><Value Name="Marker Pos" Value="12 0 0"/></Marker>'
        r=inspect_xml(f'<Scene>{eggs}<List Name="StartArea">{markers}</List></Scene>'.encode())
        self.assertTrue(r['structurally_ready_for_eight']);self.assertEqual(r['terrain_clearance_runtime'],'UNKNOWN')
    def test_missing_template_not_hidden(self):
        self.assertFalse(inspect_xml(b'<Scene><List Name="StartArea"/></Scene>')['structurally_ready_for_eight'])
if __name__=='__main__':unittest.main()
