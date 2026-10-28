import hashlib,struct,unittest,zlib
from master_rallye.addon_sdk import auto_features as af
from master_rallye.addon_sdk.native_states import author_states
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.preview_scene import logical_cases
from tests.synthetic.test_library import simple_record,synthetic_dx,footer56

# Three draws: 0 body, 1 rear red lamp (faces -Z at the tail), 2 blended glass
# with a front pane (+Z normal) and a left pane (-X normal at the side).
BODY=[(-1.,0.,-1.),(1.,0.,-1.),(0.,0.,2.)]
LAMP=[(-.5,.5,-2.),(.5,1.,-2.),(.5,.5,-2.)]
GLASS=[(-.5,1.,1.),(.5,1.,1.),(0.,1.5,.8),(-1.,1.,.5),(-1.,1.5,-.5),(-1.,1.,-.5)]


def model(glass_flags=(1,0,1,1)):
    points=BODY+LAMP+GLASS;records=[]
    for i,(start,count,tex,flags) in enumerate([(0,3,'body-tga',(0,0,1,1)),(3,3,'lamp-tga',(0,0,1,1)),(6,6,'glass-tga',glass_flags)]):
        b=bytearray(simple_record(start,count-1,start,count,(tex,'Null','Null')));b[32:36]=bytes(flags);struct.pack_into('<I',b,36,3);records.append(b)
    local=[1,0,2,1,0,2,1,0,2,4,3,5] # stored (b,a,c), as the MR writer
    return synthetic_dx(points,local,records,[(0,0,3),(3,3,3),(6,6,6)],trailing=footer56(points))


def texture(rgba):
    bgra=bytes(v for p in rgba for v in (p[2],p[1],p[0],p[3]))
    return struct.pack('<5I',0xfeed,1,zlib.crc32(bgra)&0xffffffff,len(rgba),1)+bgra


TEXTURES={'body-tga.dxt':texture([(90,90,90,255)]),'lamp-tga.dxt':texture([(200,20,20,255)]),'glass-tga.dxt':texture([(40,50,60,120)])}


class AutoFeatureTests(unittest.TestCase):
    def test_sidecar_mesh_names_and_patterns(self):
        text='moMesh(Name [glass $glass] Index 4 Size 6)\nmoMesh(Name [blight $perspex] Index 10 Size 2)\nmoMesh(Name [blcase $perspex] Index 12 Size 2)'
        meshes=af.sidecar_meshes(text)
        self.assertEqual(meshes[0],('glass','$glass',4,6))
        self.assertTrue(af.BRAKE_RE.match('blight'));self.assertTrue(af.BRAKE_RE.match('BRAKELIGHTS'));self.assertFalse(af.BRAKE_RE.match('blcase'))
        self.assertTrue(af.GLASS_RE.match('windows2'));self.assertFalse(af.GLASS_RE.match('lightglass01'))

    def test_zone_glass_uses_native_axes(self):
        tris={0:((-.5,1.,1.),(.5,1.,1.),(0.,1.5,.8)),1:((-1.,1.,.5),(-1.,1.5,-.5),(-1.,1.,-.5)),2:((1.,1.,-.5),(1.,1.5,-.5),(1.,1.,.5)),3:((.5,1.,-1.),(-.5,1.,-1.),(0.,1.5,-.8))}
        zones=af.zone_glass(tris)
        self.assertEqual(zones['screenfront'],[0]);self.assertEqual(zones['screenleft'],[1]);self.assertEqual(zones['screenright'],[2]);self.assertEqual(zones['screenrear'],[3])

    def test_lamp_textures_mask_red_and_fallback(self):
        lit,glow,red=af.lamp_textures(parse_dxt_bytes(texture([(200,20,20,255),(20,200,20,255)])))
        self.assertEqual(red,1);g=parse_dxt_bytes(glow).bgra;self.assertGreater(g[3],0);self.assertEqual(g[7],0)
        _,glow,red=af.lamp_textures(parse_dxt_bytes(texture([(150,150,150,255)])))
        self.assertEqual(red,0);self.assertEqual(parse_dxt_bytes(glow).bgra[3],120)

    def test_record_mapping_discovers_axis_map(self):
        m=parse_dx_bytes(model())
        # Source records in a (x,z,-y) frame, as Demo GXM vs DX.
        records=[tuple((p[0],-p[2],p[1])for p in tri)for tri in (LAMP,GLASS[:3],GLASS[3:])]
        mapping,proof=af.map_records(m,records,[0,1,2])
        self.assertEqual(proof['matched'],3);self.assertEqual(mapping,{1:[0],2:[0,1]})
        moved=[tuple((p[0]+.002,p[1],p[2])for p in records[0])]
        mapping,proof=af.map_records(m,moved,[0])
        self.assertEqual(mapping,{1:[0]});self.assertEqual(proof['nearest_matches'],1)

    def test_geometric_fallback_recipe_conserves_model(self):
        raw=model();states,extra,report=af.derive(raw,TEXTURES)
        self.assertEqual(report['zones'],{'screenfront':1,'screenleft':1})
        self.assertEqual(states['brake']['source_draw'],1);self.assertEqual(len(extra),2)
        data,audit=author_states(raw,states)
        self.assertTrue(audit['collision_preserved']);self.assertTrue(audit['intact_off_geometry_normals_uv_materials_identical'])
        labels=sorted(g.root.group_label for g in parse_dx_bytes(data).draw_groups if g.root.tag==7)
        self.assertEqual(labels,['blight','screenfront','screenleft'])
        logical_cases(parse_dx_bytes(data))

    def test_state_scene_validator_admits_auto_recipe_only(self):
        from master_rallye.addon_sdk.native_states import validate_state_scene
        raw=model();states,_,_=af.derive(raw,TEXTURES);data,_=author_states(raw,states)
        result=validate_state_scene(raw,data)
        self.assertEqual(result['labels'],['blight','screenfront','screenleft']);self.assertFalse(result['runtime_qualified'])
        with self.assertRaises(ValueError):validate_state_scene(raw,raw)

    def test_sidecar_evidence_overrides_fallback(self):
        raw=model();records=[tuple((p[0],-p[2],p[1])for p in tri)for tri in (LAMP,GLASS[:3],GLASS[3:])]
        import unittest.mock as mock
        with mock.patch.object(af,'gxm_triangles',return_value=records):
            states,_,report=af.derive(raw,TEXTURES,sidecar_text='moMesh(Name [blight $perspex] Index 0 Size 1)\nmoMesh(Name [glass $glass] Index 1 Size 1)',gxm_raw=b'x')
        self.assertEqual([e['source']for e in report['evidence']],['car.txt mesh names + car.gxm records']*2)
        self.assertEqual(report['zones'],{'screenfront':1})

    def test_stale_global_index_table_is_rebuilt_from_local(self):
        from master_rallye.addon_sdk.heritage_source import repair_global_indices,compatible_model
        raw=model();m=parse_dx_bytes(raw);t=m.global_index_table
        bad=bytearray(raw);struct.pack_into('<3I',bad,t.data_offset,*reversed(t.indices[:3]))
        self.assertFalse(parse_dx_bytes(bytes(bad)).diagnostics.validated)
        fixed,changed=repair_global_indices(bytes(bad));self.assertEqual(fixed,raw);self.assertEqual(changed,2)
        out,report=compatible_model(bytes(bad),'synthetic');self.assertEqual(report['status'],'REV135_GLOBAL_INDEX_TABLE_REBUILT');self.assertEqual(out,raw)

    def test_false_blend_on_opaque_texture_is_normalized_but_glass_kept(self):
        from master_rallye.addon_sdk.heritage_source import normalize_false_blend
        raw=model();tex=dict(TEXTURES,**{'glass-tga.dxt':texture([(40,50,60,255)])})
        fixed,changed=normalize_false_blend(raw,tex)
        self.assertEqual([c['draw']for c in changed],[2]);self.assertEqual(tuple(parse_dx_bytes(fixed).physical_draws[2].flags_0x20),(0,0,1,1))
        _,changed=normalize_false_blend(raw,TEXTURES);self.assertEqual(changed,[])

    def test_procedural_cracks_is_valid_texture(self):
        t=parse_dxt_bytes(af.procedural_cracks(32));self.assertEqual((t.width,t.height),(32,32))


if __name__=='__main__':unittest.main()
