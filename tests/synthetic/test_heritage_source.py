import copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from master_rallye.addon_sdk.heritage_source import compatible_model,inspect_family,stage_family,edition,verify_author,create_author
from master_rallye.addon_sdk.native_states import author_states,wrap_states
from master_rallye.gxi import parse_gxi_bytes,encode_gxi_as_observed_dxt
from master_rallye.dx import parse_dx_bytes
from master_rallye.preview_scene import logical_cases
from tests.synthetic.test_library import simple_record,synthetic_dx,footer56


def fixture():
    points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]*3
    records=[]
    for i in range(3):
        b=bytearray(simple_record(i*3,2,i*3,3,('base-tga','Null','Null')));b[32:36]=bytes([0,0,1,1]);struct.pack_into('<I',b,36,3);records.append(b)
    return synthetic_dx(points,[0,1,2]*3,records,[(i*3,i*3,3)for i in range(3)],trailing=footer56(points))


class HeritageTests(unittest.TestCase):
    def test_edition_fingerprints_are_full_sha256(self):
        from master_rallye.addon_sdk.heritage_source import EDITIONS
        for value in EDITIONS:self.assertRegex(value,r'^[0-9a-f]{64}$')

    def test_reindexed_mirrored_wheels_require_two_geometry_uv_topology_proofs(self):
        from dataclasses import replace
        from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
        from master_rallye.topology_writer import CompiledVertex,DrawGeometry
        from master_rallye.preview_scene import _unordered_presentation_wheels
        vs=tuple(CompiledVertex(p,(1.,0.,0.),b'\xff'*4,((i/4.,i/8.),))for i,p in enumerate(((0.,0.,0.),(.2,.1,0.),(.1,.3,.2),(.05,.2,-.3))))
        g=DrawGeometry(vs,((0,1,2),(0,2,3),(0,3,1),(1,3,2)))
        wheel_parts=[ScenePart(g,(name,'Null','Null'))for name in ('a','b')];complete_parts=[]
        for part in wheel_parts:
            vertices=[];triangles=[]
            for j,(x,z)in enumerate(((-1.,-1.2),(-1.,1.2),(1.,-1.2),(1.,1.2))):
                order=list(range(4))if j<2 else [2,0,3,1];mapping={old:j*4+new for new,old in enumerate(order)}
                for old in order:
                    v=vs[old];p=v.position;vertices.append(replace(v,position=((1 if x<0 else -1)*p[0]+x,p[1],p[2]+z),color=b'\x80'*4))
                triangles.extend(tuple(mapping[k]for k in t)for t in g.triangles)
            complete_parts.append(replace(part,geometry=DrawGeometry(tuple(vertices),tuple(triangles))))
        wheel=parse_dx_bytes(write_scene_dx(fixture(),wheel_parts));complete=parse_dx_bytes(write_scene_dx(fixture(),complete_parts))
        result=_unordered_presentation_wheels(None,complete,wheel,(0.,0.,0.),2)
        self.assertEqual(len(result['race_wheel_instances']),4);self.assertIn('2 independent parts',result['provenance'])
        bad=replace(complete_parts[1],geometry=replace(complete_parts[1].geometry,triangles=complete_parts[1].geometry.triangles[:-1]))
        with self.assertRaises(ValueError):_unordered_presentation_wheels(None,parse_dx_bytes(write_scene_dx(fixture(),[complete_parts[0],bad])),wheel,(0.,0.,0.),2)

    def test_independent_donor_recomputed_from_both_exact_retail_members(self):
        from tests.synthetic.test_physics_profile import fixture as physics_fixture
        from master_rallye.addon_sdk.physics_profile import compile_family
        from tools.addon_collection_runtime import _verify_independent_donor
        sources,profile=physics_fixture();sources={n:b.replace(b'Navara',b'Trooper')for n,b in sources.items()};profile['donor_family']='Trooper';profile['source_sha256']={n:hashlib.sha256(b).hexdigest()for n,b in sources.items()}
        with tempfile.TemporaryDirectory()as td:
            r=Path(td)
            for member,raw in sources.items():
                f=r/member;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(compile_family(raw,profile,donor_family='Trooper',runtime_family='AddonOne',source_label=member)[0])
            with patch('master_rallye.addon_sdk.project.read_sma_member',side_effect=lambda path,member:sources[member]):
                _verify_independent_donor(r,'Trooper','AddonOne',profile)
                (r/'DataGame/vehicles.xml').write_bytes(b'tamper')
                with self.assertRaisesRegex(ValueError,'recompilation'):_verify_independent_donor(r,'Trooper','AddonOne',profile)

    def test_gxi_exact_orientation_bgra_and_crc(self):
        raw=struct.pack('<IHH',0x13039,2,2)+bytes(range(16));image=parse_gxi_bytes(raw)
        data=encode_gxi_as_observed_dxt(image)
        self.assertEqual(data[20:],bytes([10,9,8,11,14,13,12,15,2,1,0,3,6,5,4,7]))
        for bad in (raw[:-1],raw+b'x',b'bad',struct.pack('<IHH',0x13039,0,2)):
            with self.assertRaises(Exception):parse_gxi_bytes(bad)
    def test_revision_passthrough_and_unsupported_fail_closed(self):
        raw=fixture();self.assertEqual(compatible_model(raw,'synthetic')[0],raw)
        bad=bytearray(raw);struct.pack_into('<I',bad,4,127)
        with self.assertRaisesRegex(ValueError,'127'):compatible_model(bytes(bad),'test')
    def test_closure_exact_local_texture_and_missing_role(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td)
            for n in ('car.dx','complete.dx','wheel.dx'):(r/n).write_bytes(fixture())
            (r/'base-tga.gxi').write_bytes(struct.pack('<IHH',0x13039,1,1)+bytes([1,2,3,255]))
            a=inspect_family(r);self.assertTrue(a['qualified_for_staging']);self.assertEqual(a['textures']['base-tga']['policy'],'OBSERVED_GXI_TO_DXT')
            (r/'base-tga.dxt').write_bytes(encode_gxi_as_observed_dxt(parse_gxi_bytes((r/'base-tga.gxi').read_bytes())))
            self.assertTrue(inspect_family(r)['textures']['base-tga']['gxi_pair_byte_identical'])
            (r/'car.dx').unlink();self.assertFalse(inspect_family(r)['qualified_for_staging'])
    def test_unknown_edition_inventory_is_not_build_permission(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);(r/'MRallye.exe').write_bytes(b'unknown executable')
            self.assertFalse(edition(r)['executable_qualified'])
            with self.assertRaises((ValueError,FileNotFoundError)):stage_family(r,'Missing',r/'out')
            self.assertFalse((r/'out').exists())
    def test_explicit_states_preserve_all_off_attributes_and_collision(self):
        raw=fixture();p={'source_sha256':hashlib.sha256(raw).hexdigest(),'panes':[{'label':'screenfront','source_draw':0,'triangles':[0],'broken_uv_axes':[0,1],'broken_texture':'broken-tga'}],'brake':{'source_draw':1,'triangles':[0],'lit_texture':'lit-tga','glow_texture':'glow-tga','evidence':'synthetic explicit source'}}
        data,a=author_states(raw,p);m=parse_dx_bytes(data);self.assertTrue(a['collision_preserved']);self.assertEqual(a['original_triangles'],3);self.assertEqual(data,author_states(raw,p)[0]);self.assertFalse(a['runtime_qualified'])
        cases,_=logical_cases(m);self.assertEqual(len(cases),5)
        for kind in ('hash','duplicate','overlap','control'):
            q=copy.deepcopy(p)
            if kind=='hash':q['source_sha256']='0'*64
            elif kind=='duplicate':q['panes'][0]['triangles']=[0,0]
            elif kind=='overlap':q['brake']['source_draw']=0
            else:q['panes'][0]['label']='guess'
            with self.assertRaises(ValueError):author_states(raw,q)
    def test_source_tamper_rejected_and_normal_projects_unchanged(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);self.assertIsNone(verify_author(r));(r/'native-import').mkdir();(r/'native-import/a.txt').write_bytes(b'original');(r/'assets/source/Donor').mkdir(parents=True)
            report={'version':1,'adapter':'native-mr-heritage','source':{'edition':'synthetic'},'family':'Synthetic','physics_donor':'Donor','resource_pins':{},'immutable_source_sha256':{'a.txt':hashlib.sha256(b'original').hexdigest()}}
            (r/'heritage-import.json').write_text(json.dumps(report));self.assertEqual(verify_author(r)['status'],'PASS_IMMUTABLE_HERITAGE_SOURCE');(r/'native-import/a.txt').write_bytes(b'tamper')
            with self.assertRaisesRegex(ValueError,'changed'):verify_author(r)

if __name__=='__main__':unittest.main()
