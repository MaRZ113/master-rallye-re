"""Portable regression fixtures for source-format differences, without game bytes."""
import copy
import tempfile
import unittest
import struct
import zlib
from pathlib import Path
from unittest.mock import patch

from tests.synthetic.test_gt4_material_pipeline import draws
from build_gt4_vehicle import compile_draws
from validate_gt4_vehicle import qualify_embedded_rim
from normalize_vehicle_texture_residency import box_resize,normalize
from tests.synthetic.test_gt4_material_pipeline import scene


class SecondSourceTests(unittest.TestCase):
    def test_integer_texture_filter_and_preserved_geometry(self):
        self.assertEqual(box_resize(bytes((0,0,0,0,100,200,80,240,100,200,80,240,0,0,0,0)),2,2,1,1),bytes((50,100,40,120)))
        with self.assertRaisesRegex(ValueError,'integer reduction'):
            box_resize(b'',3,3,2,2)
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input';source.mkdir();template,_=scene()
            for name in ('car.dx','complete.dx','wheel.dx'):(source/name).write_bytes(template)
            pixels=bytes((10,20,30,255))*(256*128)
            (source/'own.dxt').write_bytes(struct.pack('<5I',0xfeed,1,zlib.crc32(pixels)&0xffffffff,256,128)+pixels)
            result=normalize(source,Path(tmp)/'output',128)
            self.assertEqual(result['before']['cache_bytes'],4*result['after']['cache_bytes'])
            for name in ('car.dx','complete.dx','wheel.dx'):self.assertEqual((source/name).read_bytes(),(Path(tmp)/'output'/name).read_bytes())
            with self.assertRaisesRegex(ValueError,'output exists'):normalize(source,Path(tmp)/'output',128)

    def test_non_depth_alpha_only_pass_is_accounted_without_visible_geometry(self):
        base,_=draws([128]*16)
        effect=copy.deepcopy(base)
        effect['state'].update(fbmask=0xffffff,depth_write=False)
        with tempfile.TemporaryDirectory() as tmp:
            parts,records=compile_draws([base,effect],Path(tmp))
            self.assertEqual(len(parts),1)
            self.assertEqual(len(records),2)
            self.assertIn('alpha-only',records[1]['route'])
            effect['state']['depth_write']=True
            with self.assertRaisesRegex(ValueError,'fragment state'):
                compile_draws([base,effect],Path(tmp))
            effect['state'].update(depth_write=False,fbmask=0x00ffff)
            with self.assertRaisesRegex(ValueError,'fragment state'):
                compile_draws([base,effect],Path(tmp))

    def test_separate_wheel_bank_need_not_equal_explicit_car4_rim(self):
        model={'models':[{}],'shapes':[{}],'base':0}
        with patch('validate_gt4_vehicle.component',return_value=(b'embedded',{'header_field':'0x20'})), \
             patch('validate_gt4_vehicle.modelset',return_value=model), \
             patch('validate_gt4_vehicle.shape_geometry',return_value={'triangles':[(0,1,2)]}), \
             patch('validate_gt4_vehicle.model_texture_sets',return_value=[]):
            result=qualify_embedded_rim(b'CAR4',b'independent')
            self.assertFalse(result['byte_equal'])
            self.assertNotEqual(result['banks']['embedded']['sha256'],result['banks']['independent']['sha256'])
            self.assertIn('0x20',result['assembly_authority'])
        with patch('validate_gt4_vehicle.component',return_value=(b'embedded',{})), \
             patch('validate_gt4_vehicle.modelset',return_value=model), \
             patch('validate_gt4_vehicle.shape_geometry',side_effect=ValueError('malformed original shape')):
            with self.assertRaisesRegex(ValueError,'malformed original'):
                qualify_embedded_rim(b'CAR4',b'independent')


if __name__=='__main__':unittest.main()
