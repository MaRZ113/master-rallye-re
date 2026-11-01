import copy,struct,unittest
from dataclasses import replace
from master_rallye.addon_sdk.auto_features import zone_glass
from master_rallye.addon_sdk.heritage_source import repair_global_indices
from master_rallye.addon_sdk.native_effect_reference import reference_brake_glow
from master_rallye.addon_sdk.native_states import wrap_states,author_states
from master_rallye.addon_sdk.historical_physics import source_family_profile
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.topology_writer import DrawGeometry,CompiledVertex
from master_rallye.dx import parse_dx_bytes
from tests.synthetic.test_heritage_source import fixture
from tests.synthetic.test_physics_profile import fixture as physics_fixture
from tools.build_runtime_launcher import _header,LauncherBuildError
from tools.build_sdk_roster import derive
from tools.restore_demo_forester import localized_records


def lamps(scale=1.):
    vertices=[];triangles=[]
    for cx in (-1.,1.):
        start=len(vertices)
        for x,y in ((-.1,-.1),(.1,-.1),(.1,.1),(-.1,.1)):
            vertices.append(CompiledVertex((cx+x*scale,y*scale,-1.),(0.,0.,-1.),b'\xff'*4,(((x+.1)*5,(y+.1)*5),)))
        triangles.extend((tuple(start+i for i in t))for t in ((0,2,1),(0,3,2)))
    return DrawGeometry(tuple(vertices),tuple(triangles))


class DefinitiveRestorationTests(unittest.TestCase):
    def test_windshield_outer_corners_must_not_become_side_glass(self):
        points={0:((.8,0,0),(1.,0,0),(.9,1,-1)),1:((-1.,0,0),(-.8,0,0),(-.9,1,-1))}
        self.assertEqual(dict(zone_glass(points)),{'screenfront':[0,1]})

    def test_cache_repair_rejects_changes_to_triangle_membership(self):
        raw=fixture();m=parse_dx_bytes(raw);bad=bytearray(raw)
        struct.pack_into('<I',bad,m.global_index_table.data_offset,8)
        with self.assertRaises(ValueError):repair_global_indices(bytes(bad),require_order_equivalence=True)

    def test_cache_repair_of_cyclic_order_preserves_every_noncache_byte(self):
        raw=fixture();m=parse_dx_bytes(raw);changed=bytearray(raw);off=m.global_index_table.data_offset
        first=struct.unpack_from('<3I',raw,off);struct.pack_into('<3I',changed,off,*first[1:],first[0])
        fixed,count=repair_global_indices(bytes(changed))
        self.assertEqual(fixed,raw);self.assertEqual(count,3)

    def test_reference_glow_preserves_native_uv_color_and_separate_geometry(self):
        geometry=lamps();off=ScenePart(geometry,('off-tga','perspex-tga','Null'),environment=True);on=replace(off,textures=('on-tga','perspex-tga','Null'),diffuse=False,environment=True)
        halo=replace(on,geometry=lamps(1.8),textures=('halo-tga','perspex-tga','Null'),alpha=True)
        donor=wrap_states(fixture(),[('blight',[off],[on,halo])]);source=write_scene_dx(fixture(),[replace(off,geometry=lamps(1.3))])
        selection={'source_draw':0,'triangles':[0,1,2,3]}
        glow,report=reference_brake_glow(source,donor,selection)
        self.assertEqual(len(glow.geometry.triangles),4);self.assertTrue(glow.alpha);self.assertFalse(glow.diffuse)
        self.assertEqual([v.uvs for v in glow.geometry.vertices],[v.uvs for v in halo.geometry.vertices])
        self.assertNotEqual(glow.geometry.vertices,halo.geometry.vertices)
        profile={'source_sha256':__import__('hashlib').sha256(source).hexdigest(),'brake':{**selection,'lit_texture':'source-lit','glow_texture':'unused','evidence':'synthetic native reference'}}
        result,audit=author_states(source,profile,brake_glow=glow,brake_material=report['lit_material'])
        self.assertTrue(parse_dx_bytes(result).diagnostics.validated);self.assertTrue(audit['intact_off_geometry_normals_uv_materials_identical'])
        self.assertEqual(result,author_states(source,profile,brake_glow=glow,brake_material=report['lit_material'])[0])
        with self.assertRaises(ValueError):reference_brake_glow(source,source,selection)
        with self.assertRaises(ValueError):reference_brake_glow(source,donor,{'source_draw':0,'triangles':[0,0]})

    def test_original_physics_values_are_typed_and_donor_only_fields_explicit(self):
        resources,_=physics_fixture();source=resources['DataGame/vehicles.xml'].replace(b'Value="1000"',b'Value="1340"')
        profile,report=source_family_profile(source,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored')
        self.assertEqual(profile['overrides']['DataGame/vehicles.xml']['Chassis/TotalMass'],1340.)
        self.assertEqual(report['unmapped'],[]);self.assertEqual(resources,physics_fixture()[0])
        bad=source.replace(b'</Broker>',b'<Value Name="Vehicles/Navara/Unknown/Value" Type="Float" Value="2"/></Broker>')
        with self.assertRaisesRegex(ValueError,'Unmapped'):source_family_profile(bad,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored')

    def test_31_records_require_distinct_launcher_profile_and_contiguous_ids(self):
        p=dict(addon_plan_sha256='a'*64,native_patch_manifest_sha256='a'*64,native_patch_operations_sha256='a'*64,resource_manifest_sha256='a'*64,resource_index_sha256='a'*64,reconstructed_reference_file_sha256='a'*64,retail_exe={'sha256':'a'*64},resource_count=1,
               profile='sdk-multi-addon-roster-experimental-31',sdk_roster_layout={'record_count':31,'addon_ids':list(range(26,31))},native_extension={'address':0x10000000,'size':180000,'allocation_size':262144,'sha256':'a'*64})
        self.assertIn(b'262144u',_header(p,{'operations':[{}]}))
        for key,value in [('profile','sdk-multi-addon-roster'),('sdk_roster_layout',{'record_count':31,'addon_ids':[26,27,28,30]})]:
            bad=copy.deepcopy(p);bad[key]=value
            with self.assertRaises(LauncherBuildError):_header(bad,{'operations':[{}]})
        for value in (True,32,'31'):
            with self.assertRaises(ValueError):derive({'sdk_roster_version':1,'base_runtime':'absent','projects':[{}, {}, {}],'experimental_record_count':value})
        with self.assertRaisesRegex(ValueError,'explicit experimental_record_count'):derive({'sdk_roster_version':1,'base_runtime':'absent','projects':[{}, {}, {}]})

    def test_historical_tyre_coefficients_have_private_ownership(self):
        from master_rallye.addon_sdk.physics_profile import compile_family,publish_owned_tyres
        from master_rallye.addon_sdk.manifest import AddonValidationError
        import xml.etree.ElementTree as ET
        resources,_=physics_fixture();original=resources['DataGame/vehicles.xml']
        source=original.replace(b'Name="Vehicles/Tyres/harddirt0/PeakMu" Type="Float" Value="1"',b'Name="Vehicles/Tyres/harddirt0/PeakMu" Type="Float" Value="1.4"')
        profile,report=source_family_profile(source,resources,source_family='Navara',donor_family='Navara',runtime_family='Restored')
        self.assertEqual(report['owned_tyres']['different_source_fields'],['0/PeakMu'])
        compiled,_=compile_family(original,profile,donor_family='Navara',runtime_family='Restored',source_label='DataGame/vehicles.xml')
        rows={v.get('Name'):v.get('Value')for v in ET.fromstring(compiled).iter('Value')}
        self.assertEqual(rows['Vehicles/Tyres/harddirt0/PeakMu'],'1');self.assertEqual(float(rows['Vehicles/Tyres/RestoredTyre0/PeakMu']),1.4)
        self.assertEqual(rows['Vehicles/Restored/Suspension/Front/TyreType'],'RestoredTyre')
        published=publish_owned_tyres(original,compiled,profile)
        with self.assertRaises(AddonValidationError):publish_owned_tyres(published,compiled,profile)
        wrong=compiled.replace(b'Value="1.4"',b'Value="9"')
        with self.assertRaises(AddonValidationError):publish_owned_tyres(original,wrong,profile)

    def test_localized_binding_uses_category_and_index_not_nearby_string_order(self):
        data=struct.pack('<6I',52,8,0x4530f0,57,8,0x453ac8)
        self.assertEqual(localized_records(data,0x453ac8),[{'file_offset':12,'category':57,'index':8,'pointer':0x453ac8}])
        self.assertEqual(localized_records(b'x'+data,0x453ac8),[])


if __name__=='__main__':unittest.main()
