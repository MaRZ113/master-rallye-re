from __future__ import annotations
import hashlib
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for path in (ROOT/"src",ROOT/"tests"/"blender"):
    sys.path.insert(0,str(path))
from generate_fixture import build_dx,build_dxt
from master_rallye.dx import parse_dx_bytes
from master_rallye.dx_writer import audit_binary_diff
from master_rallye.dxt import parse_dxt_bytes,encode_png
from master_rallye.r4e_writer import aggregate_corners,classify_edit,patch_dx_attributes
from master_rallye.texture_authoring import decode_rgba_png,export_texture,replace_texture
from master_rallye.vehicle_packaging import vehicle_dependencies,texture_users,bundle_vehicle,pack_sma,unpack_sma

class R4ETests(unittest.TestCase):
    def setUp(self):
        self.data=build_dx()
        self.model=parse_dx_bytes(self.data)
    def test_zero_edit_attributes(self):
        m=self.model
        patch=patch_dx_attributes(self.data,positions=m.vertices.positions,normals=m.vertices.normals,uv_sets=[x.values for x in m.uv_sets],colors=m.vertices.colors)
        self.assertEqual(patch.data,self.data)
        self.assertEqual(patch.classification,"NO_CHANGE")
    def test_uv_normal_color_patches_and_independence(self):
        m=self.model
        uv=[list(x.values) for x in m.uv_sets]
        uv[0][0]=(0.125,0)
        normals=list(m.vertices.normals); normals[0]=(0,0,1.25)
        colors=bytearray(m.vertices.colors); colors[0]^=1
        for keyword,label in ((dict(uv_sets=uv),"UV0"),(dict(normals=normals),"normal"),(dict(colors=colors),"vertex_color_raw")):
            result=patch_dx_attributes(self.data,**keyword)
            self.assertTrue(result.diff.valid)
            self.assertEqual({x.field for x in result.changes},{label})
            self.assertEqual(result.collision_sha256,patch_dx_attributes(result.data).collision_sha256)
            self.assertEqual(result.topology_sha256,patch_dx_attributes(result.data).topology_sha256)
    def test_corner_aggregation_and_seam_rejection(self):
        src=((0,0),(1,0))
        self.assertEqual(aggregate_corners([0,1,0],[(.2,.3),(1,0),(.2,.3)],src,field="UV"),((.2,.3),(1.,0.)))
        with self.assertRaisesRegex(Exception,"REQUIRES_R4F_TOPOLOGY_WRITER"):
            aggregate_corners([0,0],[(0,0),(.1,0)],src,field="UV")
        for field,values in (("normal",[(0,0,1),(0,1,0)]),("color",[(255,0,0,255),(0,0,255,255)])):
            with self.assertRaisesRegex(Exception,"REQUIRES_R4F_TOPOLOGY_WRITER"):
                aggregate_corners([0,0],values,[values[0]],field=field)
    def test_material_alpha_preserves_unknowns(self):
        result=patch_dx_attributes(self.data,material_alpha={0:True})
        self.assertEqual(result.classification,"SAFE_MATERIAL_STATE_CHANGE")
        self.assertEqual(result.diff.changed_byte_count,1)
        old=self.model.physical_draws[0]; new=parse_dx_bytes(result.data).physical_draws[0]
        self.assertEqual(old.flags_0x20[1:],new.flags_0x20[1:])
        self.assertEqual(old.unknown_0x24,new.unknown_0x24)
        self.assertEqual(old.texture_tuple,new.texture_tuple)
    def test_classification_and_binary_rejection(self):
        self.assertEqual(classify_edit(texture=True),"TEXTURE_CONTENT_ONLY")
        self.assertEqual(classify_edit(position=True,texture=True),"MULTIPLE_SAFE_CHANGES")
        self.assertEqual(classify_edit(topology_valid=False),"TOPOLOGY_CHANGED")
        data=bytearray(self.data); data[self.model.vertices.color_offset]^=1
        self.assertFalse(audit_binary_diff(self.data,data,()).valid)
    def test_dxt_png_orientation_and_replacement(self):
        original=build_dxt(((255,0,0,255),(255,0,0,255)),((0,0,255,128),(0,0,255,128)))
        texture=parse_dxt_bytes(original)
        w,h,rgba=decode_rgba_png(encode_png(texture))
        self.assertEqual((w,h),(2,2))
        self.assertEqual(tuple(rgba[:4]),(255,0,0,255))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"source.dxt"; png=root/"edit.png"; output=root/"out.dxt"
            source.write_bytes(original)
            export_texture(source,png)
            result=replace_texture(source,png,output,expected_source_sha256=hashlib.sha256(original).hexdigest())
            self.assertEqual(output.read_bytes(),original)
            self.assertTrue(result["same_header"])
    def test_dependencies_bundle_and_sma(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); vehicle=root/"Astero"; vehicle.mkdir()
            (vehicle/"car.dx").write_bytes(self.data)
            for name in ("synthetic-top-tga.dxt","synthetic-bottom-tga.dxt"):
                (vehicle/name).write_bytes(build_dxt(((255,0,0,255),(255,0,0,255)),((0,0,255,128),(0,0,255,128))))
            dependencies=vehicle_dependencies(vehicle)
            self.assertEqual(dependencies["unresolved_count"],0)
            self.assertEqual(texture_users(vehicle,"synthetic-top-tga.dxt")["count"],1)
            replacement=root/"modified.dx"
            replacement.write_bytes(patch_dx_attributes(self.data,material_alpha={0:True}).data)
            stage=root/"stage"
            bundle=bundle_vehicle(vehicle,{"car.dx":replacement},stage)
            self.assertEqual(bundle["files"][0]["status"],"modified")
            bad_replacement=root/"bad.dx"
            changed=bytearray(self.data); changed[4]^=1
            bad_replacement.write_bytes(changed)
            with self.assertRaises(Exception):
                bundle_vehicle(vehicle,{"car.dx":bad_replacement},root/"bad_stage")
            archive=root/"out.sma"; info=pack_sma(stage,archive)
            self.assertEqual(info["status"],"STRUCTURALLY_VALID")
            unpack=root/"unpack";unpack_sma(archive,unpack)
            self.assertEqual((unpack/"DataGx"/"Vehicles"/"Astero"/"car.dx").read_bytes(),replacement.read_bytes())
            with self.assertRaisesRegex(ValueError,"overwrite"):
                pack_sma(stage,archive)
            bad=root/"bad"; (bad/"extra"/"DataGx").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,"root"):
                pack_sma(bad,root/"bad.sma")
if __name__=="__main__":
    unittest.main()
