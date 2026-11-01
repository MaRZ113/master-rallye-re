"""Source-free restoration policy, ownership and compatibility boundaries."""
import copy,json,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from master_rallye.addon_sdk.demo_restoration import validate_manifest,verify_inputs,resolve
from master_rallye.addon_sdk.historical_physics import source_family_profile
from master_rallye.addon_sdk.physics_profile import compile_family
from tests.synthetic.test_physics_profile import fixture
from tools.build_runtime_launcher import _header,LauncherBuildError
from tools.build_sdk_roster import derive
ROOT=Path(__file__).resolve().parents[2]


class DemoRestorationTests(unittest.TestCase):
    def manifest(self):return json.loads((ROOT/'research/vehicles/sdk/restorations/rav4-931.json').read_text())

    def test_per_car_data_and_unknown_driver_are_explicit(self):
        a=self.manifest();b=json.loads((ROOT/'research/vehicles/sdk/restorations/forester-931.json').read_text())
        self.assertIs(validate_manifest(a),a);self.assertIs(validate_manifest(b),b)
        self.assertIsNone(a['identity']['driver']['value']);self.assertEqual(b['identity']['driver']['value'],'DARREN SUTHERLAND')
        self.assertNotEqual(a['features']['states']['source_sha256'],b['features']['states']['source_sha256'])
        self.assertEqual(len({t for p in a['features']['states']['panes']for t in p['triangles']}),14)
        self.assertEqual(sum(len(p['triangles'])for p in a['features']['states']['panes']),14)
        for change in ({'runtime_family':'../stock'},{'version':True},{'original_geometry':{}},{'runtime':{**a['runtime'],'physical_id':True}}):
            with self.assertRaises(ValueError):validate_manifest({**a,**change})

    def test_manifests_cannot_write_texture_or_artwork_outside_the_project(self):
        original=self.manifest()
        for value in ('../../original','C:/game/original','Null','a\\b'):
            bad=copy.deepcopy(original);key=next(iter(bad['features']['texture_aliases']));bad['features']['texture_aliases'][key]=value
            with self.assertRaises(ValueError):validate_manifest(bad)
        bad=copy.deepcopy(original);bad['identity']['artwork']['../../original']=bad['identity']['artwork'].pop('smallcarsheet')
        with self.assertRaises(ValueError):validate_manifest(bad)

    def test_source_escape_and_links_fail_before_any_output(self):
        with tempfile.TemporaryDirectory()as td:
            roots={'data':td}
            for p in ('../other','/absolute','a\\b','C:/game'):
                with self.assertRaises(ValueError):resolve(roots,'data',p)
            self.assertEqual(resolve(roots,'data','car.dx'),Path(td)/'car.dx')
            source=Path(td)/'source';source.mkdir();(source/'extra.dx').write_bytes(b'fixture')
            m=self.manifest();m['source'].update(root='data',directory='source')
            with self.assertRaisesRegex(ValueError,'file set'):verify_inputs(m,roots)

    def test_output_cannot_be_nested_inside_an_accepted_project(self):
        from unittest.mock import patch
        from master_rallye.addon_sdk.demo_restoration import prepare
        with tempfile.TemporaryDirectory()as td:
            root=Path(td);sdk=root/'sdk';source=root/'source';source.mkdir();accepted=sdk/'.research-output/accepted'
            config={'projects':[{'project':str(accepted/str(i)),'build':str(accepted/(str(i)+'-build')),'physical_id':i}for i in (28,29,30)]}
            path=root/'roster.json';path.write_text(json.dumps(config));output=accepted/'30/new-output'
            with patch('master_rallye.addon_sdk.demo_restoration.verify_inputs',return_value=(source,{}, {}, [])):
                with self.assertRaises(ValueError):prepare(self.manifest(),{'data':str(source)},path,output,sdk_root=sdk,build=False)
            self.assertFalse(output.exists());self.assertEqual(json.loads(path.read_text()),config)

    def test_compatible_physics_keeps_unsupported_source_values_out_of_retail(self):
        resources,_=fixture();raw=resources['DataGame/vehicles.xml'];source=raw.replace(b'</Broker>',b'<Value Name="Vehicles/Navara/DamageParams/OldThreshold" Type="Float" Value="99"/>\n</Broker>')
        reason={'DamageParams/OldThreshold':'Older damage solver is not equivalent'}
        profile,report=source_family_profile(source,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored',source_only=reason)
        self.assertEqual(report['source_only_fields']['DamageParams/OldThreshold']['original']['Value'],'99')
        compiled,_=compile_family(raw,profile,donor_family='Navara',runtime_family='Restored',source_label='DataGame/vehicles.xml')
        self.assertNotIn(b'OldThreshold',compiled);self.assertEqual(resources,fixture()[0])
        with self.assertRaisesRegex(ValueError,'Unmapped'):source_family_profile(source,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored')
        with self.assertRaises(ValueError):source_family_profile(source,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored',source_only={'NotPresent':'guess'})

    def test_retained_curve_and_tyres_require_complete_explicit_groups(self):
        resources,_=fixture();source=resources['DataGame/vehicles.xml'];prefix='Vehicles/Navara/'
        names=[v.get('Name')[len(prefix):]for v in ET.fromstring(source).iter('Value')if v.get('Name','').startswith(prefix)]
        with self.assertRaisesRegex(ValueError,'count and every'):source_family_profile(source,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored',source_only={'Engine/TorqueEntries':'old curve'})
        retained={n:'Retain retail curve as a group'for n in names if n=='Engine/TorqueEntries'or n.startswith('Engine/TorqueEntry')}
        retained.update({f'Suspension/{a}/TyreType':'Retain retail tyre references'for a in ('Front','Rear')})
        p,r=source_family_profile(source,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored',source_only=retained)
        self.assertNotIn('owned_tyres',p);self.assertFalse(any(n in p['overrides']['DataGame/vehicles.xml']for n in retained))

    def test_32_layout_has_a_distinct_header_guard_and_no_33_upgrade(self):
        p=dict(addon_plan_sha256='a'*64,native_patch_manifest_sha256='a'*64,native_patch_operations_sha256='a'*64,resource_manifest_sha256='a'*64,resource_index_sha256='a'*64,reconstructed_reference_file_sha256='a'*64,retail_exe={'sha256':'a'*64},resource_count=1,
               profile='sdk-multi-addon-roster-experimental-32',sdk_roster_layout={'record_count':32,'addon_ids':list(range(26,32))},native_extension={'address':0x10000000,'size':190000,'allocation_size':262144,'sha256':'a'*64})
        self.assertIn(b'262144u',_header(p,{'operations':[{}]}))
        for profile in ('sdk-multi-addon-roster','sdk-multi-addon-roster-experimental-31'):
            with self.assertRaises(LauncherBuildError):_header({**p,'profile':profile},{'operations':[{}]})
        for count in (True,33,'32'):
            with self.assertRaises(ValueError):derive({'sdk_roster_version':1,'base_runtime':'absent','projects':[{}, {}, {}, {}],'experimental_record_count':count})

    def test_shared_workflow_contains_no_vehicle_geometry_or_identity_literals(self):
        from master_rallye.addon_sdk import demo_restoration
        source=Path(demo_restoration.__file__).read_text()
        for token in ('DARREN SUTHERLAND','DefForester','DefRav4','screenfront\": [0','75d3a6a37b'):
            self.assertNotIn(token,source)

    def test_generated_menu_and_hud_use_independent_cameras_and_keep_mesh_immutable(self):
        from tools.generate_vehicle_ui_previews import render_sources
        from tests.synthetic.test_heritage_source import fixture as mesh_fixture
        import hashlib
        with tempfile.TemporaryDirectory()as td:
            root=Path(td);family=root/'family';family.mkdir();raw=mesh_fixture();(family/'complete.dx').write_bytes(raw)
            report=render_sources(family,root/'ui',roles=['vehicle_select_art','smallcarsheet'])
            self.assertEqual((family/'complete.dx').read_bytes(),raw)
            menu,hud=report['vehicle_select_art'],report['smallcarsheet']
            self.assertEqual(menu['projection'],'perspective');self.assertEqual(hud['projection'],'orthographic')
            self.assertNotEqual(menu['camera_azimuth'],hud['camera_azimuth'])
            self.assertNotEqual((root/'ui/vehicle_select_art.png').read_bytes(),(root/'ui/smallcarsheet.png').read_bytes())
