import struct,unittest
from master_rallye.addon_sdk.gt4_materials import interpret,blend_pixel,write_fragment
from master_rallye.addon_sdk.gt4_textures import address32,address_indexed,TextureSet,display_rgba

def command(op,*a):return {'opcode':op,'operands':list(a)}

class GSStateTests(unittest.TestCase):
    def test_preserve_mask_and_pgl_depth_remap(self):
        s=interpret([command(36,0xff000000)])
        self.assertEqual(s['write_bits'],0xffffff)
        for pgl,gs in enumerate((0,1,3,2)):self.assertEqual(interpret([command(25,pgl)])['depth_func'],gs)
        self.assertEqual(interpret([])['depth_func'],2)
    def test_blend_unity_and_destination_alpha(self):
        self.assertEqual(blend_pixel((200,100,50,128),(20,40,80,0),(0,1,0,1,0)),(200,100,50,128))
        self.assertEqual(blend_pixel((100,100,100,0),(30,30,30,64),(0,2,1,1,0)),(80,80,80,0))
    def test_date_alpha_fail_and_rgb_preserve(self):
        s=interpret([command(27),command(36,0xff000000)])
        self.assertEqual(write_fragment((1,2,3,128),(10,20,30,77),s,blend_enabled=False),((1,2,3,77),True))
        s=interpret([command(29),command(31,5)])
        self.assertEqual(write_fragment((1,2,3,128),(0,0,0,127),s),(None,False))
        s=interpret([command(28,6,128),command(47,3)])
        self.assertEqual(write_fragment((1,2,3,64),(10,20,30,99),s,blend_enabled=False),((1,2,3,99),False))
    def test_addresses_cover_pages_without_aliasing(self):
        self.assertEqual(len({address32(0,1,x,y) for y in range(32) for x in range(64)}),2048)
        self.assertEqual({address32(0,1,x,y) for y in range(32) for x in range(64)},set(range(0,8192,4)))
        for bits,h in ((4,128),(8,64)):
            got={address_indexed(0,2,x,y,bits) for y in range(h) for x in range(128)}
            self.assertEqual(len(got),128*h)
            self.assertTrue(all(0<=a<8192 and shift in (0,4) for a,shift in got))
    def test_tex1_direct_rgba_and_alpha_kept_separate(self):
        # Small complete CT32 transfer with an asymmetric 2x2 sampled texture.
        blob=bytearray(256+64*32*4);blob[:4]=b'Tex1';struct.pack_into('<I',blob,12,len(blob));struct.pack_into('<HHIII',blob,20,1,1,48,88,0)
        tex0=(1<<14)|(1<<26)|(1<<30)|(1<<34)
        struct.pack_into('<5Q',blob,48,tex0,0,0,0,0);struct.pack_into('<IHBBHH',blob,88,256,0,1,0,64,32)
        for y in range(32):
            for x in range(64):struct.pack_into('<4B',blob,256+4*(y*64+x),x,y,17,128 if x==0 else 64)
        t=TextureSet(bytes(blob),0).texture(0)
        self.assertEqual(t['rgba_ps2'],bytes([0,0,17,128,1,0,17,64,0,1,17,128,1,1,17,64]))
        self.assertEqual(display_rgba(t)[3::4],bytes([255,127,255,127]))
        with self.assertRaises(ValueError):TextureSet(b'Tex1'+bytes(40),0)

if __name__=='__main__':unittest.main()
