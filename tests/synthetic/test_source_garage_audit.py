import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('garage_audit', Path(__file__).resolve().parents[2]/'tools/source_garage_audit.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def test_file_cannot_masquerade_as_source_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'file';p.write_bytes(b'input')
            result=audit.scan_game({'id':'a','path':str(p)},root)
            self.assertEqual(result['status'],'FAIL')

    def test_enumeration_error_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def denied(*args,**kwargs):
                kwargs['onerror'](PermissionError(13,'denied',str(root/'private')))
                return iter([])
            with patch.object(audit.os,'walk',denied):
                result=audit.scan_game({'id':'a','path':str(root)},root)
            self.assertEqual(result['status'],'WARN')
            self.assertIn('enumeration failed',result['errors'][0]['error'])

    def test_missing_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = audit.scan_game({'id':'a','path':'absent'},Path(tmp))
            self.assertEqual(report['status'],'MISSING INPUT')
            self.assertEqual(report['files'],[])

    def test_hashes_candidates_and_original_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'cars').mkdir()
            p=root/'cars'/'toyota.bin'; p.write_bytes(b'not a decoded model')
            before=p.stat(); result=audit.scan_game({'id':'a','path':str(root)},root)
            self.assertEqual(result['status'],'PASS')
            self.assertEqual(result['file_count'],1)
            self.assertEqual(result['levels']['L1'],'NOT TESTED')
            self.assertIn('model-candidate',result['files'][0]['roles'])
            self.assertEqual(p.read_bytes(),b'not a decoded model')
            self.assertEqual(p.stat().st_mtime_ns,before.st_mtime_ns)

    def test_limits_and_truncated_pe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'model.exe'; p.write_bytes(b'MZ'+bytes(62))
            r=audit.scan_game({'id':'a','path':str(root)},root,max_file_bytes=10)
            self.assertEqual(r['status'],'WARN'); self.assertEqual(r['file_count'],0)
            with self.assertRaises(ValueError):
                audit.scan_game({'id':'a','path':str(root)},root,max_total_bytes=10)
            with self.assertRaises(ValueError):
                audit.scan_game({'id':'a','path':str(root)},root,max_files=0)
            self.assertNotIn('pe_machine',audit.identity(p,root,100))

    def test_cannot_write_into_source_or_replace_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError): audit.output_guard(root/'output.json',[root])
            p=root/'old.json';p.write_text('{}')
            with self.assertRaises(ValueError): audit.output_guard(p,[])

    def test_output_identity_and_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'external';source.mkdir();(source/'a.pod').write_bytes(b'POD2')
            cfg=root/'roots.json';cfg.write_text(json.dumps({'schema':'source-garage-roots/1','base':str(root),'games':[{'id':'a','path':'external'}]}))
            result=audit.run(cfg,root/'full.json',root/'small.json',1)
            self.assertEqual(result['games'][0]['file_count'],1)
            self.assertEqual(result['games'][0]['signature_counts'],{'POD2':1})
            self.assertEqual(result['full_inventory']['sha256'],audit.hashlib.sha256((root/'full.json').read_bytes()).hexdigest())
            with self.assertRaises(ValueError): audit.run(cfg,root/'new.json',root/'new.json',1)

    def test_symlink_rejected_where_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'real';source.mkdir();(source/'x').write_bytes(b'x')
            link=root/'link'
            try: link.symlink_to(source,target_is_directory=True)
            except OSError: self.skipTest('symlink creation unavailable')
            with self.assertRaises(ValueError): audit.scan_game({'id':'x','path':str(link)},root)


if __name__=='__main__': unittest.main()
