"""Cross-milestone GT Garage / automatic-import compatibility checks."""
import gzip,json,tempfile,unittest
from pathlib import Path
from master_rallye.gt3_source import read_source,MAX_BYTES
from master_rallye.workshop.service import WorkshopProject
from master_rallye.workshop.classic import rebuild_classic,require_classic_approval
from master_rallye.classic_style import digest
from master_rallye.addon_sdk.auto_features import derive,procedural_cracks
from master_rallye.addon_sdk.native_states import author_states
from tests.synthetic.test_auto_features import model,TEXTURES

class GarageAutoSyncTests(unittest.TestCase):
    def test_wheel_image_binding_requires_finite_original_uvs(self):
        from master_rallye.addon_sdk.gt3_scene import packet_has_uvs
        from master_rallye.gt_auto_profile import wheel_face_bindings
        def draw(slot,uv,packet=0):
            return {'source_shape':slot,'packet':packet,'state':{'external_texture_index':slot},'issues':['runtime external environment texture'],'vertices':[{'uv':uv}for _ in range(3)],'triangles':[(0,1,2)]}
        good=draw(1,(0.,1.));generated=draw(0,None)
        bindings,audit=wheel_face_bindings({'draws':[generated,good,draw(1,None,1)]},[{'textures':1},{'textures':1}])
        self.assertEqual(set(bindings),{'1'})
        self.assertEqual(len(audit['unbound_no_uv_packets']),2)
        self.assertTrue(packet_has_uvs(good['vertices'],good['triangles']))
        for uv in (None,(),(0.,),(float('nan'),0.),(0.,float('inf'))):
            d=draw(1,uv);self.assertFalse(packet_has_uvs(d['vertices'],d['triangles']))
        self.assertFalse(packet_has_uvs(good['vertices'],[]))
        self.assertEqual(wheel_face_bindings({'draws':[good]},[{'textures':1}])[0],{})

    def test_shared_raw_gzip_reader_preserves_sources_and_bounds_expansion(self):
        from master_rallye.gt_auto_profile import read_source as auto_read
        from master_rallye.gt3_vehicle import _read_source as build_read
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);raw=b'synthetic GT source';plain=root/'source';packed=root/'source.gz';plain.write_bytes(raw);data=gzip.compress(raw);packed.write_bytes(data)
            for fn in (read_source,auto_read,build_read):self.assertEqual(fn(plain),raw);self.assertEqual(fn(packed),raw)
            self.assertEqual(packed.read_bytes(),data)
            packed.write_bytes(gzip.compress(bytes(MAX_BYTES+1)))
            for fn in (read_source,auto_read,build_read):
                with self.assertRaisesRegex(ValueError,'decoded source size budget'):fn(packed)
            packed.write_bytes(b'\x1f\x8bbroken')
            with self.assertRaisesRegex(ValueError,'gzip'):read_source(packed)

    def test_classic_noop_preserves_auto_native_state_type_and_controllers(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);donor=root/'stock/Navara';donor.mkdir(parents=True);raw=model()
            from master_rallye.dx import parse_dx_bytes
            from master_rallye.topology_writer import source_geometry
            from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
            m=parse_dx_bytes(raw);gs=source_geometry(m)
            raw=write_scene_dx(raw,[ScenePart(gs[d.draw_index],d.texture_tuple,bool(d.flags_0x20[0]),bool(d.flags_0x20[1]),bool(d.unknown_0x24&4))for d in m.physical_draws])
            for n in ('car.dx','complete.dx','wheel.dx'):(donor/n).write_bytes(raw)
            for n,v in TEXTURES.items():(donor/n).write_bytes(v)
            states,extra,_=derive(raw,TEXTURES);native,_=author_states(raw,states)
            for n,v in extra.items():(donor/n).write_bytes(v)
            (donor/'mr-auto-cracked-tga.dxt').write_bytes(procedural_cracks())
            candidate=root/'native-car.dx';candidate.write_bytes(native);author=root/'author';author.mkdir()
            spec={'vehicle_name':'Navara','source_vehicle_dir':str(donor),'resources':{'car.dx':{'source_sha256':digest(raw),'native_state_scene_candidate':str(candidate)}},'texture_edits':{},'texture_replacements':{}}
            (author/'vehicle-project.json').write_text(json.dumps(spec));(author/'addon.json').write_text(json.dumps({'addon_id':'synthetic-auto-state'}))
            p=WorkshopProject.create(author,root/'workshop');recipe={'version':2,'source_format':'GT3 ModelSet1','source_identity':{'model':'synthetic'},'class_reference':{'class':'T2','evidence':'synthetic only'},'source_models':p.data['inputs'],'stock_wheel_family':'Navara','stock_brake_family':'Navara','stock_wheel_sha256':digest(raw),'stock_brake_sha256':digest(raw),'roles':[],'limitations':['Synthetic no-op style; no gameplay claim']}
            path=root/'recipe.json';path.write_text(json.dumps(recipe));c,s,report=rebuild_classic(p,path,root/'stock',root/'version')
            rewritten=json.loads((c.working/'vehicle-project.json').read_text())['resources']['car.dx']
            self.assertIn('native_state_scene_candidate',rewritten)
            self.assertEqual((c.assets/'car.dx').read_bytes(),native);self.assertEqual((s.assets/'car.dx').read_bytes(),native)
            self.assertEqual(c.validate()['status'],'PASS')
            with self.assertRaisesRegex(ValueError,'approve'):require_classic_approval(c)

if __name__=='__main__':unittest.main()
