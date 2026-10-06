# R-MAT1 validation and reproduction

All runs use the main checkout and protected retail vehicle corpus, with game
sources read-only. Raw exports, decoded PNGs, synthetic assets, DX verification
copies, ZIP, Blender profiles and saved scenes stay under ignored
`.research-output/r-mat1/`. No original EXE/archive/DX/DXT was written.

## Baseline and final checks

| Check | Baseline | Final |
|---|---|---|
| Synthetic unittest discovery | 245 passed, 0 failed, 0 skipped | 254 passed, 0 failed, 0 skipped |
| compileall src/tools/tests | PASS | PASS |
| Existing R4E synthetic attribute smoke | PASS | PASS |
| Existing R4E full-corpus zero-edit Blender export | 78/78 byte-identical | 78/78 covered again by loaded-texture R-MAT1 audit |
| Standard synthetic importer smoke | available | PASS: operators, UV/raster, normals, collision, warning scope, provenance, save/reload, position export |
| ZIP build/install and vendored import/export | available | PASS; V3 and vendored semantic model asserted |
| Loaded-texture material audit | absent | PASS: 1478 draws, 78 resources, eight helper names, 1089 env previews |
| Corpus material inventory/hardening | 1478 draws, matches existing counts | 1478 CLASSIFIED, 0 UNKNOWN; hashes/raw rows retained |
| diff check | PASS | PASS |

Blender is 5.2.2 LTS, hash `d13f752e3b9c`. The R-MAT1 script checks one mesh
per resource, material counts, raw controls/flags/mask/ordered slots, exact
semantic annotations, node image identity, diffuse/UV gates, alpha linkage,
generic env graph, the five NULL-base cases and Reflections OFF. It also tests
synthetic alphatest and an explicit UNKNOWN variant, save/reload, image paths,
78 source-identical exports and another source-identical export after clearing
preview nodes. There are zero final failure/skip cases in the vehicle runs.
Course installation test mode was NOT_RUN because it is outside this phase.

Development test harness fixes retain validation strength: AttributePatch is
checked through its output bytes, missing-texture diagnostics preserve the
existing searchable message prefix, and the standard saved-image existence
check resolves Blender `//` paths via `bpy.path.abspath` before calling Path.
No export/provenance check was disabled. The R4D.1 test's ordinary draw fixture
now uses stock variant=0, with a separate explicit UNKNOWN-variant test.

## Reproduction

From the checkout root (PowerShell):

```powershell
python -m unittest discover -s tests/synthetic -v
python -m compileall src tools tests
python tools/scanner/r_mat1_corpus.py '..\corpora\retail\Data.sma_unpacked\DataGx\Vehicles' --output research/r-mat1/corpus-validation.json
python tests/blender/generate_fixture.py .research-output/r-mat1/fixture
python tools/build_blender_addon.py --output .research-output/r-mat1/package/master_rallye_io.zip
```

Use the existing Blender executable under
`_reverse-tools/blender-5.2.2-windows-x64/blender.exe`, with
`--background --factory-startup --python-exit-code 1 --python <script> -- <args>`.
Set TEMP/TMP and BLENDER_USER_RESOURCES to this checkout's ignored temporary
cache/profile directories so the test's PNGs and installed ZIP remain local.

| Script | Arguments after -- |
|---|---|
| tests/blender/import_smoke.py | fixture directory, output.blend, report.json |
| tests/blender/r4e_smoke.py | fixture directory, output directory |
| tests/blender/r_mat1_smoke.py | protected vehicle root, output directory |
| tests/blender/addon_install_smoke.py | generated ZIP, fixture/synthetic.dx |

For static evidence, run the bridge's `.venv/Scripts/python.exe` with
`tools/scanner/r_mat1_exe.py`, explicit hexadecimal addresses, newest installed
Ghidra path, main-checkout project path and ignored output. Example:

```powershell
& '..\_reverse-tools\ghidra-bridge-main\.venv\Scripts\python.exe' tools/scanner/r_mat1_exe.py 5528b0 576970 577620 5781b0 580360 5860a0 586560 586150 5867a0 564ee0 562560 562810 562430 583880 5c4df0 5c2e5c --install '..\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC' --project _ghidra_project --output .research-output/r-mat1/ghidra --data 6911d0 69270c 692714 692364
```

The helper hash-locks the analyzed target, confines evidence to this checkout,
opens the program read-only and rolls back temporary method disassembly. Raw
function exports contain assembly/decompilation/high-pcode/CFG and xrefs;
their tracked index identifies exact local evidence without committing a
Ghidra database or game asset.

No new human runtime validation was performed. No runtime experiment is
required by the remaining decision gate. Damage fade and pixel parity remain
explicit boundaries, not automated runtime passes.
