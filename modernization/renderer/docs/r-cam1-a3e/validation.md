# R-CAM1-A3e validation

## Automated results

- Exact pristine retail EXE SHA256 was verified at
  `D:\Game\Master Rallye Pristine\MRallye.exe`:
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Full renderer Python suite: **154/154 passed**. The A3e-focused
  `test_free_camera` module then passed **9/9**, including the first-flight
  golden capture summary added after the full run.
- Win32 x86 Release build and native CTest: **13/13 passed**. This includes
  exact captured root/HUD flags, job-local commit success under a changed
  manager scene ID, RaceState 0/2 admission, RaceState 1/3 rejection, failed
  root and child jobs, stale lifecycle/owner, retirement, unsupported context,
  wrong camera and existing camera-scope/control contracts.
- `python -m compileall modernization`: **passed**. The command also walked
  ignored historical scratch snapshots; the `.pyc` files it created there were
  removed without touching their sources or Ghidra databases.
- `git diff --check`: **passed**.
- `verify_proxy.py`: **passed**. DLL is PE32/I386, exports the three required
  direct exports at their required ordinals, and does not import `d3d8.dll`.

## Build artifact

- Path:
  `modernization/renderer/.build-msvc/Release/d3d8.dll`
- Size: **1,722,368 bytes**
- SHA256:
  `a509356a0db4d0270aa0ec557b2ef2b82b43a5eabfea3fb10c3699a270869439`
- Build/export evidence is **BUILD_VERIFIED_NOT_RUNTIME**.

## Runtime boundary

The prior DLL's real first-flight capture is recorded in
`research/r-cam1-a3e/first-flight-capture-summary.json`. It explains why
A3d's gate rejected the active race; it does not demonstrate an A3e flight.
The new candidate still needs a human run using the short sequence in
`runtime-handoff.md`. Expected minimum: live certificate true, F8 sampled
pressed while focused, controller edge true, `free_camera.active` true during
movement, then a verified restore after F8 off. Until that happens, flight
status remains **PENDING HUMAN VALIDATION**.
