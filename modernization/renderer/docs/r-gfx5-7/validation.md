# R-GFX5-7 validation record

## Status

`READY_FOR_DIAGNOSTIC_RUNTIME` is the intended checkpoint if implementation, regression suites, and Win32 verification pass. Windowed live resizing is ready for human testing. Exclusive remains unresolved pending a causal runtime trace. This document must not be read as a game-runtime pass.

## Source and handoff

- Repository: `master-rallye-re-general`
- Branch: `master`
- Starting HEAD: `f43d720e08961791ad46875af0d15430ed555e02`
- PC-VISUAL-PILOT1 CPU upload provenance: preserved from that commit
- Foliage Mode 1: still blocked and Stock
- Foliage diagnostics: off by default; no material override added
- PreserveMargins v2: `CONFIRMED_BY_RUNTIME` from the user's prior test report

## Test results

`CONFIRMED_BY_SYNTHETIC_TEST`:

- Native CTest: 9/9 passed, including Windowed live resize/maximize/restore, Exclusive lifecycle/HRESULT forwarding, foliage provenance, COM/resource lifetime, FOV, vehicles, reflections, and existing renderer contracts.
- Python renderer suite: 114/114 passed. The run used `.analysis/tmp` for temporary files because the sandbox denies writes to its system `%TEMP%` directory.
- `python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization`: passed.
- `git diff --check`: passed before final commit.

The repository's `tools/build.py` uses MSBuild parallelism 4 and three attempts stopped after the MSBuild banner without progressing in this environment. The same configured Win32 tree completed successfully with sequential MSBuild:

```powershell
cmake --build modernization/renderer/.build-msvc --config Release --parallel 1
cmake --build modernization/renderer/.build-msvc --config Release --target RUN_TESTS --parallel 1
```

The build reported 0 errors. The generated `d3d8.dll` verified as PE32/I386 (machine `0x014C`), with required exports `Direct3DCreate8`, `ValidatePixelShader`, and `ValidateVertexShader`; imports are `bcrypt.dll`, `USER32.dll`, and `KERNEL32.dll`, with no recursive `d3d8.dll` import.

Final output: `modernization/renderer/.build-msvc/Release/d3d8.dll`, 1,502,720 bytes, SHA-256 `dd07359719a71f6b64fe56d49f384d9dd75cc04121831adb539f338c6abe140d`; file timestamp `2026-10-09 20:34` local. The verifier reports PE timestamp `778513332`.

Evidence grades remain separate:

- `CONFIRMED_BY_SOURCE`: implementation and static data flow reviewed.
- `CONFIRMED_BY_EXE`: exact-build Ghidra instructions at `0x0055AB90` and `0x0055AED0`.
- `CONFIRMED_BY_SYNTHETIC_TEST`: mock lifecycle assertions.
- `CONFIRMED_BY_RUNTIME`: only behavior actually reported by the user.
- `UNKNOWN`: current Exclusive causal transition and physical Windowed resize behavior on this build.

## Final build and commit

The game was not launched and no hardware/runtime behavior is claimed from this validation. Commit and final worktree state are recorded in the closeout report; no generated DLL/PDB/OBJ/LIB/EXP or runtime capture is part of the commit.
