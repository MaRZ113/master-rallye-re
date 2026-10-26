import copy
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from master_rallye.workshop.shadow import ShadowAuthoring
from master_rallye.shadow_preview import shadow_guides
from master_rallye.classic_materials import apply_materials, references
from master_rallye.classic_style import prepare_paint
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.r4e_writer import patch_dx_attributes
from master_rallye.workshop.ui_actions import ICONS,action_name
from tests.synthetic.test_vehicle_shadow import fixture
from tests.synthetic.test_library import synthetic_dx,simple_record,footer56


def sha(raw):return hashlib.sha256(raw).hexdigest()
def texture(pixels):return struct.pack('<5I',0xfeed,1,0,2,2)+b''.join(bytes(v) for v in pixels)
def mesh(alpha,env=False):
    p=[(-1.,0.,-1.),(1.,0.,-1.),(0.,1.,1.)]
    r=bytearray(simple_record(0,2,0,3,('base','reflection'if env else'Null','Null')))
    r[32:36]=bytes([alpha,0,1,1]);struct.pack_into('<I',r,36,7 if env else 3)
    raw=synthetic_dx(p,[0,1,2],[r],[(0,0,3)],trailing=footer56(p))
    return patch_dx_attributes(raw,colors=bytes([171,171,171,255])*3).data


class Harness(ShadowAuthoring):
    def __init__(self,root):
        self.root=root;self.working=root;self.data={'kind':'addon','history':[]}
        (root/'addon.json').write_text(json.dumps({'identity':{'runtime_family':'Fixture'}}))
        self.model,self.texture=fixture()
    def save(self):pass
    def _record(self):self.data['history'].append(copy.deepcopy(self.data.get('shadow')))
    def materialize(self):self.shadow_materialize()
    def shadow_sources(self):return self.model,self.texture


class FidelityTests(unittest.TestCase):
    def test_shadow_modes_do_not_mutate_model_or_shared_texture(self):
        with tempfile.TemporaryDirectory()as td:
            h=Harness(Path(td));before=(h.model,h.texture)
            self.assertFalse(h.shadow_calculate()['enabled'])
            a=h.shadow_update('auto');self.assertTrue(a['enabled'])
            h.shadow_update('custom',scale_x=.6,scale_z=.7,offset_x_m=.2)
            self.assertNotEqual(h.shadow_calculate()['generated_alpha_support_xz_m'],a['generated_alpha_support_xz_m'])
            h.shadow_reset('original');self.assertFalse((h.root/'shadow-profile.json').exists())
            self.assertEqual(before,(h.model,h.texture));self.assertEqual(len(h.data['history']),3)
            for kwargs in ({'scale_x':float('nan')},{'alpha_threshold':True},{'margin_x_m':-1},{'scale_z':3},{'fake':1}):
                with self.assertRaises(ValueError):h.shadow_update('custom',**kwargs)

    def test_shadow_donor_reset_and_profile_validation(self):
        from master_rallye.addon_sdk.vehicle_shadow import generate_profile
        with tempfile.TemporaryDirectory()as td:
            h=Harness(Path(td));profile=generate_profile(h.model,h.texture,'Fixture',scale_z=.8)
            (h.root/'shadow-profile.json').write_text(json.dumps(profile));h.shadow_state()
            self.assertEqual(h.shadow_calculate()['profile']['scale_z'],.8)
            h.shadow_update('auto');self.assertEqual(h.shadow_calculate()['profile']['scale_z'],1.)
            h.shadow_reset();self.assertEqual(h.shadow_calculate()['profile']['scale_z'],.8)
            h.data['shadow_baseline']['runtime_family']='Other'
            with self.assertRaises(ValueError):h.shadow_calculate()
            h.data['kind']='stock'
            with self.assertRaises(ValueError):h.shadow_state()

    def test_shadow_guides_are_bounded_preview_only(self):
        with tempfile.TemporaryDirectory()as td:
            h=Harness(Path(td));report=h.shadow_debug_profile();draws=shadow_guides(report,-.1)
            self.assertEqual(sum(d[0].startswith('diagnostic:shadow:')for d in draws),12)
            self.assertTrue(all(d[1]==1 for d in draws))
            for bad in (float('nan'),True,101):
                altered=copy.deepcopy(report);altered['body_bounds_xz_m'][0][0]=bad
                with self.assertRaises(ValueError):shadow_guides(altered,0)

    def rules(self,role):
        old=mesh(role=='glass');ref=mesh(role=='glass',True)
        diffuse=texture([(63,63,63,63),(24,24,24,255)]*2)
        original=texture([(12,20,25,209),(0,0,0,255)]*2) if role=='glass' else texture([(30,30,30,255)]*4)
        resources={'car.dx':old,'base.dxt':original}
        refs={'model':ref,'diffuse':diffuse,'env':texture([(20,25,30,255)]*4)}
        rule={'texture':'base.dxt','source_sha256':sha(original),'reference_model':'model','reference_draw':0,'reference_diffuse':'diffuse','reference_environment':'env','draws':{'car.dx':[0]},'tread_v_range':[0,1],'window_alpha_value':209,'reference_rgb':[63]*3,'reference_alpha':63,'vertex_rgb':171}
        return resources,refs,{'version':1,role:rule}

    def test_classic_glass_changes_only_optical_texels_and_native_material(self):
        res,refs,plan=self.rules('glass');out,audit=apply_materials(res,res,plan,refs,{})
        a,b=parse_dx_bytes(res['car.dx']),parse_dx_bytes(out['car.dx'])
        self.assertEqual(a.vertices,b.vertices);self.assertEqual(a.local_indices,b.local_indices)
        self.assertEqual(res['car.dx'][a.trailing.offset:],out['car.dx'][b.trailing.offset:])
        self.assertEqual(a.physical_draws[0].flags_0x20,b.physical_draws[0].flags_0x20)
        self.assertTrue(b.physical_draws[0].unknown_0x24&4)
        tex=parse_dxt_bytes(out[b.physical_draws[0].texture_tuple[0]+'.dxt'])
        self.assertEqual(tex.bgra[:4],bytes([63]*4));self.assertEqual(tex.bgra[4:8],bytes([0,0,0,255]))
        self.assertEqual(out,apply_materials(res,res,plan,refs,{})[0])
        self.assertEqual(res['base.dxt'][20:24],bytes([12,20,25,209]))

    def test_classic_tyre_stays_opaque_geometry_uv_and_alpha_unchanged(self):
        res,refs,plan=self.rules('tyres');out,audit=apply_materials(res,res,plan,refs,{})
        a,b=parse_dx_bytes(res['car.dx']),parse_dx_bytes(out['car.dx'])
        self.assertEqual(a.vertices,b.vertices);self.assertEqual(a.uv_sets,b.uv_sets)
        self.assertFalse(b.physical_draws[0].flags_0x20[0])
        t=parse_dxt_bytes(out[b.physical_draws[0].texture_tuple[0]+'.dxt']);self.assertEqual(set(t.bgra[3::4]),{255})
        self.assertTrue(audit['tyres']['vertex_alpha_preserved'])

    def test_optical_colour_mask_preserves_coloured_banner_even_with_same_alpha(self):
        res,refs,plan=self.rules('glass')
        res['base.dxt']=texture([(12,20,25,209),(2,15,190,209),(50,10,2,255),(12,20,25,209)])
        rule=plan['glass'];rule.update(source_sha256=sha(res['base.dxt']),optical_bgra=[12,20,25,209],optical_sampling='stock_connected_regions',preserve_overlay_colour=True)
        out,_=apply_materials(res,res,plan,refs,{})
        m=parse_dx_bytes(out['car.dx']);self.assertEqual(m.physical_draws[0].texture_tuple[1],'Null');self.assertEqual(m.physical_draws[0].unknown_0x24,3)
        t=parse_dxt_bytes(out[m.physical_draws[0].texture_tuple[0]+'.dxt'])
        self.assertEqual(t.bgra[4:12],res['base.dxt'][24:32])
        self.assertEqual(m.vertices.colors,parse_dx_bytes(res['car.dx']).vertices.colors)

    def test_semantic_roles_reset_and_changed_or_mixed_sources_refuse(self):
        res,refs,plan=self.rules('glass');plan['glass']['enabled']=False
        self.assertEqual(apply_materials(res,res,plan,refs,{})[0],res)
        plan['glass']['enabled']=True;plan['glass']['source_sha256']='0'*64
        with self.assertRaises(ValueError):apply_materials(res,res,plan,refs,{})
        plan['glass']['source_sha256']=sha(res['base.dxt']);plan['glass']['window_alpha_value']=200
        with self.assertRaises(ValueError):apply_materials(res,res,plan,refs,{})
        plan['glass']['window_alpha_value']=209;plan['glass']['reference_alpha']=64
        with self.assertRaises(ValueError):apply_materials(res,res,plan,refs,{})

    def test_stock_material_reference_path_and_hash_guard(self):
        with tempfile.TemporaryDirectory()as td:
            for path in ('../private/car.dx','Car/../../car.dx','C:/car.dx','Car/car.exe'):
                with self.assertRaises(ValueError):references({'semantic_materials':{'references':{'a':{'path':path,'sha256':'0'*64}}}},td)

    def test_action_icons_leave_text_labels_and_roles_discoverable(self):
        for text in ('Undo','Redo','Save','Restore all','Validate','Build','Open interactive 3D','Reload preview','Play original','Stop','Outside'):
            self.assertIn(action_name(text),ICONS)
        self.assertIsNone(action_name('Native field'))

    def test_classic_preserve_source_paint_has_no_generated_texture(self):
        raw=texture([(12,13,14,209),(20,70,190,255),(170,180,190,63),(0,0,0,255)])
        res={'paint.dxt':raw};rule={'texture':'paint.dxt','source_sha256':sha(raw),'mode':'preserve_source'}
        out,audit=prepare_paint(res,rule)
        self.assertEqual(out,{});self.assertEqual(audit['mode'],'preserve_source');self.assertEqual(res['paint.dxt'],raw)
        rule['mode']='guess'
        with self.assertRaises(ValueError):prepare_paint(res,rule)
        rule.update(mode='preserve_source',source_sha256='0'*64)
        with self.assertRaises(ValueError):prepare_paint(res,rule)


if __name__=='__main__':unittest.main()
