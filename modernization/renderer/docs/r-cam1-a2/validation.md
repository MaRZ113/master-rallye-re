# R-CAM1-A2 validation

## Repository snapshot

- Repository: `D:\Game\Master Rallye\master-rallye-re-general`
- Starting branch: `master`
- Starting HEAD: `0b2aece` (`fix: correct camera owner probe callsite`)
- Starting renderer worktree: clean; unrelated Observatory changes were present elsewhere in the worktree and were preserved.
- No branch or worktree was created, no game executable was patched, and no proprietary binary was added to the repository.

## Scope

The phase adds only a bounded read-only pre-submission CameraFrame snapshot to the existing exact-retail FOV submission hook and serializes it in the existing F10 camera-owner record. It does not enable Freecam or write camera pose fields.

## Build and test record

The existing Win32 x86 Release build completed successfully with a sequential MSBuild invocation. `verify_proxy.py` accepted the resulting DLL:

- DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`
- SHA256: `74f254c9d42ace91ea649e1ce69c5ccc0ae27642095562f55ce278224e2ca436`
- Size: `1,546,240` bytes
- Format: PE32, I386, DLL
- Required exports: `Direct3DCreate8`, `ValidatePixelShader`, `ValidateVertexShader`
- Recursive `d3d8.dll` import: none

Validation results:

- Native CTest: **10/10 passed**, including `camera_probe_contracts`.
- Python renderer suite: **118/118 passed**. The first attempt used the sandbox's unwritable default Windows temp directory; rerunning with `TEMP`/`TMP` pointed at an isolated writable directory passed, without test changes.
- Python compile check: `python -m compileall -q modernization/renderer/src modernization/renderer/tools modernization/renderer/tests` passed.
- `git diff --check` passed for the R-CAM1-A2 changes.

The exact retail executable was independently rechecked at `D:\Game\Master Rallye\MRallye.exe`: 3,121,214 bytes, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. It was read only.

In-game validation remains pending. The diagnostic handoff is in [runtime-test-plan.md](runtime-test-plan.md).

## Runtime boundary

The build and tests establish only that the added read-only snapshot contract compiles, serializes, and respects camera-pointer matching. They do not establish frontend-versus-race ownership, full-frame pose stability, or a safe temporary-pose restoration boundary. No live runtime capture was performed in this work session. Status remains `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION`; functional Freecam remains disabled.
