import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('course_coverage_report', Path(__file__).parents[1] / 'tools/course_coverage_report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def ledger(rows):
    return {'type': 'atmosphere_coverage_ledger', 'schema': 1, 'frame': 1, 'overflow': False, 'rows': rows}


def row(course, sha, verdict, tris, reason='', material=''):
    return {'course': course, 'texture_sha256': sha, 'material': material, 'verdict': verdict, 'reason': reason,
            'fvf': 0x142, 'category': 0, 'draws': 1, 'triangles': tris, 'frames': 1}


class CoverageReportTests(unittest.TestCase):
    def test_merges_sessions_and_lists_only_open_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp) / 'logs'; logs.mkdir()
            (logs / 'coverage-1.json').write_text(json.dumps(ledger([
                row('Italy1', 'a' * 64, 'Lit', 300, material='rock-tga'),
                row('Italy1', 'b' * 64, 'Excluded', 100, 'resolver_excluded_material', 'pinus-tga')])), encoding='utf-8')
            (logs / 'coverage-2.json').write_text(json.dumps(ledger([
                row('Italy1', 'b' * 64, 'Excluded', 100, 'resolver_excluded_material', 'pinus-tga')])), encoding='utf-8')
            (logs / 'unrelated.json').write_text('{}', encoding='utf-8')
            out = Path(tmp) / 'out'
            summary = report.build(logs, out, None)
            self.assertEqual(summary['ledgers'], ['coverage-1.json', 'coverage-2.json'])
            self.assertAlmostEqual(summary['courses']['Italy1']['Lit'], 60.0)
            self.assertAlmostEqual(summary['courses']['Italy1']['Excluded'], 40.0)
            lines = (out / 'unlit.csv').read_text(encoding='utf-8').splitlines()
            self.assertEqual(len(lines), 2)
            self.assertIn('pinus-tga', lines[1])
            self.assertIn(',200,', lines[1])
            self.assertIn('Italy1', (out / 'index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
