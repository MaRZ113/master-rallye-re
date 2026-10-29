"""Invented geometry/palettes only; no donor data needed."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from copy import deepcopy
from test_michelin_research import xobj, tga
from master_rallye.source_adapters import michelin as m
from master_rallye import universal_vehicle_scene as u
from master_rallye.pajero_spare_probe import overlay


def toc(names):
    data = bytearray(8+54*(len(names)+1)+4);data[:4]=b'PTOC'
    struct.pack_into('<I',data,4,len(names)+1)
    for i,name in enumerate(names,1):
        at=8+54*i;struct.pack_into('<hf',data,at,3,float((i-1)*10))
        data[at+6:at+6+len(name)] = name.encode()
    struct.pack_into('<i',data,len(data)-4,sum(data[8:-4])-0xcc11bc)
    return bytes(data)


def decoded():
    files={'decoded/tex.tga':bytes(tga())}
    names=['CAR25A_%d.XO'%i for i in range(4)]
    for i,name in enumerate(names):
        files['decoded/'+name]=bytes(xobj())
        files['decoded/CAR25_%d_VERTEX.BIN'%i]=struct.pack('<9f',2,0,0,1,0,0,0,1,0)
    files['decoded/INDEX.TOC']=toc(names)
    return files


class MichelinSceneTests(unittest.TestCase):
    def build(self,root):
        with patch.object(m.f,'inspect_archive',return_value=({'entries':[]},decoded())):
            return m.build(b'invented','Car25A.PDO',0,root)

    def test_original_corner_order_and_uvs(self):
        model=m.f.xobj_structure(bytes(xobj()));before=deepcopy(model)
        meshes=m.geometry(model,'invented.xo','0'*64)
        self.assertEqual(meshes[0]['positions'],model['positions'])
        self.assertEqual(meshes[0]['uvs'],model['triangles'][0]['uv'])
        self.assertEqual(meshes[0]['triangles'],[[0,1,2]])
        self.assertEqual(before,model)

    def test_geometry_invalid_index_and_zero_normal_rejected(self):
        model=m.f.xobj_structure(bytes(xobj()));model['triangles'][0]['vertex_indices'][0]=99
        with self.assertRaises(ValueError):m.geometry(model,'x','0'*64)
        model=m.f.xobj_structure(bytes(xobj()));model['normals'][0]=[0,0,0]
        self.assertTrue(m.geometry(model,'x','0'*64)[0]['source']['face_normal_fallbacks'])
        model['triangles'][0]['face_normal']=[0,0,0]
        with self.assertRaises(ValueError):m.geometry(model,'x','0'*64)

    def test_ptoc_native_checksum_and_lod_records(self):
        data=toc(['a.xo','b.xo']);rows=m.ptoc(data)
        self.assertEqual([r['distance']for r in rows[1:]],[0.,10.])
        self.assertEqual([r['name']for r in rows[1:]],['a.xo','b.xo'])
        for bad in [data[:-1],b'FAIL'+data[4:],data[:-4]+bytes(4)]:
            with self.assertRaises(ValueError):m.ptoc(bad)

    def test_native_index_zero_coverage_requires_magenta_dispatch(self):
        raw=bytearray(tga());raw[18:24]=bytes([255,0,255,0,0,0])
        before=bytes(raw);meta,rgba,keyed=m.texture_preview(raw)
        self.assertTrue(keyed);self.assertEqual(list(rgba[3::4]),[0,255])
        self.assertEqual(rgba[4:7],bytes(3)) # Black remains opaque.
        self.assertEqual(bytes(raw),before)
        raw[18:21]=bytes(3)
        self.assertFalse(m.texture_preview(raw)[2]);self.assertEqual(set(m.texture_preview(raw)[1][3::4]),{255})

    def test_catalog_exact_initial_hub_formula_and_choice(self):
        data=bytearray(24*1608);struct.pack_into('<I',data,28,25)
        struct.pack_into('<5I',data,0x140,4,5,6,7,8)
        for i in range(4):struct.pack_into('<3f',data,0x1d0+i*12,float(i),.25,1.)
        r=m.catalog_rest(data,25,0)
        self.assertEqual(r['archive'],'Tarmac_t0004.pdo')
        self.assertAlmostEqual(r['hubs'][0]['initial_hub_xyz'][1],.25-r['initial_radius'])
        self.assertEqual(r['hubs'][0]['original_xyz'],[0.,.25,1.])
        for choice in [-1,5,True]:
            with self.assertRaises(ValueError):m.catalog_rest(data,25,choice)
        with self.assertRaises(ValueError):m.catalog_rest(data[:-1],25,0)

    def test_scene_reopen_channels_and_determinism(self):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td)/'source';root.mkdir();s,a=self.build(root)
            p=Path(td)/'A';q=Path(td)/'B'
            ra=u.save_scene(s,p,a);rb=u.save_scene(s,q,a)
            self.assertEqual(ra['scene_sha256'],rb['scene_sha256'])
            self.assertEqual(u.load_scene(p/'scene.json'),s)
            for texture in s['textures']:
                self.assertEqual(set(a[texture['rgba_path']][3::4]),{255})
            self.assertEqual(a['original/tex.tga'],bytes(tga()))
            self.assertEqual(s['metadata']['external_different_positions'],1)

    def test_missing_resources_and_stream_mismatch_fail(self):
        for key in ['decoded/tex.tga','decoded/CAR25_0_VERTEX.BIN','decoded/INDEX.TOC']:
            files=decoded();del files[key]
            with patch.object(m.f,'inspect_archive',return_value=({},files)),self.assertRaises(ValueError):
                m.build(b'invented','Car25A.PDO',0,Path.cwd())
        files=decoded();files['decoded/CAR25_0_VERTEX.BIN']=bytes(12)
        with patch.object(m.f,'inspect_archive',return_value=({},files)),self.assertRaises(ValueError):
            m.build(b'invented','Car25A.PDO',0,Path.cwd())

    def test_unqualified_hash_and_output_containment(self):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td);(root/'Data/Objects').mkdir(parents=True)
            p=root/'Data/Objects/Car25A.PDO';p.write_bytes(b'invented')
            with self.assertRaises(ValueError):m.recover(root,'Car25A.PDO',0,root/'out')
            self.assertEqual(p.read_bytes(),b'invented')
            s,a=self.build(root)
            with self.assertRaises(ValueError):u.save_scene(s,root/'out',a)

    def test_unknowns_and_explicit_variant_boundary(self):
        s,_=self.build(Path.cwd());self.assertTrue(s['unknown_semantics'])
        self.assertFalse(s['metadata']['native_create'])
        for v in [-1,4,True]:
            with self.assertRaises(ValueError):m.build(b'','Car25A.PDO',v,Path.cwd())

    def test_two_bank_assembly_provenance_and_immutable_sources(self):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td)/'source';(root/'Data/Objects').mkdir(parents=True);(root/'Server/Data').mkdir(parents=True)
            catalog=bytearray(24*1608);struct.pack_into('<I',catalog,28,25);struct.pack_into('<5I',catalog,0x140,*([4]*5))
            for i in range(4):struct.pack_into('<3f',catalog,0x1d0+i*12,float(i),.25,1.)
            raw={'RallyMasters.EXE':b'invented exe','Server/Data/Cars.BIN':bytes(catalog),
                 'Data/Objects/Car25A.PDO':b'body','Data/Objects/Tarmac_t0004.pdo':b'wheel'}
            for k,v in raw.items():(root/k).write_bytes(v)
            w={'decoded/tex.tga':bytes(tga()),'decoded/Tarmac_t0004_0.XO':bytes(xobj()),
               'decoded/INDEX.TOC':toc(['Tarmac_t0004_0.XO'])}
            def inspect(raw):return ({'entries':[]},decoded()if raw==b'body'else w)
            with patch.object(m,'QUALIFIED',{'Car25A.PDO':(u.sha(b'body'),'Invented car')}),\
                 patch.object(m,'WHEEL_SHA',{'Tarmac_t0004.pdo':u.sha(b'wheel')}),\
                 patch.object(m,'EXE_SHA',u.sha(raw['RallyMasters.EXE'])),\
                 patch.object(m,'CATALOG_SHA',u.sha(bytes(catalog))),patch.object(m.f,'inspect_archive',side_effect=inspect):
                result=m.assemble(root,'Car25A.PDO',Path(td)/'out')
            s=u.load_scene(Path(result['scene']));self.assertEqual(len(s['nodes']),5)
            self.assertEqual([n['role']for n in s['nodes']].count('wheel'),4)
            self.assertTrue(all(t['source']['member'].startswith(('body/','wheel/'))for t in s['textures']if 'source'in t))
            for k,v in raw.items():self.assertEqual((root/k).read_bytes(),v)

    def test_spare_overlay_restore_is_exact_and_unknown_node_rejected(self):
        s={'nodes':[],'arbitrary':'source'}
        self.assertEqual(overlay(s,False),s)
        with self.assertRaises(ValueError):overlay(s,True)
        with self.assertRaises(ValueError):overlay(s,1)

    def test_spare_instance_keeps_original_arrays_and_explicit_authorship(self):
        s,_=self.build(Path.cwd());n=s['nodes'][0]
        n['id']='node-030';n['name']='PAJ_SPAREWHEEL2';n['source_transform_record']={'invented':True}
        before=deepcopy(s);derived=overlay(s,True)
        self.assertEqual(s,before);self.assertEqual(derived['nodes'][:-1],s['nodes'])
        for key in ['meshes','textures','materials']:self.assertEqual(derived[key],s[key])
        self.assertFalse(derived['nodes'][-1]['source_visible'])
        self.assertIsNone(derived['nodes'][-1]['source_local_transform'])
        self.assertEqual(overlay(s,False),s)
