"""Invented disc/resource bytes only; no donor assets or source-dependent skips."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from master_rallye.source_adapters import dakar2_disc as disc,dakar2_formats as fmt

def rbb(endian='<'):
    data=bytearray(256)
    def put(at,*values):struct.pack_into(endian+str(len(values))+'I',data,at,*values)
    data[:4]=b'\0RBB';put(4,256,0x42425200^256 if endian=='<'else 0x00524242^256)
    put(16,1,0,1,1,1);put(36,0,84,172,16,1,0,0,1,0)
    data[72:76]=b'TST\0';put(76,0,101);put(84,4);put(104,8);put(112,0x3f800000)
    def xor(at,size):
        n=0
        for(v,)in struct.iter_unpack(endian+'I',data[at:at+size]):n^=v
        return n
    put(68,xor(84,172));put(12,xor(16,68));return bytes(data)

def cube():
    data=bytearray(32768);data[:6]=b'TSTE00';data[28:32]=bytes.fromhex('c2339f3d')
    struct.pack_into('>III',data,0x420,0x100,0x500,50)
    struct.pack_into('>9I',data,0x500,0x01000000,0,3,0x01000000,0,3,5,0x1000,256)
    data[0x524:0x532]=b'cars\0body.rbb\0';data[0x1000:0x1100]=rbb('>');return bytes(data)

class Dakar2FormatTests(unittest.TestCase):
    def test_source_output_and_unsupported_vehicle_fail_before_any_write(self):
        from master_rallye.source_adapters.dakar2 import create_scene
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);image=root/'original.iso';image.write_bytes(b'original')
            with self.assertRaises(ValueError):create_scene(image,root/'new')
            with self.assertRaises(ValueError):create_scene(image,root/'new','invented')
            self.assertEqual(image.read_bytes(),b'original');self.assertFalse((root/'new').exists())

    def test_missing_model_hierarchy_or_texture_type_never_falls_back_to_guessed_geometry(self):
        r=fmt.RBB(rbb())
        for function in(fmt.hierarchy,fmt.xmd_meshes,fmt.xtx_texture):
            with self.assertRaises(ValueError):function(r,0)

    def test_xtx_bc1_channels_rectangular_layout_and_mips(self):
        class Texture:
            endian='<';resources=[{'type':'XTX','offset':0}]
            def __init__(self,data):self.data=data
            def slice(self,p,n):disc.span(p,n,len(self.data));return self.data[p:p+n]
            def u(self,p):return struct.unpack('<I',self.slice(p,4))[0]
            def pointer(self,p):return p+self.u(p)
        data=bytearray(120);struct.pack_into('<4I',data,0,8,4,12,2);struct.pack_into('<I',data,44,52)
        red=struct.pack('<HHI',0xf800,0,0);green=struct.pack('<HHI',0x07e0,0,0)
        data[96:]=red+green+red;tex=fmt.xtx_texture(Texture(bytes(data)),0)
        self.assertEqual(tex['original'],red+green+red);self.assertEqual(len(tex['mips']),2)
        self.assertEqual(tex['rgba'][:4],bytes((255,0,0,255)));self.assertEqual(tex['rgba'][16:20],bytes((0,255,0,255)))
        for offset,value in[(0,7),(8,6),(12,99),(44,999)]:
            bad=bytearray(data);struct.pack_into('<I',bad,offset,value)
            with self.assertRaises(ValueError):fmt.xtx_texture(Texture(bytes(bad)),0)

    def test_rvz_decompression_bomb_fails_with_bounded_output(self):
        try:from compression import zstd
        except ImportError:self.skipTest('RVZ optional Python3.14+ stdlib Zstandard')
        payload=zstd.compress(bytes(1024*1024))
        with self.assertRaises(ValueError):disc._zstd(payload,1024)

    def test_rbb_two_endians_checksums_and_immutable_self_relative_pointer(self):
        for endian in('<','>'):
            original=rbb(endian);parsed=fmt.RBB(original,endian)
            self.assertEqual(parsed.resources[0]['type'],'TST');self.assertEqual(parsed.pointer(104),112)
            self.assertEqual(parsed.floats(112,1),[1.]);self.assertEqual(parsed.data,original)
            with self.assertRaisesRegex(ValueError,'unqualified'):parsed.pointer(108)

    def test_rbb_corruption_wrong_endian_and_excessive_counts_rejected(self):
        for at in(0,4,8,12,16,24,28,32,40,44,52,64,68,80,84,112):
            data=bytearray(rbb());data[at]^=0xff
            with self.subTest(at=at),self.assertRaises((ValueError,UnicodeError)):fmt.RBB(bytes(data))
        with self.assertRaises(ValueError):fmt.RBB(rbb(),'>')
        with self.assertRaises(ValueError):fmt.RBB(b'\0RBB')

    def test_sbb_member_ranges_provenance_and_no_declared_length_overread(self):
        data=bytearray(384);struct.pack_into('<I',data,0,1);data[16:21]=b'A.LOD'
        struct.pack_into('<4I',data,48,128,256,123,264);data[128:]=rbb()
        rows=fmt.sbb_entries(bytes(data));self.assertEqual(rows[0]['stored_bytes'],256)
        self.assertEqual(rows[0]['sha256'],fmt.digest(rbb()));self.assertTrue(rows[0]['warnings'])
        for word,value in[(0,100000),(48,0),(52,9999),(60,9000)]:
            bad=bytearray(data);struct.pack_into('<I',bad,word,value)
            with self.assertRaises(ValueError):fmt.sbb_entries(bytes(bad))

    def test_original_strip_is_conserved_parity_includes_degenerate_indices(self):
        original=[0,1,2,2,3,3,4,5]
        self.assertEqual(fmt.strip_triangles(original,6),[[0,1,2],[4,3,5]])
        self.assertEqual(original,[0,1,2,2,3,3,4,5])
        for bad in([0,1,6],[0,-1,2],[]):
            with self.assertRaises(ValueError):fmt.strip_triangles(bad,6)

    def test_packed_signed_normal_edges_are_not_unsigned_color(self):
        self.assertEqual(fmt.packed_normal(1023),[1.,0.,0.])
        self.assertEqual(fmt.packed_normal(1024),[-1.,0.,0.])
        self.assertEqual(fmt.packed_normal(511<<22),[0.,0.,1.])
        self.assertEqual(fmt.packed_normal(512<<22),[0.,0.,-1.])

    def test_xdvdfs_checked_tree_and_bad_child_or_name(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'disc.iso';data=bytearray(0x12000);magic=b'MICROSOFT*XBOX*MEDIA'
            data[0x10000:0x10014]=magic;data[0x107ec:0x10800]=magic
            struct.pack_into('<II',data,0x10014,34,32)
            struct.pack_into('<HHIIBB',data,34*2048,0,0,35,4,0,9);data[34*2048+14:34*2048+23]=b'model.bin'
            p.write_bytes(data);reader=disc.FileReader(p);before=p.read_bytes()
            row=disc.xdvdfs(reader,0)[0];self.assertEqual((row['path'],row['offset']),('model.bin',35*2048));self.assertEqual(p.read_bytes(),before)
            for at,patch in[(0x10000,b'BAD!'),(34*2048,b'\xff\xff'),(34*2048+14,b'../')]:
                bad=bytearray(data);bad[at:at+len(patch)]=patch;p.write_bytes(bad)
                with self.assertRaises(ValueError):disc.xdvdfs(reader,0)

    def test_gamecube_fst_hierarchy_and_bad_name_or_root(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'disc.iso';data=cube();p.write_bytes(data);reader=disc.FileReader(p)
            result=disc.gamecube_fst(reader);self.assertEqual(result['files'][0]['path'],'cars/body.rbb')
            for at,value in[(0x508,999999),(0x514,1),(0x518,0xffffff)]:
                bad=bytearray(data);struct.pack_into('>I',bad,at,value);p.write_bytes(bad)
                with self.assertRaises(ValueError):disc.gamecube_fst(reader)

    def test_rvz_literals_padding_budget_and_incomplete_stream(self):
        literal=struct.pack('>I',4)+b'test';self.assertEqual(disc.unpack_rvz(literal,4,0),b'test')
        padding=struct.pack('>I',0x80000010)+bytes(68)
        self.assertEqual(disc.unpack_rvz(padding,16,0),bytes(16))
        self.assertEqual(disc.unpack_rvz(padding,16,100),bytes(16))
        for data,n in[(literal,3),(literal[:-1],4),(b'\0',4),(literal,5),(literal,8*1024*1024)]:
            with self.assertRaises(ValueError):disc.unpack_rvz(data,n,0)

    def test_rvz_real_compressed_roundtrip_and_header_hash_rejection(self):
        try:from compression import zstd
        except ImportError:self.skipTest('RVZ optional Python3.14+ stdlib Zstandard')
        original=cube();compressed=zstd.compress(original);size=4096+len(compressed);data=bytearray(size)
        d=bytearray(0xdc);struct.pack_into('>4I',d,0,1,5,1,32768);d[16:144]=original[:128]
        raw=zstd.compress(struct.pack('>QQII',128,32768-128,0,1));group=zstd.compress(struct.pack('>III',1024,len(compressed)|0x80000000,0))
        struct.pack_into('>IQIIQI',d,0xb4,1,384,len(raw),1,512,len(group))
        header=bytearray(72);header[:4]=b'RVZ\1';struct.pack_into('>III',header,4,0x1000000,0x1000000,0xdc);header[16:36]=hashlib.sha1(d).digest();struct.pack_into('>QQ',header,36,32768,size);header[52:72]=hashlib.sha1(header[:52]).digest()
        data[:72]=header;data[72:292]=d;data[384:384+len(raw)]=raw;data[512:512+len(group)]=group;data[4096:]=compressed
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'disc.rvz';p.write_bytes(data);reader=disc.RVZReader(p)
            self.assertEqual(reader.read(0,32768),original)
            self.assertEqual(disc.gamecube_fst(reader)['files'][0]['path'],'cars/body.rbb')
            bad=bytearray(data);bad[8]^=1;p.write_bytes(bad)
            with self.assertRaises(ValueError):disc.RVZReader(p)


if __name__=='__main__':unittest.main()
