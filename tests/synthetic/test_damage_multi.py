import struct,unittest
from test_library import simple_record,synthetic_dx,footer56
from tools import vehicle_damage_native as native
from tools.vehicle_damage_multi_validate import validate


def fixture(offset=0):
    points=[(float(offset),0.,0.),(1.+offset,0.,0.),(float(offset),1.,0.)]
    record=bytearray(simple_record(0,2,0,3));record[0x20]=1;record[0x22]=1
    return synthetic_dx(points,[0,1,2],[bytes(record)],[(0,0,3)],trailing=footer56(points))


class DamageMultiTests(unittest.TestCase):
    def test_singleton_preserves_legacy(self):
        raw=fixture();self.assertEqual(native.payload(raw),native.payload_models([raw]))

    def test_multi_dispatch_call_once_and_unknown(self):
        report=validate([fixture(),fixture(2)])
        self.assertEqual(len(report['checks']),16);self.assertFalse(report['runtime_qualified'])

    def test_duplicate_rejected(self):
        raw=fixture()
        with self.assertRaisesRegex(ValueError,'duplicate'):native.payload_models([raw,raw])

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError,'count'):native.payload_models([])

    def test_ambiguous_identity_rejected(self):
        raw=fixture();model=native.parse_dx_bytes(raw);other=bytearray(raw);other[model.vertices.color_offset]^=1
        with self.assertRaisesRegex(ValueError,'ambiguous'):native.payload_models([raw,bytes(other)])
