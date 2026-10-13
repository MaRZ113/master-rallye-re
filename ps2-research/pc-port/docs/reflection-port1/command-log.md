# Commands and external dependencies

Executed in D:\Game\Master Rallye\master-rallye-re-general on master.
HEAD 3f837f4ddcb27ee1034a4b0753634c92009360ec stayed unchanged.
CMake 4.4.3; Visual Studio 18 2026; MSVC 19.51.36260.0; Windows SDK
10.0.26100.0; Win32 Release; serial MSBuild.
Private source paths are needed only for source verification/local asset preparation.

## Executed preflight/source checks

```powershell
git status --short --branch
git branch --show-current
git rev-parse HEAD
git log --oneline -8
git -C 'D:/Game/Master Rallye/master-rallye-re-course' status --short --branch
git -C 'D:/Game/Master Rallye/master-rallye-re-course' rev-parse HEAD
```

Course SDK reference HEAD: 4244fa0c4d878523c9947f54816bf377cdfb2589; clean.
The source-preparation command shown in runtime-ab.md was executed with the
canonical PS2 corpus and protected retail PC corpus. Its compact output is
material-source-contract.json; the original GXI resides only in ignored .assets.
All 78 retail vehicle DX files were checked for the target face signature; only
Tata/car.dx record 19 matched. The REA byte probe and independent PE-byte check
are recorded in pc-executable-cross-check.json.

## Executed independent builds

```powershell
$env:MRR_PS2PORT_BUILD_ROOT=(Join-Path (Get-Location) 'ps2-research/pc-port/.build-overlay-reflection1-final')
$env:MRR_PS2PORT_REPORT_PATH=(Join-Path $env:MRR_PS2PORT_BUILD_ROOT 'build-report.json')
python ps2-research/pc-port/overlay/build_overlay.py
```

The script staged from pinned Git objects, checked exact patches and ran:

```powershell
cmake --build ps2-research/pc-port/.build-overlay-reflection1-final/baseline/build --config Release --parallel 1
ctest --test-dir ps2-research/pc-port/.build-overlay-reflection1-final/baseline/build -C Release --output-on-failure
cmake --build ps2-research/pc-port/.build-overlay-reflection1-final/ps2-enabled/build --config Release --parallel 1
ctest --test-dir ps2-research/pc-port/.build-overlay-reflection1-final/ps2-enabled/build -C Release --output-on-failure
```

After narrow strict-config and Reset safety changes, the final PS2 variant was
rebuilt serially and all 26 CTest cases repeated. The enabled-image lifecycle case
was additionally executed with this environment:

```powershell
$env:MRR_REFLECTION_TEST_GXI=(Resolve-Path 'ps2-research/pc-port/.assets/reflection/PS2EnvSource64x64.gxi').Path
ctest --test-dir ps2-research/pc-port/.build-overlay-reflection1-final/ps2-enabled/build -C Release --output-on-failure
& 'ps2-research/pc-port/.build-overlay-reflection1-final/ps2-enabled/build/Release/ps2_reflection_pilot_tests.exe'
$env:MRR_PC_PORT_RENDERER_ROOT=(Resolve-Path 'ps2-research/pc-port/.build-overlay-reflection1-final/ps2-enabled/modernization/renderer').Path
python -m unittest discover -s ps2-research/pc-port/tests -v
python modernization/renderer/tools/verify_proxy.py ps2-research/pc-port/.build-overlay-reflection1-final/baseline/build/Release/d3d8.dll
python modernization/renderer/tools/verify_proxy.py ps2-research/pc-port/.build-overlay-reflection1-final/ps2-enabled/build/Release/d3d8.dll
python -m compileall -q ps2-research/pc-port/renderer ps2-research/pc-port/tests ps2-research/pc-port/tools ps2-research/pc-port/overlay
git diff --quiet HEAD -- modernization/renderer
git diff --check
```

Build/proxy/CTest/Python command output remains in ignored build logs and
.analysis/reflection-port1. Compact results and final artifact hashes are included.

## Handoff command

```powershell
python ps2-research/pc-port/overlay/package_reflection_handoff.py
```

The packager verifies frozen sources, exact patch/source/staging/DLL hashes,
then writes a sorted fixed-timestamp ZIP, manifest and archive checksum. It
checks repeated serialization, CRC and every manifest member. Package integrity
is separate from runtime acceptance.

The generated archive was additionally extracted into a temporary ignored
.analysis directory. All 25 Python tests passed from that extraction with
MRR_PC_PORT_RENDERER_ROOT pointing to the verified external staging tree; no
private corpus was used by that test run. Four canonical PS2 SHA-256 hashes
were rechecked after the builds. No source/asset writes were performed by those
checks.

## Independent review/rebuild requirements

The tree-lock tests and compact source-witness tests require Python/Git only.
Native rebuilding and full integration tests additionally require an external
Git checkout containing the pinned baseline objects and the Windows toolchain.
The repository's full frozen renderer is not copied into the handoff.
prepare_reflection_pilot.py additionally needs original PS2 PackFS inputs,
protected retail PC files and the read-only Course SDK. Blender is not required.
The A/B game launches are instructions only; they were not executed by Codex.
