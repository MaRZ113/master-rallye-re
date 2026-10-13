# Actual commands

Working tree: D:\Game\Master Rallye\master-rallye-re-general; master;
HEAD3f837f4ddcb27ee1034a4b0753634c92009360ec. Pre-existing modifications/untracked
research were retained. Course SDK stayed at4244fa0c4d878523c9947f54816bf377cdfb2589.

Executed preflight: git status --short --branch, git branch --show-current,
git rev-parse HEAD, renderer diff integrity, and read-only SDK status.

Source preparation was executed twice using the command in runtime-ab.md.
Both runs verified canonical PS2 inputs and produced the same artifact SHA.
The old turkey3.jsonl capture was read without modifying it or launching the game.

```powershell
$env:MRR_PS2PORT_BUILD_ROOT=(Join-Path (Get-Location) 'ps2-research/pc-port/.build-overlay-course-objects-final')
$env:MRR_PS2PORT_REPORT_PATH=(Join-Path $env:MRR_PS2PORT_BUILD_ROOT 'build-report.json')
$env:MRR_COURSE_OBJECT_TEST_ASSET=(Resolve-Path 'ps2-research/pc-port/.assets/course-objects/Turkey3Puddles.ps2obj').Path
$env:MRR_REFLECTION_TEST_GXI=(Resolve-Path 'ps2-research/pc-port/.assets/reflection/PS2EnvSource64x64.gxi').Path
python ps2-research/pc-port/overlay/build_overlay.py
```

The script independently configured, generated interfaces twice, built both
Win32 Release variants with --parallel1, ran CTest, proxy verification and Python.
Final narrow safety changes were exact-patch staged and generator-checked in a
separate ignored .build-overlay-course-objects-check root, then rebuilt serially:

```powershell
cmake --build ps2-research/pc-port/.build-overlay-course-objects-final/ps2-enabled/build --config Release --parallel 1
ctest --test-dir ps2-research/pc-port/.build-overlay-course-objects-final/ps2-enabled/build -C Release --output-on-failure
& 'ps2-research/pc-port/.build-overlay-course-objects-final/ps2-enabled/build/Release/ps2_course_objects_tests.exe'
$env:MRR_PC_PORT_RENDERER_ROOT=(Resolve-Path 'ps2-research/pc-port/.build-overlay-course-objects-final/ps2-enabled/modernization/renderer').Path
python -m unittest discover -s ps2-research/pc-port/tests -v
python modernization/renderer/tools/verify_proxy.py ps2-research/pc-port/.build-overlay-course-objects-final/ps2-enabled/build/Release/d3d8.dll
python -m compileall -q ps2-research/pc-port/tools ps2-research/pc-port/overlay ps2-research/pc-port/tests
git diff --quiet HEAD -- modernization/renderer
git diff --check
python ps2-research/pc-port/overlay/package_course_objects_handoff.py
```

Build/CTest/proxy outputs remain in ignored logs. Compact final hashes/results
are included. Rebuilding requires the external pinned renderer Git objects,
Python, CMake4.4.3 and Visual Studio18 2026 Win32/MSVC. Canonical asset preparation
requires the original PS2 corpus, but no Course SDK or Blender. Synthetic tests
require no original geometry; optional private-asset tests declare their inputs.

Runtime A/B launches in runtime-ab.md are user instructions only. Codex performed
no DLL deployment, game launch, asset modification, Git commit or push.

The handoff was extracted into an ignored temporary directory and all41 Python
tests passed from the packaged source using external verified staging. ZIP CRC,
full hash-manifest round-trip, repeat serialization and original-asset exclusion
checks passed. Earlier foliage/reflection archive hashes stayed unchanged.
