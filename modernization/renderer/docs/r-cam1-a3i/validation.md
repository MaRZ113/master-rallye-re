# R-CAM1-A3i validation

## Build and automated checks

- `python modernization/renderer/tools/build.py` — PASS; Win32 Release build succeeded and CTest passed 15/15, including `camera_bookmark_contracts`.
- `python -m unittest discover -s modernization/renderer/tests -v` — PASS, 160 tests.
- `python -m unittest discover -s tests/synthetic -v` — PASS, 630 tests.
- `python -m compileall -q modernization/renderer` — PASS.
- `python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-msvc/Release/d3d8.dll` — PASS; PE32/I386, required exports present, no recursive `d3d8.dll` import.
- `git diff --check` — PASS; Git reports existing CRLF normalization warnings for modified renderer sources.

The native bookmark suite exercises controller capture/restore, positive and negative roll, near-vertical pose, transition settling, velocity and stale-input clearing, FOV preservation, rigid-basis rejection, three-slot serialization, schema/course/build identity, missing/corrupt/oversized files, cross-instance reload, intentional overwrite and failed-path preservation. Its cross-session case reloads through the production JSON reader; a real game-process restart remains part of the human check.

Two existing R-GFX4 analyzer tests initially exposed a test-fixture provenance mismatch: `reflection_tests.exe` has its own caller RVA while the draw classifier records the canonical retail owner RVA. The offline audit now reconstructs learned keys from `semantic_owner_return_rva` and permits the distinct caller only for the exact synthetic reflection-test executable. Both tests pass; production renderer behavior was not changed for this audit correction.

## Binary result

- Path: `modernization/renderer/.build-msvc/Release/d3d8.dll`
- SHA-256: `63729c15fe7abf91a0c337f049759e1216898aefc91f1178f6b5b4ae58dca8d9`
- Size: 1,867,264 bytes
- Architecture: PE32 / I386
- Exports: `Direct3DCreate8` (ordinal 5), `ValidatePixelShader` (ordinal 2), `ValidateVertexShader` (ordinal 3)
- Imported DLLs: `bcrypt.dll`, `USER32.dll`, `KERNEL32.dll`

This verifies the local build artifact only. It does not establish in-game behavior.

## Runtime status

No game runtime test was performed in this task. Human confirmation remains required for the listed same-session save/load, three-slot cycling, close pose/FOV/Roll match, cross-process restart, Clean View, pause, focus-loss, race-restart and native-key-conflict checks in [runtime-handoff.md](runtime-handoff.md). Until then the feature is `READY_FOR_IN_GAME_VALIDATION`, not runtime-confirmed.
