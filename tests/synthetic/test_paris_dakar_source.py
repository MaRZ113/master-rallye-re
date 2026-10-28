"""Invented small fixtures only. Actual corpus validation is a separate tool."""
from pathlib import Path
import copy
import struct
import tempfile
import unittest
from unittest.mock import patch
from master_rallye.source_adapters import paris_dakar_formats as f, paris_dakar as a
from master_rallye import universal_vehicle_scene as u

KEYS=f.Keys(b'header-test',b'table-test')


def tc(members):
    result=bytearray(2048);entries=[]
    for n,b in members:
        at=len(result);result.extend(b);result.extend(bytes((-len(result))%2048))
        e=bytearray(404);struct.pack_into('<4I',e,0,0,0,at,len(b));e[20:20+len(n)]=n.encode();entries.append(e)
    off=len(result);table=b''.join(entries);result.extend(f.xor(table,KEYS.directory))
    h=bytearray(80);struct.pack_into('<I',h,0,0xdeafbeef);struct.pack_into('<2I',h,68,len(entries),off)
    result[:80]=f.xor(h,KEYS.header);return result


def gex():
    b=bytearray(112+40+84+128+3*32);b[:4]=b'Gex#';b[4:10]=b'test.x'
    struct.pack_into('<6f',b,68,0,0,0,1,1,0);struct.pack_into('<5I',b,92,1,0,1,1,3)
    b[112:119]=b'tex.3df';mat=152;b[mat+20:mat+23]=b'mat'
    batch=236;struct.pack_into('<3I',b,batch+32,0,3,3);b[batch+64:batch+67]=bytes([0,3,6])
    for i,(x,y,uvx,uvy)in enumerate([(0,0,0,0),(1,0,1,0),(0,1,0,1)]):
        struct.pack_into('<8f',b,batch+128+i*32,x,y,0,1,uvx,uvy,0,0)
    return b


def tim():
    b=bytearray(1044+64+16+4+1);struct.pack_into('<II',b,0,16,0x40009)
    for i in range(256):b[8+i*4:12+i*4]=bytes([i,255-i,17,i])
    struct.pack_into('<IIHH',b,1032,76,0,8,8);b[1044:1108]=bytes(range(64));return b


def desc():
    lines=['RallyCar 1.00','ArchList Body : MainBody','ArchList BodyShadow : NULL',
           'ArchList FrontWheel : WheelFL','ArchList RearWheel : NULL']
    for x,z in [(-1,1),(1,1),(-1,-1),(1,-1)]:
        lines.extend([f'Vector3 Attach Point : {x} 1 {z}','Float Radius : 0.4','Float Rest Position : 0.46'])
    return ('\r\n'.join(lines)+'\r\n').encode()


class ParisDakarTests(unittest.TestCase):
    def test_directory_offsets_names_hashes(self):
        b=tc([('Description',b'abc'),('MainBody',gex())]);r=f.container(b,KEYS)
        self.assertEqual(r['entries'][1]['offset'],4096)
        self.assertEqual(r['entries'][0]['sha256'],u.sha(b'abc'))
        self.assertEqual(f.container(bytes(b),KEYS),r)

    def test_signature_wrong_key_and_truncation(self):
        b=tc([('a',b'a')])
        for bad in (b'',b[:79],b[:-1],bytes(80)):
            with self.assertRaises(ValueError):f.container(bad,KEYS)
        with self.assertRaises(ValueError):f.container(b,f.Keys(b'wrong',KEYS.directory))
        with self.assertRaises(ValueError):f.executable_keys(b'not an executable')

    def test_directory_count_and_resource_ranges(self):
        b=tc([('a',b'abc'),('b',b'def')]);r=f.container(b,KEYS);off=r['directory_offset']
        for field,value in [(8,0),(8,80),(12,off)]:
            bad=bytearray(b);table=bytearray(f.xor(b[off:],KEYS.directory));struct.pack_into('<I',table,field,value)
            bad[off:]=f.xor(table,KEYS.directory)
            with self.assertRaises(ValueError):f.container(bad,KEYS)
        h=bytearray(f.xor(b[:80],KEYS.header));struct.pack_into('<I',h,68,1000000);b[:80]=f.xor(h,KEYS.header)
        with self.assertRaises(ValueError):f.container(b,KEYS)

    def test_path_names_duplicate_case_and_overlap(self):
        for entries in [[('../bad',b'a')],[('a',b'a'),('A',b'b')]]:
            with self.assertRaises(ValueError):f.container(tc(entries),KEYS)
        b=tc([('a',b'a'),('b',b'b')]);off=f.container(b,KEYS)['directory_offset'];t=bytearray(f.xor(b[off:],KEYS.directory))
        struct.pack_into('<I',t,404+8,2048);b[off:]=f.xor(t,KEYS.directory)
        with self.assertRaises(ValueError):f.container(b,KEYS)

    def test_real_vertex_reorder_and_uv(self):
        m=f.gex(gex());self.assertEqual(m['triangles'],1)
        batch=m['batches'][0];self.assertEqual(batch['normals'],[[0,0,1]]*3)
        self.assertEqual(batch['uvs'],[[0,0],[1,0],[0,1]])
        self.assertEqual(batch['triangles'],[[0,1,2]])

    def test_index_reference_batch_and_allocation_rejections(self):
        for at,value,fmt in [(236+64,4,'B'),(236+64,9,'B'),(236+32,1,'I'),(236+36,49,'I'),(236+40,100000,'I'),(236,4,'I')]:
            b=gex();struct.pack_into('<'+fmt,b,at,value)
            with self.assertRaises(ValueError):f.gex(b)
        for b in (gex()[:-1],gex()+b'x',b'xof '+bytes(200)):
            with self.assertRaises(ValueError):f.gex(b)

    def test_nonfinite_uv_or_incorrect_normal(self):
        for at,value in [(236+128+16,float('nan')),(236+128+12,0.)]:
            b=gex();struct.pack_into('<f',b,at,value)
            with self.assertRaises(ValueError):f.gex(b)

    def test_texture_channel_exact_preservation(self):
        b=tim();meta,rgba,samples,pal=f.tim(b)
        self.assertEqual(rgba[:8],bytes([0,255,17,0,1,254,17,1]))
        self.assertEqual(samples,bytes(range(64)));self.assertEqual(pal,b[8:1032])
        self.assertEqual(len(meta['mip_planes']),4)
        for bad in (b[:-1],b+b'x',bytes(1044)):
            with self.assertRaises(ValueError):f.tim(bad)
        struct.pack_into('<H',b,1040,4096)
        with self.assertRaises(ValueError):f.tim(b)

    def test_explicit_static_coordinate_records(self):
        d=f.description(desc());self.assertEqual(d['wheels'][0]['attach_point'],[-1,1,1])
        for b in (desc().replace(b'-1 1 1',b'1 1 1'),desc().replace(b'Float Radius',b'Other Radius'),desc()[:50]):
            with self.assertRaises(ValueError):f.description(b)

    def test_missing_body_wheel_and_texture_references(self):
        for members in [[('Description',desc())],[('Description',desc()),('MainBody',gex()),('WheelFL',gex())]]:
            with self.assertRaises(ValueError):a.inspect(tc(members),KEYS)

    def test_scene_serialization_immutability_and_determinism(self):
        # Use complete original fake assembly, then existing shared serializer.
        with tempfile.TemporaryDirectory()as tmp:
            base=Path(tmp);root=base/'sources'/'game';root.mkdir(parents=True);(root/'Data').mkdir()
            exe=root/'dakar.exe';exe.write_bytes(b'fixture')
            data=tc([('Description',desc()),('MainBody',gex()),('WheelFL',gex()),('tex',tim())])
            (root/'Data/PajeroRED.tc').write_bytes(data);before={p:(p.read_bytes(),p.stat().st_mtime_ns)for p in root.rglob('*')if p.is_file()}
            with patch.object(f,'executable_keys',return_value=KEYS),patch.dict(a.QUALIFIED,{'PajeroRED.tc':u.sha(data)}):
                r=a.create_scene(root,base/'one');r2=a.create_scene(root,base/'two')
                self.assertEqual(r['manifest_sha256'],r2['manifest_sha256'])
                scene=u.load_scene(base/'one/scene.json');self.assertEqual(len(scene['nodes']),5)
                self.assertTrue(scene['unknown_semantics']);self.assertEqual(scene['coordinate_system']['source_to_normalized'],a.NORMALIZATION)
                for out in [root/'new',base/'sources/new',root.parent,base/'one']:
                    with self.assertRaises(ValueError):a.create_scene(root,out)
                (base/'one/textures/tex-0003.rgba').write_bytes(b'bad')
                with self.assertRaises(ValueError):u.load_scene(base/'one/scene.json')
            for p,(blob,mtime)in before.items():self.assertEqual((p.read_bytes(),p.stat().st_mtime_ns),(blob,mtime))

    def test_xor_budget_and_unsupported_catalog(self):
        with self.assertRaises(ValueError):f.xor(b'abc',b'')
        with self.assertRaises(ValueError):a.create_scene(Path('.'),Path('never-written'),'invented.tc')

    def test_shared_preview_culling_and_research_native_gate(self):
        from master_rallye.source_scene_preview import preview_cull,viewer_command
        from master_rallye.workshop.source_garage_ui import native_creation_available,preview_configuration
        scene={'metadata':{'adapter':a.VERSION,'neutral_preview':{'cull':'cw'}},'materials':[],'nodes':[]}
        original=copy.deepcopy(scene)
        self.assertEqual(preview_configuration(scene,{'wheel_detail':None}),scene)
        self.assertFalse(native_creation_available(scene));self.assertEqual(scene,original)
        self.assertTrue(native_creation_available({'metadata':{'source_adapter':'evo2-4runner/1'}}))
        self.assertEqual(preview_cull({}),'none');self.assertEqual(preview_cull(scene),'cw')
        command=viewer_command(Path('viewer'),Path('test.mrpv'),cull=preview_cull(scene))
        self.assertEqual(command[command.index('--cull')+1],'cw')
        for invalid in ('',None,'guess'):
            with self.assertRaises(ValueError):viewer_command(Path('viewer'),Path('test.mrpv'),cull=invalid)
