import tempfile,unittest,struct
from pathlib import Path
from master_rallye.addon_sdk.stock_project import create,build,conflicts,restore,validated_overrides
from master_rallye.errors import MasterRallyeError
class StockTests(unittest.TestCase):
 def test_zero_change_and_restore(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);s=r/'source';f=s/'DataGx/Vehicles/Pajero/test.dxt';f.parent.mkdir(parents=True);f.write_bytes(struct.pack('<5I',0xfeed,0,0,1,1)+bytes([1,2,3,255]))
   create(s,r/'project','Pajero',1)
   self.assertTrue(build(r/'project',r/'zero')['zero_edit'])
   p=r/'project/resources/DataGx/Vehicles/Pajero/test.dxt';p.write_bytes(struct.pack('<5I',0xfeed,0,0,1,1)+bytes([3,2,1,255]))
   m=build(r/'project',r/'edited');self.assertEqual(len(m['resources']),1);self.assertEqual(f.read_bytes(),struct.pack('<5I',0xfeed,0,0,1,1)+bytes([1,2,3,255]))
   with self.assertRaises(ValueError):conflicts([m,m])
   self.assertEqual(list(validated_overrides(r/'project')),['DataGx/Vehicles/Pajero/test.dxt'])
   restore(r/'project','DataGx/Vehicles/Pajero/test.dxt');self.assertTrue(build(r/'project',r/'reset')['zero_edit'])
 def test_source_drift_and_paths(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);f=r/'source/DataGx/Vehicles/Pajero/a';f.parent.mkdir(parents=True);f.write_bytes(b'x');create(r/'source',r/'p','Pajero',1);f.write_bytes(b'y')
   with self.assertRaises((ValueError,MasterRallyeError)):build(r/'p',r/'out')
   with self.assertRaises(ValueError):create(r/'source',r/'q','../Test',0)

 def test_invalid_changed_resource_and_identity(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);f=r/'source/DataGx/Vehicles/Megane/a.dxt';f.parent.mkdir(parents=True);f.write_bytes(b'original')
   create(r/'source',r/'p','Megane',18)
   (r/'p/resources/DataGx/Vehicles/Megane/a.dxt').write_bytes(b'invalid')
   with self.assertRaises((ValueError,MasterRallyeError)):build(r/'p',r/'out')
   self.assertFalse((r/'out').exists())
   with self.assertRaises(ValueError):create(r/'source',r/'wrong','Megane',1)
