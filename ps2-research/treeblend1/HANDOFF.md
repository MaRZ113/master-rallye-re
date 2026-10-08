# PS2-TREEBLEND1 research handoff

The phase is a bounded static reverse of tree/treeblend material rendering. It contains **no PC implementation, original game assets, full source meshes or emulator frame capture**.

Start with `ps2-research/treeblend1/final-report.md`, then `findings.md`. The concrete original-word oracle is `instruction-evidence.json`; register masks and unknown inherited fields are in `render-contract.json`; five material/geometry/resource cases are in `foliage-material-matrix.json`. `elf-functions.json` records canonical functions/bounds/call flow. `source-provenance.json` records external identities.

## What works without game data

Python3.11+ standard library is sufficient for the material/GS/color diagnostics and synthetic tests:

```powershell
python ps2-research/tools/foliage_runtime.py states
python -m unittest discover -s ps2-research/tests -v
python -m compileall ps2-research/tools ps2-research/tests
```

Without external roots, corpus-dependent tests use their existing explicit SkipTest conventions; unavailable proprietary data is never called PASS. The archive includes all test modules, tool imports and their small historical JSON fixtures, including UI2/DRESSING1 dependencies. Included older tools' unrelated research-report generation commands are not guaranteed without their external source data/documentation.

Pytest and pytest-subtests are optional test dependencies, not packaged third-party code. With them available:

```powershell
python -m pytest ps2-research/tests -q -p no:cacheprovider
```

The isolated review check uses a copied bundle directory, unset game/SDK/HUD roots and no hidden repository fixtures. Actual counts/results are in `validation.md` and included logs.

## External input roots

| Dependency | Used for |
|---|---|
| `MASTER_RALLYE_PS2_INPUT=D:/Game/Master Rallye PS2` | Canonical ELF/PAK/000/CNF checks, fresh extraction, original words/GXI/PSM integration |
| `MASTER_RALLYE_PC_INPUT=D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked` | Paired retail course DX/TXT and selected DXT comparisons |
| `MASTER_RALLYE_COURSE_SDK=D:/Game/Master Rallye/master-rallye-re-course` | Read-only existing DX/DXT/XML/sidecar parsers; reference HEAD in provenance |
| `PS2_UI_CORPUS=<repo>/ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD` | Older HUD PSB/GXI integration tests only |
| pytest/pytest-subtests | Pytest run only; workstation copy was ignored `data/cdelta1/python` |
| Latest local Ghidra12.1.4 /installed ghidra-bridge | Optional fresh disassembly export; compact original-word review/tests do not require Ghidra |
| Blender/PCSX2 | Not required for this offline bundle; no live capture or Blender scene is claimed |

Set all four external roots to reproduce the full integration regression. Do not point tests at unknown builds. The PC adapter verifies selected DX/TXT hashes against the included frozen WATER1 fixture. Texture/source hashes are also retained explicitly.

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:/Game/Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:/Game/Master Rallye/master-rallye-re-course'
$env:PS2_UI_CORPUS='<repo>/ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD'
python -m unittest discover -s ps2-research/tests -v
```

To regenerate compact cases with PC evidence, use the command in `offline-validation.md`; choose a new ignored output path. Full geometry/GXI inputs stay local, and the tool does not export playable game data. The committed matrix adds explicit review annotations to the reproducible core.

## Integrity and archive workflow

Executed review/archive commands are recorded in `command-log.md`; the following is the reproducible packaging interface:

```powershell
python ps2-research/tools/package_foliage_handoff.py --check-dir ps2-research/data/treeblend1/review-check
python ps2-research/tools/package_foliage_handoff.py --archive ps2-research/data/treeblend1/PS2-TREEBLEND1-handoff.zip
```

The packager reuses the previous CRC/SHA writer, includes only source/docs/compact JSON/validation logs, refuses existing destinations and writes a separate receipt. `MANIFEST.json` has relative paths, sizes, SHA-256 and the **actual source commit**. Manifest self-hashing is deliberately excluded; the external ZIP receipt covers the entire archive. ZIP CRC, per-file SHA and sizes are checked by the writer.

The precommit review copy tests the payload set. The final archive is built after the local research commit, so its manifest identifies that commit. Reports inside that commit identify Ending HEAD by this manifest rather than trying to include their own self-referential Git hash. The final response reports the exact hash.

## Proof boundaries

Material/mode/geometry/resource/CPU packet and GS mask producers are executable-backed. Selected original VU bytes and upload producers are grounded in the canonical ELF. **LIVE_RESIDENCY_UNKNOWN / LIVE_FRAME_NOT_CAPTURED** remain explicit. No file-alpha histogram, synthetic inherited word or passing test is a controlled runtime draw. `offline-validation.md` provides the later read-only capture plan.

Consolidated topic map: `shader-registration.md` covers material contract/lifecycle; `tree-vs-treeblend.md` covers both render paths, alpha/depth/order; `foliage-geometry.md` covers geometry/attributes; `camera-lod-and-animation.md` covers billboard/conditional/animation questions; `course-case-studies.md` covers Turkey/Italy/France controls. This avoids artificial one-paragraph files while preserving all requested subjects.
