import copy
import json
from pathlib import Path
import struct
import unittest
import zlib

from master_rallye.addon_sdk.collection import reserve_roster, merge_resources, compose_ui_bank, plan_collection
from master_rallye.addon_sdk.manifest import AddonValidationError, load_capabilities, load_manifests, validate_manifests
from master_rallye.addon_sdk.ui_assets import append_frame, parse_bank

ROOT=Path(__file__).resolve().parents[2]


def bank(count):
    rows=[]
    for n in range(count):
        name=f'carsheet_{n:03d}_000'.encode()
        part=bytes(48)+struct.pack('<I',len(name))+name
        rows.append(struct.pack('<I',2)+part*2)
    return struct.pack('<3I',0xf001,125,count)+b''.join(struct.pack('<2I',i,i) for i in range(count))+struct.pack('<I',count)+b''.join(rows)


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.slots=[{'physical_id':27,'vehicle_class':'T2','class_local_index':7},
                    {'physical_id':28,'vehicle_class':'T2','class_local_index':8}]
    def test_stable_ids_and_tombstones(self):
        requests=[{'addon_id':'z-car','vehicle_class':'T2'}, {'addon_id':'a-car','vehicle_class':'T2','physical_id':28}]
        lock,rows=reserve_roster(requests,slots=self.slots)
        self.assertEqual([r['addon_id'] for r in rows],['z-car','a-car'])
        self.assertEqual(reserve_roster(list(reversed(requests)),slots=self.slots),(lock,rows))
        lock2,rows2=reserve_roster([requests[0]],slots=self.slots,previous=lock)
        self.assertEqual(lock2,lock)
        with self.assertRaises(AddonValidationError):
            reserve_roster([requests[0],{'addon_id':'new-car','vehicle_class':'T2'}],slots=self.slots,previous=lock)
        with self.assertRaises(AddonValidationError):
            reserve_roster([requests[1]],slots=self.slots,previous=lock)
    def test_fail_closed_profiles_and_identity_changes(self):
        for bad in ({},[],{'version':True,'reservations':[]},{'version':1,'reservations':{}}):
            with self.assertRaises(AddonValidationError):reserve_roster([],slots=self.slots,previous=bad)
        with self.assertRaises(AddonValidationError):reserve_roster([],slots=self.slots+self.slots)
        lock,_=reserve_roster([{'addon_id':'car-a','vehicle_class':'T2'}],slots=self.slots)
        with self.assertRaises(AddonValidationError):reserve_roster([{'addon_id':'car-a','vehicle_class':'T2','physical_id':28}],slots=self.slots,previous=lock)
    def test_resource_ownership(self):
        data,report=merge_resources([('a',{'DataGx/a.dxt':b'a'}),('b',{'datagx/A.dxt':b'a'})])
        self.assertEqual(len(report),1)
        with self.assertRaises(AddonValidationError):merge_resources([('a',{'../a':b''})])
        with self.assertRaises(AddonValidationError):merge_resources([('a',{'A':b'a'}),('b',{'a':b'b'})])
    def test_ui_rebases_independent_frames_without_overwrite(self):
        original=bank(32);one,_=append_frame(original,23);bgra=bytes([1,2,3,255])*(128*128)
        texture=struct.pack('<5I',0xfeed,1,zlib.crc32(bgra)&0xffffffff,128,128)+bgra
        two,textures,assigned=compose_ui_bank(original,'vehicle_select_art',[('car-a',one,texture),('car-b',one,texture)])
        self.assertEqual(assigned,{'car-a':32,'car-b':33});self.assertEqual(len(textures),2)
        self.assertEqual(parse_bank(two)['records'][:32],parse_bank(original)['records'])
        three,_,assigned=compose_ui_bank(one,'vehicle_select_art',[('car-b',one,texture)])
        self.assertEqual(assigned,{'car-b':33});self.assertEqual(three,two)
        with self.assertRaises(AddonValidationError):compose_ui_bank(original,'vehicle_select_art',[('a',one,texture[:-1])])
    def test_multiple_class_slots_and_explicit_order(self):
        path=ROOT/'research/vehicles/sdk/capabilities/retail-2001.json'
        caps,_=load_capabilities(path)
        manifests,_=load_manifests([ROOT/'research/vehicles/sdk/examples/r5v-qualifier-t2.json'])
        a=manifests[0];a['addon_id']='z-first';a['physical_id']={'policy':'explicit','value':27}
        b=copy.deepcopy(a);b['addon_id']='a-second';b['physical_id']['value']=28
        b['identity']={k:('Vehicles/' if k=='physics_family' else '')+'Second' for k in b['identity']}
        b['assets']['model_package_root']='DataGx/Vehicles/Second'
        caps['supported_addon_physical_ids'].append(28);caps['qualified_addon_slots'].append(self.slots[1]);caps['class_slot_limits']['T2']=9
        plan=validate_manifests([b,a],caps)
        self.assertEqual(plan['class_mapping']['class_to_physical_ids']['T2'],list(range(7,14))+[27,28])
        self.assertFalse(plan['evidence_boundary']['resolved_addon_ids_runtime_qualified'])
        # A later collection preserves earlier assignment rather than assigning
        # a newly alphabetically earlier name to the first class-local slot.
        a['physical_id']={'policy':'auto','value':None}
        b['physical_id']={'policy':'auto','value':None}
        lock,_=reserve_roster([{'addon_id':'z-first','vehicle_class':'T2','physical_id':27},
                              {'addon_id':'a-second','vehicle_class':'T2','physical_id':28}],slots=caps['qualified_addon_slots'])
        resolved,same=plan_collection([a,b],caps,lock)
        self.assertEqual(same,lock)
        self.assertEqual({r['addon_id']:r['physical_id'] for r in resolved['addons']},
                         {'z-first':27,'a-second':28})


if __name__=='__main__':unittest.main()
