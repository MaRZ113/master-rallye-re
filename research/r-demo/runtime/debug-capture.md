# Debug window capture and channel status (historical approach)

R-DEMO2 priority is Sysinternals DebugView; this Win32 control-text approach failed in user testing and should not receive further work unless DebugView also fails. See `research/r-demo2/runtime/debugview-findings.md`.

Demo 8.4.1 displays a Debug window according to the user's first-pass runtime observation. On this research host no demo process was running during the check, and `python tools/runtime/demo_debug_capture.py --list-windows --window-title Debug` returned `[]`. The user subsequently reported that this helper failed to locate/read the visible window by PID, title and list-windows. Child-control details and stdout/stderr remain unknown; use DebugView as described in `research/r-demo2/runtime/debugview-findings.md`.

`tools/runtime/demo_debug_capture.py` uses Win32 `EnumWindows`, `EnumChildWindows`, `GetClassNameW`, `WM_GETTEXTLENGTH` and `WM_GETTEXT` with timeouts. It waits for a title fragment, chooses a readable standard EDIT/RichEdit child, polls text, detects appended text or buffer resets, and writes timestamped UTF-8 lines. It does not inject, patch, automate input, or read process memory. The `--list-windows` diagnostic mode reports window and child classes and readable lengths without saving game text.

From the R-DEMO worktree, start before launching the scratch demo:

```powershell
python tools/runtime/demo_debug_capture.py --list-windows --window-title Debug
python tools/runtime/demo_debug_capture.py --window-title Debug --output '.research-output/r-demo/runtime-logs/trooper-8_4_1.log' --poll-ms 250
```

If multiple Debug windows are visible, add `--pid <MRallye.exe PID>`. The output path is restricted to the ignored runtime-logs directory. Stop with Ctrl+C after a clean game exit. If the diagnostic shows no readable EDIT/RichEdit child or WM_GETTEXT fails, record the class tree and use the fallbacks below; the helper cannot claim capture success without real lines.

Fallback order: (1) standard control text via the helper; (2) launch the scratch demo from a console with stdout/stderr redirected and check whether the observed Debug lines appear in those files; (3) use Microsoft Sysinternals DebugView to capture `OutputDebugStringA` and export a short session. Both demo EXEs import `OutputDebugStringA`; in 8.4.1 a candidate installed logging sink calls it before forwarding text to another sink (**CONFIRMED_BY_EXECUTABLE**). Import and code path do not establish that the observed messages reach DebugView in a given run. Keep raw logs and redirection files under ignored `.research-output/r-demo/runtime-logs/`.

Suggested short session: start capture, launch demo 8.4.1, display Trooper in vehicle selection, start a Trooper race, drive briefly, exit to menu and then game. Save the complete output locally, then run `tools/runtime/demo_debug_classify.py` against it. A minimal 9.3.1 run can later check whether the same window/messages exist. The live channel status remains **PENDING**.
