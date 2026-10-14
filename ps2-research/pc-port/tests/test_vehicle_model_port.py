from pathlib import Path
import importlib.util
import json
import math
import struct
import unittest

PORT=Path(__file__).resolve().parents[1]

def module(name):
    spec=importlib.util.spec_from_file_location(name,PORT/'tools'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

p=module('prepare_vehicle_models')
g=module('generate_vehicle_partitions')

class VehicleModelTests(unittest.TestCase):
    def synthetic(self):
        vertex=struct.pack('<3fII4f4f',0,1,0,1,0x11223344,.25,.75,0,1,1,2,3,1)
        meta={'source_sha256':'ab'*32,'meshes':[{'strips':[{'start':0,'count':1,'flag':17,'scale':1.}]}]}
        return meta,vertex,[b'synthetic texture']

    def test_private_representation_roundtrip_and_control_bits(self):
        meta,vertex,textures=self.synthetic();data=p.serialize(meta,vertex,textures)
        self.assertEqual(p.validate(data)['vertices'],1)
        self.assertEqual(p.validate(data)['textures'],1)
        self.assertEqual(data[p.HEADER.size+len(json.dumps(meta,sort_keys=True,separators=(',',':')).encode()):][:52],vertex)
        self.assertEqual(data,p.serialize(meta,vertex,textures))
        # raw normal, UV, XYZ/W, color and suppression bit are preserved exactly
        self.assertEqual(struct.unpack_from('<I',vertex,12)[0],1)

    def test_truncation_nonfinite_source_identity_and_strip_bounds(self):
        meta,vertex,textures=self.synthetic();data=p.serialize(meta,vertex,textures)
        for value in (data[:10],data[:-1],data+b'x'):
            with self.assertRaises(ValueError):p.validate(value)
        wrong=bytearray(data);wrong[24]=0
        with self.assertRaises(ValueError):p.validate(bytes(wrong))
        bad=bytearray(vertex);struct.pack_into('<f',bad,0,math.inf)
        with self.assertRaises(ValueError):p.serialize(meta,bytes(bad),textures)
        meta['meshes'][0]['strips'][0]['count']=2
        with self.assertRaises(ValueError):p.validate(p.serialize(meta,vertex,textures))

    def test_output_boundary(self):
        for value in ('../car','FORESTER/OTHER','forester','C:'):
            with self.assertRaises(ValueError):p.output_path(value)
        self.assertEqual(p.output_path('WOOLDAND'),PORT/'.assets/vehicles/WOOLDAND-COMPLETE.ps2vehicle')

    def test_exact_generated_registry_and_multiset_validation(self):
        evidence=json.loads(g.SOURCE.read_text())
        self.assertEqual(g.render(evidence),(PORT/'renderer/vehicle_partition_registry.hpp').read_text())
        evidence['vehicles'][0]['draws'][0]['geometry_sha256']='f'*64
        with self.assertRaises(ValueError):g.render(evidence)

    def test_all_models_and_forester_distinction(self):
        inventory=json.loads(p.INVENTORY.read_text())
        self.assertEqual(len(inventory['inventory']),29)
        rows={r['family']:r for r in inventory['inventory']}
        self.assertEqual(rows['FORESTER']['pc_pair'],'NO_VERIFIED_PC_COUNTERPART')
        self.assertEqual(rows['WOOLDAND']['pc_pair']['path'],'Forester/complete.dx')
        prepared=json.loads((PORT/'docs/vehicle-model-port1/private-model-preparation.json').read_text())
        self.assertEqual(len(prepared['models']),29)
        self.assertTrue(all(r['unresolved_texture_count']==0 for r in prepared['models']))
        self.assertEqual(prepared['runtime_replacement'],'NOT_IMPLEMENTED')

if __name__=='__main__':unittest.main()
