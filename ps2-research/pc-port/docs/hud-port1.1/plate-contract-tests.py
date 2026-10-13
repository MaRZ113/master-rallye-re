import importlib.util
from pathlib import Path
import struct
import unittest

spec=importlib.util.spec_from_file_location('plate',Path(__file__).with_name('plate-contract.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
spec2=importlib.util.spec_from_file_location('collector',Path(__file__).with_name('paused-plate-probe.py'))
collector=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(collector)

class Memory:
    def __init__(self):
        self.data={};self.bytes_read=0;self.reads={};self.change=None
    def put(self,p,b):
        for i,v in enumerate(b):self.data[p+i]=v
    def read(self,p,n):
        self.reads[(p,n)]=self.reads.get((p,n),0)+1;self.bytes_read+=n
        b=bytes(self.data[p+i] for i in range(n))
        if self.change==(p,n) and self.reads[(p,n)]>1:return bytes([b[0]^1])+b[1:]
        return b
    def word(self,p,v):self.put(p,struct.pack('<I',v))

def fixture():
    m=Memory();esp=0x90000;owner=0x10000;ai=0x10100;packet=0x11000
    m.put(c.CHECKPOINT,bytes.fromhex('8d4e20'));m.word(esp+0x11C,owner);m.word(esp+0x14,packet)
    m.put(owner+4,struct.pack('<4I',ai,0,0,0));m.word(owner+0x4C,packet);m.word(ai,c.SPEED_DIAL_VTABLE)
    m.put(packet+8,struct.pack('<II',0x12000,0x12038));row=bytearray(0x38)
    struct.pack_into('<II',row,4,0x13000,0x13002);m.put(0x12000,row);m.put(0x13000,b'\x00\x00')
    m.word(esp+0x1C,0x20000);m.word(esp+0x44,0x21000)
    m.put(0x20004,struct.pack('<5I',0x21000,0x21010,0,0,0x22000))
    m.word(0x22004,0x23000);m.word(0x6F6478,0x24000)
    m.put(0x23000,struct.pack('<IIIhh',0x24000,0,0x24000,0,0))
    m.put(0x21000,struct.pack('<4I',0,0x30000,0x30068,0))
    m.put(0x30000,struct.pack('<I6f6i',42,0,0,1,0,1,1,*([0]*6))*2)
    m.word(0x40000,0x41000)
    return m,dict(eip=c.CHECKPOINT,esp=esp,esi=0x30000,eax=0x40000)

class CollectorTests(unittest.TestCase):
    def test_readonly_fixture_join(self):
        m,r=fixture();v=collector.collect(m,r)
        self.assertEqual(v['native_texture_argument_pointer'],0x41000)
        self.assertEqual(v['image_key'],0);self.assertFalse(v['replacement_authorized'])
    def test_owner_change(self):
        m,r=fixture();m.change=(0x10004,16)
        with self.assertRaises(ValueError):collector.collect(m,r)
    def test_bank_change(self):
        m,r=fixture();m.change=(0x20004,0x14)
        with self.assertRaises(ValueError):collector.collect(m,r)
    def test_triangle_change(self):
        m,r=fixture();m.change=(0x30000,0x68)
        with self.assertRaises(ValueError):collector.collect(m,r)
    def test_texture_argument_change(self):
        m,r=fixture();m.change=(0x40000,4)
        with self.assertRaises(ValueError):collector.collect(m,r)

class PlateTests(unittest.TestCase):
    def test_original_layout(self):
        raw=struct.pack('<I6f6i',42,0,0,1,0,1,1,-64,64,64,64,64,-64)
        t=c.decode_triangle(raw)
        self.assertEqual(t['texture_resource_id'],42)
        self.assertEqual(t['source_xy'][0],[-64,64])
        self.assertEqual(c.original_vertices(t,(0,0,0),0)[0],[-64.5,-63.5,0])
    def test_no_nonfinite_uv(self):
        with self.assertRaises(ValueError):c.decode_triangle(struct.pack('<I6f6i',0,float('nan'),0,0,0,0,0,*([0]*6)))
    def test_truncated_triangle(self):
        with self.assertRaises(ValueError):c.decode_triangle(bytes(51))
    def test_span_caps(self):
        self.assertEqual(c.bounded_span(0x10000,0x10068,52,2),2)
        for end in (0xFFFF,0x10069,0x1009C):
            with self.assertRaises(ValueError):c.bounded_span(0x10000,end,52,2)
    def args(self):
        return [dict(eip=c.CHECKPOINT,esi=0x30000),0x10000,0x11000,c.SPEED_DIAL_VTABLE,[0],0,0x20000,0x20000,0x20010,0x30000,0x30068]
    def test_exact_structural_join_not_authorized(self):
        self.assertFalse(c.qualify(*self.args())['replacement_authorized'])
    def test_wrong_class(self):
        a=self.args();a[3]=0x690000
        with self.assertRaises(ValueError):c.qualify(*a)
    def test_needle_key(self):
        a=self.args();a[4]=[2]
        with self.assertRaises(ValueError):c.qualify(*a)
    def test_ambiguous_keys(self):
        a=self.args();a[4]=[0,2]
        with self.assertRaises(ValueError):c.qualify(*a)
    def test_wrong_subimage(self):
        a=self.args();a[6]+=16
        with self.assertRaises(ValueError):c.qualify(*a)
    def test_wrong_triangle_checkpoint(self):
        a=self.args();a[0]['esi']+=52
        with self.assertRaises(ValueError):c.qualify(*a)
    def test_wrong_consumer_checkpoint(self):
        a=self.args();a[0]['eip']+=1
        with self.assertRaises(ValueError):c.qualify(*a)

if __name__=='__main__':unittest.main()

