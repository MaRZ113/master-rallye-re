import contextlib
import io
import json
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/runtime'))
import dev_command_trigger as t
import mr_observe as observe


class BrokerOpenTests(unittest.TestCase):
    def setUp(self):
        self.main=t.TargetWindow(123, 0x1234, Path('C:/test/MRallye.exe'), t.RETAIL_SHA256,
                                 'Master Rallye', t.RETAIL_PRISTINE)
        self.broker=t.TargetWindow(123, 0x2345, self.main.image_path, self.main.sha256,
                                   'Broker Editor', t.RETAIL_PRISTINE)

    def run_open(self, *, completed=True, error=0, windows=None, statuses=None):
        timer=[0.0]
        def sleep(n):timer[0]+=n
        dispatch=Mock(return_value=t.OpenDispatch(completed,error,3000 if not completed else 1))
        discover=Mock(side_effect=windows) if windows is not None else Mock(return_value=[])
        status=Mock(side_effect=statuses) if statuses is not None else Mock(return_value=(True,True))
        report,window=t.open_tool_once(self.main,'broker-editor',grace=.3,dispatch=dispatch,
            discover=discover,status=status,clock=lambda:timer[0],sleep=sleep)
        dispatch.assert_called_once_with(self.main,'broker-editor')
        self.assertEqual(report.command,0x27);self.assertEqual(report.command_count,1)
        self.assertFalse(report.dump_sent);self.assertEqual((report.pid,report.hwnd),(123,0x1234))
        return report,window

    def test_synchronous_success_requires_verified_window(self):
        r,w=self.run_open(windows=[[self.broker]])
        self.assertEqual(r.outcome,t.OpenOutcome.COMPLETED);self.assertEqual(w,self.broker)

    def test_completed_dispatch_without_window_is_not_success(self):
        r,w=self.run_open();self.assertEqual(r.outcome,t.OpenOutcome.FAILED);self.assertIsNone(w)

    def test_timeout_is_completion_unknown_no_retry(self):
        r,w=self.run_open(completed=False,error=1460)
        self.assertEqual(r.outcome,t.OpenOutcome.UNCERTAIN);self.assertIsNone(w)
        self.assertEqual(r.win32_error,1460);self.assertTrue(r.process_alive)

    def test_zero_error_is_uncertain_not_permission_failure(self):
        r,_=self.run_open(completed=False);self.assertEqual(r.outcome,t.OpenOutcome.UNCERTAIN)
        self.assertEqual(r.win32_error,0)

    def test_real_win32_failure_is_preserved(self):
        r,_=self.run_open(completed=False,error=5)
        self.assertEqual(r.outcome,t.OpenOutcome.FAILED);self.assertEqual(r.win32_error,5)

    def test_late_broker_after_timeout(self):
        r,w=self.run_open(completed=False,error=1460,windows=[[],[self.broker]])
        self.assertEqual(r.outcome,t.OpenOutcome.LATE);self.assertEqual(w,self.broker)
        self.assertGreater(r.elapsed_ms,0)

    def test_process_exit_during_open(self):
        r,_=self.run_open(statuses=[(True,True),(False,False)])
        self.assertEqual(r.outcome,t.OpenOutcome.INVALIDATED);self.assertFalse(r.process_alive)

    def test_main_window_identity_change(self):
        r,_=self.run_open(statuses=[(True,True),(True,False)])
        self.assertEqual(r.outcome,t.OpenOutcome.INVALIDATED)

    def test_process_alive_unknown_is_preserved(self):
        r,_=self.run_open(completed=False,error=1460,statuses=[(None,True)]*10)
        self.assertIsNone(r.process_alive)

    def test_ambiguous_broker_windows(self):
        r,w=self.run_open(windows=[[self.broker,self.broker]])
        self.assertEqual(r.reason,'ambiguous_tool_windows');self.assertIsNone(w)

    def test_broker_other_process_is_not_accepted(self):
        from dataclasses import replace
        r,w=self.run_open(windows=[[replace(self.broker,pid=124)]])
        self.assertEqual(r.outcome,t.OpenOutcome.INVALIDATED);self.assertIsNone(w)

    def test_no_arbitrary_command_or_unbounded_grace(self):
        for tool,grace in [('dump',1),('broker-editor',float('nan')),('broker-editor',6)]:
            send=Mock()
            with self.assertRaises(ValueError):t.open_tool_once(self.main,tool,grace=grace,dispatch=send)
            send.assert_not_called()

    def test_unknown_completion_error_is_not_generic_access_error(self):
        r,_=self.run_open(completed=False,error=1460)
        stderr=io.StringIO()
        with contextlib.redirect_stderr(stderr):observe.report_error(t.ToolOpenError(r))
        self.assertIn('completion is uncertain',stderr.getvalue())
        self.assertNotIn('File/process access',stderr.getvalue())
        self.assertIn('Dump was not sent',stderr.getvalue())
        self.assertEqual(json.loads(r.json())['win32_error'],1460)

    def test_menu_less_exact_native_owner(self):
        words={0x6f9cf0:0x20000,0x6f9d80:0x30000,0x20020:0x30000,
               0x30000:0x69228c,0x3005c:0x1234}
        def read(a,n):self.assertEqual(n,4);return struct.pack('<I',words[a])
        self.assertTrue(t.validate_retail_main_owner(read,0x400000,0x1234))
        words[0x3005c]=0x5678
        self.assertFalse(t.validate_retail_main_owner(read,0x400000,0x1234))
        words[0x3005c]=0x1234;words[0x20020]=0x40000
        self.assertFalse(t.validate_retail_main_owner(read,0x400000,0x1234))
        self.assertFalse(t.validate_retail_main_owner(read,0x500000,0x1234))

    def test_menu_less_unknown_profile_rejected_before_live_reads(self):
        from dataclasses import replace
        profile=replace(t.RETAIL_PRISTINE,sha256='0'*64)
        self.assertFalse(t._verified_menu_less_main(123,0x1234,profile))

    def test_real_dispatch_adapter_clears_and_retains_win32_error(self):
        user=Mock();kernel=Mock();user.IsWindow.return_value=True;user.IsWindowVisible.return_value=True
        def pid(_hwnd,out):out._obj.value=123
        def title(_hwnd,out,_size):out.value='Master Rallye'
        user.GetWindowThreadProcessId.side_effect=pid;user.GetWindowTextW.side_effect=title
        for sent,error in [(1,0),(0,1460),(0,0),(0,5)]:
            user.SendMessageTimeoutW.reset_mock();user.SendMessageTimeoutW.return_value=sent
            with patch('ctypes.WinDLL',side_effect=[user,kernel],create=True), \
                 patch.object(t,'_configure_user32'),patch.object(t,'_configure_kernel32'), \
                 patch.object(t,'_image_for_pid',return_value=self.main.image_path), \
                 patch.object(t,'verified_profile',return_value=t.RETAIL_PRISTINE), \
                 patch.object(t,'_has_expected_main_menu',return_value=True), \
                 patch('broker_observatory.verify_live_capability'), \
                 patch('ctypes.set_last_error',create=True) as clear, \
                 patch('ctypes.get_last_error',return_value=error,create=True):
                d=t.send_tool_command(self.main,'broker-editor')
            self.assertEqual((d.completed,d.win32_error),(bool(sent),error))
            clear.assert_called_once_with(0)
            self.assertEqual(user.SendMessageTimeoutW.call_count,1)
            self.assertEqual(user.SendMessageTimeoutW.call_args.args[:6],(0x1234,0x111,0x27,0,2,3000))

    def test_ensure_tool_uses_report_and_never_sends_dump(self):
        process=Mock(pid=123,profile=t.RETAIL_PRISTINE)
        report=t.OpenReport(t.OpenOutcome.COMPLETED,0x27,123,0x1234,0,10,True,0x2345,'verified')
        with patch.object(t,'find_tool_windows',return_value=[]), \
             patch.object(t,'find_retail_main_windows',return_value=[self.main]), \
             patch.object(t,'open_tool_once',return_value=(report,self.broker)) as opener, \
             patch.object(t,'send_broker_dump') as dump:
            self.assertEqual(observe.ensure_tool(process,'broker-editor'),self.broker)
        opener.assert_called_once();dump.assert_not_called()

if __name__=='__main__':unittest.main()
