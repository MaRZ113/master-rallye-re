"""Per-wheel native route guards and x86 ABI, without proprietary fixtures."""
import copy
import hashlib
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import vehicle_wheels_native as wheels
from validate_vehicle_wheels_native import synthetic_wrapper_replay,PROFILE
from vehicle_mechanics_native import append_mechanics


class NativeWheelSelectorTests(unittest.TestCase):
    def setUp(self):
        self.source=b'\xe8'+struct.pack('<i',wheels.REGISTER_WHEEL-wheels.CALL-5)+b'\0'*59
        self.prefix=b'research-owned existing payload'
        self.profile=copy.deepcopy(PROFILE)

    def append(self,profiles=None,**kwargs):
        with patch.object(wheels,'RETAIL_SHA256',hashlib.sha256(self.source).hexdigest()), \
             patch.object(wheels.registry,'parse_pe',return_value={}), \
             patch.object(wheels.registry,'va_to_file_offset',return_value=0):
            return wheels.append_wheels(self.source,kwargs.pop('image',self.source),kwargs.pop('blob',self.prefix),
                                       0x10000000,[self.profile]if profiles is None else profiles,
                                       kwargs.pop('allocation_size',131072),**kwargs)

    def test_generated_x86_routes_native_order_and_preserves_abi(self):
        report=synthetic_wrapper_replay()
        self.assertEqual(report['status'],'PASS_SYNTHETIC_WHEEL_SELECTOR_X86')
        self.assertEqual(len(report['cases']),12)

    def test_append_preserves_inputs_prefix_and_single_callsite(self):
        before=copy.deepcopy(self.profile);image,blob,report=self.append()
        self.assertEqual(self.profile,before);self.assertTrue(blob.startswith(self.prefix))
        self.assertEqual(image[5:],self.source[5:]);self.assertEqual(len(image),len(self.source))
        target=wheels.CALL+5+struct.unpack('<i',image[1:5])[0]
        self.assertEqual(target,report['entry_va']);self.assertEqual(report['auxiliary_entities_added'],0)
        self.assertEqual(report['delegate_registration_va'],wheels.REGISTER_WHEEL)
        self.assertFalse(report['runtime_qualified'])

    def test_repeated_front_rear_resource_keys_are_valid(self):
        self.profile['resource_keys']=[self.profile['resource_keys'][0],self.profile['resource_keys'][1]]*2
        self.append()

    def test_profile_paths_families_and_counts_fail_closed(self):
        cases=[{},dict(self.profile,unknown=True),dict(self.profile,runtime_family='../../Other'),
               dict(self.profile,runtime_family='Évo'),dict(self.profile,resource_keys=[]),
               dict(self.profile,resource_keys=['Vehicles/Foreign/wheel0']*4),
               dict(self.profile,resource_keys=['Vehicles/Evo2FourRunner/../wheel']*4),
               dict(self.profile,resource_keys=['Vehicles/Evo2FourRunner/wheel.dx']*4),
               dict(self.profile,resource_keys=['Vehicles/Evo2FourRunner/a/b']*4)]
        for value in cases:
            with self.subTest(value=value),self.assertRaises(ValueError):self.append([value])
        with self.assertRaises(ValueError):self.append([self.profile,dict(self.profile,runtime_family='evo2fourrunner')])
        with self.assertRaises(ValueError):self.append([dict(self.profile,runtime_family='A'+str(i))for i in range(9)])

    def test_unqualified_source_occupied_hook_and_output_budget_rejected(self):
        with self.assertRaises(ValueError):wheels.append_wheels(self.source,self.source,b'',0x10000000,[self.profile],131072)
        with self.assertRaisesRegex(ValueError,'already occupied'):self.append(image=b'\xe8\x11\x22\x33\x44'+self.source[5:])
        with self.assertRaisesRegex(ValueError,'allocation'):self.append(allocation_size=32)
        self.assertEqual(wheels.append_wheels(b'',b'unchanged',b'prefix',0,[],0),(b'unchanged',b'prefix',None))

    def test_only_exact_rebuilt_mechanics_delegate_is_admitted(self):
        import vehicle_mechanics_native as mechanics
        profile={'runtime_family':'LancerEvo4','resource_keys':['Vehicles/LancerEvo4/mechanics'+str(i)for i in range(4)]}
        with patch.object(mechanics,'RETAIL_SHA256',hashlib.sha256(self.source).hexdigest()), \
             patch.object(wheels.registry,'parse_pe',return_value={}), \
             patch.object(wheels.registry,'va_to_file_offset',return_value=0):
            image,blob,prior=append_mechanics(self.source,self.source,self.prefix,0x10000000,[profile],131072)
            output,new,report=self.append(image=image,blob=blob,mechanics_report=prior)
            self.assertTrue(new.startswith(blob));self.assertTrue(report['mechanics_delegate_verified'])
            self.assertEqual(report['delegate_registration_va'],prior['entry_va'])
            for changed in (dict(prior,entry_va=prior['entry_va']+1),dict(prior,prefix_size=-1),
                            dict(prior,prefix_sha256='0'*64),dict(prior,families=[])):
                with self.subTest(changed=changed),self.assertRaises(ValueError):
                    self.append(image=image,blob=blob,mechanics_report=changed)
            broken=bytearray(blob);broken[prior['entry_va']-0x10000000]^=1
            with self.assertRaisesRegex(ValueError,'bytes/entry'):
                self.append(image=image,blob=bytes(broken),mechanics_report=prior)
            self.profile['runtime_family']='LancerEvo4';self.profile['resource_keys']=profile['resource_keys']
            with self.assertRaisesRegex(ValueError,'overlap'):self.append(image=image,blob=blob,mechanics_report=prior)


if __name__=='__main__':unittest.main()
