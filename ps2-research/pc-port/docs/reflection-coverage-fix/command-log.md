# Executed commands

Commands were run from `master-rallye-re-general`, on master. All source reads
use original/protected corpora; all generated builds reuse canonical roots.

```powershell
git status --short --branch
git branch --show-current
git rev-parse HEAD
git rev-parse HEAD:modernization/renderer
python ps2-research/pc-port/docs/reflection-coverage-fix/source-audit/audit.py
python ps2-research/pc-port/docs/reflection-coverage-fix/wooldand/audit.py
python ps2-research/pc-port/docs/reflection-coverage-fix/modified_correspondence.py
python ps2-research/pc-port/overlay/build_overlay.py
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix/source-audit -p test_audit.py -v
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix/wooldand -p test_join.py -v
```

The build command stages verified immutable objects, applies exact patches,
checks each generator twice, builds both Win32 Release variants with
`cmake --build ... --config Release --parallel 1`, runs CTest, verifies proxy
exports and executes port unittest/compileall. Both builds succeeded.

Verified local fixture environment for the build:
`MRR_REFLECTION_TEST_GXI=.assets/reflection/PS2EnvSource64x64.gxi`,
`MRR_COURSE_OBJECT_TEST_ASSET=.assets/course-objects/Turkey3Puddles.ps2obj`,
`MRR_GRASS_TEST_ASSET=.assets/grass/Turkey3Grass.ps2grass`,
`MRR_SHRUB_TEST_ASSET=.assets/grass/Turkey3Shrubs.ps2grass`,
`MRR_GRASS_MULTI_DIRECTORY=.assets/grass` (resolved to absolute local paths).

```powershell
$env:PYTHONPATH='ps2-research/data/cdelta1/python'
$env:MRR_PC_PORT_RENDERER_ROOT=(Resolve-Path ps2-research/pc-port/.staging/ps2-enabled/modernization/renderer).Path
python -m pytest ps2-research/pc-port/tests -q
python -m compileall -q ps2-research/pc-port/docs/reflection-coverage-fix
git diff --check
git diff HEAD -- modernization/renderer
```

Pytest115 PASS with470 subtests. Both final diff commands succeed; no renderer
source delta. REA used canonical x86 `analyze_function` at0x57707e, followed by
independent PE byte-window verification; see `rea-draw-evidence.json`.

Closeout additionally executed:

```powershell
python -m unittest discover -s ps2-research/pc-port/docs/reflection-coverage-fix -p test_modified_materials.py -v
python -m compileall -q ps2-research/pc-port/overlay/package_reflection_coverage_fix.py ps2-research/pc-port/docs/reflection-coverage-fix
git diff --check
python ps2-research/pc-port/overlay/package_reflection_coverage_fix.py
```

The first metadata assertion failed by treating raw Navara3/4 counts as
nondegenerate counts; corrected3/1 degenerate qualification then3/3 PASS.
Packaging runs16 corpus-independent checks from an extracted archive, verifies
CRC and all SHA-256 entries, and checks repeated byte-identical serialization.
No game launch, deployment, original asset writes or push were performed.
