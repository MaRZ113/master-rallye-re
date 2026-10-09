# R-CAM1-A1 validation record

**Status: `READY_FOR_CAMERA_DIAGNOSTIC_VALIDATION`.** The exact-build gameplay VIEW site and the corrected production gate are verified. Automated validation passed. Fresh in-game owner captures remain pending; this result does not establish a safe Freecam owner or implement Freecam movement.

## Build identity and callsite evidence

- Pristine game: `D:\Game\Master Rallye\MRallye.exe`.
- SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- File size: **3,121,214 bytes**; PE32/I386; timestamp `0x3C02695D`; ImageBase `0x00400000`; entry VA `0x005C4602`.
- At VA `0x00561A1B`, the function pushes `2` (`D3DTS_VIEW`); the indirect D3D8 call begins at `0x00561A20` through vtable offset `0x94` (slot 37, `SetTransform`); the return VA is `0x00561A26`, RVA `0x00161A26`.
- Exact-binary disassembly and the existing read-only Ghidra export for `FUN_005614A0` agree. Gameplay PROJECTION remains VA/RVA `0x0053FA75` / `0x0013FA75`; UI PROJECTION and VIEW remain `0x00561ED3` / `0x00161ED3` and `0x00561FDC` / `0x00161FDC`.

## Automated validation

| Check | Result |
|---|---|
| Renderer Python suite | **118/118 PASS**. `TEMP` and `TMP` were redirected to ignored `modernization/renderer/.analysis/test-temp` because the sandbox's default C: temporary directory denied writes. |
| Native CTest | **10/10 PASS**, including production camera gate, frame accounting, serialization, and wrapper forwarding contracts. |
| Camera observation JSON round trip | **PASS** using Python `json.loads` for complete-owner and partial-owner sequence payloads; both identify caller RVA `0x00161a26`. |
| Compileall | **PASS** (`python -X pycache_prefix=modernization/renderer/.analysis/pycache -m compileall -q modernization`). |
| Proxy verification | **PASS**; PE32/I386, required exports present, no recursive `d3d8.dll` import. |
| `git diff --check` | **PASS**; only line-ending conversion warnings. |

The canonical `build.py` configured successfully, then its parallel-4 MSBuild stalled at `Checking Build System` without compile progress. The process was interrupted and the same tree built successfully with sequential MSBuild:

```powershell
cmake --build modernization/renderer/.build-r-cam1-a --config Release --parallel 1
ctest --test-dir modernization/renderer/.build-r-cam1-a -C Release --output-on-failure
python modernization/renderer/tools/verify_proxy.py modernization/renderer/.build-r-cam1-a/Release/d3d8.dll
```

FOV/culling, PreserveMargins, Windowed and Borderless paths, foliage F10 behavior, and upload provenance were covered by the passing existing regression suites. Exclusive handling was not changed. `Device8::SetTransform` retains original pointer forwarding and native HRESULT; no camera or EXE hook was added.

## Candidate DLL

- Path: `modernization/renderer/.build-r-cam1-a/Release/d3d8.dll` (ignored build output; not staged).
- SHA256: `fee1af00f4698c4e10b6cc43ac05b170a8bd91fb49a936ebac2655b200ea181d`.
- Size: **1,543,680 bytes**.
- Format: PE32 DLL, I386, ImageBase `0x10000000`.
- Exports: `Direct3DCreate8` ordinal 5, `ValidatePixelShader` ordinal 2, `ValidateVertexShader` ordinal 3.
- Imports: `bcrypt.dll`, `USER32.dll`, `KERNEL32.dll`; no recursive `d3d8.dll` import.

## In-game evidence

- Corrected gameplay VIEW diagnostic: **pending three fresh captures**.
- Source45 frontend observation: **pending capture or matching frame-summary skip reason**.
- Source90 default and alternate France1 camera owner data: **pending capture**.
- Freecam movement, culling, and restore: **not implemented; not tested**.

Use the three-capture procedure in [runtime-test-plan.md](runtime-test-plan.md). The full owner payload is in the session JSONL; bounded reason/status is also attached to each completed F10 frame summary.
