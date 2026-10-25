"""Independent physics ownership using generated Broker data, no game assets."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from master_rallye.addon_sdk.physics_profile import compile_family,apply_profile,validate_profile,validate_player_defaults
from master_rallye.addon_sdk.physics import clone_vehicle_family_xml
from master_rallye.addon_sdk.manifest import AddonValidationError
from master_rallye.vehicle_config_schema import RETAIL_REQUIRED_FIXED_SCHEMA
from master_rallye.vehicle_family_broker import PLAYER_MODIFICATION_FIELDS
from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes

def fixture():
    fields={}
    for p,t in RETAIL_REQUIRED_FIXED_SCHEMA.items():
        value={'Float':'1','Int':'1','Bool':'False','String':'harddirt','Vector3':'1 1 1'}[t]
        fields[p]=(t,value)
    for p,v in {'Chassis/TotalMass':'1000','Suspension/Front/UnsprungMass':'40','Suspension/Rear/UnsprungMass':'40','Engine/IdleRevs':'800','Engine/RevLimit':'8000','Engine/DriveType':'2','Engine/Gears':'3','Engine/TorqueEntries':'3','Engine/BrakeBias':'.5'}.items():fields[p]=(fields[p][0],v)
    for i in range(3):
        for group in ('Gear','ChangeUpRevs','ChangeDownRevs'):fields[f'Engine/{group}{i}']=('Float',str(i))
        fields[f'Engine/TorqueEntry{i}']=('Vector2',f'{i/2} 1')
    def xml(rows):return ('<Game>\n<Broker>\n'+'\n'.join(f'<Value Name="{p}" Type="{t}" Value="{v}" SaveOptions="False" SavePlayerState="False"/>' for p,(t,v) in rows.items())+'\n</Broker>\n</Game>\n').encode()
    vehicles=xml({'Vehicles/Navara/'+p:r for p,r in fields.items()}|{'Vehicles/Tyres/harddirt0/PeakMu':('Float','1')})
    mods=xml({f'Vehicles/Navara/Player{player}/Modifications/{p}':('Float','0') for player in (1,2) for p in PLAYER_MODIFICATION_FIELDS})
    sources={'DataGame/vehicles.xml':vehicles,'DataGame/Modifications.xml':mods}
    profile={'profile_version':1,'donor_family':'Navara','runtime_family':'AddonOne','source_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in sources.items()},'overrides':{},'notes':'synthetic fixture'}
    return sources,profile

class PhysicsProfileTests(unittest.TestCase):
    def test_raw_registry_binding_is_explicit_and_preserves_legacy_reproduction(self):
        from tools.vehicle_physics_native import reference_match_name,runtime_reference
        _,p=fixture();p['ride_height_reference_m']={'Front':-.15,'Rear':-.15}
        self.assertEqual(reference_match_name(p),'Vehicles/AddonOne')
        self.assertEqual(runtime_reference(p),{})
        p['ride_height_reference_binding']='registry_name'
        validate_profile(p,donor_family='Navara',runtime_family='AddonOne')
        self.assertEqual(reference_match_name(p),'AddonOne')
        self.assertEqual(runtime_reference(p),p['ride_height_reference_m'])
        p['ride_height_reference_binding']='guessed_path'
        with self.assertRaises(ValueError):validate_profile(p,donor_family='Navara',runtime_family='AddonOne')
        p['ride_height_reference_binding']='registry_name';del p['ride_height_reference_m']
        with self.assertRaises(ValueError):validate_profile(p,donor_family='Navara',runtime_family='AddonOne')

    def test_arch_solver_and_degenerate_selection_math(self):
        from tools.diagnose_vehicle_wheel_arches import solve
        self.assertEqual(solve([[2,0,0],[0,4,0],[0,0,8]],[4,12,32]),[2,3,4])
        with self.assertRaises(ValueError):solve([[1,1,1]]*3,[1,1,1])

    def test_optional_ride_reference_is_bounded_and_not_baked_into_menu_xml(self):
        from master_rallye.addon_sdk.physics_profile import validate_profile
        sources,p=fixture();p['ride_height_reference_m']={'Front':-.15,'Rear':-.15}
        a,_=compile_family(sources['DataGame/vehicles.xml'],p,donor_family='Navara',runtime_family='AddonOne',source_label='DataGame/vehicles.xml')
        q=copy.deepcopy(p);del q['ride_height_reference_m']
        b,_=compile_family(sources['DataGame/vehicles.xml'],q,donor_family='Navara',runtime_family='AddonOne',source_label='DataGame/vehicles.xml')
        self.assertEqual(a,b)
        for invalid in [{'Front':0},{'Front':float('nan'),'Rear':0},{'Front':True,'Rear':0},{'Front':.51,'Rear':0}]:
            p['ride_height_reference_m']=invalid
            with self.assertRaises(ValueError):validate_profile(p,donor_family='Navara',runtime_family='AddonOne')

    def test_effective_saved_setup_and_menu_units(self):
        from master_rallye.addon_sdk.physics_model import effective_setup
        sources,p=fixture();fields=parse_vehicle_config_bytes(sources['DataGame/vehicles.xml'],build='fixture').families['Navara']
        fields['Suspension/Front/RideHeight']['value']='-.18535'
        saved=b'<Game><Value Name="Vehicles/AddonOne/Player1/Modifications/Suspension/Front/RideHeight" Value=".18535"/></Game>'
        result,report=effective_setup(fields,family='AddonOne',saved_state=saved,reference={'Front':-.15,'Rear':-.14})
        self.assertAlmostEqual(report['menu_ride_height_mm']['Front'],0)
        self.assertAlmostEqual(float(result['Suspension/Front/RideHeight']['value']),-.15)
        self.assertEqual(fields['Suspension/Front/RideHeight']['value'],'-.18535')
        other,_=effective_setup(fields,family='Different',saved_state=saved)
        self.assertEqual(float(other['Suspension/Front/RideHeight']['value']),-.18535)
        with self.assertRaises(ValueError):effective_setup(fields,player=3)
        with self.assertRaises(ValueError):effective_setup(fields,family='AddonOne',saved_state=saved.replace(b'.18535',b'nan'))

    def test_symmetric_native_preload_is_not_mg_over_k_sag(self):
        from master_rallye.addon_sdk.physics_model import suspension_summary
        sources,p=fixture();fields=parse_vehicle_config_bytes(sources['DataGame/vehicles.xml'],build='fixture').families['Navara']
        for axle in ('Front','Rear'):
            fields['Suspension/'+axle+'/SpringArmRatio']['value']='1'
            fields['Suspension/'+axle+'/SpringRate']['value']='35000'
        rows=suspension_summary(fields)['rows']
        self.assertEqual([r['symmetric_jounce_estimate_m'] for r in rows],[0,0])

    def test_explicit_core_collision_fit_preserves_render_and_topology(self):
        from tests.synthetic.test_r4f import fixture as model_fixture
        from master_rallye.addon_sdk.physics_collision import fit_collision
        from master_rallye.dx import parse_dx_bytes
        raw=model_fixture(collision=True);model=parse_dx_bytes(raw)
        definition={'source_sha256':hashlib.sha256(raw).hexdigest(),'core_draw_indices':[0,1],'padding_m':[.05,.05,.05],'evidence':'two synthetic core meshes'}
        out,report=fit_collision(raw,definition);other=parse_dx_bytes(out)
        self.assertEqual(model.vertices,other.vertices);self.assertEqual(model.physical_draws,other.physical_draws)
        self.assertEqual(model.collision.convex_hull.representation_b.edges,other.collision.convex_hull.representation_b.edges)
        self.assertTrue(report['render_bytes_unchanged'])
        for edit in [{'source_sha256':'0'*64},{'core_draw_indices':[999]},{'padding_m':[100,100,100]}]:
            with self.assertRaises(ValueError):fit_collision(raw,{**definition,**edit})
    def test_native_attachment_formula_is_separate_from_source_preview(self):
        from master_rallye.addon_sdk.physics_model import wheel_attachments
        sources,p=fixture();fields=parse_vehicle_config_bytes(sources['DataGame/vehicles.xml'],build='fixture').families['Navara']
        fields['Dimensions/WheelBase']['value']='2.51';fields['Dimensions/TrackWidthFront']['value']='1.49';fields['Suspension/Front/RideHeight']['value']='-0.18535'
        result=wheel_attachments(fields);front=result['race_wheel_instances'][:2]
        self.assertEqual(front[0]['translation'],[.745,.18535,1.255]);self.assertEqual(front[1]['translation'],[-.745,.18535,1.255])
        fields['Dimensions/WheelBase']['value']='nan'
        with self.assertRaises(ValueError):wheel_attachments(fields)
    def test_empty_profile_is_exact_donor_clone(self):
        sources,p=fixture()
        for member,raw in sources.items():
            actual,r=compile_family(raw,p,donor_family='Navara',runtime_family='AddonOne',source_label=member)
            expected,_=clone_vehicle_family_xml(raw,donor_family='Navara',runtime_family='AddonOne',source_label=member)
            self.assertEqual(actual,expected);self.assertFalse(r['semantic_delta'])
    def test_typed_edits_are_deterministic_and_scoped(self):
        sources,p=fixture();p['overrides']={'DataGame/vehicles.xml':{'Dimensions/WheelBase':2.51,'Suspension/Front/RideHeight':-.18535,'Chassis/CentreOfGravity':[0,.35,.2],'Engine/AutoGears':True,'Engine/DriveType':2,'Engine/TorqueEntry1':[.5,.8]}}
        kwargs=dict(donor_family='Navara',runtime_family='AddonOne',source_label='DataGame/vehicles.xml');raw=sources[kwargs['source_label']]
        out,r=compile_family(raw,p,**kwargs);self.assertEqual(out,compile_family(raw,p,**kwargs)[0]);self.assertTrue(r['other_families_unchanged'])
        d=parse_vehicle_config_bytes(out,build='fixture');old=parse_vehicle_config_bytes(raw,build='fixture')
        self.assertEqual(d.families['Navara'],old.families['Navara']);self.assertEqual(d.excluded_families,old.excluded_families)
        self.assertEqual(d.families['AddonOne']['Dimensions/WheelBase']['value'],'2.51')
    def test_multiple_addons_do_not_alias(self):
        sources,p=fixture();raw=sources['DataGame/vehicles.xml'];p['overrides']={'DataGame/vehicles.xml':{'Dimensions/WheelBase':2.51}}
        out,_=compile_family(raw,p,donor_family='Navara',runtime_family='AddonOne',source_label='DataGame/vehicles.xml')
        q=copy.deepcopy(p);q['runtime_family']='AddonTwo';q['overrides']['DataGame/vehicles.xml']['Dimensions/WheelBase']=3.1
        out,_=clone_vehicle_family_xml(out,donor_family='Navara',runtime_family='AddonTwo',source_label='DataGame/vehicles.xml')
        out,_=apply_profile(out,q,donor_family='Navara',runtime_family='AddonTwo',source_label='DataGame/vehicles.xml')
        d=parse_vehicle_config_bytes(out,build='fixture');self.assertEqual(d.families['AddonOne']['Dimensions/WheelBase']['value'],'2.51');self.assertEqual(d.families['AddonTwo']['Dimensions/WheelBase']['value'],'3.1');self.assertEqual(d.families['Navara']['Dimensions/WheelBase']['value'],'1')
    def test_bad_types_ranges_counts_and_names_fail(self):
        sources,p=fixture();raw=sources['DataGame/vehicles.xml'];kw=dict(donor_family='Navara',runtime_family='AddonOne',source_label='DataGame/vehicles.xml')
        for path,value in [('Dimensions/WheelBase',True),('Dimensions/WheelBase',float('nan')),('Dimensions/WheelBase',0),('Chassis/TotalMass',100),('Chassis/MomentOfInertia',[0,1,1]),('Chassis/CentreOfGravity',[1,2]),('Engine/AutoGears',1),('Engine/DriveType',4),('Engine/Gears',4),('Engine/RevLimit',100),('Suspension/Front/RideHeight',3),('Suspension/Front/SpringRate',-1),('Suspension/Rear/TyreType','missing'),('Vehicles/Navara/Chassis/TotalMass',5),('Engine/TorqueEntry1',[0,.8]),('Engine/MagicAWD',1)]:
            with self.subTest(path=path,value=value):
                q=copy.deepcopy(p);q['overrides']={'DataGame/vehicles.xml':{path:value}}
                with self.assertRaises(AddonValidationError):compile_family(raw,q,**kw)
        q=copy.deepcopy(p);q['source_sha256']['DataGame/vehicles.xml']='0'*64
        with self.assertRaises(AddonValidationError):compile_family(raw,q,**kw)
        with self.assertRaises(AddonValidationError):compile_family(raw,p,**{**kw,'runtime_family':'Navara'})
    def test_player_defaults_have_independent_ownership(self):
        sources,p=fixture();member='DataGame/Modifications.xml';p['overrides']={member:{'Player1/Modifications/Suspension/Front/RideHeight':.1}}
        out,r=compile_family(sources[member],p,donor_family='Navara',runtime_family='AddonOne',source_label=member)
        self.assertIn(b'Value="0.1"',out);self.assertEqual(sources[member].count(b'Value="0"'),26)
        p['overrides'][member]['Player1/Modifications/Suspension/Front/RideHeight']=3
        with self.assertRaises(AddonValidationError):compile_family(sources[member],p,donor_family='Navara',runtime_family='AddonOne',source_label=member)
    def test_player_setup_is_additive_in_native_units(self):
        sources,p=fixture();p['overrides']={'DataGame/Modifications.xml':{'Player1/Modifications/Suspension/Front/SpringRate':1000}}
        generated={member:compile_family(raw,p,donor_family='Navara',runtime_family='AddonOne',source_label=member)[0] for member,raw in sources.items()}
        validate_player_defaults(generated['DataGame/vehicles.xml'],generated['DataGame/Modifications.xml'],'AddonOne')
        p['overrides']['DataGame/Modifications.xml']['Player1/Modifications/Suspension/Front/SpringRate']=-1000
        mods=compile_family(sources['DataGame/Modifications.xml'],p,donor_family='Navara',runtime_family='AddonOne',source_label='DataGame/Modifications.xml')[0]
        with self.assertRaises(AddonValidationError):validate_player_defaults(generated['DataGame/vehicles.xml'],mods,'AddonOne')
    def test_collection_reapplies_only_explicit_profile(self):
        from tools.addon_collection_runtime import _compose_family_xml,_family_value_map
        sources,p=fixture();raw=sources['DataGame/vehicles.xml'];p['overrides']={'DataGame/vehicles.xml':{'Dimensions/WheelBase':2.51}}
        base,_=clone_vehicle_family_xml(raw,donor_family='Navara',runtime_family='OldAddon',source_label='DataGame/vehicles.xml')
        expected,_=compile_family(raw,p,donor_family='Navara',runtime_family='AddonOne',source_label='DataGame/vehicles.xml')
        out,_=_compose_family_xml(base,base_family='OldAddon',addon_family='AddonOne',donor_family='Navara',expected_project_data=expected,source_label='DataGame/vehicles.xml',physics_profile=p)
        self.assertEqual(_family_value_map(out,'AddonOne','fixture'),_family_value_map(expected,'AddonOne','fixture'))
        with self.assertRaises(ValueError):_compose_family_xml(base,base_family='OldAddon',addon_family='AddonOne',donor_family='Navara',expected_project_data=expected,source_label='DataGame/vehicles.xml')
