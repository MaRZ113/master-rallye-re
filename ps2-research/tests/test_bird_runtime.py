"""AMBIENT2 synthetic invariants, original instruction windows, optional corpus.

No original point positions, PSB payload or GXI image is embedded as a fixture.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import bird_runtime as b
import tngtool as t


def scene(extra='',lists=None,refs='FlightList'):
    if lists is None:
        lists='<List Name="FlightList"><Marker No="9"><Value Name="Marker Type" Type="String" Value="Flight"/><Value Name="Marker Pos" Type="Vector3" Value="1 2 3"/><Value Name="Marker Dir" Type="Vector3" Value="0 0 1"/></Marker></List><List Name="MillList"/>'
    return ('<Scene><MarkerLists>'+lists+'</MarkerLists><EggLists_Version4><List Name="IConManager"><Egg Name="birds"><AI_List><AI No="0"><Value Name="AI Name" Type="String" Value="gaAnimals_BirdManager"/><gaAnimals_BirdManager><Value Name="Flight MarkerList" Type="String" Value="'+refs+'"/>'+extra+'</gaAnimals_BirdManager></AI></AI_List></Egg></List></EggLists_Version4></Scene>').encode()


class Authored(unittest.TestCase):
    def parse(self,*args,**kwargs): return b.parse_authored(scene(*args,**kwargs),'SYNTHETIC')['managers'][0]

    def test_exact_owner_name_no_silent_normalization(self):
        self.assertEqual(len(b.parse_authored(scene(),'SYNTHETIC')['managers']),1)
        self.assertEqual(b.parse_authored(scene().replace(b'gaAnimals_BirdManager',b'gaAnimals_Birdmanager'),'SYNTHETIC')['managers'],[])

    def test_duplicate_properties_preserved_and_brown_write_bug(self):
        m=self.parse('<Value Name="Bird Brown" Type="Bool" Value="False"/><Value Name="Bird Brown" Type="Bool" Value="True"/>')
        self.assertEqual(m['bird_brown_authored'],['False','True'])
        self.assertTrue(m['bird_brown_loaded'])

    def test_first_typed_number_is_used_and_upper_clamp_only(self):
        m=self.parse('<Value Name="Rnd Fly" Type="Int" Value="21"/><Value Name="Rnd Fly" Type="Int" Value="3"/><Value Name="Rnd Mil" Type="Int" Value="-2"/>')
        self.assertEqual(m['resolved_config']['Rnd Fly'],10)
        self.assertEqual(m['resolved_config']['Rnd Mil'],-2)

    def test_missing_and_empty_list_are_distinct(self):
        m=self.parse(refs='flightlist')
        self.assertIsNone(m['lists']['flight'])
        self.assertEqual(m['lists']['milling'],[])

    def test_marker_no_does_not_sort_source_order(self):
        first=scene().decode().split('<Marker No="9">')[1].split('</Marker>')[0]
        m=self.parse(lists='<List Name="FlightList"><Marker No="9">'+first+'</Marker><Marker No="1">'+first.replace('1 2 3','4 5 6')+'</Marker></List>')
        self.assertEqual([x['position'] for x in m['lists']['flight']],[(1.,2.,3.),(4.,5.,6.)])

    def test_duplicate_points_are_not_deduplicated(self):
        data=scene();marker=data.split(b'<Marker No="9">')[1].split(b'</Marker>')[0]
        data=data.replace(b'</Marker>',b'</Marker><Marker No="8">'+marker+b'</Marker>',1)
        m=b.parse_authored(data,'SYNTHETIC')['managers'][0]
        self.assertEqual(len(m['lists']['flight']),2)

    def test_duplicate_list_fails_closed(self):
        with self.assertRaises(b.Error): self.parse(lists='<List Name="FlightList"/><List Name="FlightList"/>')

    def test_malformed_wrong_version_nonfinite_and_entities(self):
        for raw in (b'<Scene>',b'<Scene/>',scene().replace(b'1 2 3',b'nan 2 3'),b'<!DOCTYPE Scene>'+scene()):
            with self.subTest(raw=raw[:20]),self.assertRaises(b.Error): b.parse_authored(raw,'SYNTHETIC')

    def test_compact_contract_contains_no_point_array(self):
        m=b.compact_authored(b.parse_authored(scene(),'SYNTHETIC'))['managers'][0]
        r=m['lists']['flight']
        self.assertEqual((r['runtime_record_stride'],r['position_offset'],r['homogeneous_w_offset']),(80,64,76))
        self.assertNotIn('position',r)


class Randomness(unittest.TestCase):
    def test_positive_state_independent_modular_oracle(self):
        rng=b.RandomStream(12345);state=12345
        for _ in range(1000):
            state=(48271*state)%2147483647
            self.assertEqual(rng.unit(),(state&0xffffff)/2**24)
            self.assertEqual(rng.state,state)

    def test_output_is_low24_not_modulus_division(self):
        rng=b.RandomStream(12345);u=rng.unit()
        self.assertEqual(rng.state,595905495)
        self.assertNotEqual(u,rng.state/2147483647)

    def test_zero_and_signed_inputs_retain_defined_integer_operations(self):
        r=b.RandomStream(0);r.unit();self.assertEqual(r.state,2147483647)
        for state in (2**31,2**32-1):
            rng=b.RandomStream(state)
            self.assertTrue(0<=rng.unit()<1)

    def test_invalid_state_rejected_without_invented_seed(self):
        for state in (-1,2**32,True,1.5,None):
            with self.assertRaises(b.Error):b.RandomStream(state)

    def test_integer_upper_exclusive_and_empty_range(self):
        rng=b.RandomStream(12345);values=[rng.integer(0,10) for _ in range(200)]
        self.assertEqual(set(values),set(range(10)))
        self.assertEqual(rng.integer(4,4),4)
        with self.assertRaises(b.Error):rng.integer(2,1)


class Selection(unittest.TestCase):
    def test_horizontal_nearest_ignores_height(self):
        self.assertEqual(b.nearest_marker([(1,900,0),(2,0,0)],(0,0,0)),0)

    def test_cached_half_open_window_is_not_global_closest(self):
        points=[(100+i,0,0) for i in range(12)];points[10]=(0,0,0)
        self.assertEqual(b.nearest_marker(points,(0,0,0)),10)
        self.assertEqual(b.nearest_marker(points,(0,0,0),5),0)

    def test_tie_is_first_in_scanned_source_order(self):
        self.assertEqual(b.nearest_marker([(1,0,0),(-1,0,0)],(0,0,0)),0)

    def test_random_positive_offset_is_clamped(self):
        base,selected=b.spawn_marker([(3,0,0),(1,0,0)],(0,0,0),-1,b.RandomStream(12345))
        self.assertEqual((base,selected),(1,1))

    def test_strict_spawn_annulus(self):
        self.assertFalse(b.flight_gate(100,10,20));self.assertFalse(b.flight_gate(400,10,20))
        self.assertTrue(b.flight_gate(225,10,20))

    def test_empty_invalid_index_and_nonfinite_fail_closed(self):
        for points,observer,index in (([],(0,0,0),-1),([(0,0,0)],(0,0,0),1),([(math.inf,0,0)],(0,0,0),-1)):
            with self.assertRaises(b.Error):b.nearest_marker(points,observer,index)


class Motion(unittest.TestCase):
    def test_initializer_uses_six_random_draws(self):
        rng=b.RandomStream(12345);bird=b.FlyBird((0,10,0));bird.initialize((100,10,0),rng)
        self.assertEqual(rng.calls,6);self.assertTrue(bird.direction[0]<0)
        self.assertTrue(15<=bird.speed<30)
        self.assertAlmostEqual(sum(x*x for x in bird.direction),1,places=6)

    def test_origin_equal_observer_has_vertical_direction(self):
        bird=b.FlyBird((0,0,0));bird.initialize((0,0,0),b.RandomStream(12345))
        self.assertAlmostEqual(bird.direction[1],1,places=6)
        self.assertEqual((bird.direction[0],bird.direction[2]),(0,0))

    def test_current_direction_times_total_travel_not_integrated_velocity(self):
        bird=b.FlyBird((1,2,3),direction=(1,.1,0),speed=20,travel=10)
        old_y=bird.origin[1]+bird.direction[1]*bird.travel
        result=bird.step(b.RandomStream(12345))
        self.assertEqual(result[1],b.add(2,b.mul(bird.direction[1],bird.travel)))
        self.assertNotEqual(result[1],b.add(old_y,b.mul(bird.direction[1],b.div(bird.speed,30))))

    def test_y_threshold_stops_only_rise_random_draw(self):
        rng=b.RandomStream(12345);bird=b.FlyBird((0,0,0),direction=(1,b.f32(.35),0))
        bird.step(rng);self.assertEqual(rng.calls,1);self.assertEqual(bird.direction[1],b.f32(.35))

    def test_original_fpu_windows_independently_check_operation_order(self):
        probes=json.loads((b.ROOT/'ambient2/instruction-probes.json').read_text())['windows']
        def probe(name,fpu,mem):
            d=probes[name];words=[int(x,16) for x in d['words']]
            self.assertEqual(hashlib.sha256(struct.pack('<'+'I'*len(words),*words)).hexdigest(),d['sha256'])
            return b.probe_scalar(words,int(d['start'],16),fpu,mem)[1]
        rng=b.RandomStream(12345);dy=rng.real(.001,.05);accel=rng.real(.1,2.5)
        rise=probe('rise',{0:dy},{0x1c:b.f32(.1)})
        speed=probe('speed_travel',{0:accel,20:100.},{0x28:20.,0x2c:10.})
        bird=b.FlyBird((0,0,0),direction=(1,.1,0),speed=20,travel=10);bird.step(b.RandomStream(12345))
        self.assertEqual(bird.direction[1],rise[0x1c]);self.assertEqual(bird.speed,speed[0x28]);self.assertEqual(bird.travel,speed[0x2c])

    def test_invalid_xyz_and_nonfinite_rejected(self):
        for origin in ((0,0),(0,0,math.nan)):
            with self.assertRaises(b.Error):b.FlyBird(origin)

    def test_trace_is_repeatable_and_explicitly_synthetic(self):
        first=b.trace((0,10,0),(100,10,0),12345,15)
        self.assertEqual(first,b.trace((0,10,0),(100,10,0),12345,15))
        fixture=json.loads((b.ROOT/'ambient2/synthetic-flight-trace.json').read_text())
        self.assertEqual(json.loads(json.dumps(first)),fixture)
        self.assertIn('SYNTHETIC',first['inputs']);self.assertEqual(first['runtime_validation'],'NOT_PERFORMED')


class Visual(unittest.TestCase):
    def test_three_frame_cycle_every_five_owner_invocations(self):
        switch=b.BankSwitcher();frames=[switch.step() for _ in range(15)]
        self.assertEqual(frames,[0]*4+[1]*5+[2]*5+[0])

    def test_missing_visual_freezes_switcher(self):
        switch=b.BankSwitcher(2,4);self.assertEqual(switch.step(False),2);self.assertEqual(switch.counter,4)

    def test_camera_y_locked_basis_not_velocity_orientation(self):
        rows=b.billboard_rows([(1,0,0),(0,1,0),(0,.6,.8)])
        self.assertEqual(rows[1],[0,b.f32(.1),0,0])
        self.assertEqual(rows[0][0],b.mul(b.f32(.8),b.f32(.1)))
        self.assertEqual(rows[2][1],0)

    def test_vertical_camera_fallback_keeps_scale(self):
        rows=b.billboard_rows([(1,0,0),(0,0,1),(0,1,0)])
        self.assertEqual(rows[2],[b.f32(.1),0,0,0]);self.assertEqual(rows[0],[0,0,-b.f32(.1),0])

    def test_mode8_separates_blend_test_depth_enable_and_write(self):
        c=b.gs_state()
        self.assertEqual(c['ALPHA']['fields'],dict(A=0,B=1,C=0,D=1,FIX=0))
        self.assertEqual(c['TEST']['fields']['ATE'],0);self.assertEqual(c['PRIM']['ABE'],1)
        self.assertEqual(c['TEST']['fields']['ZTE'],'INHERITED');self.assertEqual(c['ZBUF']['fields']['ZMSK'],1)
        self.assertEqual(c['TEX0']['fields']['TCC'],1);self.assertEqual(c['TEX0']['fields']['TFX'],0)

    def test_asset_metadata_is_four_alternative_quads_not_eight_live_faces(self):
        d=json.loads((b.ROOT/'ambient2/bird-resource-inventory.json').read_text())
        banks=[r for r in d['resources'] if r['type']=='SPRITE_BANK']
        self.assertEqual(len(banks),2)
        for bank in banks:
            self.assertEqual([m['key_u32'] for m in bank['mapping']],[0,1,2,3])
            self.assertEqual([image['source_triangle_count'] for image in bank['images']],[2]*4)

    def test_original_data_outputs_cannot_escape_ignored_root(self):
        with self.assertRaises(b.Error):b.local_output(b.ROOT/'ambient2/forbidden.json')
        with patch.object(Path,'exists',return_value=True),self.assertRaises(b.Error):
            b.local_output(b.ROOT/'data/ambient2/existing.json')


@unittest.skipUnless(os.getenv('MASTER_RALLYE_PS2_INPUT'),'Canonical PS2 corpus unavailable; set MASTER_RALLYE_PS2_INPUT')
class Corpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=Path(os.environ['MASTER_RALLYE_PS2_INPUT']);cls.corpus=b.s.Corpus(cls.directory)

    def test_reextract_all36_against_frozen_counts_hashes_and_references(self):
        actual=b.corpus_inventory(self.directory)
        self.assertEqual(actual,json.loads((b.ROOT/'ambient2/bird-course-inventory.json').read_text()))
        self.assertEqual(actual['totals'],dict(course_pairs=36,managers=36,flight_points=542,milling_points=55,local_milling_lists=10))
        cases={c['course']:c['managers'][0] for c in actual['courses']}
        self.assertEqual([cases[c]['lists']['flight']['authored_point_count'] for c in ('FRANCE1','SPAINW','TURKEY3','ITALYS4')],[10,3,12,6])
        self.assertFalse(cases['TURKEY3']['lists']['milling']['present'])

    def test_source_instruction_windows_match_original_elf_bytes(self):
        raw=(self.directory/'SLES_509.06').read_bytes()
        self.assertEqual(t.sha(raw),b.s.ELF_SHA)
        for probe in json.loads((b.ROOT/'ambient2/instruction-probes.json').read_text())['windows'].values():
            data=raw[int(probe['start'],16)-0xff000:int(probe['end_exclusive'],16)-0xff000]
            self.assertEqual(t.sha(data),probe['sha256'])

    def test_original_bird_resources_match_frozen_parser_and_bank_evidence(self):
        self.assertEqual(b.resource_inventory(self.directory),json.loads((b.ROOT/'ambient2/bird-resource-inventory.json').read_text()))

    def test_upload_commands_and_program_bytes_are_separate(self):
        raw=(self.directory/'SLES_509.06').read_bytes()
        contract=json.loads((b.ROOT/'ambient2/upload-evidence.json').read_text());chunks=[]
        for c in contract['chunks']:
            command_va=int(c['command_va'],16)
            self.assertEqual(struct.unpack_from('<I',raw,command_va-0xff000)[0],int(c['word'],16))
            self.assertEqual(c['source_va'],command_va+4)
            data=raw[c['source_va']-0xff000:c['source_va']-0xff000+c['count']*8]
            self.assertEqual(t.sha(data),c['sha256']);chunks.append(data)
        self.assertEqual(t.sha(b''.join(chunks)),contract['combined_program_sha256'])


if __name__=='__main__':unittest.main()
