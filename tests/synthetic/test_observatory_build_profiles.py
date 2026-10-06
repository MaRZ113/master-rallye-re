from __future__ import annotations
import contextlib
import ctypes
import hashlib
import io
import struct
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/runtime'))
import observatory_build_profiles as profiles
import broker_observatory as core
import mr_observe as observe
import dev_command_trigger as commands
from test_broker_observatory import dump, row


class KnownBuildProfileTests(unittest.TestCase):
    def test_frontend_file_verification_selects_each_profile(self):
        for p in profiles.PROFILES:
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/'MRallye.exe'
                with path.open('wb') as stream:
                    stream.truncate(p.file_size)
                with patch.object(observe,'PORTABLE',False), \
                     patch.object(observe,'resolve_executable_profile',return_value=p):
                    self.assertIs(observe.verify_executable(path),p)

    def test_dump_rejects_same_hwnd_with_changed_build_before_send(self):
        target = commands.TargetWindow(1,123,Path('MRallye.exe'),profiles.RETAIL_PRISTINE.sha256,'Broker Editor')
        changed = commands.TargetWindow(1,123,Path('MRallye.exe'),profiles.RETAIL_WIDESCREEN_FREEZE.sha256,'Broker Editor')
        with patch.object(commands,'find_tool_windows',return_value=[changed]), self.assertRaises(RuntimeError):
            commands.send_broker_dump(target)

    def test_pristine_identity_and_anchors_preserved(self):
        p = profiles.RETAIL_PRISTINE
        self.assertIs(profiles.match_profile(p.sha256, 3121214), p)
        self.assertEqual((p.active_log_sink_rva, p.debug_sink_vtable_rva), (0x2F7B7C, 0x29CEA8))

    def test_patched_identity_and_anchors(self):
        p = profiles.RETAIL_WIDESCREEN_FREEZE
        self.assertIs(profiles.match_profile(p.sha256, 3117118), p)
        self.assertEqual((p.active_log_sink_rva, p.debug_sink_vtable_rva), (0x2F6B64, 0x29BF3C))

    def test_unknown_hash_rejected(self):
        with self.assertRaises(ValueError):
            profiles.match_profile('0' * 64, 3121214)

    def test_wrong_size_rejected_for_each_profile(self):
        for p in profiles.PROFILES:
            with self.assertRaises(ValueError):
                profiles.match_profile(p.sha256, p.file_size + 1)

    def test_profiles_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            profiles.RETAIL_PRISTINE.active_log_sink_rva = 1

    def test_profile_specific_global_and_vtable_checks(self):
        for p in profiles.PROFILES:
            base, sink, helper, buffer = 0x400000, 0x100000, 0x200000, 0x300000
            obj = bytearray(0x30)
            for offset, value in {0:p.debug_sink_vtable_rva + base, 0xC:helper,
                    0x20:buffer, 0x24:buffer+100, 0x28:buffer, 0x2C:buffer+10}.items():
                struct.pack_into('<I', obj, offset, value)
            memory = {base+p.active_log_sink_rva:struct.pack('<I',sink), sink:bytes(obj),
                      helper+4:struct.pack('<I',123)}
            with patch.object(core, '_read_remote', side_effect=lambda k,h,a,n,c: memory[a]) as read:
                state = core._read_sink_state(Mock(), Mock(), 1, base, ctypes, p)
            self.assertEqual(read.call_args_list[0].args[2], base+p.active_log_sink_rva)
            self.assertEqual(state['vtable'], base+p.debug_sink_vtable_rva)
            struct.pack_into('<I', obj, 0, base+0x1234)
            memory[sink] = bytes(obj)
            with patch.object(core, '_read_remote', side_effect=lambda k,h,a,n,c: memory[a]):
                with self.assertRaises(core.ObservatoryError):
                    core._read_sink_state(Mock(), Mock(), 1, base, ctypes, p)

    def test_live_capability_requires_matching_used_code_fingerprints(self):
        code_a=b"logger-anchor";code_b=b"vtable-anchor"
        profile=replace(profiles.RETAIL_PRISTINE,profile_origin="locally_audited",exact_profile_id=None,
            capabilities={"broker_read":True},
            pe_identity={"image_base":0x400000,"size_of_image":0x500000},
            runtime_anchors=(
                {"name":"debug_logger","rva":0x1000,"length":len(code_a),"sha256":hashlib.sha256(code_a).hexdigest()},
                {"name":"debug_sink_vtable","rva":0x2000,"length":len(code_b),"sha256":hashlib.sha256(code_b).hexdigest()},
            ))
        data={0x401000:code_a,0x402000:code_b}
        def remote(_kernel,_process,address,size,_ctypes):
            value=data.get(address,b"")
            self.assertEqual(len(value),size)
            return value
        with patch.object(core,"_read_remote",side_effect=remote):
            names=core._verify_remote_anchors(Mock(),Mock(),0x400000,ctypes,profile,"broker_read")
        self.assertEqual(names,["debug_logger","debug_sink_vtable"])
        data[0x401000]=b"changed-bytes"
        with patch.object(core,"_read_remote",side_effect=remote), self.assertRaisesRegex(core.ObservatoryError,"fingerprint differs"):
            core._verify_remote_anchors(Mock(),Mock(),0x400000,ctypes,profile,"broker_read")

    def test_locally_audited_profile_without_used_fingerprints_fails_closed(self):
        profile=replace(profiles.RETAIL_PRISTINE,profile_origin="locally_audited",exact_profile_id=None,
                        capabilities={"broker_read":True},runtime_anchors=())
        with self.assertRaisesRegex(core.ObservatoryError,"No runtime code fingerprints"):
            core._verify_remote_anchors(Mock(),Mock(),0x400000,ctypes,profile,"broker_read")

    def test_live_capture_metadata_and_profile_propagation(self):
        for p in profiles.PROFILES:
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/'MRallye.exe'
                with path.open('wb') as stream:
                    stream.truncate(p.file_size)
                state = dict(buffer_base=0x300000, used_bytes=3, capacity_bytes=100,
                             sink_pointer=0x100000, vtable=0x400000+p.debug_sink_vtable_rva, hwnd=123)
                with patch.object(core.os,'name','nt'), patch('ctypes.WinDLL',return_value=Mock(),create=True), \
                     patch.object(core,'_configure_win32'), patch.object(core,'_process_image_path',return_value=(1,path)), \
                     patch.object(core,'sha256_file',return_value=p.sha256), \
                     patch.object(core,'_module_base',return_value=0x400000), \
                     patch.object(core,'_read_sink_state',return_value=state) as read_state, \
                     patch.object(core,'_read_remote',return_value=b'abc'):
                    raw, source = core.capture_debug_buffer(123)
                self.assertEqual(raw,b'abc')
                self.assertEqual(source['build_profile_id'],p.id)
                self.assertEqual(source['image_sha256'],p.sha256)
                self.assertEqual(source['image_size'],p.file_size)
                self.assertEqual(source['sink_vtable'],f'0x{state["vtable"]:08X}')
                self.assertTrue(all(call.args[-1] is p for call in read_state.call_args_list))

    def test_multiple_known_processes_require_selection_and_show_profiles(self):
        candidates = [observe.ProcessCandidate(i,Path('MRallye.exe'),p.sha256)
                      for i,p in enumerate(profiles.PROFILES,1)]
        with self.assertRaises(core.ObservatoryError):
            observe.select_process(candidates)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertIs(observe.select_process(candidates,input_fn=lambda _: '2'),candidates[1])
        for p in profiles.PROFILES:
            self.assertIn(p.id,out.getvalue())

    def test_old_snapshot_without_profile_metadata_remains_readable(self):
        old = core.parse_dump_bytes(dump([row('Test/X','1')]), {'image_sha256':core.RETAIL_SHA256})
        self.assertNotIn('build_profile_id',old['source'])
        self.assertEqual(core.diff_snapshots(old,old)['summary'],{})

    def test_unverified_flow_builder_is_rejected_before_discovery(self):
        p = profiles.RETAIL_WIDESCREEN_FREEZE
        candidate = observe.ProcessCandidate(1,Path('MRallye.exe'),p.sha256)
        with patch.object(commands,'find_tool_windows') as find, self.assertRaises(core.ObservatoryError):
            observe.ensure_tool(candidate,'flow-builder')
        find.assert_not_called()
