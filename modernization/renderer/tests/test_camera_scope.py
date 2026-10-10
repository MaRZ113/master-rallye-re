from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inspect_camera_scope import ROOT, SITES, inspect, output_path, verify_sites


class SyntheticPE:
    image_base = 0x400000

    def __init__(self):
        self.offsets = {}
        self.blob = b''
        for va, _, signature, _ in SITES:
            self.offsets[va - self.image_base] = len(self.blob)
            self.blob += bytes.fromhex(signature)

    def offset(self, rva, n=1):
        return self.offsets[rva]


class CameraScopeTests(unittest.TestCase):
    def test_unknown_build_rejected_before_pe_read(self):
        with self.assertRaisesRegex(ValueError, 'Not pristine retail'):
            inspect(b'not a supported image')

    def test_return_and_late_camera_dependency_are_both_pinned(self):
        pe = SyntheticPE()
        rows = verify_sites(pe.blob, pe)
        by_role = {row['role']: row for row in rows}
        self.assertTrue(by_role['TraversalFullBody_RET8']['expected_bytes'].endswith('c20800'))
        late = by_role['PostTraversalCameraBuilderCall']
        self.assertEqual(late['va'], '0x0056E40A')
        self.assertEqual(late['rva'], '0x0016E40A')
        self.assertEqual(late['call_target'], '0x005614A0')
        self.assertEqual(by_role['RendererVtableFinalizeCamera']['expected_bytes'], '50e25600')
        self.assertEqual(by_role['ParticlesUseCurrentPose']['va'], '0x0056410E')
        self.assertEqual(by_role['ParticlesUseCurrentPose']['expected_bytes'], '81c388000000')
        self.assertEqual(by_role['ParticlesPassCurrentPoseToBillboardBuilder']['va'], '0x00564185')

    def test_every_anchor_rejects_mutation(self):
        pe = SyntheticPE()
        for va, _, _, _ in SITES:
            with self.subTest(va=hex(va)):
                bad = bytearray(pe.blob)
                bad[pe.offset(va - pe.image_base)] ^= 1
                with self.assertRaisesRegex(ValueError, 'Signature mismatch'):
                    verify_sites(bad, pe)

    def test_short_mapping_and_wrong_placement_rejected(self):
        pe = SyntheticPE()
        with self.assertRaisesRegex(ValueError, 'Signature mismatch'):
            verify_sites(pe.blob[:-1], pe)
        pe.image_base = 0x500000
        with self.assertRaisesRegex(ValueError, 'image base'):
            verify_sites(pe.blob, pe)

    def test_output_cannot_overwrite_binary_or_escape_renderer(self):
        for folder in ('research', '.analysis', 'scratch-camera'):
            self.assertEqual(output_path(ROOT / folder / 'scope.json'), ROOT / folder / 'scope.json')
        for path in (ROOT / 'MRallye.exe', ROOT.parent / 'scope.json', ROOT / 'research' / '..' / '..' / 'scope.json'):
            with self.subTest(path=str(path)), self.assertRaises(ValueError):
                output_path(path)
