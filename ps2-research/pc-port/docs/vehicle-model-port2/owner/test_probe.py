import unittest
import struct
import probe


class Memory:
    def __init__(self):
        self.words={0x10000:0x69020c,0x69021c:0x44c4c0,
                    0x20050:0x30000,0x3000c:42,0x30074:0x40000,
                    0x400b0:0x30000,0x4008c:0x50000}
    def read(self,address,size):
        return b''.join(struct.pack('<I',self.words.get(address+i,0)) for i in range(0,size,4))


class Tests(unittest.TestCase):
    def tree(self):
        m=Memory();m.words.update({0x50018:0x60000,0x60000:0x70000,0x70004:0x80000,
            0x80000:0x6921b0,0x80004:0x90000,0x6921e0:0x578f30,
            0x90000:0x692364,0x692394:0x576910})
        return m
    def test_exact_rooted_membership(self):
        r=probe.model_mesh_membership(self.tree(),0x50000,0x90000)
        self.assertTrue(r['source_mesh_in_model'])
        self.assertFalse(r['replacement_authorized'])
    def test_unrelated_mesh_rejected_by_membership(self):
        self.assertFalse(probe.model_mesh_membership(self.tree(),0x50000,0x91000)['source_mesh_in_model'])
    def test_cycle_rejected(self):
        m=self.tree();m.words[0x90008]=0x90000
        with self.assertRaises(probe.ProbeError):probe.model_mesh_membership(m,0x50000,0x90000)
    def test_unknown_node_type_rejected(self):
        m=self.tree();m.words[0x90000]=0x692368
        with self.assertRaises(probe.ProbeError):probe.model_mesh_membership(m,0x50000,0x90000)
    def test_current_chain_is_observation_not_authority(self):
        r=probe.sample(Memory(),0x10000,0x20000)
        self.assertTrue(r['cache_packet_backref_matches'])
        self.assertFalse(r['replacement_authorized'])
        self.assertEqual(r['draw_resource_join'],'UNKNOWN_PENDING_CURRENT_CONSUMER')
    def test_wrong_ai_rejected(self):
        m=Memory();m.words[0x10000]=0x69020d
        with self.assertRaises(probe.ProbeError):probe.sample(m,0x10000,0x20000)
    def test_no_cache_rejected(self):
        m=Memory();m.words[0x30074]=0
        with self.assertRaises(probe.ProbeError):probe.sample(m,0x10000,0x20000)
    def test_change_rejected(self):
        class Changed(Memory):
            def __init__(self):super().__init__();self.count=0
            def read(self,address,size):
                if address==0x30074:
                    self.count+=1
                    if self.count>1:return struct.pack('<I',0x40004)
                return super().read(address,size)
        with self.assertRaises(probe.ProbeError):probe.sample(Changed(),0x10000,0x20000)


if __name__=='__main__':unittest.main()
