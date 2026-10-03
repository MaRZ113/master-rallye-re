import json
import contextlib
import io
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/runtime'))
import mr_observe as observe
import broker_observatory as core
from test_broker_observatory import dump, row


class CaptureResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = dump([row('Synthetic/Value', '1')])
        self.path = self.store('patched-front-1')

    def store(self, label):
        return observe.store_capture(self.root, self.raw, {'capture_kind': 'synthetic'}, label,
                                     datetime(2026, 10, 3, 14, 32, 36))

    def test_explicit_path(self):
        self.assertEqual(observe.resolve_capture(self.path, self.root), self.path)

    def test_filename(self):
        self.assertEqual(observe.resolve_capture(self.path.name, self.root), self.path)

    def test_stem(self):
        self.assertEqual(observe.resolve_capture(self.path.stem, self.root), self.path)

    def test_label(self):
        self.assertEqual(observe.resolve_capture('patched-front-1', self.root), self.path)

    def test_label_with_json_suffix(self):
        self.assertEqual(observe.resolve_capture('patched-front-1.json', self.root), self.path)

    def test_diff_command_uses_resolver(self):
        self.store('patched-front-2')
        args = observe.build_parser().parse_args(['diff', 'patched-front-1', 'patched-front-2'])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(observe.execute(args, self.root, {}), 0)

    def test_missing(self):
        with self.assertRaisesRegex(observe.UserError, 'Capture not found'):
            observe.resolve_capture('missing', self.root)

    def test_ambiguous_label_lists_candidates(self):
        other = self.store('patched-front-1')
        with self.assertRaisesRegex(observe.UserError, 'ambiguous') as caught:
            observe.resolve_capture('patched-front-1', self.root)
        self.assertIn(self.path.name, str(caught.exception))
        self.assertIn(other.name, str(caught.exception))

    def test_corrupt_and_missing_raw_are_rejected(self):
        raw = self.path.with_suffix('.dump.bin')
        for bad in ('corrupt', 'missing'):
            if bad == 'corrupt':
                raw.write_bytes(b'broken')
            else:
                raw.unlink()
            with self.assertRaises(core.ObservatoryError):
                observe.resolve_capture(self.path, self.root)
            with self.assertRaisesRegex(observe.UserError, 'Capture not found'):
                observe.resolve_capture(self.path.stem, self.root)

    def test_valid_pair_is_still_checked(self):
        path = observe.resolve_capture(self.path.name, self.root)
        self.assertEqual(observe.checked_snapshot(path)['source']['label'], 'patched-front-1')

    def test_standalone_raw_is_not_a_capture(self):
        with self.assertRaisesRegex(observe.UserError, 'capture JSON'):
            observe.resolve_capture(self.path.with_suffix('.dump.bin'), self.root)

    def test_selected_block_tampering_is_rejected(self):
        snapshot = json.loads(self.path.read_text())
        snapshot['source']['selected_block_sha256'] = '0'*64
        self.path.write_text(json.dumps(snapshot))
        with self.assertRaises(core.ObservatoryError):
            observe.resolve_capture(self.path, self.root)
        self.assertEqual(observe.capture_history(self.root), [])
