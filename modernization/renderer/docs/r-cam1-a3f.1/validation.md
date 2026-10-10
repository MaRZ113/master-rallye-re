# R-CAM1-A3f.1 validation

## Automated checks

- `python modernization/renderer/tools/build.py`: passed, Win32 x86 Release.
- Native CTest: **13/13 passed**, including new Freecam movement, speed, HWND cursor and wheel-message contracts; the existing orientation, camera scope, scheduler ABI, reset, renderer, UI and identity contracts also passed.
- Renderer Python suite: **155/155 passed**.
- Root `tests/synthetic`: **630/630 passed**.
- `python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization`: passed.
- `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll`: passed; PE32/I386, required direct exports present, and no recursive `d3d8.dll` import.
- `git diff --check`: passed.

The final candidate DLL is `modernization/renderer/.build-msvc/Release/d3d8.dll`, size **1,739,776 bytes**, SHA256 `2091904597e895f88d6f440ed88bfec93e521d1fe73bbe8e50c8f8697be22232`. The final rebuild after updating the A3f.1 transition label passed all 13 CTest cases; the focused Freecam Python checks then passed **9/9**. It is a generated, ignored build artifact and is not committed.

## Runtime boundary

No game runtime was exercised for A3f.1. The test suite confirms controller math and Win32 message routing, but it cannot certify how flight feel or cursor visibility appears in the live game. The candidate is **READY_FOR_IN_GAME_VALIDATION**, not runtime-confirmed. Use [the short handoff](runtime-handoff.md) for the focused France1 check.
