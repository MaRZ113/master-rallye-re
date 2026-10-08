# PS2-DRESSING1 research handoff

Start with ps2-research/dressing1/final-report.md, then the four case reports and
novel-candidates.json. Every candidate includes bounds, original material/texture
slots, ancestor paths/offsets, multiple component methods, PC searches, precise
fit qualifiers and explicit instance/live-state unknowns. No earlier handoff
needs to be manually assembled for the supplied corpus-independent tests.

The archive contains DRESSING1 documents/compact JSON, all current research
Python tools/tests, required UI2/WATER1/REFL1/CDELTA1/GEOM1 small JSON fixtures,
synthetic fixtures embedded in tests, original bounded instruction probes,
command/provenance records and a file-level SHA256 manifest. It excludes game
binaries, extracted PSM/DX/GXI, full meshes, original textures, maps/screenshots,
raw Ghidra projects and the pre-existing user ps2-research.zip.

## Corpus-independent review and tests

From the extracted bundle root with Python3.10 or newer:

```powershell
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q -p no:cacheprovider
python -m compileall ps2-research/tools ps2-research/tests
```

Unittest/diagnostic math use the standard library. Pytest requires pytest and
pytest-subtests; they are not packaged. Historical synthetic XML tests also
depend on the separate Course SDK. Missing SDK/game/HUD fixtures are declared
SKIP dependencies; unexpected errors remain failures. See validation.md for the
actually executed isolated/full results.

## Private inputs for full regression and regeneration

```text
MASTER_RALLYE_PS2_INPUT=D:/Game/Master Rallye PS2
MASTER_RALLYE_PC_INPUT=D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked
MASTER_RALLYE_COURSE_SDK=D:/Game/Master Rallye/master-rallye-re-course
PS2_UI_CORPUS=<complete ignored HUD folder with PSB and all referenced GXI>
```

The PS2 root requires the four canonical files with source-provenance.json
identities. PC requires selected retail DX/TXT and RaceTest XML; compiled DX is
authoritative and GXM is not required. The read-only SDK reference is commit
4244fa0c4d878523c9947f54816bf377cdfb2589, supplying src/master_rallye readers.
SDK imports disable bytecode writes. SDK source is not included in this archive.
The historical UI2 fixture also requires ignored data/ui2/ITALYS1.XML. The full
workstation suite used the existing complete data/ui1/extracted/TNG/DATAPSM/HUD;
the smaller data/validation folder was insufficient and produced a recorded
failed first attempt. No historical tests were weakened.

To recreate private diagnostics, using your verified roots:

```powershell
python ps2-research/tools/dressing_runtime.py --ps2-root "D:/Game/Master Rallye PS2" --pc-root "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked" --sdk "D:/Game/Master Rallye/master-rallye-re-course" --output ps2-research/data/dressing1/inventory-final.json --compact-output ps2-research/data/dressing1/inventory-final-compact.json
python ps2-research/tools/dressing_visualize.py --inventory ps2-research/data/dressing1/inventory-final.json --ps2-root "D:/Game/Master Rallye PS2" --pc-root "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked" --sdk "D:/Game/Master Rallye/master-rallye-re-course" --output-directory ps2-research/data/dressing1/maps
```

Full diagnostics and SVG source geometry must stay ignored. No Blender dependency
or add-on installation is needed. The optional PNG inspection used Pillow and a
private rasterization helper; that PNG is excluded. Raw Ghidra query regeneration
needs the latest observed D: Ghidra12.1.4, installed ghidra-ai-bridge/PyGhidra,
JDK and the private hash-locked PackFS project/profile. The archive's instruction
probes permit source inspection without those tools. Queries roll back every
analysis-only surrogate and never patch the canonical ELF.

command-log.md separates actual commands from deferred runtime recipes. The
post-commit archive MANIFEST.json and external ZIP_SHA256 receipt identify the
actual final commit; committed Markdown cannot recursively contain its own SHA.
Exactly one next recommendation is PS2-TREEBLEND1; it has not begun.
