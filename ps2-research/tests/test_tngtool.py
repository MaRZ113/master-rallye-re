"""Synthetic corruption tests; proprietary integration inputs are optional."""
import importlib.util
import os
import struct
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tngtool', ROOT / 'tools' / 'tngtool.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)

def literal(payload=b'abcd'):
    return bytes([17+len(payload)]) + payload + b'\x11\x00\x00'

def framed(payload=b'abcd'):
    stream = literal(payload)
    return struct.pack('<IBBHII', len(payload), 1, 1, 8192, 0, len(stream)) + stream + struct.pack('<II', len(stream), 0)

class Compression(unittest.TestCase):
    def long_literal(self,n):
        extra=n-18
        zeros=(extra-1)//255
        return b'\0'+b'\0'*zeros+bytes([extra-zeros*255])+b'A'*n

    def test_first_literal_special_match(self):
        self.assertEqual(t.lzo1x(self.long_literal(2050)+b'\0\0\x11\0\0',2053),b'A'*2053)

    def test_m4_long_distance(self):
        self.assertEqual(t.lzo1x(self.long_literal(16385)+b'\x11\x04\0\x11\0\0',16388),b'A'*16388)

    def test_extended_m3(self):
        self.assertEqual(t.lzo1x(b'\x12A\x20\x01\0\0\x11\0\0',35),b'A'*35)
    def test_literals(self):
        for n in range(1, 20):
            payload = b'x'*n
            self.assertEqual(t.lzo1x(literal(payload), n), payload)

    def test_overlapping_m2(self):
        self.assertEqual(t.lzo1x(b'\x15abcd\x40\x00\x11\0\0', 7), b'abcdddd')

    def test_m3(self):
        self.assertEqual(t.lzo1x(b'\x15abcd\x21\x00\x00\x11\0\0', 7), b'abcdddd')

    def test_small_match_and_tail(self):
        self.assertEqual(t.lzo1x(b'\x14abc\x01\0z\x11\0\0', 6), b'abcccz')

    def test_extended_literals(self):
        self.assertEqual(t.lzo1x(b'\0\x0e' + b'a'*32 + b'\x11\0\0', 32), b'a'*32)

    def test_invalid_backref(self):
        with self.assertRaises(t.FormatError): t.lzo1x(b'\x40\xff\x11\0\0', 3)

    def test_inner_rejects_frame(self):
        with self.assertRaises(t.FormatError): t.lzo1x(framed(), 4)

    def test_valid_frame(self):
        payload, info = t.decompress(framed())
        self.assertEqual(payload, b'abcd')
        self.assertEqual(len(info['blocks']), 1)

    def test_two_blocks_with_short_final(self):
        one,two=literal(b'abcd'),literal(b'ef')
        frame=struct.pack('<IBBHII',6,1,1,4,0,len(one))+one
        frame+=struct.pack('<II',len(one),len(two))+two+struct.pack('<II',len(two),0)
        payload,info=t.decompress(frame)
        self.assertEqual(payload,b'abcdef')
        self.assertEqual([r['unpacked_size'] for r in info['blocks']],[4,2])

    def test_every_truncation(self):
        frame = framed()
        for n in range(len(frame)):
            with self.subTest(n=n), self.assertRaises(t.FormatError): t.decompress(frame[:n])

    def test_bad_frame_fields(self):
        frame = framed()
        variants = []
        for offset, fmt, value in [(0,'<I',3),(0,'<I',5),(6,'<H',0),(8,'<I',1),(12,'<I',0xffffffff), (len(frame)-8,'<I',99),(len(frame)-4,'<I',1)]:
            b = bytearray(frame); struct.pack_into(fmt,b,offset,value); variants.append(bytes(b))
        variants += [frame+b'garbage', frame[:-8], frame[:4]+b'\x02'+frame[5:]]
        for b in variants:
            with self.subTest(data=b), self.assertRaises(t.FormatError): t.decompress(b)

    def test_lzo_trailing_and_wrong_size(self):
        for data, n in [(literal()+b'x',4),(literal(),3),(literal(),5),(b'\x15abcd\x12\0\0',4)]:
            with self.assertRaises(t.FormatError): t.lzo1x(data,n)

    def test_golden(self):
        source = os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not source: self.skipTest('INPUT_UNAVAILABLE: MASTER_RALLYE_PS2_INPUT')
        path = Path(source)/'TNG.PAK'
        if not path.is_file(): self.skipTest('INPUT_UNAVAILABLE: TNG.PAK')
        data = path.read_bytes()
        self.assertEqual(t.sha(data), t.PAK_SHA)
        output, info = t.decompress(data)
        self.assertEqual(len(output), 269668)
        self.assertEqual(t.sha(output), t.DIRECTORY_SHA)
        self.assertEqual(len(info['blocks']),33)

def tiny_directory():
    base=0x1000
    body=bytearray(140)
    struct.pack_into('<HHIIIIIII',body,0,2,2,base+32,40,base+72,8,base+80,60,base)
    struct.pack_into('<I',body,32,base+64)
    struct.pack_into('<I',body,48,base+68)
    body[64:72]=b'dir\0raw\0'
    struct.pack_into('<HHI',body,72,1,0,base+80)
    struct.pack_into('<IIIIIHH',body,80,base+108,0,0,0,base+108,0,0)
    body[104:108]=b'\\\0ii'
    struct.pack_into('<IIIIIHH',body,108,3,4,4,0,0,1,0)
    body[132:140]=b'\\A.GXI\0i'
    return struct.pack('<II',0x0100face,len(body))+body

class Directory(unittest.TestCase):
    def test_json_uses_platform_independent_lf(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'manifest.json'
            t.write_json(path,{'path':r'\TNG\A.GXI','size':4})
            before=path.read_bytes()
            self.assertNotIn(b'\r',before)
            t.write_json(path,{'path':r'\TNG\A.GXI','size':4})
            self.assertEqual(path.read_bytes(),before)

    def test_synthetic_root_and_file(self):
        m=t.parse_directory(tiny_directory())
        self.assertEqual((m['root'],m['directory_count'],m['file_count']),('\\',1,1))
        self.assertEqual(m['entries'][1]['offset'],3)

    def test_invalid_structures(self):
        variants=[]
        for offset,fmt,value in [(0,'<I',0),(4,'<I',99),(8,'<H',3),(12,'<I',1),
                                 (40,'<I',0xfffffff0),(84,'<I',0),(88,'<I',0xfffffff0),
                                 (104,'<I',0x1050),(136,'<H',9)]:
            b=bytearray(tiny_directory());struct.pack_into(fmt,b,offset,value);variants.append(bytes(b))
        b=bytearray(tiny_directory());b[132:]=b'x'*(len(b)-132);variants.append(bytes(b))
        for b in variants:
            with self.subTest(data=b),self.assertRaises(t.FormatError):t.parse_directory(b)

    def test_ranges(self):
        m=t.parse_directory(tiny_directory())
        self.assertEqual(t.validate_ranges(m,7),[])
        self.assertEqual(len(t.validate_ranges(m,6)),1)
        m['entries'][1]['offset']=-1
        self.assertEqual(len(t.validate_ranges(m,7)),1)

    def test_path_traversal(self):
        for path in ['../bad',r'\TNG\..\bad',r'C:\bad',r'\\server\bad',r'\TNG\CON.GXI',r'\TNG\name.',r'\TNG\bad:stream']:
            with self.subTest(path=path),self.assertRaises(t.FormatError):t.logical_path(path)
        self.assertEqual(t.logical_path('/TNG/A.GXI'),r'\TNG\A.GXI')

    def test_input_overwrite_guard(self):
        with self.assertRaises(t.FormatError):t.protect_inputs(Path('TNG.PAK'),[Path('TNG.PAK')])
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'TNG.PAK';source.write_bytes(b'synthetic')
            link=Path(temp)/'output';os.link(source,link)
            with self.assertRaises(t.FormatError):t.protect_inputs(link,[source])

    def test_direct_seek_extraction(self):
        entry=t.parse_directory(tiny_directory())['entries'][1]
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'TNG.000';p.write_bytes(b'padabcdtail')
            data,report=t.read_payload(entry,p)
            self.assertEqual(data,b'abcd')
            self.assertEqual(report['stored_sha256'],t.sha(b'abcd'))
            self.assertTrue(t.extraction_path(Path(temp),entry['path']).is_relative_to(Path(temp)))
            p.write_bytes(b'padabc')
            with self.assertRaises(t.FormatError):t.read_payload(entry,p)

    def test_nested_extraction(self):
        frame=framed()
        entry=t.parse_directory(tiny_directory())['entries'][1]
        entry.update(offset=3,stored_size=len(frame),storage_codec='gz')
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'TNG.000';p.write_bytes(b'pad'+frame+b'tail')
            data,report=t.read_payload(entry,p)
            self.assertEqual(data,b'abcd')
            self.assertEqual(report['compression'],'packfs_lzo')

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'root';root.mkdir()
            outside=Path(temp)/'outside';outside.mkdir()
            try:(root/'TNG').symlink_to(outside,target_is_directory=True)
            except OSError:self.skipTest('Symlink creation unavailable on this host')
            with self.assertRaises(t.FormatError):t.extraction_path(root,r'\TNG\A.GXI')

    def test_canonical_directory(self):
        source=os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not source:self.skipTest('INPUT_UNAVAILABLE: MASTER_RALLYE_PS2_INPUT')
        pak=Path(source)/'TNG.PAK'
        if not pak.is_file():self.skipTest('INPUT_UNAVAILABLE: TNG.PAK')
        m,_=t.load_pak(pak)
        self.assertEqual((m['directory_count'],m['file_count']),(137,3599))
        paths={r['path'] for r in m['entries']}
        self.assertIn(r'\TNG\DATAPSM\HUD\HUD-TEMPLATE.PSB',paths)
        self.assertIn(r'\TNG\DATAPSM\COMMONTEXTURES\ENVSOURCE64X64.GXI',paths)
        data=Path(source)/'TNG.000'
        if not data.is_file():self.skipTest('INPUT_UNAVAILABLE: TNG.000')
        self.assertEqual(t.validate_ranges(m,data.stat().st_size),[])
        row=next(r for r in m['entries'] if r['path']==r'\TNG\DATAPSM\HUD\HUD-TEMPLATE.PSB')
        payload,report=t.read_payload(row,data)
        self.assertEqual(len(payload),3004)
        self.assertEqual(report['compression'],'packfs_lzo')

if __name__ == '__main__': unittest.main()
