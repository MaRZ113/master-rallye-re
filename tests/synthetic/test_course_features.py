import sys
from pathlib import Path
import struct
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.course_features import read_proxy_features
from master_rallye.course_rigid import read_rigid_asset


class FeatureTests(unittest.TestCase):
    def test_grass_points_are_source_coordinates_and_wrong_bin_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Grass.ps2grass'
            header=struct.pack('<8s6I32s32s32s',b'PS2GRS01',1,1,1,32,32,4096,b'a'*32,b'b'*32,b'c'*32)
            raw=header+struct.pack('<2i2I',0,0,0,1)+struct.pack('<3f',1,2,3)+bytes(4096)
            path.write_bytes(raw);rows=read_proxy_features(path,'DataGx/Course/Any/any.dx')
            self.assertEqual(rows[0]['points'],[(1,2,3)]);self.assertEqual(rows[0]['support'],'INSPECT_ONLY')
            path.write_bytes(header+struct.pack('<2i2I',1,0,0,1)+raw[144:])
            with self.assertRaisesRegex(ValueError,'outside'):read_proxy_features(path,'unused')
            path.write_bytes(raw[:-1])
            with self.assertRaises(ValueError):read_proxy_features(path,'unused')

    def test_unsupported_rigid_version_is_rejected_without_hash_whitelist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'unknown.ps2rgd';path.write_bytes(struct.pack('<8s9I',b'PS2RGD02',99,1,1,3,4,4,1,1,0))
            with self.assertRaisesRegex(ValueError,'header'):read_rigid_asset(path)


if __name__=='__main__':unittest.main()
