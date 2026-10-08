"""TREEBLEND1: synthetic invariants, compact instruction oracles, optional corpus."""
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import foliage_runtime as f
from elf_query import SHA
import tngtool as t
import water_runtime as w


class Materials(unittest.TestCase):
    def test_registration_ids_are_independently_distinct(self):
        self.assertEqual(f.material_contract('$shader(tree)')['classification']['mode'], 6)
        self.assertEqual(f.material_contract('$shader(treeblend)')['classification']['mode'], 2)
        self.assertEqual(f.material_contract('$shader(object)')['classification']['mode'], 15)

    def test_authored_case_preserved_after_interner_folding(self):
        r = f.material_contract('$shader(TREEBLEND)')
        self.assertEqual(r['authored_shader'], 'TREEBLEND')
        self.assertEqual(r['interned_shader'], 'treeblend')

    def test_property_case_and_first_substring_semantics(self):
        self.assertIsNone(f.material_contract('$SHADER(tree)')['classification'])
        self.assertEqual(f.material_contract('$shaderExtra(tree) $shader(treeblend)')['interned_shader'], 'tree')

    def test_unknown_spelling_whitespace_and_missing_delimiter(self):
        for text in ('$shader(treeblnd)', '$shader( tree)', '$shader(tree )', '$shader(tree'):
            with self.subTest(text=text):
                self.assertIsNone(f.material_contract(text)['classification'])

    def test_alpha_marker_is_not_a_blend_mode_override(self):
        r = f.material_contract('bush $alphatest() $shader(treeblend)')
        self.assertTrue(r['alphatest_marker_present'])
        self.assertFalse(r['marker_is_final_gs_state'])
        self.assertEqual(f.state_contract(r['interned_shader'])['registers']['TEST']['decoded']['ATE'], 0)

    def test_geometry_and_mip_field_are_separate_from_opacity(self):
        r = f.material_contract('$shader(treeblend)')
        self.assertFalse(r['texture_name_override'])
        self.assertEqual(r['classification']['mip_factor_word'], 0x3e19999a)
        self.assertEqual(r['geometry_source'], 'AUTHORED_VISUAL_STRIPS')


class State(unittest.TestCase):
    def test_tree_cutout_greater64_keep_and_depth_write_allowed(self):
        fields = f.state_contract('tree')['registers']
        self.assertEqual({k:fields['TEST']['decoded'][k] for k in ('ATE','ATST','AREF','AFAIL')},
                         dict(ATE=1,ATST=6,AREF=64,AFAIL=0))
        self.assertEqual(fields['ZBUF']['decoded']['ZMSK'], 0)
        self.assertEqual(fields['GIF_TAG']['decoded']['ABE'], 0)

    def test_blend_source_alpha_no_test_and_depth_mask(self):
        c = f.state_contract('treeblend')
        self.assertEqual(c['blend_equation'], '(Cs-Cd)*As/128+Cd')
        self.assertEqual(c['registers']['ALPHA']['decoded'], dict(A=0,B=1,C=0,D=1,FIX=0))
        self.assertEqual(c['registers']['GIF_TAG']['decoded']['ABE'], 1)
        self.assertEqual(c['registers']['TEST']['decoded']['ATE'], 0)
        self.assertEqual(c['registers']['ZBUF']['decoded']['ZMSK'], 1)

    def test_negative_object_test_and_blend_are_disabled(self):
        c = f.state_contract('object')['registers']
        self.assertEqual(c['TEST']['decoded']['ATE'], 0)
        self.assertEqual(c['GIF_TAG']['decoded']['ABE'], 0)
        self.assertEqual(c['ZBUF']['decoded']['ZMSK'], 0)

    def test_depth_enable_and_frame_are_never_guessed(self):
        for shader in f.SHADERS:
            c = f.state_contract(shader)
            self.assertEqual(c['registers']['TEST']['decoded']['ZTE'], 'INHERITED')
            self.assertEqual(c['registers']['TEST']['decoded']['ZTST'], 2)
            self.assertIsNone(c['registers']['TEST']['result_word'])
            self.assertIn('FRAME', c['inherited_scope'])

    def test_supplied_depth_enable_survives_every_mode(self):
        for shader in f.SHADERS:
            for zte in (0,1):
                c = f.state_contract(shader, {'TEST':zte<<16})
                self.assertEqual(c['registers']['TEST']['decoded']['ZTE'], zte)
                self.assertEqual(c['input_provenance'], 'EXPLICIT_SYNTHETIC_INHERITED_WORDS')

    def test_texture_alpha_is_selected_independent_of_test_and_blend(self):
        for shader in f.SHADERS:
            self.assertEqual(f.state_contract(shader)['registers']['TEX0']['decoded']['TCC'], 1)
            self.assertEqual(f.state_contract(shader)['registers']['TEX0']['decoded']['TFX'], 0)

    def test_actual_register_is_fba_not_pabe(self):
        for shader in f.SHADERS:
            c = f.state_contract(shader)
            self.assertEqual(c['registers']['FBA']['decoded']['FBA'], 0)
            self.assertNotIn('PABE', c['registers'])
            self.assertIn('PABE', c['inherited_scope'])

    def test_only_one_effective_primitive_stream(self):
        for shader in f.SHADERS:
            c = f.state_contract(shader)
            self.assertEqual(c['effective_geometry_streams'], 1)
            self.assertTrue(c['secondary_gif_registers'].startswith('0xfff'))

    def test_masks_preserve_unowned_register_bits(self):
        for shader in f.SHADERS:
            for reg,(mask,bits) in f.state_operations(shader).items():
                c = f.state_contract(shader, {reg:f.MASK64})['registers'][reg]
                result = int(c['result_word'],16)
                self.assertEqual(result & mask, mask)
                self.assertEqual(result & ~mask & f.MASK64, bits & ~mask)

    def test_unsupported_inputs_fail_closed(self):
        for bad in ({'TEST':-1}, {'TEST':2**64}, {'TEST':True}, {'TEST':.5}, {'FRAME':0}):
            with self.assertRaises(t.FormatError): f.state_contract('tree',bad)
        with self.assertRaises(t.FormatError): f.state_contract('unknown')


class Vertex(unittest.TestCase):
    def test_channel_order_and_loader_clamp(self):
        c = f.vertex_color(0x211a00ff)
        self.assertEqual(c['source_rgba'], (33,26,0,255))
        self.assertEqual(c['runtime_rgba_bytes'], (33,26,2,254))
        self.assertEqual(c['cached_rgba_f32'], (16.5,13.,1.,127.))
        self.assertEqual(c['vu_rgba_integers'], (16,13,1,127))

    def test_all_source_byte_normalized_round_trips(self):
        for byte in range(256):
            normalized = f.d.div(float(byte),255.)
            recovered = f.d.mul(normalized,255.)
            self.assertEqual(recovered,float(byte))
            c = f.vertex_color(byte*0x01010101)
            self.assertEqual(c['vu_rgba_integers'], (min(254,max(2,byte))//2,)*4)

    def test_color_input_validation(self):
        for bad in (-1,2**32,False,math.nan):
            with self.assertRaises(t.FormatError): f.vertex_color(bad)

    def test_source_52byte_attributes_independently_placed(self):
        payload = struct.pack('<3I4fI',0xd00d,2,0x539,0.,0.,0.,1.,1)
        payload += struct.pack('<3fII4f4f',1.,0.,0.,1,0x10203040,.25,.5,.75,1.,2.,3.,4.,1.)
        payload += struct.pack('<2I',1,0)+struct.pack('<I',100)
        scene = w.decode_scene(payload)
        v = f.source_vertex(scene,0)
        self.assertEqual(v['position'], (2.,3.,4.))
        self.assertEqual(v['normal'], (1.,0.,0.))
        self.assertEqual(v['control'],1)
        self.assertEqual(v['uv4'],(.25,.5,.75,1.))
        self.assertEqual(v['color']['source_rgba'],(16,32,48,64))

    def test_nonfinite_normal_is_rejected(self):
        data = struct.pack('<3I4fI',0xd00d,2,0x539,0.,0.,0.,1.,1)
        data += struct.pack('<3fII4f4f',math.nan,0.,0.,0,0xffffffff,0.,0.,0.,0.,2.,3.,4.,1.)
        data += struct.pack('<2I',1,0)+struct.pack('<I',100)
        with self.assertRaises(t.FormatError): f.source_vertex(w.decode_scene(data),0)


class Evidence(unittest.TestCase):
    def test_frozen_compact_handlers_and_case_matrix(self):
        matrix = json.loads((f.ROOT/'treeblend1/foliage-material-matrix.json').read_text())
        rows = matrix['cases']
        self.assertEqual([r['case_id'] for r in rows],list('ABCDE'))
        self.assertEqual([r['source_faces'] for r in rows],[256,64,80,139,24])
        self.assertTrue(all(r['runtime_validation']=='NOT_PERFORMED' for r in rows))
        for row in rows:
            shader = row['material_contract']['interned_shader']
            self.assertEqual(row['render_contract'],f.state_contract(shader))

    def test_instruction_probe_is_small_and_original_hash_locked(self):
        probe = json.loads((f.ROOT/'treeblend1/instruction-evidence.json').read_text())
        self.assertEqual(probe['canonical_elf_sha256'], SHA)
        # Includes both foliage GS branches and the independent opaque control.
        self.assertLess(sum(len(x['instructions']) for x in probe['cpu_windows']),750)
        self.assertTrue(all(row['original_word'].startswith('0x') for block in probe['cpu_windows'] for row in block['instructions']))

    def test_json_determinism_without_original_state_inputs(self):
        a = json.dumps([f.state_contract(s) for s in f.SHADERS],sort_keys=True,allow_nan=False)
        b = json.dumps([f.state_contract(s) for s in f.SHADERS],sort_keys=True,allow_nan=False)
        self.assertEqual(a,b)

    def test_output_cannot_escape_research_directory(self):
        with self.assertRaises(t.FormatError): f.local_output(f.ROOT/'treeblend1/proprietary.json')
        with self.assertRaises(t.FormatError): f.local_output(f.ROOT/'data/treeblend1')


class CanonicalElf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not root: raise unittest.SkipTest('Requires canonical MASTER_RALLYE_PS2_INPUT')
        cls.binary = (Path(root)/'SLES_509.06').read_bytes()
        if t.sha(cls.binary) != SHA:
            raise t.FormatError('Canonical ELF mismatch')

    def test_original_instruction_words_and_vu_pairs(self):
        p = json.loads((f.ROOT/'treeblend1/instruction-evidence.json').read_text())
        for anchor in p['data_anchors']:
            offset = int(anchor['address'],16)-0xff000
            raw = bytes.fromhex(anchor['raw_hex'])
            self.assertEqual(self.binary[offset:offset+len(raw)],raw)
        for block in p['cpu_windows']:
            for r in block['instructions']:
                va = int(r['address'],16)
                self.assertEqual(struct.unpack_from('<I',self.binary,va-0xff000)[0],int(r['original_word'],16))
        for r in p['vu_pairs']:
            va = int(r['elf_va'],16)
            self.assertEqual(struct.unpack_from('<2I',self.binary,va-0xff000),
                             (int(r['lower_word'],16),int(r['upper_word'],16)))


class CanonicalMeshes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = os.environ.get('MASTER_RALLYE_PS2_INPUT')
        if not root: raise unittest.SkipTest('Requires canonical PS2 PackFS corpus')
        cls.result = f.inspect_cases(Path(root))

    def test_original_material_binding_and_source_counts(self):
        frozen = json.loads((f.ROOT/'treeblend1/foliage-material-matrix.json').read_text())
        for actual,expected in zip(self.result['cases'],frozen['cases']):
            for key in ('case_id','node_offset','material_offset','material','source_hash','source_faces','attributes'):
                self.assertEqual(actual[key],expected[key])
            self.assertEqual(actual['geometry']['component_sizes'],expected['geometry']['component_sizes'])

    def test_original_gxi_hash_and_stored_alpha(self):
        frozen = json.loads((f.ROOT/'treeblend1/foliage-material-matrix.json').read_text())
        self.assertEqual(self.result['textures'],frozen['textures'])


class CanonicalPc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = ('MASTER_RALLYE_PS2_INPUT', 'MASTER_RALLYE_PC_INPUT', 'MASTER_RALLYE_COURSE_SDK')
        values = [os.environ.get(name) for name in names]
        if not all(values):
            raise unittest.SkipTest('Requires canonical PS2/PC and read-only Course SDK roots')
        cls.pc_root = Path(values[1])
        cls.result = f.inspect_cases(*(Path(value) for value in values))

    def test_paired_pixels_and_source_sizes(self):
        textures = {Path(row['path']).stem:row for row in self.result['pc_texture_evidence']}
        for name in ('pinus2-tga','pinetree-tga'):
            self.assertTrue(textures[name]['row_policy_comparisons']['flip-vertical']['identical_ps2_stored_rgba'])
            self.assertFalse(textures[name]['row_policy_comparisons']['preserve-stored']['identical_ps2_stored_rgba'])
        self.assertEqual(textures['bush01-tga']['dimensions'],[128,128])
        self.assertFalse(textures['bush01-tga']['same_dimensions'])
        self.assertEqual(textures['shrubtrig2-tga']['status'],'NOT_FOUND_AT_PAIRED_MATERIAL_PATH')

    def test_pc_flags_against_direct_bytes_and_triangle_multiplicity(self):
        cases = {row['case_id']:row for row in self.result['cases']}
        for case_id, draw_index, unique, repeats in (('C',283,80,4),('E',54,24,2)):
            case = cases[case_id]
            draw, = case['pc']['selected_draw_attributes']
            self.assertEqual(draw['draw_index'],draw_index)
            self.assertEqual(draw['exact_unsigned_unique_triangles'],unique)
            self.assertEqual(draw['triangle_multiplicity_histogram'],{repeats:unique})
            self.assertEqual(draw['unsigned_triangles_with_both_windings'],unique)
            binary = (self.pc_root/case['pc']['source']['path']).read_bytes()
            self.assertEqual(list(binary[draw['core_offset']+0x20:draw['core_offset']+0x24]),[1,1,1,1])
            self.assertEqual(struct.unpack_from('<I',binary,draw['core_offset']+0x24)[0],3)


if __name__ == '__main__': unittest.main()
