# Executed commands

Working directory: D:/Game/Master Rallye/master-rallye-re-general, master.
Pre-existing unrelated documentation/research changes were preserved.

```powershell
git status --short --branch
git rev-parse HEAD
git rev-parse HEAD:modernization/renderer
python ps2-research/pc-port/docs/full-coverage/vehicles/audit.py
python ps2-research/pc-port/docs/full-coverage/vehicles/test_audit.py
python ps2-research/pc-port/docs/full-coverage/courses/prepare_all.py --ps2 'D:/Game/Master Rallye PS2' --pc 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --publish --budget 1000000
python ps2-research/pc-port/docs/full-coverage/courses/validate_registry.py
python ps2-research/pc-port/docs/full-coverage/courses/test_prepare_all.py
```

The initial diagnostic generation cap was1M; observed maximum288863 led to a
final300000 cap without altering artifact bytes. Exact France special-stage
ownership was resolved from canonical source resource identity.

Before both serial build runs:

```powershell
$env:MRR_REFLECTION_TEST_GXI=(Resolve-Path ps2-research/pc-port/.assets/reflection/PS2EnvSource64x64.gxi).Path
$env:MRR_COURSE_OBJECT_TEST_ASSET=(Resolve-Path ps2-research/pc-port/.assets/course-objects/Turkey3Puddles.ps2obj).Path
$env:MRR_GRASS_TEST_ASSET=(Resolve-Path ps2-research/pc-port/.assets/grass/Turkey3Grass.ps2grass).Path
$env:MRR_SHRUB_TEST_ASSET=(Resolve-Path ps2-research/pc-port/.assets/grass/Turkey3Shrubs.ps2grass).Path
$env:MRR_GRASS_MULTI_DIRECTORY=(Resolve-Path ps2-research/pc-port/.assets/grass).Path
python ps2-research/pc-port/overlay/build_overlay.py
python ps2-research/pc-port/docs/full-coverage/msaa/run_native_smoke.py
python ps2-research/pc-port/docs/full-coverage/measure_native_cache.py
```

The build script actually invoked both Win32 Release builds with --parallel1,
CTest, export verification and generators twice. The second incremental run
included corrected generic/new-car diagnostic labels. The standalone MSAA
compiler's first cmd quoting attempt failed; stdin-command invocation was fixed
in its own script, without renderer/build configuration changes. Final native
smoke performed all six cases and bounded synthetic output readback.

Full suites:

```powershell
python -m unittest discover -s modernization/renderer/tests -v
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/pc-port/tests -q
python -m pytest ps2-research/tests -q
python -m compileall -q ps2-research/pc-port/docs/full-coverage ps2-research/pc-port/tools ps2-research/pc-port/tests
git diff --check
```

PS2 suites used existing bundled Codex Python with Pillow, original PS2 root,
protected retail PC root, read-only Course SDK and ignored UI1 extraction via
MASTER_RALLYE_PS2_INPUT,MASTER_RALLYE_PC_INPUT,MASTER_RALLYE_COURSE_SDK,
PS2_UI_CORPUS. Pytest came from existing ignored data/cdelta1/python. Frozen
renderer suite used existing local Capstone dependency; pefile remains missing.
No installs/upgrades or silent skips. Original ELF/PC EXE hashes and clean SDK/
renderer status were checked again after builds.

Runtime deployment/A-B steps in runtime-ab.md are instructions only. No game
launch, deployment, course modification or game FPS capture was performed.
