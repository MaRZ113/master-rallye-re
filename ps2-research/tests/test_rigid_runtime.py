"""RIGID1 synthetic invariants, compact original instruction oracles, corpus checks."""
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import rigid_runtime as r
import tngtool as t
import dressing_runtime as d


def synthetic_xml(params=None, duplicates=1, model='misc\\haybale\\haybale'):
    scene=ET.Element('Scene');group=ET.SubElement(ET.SubElement(scene,'EggLists_Version4'),'List',Name='IContManager')
    for _ in range(duplicates):
        egg=ET.SubElement(group,'Egg',Name='haybale')
        ET.SubElement(egg,'Value',Name='en3d Model Name',Type='String',Value=model)
        ET.SubElement(egg,'Value',Name='en3d Matrix',Type='Matrix',Row0='1 0 0 0',Row1='0 1 0 0',Row2='0 0 1 0',Row3='0 0 0 1')
        ai=ET.SubElement(ET.SubElement(egg,'AI_List'),'AI');ET.SubElement(ai,'Value',Name='AI Name',Type='String',Value='gaAiRigidBody')
        config=ET.SubElement(ai,'gaAiRigidBody')
        for p in params or []:ET.SubElement(config,'Value',**p)
    return ET.tostring(scene)


def instruction_oracle(window, body, output=0x2000):
    """Independent straight-line instruction interpreter; finite IEEE32 only.

    Original instruction words drive register/memory topology. This is a small
    test oracle, not a PS2 emulator, and cannot certify live timing/contacts.
    """
    bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    real=lambda v:struct.unpack('<f',struct.pack('<I',v&0xffffffff))[0]
    mem={0x1000+o:bits(v) for o,v in body.items()};reg={0:0,4:0x1000,5:output,29:0x8000};fp={}
    for text in window['words']:
        word=int(text,16);op=word>>26;rs=(word>>21)&31;rt=(word>>16)&31;rd=(word>>11)&31
        imm=word&65535;imm=imm if imm<32768 else imm-65536;fn=word&63;fd=(word>>6)&31
        if op==9:reg[rt]=reg[rs]+imm
        elif op==15:reg[rt]=(word&65535)<<16
        elif op==0 and fn==45:reg[rd]=reg[rs]+reg[rt]
        elif op==0 and fn==8:break
        elif word==0:pass
        elif op==43:mem[reg[rs]+imm]=reg[rt]&0xffffffff
        elif op==49:fp[rt]=real(mem[reg[rs]+imm])
        elif op==57:mem[reg[rs]+imm]=bits(fp[rt])
        elif op==17 and rs==4:fp[rd]=real(reg[rt])
        elif op==17 and rs==16:
            a=fp[rd]
            if fn==0:fp[fd]=r.f32(a+fp[rt])
            elif fn==1:fp[fd]=r.f32(a-fp[rt])
            elif fn==2:fp[fd]=r.f32(a*fp[rt])
            elif fn==6:fp[fd]=a
            elif fn==7:fp[fd]=-a
            else:raise AssertionError('Unsupported original FPU instruction '+text)
        else:raise AssertionError('Unsupported original instruction '+text)
    return {a:real(v) for a,v in mem.items()}


class RigidSyntheticTests(unittest.TestCase):
    def test_constructor_defaults(self):
        self.assertEqual(r.resolve_properties([]),dict(mass=500.,moi=(100.,100.,100.),trigger_distance=5.,casts_shadow=False))

    def test_first_typed_mass_not_last_duplicate(self):
        rows=[dict(Name='Mass',Type='String',Value='1'),dict(Name='Mass',Type='Float',Value='5'),dict(Name='Mass',Type='Float',Value='500')]
        self.assertEqual(r.resolve_properties(rows)['mass'],5.)

    def test_finite_unusual_authored_values_retained(self):
        rows=[dict(Name='Mass',Type='Float',Value='-5'),dict(Name='MOI',Type='Vector3',Value='0 -2 3')]
        self.assertEqual(r.parse_authored(synthetic_xml(rows),'synthetic')['records'][0]['resolved']['mass'],-5)

    def test_unknown_properties_retained(self):
        rows=[dict(Name='Wind',Type='Float',Value='13')]
        case=r.parse_authored(synthetic_xml(rows),'synthetic')
        self.assertEqual(case['records'][0]['parameters'],rows)
        self.assertNotIn('Wind',case['records'][0]['resolved'])

    def test_duplicates_and_order_preserved(self):
        case=r.parse_authored(synthetic_xml(duplicates=2),'synthetic')
        a,b=case['records'];self.assertNotEqual(a['source_id'],b['source_id']);self.assertEqual(a['matrix_sha256'],b['matrix_sha256'])
        self.assertEqual([a['egg_index'],b['egg_index']],[0,1])

    def test_compact_inventory_excludes_original_matrices(self):
        compact=r.compact_authored(r.parse_authored(synthetic_xml(),'synthetic'))
        self.assertNotIn('matrix',compact['records'][0]);self.assertEqual(compact['counts']['authored_eggs'],1)

    def test_unknown_model_remains_unknown(self):
        case=r.parse_authored(synthetic_xml(model='misc\\unknown'),'synthetic')
        self.assertEqual(case['records'][0]['family'],'UNKNOWN')

    def test_bad_declaration_fails_closed(self):
        with self.assertRaises(r.Error):r.parse_authored(b'<!DOCTYPE x>'+synthetic_xml(),'bad')

    def test_bad_matrix_fails_closed(self):
        with self.assertRaises(r.Error):r.parse_authored(synthetic_xml().replace(b'1 0 0 0',b'nan 0 0 0'),'bad')

    def test_bad_moi_length_fails_closed(self):
        with self.assertRaises(r.Error):r.resolve_properties([dict(Name='MOI',Type='Vector3',Value='1 2')])

    def test_activation_3d_inclusive_boundary(self):
        self.assertTrue(r.near_gate((0,0,0),[dict(position=(0,100,0),predicate_200550=True)])['near'])
        self.assertFalse(r.near_gate((0,0,0),[dict(position=(0,100.01,0),predicate_200550=True)])['near'])

    def test_view_predicate_is_independent_of_distance(self):
        self.assertFalse(r.near_gate((0,0,0),[dict(position=(0,0,0),predicate_200550=False)])['near'])

    def test_second_view_and_ignored_third(self):
        v=[dict(position=(1000,0,0),predicate_200550=True),dict(position=(0,0,0),predicate_200550=True)]
        self.assertEqual(r.near_gate((0,0,0),v)['selected'],1)
        v[1]['predicate_200550']=False;v.append(dict(position=(0,0,0),predicate_200550=True))
        self.assertFalse(r.near_gate((0,0,0),v)['near'])

    def test_original_view_predicate_boundary(self):
        # Reuse independently recovered DRESSING1 200550 consumer; radius4.
        planes=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]
        self.assertFalse(d.sphere_eligibility(4,(4,0,0),(0,0,0),(0,0,1),planes)['eligible'])
        self.assertTrue(d.sphere_eligibility(4,(3.9,0,0),(0,0,0),(0,0,1),planes)['eligible'])

    def test_near_does_not_wake_initial_settled_body(self):
        self.assertEqual(r.activation_step(r.Activation(),True)['state'],r.asdict(r.Activation()))

    def test_contact_wake_acknowledged(self):
        result=r.activation_step(r.Activation(paused=False),True)
        self.assertEqual(result['branch'],'ACKNOWLEDGE_CONTACT_WAKE');self.assertFalse(result['state']['paused'])

    def test_far_pause_starts_60_invocation_decay(self):
        result=r.activation_step(r.Activation(paused=False,acknowledged=True,settled=False),False)
        self.assertEqual(result['state']['timer'],59);self.assertTrue(result['state']['paused']);self.assertTrue(result['state']['far_decay'])

    def test_far_decay_not_restarted_and_last_zeroed(self):
        result=r.activation_step(r.Activation(far_decay=True,settled=False,timer=1),False)
        self.assertEqual(result['decay'],'ZERO_MOMENTA_AND_VELOCITIES');self.assertEqual(result['state']['timer'],0)

    def test_near_resumes_far_body(self):
        result=r.activation_step(r.Activation(far_decay=True,settled=False,timer=30),True)
        self.assertFalse(result['state']['paused']);self.assertEqual(result['state']['timer'],0)

    def test_malformed_activation_fields_fail(self):
        with self.assertRaises(r.Error):r.activation_step(r.Activation(timer=1.5),False)
        with self.assertRaises(r.Error):r.activation_step(r.Activation(paused=1),True)

    def test_mass_and_inverse_diagonal(self):
        params=r.body_parameters(5,(2,2,2));self.assertEqual(params['inverse_body_inertia_diagonal'],(.5,.5,.5))
        self.assertAlmostEqual(params['inverse_mass'],.2)
        with self.assertRaises(r.Error):r.body_parameters(0,(2,2,2))

    def test_quaternion_derivative_independent_hamilton_product(self):
        q=(.5,.5,.5,.5);o=(1.,2.,3.)
        derivative=r.derivative(q,(0,0,0),o,(0,0,0),(0,0,0))
        self.assertEqual(derivative[3:7],(-1.5,0.,1.,.5))
        self.assertAlmostEqual(sum(a*b for a,b in zip(q,derivative[3:7])),0.)

    def test_derivative_accumulators_not_lost(self):
        out=r.derivative((1,0,0,0),(1,2,3),(0,0,0),(0,-49.05,0),(1,0,0),(0,1,0),(0,2,0))
        self.assertEqual(out[:3],(1.,2.,3.));self.assertEqual(out[10:],(1.,2.,0.));self.assertAlmostEqual(out[8],-48.05,places=4)

    def test_linear_rk4_matches_independent_constant_acceleration(self):
        for mass in (5,500):
            result=r.linear_step((0,10,0),(0,0,0),mass,r.DT_HALF)
            self.assertAlmostEqual(result['position'][1],10.-.5*r.GRAVITY*r.DT_HALF**2,places=5)
            self.assertAlmostEqual(result['momentum'][1]/mass,-r.GRAVITY*r.DT_HALF,places=6)

    def test_paused_state_and_external_force(self):
        self.assertEqual(r.linear_step((1,2,3),(4,5,6),5,.1,paused=True)['position'],(1.,2.,3.))
        result=r.linear_step((0,0,0),(0,0,0),5,1.,extra_force=(10,0,0))
        self.assertEqual(result['position'][0],1.);self.assertEqual(result['momentum'][0],10.)

    def test_visual_pose_com_and_row_convention(self):
        rows=((0,0,1),(0,1,0),(-1,0,0));right=(0,0,-1);up=(0,1,0);forward=(1,0,0)
        pose=r.visual_pose((10,20,30),rows,(1,0,0),right,up,forward)
        self.assertEqual(pose[0],[0.,0.,-1.,0.]);self.assertEqual(pose[3],[10.,20.,31.,1.])

    def test_quaternion_fallback_and_original_y_rotation(self):
        self.assertEqual(r.quaternion_rotation((0,0,0,0))[0],(1.,0.,0.,0.))
        pose=r.quaternion_pose((0,0,0),(math.sqrt(.5),0,math.sqrt(.5),0),(0,0,0))
        self.assertAlmostEqual(pose['body_rotation_rows'][0][2],1.,places=6)
        self.assertAlmostEqual(pose['en3d_matrix'][0][2],-1.,places=6)

    def test_original_instruction_derivative_and_gravity(self):
        windows=json.loads((r.ROOT/'rigid1/instruction-probes.json').read_text())['numeric_windows']
        body={0x11c:1.,0x120:2.,0x124:3.,0x128:1.,0x12c:2.,0x130:3.,0xac:.5,0xb0:.5,0xb4:.5,0xb8:.5,
              0x18c:4.,0x190:5.,0x194:6.,0x198:1.,0x19c:2.,0x1a0:3.,0x1a4:7.,0x1a8:8.,0x1ac:9.,0x1b0:4.,0x1b4:5.,0x1b8:6.}
        mem=instruction_oracle(windows['derivative'],body)
        expected=r.derivative((.5,.5,.5,.5),(1,2,3),(1,2,3),(4,5,6),(1,2,3),(7,8,9),(4,5,6))
        self.assertEqual(tuple(mem[0x2000+i*4] for i in range(13)),expected)
        mem=instruction_oracle(windows['gravity'],{0x1c:r.GRAVITY,0x20:500.})
        self.assertEqual((mem[0x118c],mem[0x1190],mem[0x1194]),(0.,-4905.,0.))

    def test_committed_inventory_totals_and_duplicate_control(self):
        case=json.loads((r.ROOT/'rigid1/rigid-course-inventory.json').read_text())
        self.assertEqual(case['totals'],dict(course_pairs=36,rigid_courses=9,authored_eggs=83,families=dict(haybale=58,tumbleweed=25)))
        italy=next(x for x in case['courses'] if x['course']=='ITALYS1')
        self.assertEqual((italy['counts']['authored_eggs'],italy['counts']['distinct_matrix_hashes']),(14,13))

    def test_contract_stays_static_and_contact_unknowns_explicit(self):
        contract=json.loads((r.ROOT/'rigid1/rigid-physics-contract.json').read_text())
        self.assertEqual(contract['runtime_validation'],'NOT_PERFORMED');self.assertEqual(contract['trigger_distance']['update_consumer'],'NOT_READ_IN_1a0258')
        self.assertIn('impulse magnitude',contract['unknowns'])

    def test_synthetic_cli_is_repeatable_and_matches_committed_trace(self):
        command=[sys.executable,str(r.ROOT/'tools/rigid_runtime.py'),'evaluate','--input',str(r.ROOT/'rigid1/synthetic-input.json')]
        first=subprocess.check_output(command);second=subprocess.check_output(command)
        self.assertEqual(first,second)
        self.assertEqual(json.loads(first),json.loads((r.ROOT/'rigid1/synthetic-expected.json').read_text()))

    def test_pc_collision_exists_without_claiming_pc_dynamics(self):
        evidence=json.loads((r.ROOT/'rigid1/pc-counterparts.json').read_text())
        self.assertIn('UNKNOWN',evidence['live_behavior'])
        self.assertEqual(evidence['scan']['absence_grade'],'NOT_FOUND_IN_SCANNED_PC_CORPUS')

    def test_output_boundary(self):
        with self.assertRaises(r.Error):r.local_output(r.ROOT/'rigid1/should-not-create.json')
        self.assertFalse((r.ROOT/'rigid1/should-not-create.json').exists())


class RigidCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ps2=os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not cls.ps2:raise unittest.SkipTest('MASTER_RALLYE_PS2_INPUT external canonical corpus required')

    def test_reextract_all_36_and_83(self):
        actual=r.corpus_inventory(self.ps2)
        expected=json.loads((r.ROOT/'rigid1/rigid-course-inventory.json').read_text())
        self.assertEqual(json.loads(json.dumps(actual)),expected)

    def test_original_instruction_words(self):
        corpus=r.s.Corpus(self.ps2);raw=(corpus.directory/'SLES_509.06').read_bytes()
        probes=json.loads((r.ROOT/'rigid1/instruction-probes.json').read_text())
        for p in [*probes['windows'].values(),*probes['numeric_windows'].values()]:
            data=raw[int(p['start'],16)-0xff000:int(p['end_exclusive'],16)-0xff000]
            self.assertEqual(t.sha(data),p['sha256']);self.assertEqual(list(struct.unpack('<%dI'%(len(data)//4),data)),[int(x,16) for x in p['words']])
        tables=json.loads((r.ROOT/'rigid1/vtable-evidence.json').read_text())['tables']
        for table in tables.values():
            base=int(table['address'],16)-0xff000
            data=raw[base:base+8*len(table['entries'])]
            self.assertEqual(t.sha(data),table['sha256'])
            for entry in table['entries']:
                offset=int(entry['offset'],16)
                self.assertEqual(struct.unpack_from('<I',data,offset+4)[0],int(entry['target'],16))
                self.assertEqual(struct.unpack_from('<h',data,offset)[0],entry['this_adjustment'])

    def test_shapes_and_aliases_independent_sdk(self):
        sdk=os.environ.get('MASTER_RALLYE_COURSE_SDK')
        if not sdk:self.skipTest('MASTER_RALLYE_COURSE_SDK read-only external SDK required')
        actual=r.shapes(self.ps2,sdk);expected=json.loads((r.ROOT/'rigid1/collision-shape-inventory.json').read_text())
        self.assertEqual(json.loads(json.dumps(actual)),expected);self.assertEqual(actual['models'][0]['sha256'],actual['models'][1]['sha256'])
        self.assertEqual([m['collision']['representation_b']['geometry_a']['vertices'] for m in actual['models']],[16,16,26])

    def test_pc_collision_and_baked_candidates(self):
        sdk=os.environ.get('MASTER_RALLYE_COURSE_SDK');pc=os.environ.get('MASTER_RALLYE_PC_INPUT')
        if not sdk or not pc:self.skipTest('External PC retail corpus and read-only Course SDK required')
        actual=r.pc_counterparts(pc,sdk,self.ps2);expected=json.loads((r.ROOT/'rigid1/pc-counterparts.json').read_text())
        self.assertEqual(json.loads(json.dumps(actual)),expected)
        self.assertEqual(actual['hay_standalone']['ps2_collision_agreement']['representation_b']['positions']['tolerance_matches'],16)


if __name__=='__main__':unittest.main()
