"""Synthetic contracts: ambiguous COM offsets, exact-build rejection, safe output.

No game, old project tests, Ghidra database or runtime launch required.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

scan = module('scan_d3d8')
bridge = module('ghidra_readonly')

class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / '.analysis').mkdir(exist_ok=True)

    def test_wrong_build_fails_before_parse(self):
        with self.assertRaisesRegex(ValueError, 'Wrong build'):
            scan.require_build(b'not the game')

    def test_wrong_build_cli_has_no_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.analysis') as td:
            t = Path(td)
            binary = t / 'synthetic.exe'
            binary.write_bytes(b'wrong')
            out = t / 'output'
            r = subprocess.run([sys.executable, str(ROOT / 'tools/scan_d3d8.py'),
                                str(binary), '--output', str(out)], capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(out.exists())

    def test_output_boundaries(self):
        self.assertEqual(scan.guarded_output(ROOT / 'data'), ROOT / 'data')
        for path in (ROOT, ROOT.parent / 'research', ROOT / '..' / 'escape'):
            with self.assertRaises(ValueError):
                scan.guarded_output(path)
        self.assertEqual(bridge.guarded_output(ROOT / '.analysis/query'), ROOT / '.analysis/query')
        with self.assertRaises(ValueError):
            bridge.guarded_output(ROOT / 'data')

    def test_bridge_wrong_build_never_opens_project(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.analysis') as td:
            t = Path(td)
            binary = t / 'synthetic.exe'
            binary.write_bytes(b'wrong')
            out = t / 'raw'
            r = subprocess.run([sys.executable, str(ROOT / 'tools/ghidra_readonly.py'),
                '--binary', str(binary), '--output', str(out), '--install', str(t / 'absent'),
                '--java', str(t / 'absent-java'), '--project', str(t / 'absent-project')],
                capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn(b'Not the pristine retail executable', r.stderr)
            self.assertFalse(out.exists())

    def test_offsets_are_ambiguous(self):
        matches = scan.method_candidates(0x3c)
        self.assertEqual({m['method'] for m in matches}, {'CreateDevice', 'Present'})
        self.assertEqual(scan.method_candidates(0xc8)[0]['method'], 'SetRenderState')
        self.assertEqual(scan.method_candidates(0xf8)[0]['method'], 'GetTextureStageState')
        self.assertEqual(scan.method_candidates(0x130)[0]['method'], 'SetVertexShader')
        for bad in (-4, 3, 0x1000):
            self.assertEqual(scan.method_candidates(bad), [])

    def test_candidates_are_not_confirmed(self):
        code = bytes.fromhex('8b01ff503cc3')  # load vtable; call +3c; ret
        r = list(scan.decode_indirect(code, 0x1000))
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['evidence_grade'], 'HYPOTHESIS')
        self.assertEqual(len(r[0]['candidates']), 2)
        self.assertEqual(r, list(scan.decode_indirect(code, 0x1000)))

    def test_iat_and_register_calls_are_not_com_offset_proof(self):
        code = bytes.fromhex('ff1540000000ffd0c3')
        self.assertEqual(list(scan.decode_indirect(code, 0x1000)), [])

    def test_review_bytes_and_interface_are_checked(self):
        pe = types.SimpleNamespace(OPTIONAL_HEADER=types.SimpleNamespace(ImageBase=0x400000),
                                   get_offset_from_rva=lambda rva: rva)
        blob = bytes.fromhex('ff90c8000000')
        r = {'va':'0x00400000', 'bytes':blob.hex(), 'interface':'IDirect3DDevice8',
             'method':'SetRenderState', 'receiver_evidence':'synthetic receiver flow'}
        result = scan.validate_review(pe, blob, r)
        self.assertEqual(result['rva'], '0x00000000')
        self.assertEqual(result['vtable_slot'], 50)
        self.assertEqual(result['return_va'], '0x00400006')
        self.assertEqual(result['return_rva'], '0x00000006')
        with self.assertRaisesRegex(ValueError, 'Stale'):
            scan.validate_review(pe, b'\0' * len(blob), r)
        with self.assertRaises(ValueError):
            scan.validate_review(pe, blob, dict(r, method='GetRenderState'))
        with self.assertRaisesRegex(ValueError, 'Receiver'):
            scan.validate_review(pe, blob, dict(r, receiver_evidence=''))

    def test_review_cannot_promote_direct_iat_call(self):
        pe = types.SimpleNamespace(OPTIONAL_HEADER=types.SimpleNamespace(ImageBase=0x400000),
                                   get_offset_from_rva=lambda rva: rva)
        blob = bytes.fromhex('ff15c8000000')
        with self.assertRaises(ValueError):
            scan.validate_review(pe, blob, {'va':'0x00400000','bytes':blob.hex(),
                'interface':'IDirect3DDevice8','method':'SetRenderState','receiver_evidence':'invalid'})

    def test_committed_addresses_and_interfaces(self):
        data = json.loads((ROOT / 'data/d3d8-callmap.json').read_text())
        self.assertEqual(data['build_sha256'], scan.SHA256)
        sites = set()
        for row in data['calls']:
            self.assertNotIn(row['va'], sites)
            sites.add(row['va'])
            self.assertEqual(int(row['va'],16)-0x400000, int(row['rva'],16))
            self.assertEqual(int(row['return_va'],16), int(row['va'],16)+len(bytes.fromhex(row['bytes'])))
            self.assertEqual(int(row['return_va'],16)-0x400000, int(row['return_rva'],16))
            self.assertEqual(scan.METHODS[row['interface']][row['vtable_slot']], row['method'])

    def test_master_map_matches_reviewed_inventory(self):
        data = json.loads((ROOT / 'data/d3d8-callmap.json').read_text())
        master = json.loads((ROOT / 'data/renderer-map.json').read_text())
        self.assertEqual(master['build']['sha256'], scan.SHA256)
        self.assertEqual(master['apis'], data['methods'])
        passes = json.loads((ROOT / 'data/render-passes.json').read_text())
        self.assertEqual(master['passes'], passes['passes'])
        for row in passes['passes']:
            self.assertEqual(int(row['owner_va'],16)-0x400000, int(row['owner_rva'],16))

if __name__ == '__main__':
    unittest.main()
