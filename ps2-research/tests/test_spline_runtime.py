"""Analytic checks, original ELF instruction probes and optional named corpus gates."""
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import spline_runtime as s


POINTS = [(0., 0., 0.), (3., 0., 0.), (3., 4., 0.), (6., 4., 0.)]
CONFIG = s.Config(True, False, False, 2., 3., 6., False, 0, 0., 30)


def synthetic():
    markers = ''.join(f'<Marker No="{n}"><Value Name="Marker Pos" Type="Vector3" Value="{x} {y} {z}"/>'
                      '<Value Name="Marker Type" Type="String" Value="Null"/>'
                      '<Value Name="Marker Dir" Type="Vector3" Value="1 0 0"/></Marker>'
                      for n, (x,y,z) in zip([9,1,6,3], POINTS))
    return ('<Scene><EggLists_Version4><List Name="ambient"><Egg Name="boat">'
            '<Value Name="en3d Model Name" Type="String" Value="synthetic/model"/>'
            '<AI_List><AI No="0"><Value Name="AI Name" Type="String" Value="gaEntitySpline"/>'
            '<gaEntitySpline><Value Name="MarkerList Name" Type="String" Value="route"/>'
            '<Value Name="Use Const Speed" Type="Bool" Value="True"/>'
            '<Value Name="Max Speed/Const Speed" Type="Float" Value="2.00000"/>'
            '<Value Name="Max Speed/Const Speed" Type="Float" Value="99"/>'
            '<Value Name="Number Of Samples" Type="Int" Value="30"/>'
            '</gaEntitySpline></AI></AI_List></Egg></List></EggLists_Version4>'
            '<MarkerLists><List Name="route">'+markers+'</List></MarkerLists></Scene>').encode()


class ParsingTests(unittest.TestCase):
    def test_preserves_order_numbers_duplicates_and_binding(self):
        i,p,c = s.parse_case(synthetic(), 'synthetic.xml', 'boat')
        self.assertEqual([m['attributes']['No'] for m in i['markers']], ['9','1','6','3'])
        self.assertEqual(p, POINTS)
        speed = [v for v in i['parameters'] if v['Name'] == 'Max Speed/Const Speed']
        self.assertEqual([v['Value'] for v in speed], ['2.00000','99'])
        self.assertEqual(c.speed, 2.)
        self.assertEqual(i['ai_attributes'], {'No':'0'})

    def test_case_sensitive_name_resolution(self):
        with self.assertRaises(s.ContractError):
            s.parse_case(synthetic().replace(b'Value="route"', b'Value="Route"'), 'x', 'boat')

    def test_provenance_and_route_identity(self):
        a = s.parse_case(synthetic(), 'x', 'boat')[0]
        b = s.parse_case(synthetic(), 'x', 'boat')[0]
        self.assertEqual(a,b)
        c = s.parse_case(synthetic().replace(b'No="9"', b'No="8"'), 'x', 'boat')[0]
        self.assertNotEqual(a['route_sha256'],c['route_sha256'])
        self.assertNotEqual(a['decoded_sha256'],c['decoded_sha256'])

    def test_missing_list_and_wrong_types_fail_closed(self):
        for data in [synthetic().replace(b'Name="route"', b'Name="missing"'),
                     synthetic().replace(b'Type="Vector3"', b'Type="Vector2"'),
                     synthetic().replace(b'Type="Int"', b'Type="Float"')]:
            with self.subTest(data=data), self.assertRaises(s.ContractError): s.parse_case(data, 'x','boat')

    def test_duplicate_list_and_absent_egg(self):
        for data,egg in [(synthetic().replace(b'</MarkerLists>',b'<List Name="route"/></MarkerLists>'),'boat'),
                         (synthetic(),'missing')]:
            with self.assertRaises(s.ContractError): s.parse_case(data, 'x',egg)

    def test_malformed_and_nonfinite(self):
        for data in [b'<Scene>', b'<!DOCTYPE Scene>'+synthetic(),
                     synthetic().replace(b'Value="0.0 0.0 0.0"',b'Value="nan 0 0"')]:
            with self.subTest(data=data), self.assertRaises(s.ContractError): s.parse_case(data,'x','boat')

    def test_absent_numeric_and_boolean_are_zero_after_config(self):
        _,_,c = s.parse_case(synthetic(),'x','boat')
        self.assertFalse(c.loop)
        self.assertFalse(c.trigger)
        self.assertEqual((c.on,c.off,c.rest_ticks,c.banking),(0.,0.,0,0.))

    def test_rest_signed_low32_conversion(self):
        rows = s.parse_case(synthetic(),'x','boat')[0]['parameters']
        c = s.Config.from_properties(rows+[{'Name':'Rest Time (sec)','Type':'Int','Value':'300'}])
        self.assertEqual(c.rest_ticks,9000)


class NumericalTests(unittest.TestCase):
    def test_independent_catmull_rom_rational_weights(self):
        # Independent closed-form polynomials, not an alternate call to weights().
        for u in [0.,.125,.25,.5,.75,1.]:
            expected = (-.5*u**3+u*u-.5*u,
                        1.5*u**3-2.5*u*u+1,
                        -1.5*u**3+2*u*u+.5*u,
                        .5*u**3-.5*u*u)
            self.assertEqual(s.weights(u),expected)
            self.assertEqual(sum(expected),1.)

    def test_collinear_interior_is_linear(self):
        p=s.PathState([(i*10.,0.,0.) for i in range(4)], replace(CONFIG,speed=10.))
        self.assertEqual(p.evaluate(1.25),(12.5,0.,0.))
        self.assertEqual(p.evaluate(1.5),(15.,0.,0.))

    def test_open_endpoints_clamp(self):
        p=s.PathState(POINTS,CONFIG)
        self.assertEqual(p.evaluate(0.),POINTS[0])
        self.assertEqual(p.evaluate(p.duration),POINTS[-1])
        self.assertEqual(p.evaluate(s.add(p.duration,5.)),POINTS[-1])

    def test_constant_speed_chord_timing_includes_open_closing_hold(self):
        p=s.PathState(POINTS,CONFIG)
        self.assertEqual(p.knots,[0.,1.5,3.5,5.])
        self.assertAlmostEqual(p.duration,5.+math.sqrt(52)/2.,places=5)
        self.assertGreater(p.duration,p.knots[-1])

    def test_variable_speed_uniform_knots_open_and_closed(self):
        p=s.PathState(POINTS,replace(CONFIG,const_speed=False))
        self.assertEqual(p.knots,[0.,1.25,2.5,3.75])
        self.assertEqual(p.closing_time,0.)
        q=s.PathState(POINTS,replace(CONFIG,const_speed=False,loop=True))
        self.assertAlmostEqual(q.duration,(10+math.sqrt(52))/2.,places=5)

    def test_loop_evaluator_wraps_at_equality(self):
        p=s.PathState(POINTS,replace(CONFIG,loop=True))
        self.assertEqual(p.evaluate(p.duration),POINTS[0])
        self.assertEqual(p.evaluate(s.mul(p.duration,2.)),POINTS[0])

    def test_sample_count_does_not_subdivide_route(self):
        a=s.PathState(POINTS,CONFIG)
        b=s.PathState(POINTS,replace(CONFIG,samples=4))
        self.assertEqual(a.knots,b.knots)
        for t in [0.,.5,1.,2.,4.]:self.assertEqual(a.evaluate(t),b.evaluate(t))

    def test_float32_and_degenerate_inputs(self):
        self.assertEqual(s.f32(.1),struct.unpack('<f',bytes.fromhex('cdcccc3d'))[0])
        for points in [[],POINTS[:3],[POINTS[0]]*4,
                       [(math.nan,0,0)]+POINTS[1:]]:
            with self.assertRaises(s.ContractError):s.PathState(points,CONFIG)
        with self.assertRaises(s.ContractError):s.div(1.,0.)

    def test_matrix_uses_original_right_row_even_for_vertical_direction(self):
        m=s.matrix((1.,2.,3.),(0.,.6,.8),(0.,1.,0.))
        self.assertEqual(m[0],[.8,.6,-0.,0.])
        self.assertEqual(m[3],[1.,2.,3.,1.])
        self.assertEqual(s.dot(m[0][:3],m[2][:3]),s.f32(.36))


class LifecycleTests(unittest.TestCase):
    def controller(self,**changes):return s.Controller(s.PathState(POINTS,replace(CONFIG,**changes)),0)

    def test_observer_is_required_even_without_trigger(self):
        c=self.controller()
        r=c.step(None)
        self.assertEqual(r['status'],'NO_OBSERVER')
        self.assertEqual(c.time,0.)

    def test_strict_trigger_hysteresis(self):
        self.assertFalse(s.trigger_state(False,9.,3.,6.))
        self.assertTrue(s.trigger_state(False,8.,3.,6.))
        self.assertTrue(s.trigger_state(True,36.,3.,6.))
        self.assertFalse(s.trigger_state(True,37.,3.,6.))
        self.assertFalse(s.trigger_state(False,20.,3.,6.))
        self.assertTrue(s.trigger_state(True,20.,3.,6.))

    def test_horizontal_trigger_pause_and_resume(self):
        c=self.controller(trigger=True)
        self.assertEqual(c.step((1.,100000.,0.))['status'],'ACTIVE')
        saved=c.time
        self.assertEqual(c.step((100.,0.,0.))['status'],'INACTIVE')
        self.assertEqual(c.time,saved)
        c.step(c.position)
        self.assertEqual(c.time,s.add(saved,s.f32(1/30)))

    def test_publish_precedes_advance(self):
        c=self.controller()
        r=c.step(POINTS[0])
        self.assertEqual(r['evaluated_time'],0.)
        self.assertEqual(r['position'],list(POINTS[0]))
        self.assertEqual(r['next_time'],s.f32(1/30))

    def test_loop_discards_overshoot_and_ignores_rest(self):
        c=self.controller(loop=True,rest=True,rest_ticks=100)
        c.time=s.sub(c.path.duration,.001)
        c.step(POINTS[0])
        self.assertEqual(c.time,0.)
        self.assertEqual(c.rest_counter,0)

    def test_nonloop_stays_active_at_endpoint(self):
        c=self.controller()
        c.time=c.path.duration
        r=c.step(POINTS[0])
        self.assertTrue(r['active'])
        self.assertEqual(c.time,c.path.duration)
        self.assertEqual(c.position,POINTS[-1])

    def test_rest_count_and_reset(self):
        c=self.controller(rest=True,rest_ticks=2)
        c.time=c.path.duration
        c.step(POINTS[0]);self.assertEqual(c.rest_counter,1)
        c.step(None);self.assertEqual(c.rest_counter,1)
        c.step(POINTS[0]);self.assertEqual(c.rest_counter,2)
        c.step(POINTS[0]);self.assertEqual((c.time,c.rest_counter),(0.,0))

    def test_independent_instances_and_banking_buffers(self):
        a=self.controller(trigger=True,banking=.5)
        b=self.controller(trigger=True,banking=.5)
        a.step(POINTS[0]);a.step(POINTS[0])
        self.assertEqual(b.time,0.)
        self.assertFalse(b.active)
        self.assertIsNot(a.history,b.history)
        self.assertIsNot(a.path,b.path)

    def test_banking_only_changes_up_row(self):
        c=self.controller(banking=.5,samples=4)
        c.time=1.6
        c.step(POINTS[0])
        self.assertTrue(all(math.isfinite(x) for x in c.up))
        self.assertNotEqual(c.bank_mean,0.)
        self.assertEqual(s.matrix(c.position,c.direction,c.up)[0],
                         [c.direction[2],c.direction[1],-c.direction[0],0.])

    def test_unknown_initializer_state_is_explicit(self):
        with self.assertRaises(s.ContractError):s.Controller(s.PathState(POINTS,CONFIG),1)
        with self.assertRaises(s.ContractError):s.ignored_output(ROOT/'ambient1'/'timeline.json')

    def test_deterministic_diagnostic(self):
        a=s.diagnostic({'source':'synthetic'},POINTS,CONFIG,[POINTS[0]]*50,initial_bank_flag=0)
        b=s.diagnostic({'source':'synthetic'},POINTS,CONFIG,[POINTS[0]]*50,initial_bank_flag=0)
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        self.assertEqual(a['runtime_validation'],'NOT_PERFORMED')


@unittest.skipUnless(os.environ.get('MASTER_RALLYE_PS2_INPUT'),'optional proprietary integration corpus')
class CanonicalIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.corpus=s.Corpus(os.environ['MASTER_RALLYE_PS2_INPUT'])

    def test_actual_instruction_basis_probe(self):
        elf=self.corpus.directory/'SLES_509.06'
        for segment in [0,1,3,7]:
            for u in [0.,.1,.125,.3,.5,.875]:
                coordinate=s.add(float(segment),s.f32(u))
                local=s.sub(coordinate,float(segment))
                self.assertEqual(s.weights(local),s.probe_basis_from_elf(elf,coordinate,segment))

    def test_six_named_cases(self):
        cases=[('ITALY3','barge',11),('TURKEYW','barge',10),('FRANCE1','boat1',6),
               ('FRANCEM','zeppelin',4),('SPAINS2','boat1',7),('SPAINS2','boat5',5)]
        for course,egg,count in cases:
            with self.subTest(course=course,egg=egg):
                i,p,c=self.corpus.case(course,egg)
                self.assertEqual(len(p),count)
                result=s.diagnostic(i,p,c,[p[0]]*120,initial_bank_flag=0)
                self.assertTrue(all(math.isfinite(x) for r in result['timeline'] for row in r['world_rows'] for x in row))
                self.assertEqual(result['identity']['owner'],'gaEntitySpline')

    def test_unknown_elf_rejected_before_execution(self):
        with self.assertRaises(s.ContractError):s.probe_basis_from_elf(Path(__file__),.5,0)

    def test_original_vtable_factory_and_model_matrix_writes(self):
        blob=(self.corpus.directory/'SLES_509.06').read_bytes()
        def word(va):return struct.unpack_from('<I',blob,va-0xff000)[0]
        self.assertEqual(word(0x473b10+0x2c),0x1a80e8)
        self.assertEqual(word(0x473b10+0x34),0x1a7ef8)
        self.assertEqual(word(0x15d378),0x24040130) # allocation delay slot: a0=0x130
        self.assertEqual(word(0x15d37c),0x0c069ec2) # JAL 001a7b08
        # Decode effective store addresses: the ELF uses a temporary row pointer
        # and SW zero for the homogeneous pads, as well as SWC1 for float values.
        regs=[0]*32
        regs[4],regs[5]=0x10000,0x20000
        en3d=0x30000
        stores=[]
        loads=0
        for va in range(0x1aa308,0x1aa3b8,4):
            w=word(va)
            op,rs,rt,imm=w>>26,(w>>21)&31,(w>>16)&31,w&65535
            signed=imm if imm<32768 else imm-65536
            if op==35:
                self.assertEqual(regs[rs]+signed,0x20050)
                regs[rt]=en3d
                loads+=1
            elif op==9:regs[rt]=regs[rs]+signed
            elif op==15:regs[rt]=imm<<16
            elif op in (43,57):stores.append(regs[rs]+signed-en3d)
        self.assertEqual(sorted(stores),list(range(0x20,0x60,4)))
        self.assertEqual(loads,4) # entity +0x50, reloaded for each matrix row


if __name__ == '__main__':unittest.main()
