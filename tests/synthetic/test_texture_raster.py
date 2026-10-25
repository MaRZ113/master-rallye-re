import unittest
from PIL import Image
from master_rallye.workshop.texture_view import rasterize,display_image,MAX_VIEW_PIXELS
from master_rallye.dxt import DxtTexture,encode_png

class TextureRasterTests(unittest.TestCase):
    def image(self):
        im=Image.new('RGBA',(64,32));im.putdata([(x*3,y*7,127,(x*9+y*11)%256) for y in range(32) for x in range(64)]);return im
    def test_exact_one_to_one_including_hidden_rgb(self):
        im=self.image();before=im.tobytes();out,origin=rasterize(im,1,(3,5,20,13));self.assertEqual(out.tobytes(),im.crop((3,5,23,18)).tobytes());self.assertEqual(im.tobytes(),before)
    def test_filter_matches_global_mapping_across_zoom_and_pan(self):
        im=self.image()
        for scale in (.25,.5,.75,1,1.25,2,4):
            size=(round(im.width*scale),round(im.height*scale));full=im if scale==1 else im.convert('RGBa').resize(size,Image.Resampling.LANCZOS if scale<1 else Image.Resampling.BICUBIC).convert('RGBA')
            out,_=rasterize(im,scale,(2,1,7,5));expected=full.crop((2,1,9,6))
            # Pillow may round fractional filter coefficients at the source-box
            # boundary; the output shares the global scale and texel centers.
            self.assertLessEqual(max(abs(a-b) for a,b in zip(out.tobytes(),expected.tobytes())),3,scale)
    def test_premultiplied_alpha_does_not_bleed_hidden_red(self):
        im=Image.new('RGBA',(32,16),(255,0,0,0));im.paste((255,255,255,255),(16,0,32,16))
        for scale in (.25,.5,.75,1.25,2,4):
            out,_=rasterize(im,scale,(0,0,100,100))
            for r,g,b,a in zip(*(iter(out.tobytes()),)*4):
                if a:self.assertEqual((r,g,b),(255,255,255))
    def test_pixel_mode_and_view_budget(self):
        im=self.image();out,_=rasterize(im,4,(0,0,256,128),pixel=True);self.assertEqual(out.tobytes(),im.resize((256,128),Image.Resampling.NEAREST).tobytes())
        out,_=rasterize(im,16,(0,0,100000,100000));self.assertLessEqual(out.width*out.height,MAX_VIEW_PIXELS)
    def test_native_bytes_orientation_and_channels_unchanged(self):
        texture=DxtTexture('fixture',1,0,2,2,bytes(range(16)),b'');png=encode_png(texture);im=display_image(texture)
        self.assertEqual(im.getpixel((0,0)),(10,9,8,11));self.assertEqual(display_image(texture,'Alpha').getpixel((0,0)),(11,11,11,255));self.assertEqual(display_image(texture,'RGB').getpixel((0,0)),(10,9,8,255));self.assertEqual(encode_png(texture),png)
    def test_icon_sizes_and_vector_are_original_local_assets(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[2]/'assets/workshop';icon=Image.open(root/'rally-workshop.ico');self.assertEqual(icon.ico.sizes(),{(n,n) for n in (16,24,32,48,64,128,256)});icon.close()
        text=(root/'rally-workshop.svg').read_text();self.assertNotIn('<image',text);self.assertNotIn('href=',text)
