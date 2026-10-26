import copy,json,math,struct,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.classic_geometry import simplify_radial_cover
from master_rallye.classic_style import paint_texture,digest
from master_rallye.workshop.classic import approve_classic,require_classic_approval,source_project,_transfer_layers
from master_rallye.workshop.service import WorkshopProject,write_json
from tests.synthetic.test_workshop import family


def cover():
    n=16;v=[CompiledVertex((0,0,.02),(0,0,1),bytes([255]*4),((.5,.5),))]
    for r,z in ((.09,.015),(.1,0)):
        for j in range(n):
            a=j*2*math.pi/n;x,y=r*math.cos(a),r*math.sin(a)
            v.append(CompiledVertex((x,y,z),(0,0,1),bytes([255]*4),((.5+x*4,.5+y*4),)))
    ts=[]
    for j in range(n):
        k=(j+1)%n;ts.extend([(0,1+j,1+k),(1+j,17+j,17+k),(1+j,17+k,1+k)])
    return DrawGeometry(tuple(v),tuple(ts))


class ClassicTests(unittest.TestCase):
    def test_cover_keeps_exact_contour_center_and_winding(self):
        old=cover();new,r=simplify_radial_cover(old)
        self.assertEqual((r['triangles_before'],r['triangles_after']),(48,16))
        self.assertEqual(new.vertices[0],old.vertices[0]);self.assertEqual(set(new.vertices[1:]),set(old.vertices[17:]));self.assertTrue(r['boundary_preserved'])

    def test_cover_rejects_nonradial_uv_seams_and_large_relief(self):
        old=cover();v=list(old.vertices);v[0]=replace(v[0],position=(0,0,.1))
        with self.assertRaisesRegex(ValueError,'relief'):simplify_radial_cover(DrawGeometry(tuple(v),old.triangles))
        v=list(old.vertices);v[2]=replace(v[2],uvs=((.01,.03),))
        with self.assertRaisesRegex(ValueError,'UV'):simplify_radial_cover(DrawGeometry(tuple(v),old.triangles))
        with self.assertRaises(ValueError):simplify_radial_cover(old,expected_boundary=12)
        with self.assertRaises(ValueError):simplify_radial_cover(DrawGeometry(old.vertices,old.triangles[:-1]))

    def test_duplicate_identical_strip_vertices_weld_without_attribute_loss(self):
        old=cover();v=old.vertices+old.vertices;ts=tuple(tuple(i+len(old.vertices)for i in t)if j%2 else t for j,t in enumerate(old.triangles))
        a,_=simplify_radial_cover(old);b,_=simplify_radial_cover(DrawGeometry(v,ts));self.assertEqual(a,b)

    def test_paint_regenerates_rgb_preserves_cutout_alpha_and_protected_pixels(self):
        with tempfile.TemporaryDirectory()as td:
            raw=family(Path(td)/'family');rule={'source_sha256':digest(raw),'rectangles':[[0,0,1,1]],'base_rgb':[220,20,30],'opaque_size':[1,1],'paint_reflection_alpha':255}
            outputs,audit=paint_texture(raw,rule)
            from master_rallye.dxt import parse_dxt_bytes
            a,b=parse_dxt_bytes(raw),parse_dxt_bytes(outputs['cutout']);self.assertEqual(a.bgra[3::4],b.bgra[3::4]);self.assertEqual(a.bgra[:8],b.bgra[:8]);self.assertNotEqual(a.bgra[8:11],b.bgra[8:11]);self.assertEqual(a.bgra[12:],b.bgra[12:]);self.assertEqual(parse_dxt_bytes(outputs['opaque']).width,1)
            with self.assertRaises(ValueError):paint_texture(raw,{**rule,'source_sha256':'0'*64})
            with self.assertRaises(ValueError):paint_texture(raw,{**rule,'rectangles':[[0,0,3,1]]})
            for bad in ({'base_rgb':[300,0,0]},{'base_rgb':[True,0,0]},{'paint_reflection_alpha':300},{'opaque_size':[16384,16384]},{'opaque_size':[3,2]},{'rectangles':[[0.,0,1,1]]}):
                with self.assertRaises(ValueError):paint_texture(raw,{**rule,**bad})

    def test_characteristic_graphics_are_explicit_and_clipped_to_paint_mask(self):
        with tempfile.TemporaryDirectory()as td:
            from master_rallye.dxt import parse_dxt_bytes
            raw=family(Path(td)/'family');rule={'source_sha256':digest(raw),'rectangles':[[0,0,1,1]],'base_rgb':[220]*3,'opaque_size':[2,2],'paint_reflection_alpha':255,'graphics':[{'name':'red field','rgb':[168,28,20],'polygon':[[0,0],[2,0],[2,2],[0,2]]}]}
            outputs,audit=paint_texture(raw,rule);t=parse_dxt_bytes(outputs['cutout']);self.assertEqual(t.bgra[:8],raw[20:28]);self.assertEqual(t.bgra[8:11],bytes([20,28,168]));self.assertEqual(t.bgra[12:],raw[32:]);self.assertEqual(audit['graphics'][0]['name'],'red field')

    def test_conversion_refuses_unknown_source_before_any_mutation(self):
        from master_rallye.classic_style import convert
        r={'version':1,'source_models':{'car.dx':'0'*64}};resources={'car.dx':b'unchanged'}
        with self.assertRaisesRegex(ValueError,'immutable'):convert(resources,r,b'',b'')
        self.assertEqual(resources,{'car.dx':b'unchanged'})

    def test_report_approval_exact_hash_and_persistent_build_gate(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);family(r/'f');p=WorkshopProject.create(r/'f',r/'p');report=r/'report.json';report.write_text('{}');h=digest(report.read_bytes())
            p.data['classic_generation']={'report':str(report),'report_sha256':h,'approved_report_sha256':None,'version_style':'Classic MR Style','source_root':str(r/'source')};p.save()
            with self.assertRaisesRegex(ValueError,'blocked'):p.build(r/'build',sdk_root=r)
            self.assertFalse((r/'build').exists())
            with self.assertRaises(ValueError):approve_classic(p,'0'*64)
            approve_classic(p,h);require_classic_approval(WorkshopProject(p.root));report.write_text('{"changed":1}')
            with self.assertRaises(ValueError):require_classic_approval(p)

    def test_source_resolution_never_decimates_a_previous_classic(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);family(r/'f');source=WorkshopProject.create(r/'f',r/'source');one=WorkshopProject.create(r/'f',r/'one');two=WorkshopProject.create(r/'f',r/'two')
            one.data['classic_generation']={'source_root':str(source.root)};one.save();two.data['classic_generation']={'source_root':str(one.root)};two.save();self.assertEqual(source_project(two).root,source.root)
            one.data['classic_generation']['source_root']=str(two.root);one.save()
            with self.assertRaisesRegex(ValueError,'cycle'):source_project(two)

    def test_manual_compatible_layers_reopen_undo_restore_and_conflicts(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);family(r/'f');a=WorkshopProject.create(r/'f',r/'a');b=WorkshopProject.create(r/'f',r/'b')
            a.tint('base-tga.dxt',[.5,1,1]);a.edit_surface('car.dx',0,rgb=[.5,1,1]);result=_transfer_layers(a,b,{})
            self.assertEqual(len(result['applied']),2);self.assertFalse(result['conflicts']);before=(b.assets/'car.dx').read_bytes()
            q=WorkshopProject(b.root);q.materialize();self.assertEqual((q.assets/'car.dx').read_bytes(),before)
            q.restore();q.undo();self.assertEqual((q.assets/'car.dx').read_bytes(),before)
            c=WorkshopProject.create(r/'f',r/'c');c.data['inputs']['base-tga.dxt']='0'*64
            # Conflict classification itself remains conservative; verify_inputs
            # prevents a changed baseline from being materialized afterwards.
            with self.assertRaisesRegex(ValueError,'baseline changed'):_transfer_layers(a,c,{})


if __name__=='__main__':unittest.main()
