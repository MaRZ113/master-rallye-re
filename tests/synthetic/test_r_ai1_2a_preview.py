import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import r_ai1_2a_preview as p

def snapshot(values):return {'source':{'process_id':123},'entries':[{'path':k,'value':v} for k,v in values.items()]}

class PreviewPairTests(unittest.TestCase):
    def setUp(self):
        self.config=b'[OpponentRandomizer]\nConfigVersion=1\nChallenge=Mixed\n'
        self.hash=p.sha256(self.config)
        self.front=snapshot({'Frontend/Challenge/PlayerCar':18,'Frontend/Challenge/Challenge':10,'Frontend/Challenge/OpponentCar':2,'Frontend/Challenge/Car2Text':'TOMMEK TATA'})
        self.race=snapshot({'Race/RaceID':35,'Race/Car0/CarID':18,'Race/Car0/CarClass':2,'Race/Car0/PlayerType':1,'Race/Car0/DriverID':30,'Race/NumNetworkPlayers':0,'Race/Car1/CarID':2,'Race/Car1/CarClass':0,'Race/Car1/DriverID':2,'Race/NumCars':2,'Race/NumPlayers':1,'Race/Car1/PlayerType':2,'Race/Type':7,'Race/AttractMode':False,'Race/PlaybackReplay':False})
        self.log=f'Challenge Mixed 1 1 0 {self.hash}\nPreviewV1 Begin 1 10 Mixed 2 0 {self.hash} 123\nPreviewV1 Use 1 10 Mixed 2 0 {self.hash} 123\n'.encode()
    def check(self):return p.check_pair(self.front,self.race,self.log,self.config)
    def test_match_is_not_visibility(self):
        r=self.check();self.assertEqual(r['status'],'CHALLENGE_PREVIEW_STATE_MATCH_ONLY');self.assertFalse(r['runtime_full_pass']);self.assertFalse(r['visible_model_or_text_equality_proven']);self.assertEqual(r['generation_groups'],1)
    def test_second_event_is_generic(self):
        self.race['entries'][0]['value']=25
        next(e for e in self.race['entries'] if e['path']=='Race/Car0/CarID')['value']=6
        next(e for e in self.race['entries'] if e['path']=='Race/Car0/CarClass')['value']=0
        self.front['entries'][0]['value']=6
        self.log=self.log.replace(b'1 10 Mixed',b'1 0 Mixed');self.assertEqual(self.check()['event'],0)
    def test_stale_frontend_selection_not_a_roster_owner(self):
        self.front['entries'][1]['value']=0;self.assertEqual(self.check()['event'],10)
    def test_identity_mismatch_rejected(self):
        for path in ('Race/Car1/CarID','Race/Car1/CarClass','Race/Car0/CarID','Race/RaceID'):
            original=copy.deepcopy(self.race)
            next(e for e in self.race['entries'] if e['path']==path)['value']=24
            with self.assertRaises(ValueError):self.check()
            self.race=original
    def test_second_rng_group_rejected(self):
        self.log=self.log.replace(b'PreviewV1 Use',f'Challenge Mixed 1 1 0 {self.hash}\nPreviewV1 Use'.encode())
        with self.assertRaises(ValueError):self.check()
    def test_start_without_begin_rejected(self):
        self.log=b'\n'.join(line for line in self.log.splitlines() if b' Begin ' not in line)
        with self.assertRaises(ValueError):self.check()
    def test_config_provenance_frozen(self):
        with self.assertRaises(ValueError):p.check_pair(self.front,self.race,self.log,self.config.replace(b'Mixed',b'Stock'))
        self.assertEqual(self.check()['policy'],'Mixed')
    def test_process_mismatch_rejected(self):
        self.race['source']['process_id']=456
        with self.assertRaises(ValueError):self.check()
    def test_log_process_mismatch_rejected(self):
        self.log=self.log.replace(b'123',b'456')
        with self.assertRaises(ValueError):self.check()
    def test_redraw_has_no_additional_generation(self):
        self.log+=f'PreviewV1 Use 1 10 Mixed 2 0 {self.hash} 123\n'.encode()
        self.assertEqual(self.check()['generation_groups'],1)
    def test_conflicting_broker_value_rejected(self):
        self.front['entries'].append({'path':'Frontend/Challenge/OpponentCar','value':23})
        with self.assertRaises(ValueError):self.check()
    def test_unknown_context_rejected(self):
        next(e for e in self.race['entries'] if e['path']=='Race/NumCars')['value']=6
        with self.assertRaises(ValueError):self.check()
    def test_stock_control(self):
        self.config=self.config.replace(b'Mixed',b'Stock');self.hash=p.sha256(self.config)
        self.front['entries'][2]['value']=23
        next(e for e in self.race['entries'] if e['path']=='Race/Car1/CarID')['value']=23
        next(e for e in self.race['entries'] if e['path']=='Race/Car1/CarClass')['value']=2
        self.log=f'Challenge Stock 1 1 - {self.hash}\nPreviewV1 Begin 1 10 Stock 23 2 {self.hash} 123\nPreviewV1 Use 1 10 Stock 23 2 {self.hash} 123\n'.encode()
        self.assertEqual(self.check()['CarID'],23)
    def test_diverse_same_lifecycle(self):
        before=self.hash;self.config=self.config.replace(b'Mixed',b'Diverse');self.hash=p.sha256(self.config)
        self.log=self.log.replace(b'Mixed',b'Diverse').replace(before.encode(),self.hash.encode())
        self.assertEqual(self.check()['policy'],'Diverse')

class BridgeTests(unittest.TestCase):
    def test_only_three_stock_sites_added(self):
        sites=[r['va'] for r in p.preview_ranges() if r['va'] is not None and r['va']<p.PREVIEW]
        self.assertEqual(set(sites),{0x45EC35,0x45E511,0x45EA9A})
    def test_known_input_hash_is_mandatory(self):
        with self.assertRaises(ValueError):p.build(bytes(p.RETAIL_SIZE))
    def test_unknown_candidate_rejected(self):
        with self.assertRaises(ValueError):p.verify(bytes(p.RETAIL_SIZE))
    def test_nonoverlap_and_no_iat_write(self):
        for five in (False,True):
            rows=p.ranges(five)
            for a,b in zip(rows,rows[1:]):self.assertLessEqual(a['offset']+len(a['original']),b['offset'])
            self.assertTrue(all(r['va'] is None or r['va']+len(r['replacement'])<0x68F000 for r in p.preview_ranges()))
    def test_closed_general_ranges_preserved(self):
        new={r['offset']:r for r in p.ranges(True)}
        for r in p.base.ranges(True):
            if r['va'] is not None:self.assertEqual(new[r['offset']],r)

if __name__=='__main__':unittest.main()
