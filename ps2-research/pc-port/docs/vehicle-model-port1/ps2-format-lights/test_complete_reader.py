import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('complete_reader',HERE/'complete_reader.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def source(tag=102,values=(.4,.2),sentinel=0xffffffff):
    header=struct.pack('<8I',0xd00d,2,0x539,0,0,0,0,1)
    vertex=struct.pack('<13I',0,0,0,1,0xff112233,0,0,0,0,0,0,0,0x3f800000)
    tree=struct.pack('<2I',1,0)
    trailer=struct.pack('<I',tag)
    if tag==102:trailer+=struct.pack('<2fI',*values,sentinel)
    return header+vertex+tree+trailer


class ReaderContract(unittest.TestCase):
    def test_proved_102_tree_and_original_bytes(self):
        payload=source();digest=hashlib.sha256(payload).hexdigest()
        scene,trailer=c.decode_complete(payload)
        self.assertIs(scene.payload,payload)
        self.assertEqual(hashlib.sha256(scene.payload).hexdigest(),digest)
        self.assertEqual(scene.end,92)
        self.assertEqual(scene.node_counts,{1:1})
        self.assertEqual(trailer['tag'],102)
        self.assertEqual(trailer['sentinel_offset'],104)
        self.assertEqual(trailer['consumer'],'0x003947b0')

    def test_two_fields_preserve_source_values(self):
        _,trailer=c.decode_complete(source(values=(.75,.125)))
        self.assertEqual(trailer['values'],[.75,.125])
        self.assertEqual(trailer['value_fields'],['cylinder+0x14','cylinder+0x18'])

    def test_eof_sentinel_supported(self):
        scene,trailer=c.decode_complete(source(0xffffffff))
        self.assertEqual(trailer['kind'],'EXACT_EOF_SENTINEL')
        self.assertEqual(scene.end,92)

    def test_known_101_preserves_opaque_collision_trailer(self):
        scene,trailer=c.decode_complete(source(101)+b'opaque')
        self.assertEqual(trailer['unparsed_bytes'],6)
        self.assertEqual(trailer['kind'],'CONVEX_AUXILIARY_TRAILER_NOT_DECODED')
        self.assertEqual(scene.payload[-6:],b'opaque')

    def test_unknown_terminal_fails(self):
        with self.assertRaises(c.t.FormatError):c.decode_complete(source(104))

    def test_bad_or_missing_sentinel_fails(self):
        for b in (source(sentinel=100),source()[:-1],source()+b'\0'):
            with self.subTest(bytes=len(b)),self.assertRaises(c.t.FormatError):c.decode_complete(b)

    def test_nonfinite_parameters_fail(self):
        for value in (float('nan'),float('inf'),-float('inf')):
            with self.subTest(value=value),self.assertRaises(c.t.FormatError):
                c.decode_complete(source(values=(value,.2)))

    def test_unsupported_visual_node_never_skipped(self):
        b=bytearray(source());struct.pack_into('<I',b,84,4)
        with self.assertRaises(c.t.FormatError):c.decode_complete(bytes(b))

    def test_truncated_vertices_fail(self):
        with self.assertRaises(c.t.FormatError):c.decode_complete(source()[:48])

    def test_existing_reader_still_rejects_102(self):
        with self.assertRaises(c.t.FormatError):c.r.decode_vehicle(source())


class FrozenCorpusEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.evidence=json.loads((HERE/'complete-inventory.json').read_text())

    def test_all29_supported_with_proved_trailers(self):
        self.assertEqual(self.evidence['ps2_complete_count'],29)
        self.assertEqual(self.evidence['decoder_counts'],{'SUPPORTED_PROVED_GRAMMAR':29})
        self.assertEqual(self.evidence['trailer_counts'],{'102':25,'101':3,'4294967295':1})

    def test_wooldand_and_ps2_forester_are_distinct(self):
        rows={r['family']:r for r in self.evidence['inventory']}
        self.assertEqual(rows['WOOLDAND']['pc_pair']['path'],'Forester/complete.dx')
        self.assertEqual(rows['WOOLDAND']['pc_pair']['ps2_triangle_matches'],978)
        self.assertEqual(rows['FORESTER']['pc_pair'],'NO_VERIFIED_PC_COUNTERPART')
        self.assertNotEqual(rows['WOOLDAND']['sha256'],rows['FORESTER']['sha256'])

    def test_known_wooldand_faces_and_tata_boundary(self):
        rows={r['family']:r for r in self.evidence['inventory']}
        self.assertEqual(rows['WOOLDAND']['source_triangles'],4261)
        self.assertEqual(rows['WOOLDAND']['mesh_count'],17)
        self.assertEqual(rows['TATA']['trailer']['offset'],352800)
        self.assertEqual(rows['TATA']['source_triangles'],4620)


if __name__=='__main__':unittest.main()
