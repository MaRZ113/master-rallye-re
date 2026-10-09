# PS2-AMBIENT2 independent research handoff

This bundle contains the bounded BirdManager static reverse, tools/tests, compact course/layout/motion/resource/render contracts, original short ELF/VU probes, a synthetic flight trace, and small historical regression JSON dependencies. It excludes original ELF/PAK/000/XML/PSB/GXI/PSM/DX, textures, full point arrays, RAM/VRAM, screenshots and Ghidra databases.

`MANIFEST.json` covers every payload's path/size/SHA-256 and identifies the source Git commit. The external ZIP receipt covers archive SHA/size; the shared writer also checks ZIP CRC and every manifest row. Final ZIP is built after the local phase commit. The archive is a research handoff, not an installable Content Pack.

## Without proprietary inputs

Python3.10+ standard library is sufficient for unittest and the diagnostic. Install/use pytest in your normal environment for pytest. From bundle root:

```powershell
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q -p no:cacheprovider
python -m compileall ps2-research/tools ps2-research/tests
```

Corpus-independent tests cover integer RNG/float32 motion, original short instruction interpretation, point-parser semantics, billboard/animation/GS contracts and historical synthetic fixtures. Dependent tests skip explicitly when their original input roots are absent. Do not interpret those skips as successful integration or silently treat missing included JSON as an external dependency. Exact isolated results are in `validation.md` and logs.

`bird_runtime.py contract` can use the included static JSON. Synthetic trace requires a JSON state with `origin`, `observer`, `seed`; a15-step example is included as `synthetic-flight-trace.json`. Example-only new output commands:

```powershell
python ps2-research/tools/bird_runtime.py contract --output ps2-research/data/ambient2/review-contract.json
python ps2-research/tools/bird_runtime.py trace --state explicit-synthetic-state.json --steps 15 --output ps2-research/data/ambient2/review-trace.json
```

Use new filenames; existing diagnostic outputs are preserved. A seed alone cannot reproduce a course's global RNG interleaving. Synthetic trace does not load source points or imply a live count.

## External integration dependencies

| Input | Needed for |
|---|---|
| Canonical PS2 root `D:/Game/Master Rallye PS2` | All four exact hashes, PackFS extraction, original XML/PSB/GXI/ELF integration |
| PC retail root `D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked` | Historical cross-platform geometry/texture and source tests; bounded PC scan |
| Read-only SDK `D:/Game/Master Rallye/master-rallye-re-course` | Historical DX/scene parsers; HEAD4244fa0c4d878523c9947f54816bf377cdfb2589 |
| Original extracted HUD at ignored`data/ui1/extracted/TNG/DATAPSM/HUD` | UI1 integration; assets are not in bundle |
| Optional ignored ITALYS1 XML fixture | Existing UI2 integration according to its explicit test convention |
| Ghidra12.1.4 / installed ghidra-bridge / JDK | Re-querying canonical executable; not needed for bundled short-probe tests |
| PCSX2 | Future live capture only; not performed in this phase |

Configured example-only integration setup:

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:/Game/Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:/Game/Master Rallye/master-rallye-re-course'
$env:PS2_UI_CORPUS='<checkout>/ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD'
python -m unittest discover -s ps2-research/tests -v
```

The same dependency configuration was actually used in the primary checkout; literal workstation commands and captured results are in `command-log.md`/`validation-logs/`. Pytest on that workstation was available under ignored`data/cdelta1/python`; neither the package nor game data is bundled. Blender is unnecessary. No UI/emulator automation framework or game patch is required for the offline results.

## Review order and proof boundary

Start at `final-report.md`, then `manager-lifecycle.md`, `flight-motion.md`, `orientation-and-animation.md` and `draw-pipeline.md`. Check original words in`instruction-probes.json`, addresses/fields in`elf-functions.json`, and tested bank/program identities. Source points versus pool/active/drawn/visible counts are separate. Live list-registry pointers, Animals/MaxBirds, global random history, cadence, Miller population, inherited GS words and live VU/frame are UNKNOWN. The static flying-bird chain is closed within these explicit inputs; runtime validation remains NOT_PERFORMED.
