# R-CAM1-A3h.3a Validation

## Synthetic coverage

`clean_view_contracts` now covers completed/current scheduler and Trace-frame association, thread/device matching, age expiry, user-off context reporting, persistent request through unrelated draws and restored camera scope, repeated verified UI draws, toggle-off, and each existing fail-closed admission/draw gate.

## Build and runtime boundary

The canonical `python modernization/renderer/tools/build.py` completed a Win32 x86 Release build and all **14/14 CTest contracts** passed.

The filtered renderer Python suite passed **158 tests**. It excluded only `test_actual_trace_additive_fields` and `test_actual_full_race_hud_capture`, which require historical runtime captures keyed to a different executable hash; the latter also scans the multi-gigabyte capture corpus. No existing test was changed to conceal this mismatch. `python -m compileall -q modernization/renderer` passed. Root `tests/` discovery completed with zero unittest cases. `git diff --check` is expected to be run at final closeout.

`verify_proxy.py` reported valid PE32/I386, exports `Direct3DCreate8`, `ValidatePixelShader`, and `ValidateVertexShader`, no recursive `d3d8.dll` import, size **1,789,440 bytes**, SHA-256 `31f62047aba603d7697f6273e710b324518c0e7fe159600d8234c4a5b84ab76d`. This remains build evidence only. `git diff --check` passed.

No game runtime test was performed by Codex. A successful build and synthetic suite do not establish that the supported native UI consumer is reached or that a draw is suppressed in-game. The user must run the focused pilot in [runtime-handoff.md](runtime-handoff.md).
