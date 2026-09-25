# Debug output capture methods (historical helper; R-DEMO2.1 results)

The original Win32 control-text helper `tools/runtime/demo_debug_capture.py` failed to locate/read the visible Debug window in user testing. Its earlier `--list-windows` result was empty on a host without the demo process, so it is not evidence that the game has no Debug window. No further helper work is required for the completed R-DEMO2.1 scope.

Sysinternals DebugView captured OutputDebugString diagnostics in the tested demo 8.4.1 session, including normal Trooper cooker stages and the final incomplete `Building convex hull -` line for the crashing `$chull` candidate. In the tested 9.3.1 session, **NO_OUTPUT_OBSERVED**; this does not establish logger removal. Parsed evidence and scope are in `research/r-demo2/runtime/debugview-findings.md` and `research/r-demo2/cooker-stages.md`.

The helper uses Win32 window enumeration and standard control text APIs; it does not inject, patch, automate input, or read process memory. Both EXEs import `OutputDebugStringA`, and a bounded 8.4.1 code path calls it (**CONFIRMED_BY_EXE**), but static presence alone does not prove a live message. Raw captures remain outside Git under ignored `.research-output/r-demo2/debugview/`.
