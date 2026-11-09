"""Source provenance checks for the canonical Extra Options renderer build."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('extra_renderer_build', ROOT / 'tools/build_extra_options_candidate.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class RendererBuildTests(unittest.TestCase):
    def test_stage_records_inputs_without_copying_or_patching_staging(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with patch.object(b, 'graphics_inputs', return_value={'current': 'inputs'}):
                result = b.stage_graphics(root)
            self.assertEqual(sorted(p.name for p in result.iterdir()), ['inputs.json'])
            self.assertEqual(json.loads((result / 'inputs.json').read_text()), {'current': 'inputs'})

    def test_source_drift_rejected_before_compiler_runs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'graphics-source').mkdir()
            (root / 'graphics-source/inputs.json').write_text('{"head":"old"}')
            with patch.object(b, 'graphics_inputs', return_value={'head': 'new'}), patch.object(b.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'changed after source capture'):
                    b.build_graphics(root)
                run.assert_not_called()

    def build_case(self, fault=None):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            port = root / 'general/ps2-research/pc-port'
            out = root / 'output'
            out.mkdir()
            inputs = {'head': 'current'}
            with patch.object(b, 'graphics_inputs', return_value=inputs):
                b.stage_graphics(out)
            source = port / 'renderer/current.hpp'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'current atmosphere and bridge')
            dll = port / 'dist/current/ps2-enabled/d3d8.dll'
            dll.parent.mkdir(parents=True)
            dll.write_bytes(b'validated DLL')
            log = port / '.build/logs/ps2-enabled-ctest.log'
            log.parent.mkdir(parents=True)
            log.write_text('100% tests passed')
            report = {'ps2_source_sha256': {'renderer/current.hpp': b.sha(source)},
                      'builds': {'ps2-enabled': {'dll': str(dll.relative_to(root / 'general')),
                                               'dll_sha256': b.sha(dll)}}}
            if fault == 'source':
                source.write_bytes(b'stale staged source')
            if fault == 'binary':
                dll.write_bytes(b'unverified DLL')
            (port / 'dist/current/build-report.json').write_text(json.dumps(report))
            with patch.object(b, 'GENERAL', port), patch.object(b, 'graphics_inputs', return_value=inputs), patch.object(b.subprocess, 'run') as run:
                if fault:
                    with self.assertRaisesRegex(ValueError, 'compiled port input differs|built renderer hash mismatch'):
                        b.build_graphics(out)
                    self.assertFalse((out / 'd3d8.dll').exists())
                else:
                    b.build_graphics(out)
                    self.assertEqual((out / 'd3d8.dll').read_bytes(), dll.read_bytes())
                    self.assertEqual(json.loads((out / 'graphics-build-manifest.json').read_text()), report)
                self.assertEqual(run.call_args.args[0], [sys.executable, str(port / 'overlay/build_overlay.py')])

    def test_canonical_build_and_matching_artifact(self):
        self.build_case()

    def test_stale_compiled_source_rejected(self):
        self.build_case('source')

    def test_mutated_built_dll_rejected(self):
        self.build_case('binary')


if __name__ == '__main__':
    unittest.main()
