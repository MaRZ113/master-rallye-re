import unittest
from certificate_contract import OwnerKey,UploadKey,Warmup


class Tests(unittest.TestCase):
    def ready(self):
        w=Warmup();owner=OwnerKey(1,2,3,4,0);up=UploadKey(5,6,7,8,9,10)
        for n in range(24):
            self.assertTrue(w.observe(owner,100,n,up,tuple(range(16)),membership=True,
                source_hash_verified=True,current_native_binding=True,scene_verified=True))
        return w,owner,up
    def test_complete_current_certificate_next_frame(self):
        w,o,u=self.ready();self.assertTrue(w.admit(o,101,{n:u for n in range(24)}))
        self.assertFalse(w.admit(o,100,{n:u for n in range(24)}))
    def test_new_reset_and_owner_reject(self):
        w,o,u=self.ready();self.assertFalse(w.admit(OwnerKey(1,2,3,4,1),101,{n:u for n in range(24)}))
    def test_recreated_resource_reject(self):
        w,o,u=self.ready();ups={n:u for n in range(24)};ups[1]=UploadKey(5,11,7,8,9,10)
        self.assertFalse(w.admit(o,101,ups))
    def test_partial_or_ambiguous_reject(self):
        w,o,u=self.ready();w.records.pop(23);self.assertFalse(w.admit(o,101,w.records))
        w,o,u=self.ready();self.assertFalse(w.observe(o,100,0,u,tuple(range(16)),membership=True,
            source_hash_verified=True,current_native_binding=True,scene_verified=True))
        self.assertFalse(w.admit(o,101,w.records))
    def test_unknown_native_binding_reject(self):
        w,o,u=self.ready();self.assertFalse(w.observe(o,100,23,u,tuple(range(16)),membership=True,
            source_hash_verified=True,current_native_binding=False,scene_verified=True))
        self.assertFalse(w.admit(o,101,w.records))


if __name__=='__main__':unittest.main()
