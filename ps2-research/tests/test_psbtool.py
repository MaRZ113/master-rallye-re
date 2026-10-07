import json
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import psbtool as p


def fixture(name=b'tile',uv=None,rect=(0,0,2,2)):
    uv = (0,1,1,1,0,0) if uv is None else uv
    record = struct.pack('<6f10iI',*uv,0,0,2,0,0,2,*rect,len(name))+name
    return struct.pack('<7I',0xf001,125,1,65,0,1,1)+record


def gxi(w=2,h=2):
    return struct.pack('<IHH',0x13039,w,h)+bytes((255,0,0,128))*w*h


class PSBTests(unittest.TestCase):
    def test_minimal(self):
        doc = p.parse_psb(fixture())
        self.assertEqual((doc['header']['image_count'],doc['triangle_count']),(1,1))
        self.assertEqual(doc['texture_references'],['tile'])
        self.assertEqual(doc['images'][0]['triangles'][0]['offset'],28)
        self.assertTrue(p.verify(doc,{'tile':gxi()})['verified'])

    def test_truncated_header(self):
        for size in range(16):
            with self.subTest(size=size),self.assertRaises(p.FormatError):p.parse_psb(fixture()[:size])

    def test_bad_magic_or_version(self):
        for offset in (0,4):
            b=bytearray(fixture());struct.pack_into('<I',b,offset,3)
            with self.assertRaises(p.FormatError):p.parse_psb(b)

    def test_impossible_counts(self):
        for offset in (8,20,24):
            b=bytearray(fixture());struct.pack_into('<I',b,offset,0xffffffff)
            with self.assertRaises(p.FormatError):p.parse_psb(b)

    def test_absent_image_index(self):
        b=bytearray(fixture());struct.pack_into('<I',b,16,2)
        with self.assertRaises(p.FormatError):p.parse_psb(b)

    def test_truncated_record(self):
        with self.assertRaises(p.FormatError):p.parse_psb(fixture()[:-3])

    def test_bad_string(self):
        for name in (b'tile\0',b'../tile',b'bad\\name',b'\xff',b'.',b'..'):
            with self.subTest(name=name),self.assertRaises(p.FormatError):p.parse_psb(fixture(name))

    def test_bad_string_length(self):
        b=bytearray(fixture());struct.pack_into('<I',b,28+64,2000)
        with self.assertRaises(p.FormatError):p.parse_psb(b)

    def test_bad_rectangle(self):
        with self.assertRaises(p.FormatError):p.parse_psb(fixture(rect=(2,0,1,2)))

    def test_bad_uv(self):
        for v in (float('nan'),float('inf'),-0.1,1.1):
            with self.subTest(v=v),self.assertRaises(p.FormatError):p.parse_psb(fixture(uv=(v,1,1,1,0,0)))

    def test_unknown_trailer_preserved_but_not_verified(self):
        doc=p.parse_psb(fixture()+b'\x00\xde\xad')
        self.assertEqual(doc['unknown_ranges'][-1]['raw_hex'],'00dead')
        with self.assertRaises(p.FormatError):p.verify(doc)

    def test_null_nonfinite_exact_bits(self):
        b=bytearray(fixture(name=b'Null',rect=(0,-16,16,0)))
        struct.pack_into('<I',b,28,0x7fc01234)
        doc=p.parse_psb(b)
        self.assertEqual(doc['images'][0]['triangles'][0]['uv_raw_u32'][0],'7fc01234')
        self.assertEqual(doc['unknown_ranges'][0]['raw_hex'][:8],'3412c07f')
        self.assertIsNone(doc['images'][0]['triangles'][0]['uv_pairs'][0][0])
        self.assertEqual(doc['texture_references'],[])
        json.dumps(doc,allow_nan=False)

    def test_missing_reference(self):
        doc=p.parse_psb(fixture())
        with self.assertRaises(p.FormatError):p.resolve_textures(doc,r'\TNG\DATAPSM\HUD\X.PSB',{'entries':[]})
        with self.assertRaises(p.FormatError):p.verify(doc,{})

    def test_texture_bounds_and_uv_allocation(self):
        with self.assertRaises(p.FormatError):p.verify(p.parse_psb(fixture()),{'tile':gxi(1,1)})
        doc=p.parse_psb(fixture(rect=(0,0,1,1)))
        with self.assertRaises(p.FormatError):p.verify(doc,{'tile':gxi()})

    def test_unaligned_stream(self):
        b=fixture(name=b'abc')
        doc=p.parse_psb(b)
        self.assertEqual(doc['recognized_size'],len(b))

    def test_metrics_not_invented(self):
        glyph=p.glyphs(p.parse_psb(fixture()))[0]
        self.assertEqual(glyph['character'],'A')
        self.assertIsNone(glyph['advance'])


class GXITests(unittest.TestCase):
    def test_valid_rgba_statistics(self):
        g=p.parse_gxi(gxi())
        self.assertEqual((g['width'],g['height'],g['alpha_min'],g['alpha_max']),(2,2,128,128))
        self.assertEqual(g['average_rgba'],[255,0,0,128])

    def test_bad_header(self):
        with self.assertRaises(p.FormatError):p.parse_gxi(gxi()[:7])

    def test_zero_dimensions(self):
        with self.assertRaises(p.FormatError):p.parse_gxi(struct.pack('<IHH',0x13039,0,2))

    def test_truncated_or_extra_payload(self):
        for b in (gxi()[:-1],gxi()+b'\0'):
            with self.assertRaises(p.FormatError):p.parse_gxi(b)

    def test_unsupported_variant(self):
        b=bytearray(gxi());struct.pack_into('<I',b,0,0x23039)
        with self.assertRaises(p.FormatError):p.parse_gxi(b)


class GeometryTests(unittest.TestCase):
    def pair(self):
        a={'index':0,'texture_name':'tile','vertices_xy':[[0,0],[2,0],[0,2]],
           'uv_pairs':[[0,1],[1,1],[0,0]],'source_rect_xyxy':[0,0,2,2]}
        b={'index':1,'texture_name':'tile','vertices_xy':[[0,2],[2,0],[2,2]],
           'uv_pairs':[[0,0],[1,1],[1,0]],'source_rect_xyxy':[0,0,2,2]}
        return [a,b]

    def test_quad_and_v_origin(self):
        import ui_visuals
        rows=self.pair();quads=p.derive_quads(rows)
        self.assertEqual(len(quads),1)
        # Raw row 0 is red; a V=.5..1 quad must select that row.
        for r in rows:
            r['uv_pairs']=[[u,.5+.5*v] for u,v in r['uv_pairs']]
        image={'local_bounds_xyxy':[0,0,2,2],'triangles':rows,'quads':p.derive_quads(rows)}
        raw=struct.pack('<IHH',0x13039,2,2)+bytes((255,0,0,255))*2+bytes((0,0,255,255))*2
        self.assertEqual(ui_visuals.assemble(image,{'tile':raw}).getpixel((0,1)),(255,0,0,255))

    def test_overlapping_triangles_are_not_a_quad(self):
        rows=self.pair()
        rows[1]['vertices_xy']=[[0,0],[2,0],[2,2]]
        rows[1]['uv_pairs']=[[0,1],[1,1],[1,0]]
        self.assertEqual(p.derive_quads(rows),[])

    def test_rotated_uv_is_not_supported_diagnostic(self):
        rows=self.pair()
        rows[1]['uv_pairs']=[[1,0],[0,1],[1,1]]
        self.assertEqual(p.derive_quads(rows),[])


@unittest.skipUnless(os.environ.get('PS2_UI_CORPUS'),'Set PS2_UI_CORPUS to the ignored extracted HUD directory')
class CanonicalTests(unittest.TestCase):
    def test_nums_and_template(self):
        di=Path(os.environ['PS2_UI_CORPUS'])
        for name,counts,hash_ in (
            ('HUD-NUMS.PSB',(10,4,32),'f68b7d81d2a6c41031604cdfb745e33d105b5f85d0b5b50833269cc358256ee4'),
            ('HUD-TEMPLATE.PSB',(11,11,34),'c36f89c2978a98a4e3e3e4ce64204ff9cd52c3f9a81c5891cb9268859e172f9b')):
            with self.subTest(name=name):
                d=p.parse_psb((di/name).read_bytes())
                self.assertEqual((d['header']['mapping_count'],len(d['images']),d['triangle_count']),counts)
                self.assertEqual(d['provenance']['decoded_sha256'],hash_)
                p.verify(d,{n:(di/(n.upper()+'.GXI')).read_bytes() for n in d['texture_references']})
                if name.startswith('HUD-NUMS.'):
                    self.assertEqual([r['image_index_u32'] for r in d['mappings']],[0,0,1,2,3,3,3,3,3,3])
                    self.assertEqual(len(d['unknown_ranges']),4)
                else:
                    self.assertEqual(d['texture_references'],[f'hud-template_{i:03d}' for i in range(8)])


if __name__=='__main__':unittest.main()
