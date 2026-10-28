"""Sealed rolling-wheel resources and per-side diagnostic staging."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_sdk_roster import qualified_wheel_profiles
from master_rallye.universal_vehicle_scene import sha
from master_rallye.preview_scene import stage_vehicle
from tests.synthetic.test_workshop import family


class NativeWheelResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.assets=self.root/'assets';family(self.assets)
        self.raw=(self.assets/'wheel.dx').read_bytes()
        self.names=['wheel-source'+str(i)+'.dx'for i in range(4)]
        self.keys=['Vehicles/SyntheticSUV/'+name[:-3]for name in self.names]
        self.resources={'DataGx/'+key+'.dx':self.raw for key in self.keys}
        self.rows=[{'identity':{'runtime_family':'SyntheticSUV'},'assets':{'required_roles':['car.dx','complete.dx','wheel.dx',*self.names]}}]
        self.profile={'runtime_family':'SyntheticSUV','resource_keys':self.keys,'resource_sha256':[sha(self.raw)]*4}
        for name in self.names:(self.assets/name).write_bytes(self.raw)
        self.preview={'provenance':'Invented distinct source wheel instances; no native-game claim',
                      'race_wheel_instances':[{'translation':[(-1 if i%2 else 1),0,(2 if i<2 else -2)],'rotation_y':0}for i in range(4)],
                      'race_wheel_resources':self.names}

    def test_sealed_resources_admit_only_declared_addon_family(self):
        value=qualified_wheel_profiles([self.profile],self.resources,self.rows)
        self.assertEqual(value,[{'runtime_family':'SyntheticSUV','resource_keys':self.keys}])
        self.assertEqual(qualified_wheel_profiles([],{},[]),[])
        for patch in ({'runtime_family':'StockPajero'}, {'resource_keys':['Vehicles/Other/wheel0',*self.keys[1:]]},
                      {'resource_keys':[self.keys[0]]*4}, {'resource_sha256':['0'*64]*4}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                qualified_wheel_profiles([{**self.profile,**patch}],self.resources,self.rows)

    def test_missing_extra_dx_and_undeclared_roles_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'missing'):
            qualified_wheel_profiles([self.profile],{},self.rows)
        rows=copy.deepcopy(self.rows);rows[0]['assets']['required_roles'].pop()
        with self.assertRaisesRegex(ValueError,'required DX role'):
            qualified_wheel_profiles([self.profile],self.resources,rows)
        with self.assertRaises(ValueError):qualified_wheel_profiles([self.profile,self.profile],self.resources,self.rows)

    def test_actual_preview_stages_all_four_resources_without_shared_instances(self):
        profile=self.root/'layout.json';profile.write_text(json.dumps(self.preview))
        result=stage_vehicle(self.assets/'car.dx',self.root/'preview.mrpv',profile=profile)
        self.assertEqual(result['draws'],7)  # body, frontend, canonical wheel mode + four exact source instances
        text=json.dumps(result)
        for name in self.names:self.assertIn(name,text)
        before=(self.root/'preview.mrpv').read_bytes()
        stage_vehicle(self.assets/'car.dx',self.root/'preview.mrpv',profile=profile)
        self.assertEqual(before,(self.root/'preview.mrpv').read_bytes())

    def test_perwheel_preview_rejects_unsafe_missing_and_ambiguous_bindings(self):
        profile=self.root/'layout.json'
        for names in (['../wheel.dx',*self.names[1:]],['wheel.dx',*self.names[1:]],self.names[:3],
                      [self.names[0]]*4,['absent.dx',*self.names[1:]]):
            with self.subTest(names=names):
                profile.write_text(json.dumps({**self.preview,'race_wheel_resources':names}))
                with self.assertRaises((ValueError,OSError)):
                    stage_vehicle(self.assets/'car.dx',self.root/'preview.mrpv',profile=profile)
