"""Source-free checks of bounded Michelin authoring; no proprietary payloads."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from master_rallye import michelin_native_pilot as p
from master_rallye.scene_dx_writer import ScenePart
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.dxt import parse_dxt_bytes


def part(count):
    vertices=tuple(CompiledVertex((float(i),float(j),0.),(0.,0.,1.),bytes((20,40,80,255)),((j/2.,0.),))for i in range(count)for j in range(3))
    return ScenePart(DrawGeometry(vertices,tuple((3*i,3*i+1,3*i+2)for i in range(count))),('rear','Null','Null'))


class MichelinNativePilotTests(unittest.TestCase):
    def result(self):
        return {'report':{'source_scene_sha256':p.SCENES['Car25A.PDO'],
                'body_draws':[{'mesh_id':'body-texture-000'},{'mesh_id':'body-texture-007'}]},
                'body_parts':[part(162),part(90)]}

    def test_panes_partition_source_triangles_without_moving_or_editing_paint(self):
        r=self.result();parts,panes,lamp,core=p.semantic_parts(r)
        self.assertEqual(sum(len(x.geometry.triangles)for x in parts),252)
        source={v.position:v for part_ in r['body_parts']for v in part_.geometry.vertices}
        for part_ in parts:
            for v in part_.geometry.vertices:
                original=source[v.position]
                self.assertEqual((v.position,v.normal,v.uvs),(original.position,original.normal,original.uvs))
                self.assertEqual(v.color[:3],original.color[:3])
        self.assertEqual(sum(len(parts[i].geometry.triangles)for i in panes.values()),34)
        self.assertEqual(len(parts[lamp].geometry.triangles),12)
        self.assertEqual(parts[0].geometry.vertices[0].color[3],255)
        self.assertTrue(all(v.color[3]==96 for i in panes.values()for v in parts[i].geometry.vertices))

    def test_semantics_reject_other_models_changed_topology_and_missing_lamp(self):
        for mutation in ('hash','topology','lamp'):
            r=self.result()
            if mutation=='hash':r['report']['source_scene_sha256']=p.SCENES['Car06A.PDO']
            if mutation=='topology':r['body_parts'][0]=part(163)
            if mutation=='lamp':r['report']['body_draws'][1]['mesh_id']='unknown'
            with self.assertRaises(ValueError):p.semantic_parts(r)

    def test_rear_light_mask_excludes_red_paint_and_black_outside_original_lenses(self):
        from master_rallye.addon_sdk.auto_features import feed
        pixels=bytearray(bytes((0,0,0,255))*(256*128))
        inside=60*256+48;outside=20*256+48
        for index in (inside,outside):pixels[index*4:index*4+4]=bytes((12,12,120,255))
        texture=parse_dxt_bytes(feed(pixels,256,128));lit,glow,allowed=p.lamp_maps(texture)
        self.assertEqual(allowed,[inside]);lit=parse_dxt_bytes(lit);glow=parse_dxt_bytes(glow)
        for index in range(256*128):
            if index!=inside:
                self.assertEqual(lit.bgra[index*4:index*4+4],pixels[index*4:index*4+4])
                self.assertEqual(glow.bgra[index*4:index*4+4],bytes(4))
        self.assertGreater(glow.bgra[inside*4+3],0)
        with self.assertRaises(ValueError):p.lamp_maps(parse_dxt_bytes(feed(bytes(16),2,2)))

    def test_pinned_scene_and_scale_boundary(self):
        self.assertAlmostEqual(p.SCALE*.3400000035762787,.38)
        with tempfile.TemporaryDirectory()as tmp:
            scene=Path(tmp)/'scene.json';scene.write_bytes(b'{}')
            with patch.object(p.u,'load_scene',return_value={'source':{'catalog':'Car25A.PDO'}}):
                with self.assertRaisesRegex(ValueError,'Exact accepted'):p.qualified(scene)

    def test_candidate_rejects_output_in_original_installation_or_roster_before_writes(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);source=root/'original';source.mkdir();retail=root/'retail';retail.mkdir()
            donor=retail/'DataGx/Vehicles/Forester';donor.mkdir(parents=True)
            roster=root/'roster';roster.mkdir();scene=root/'scene/scene.json';scene.parent.mkdir()
            s={'source':{'catalog':'Car25A.PDO','root':str(source)}}
            for protected in (source,roster):
                output=protected/'new-candidate'
                with patch.object(p,'qualified',return_value=s):
                    with self.assertRaisesRegex(ValueError,'overlaps protected'):
                        p.create(scene,donor,root/'retail.sma',output,retail_root=retail,base_roster=roster)
                self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
