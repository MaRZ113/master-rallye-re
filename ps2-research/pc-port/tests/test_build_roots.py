"""Synthetic incremental staging tests; never touch the original renderer."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import os
import json
import hashlib
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'overlay/build_overlay.py'
spec=importlib.util.spec_from_file_location('single_root_builder',SCRIPT)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class BuildRootTests(unittest.TestCase):
    def test_canonical_roots_are_fixed(self):
        self.assertEqual(b.BUILD_ROOT,b.PORT/'.build')
        self.assertEqual(b.STAGING_ROOT,b.PORT/'.staging')
        self.assertEqual(b.DIST_ROOT,b.PORT/'dist/current')
        with patch.dict(os.environ,{'MRR_PS2PORT_BUILD_ROOT':str(b.PORT/'.build-overlay-old')}):
            with self.assertRaisesRegex(RuntimeError,'Single-build-root policy'):b.verify_baseline({})

    def test_incremental_stage_preserves_unchanged_timestamps_and_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);desired=root/'desired';stage=root/'stage';build=root/'.build'
            desired.mkdir();build.mkdir();(desired/'source.cpp').write_bytes(b'first')
            (build/'object.obj').write_bytes(b'keep CMake output')
            owned=b.sync_verified_stage(desired,stage,{})
            before=(stage/'source.cpp').stat().st_mtime_ns
            self.assertEqual(owned,b.sync_verified_stage(desired,stage,owned))
            self.assertEqual(before,(stage/'source.cpp').stat().st_mtime_ns)
            (desired/'source.cpp').write_bytes(b'changed')
            owned=b.sync_verified_stage(desired,stage,owned)
            self.assertEqual((stage/'source.cpp').read_bytes(),b'changed')
            (desired/'source.cpp').unlink();b.sync_verified_stage(desired,stage,owned)
            self.assertFalse((stage/'source.cpp').exists())
            self.assertEqual((build/'object.obj').read_bytes(),b'keep CMake output')

    def test_modified_or_unowned_stage_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);desired=root/'desired';stage=root/'stage';desired.mkdir()
            (desired/'source.cpp').write_bytes(b'frozen')
            owned=b.sync_verified_stage(desired,stage,{})
            (stage/'source.cpp').write_bytes(b'user edit')
            with self.assertRaisesRegex(RuntimeError,'modified staged'):b.sync_verified_stage(desired,stage,owned)
            self.assertEqual((stage/'source.cpp').read_bytes(),b'user edit')
            (stage/'source.cpp').write_bytes(b'frozen');(stage/'unknown.txt').write_text('user file')
            with self.assertRaisesRegex(RuntimeError,'Unowned'):b.sync_verified_stage(desired,stage,owned)
            self.assertTrue((stage/'unknown.txt').exists())

    def test_workflow_lock_blocks_concurrent_staging(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(b,'BUILD_ROOT',Path(directory)):
            with b.workflow_lock():
                with self.assertRaisesRegex(RuntimeError,'already in use'):
                    with b.workflow_lock():self.fail('concurrent entry')
            with b.workflow_lock():pass

    def test_committed_hud_adoption_has_two_exact_active_patches(self):
        lock=json.loads(b.LOCK_PATH.read_text())
        audit_root=b.PORT/'docs/build-policy/hud-baseline-adoption'
        audit=json.loads((audit_root/'audit.json').read_text())
        self.assertEqual(lock['baseline_head'],audit['adopted_baseline_head'])
        self.assertEqual(lock['renderer_tree'],audit['adopted_renderer_tree'])
        self.assertEqual(set(lock['patches']),set(b.PATCH_PATHS))
        self.assertEqual(set(b.PATCH_PATHS),{'0001-renderer-integration.patch','0002-interface-generator.patch'})
        self.assertEqual(lock['hud_baseline_adoption']['exact_approved_git_blob_sha256'],audit['approved_git_blob_sha256'])
        self.assertTrue(audit['approved_hud_patch_exact_git_byte_match'])
        self.assertTrue(audit['rebased_ps2_renderer_equal_previous_hud_enabled_stage'])
        for name,digest in audit['archived_files_sha256'].items():
            self.assertEqual(hashlib.sha256((audit_root/name).read_bytes()).hexdigest(),digest)
        self.assertFalse((b.PATCH_DIR/'0003-hud-context-cache.patch').exists())

    def test_missing_or_extra_locked_patch_is_rejected(self):
        lock=json.loads(b.LOCK_PATH.read_text())
        lock['files']={} # Patch admission is synthetic; no private Git checkout needed.
        with patch.object(b,'verify_renderer_identity',return_value={}),patch.object(b,'git_text',return_value=str(b.ROOT)):
            missing=json.loads(json.dumps(lock));missing['patches'].pop('0002-interface-generator.patch')
            with self.assertRaisesRegex(RuntimeError,'Locked patch set'):b.verify_baseline(missing)
            extra=json.loads(json.dumps(lock));extra['patches']['unreviewed.patch']={'sha256':'0'*64}
            with self.assertRaisesRegex(RuntimeError,'Locked patch set'):b.verify_baseline(extra)
            unhashed=json.loads(json.dumps(lock));unhashed['patches']['0001-renderer-integration.patch']={}
            with self.assertRaisesRegex(RuntimeError,'Patch hash mismatch'):b.verify_baseline(unhashed)

if __name__=='__main__':unittest.main()
