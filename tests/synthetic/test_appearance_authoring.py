import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from PIL import Image
from tests.synthetic.test_workshop import family
from master_rallye.workshop.service import WorkshopProject,sha
from master_rallye.paint_authoring import masked_paint
from master_rallye.crew_authoring import apply_crew_fit
from master_rallye.dx import parse_dx_bytes


class AppearanceTests(unittest.TestCase):
    def prepare(self,r,addon=False):
        family(r/'source')
        from tests.synthetic.test_library import synthetic_dx,simple_record,footer56
        points=[(0.,.2,.2),(.2,.8,.2),(.8,.2,.2),(-1.,-1.,-1.),(2.,0.,0.),(0.,2.,2.)]
        records=[bytearray(simple_record(i,2,i,3,('base-tga','Null','Null')))for i in (0,3)]
        for record in records:record[32:36]=bytes([0,0,1,1]);struct.pack_into('<I',record,36,3)
        raw=synthetic_dx(points,[0,1,2,0,1,2],records,[(0,0,3),(3,3,3)],trailing=footer56(points))
        for n in ('car.dx','complete.dx','wheel.dx'):(r/'source'/n).write_bytes(raw)
        if addon:
            (r/'author').mkdir();(r/'author/addon.json').write_text(json.dumps({'addon_id':'appearance-test'}))
            (r/'author/vehicle-project.json').write_text(json.dumps({'vehicle_name':'source','source_vehicle_dir':str(r/'source'),'resources':{}}))
        return WorkshopProject.create(r/('author'if addon else'source'),r/'project')

    def mask(self,r):
        m=Image.new('RGB',(2,2));m.putpixel((0,0),(255,255,255));m.save(r/'mask.png');return r/'mask.png'

    def definition(self,p):
        raw=(p.baseline/'car.dx').read_bytes()
        return {'model_sha256':sha(raw),'evidence':'Synthetic independent draw; exact original vertex IDs','people':{'driver':{'vertices':[0,1,2],'draws':[0],'pivot':[0,0,0],'role':'test crew'}},'envelope':[[-2,-2,-2],[2,2,2]]}

    def test_mask_protects_pixels_alpha_and_orientation(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);raw=(p.baseline/'base-tga.dxt').read_bytes();mask=self.mask(r).read_bytes()
            out,audit=masked_paint(raw,mask,[220,10,15],source_sha256=sha(raw),evidence='Upper left texel is qualified paint, all other texels protected')
            self.assertEqual(out[20:28],raw[20:28]);self.assertNotEqual(out[28:31],raw[28:31]);self.assertEqual(out[31:],raw[31:]);self.assertTrue(audit['alpha_preserved'])
            for color in ([True,1,2],[256,0,0],[0,0]):
                with self.assertRaises(ValueError):masked_paint(raw,mask,color,source_sha256=sha(raw),evidence='Qualified pixel ownership')
            with self.assertRaises(ValueError):masked_paint(raw,mask,[1,2,3],source_sha256='0'*64,evidence='Qualified pixel ownership')

    def test_mask_rejects_ambiguous_alpha_color_size_and_empty(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);raw=(p.baseline/'base-tga.dxt').read_bytes()
            for mode,size,color in [('RGB',(1,1),'white'),('RGBA',(2,2),(255,255,255,100)),('RGB',(2,2),'red'),('RGB',(2,2),'black')]:
                Image.new(mode,size,color).save(r/'mask.png')
                with self.assertRaises(ValueError):masked_paint(raw,(r/'mask.png').read_bytes(),[1,2,3],source_sha256=sha(raw),evidence='Qualified pixel ownership')

    def test_profiles_reopen_undo_redo_and_build_core(self):
        from master_rallye.vehicle_project import VehicleProject,validate_vehicle
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r,True);mask=self.mask(r);base=(p.assets/'base-tga.dxt').read_bytes()
            p.register_paint_region('panel','base-tga.dxt',mask,'Isolated qualified upper left paint pixel; remaining pixels protected')
            p.switch_appearance('Custom');p.paint_region('panel',[200,20,30]);paint=(p.assets/'base-tga.dxt').read_bytes()
            p.save_color_preset('Mine',[200,20,30]);p.switch_appearance('Source Fidelity');self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),base)
            p.switch_appearance('Classic MR Style');p.tint('base-tga.dxt',[1,.5,.2]);classic=(p.assets/'base-tga.dxt').read_bytes()
            p.switch_appearance('Custom');self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),paint)
            p.undo();self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),classic);p.redo();self.assertEqual((p.assets/'base-tga.dxt').read_bytes(),paint)
            q=WorkshopProject(p.root);q.materialize();self.assertEqual(q.data['appearance'],'Custom');self.assertEqual(q.data['color_presets']['Mine'],[200,20,30])
            compiled=validate_vehicle(VehicleProject.load(q.working/'vehicle-project.json'));self.assertEqual(compiled['compiled']['base-tga.dxt'],paint)
            q.restore();self.assertEqual((q.assets/'base-tga.dxt').read_bytes(),base)

    def test_crew_rigid_scope_core_compile_and_restore(self):
        from master_rallye.vehicle_project import VehicleProject,validate_vehicle
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r,True);base=(p.assets/'car.dx').read_bytes();d=self.definition(p)
            p.register_crew('car.dx',d);self.assertEqual((p.assets/'car.dx').read_bytes(),base)
            p.fit_crew('car.dx','driver',{'lateral':-.1,'vertical':.1,'longitudinal':0,'yaw_degrees':5})
            out=(p.assets/'car.dx').read_bytes();self.assertNotEqual(out,base)
            a,b=map(parse_dx_bytes,(base,out));self.assertEqual(a.local_indices,b.local_indices);self.assertEqual(a.vertices.colors,b.vertices.colors);self.assertEqual(a.uv_sets,b.uv_sets);self.assertEqual(a.physical_draws,b.physical_draws)
            p.edit_surface('car.dx',0,rgb=[.3,.4,.5])
            compiled=validate_vehicle(VehicleProject.load(p.working/'vehicle-project.json'));self.assertEqual(compiled['compiled']['car.dx'],(p.assets/'car.dx').read_bytes())
            q=WorkshopProject(p.root);q.materialize();self.assertEqual((q.assets/'car.dx').read_bytes(),(p.assets/'car.dx').read_bytes());q.restore();self.assertEqual((q.assets/'car.dx').read_bytes(),base)

    def test_crew_invalid_hash_selectors_ranges_and_shared(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);base=(p.assets/'car.dx').read_bytes();d=self.definition(p)
            for placement in ({'lateral':.6,'vertical':0,'longitudinal':0,'yaw_degrees':0},{'lateral':0,'vertical':0,'longitudinal':0,'yaw_degrees':float('nan')}):
                with self.assertRaises(ValueError):apply_crew_fit(base,d,{'driver':placement},source_sha256=sha(base))
            d['people']['driver']['vertices']=[999]
            with self.assertRaises(ValueError):p.register_crew('car.dx',d)
            d=self.definition(p);d['model_sha256']='0'*64
            with self.assertRaises(ValueError):p.register_crew('car.dx',d)

    def test_stock_catalogue_transfer_alpha_and_shared_ownership(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);family(r/'stock');rows=p.stock_materials(r/'stock');ref=rows[0]['textures'][0]
            with self.assertRaisesRegex(ValueError,'Shared'):p.use_stock_texture('car.dx',0,0,ref)
            p.use_stock_texture('car.dx',0,0,ref,allow_shared=True)
            self.assertEqual(p.data['edits']['base-tga.dxt']['operation'],'local-stock-reference')
            (r/'stock/base-tga.dxt').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'changed'):p.use_stock_texture('car.dx',0,0,ref,allow_shared=True)

    def test_mask_metadata_cannot_retarget_saved_recipes(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);mask=self.mask(r);p.register_paint_region('panel','base-tga.dxt',mask,'Qualified paint pixel; other texels protected')
            Image.new('RGBA',(2,2),'white').save(mask)
            with self.assertRaisesRegex(ValueError,'new region'):p.register_paint_region('panel','base-tga.dxt',mask,'Qualified paint pixel; other texels protected')

    def test_material_replacement_and_paint_are_not_silently_composed(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);mask=self.mask(r);p.register_paint_region('panel','base-tga.dxt',mask,'Qualified paint pixel; other texels protected');p.tint('base-tga.dxt',[.2,.4,.6])
            with self.assertRaisesRegex(ValueError,'Restore'):p.paint_region('panel',[10,20,30])

    def test_mechanical_rebase_accepts_only_unrelated_attributes(self):
        from master_rallye.addon_sdk.visual_fitment import rebase_unchanged_mechanics
        from master_rallye.surface_authoring import apply_surface_edits
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);raw=(p.assets/'car.dx').read_bytes()
            definition={'profile_version':1,'source_sha256':sha(raw),'provenance':'Qualified synthetic isolated mechanics','groups':[{'name':'disc','draw_indices':[1],'source_hub_m':[0,0,0],'target_hub_m':[0,0,0],'provenance':'Synthetic unchanged disc'}]}
            after=apply_surface_edits(raw,[{'draw_id':0,'rgb':[.2,.3,.4]}],source_sha256=sha(raw)).data
            result=rebase_unchanged_mechanics(raw,after,definition);self.assertEqual(result['source_sha256'],sha(after));self.assertEqual(result['groups'],definition['groups'])
            changed=apply_surface_edits(raw,[{'draw_id':1,'rgb':[.2,.3,.4]}],source_sha256=sha(raw)).data
            with self.assertRaisesRegex(ValueError,'selected vertex'):rebase_unchanged_mechanics(raw,changed,definition)

    def test_shadow_rebase_preserves_bounds_footprint_and_parameters(self):
        from master_rallye.addon_sdk.vehicle_shadow import rebase_unchanged_footprint,generate_profile
        from master_rallye.surface_authoring import apply_surface_edits
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);raw=(p.assets/'car.dx').read_bytes();texture=(p.assets/'base-tga.dxt').read_bytes();profile=generate_profile(raw,texture,'Synthetic')
            after=apply_surface_edits(raw,[{'draw_id':0,'rgb':[.2,.3,.4]}],source_sha256=sha(raw)).data
            result=rebase_unchanged_footprint(raw,after,profile);self.assertEqual({k:v for k,v in result.items()if k!='source_model_sha256'},{k:v for k,v in profile.items()if k!='source_model_sha256'})
            from master_rallye.r4e_writer import patch_dx_attributes
            m=parse_dx_bytes(raw);changed=bytearray(raw);struct.pack_into('<3f',changed,m.vertices.position_offset+4*m.vertices.position_stride,1.9,0,0);changed=bytes(changed)
            with self.assertRaisesRegex(ValueError,'footprint'):rebase_unchanged_footprint(raw,changed,profile)

    def test_exact_conversion_report_qualifies_crew_and_rejects_revision_drift(self):
        from master_rallye.crew_authoring import qualify_converted_crew
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);raw=(p.assets/'car.dx').read_bytes();m=parse_dx_bytes(raw);ids=[0,1,2]
            box=[[f(m.vertices.positions[i][k]for i in ids)for k in range(3)]for f in(min,max)]
            report={'outputs':{'car.dx':{'sha256':sha(raw)}},'conversion':{'car.dx':[{'component':'crew','route':'MR stock crew','rigid_fit':True,'vertices':3,'triangles':1,'textures':['base-tga','Null','Null'],'bbox':box,'person_bbox':box,'person':'driver','role':'helmet','source_draw':17,'source_sha256':'1'*64}]}}
            definition=qualify_converted_crew(raw,report,'car.dx');self.assertEqual(definition['people']['driver']['vertices'],ids);self.assertEqual(definition['people']['driver']['components'][0]['role'],'helmet')
            report['outputs']['car.dx']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'revision'):qualify_converted_crew(raw,report,'car.dx')

    def test_mask_drift_fails_project_reopen_materialization(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);mask=self.mask(r);p.register_paint_region('panel','base-tga.dxt',mask,'Qualified paint pixel; other texels protected')
            region=p.data['paint_regions']['panel'];(p.root/'paint-masks'/(region['mask_sha256']+'.png')).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'mask changed'):WorkshopProject(p.root).materialize()

    def test_crew_batch_rejects_invalid_second_model_atomically(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r);d=self.definition(p);invalid={**d,'model_sha256':'0'*64};state=p._state()
            with self.assertRaises(ValueError):p.register_crew_models({'car.dx':d,'complete.dx':invalid})
            self.assertEqual(p._state(),state)

    def test_invisible_decal_mask_is_not_qualified_as_visible_paint(self):
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);p=self.prepare(r)
            for name in ('car.dx','complete.dx','wheel.dx'):
                path=r/'source'/name;raw=bytearray(path.read_bytes());m=parse_dx_bytes(raw)
                for d in m.physical_draws:raw[d.core_offset+32]=1
                path.write_bytes(raw)
            q=WorkshopProject.create(r/'source',r/'overlay');mask=self.mask(r)
            with self.assertRaisesRegex(ValueError,'invisible alpha'):q.register_paint_region('bad','base-tga.dxt',mask,'Qualified candidate mask is actually invisible in this decal overlay')

    def test_project_publication_retries_sharing_lock_without_overwriting(self):
        import os
        from unittest.mock import patch
        from master_rallye.addon_sdk.project import _publish_new_project
        with tempfile.TemporaryDirectory()as td:
            r=Path(td);source=r/'stage';source.mkdir();(source/'text.txt').write_text('source');dest=r/'project'
            original=os.replace;calls=[];error=PermissionError('simulated Windows sharing lock');error.winerror=32
            def replace(a,b):
                calls.append(1)
                if len(calls)<3:raise error
                original(a,b)
            with patch('master_rallye.addon_sdk.project.os.name','nt'),patch('master_rallye.addon_sdk.project.os.replace',side_effect=replace),patch('time.sleep'):_publish_new_project(source,dest)
            self.assertEqual(len(calls),3);self.assertEqual((dest/'text.txt').read_text(),'source')
            source.mkdir()
            with self.assertRaises(FileExistsError):_publish_new_project(source,dest)
