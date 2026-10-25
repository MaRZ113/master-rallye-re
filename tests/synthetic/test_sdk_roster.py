import copy,unittest
from tools.build_sdk_roster import append_owned_family
from tools.build_runtime_launcher import _header,LauncherBuildError

class SDKRosterTests(unittest.TestCase):
    def test_frontend_profiler_requires_boolean(self):
        from tools.build_sdk_roster import derive
        for value in (1,'true',None,[]):
            with self.assertRaisesRegex(ValueError,'explicit boolean'):
                derive({'sdk_roster_version':1,'base_runtime':'absent','projects':[],'frontend_profiler':value})
            with self.assertRaisesRegex(ValueError,'explicit boolean'):
                derive({'sdk_roster_version':1,'base_runtime':'absent','projects':[],'frontend_bulk_read':value})
    def test_existing_probe_reservations_cannot_be_stolen(self):
        from master_rallye.addon_sdk.collection import reserve_roster
        from master_rallye.addon_sdk.manifest import AddonValidationError
        slots=[{'physical_id':27,'vehicle_class':'T2','class_local_index':7},{'physical_id':28,'vehicle_class':'T2','class_local_index':8}]
        old={'version':1,'reservations':[{'addon_id':'subaru','physical_id':27,'vehicle_class':'T2','class_local_index':7},{'addon_id':'capacity-probe-0','physical_id':28,'vehicle_class':'T2','class_local_index':8}]}
        requests=[{'addon_id':'subaru','physical_id':27,'vehicle_class':'T2'},{'addon_id':'lancer','physical_id':28,'vehicle_class':'T2'}]
        with self.assertRaises(AddonValidationError):reserve_roster(requests,slots=slots,previous=old)
        lock,rows=reserve_roster(requests,slots=slots)
        self.assertEqual(rows[1]['addon_id'],'lancer')
        self.assertEqual(reserve_roster(list(reversed(requests)),slots=slots,previous=lock)[0],lock)

    def test_workflow_routes_only_existing_tools(self):
        from tools.vehicle_sdk import command,COMMANDS
        for name in COMMANDS:
            result=command(name,['--help']);self.assertTrue(result[1].endswith('.py'));self.assertEqual(result[-1],'--help')
        with self.assertRaises(ValueError):command('arbitrary',[])

    def test_owned_family_only(self):
        base=b'<Broker>\n<Value Name="Vehicles/Stock/Mass" Value="10"/>\n</Broker>'
        source=b'<Broker>\n<Value Name="Vehicles/Other/Mass" Value="999"/>\n<Value Name="Vehicles/Addon/Mass" Value="7"/>\n</Broker>'
        result=append_owned_family(base,source,'Addon')
        self.assertIn(b'Value="10"',result);self.assertIn(b'Value="7"',result);self.assertNotIn(b'999',result)
        with self.assertRaises(ValueError):append_owned_family(result,source,'Addon')
        with self.assertRaises(ValueError):append_owned_family(base,source,'Missing')
        with self.assertRaises(ValueError):append_owned_family(base,source,'../Foo')
        mixed=b'<Broker>\n<Value Name="Vehicles/Addon/Mass" Value="7"/><Value Name="Other" Value="8"/>\n</Broker>'
        with self.assertRaises(ValueError):append_owned_family(base,mixed,'Addon')

    def test_bounded_combined_layout(self):
        p={k:'a'*64 for k in ('addon_plan_sha256','native_patch_manifest_sha256','native_patch_operations_sha256','resource_manifest_sha256','resource_index_sha256','reconstructed_reference_file_sha256')}
        p.update(profile='sdk-multi-addon-roster',retail_exe={'sha256':'a'*64},resource_count=1,sdk_roster_layout={'record_count':30,'addon_ids':[26,27,28,29]},native_extension={'address':0x10000000,'size':180000,'allocation_size':262144,'sha256':'a'*64,'writable_ranges':[{'offset':172032,'size':4096}]})
        self.assertIn(b'MR_EXTENSION_ALLOCATION_SIZE 262144u',_header(p,{'operations':[{}]}))
        for key,value in [('record_count',31),('record_count',True),('addon_ids',[26,28,29])]:
            bad=copy.deepcopy(p);bad['sdk_roster_layout'][key]=value
            with self.assertRaises(LauncherBuildError):_header(bad,{'operations':[{}]})
        bad=copy.deepcopy(p);bad['native_extension']['allocation_size']=524288
        with self.assertRaises(LauncherBuildError):_header(bad,{'operations':[{}]})
        bad=copy.deepcopy(p);bad['profile']='unknown'
        with self.assertRaises(LauncherBuildError):_header(bad,{'operations':[{}]})
