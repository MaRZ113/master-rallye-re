# Live Freecam validation

Status: `LIVE_FREECAM_READY_FOR_RUNTIME`. Automated and binary checks pass; a
human gameplay run is still required to confirm that race simulation visibly
continues while the camera is detached.

## Candidate

- DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`
- SHA-256: `bd1df3765e09cc9a034c89ef523772adec282c795043df47da954240a4732674`
- Size: 2,311,680 bytes
- PE: PE32, I386 (`0x014c`), DLL; `Direct3DCreate8`, `ValidatePixelShader`, and
  `ValidateVertexShader` exports verified; no recursive `d3d8.dll` import.
- Target EXE: pristine retail SHA-256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
  rechecked locally.

## Automated checks

- `python modernization/renderer/tools/build.py`: passed; Win32 Release DLL
  built and native CTest passed **24/24**.
- `python -m unittest discover -s modernization/renderer/tests -q`: **193
  passed**.
- `python -m unittest discover -s tests/synthetic -q`: **630 passed**.
- `python -m compileall -q modernization/renderer`: passed.
- `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll`:
  passed with the PE/export/import facts above.
- `git diff --check`: passed; Git reports existing CRLF-to-LF working-copy
  notices for edited C++ files, with no whitespace errors.

## Runtime evidence boundary

No game run was performed by these checks. They do not prove that France1
continues simulating while Freecam is active. Use the steps in
[`runtime-handoff.md`](runtime-handoff.md), then attach the session JSONL and
an F10 capture if any behavior differs. In the trace, `camera_scope_active`
describes the temporary camera/frustum scope; `camera_scope_restored` becomes
true after it is safely restored. Verify vehicle and AI motion directly.
