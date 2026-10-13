# Executed commands and dependencies

From `D:/Game/Master Rallye/master-rallye-re-general`, master:

```powershell
git status --short --branch
git rev-parse HEAD
git commit -m 'research: preserve paused rigid admission and HUD evidence'
python ps2-research/pc-port/overlay/build_overlay.py
```

Reflection-only checkpoint passed24/30 CTest and107 Python tests. The first
precision mock failed on allocation-attempt parity; repaired mock allocation
success tracking, not production state behavior. The historical byte-identical
Tata-only classifier textual check was replaced by the authorized two-entry
registry contract, with original Tata signature and native safety gates retained.

Private vegetation production, both original inputs read-only:

```powershell
python ps2-research/pc-port/docs/grass-port3/compare_selected.py --ps2 'D:/Game/Master Rallye PS2' --pc 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --course FRANCE1 --output ps2-research/pc-port/.analysis/grass3-france-publish.json --asset-directory ps2-research/pc-port/.assets/grass
python ps2-research/pc-port/docs/grass-port3/compare_selected.py --ps2 'D:/Game/Master Rallye PS2' --pc 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --course ITALY_S1 --output ps2-research/pc-port/.analysis/grass3-italy-publish.json --asset-directory ps2-research/pc-port/.assets/grass
$env:MRR_GRASS_TEST_ASSET=(Resolve-Path ps2-research/pc-port/.assets/grass/Turkey3Grass.ps2grass).Path
$env:MRR_SHRUB_TEST_ASSET=(Resolve-Path ps2-research/pc-port/.assets/grass/Turkey3Shrubs.ps2grass).Path
$env:MRR_GRASS_MULTI_DIRECTORY=(Resolve-Path ps2-research/pc-port/.assets/grass).Path
python ps2-research/pc-port/overlay/build_overlay.py
```

New three-course native private-input checks actually ran. A stale textual
Turkey3-only menu assertion failed once, then was updated for explicit per-grass
source admission, preserving its preflight-before-Broker/GPU ordering checks
and the original water gate. Final builds passed24/30 CTest, exports,
deterministic generators and107 Python tests. No full clean or new build tree.

Further private-input CTest7/7 used:

```powershell
$env:MRR_REFLECTION_TEST_GXI=(Resolve-Path ps2-research/pc-port/.assets/reflection/PS2EnvSource64x64.gxi).Path
$env:MRR_COURSE_OBJECT_TEST_ASSET=(Resolve-Path ps2-research/pc-port/.assets/course-objects/Turkey3Puddles.ps2obj).Path
ctest --test-dir ps2-research/pc-port/.build/ps2-enabled -C Release --output-on-failure -R '^(hud_visibility_contracts|ps2_.*)$'
python ps2-research/pc-port/docs/grass-port3/test_inventory.py
```

Full applicable suite commands:

```powershell
python -m unittest discover -s modernization/renderer/tests -v
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/pc-port/tests -q
python -m pytest ps2-research/tests -q
```

Default Python315 lacks Pillow/Capstone/pefile. PS2 research rerun used the
already bundled Codex dependency Python with Pillow12.3.0; public pytest9.1.1
dependencies came from existing ignored `data/cdelta1/python` via PYTHONPATH.
The Ghidra-bundled Capstone5.0.6 wheel was locally extracted under ignored
`.analysis/test-deps` for the original renderer tests; no global software was
installed/upgraded. That rerun has188 passes and1 import error for pefile.
Canonical corpus variables for345/345 research runs:
MASTER_RALLYE_PS2_INPUT,MASTER_RALLYE_PC_INPUT,MASTER_RALLYE_COURSE_SDK and
PS2_UI_CORPUS set to the existing original/retail/SDK/HUD extraction paths.
Initial dependency failures remain in ignored `.build/logs`, not hidden.
Port-local `.gitattributes` preserves exact `.patch` bytes (`-text`) and permits
their required blank context-line marker in whitespace checks. Actual source
whitespace policy is unchanged; no patch content/hash or global Git setting
was altered to clear this patch-format-only diagnostic.

Port pytest107+48 subtests; PS2 pytest345+290 subtests. Compileall, exact
baseline/patch hashes, original EXE/ELF hashes, Git diff-check and unchanged
Course SDK were checked. Packaging validates current source hashes against the
successful stage/build report before archiving both DLLs, CRC, SHA-256 and
deterministic regeneration. Runtime recipes are proposed user commands, not
executed gameplay/deployment.
