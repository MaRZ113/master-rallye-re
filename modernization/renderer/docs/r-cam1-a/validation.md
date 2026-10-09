# R-CAM1-A validation record

**Status: `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION`.** Automated validation covers the read-only projection-family classifier and bounded JSON serializer. In-game camera-owner validation is pending. No Freecam is reported as implemented or working.

## Build identity

- Pristine game: `D:\Game\Master Rallye\MRallye.exe`.
- Game SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- PE: PE32/I386, ImageBase `0x00400000`, entry VA `0x005C4602`.

## Automated checks

The camera probe tests verify source45/source90/other/unknown projection classification, owner/pointer read metadata serialization, caller VA/RVA, out-of-range manager count reporting, and non-finite values represented as JSON `null`. A JSON fixture mode is available for a standard-library parser round trip.

Final synthetic results:

| Check | Result |
|---|---|
| Renderer Python suite | **118/118 PASS** (`python -m unittest discover -s modernization/renderer/tests -v`) |
| Native CTest | **10/10 PASS**, including the new camera probe contracts |
| Compileall | **PASS** (`python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization`) |
| Camera owner JSON parser round trip | **PASS** with Python standard-library `json.loads` |
| `git diff --check` | **PASS**, line-ending conversion warnings only |
| Proxy verifier | **PASS**, valid PE32/I386 and all required exports; no recursive `d3d8.dll` import |

The canonical `tools/build.py` configured the fresh Win32 tree but its parallel-4 MSBuild invocation stalled at `Checking Build System` without compile progress and was interrupted. The same configured tree then built successfully with sequential MSBuild:

```powershell
cmake --build modernization/renderer/.build-r-cam1-a --config Release --parallel 1
ctest --test-dir modernization/renderer/.build-r-cam1-a -C Release --output-on-failure
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-r-cam1-a/Release/d3d8.dll
```

Warnings were existing SDK nameless-union and unrelated renderer/test conversion/shadowing warnings; the camera probe introduced no build error. Passing automated checks establish the instrumentation contract only; they do not validate a supported camera context or visual Freecam behavior.

## Candidate DLL

- Path: `modernization/renderer/.build-r-cam1-a/Release/d3d8.dll` (ignored build output; not staged).
- SHA256: `700d6f5c39c78563295aba53321a1ec028c8a9ebe09a2a61ea9051aaf1b40e6d`.
- Size: **1,540,096 bytes**.
- Format: PE32 DLL, I386, ImageBase `0x10000000`.
- Exports: `Direct3DCreate8` ordinal 5, `ValidatePixelShader` ordinal 2, `ValidateVertexShader` ordinal 3.
- Imports: `bcrypt.dll`, `USER32.dll`, `KERNEL32.dll`; no recursive import of `d3d8.dll`.

## In-game evidence

- Camera owner captures: **pending**.
- Source45 frontend exclusion: **pending runtime capture**.
- Replay/Attract/alternate-camera qualification: **pending runtime capture**.
- Freecam movement/culling/restore: **not applicable; feature not implemented**.
- R-GFX5 regressions: automated tests only for this candidate; no new in-game validation was performed.

See [runtime-test-plan.md](runtime-test-plan.md) for the evidence required to resolve the stop gate.
