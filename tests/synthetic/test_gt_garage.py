"""Synthetic bounded GT3 structures; no game data or source palettes bundled."""
import hashlib
import struct
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from master_rallye.gt3_source import Reader,texture_set,inspect_car
from gt3_ui_icon import read_indexed_member
from master_rallye.addon_sdk.gt4_source import unpack_uv
from master_rallye.addon_sdk.gt3_materials import interpret
from master_rallye.gt3_colourways import catalog as colour_catalog,select
from gt_garage import scan

def tex():
    b=bytearray(160);b[:4]=b'Tex1'
    struct.pack_into('<I',b,12,len(b));struct.pack_into('<HHIII',b,20,1,1,48,88,100)
    struct.pack_into('<III',b,100,2,112,120)
    struct.pack_into('<II',b,112,1,3|(42<<5));struct.pack_into('<II',b,120,1,4|(45<<5))
    return b

class GarageSourceTests(unittest.TestCase):
    def test_checkpoint_resume_is_deterministic_and_rejects_source_drift(self):
        import json
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);v=root/'volume';v.write_bytes(bytes(32)+bytes([1])*32);out=root/'report.json'
            rows=[{'path':'cars/day/'+str(i),'offset':i*32,'size':32,'uncompressed_size':32,'compressed':False}for i in range(2)]
            def inspect(b):return {'status':'PASS','sha256':hashlib.sha256(b).hexdigest(),'body':{'source_colourway_count':1}}
            with patch('gt_garage.inventory',return_value=rows),patch('gt_garage.catalog',return_value={'vehicles':[]}),patch('gt_garage.inspect_car',side_effect=inspect)as decode:
                self.assertEqual(scan(v,out,1)['inspected'],1)
                self.assertEqual(scan(v,out,resume=True)['inspected'],2)
                self.assertEqual(decode.call_count,2);before=out.read_bytes()
                scan(v,out,resume=True);self.assertEqual(out.read_bytes(),before)
                with self.assertRaisesRegex(ValueError,'--resume'):scan(v,out)
                v.write_bytes(bytes([2])*64)
                with self.assertRaisesRegex(ValueError,'source/reader changed'):scan(v,out,resume=True)
            self.assertEqual(json.loads(before)['levels']['L1'],'NOT TESTED')

    def test_gt3_current_parameters_do_not_accumulate_historical_lighting(self):
        command=lambda op,args:{'opcode':op,'operands':args}
        a=interpret([command(51,[.8,.8,.8,0]),command(50,[0])])
        self.assertFalse(a['gt3_lighting_pending']);self.assertEqual(a['unknown'],[])
        b=interpret([command(50,[0]),command(51,[.8,.8,.8,0])])
        self.assertTrue(b['gt3_lighting_pending']);self.assertEqual(b['gt3_parameters']['mode2'],[.8,.8,.8,0])
        self.assertTrue(interpret([command(255,[])])['unknown'])

    def test_original_colour_ids_not_rgb_presets(self):
        s=bytearray(32);s[:4]=b'STDB';struct.pack_into('<IhhI',s,4,2,1,0,32);struct.pack_into('<II',s,16,24,28);s[24:28]=b'\x02\0A\0';s[28:32]=b'\x02\0B\0'
        b=bytearray(84);b[:4]=b'GT2K';struct.pack_into('<5I',b,4,0,1,40,48,84);struct.pack_into('<QII',b,24,123,2,0);struct.pack_into('<II',b,40,7,19);struct.pack_into('<I',b,48,2);struct.pack_into('<4I',b,52,7,0,0,0x123456);struct.pack_into('<4I',b,68,19,1,1,0x654321)
        c=colour_catalog(b,s);m={'source_colourway_count':2,'texture_sets':[],'material_variants':[]}
        self.assertEqual(select(c,123,1,m)['colour_id'],19);self.assertEqual(select(c,123,1,m)['latin_name'],'B')
        m['source_colourway_count']=3
        with self.assertRaisesRegex(ValueError,'count mismatch'):select(c,123,0,m)
        struct.pack_into('<I',b,44,55)
        with self.assertRaisesRegex(ValueError,'unresolved'):colour_catalog(b,s)

    def test_uv_mask_only_admits_source_data_xy(self):
        values=[[struct.unpack('<i',struct.pack('<f',x))[0]for x in (.25,.75)]]
        c={'opcode':0x74,'address':0xc040,'format':[0,2],'values':values}
        self.assertEqual(unpack_uv([c],1,initial_mask=0xc0c0c0c0),[(.25,.75)])
        for mask in (None,0x55555555,0xc0c0c0c1):
            with self.assertRaisesRegex(ValueError,'masked UV'):unpack_uv([c],1,initial_mask=mask)
        with self.assertRaisesRegex(ValueError,'masked UV'):unpack_uv([{'opcode':0x20,'address':0,'register_words':[1]},c],1,initial_mask=0)

    def test_original_clut_variants_are_exact_records(self):
        b=tex();r=texture_set(Reader(b),0)
        self.assertEqual(r['colourways'],2)
        self.assertEqual(r['source_clut_variants'][0]['patches'],[{'texture_index':0,'csa':3,'cbp':42,'psm':0}])
        self.assertEqual(r['source_clut_variants'][0]['span_sha256'],hashlib.sha256(b[112:120]).hexdigest())
        self.assertNotEqual(r['source_clut_variants'][0]['span_sha256'],r['source_clut_variants'][1]['span_sha256'])

    def test_transfer_records_use_twelve_bytes(self):
        b=tex();struct.pack_into('<I',b,28,148)
        self.assertEqual(texture_set(Reader(b),0)['transfers'],1)

    def test_texture_spans_cannot_escape_into_following_component(self):
        b=tex();struct.pack_into('<I',b,12,128);struct.pack_into('<I',b,28,120)
        with self.assertRaisesRegex(ValueError,'outside Tex1'):texture_set(Reader(b),0)

    def test_invalid_clut_texture_rejected(self):
        b=tex();struct.pack_into('<I',b,116,1<<23)
        with self.assertRaisesRegex(ValueError,'texture index'):texture_set(Reader(b),0)

    def test_clut_budget_and_member_budget(self):
        b=tex();struct.pack_into('<I',b,100,257)
        with self.assertRaisesRegex(ValueError,'variant budget'):texture_set(Reader(b),0)
        with self.assertRaises(ValueError):inspect_car(bytes(8))

    def test_indexed_read_is_bounded_and_hashes_original(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'source';p.write_bytes(b'abcd')
            row={'offset':1,'size':2,'uncompressed_size':2,'compressed':False,'path':'test'}
            data,report=read_indexed_member(p,row,1)
            self.assertEqual(data,b'bc');self.assertEqual(report['decoded_sha256'],hashlib.sha256(data).hexdigest())
            row['offset']=3
            with self.assertRaisesRegex(ValueError,'outside volume'):read_indexed_member(p,row,1)

if __name__=='__main__':unittest.main()
