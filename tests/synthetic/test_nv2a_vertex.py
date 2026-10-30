"""Synthetic tokens only: no extracted Xbox shader payloads in the test corpus."""
import copy
import struct
import unittest
from master_rallye.source_adapters.nv2a_vertex import decode_program,describe,evaluate_outputs
from master_rallye.source_adapters.dakar2_vertex import link_fragments,compose_original,replay_constants,original


def token(mac=1, *, a=(2,0),b=(0,0),c=(0,0),output=3,mask=15,temp=0,temp_mask=0,ilu=0,ilu_mask=0,final=True):
    # Independently generated test operand encoding, identity swizzles.
    args=[a,b,c];vertices={v[1]for v in args if v[0]==2};constants={v[1]for v in args if v[0]==3}
    if len(vertices)>1 or len(constants)>1:raise ValueError('Shared address fields')
    vertex=next(iter(vertices),0);constant=next(iter(constants),0)+96
    w1=mac<<21|ilu<<25|constant<<13|vertex<<9|0x1b
    w2=(a[1]if a[0]==1 else 0)<<28|a[0]<<26|0x1b<<17|(b[1]if b[0]==1 else 0)<<13|b[0]<<11|0x1b<<2
    reg=c[1]if c[0]==1 else 0;w2|=reg>>2
    w3=(reg&3)<<30|c[0]<<28|temp_mask<<24|temp<<20|ilu_mask<<16|mask<<12|0x800|output<<3|int(final)
    return struct.pack('<4I',0,w1,w2,w3)


def program(*tokens):return struct.pack('<HH',0x2078,len(tokens))+b''.join(tokens)


class VertexTests(unittest.TestCase):
    def test_explicit_v0_is_not_unlit_raw_color_assumption(self):
        raw=program(token(2,a=(2,3),b=(3,40)))
        decoded=decode_program(raw);snapshot=copy.deepcopy(decoded)
        result=evaluate_outputs(decoded,{3:[.8,.6,.4,1]},{40:[.5,.25,1,1]},outputs=('V0',))
        self.assertEqual(result['V0'],[.4,.15,.4,1]);self.assertEqual(decoded,snapshot)
        with self.assertRaisesRegex(ValueError,'Missing explicit vertex constant'):
            evaluate_outputs(decoded,{3:[1]*4},{},outputs=('V0',))

    def test_undefined_light_accumulator_is_not_zero_initialized(self):
        raw=program(token(3,a=(1,11),c=(3,40)))
        with self.assertRaisesRegex(ValueError,'Undefined requested'):
            evaluate_outputs(decode_program(raw),{},{40:[.2]*4},outputs=('V0',))
        result=evaluate_outputs(decode_program(raw),{},{40:[.2]*4},outputs=('V0',),initial_temporaries={11:[.1]*4})
        self.assertAlmostEqual(result['V0'][0],.3)

    def test_alias_uv_inputs_do_not_imply_generated_output_alias(self):
        # T0=UV; T2=position, despite an equal second UV input.
        raw=program(token(a=(2,9),output=9,final=False),token(a=(2,0),output=11))
        result=evaluate_outputs(decode_program(raw),{9:[.2,.3,0,1],10:[.2,.3,0,1],0:[1,2,3,1]}, {},outputs=('T0','T2'))
        self.assertNotEqual(result['T0'],result['T2'])

    def test_original_linker_rule_preserves_all_fragments(self):
        a=program(token(a=(2,9),output=9));b=program(token(a=(2,3),output=3))
        linked=link_fragments([a,b]);decoded=decode_program(linked)
        self.assertEqual(decoded['count'],2);self.assertFalse(decoded['instructions'][0]['final'])
        self.assertEqual(len(describe(decoded)),2)
        self.assertEqual(linked,link_fragments([a,b]))
        self.assertEqual(a,program(token(a=(2,9),output=9)))
        with self.assertRaisesRegex(ValueError,'count budget'):link_fragments([a]*21)
        with self.assertRaisesRegex(ValueError,'instruction budget'):link_fragments([program(*[token(final=False)]*135,token())]*2)

    def test_reject_truncation_reserved_opcode_and_termination(self):
        for raw in(None,'x',b'',struct.pack('<HH',0x2078,137),program(token(final=False)),program(token())+b'0',program(token(15))):
            with self.assertRaises(ValueError):decode_program(raw)

    def test_unknown_operations_and_relative_constants_fail(self):
        decoded=decode_program(program(token(8)))
        with self.assertRaisesRegex(ValueError,'Unsupported'):evaluate_outputs(decoded,{0:[1]*4},{},outputs=('V0',))
        decoded=decode_program(program(token(a=(3,40))))
        decoded['instructions'][0]['inputs']['A']['relative']=True
        with self.assertRaisesRegex(ValueError,'Relative'):evaluate_outputs(decoded,{},{40:[1]*4},outputs=('V0',))

    def test_illegal_nonfinite_and_missing_output_fail(self):
        decoded=decode_program(program(token()))
        for value in([1,2,3], [1,2,3,float('inf')]):
            with self.assertRaisesRegex(ValueError,'Finite'):evaluate_outputs(decoded,{0:value},{},outputs=('V0',))
        with self.assertRaisesRegex(ValueError,'Undefined requested'):
            evaluate_outputs(decoded,{0:[1]*4},{},outputs=('T2',))
        with self.assertRaisesRegex(ValueError,'Unqualified original'):
            original(b'wrong executable',0x10000,4)

    def test_context_cannot_default_unknown_state(self):
        with self.assertRaisesRegex(ValueError,'Explicit complete'):compose_original(b'',0x192850,{})
        with self.assertRaisesRegex(ValueError,'matrix values'):
            replay_constants(b'',world=[1]*15,view=[1]*16,projection=[1]*16)
        with self.assertRaisesRegex(ValueError,'light slots'):
            compose_original(b'',0x192850,{'lighting':True,'lights':[0.]*8,'fog':False,'texture_transforms':[False]*4})
        decoded=decode_program(program(token()))
        with self.assertRaisesRegex(ValueError,'index budget'):evaluate_outputs(decoded,{16:[1]*4},{})

    def test_coissued_ilu_reads_old_temporary(self):
        # MAC overwrites r0 from v0 while ILU MOV must read pre-instruction r0.
        raw=program(token(1,a=(2,0),c=(1,0),temp=0,temp_mask=15,ilu=1,ilu_mask=15,mask=0,final=False),
                    token(a=(1,1)))
        result=evaluate_outputs(decode_program(raw),{0:[9]*4},{},outputs=('V0',),initial_temporaries={0:[2]*4})
        self.assertEqual(result['V0'],[2]*4)


if __name__=='__main__':unittest.main()
