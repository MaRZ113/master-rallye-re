"""Synthetic topology writer and deterministic corner compiler tests."""
import struct
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import CompiledVertex, DrawGeometry, rebuild_topology, source_geometry
from master_rallye.vertex_compiler import CornerInput, FaceInput, compile_faces
from tests.helpers.collision_fixture import tag101


def fixture(*, grouped=False, collision=False):
    points = ((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.),
              (0.,0.,1.),(1.,0.,1.),(0.,1.,1.))
    out = bytearray(struct.pack("<4I", 0xD00D, 135, 1337, len(points)))
    for point in points: out += struct.pack("<3f", *point)
    for _ in points: out += struct.pack("<3f", 0., 0., 1.)
    out += bytes((255,255,255,255)) * len(points)
    out += struct.pack("<I", 1)
    for point in points: out += struct.pack("<2f", point[0], point[1])
    local = (1,0,2, 2,0,3, 1,0,2)
    out += struct.pack("<I",len(local)) + struct.pack("<9H",*local)
    out += struct.pack("<2I",1,1 if grouped else 2)
    for record_index,(base, maximum, start, count, name) in enumerate(((0,3,0,6,"body"),(4,2,6,3,"glass"))):
        if grouped and record_index==0:
            out += struct.pack("<I",7)
            label=b"breakable";out += struct.pack("<I",len(label))+label
            out += struct.pack("<5I",2,2,8,1,1)
        elif grouped:
            out += struct.pack("<3I",8,2,1)
        out += struct.pack("<10I",2,base,maximum,start,count,0xDEADBEEF,0,0,0,7)
        out += struct.pack("<I",3)
        for slot in (name,"Null","Null"):
            raw=slot.encode("ascii");out += struct.pack("<I",len(raw))+raw
        out += struct.pack("<I",0)
    global_indices=(0,1,2, 0,2,3, 4,5,6)
    out += struct.pack("<2I",1,len(global_indices))+struct.pack("<9I",*global_indices)
    if collision: out += tag101()
    out += struct.pack("<I4f6f",1339,.5,.5,.5,1.,0.,0.,0.,1.,1.,1.)
    return bytes(out)


def faces_from_model(model):
    result=[]
    for draw in model.physical_draws:
        indices=model.draw_global_indices(draw)
        for at in range(0,len(indices),3):
            corners=[]
            for source_id in indices[at:at+3]:
                corners.append(CornerInput(
                    source_id,model.vertices.positions[source_id],model.vertices.normals[source_id],
                    model.vertices.colors[source_id*4:source_id*4+4],
                    tuple(layer.values[source_id] for layer in model.uv_sets),source_id,
                ))
            result.append(FaceInput(tuple(corners),draw.draw_index,draw.draw_index,
                                    draw.index_start//3+at//3,True))
    return result


class R4FTests(unittest.TestCase):
    def setUp(self):
        self.data=fixture()
        self.model=parse_dx_bytes(self.data)
        self.assertTrue(self.model.diagnostics.validated)
        self.geometries=source_geometry(self.model)

    def test_zero_rebuild_identity_and_preserved_suffix(self):
        result=rebuild_topology(self.data)
        self.assertEqual(result.data,self.data)
        self.assertTrue(result.semantic_equivalent)
        self.assertEqual(result.external_diff_count,0)

    def test_add_vertex_triangle_and_shift_downstream_bases(self):
        first=self.geometries[0]
        new=tuple(replace(vertex,position=(vertex.position[0],vertex.position[1],.1),source_vertex_id=None,
                          parent_source_vertex_id=vertex.source_vertex_id) for vertex in first.vertices[:3])
        edit=DrawGeometry(first.vertices+new,first.triangles+((4,5,6),))
        rebuilt=rebuild_topology(self.data,{0:edit})
        parsed=rebuilt.output_model
        self.assertEqual((parsed.vertex_count,parsed.triangle_count),(10,4))
        self.assertEqual((parsed.physical_draws[1].vertex_base,parsed.physical_draws[1].index_start),(7,9))
        self.assertEqual(parsed.global_index_table.indices[-3:],(7,8,9))
        self.assertEqual(parsed.draw_global_indices(parsed.physical_draws[0])[-3:],(4,5,6))
        self.assertEqual(rebuilt.data[parsed.trailing.offset:],self.data[self.model.trailing.offset:])
        self.assertEqual(rebuilt.external_diff_count,0)

    def test_add_one_referenced_vertex_and_remove_triangle_and_vertex(self):
        first=self.geometries[0]
        extra=replace(first.vertices[0],source_vertex_id=None,position=(.2,.2,.2))
        with self.assertRaisesRegex(Exception,"unreferenced compiled"):
            rebuild_topology(self.data,{0:DrawGeometry(first.vertices+(extra,),first.triangles)})
        add_triangles=((0,1,4),(1,2,4),(2,0,4),first.triangles[1])
        add=rebuild_topology(self.data,{0:DrawGeometry(first.vertices+(extra,),add_triangles)})
        self.assertEqual(add.output_vertex_count,self.model.vertex_count+1)
        self.assertEqual(add.output_triangle_count,self.model.triangle_count+2)
        reduced=DrawGeometry(first.vertices[:3],first.triangles[:1])
        remove=rebuild_topology(self.data,{0:reduced})
        self.assertEqual((remove.output_vertex_count,remove.output_triangle_count),(6,2))
        self.assertEqual((remove.output_model.physical_draws[1].vertex_base,remove.output_model.physical_draws[1].index_start),(3,3))

    def test_compiler_seams_and_determinism(self):
        original=faces_from_model(self.model)
        base,report=compile_faces(self.model,original,{0:(0,),1:(1,)})
        self.assertEqual((report.compiled_vertex_count,report.compiled_triangle_count),(7,3))
        self.assertEqual(base[0].triangles,self.geometries[0].triangles)
        for field in ("uv","normal","color"):
            faces=list(original)
            corner=faces[1].corners[0]
            if field=="uv":corner=replace(corner,uvs=((.25,.25),))
            elif field=="normal":corner=replace(corner,normal=(0.,1.,0.))
            else:corner=replace(corner,color=bytes((2,3,4,255)))
            faces[1]=replace(faces[1],corners=(corner,)+faces[1].corners[1:])
            compiled,diagnostics=compile_faces(self.model,faces,{0:(0,),1:(1,)})
            self.assertEqual(diagnostics.compiled_vertex_count,8)
            self.assertEqual((compiled,diagnostics),compile_faces(self.model,faces,{0:(0,),1:(1,)}))
            self.assertEqual(getattr(diagnostics,{"uv":"split_for_uv_seam","normal":"split_for_normal_discontinuity","color":"split_for_vertex_color_discontinuity"}[field]),1)
            self.assertTrue(rebuild_topology(self.data,compiled).output_model.diagnostics.validated)

    def test_same_count_triangle_rewire_is_reported(self):
        faces=faces_from_model(self.model)
        reordered=replace(faces[0],corners=(faces[0].corners[1],faces[0].corners[0],faces[0].corners[2]))
        _,report=compile_faces(self.model,[reordered]+faces[1:],{0:(0,),1:(1,)})
        self.assertIn(0,report.changed_draws)
        self.assertEqual(report.compiled_triangle_count,self.model.triangle_count)

    def test_draw_boundary_split_and_assignment_rules(self):
        faces=faces_from_model(self.model)
        other=replace(faces[2].corners[0],blender_vertex_id=0)
        faces[2]=replace(faces[2],corners=(other,)+faces[2].corners[1:])
        _,diagnostics=compile_faces(self.model,faces,{0:(0,),1:(1,)})
        self.assertEqual(diagnostics.split_for_draw_boundary,1)
        fresh=replace(faces[0],draw_id=None,source_triangle_id=None,assignment_explicit=False)
        inferred=compile_faces(self.model,[fresh]+faces[1:],{0:(0,),1:(1,)})[1]
        self.assertEqual(inferred.inferred_face_draw_count,1)
        with self.assertRaisesRegex(Exception,"unique existing MR draw"):
            compile_faces(self.model,[fresh]+faces[1:],{0:(0,1),1:(1,)})
        with self.assertRaisesRegex(Exception,"invalid existing draw"):
            compile_faces(self.model,[replace(fresh,draw_id=99,assignment_explicit=True)]+faces[1:],{})
        duplicate=replace(faces[1].corners[0],blender_vertex_id=999)
        with self.assertRaisesRegex(Exception,"claimed by multiple Blender points"):
            compile_faces(self.model,[faces[0],replace(faces[1],corners=(duplicate,)+faces[1].corners[1:]),faces[2]],{})

    def test_group_hierarchy_unknown_flags_and_collision_preserved(self):
        data=fixture(grouped=True,collision=True)
        model=parse_dx_bytes(data)
        self.assertEqual(model.record_tags,[7,8])
        self.assertIsNotNone(model.collision.convex_hull)
        first=source_geometry(model)[0]
        generated=replace(first.vertices[0],position=(.2,.2,.2),source_vertex_id=None)
        rebuilt=rebuild_topology(data,{0:DrawGeometry(first.vertices+(generated,),first.triangles+((0,1,4),))})
        after=rebuilt.output_model
        self.assertEqual(after.record_tags,[7,8])
        self.assertEqual(after.physical_draws[0].group_label,"breakable")
        self.assertEqual(after.physical_draws[0].control_words,(2,2,8,1,1))
        self.assertEqual(after.physical_draws[0].unknown_0x14,0xDEADBEEF)
        self.assertEqual(after.physical_draws[0].unknown_0x24,7)
        self.assertEqual(after.collision.convex_hull.raw,model.collision.convex_hull.raw)
        self.assertEqual(after.physical_draws[1].vertex_base,5)
        self.assertEqual(rebuilt.external_diff_count,0)

    def test_rejections(self):
        faces=faces_from_model(self.model)
        with self.assertRaisesRegex(Exception,"triangulate"):
            compile_faces(self.model,[replace(faces[0],corners=faces[0].corners[:2])]+faces[1:],{})
        bad=replace(faces[0].corners[0],position=(float("nan"),0.,0.))
        with self.assertRaisesRegex(Exception,"finite"):
            compile_faces(self.model,[replace(faces[0],corners=(bad,)+faces[0].corners[1:])]+faces[1:],{})
        first=self.geometries[0]
        with self.assertRaisesRegex(Exception,"bounds"):
            rebuild_topology(self.data,{0:DrawGeometry(first.vertices+(replace(first.vertices[0],position=(2.,0.,0.),source_vertex_id=None),),first.triangles)})
        with self.assertRaisesRegex(Exception,"capacity"):
            rebuild_topology(self.data,{0:DrawGeometry(first.vertices*16385,first.triangles)})


if __name__ == "__main__":
    unittest.main()
