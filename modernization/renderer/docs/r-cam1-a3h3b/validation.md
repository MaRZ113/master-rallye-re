# R-CAM1-A3h.3b Validation

## Static/runtime evidence used

The supplied exact-build capture `frame-17888-d1-00005934.jsonl` has a matching current France1 race certificate, active H request, verified native consumer scope, and 474 captured UI draw records. Its frame summary reports zero eligible/suppressed UI draws and the combined scheduler stale/uncompleted rejection. The matching session's final summary reports 3,100,206 UI draw candidates and 554,106 admission rejections. Those files do not include scheduler depth at the draw boundary, so they establish the failing handoff and scope coverage, but not whether the UI draw was in-flight or post-completion. A3h.3b adds that exact phase observation to the next F10.

Source inspection confirms the snapshot is published from `before_submit()` within the scheduler interval, while `completed` is set only by the outermost `scheduler_end()` after ordinary CameraFrame restoration. The phase validator and tests now allow a matching current in-flight snapshot and a matching completed snapshot, with stale/mismatched contexts failing open.

## Automated validation

- Canonical `python modernization/renderer/tools/build.py`: Win32 x86 Release built; **14/14 CTest contracts passed**.
- Renderer Python tests: the unfiltered suite ran 154 tests and reported two capture-bound blockers: `test_actual_trace_additive_fields` had no matching runtime capture, and `LearnedSemanticCaptureTests` requires the current vehicle-semantics integration capture. The focused remainder passed **152 tests**, excluding those runtime-dependent cases and the historical multi-gigabyte full-race HUD capture.
- Root synthetic suite `python -m unittest discover -s tests/synthetic -p 'test_*.py'`: **630 tests passed**.
- `python -m compileall -q modernization/renderer`: passed.
- `verify_proxy.py`: valid PE32/I386 DLL; required exports present; imports are `bcrypt.dll`, `USER32.dll`, and `KERNEL32.dll` (no recursive `d3d8.dll` import). DLL size **1,796,096 bytes**, SHA-256 `73ae068420af77df48e461e1982f2657e08132636146e4603d27b72b7c5bbf72`.
- `git diff --check`: passed; only existing CRLF/LF normalization warnings were emitted.

No game runtime validation has been performed on this build. Status is `READY_FOR_RUNTIME_PILOT`, not runtime-confirmed. Follow [runtime-handoff.md](runtime-handoff.md) for one active CleanView F10 and its matching session; that capture should establish the live phase and confirm actual suppression/restoration.
