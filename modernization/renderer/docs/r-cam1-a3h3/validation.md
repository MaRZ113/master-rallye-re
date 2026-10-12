# R-CAM1-A3h.3 Validation

## Static / synthetic

- Exact-build feature gates use the existing pristine SHA profile (`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`) and base `0x00400000`.
- `clean_view_contracts` covers each admission prerequisite independently, exact build/hook/thread/native consumer/identity/callsite/FVF/primitive rejection, and the final suppression conjunction.
- `race_epoch_contracts` checks typed read-only pause bool parsing, false state, wrong type, and missing key.
- `free_camera_contracts` checks pilot defaults, configurable non-conflicting H binding, and feature-local rejection of malformed/conflicting Clean View config.
- The pre-existing UI ownership capture and camera/renderer suites remain part of the native CTest build.

## Build and native tests

`python modernization/renderer/tools/build.py` completed a Win32 x86 Release build and ran all 14 CTest contracts successfully, including the new Clean View contract.

## Python tests

The focused existing renderer suites `test_free_camera`, `test_ui_ownership`, and `test_race_epoch` passed (22 tests). A filtered broad run passed 158 Python tests. It excluded only `test_actual_trace_additive_fields` and `test_actual_full_race_hud_capture`: both require runtime logs keyed to the current `reflection_tests.exe` hash, and the latter scans a 7.1 GB historical JSONL corpus. Full discovery reported the expected missing-current-capture failure and continued into that expensive corpus scan, so it was stopped. Root-level `tests/` discovery found zero unittest cases. No older tests were modified to mask the capture/hash mismatch.

## Binary checks

`verify_proxy.py` passed on `.build-msvc/Release/d3d8.dll`: PE32/I386 DLL, exports `Direct3DCreate8`, `ValidatePixelShader`, and `ValidateVertexShader`, no recursive `d3d8.dll` import, SHA-256 `d042c4d30db28787c5eb56cd4dc10d9a19b4f8f8475c7961f8d8f8baa5a37ff8`, size 1,782,272 bytes. This does not establish runtime behavior. No DLL or generated capture is included in source control or the source archive.

The source-only handoff archive is `R-CAM1-A3h.3-source-handoff.zip` in this directory; it contains the modified renderer sources/configuration/tests and this phase's notes, not build outputs or runtime logs.

## Runtime status

Not run by Codex. Completion state is `READY_FOR_RUNTIME_PILOT`, not visually validated. Follow the focused checks in [runtime handoff](runtime-handoff.md).
