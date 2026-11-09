import copy,unittest
from master_rallye.addon_sdk.roster_identity import catalog
from master_rallye.addon_sdk.competition_contract import build_contract,require_compatible
from master_rallye.addon_sdk.capacity_profile import scenario,validate_profile,SDK33

class CompetitionDependencies(unittest.TestCase):
    def setUp(self):
        self.identity=catalog([{'physical_id':33,'family':'FourRunner','vehicle_class':'T2'}])
        self.resources={'DataGame/vehicles.xml':b'<Game><Broker><Value Name="Vehicles/FourRunner/Mass" Type="Float" Value="1400"/></Broker></Game>',
                        'DataGame/Modifications.xml':b'<Game><Broker></Broker></Game>',
                        'DataGame/MasterRallye.xml':b'<Game><Broker><Value Name="Stages" Type="Int" Value="6"/></Broker></Game>'}
        self.rows=[{'physical_id':33,'vehicle_class':'T2','ai_eligibility':{'quick_race':{'enabled':True}}}]
        self.collision={'FourRunner':'qualified-collision'}
    def contract(self):return build_contract(self.identity,self.resources,self.rows,collision_fingerprints=self.collision)
    def test_active_requires_full_dependency_baseline(self):
        current=self.contract()
        with self.assertRaisesRegex(ValueError,'no identity/dependency'):require_compatible(None,current,active=True)
        require_compatible(current,current,active=True)
        self.resources['DataGame/vehicles.xml']=self.resources['DataGame/vehicles.xml'].replace(b'1400',b'1800')
        with self.assertRaisesRegex(ValueError,'vehicles.xml'):require_compatible(current,self.contract(),active=True)
        require_compatible(current,self.contract(),active=False)
    def test_visuals_and_xml_formatting_are_not_identity(self):
        old=self.contract()
        self.resources['body.dxt']=b'new paint';self.resources['livery.json']=b'new number'
        self.resources['DataGame/vehicles.xml']=b'<Game>\n<Broker> <Value Value="1400" Type="Float" Name="Vehicles/FourRunner/Mass"/> </Broker></Game>'
        require_compatible(old,self.contract(),active=True)
    def test_collision_rules_family_and_modes_are_dependencies(self):
        old=self.contract()
        self.collision['FourRunner']='changed collision'
        with self.assertRaisesRegex(ValueError,'collision'):require_compatible(old,self.contract(),active=True)
        self.collision['FourRunner']='qualified-collision';self.rows[0]['ai_eligibility']['quick_race']['enabled']=False
        with self.assertRaisesRegex(ValueError,'mode eligibility'):require_compatible(old,self.contract(),active=True)
        self.rows[0]['ai_eligibility']['quick_race']['enabled']=True;self.identity['entries'][0]['family']='OtherFamily'
        with self.assertRaisesRegex(ValueError,'stable vehicle'):require_compatible(old,self.contract(),active=True)

class FinalClassOrdering(unittest.TestCase):
    def test_new_ids_can_be_interleaved_without_moving_old_relative_order(self):
        p=scenario(35,(8,14,13));p['classes']['T2']=SDK33['T2'][:2]+[34]+SDK33['T2'][2:5]+[33]+SDK33['T2'][5:]
        result=validate_profile(p)
        self.assertEqual(result['classes']['T2'].index(34),2)
        self.assertEqual([i for i in result['classes']['T2'] if i<33],SDK33['T2'])
        bad=copy.deepcopy(p);bad['classes']['T2'][0],bad['classes']['T2'][1]=bad['classes']['T2'][1],bad['classes']['T2'][0]
        with self.assertRaises(ValueError):validate_profile(bad)

if __name__=='__main__':unittest.main()
