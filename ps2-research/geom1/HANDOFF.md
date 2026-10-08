# PS2-GEOM1 research handoff

This bundle contains the read-only geometry bridge, synthetic tests, selected
compact original-data facts and prior small JSON fixtures. It contains no game
binaries, complete meshes, original textures, screenshots or rich level exports.
The geometry delta map is a selected evidence inventory, not a converted course.

Start with ps2-research/geom1/final-report.md and validation.md. The comparison
separates PS2 visual source meshes from spatial triangles, PC compiled draws,
scene instances and live visibility. Unmatched labels are bounded candidates.
Exactly one next research recommendation is PS2-DRESSING1; it has not begun.

## Without external game data

From the extracted bundle root, use Python 3.10 or newer:

    python -m unittest discover -s ps2-research/tests -v
    python -m pytest ps2-research/tests -q -p no:cacheprovider
    python -m compileall ps2-research/tools ps2-research/tests

Unittest and the geometry algorithms use the standard library. Pytest additionally
requires pytest and pytest-subtests. Install these in your normal test environment;
they are not included in the archive. Some historical tests need the external SDK
even for synthetic XML parsing; absence is an explicit SKIP. Original-corpus
integration tests likewise skip with dependency messages. Unexpected errors must
not be reclassified as dependency skips. See validation.md for actual run counts.

The manifest includes all supplied Python test modules, all research Python tools,
and four UI2 JSON fixtures, WATER1 case/function/render fixtures, REFL1 resource/
vehicle/function/render fixtures and CDELTA1 course-pairs.json. No assembly of
older bundles is needed to run the corpus-independent subset.

## External inputs for full integration

Set these environment variables to your own verified local paths:

    MASTER_RALLYE_PS2_INPUT=D:/Game/Master Rallye PS2
    MASTER_RALLYE_PC_INPUT=D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked
    MASTER_RALLYE_COURSE_SDK=D:/Game/Master Rallye/master-rallye-re-course
    PS2_UI_CORPUS=<ignored extracted HUD directory containing PSB/GXI dependencies>

The canonical PS2 root must contain SLES_509.06, SYSTEM.CNF, TNG.PAK and TNG.000
with the identities in source-provenance.json. PC inputs are compiled retail DX,
TXT sidecars and paired RaceTest XML; GXM source files are not required. Hashes
and exact PC resource paths are recorded in the source manifests. The separately
obtained SDK must supply its src/master_rallye parsers; the verified reference
commit is 4244fa0c4d878523c9947f54816bf377cdfb2589. It is read-only, with bytecode
writes disabled by the adapter. SDK source is not repackaged here.

The historical UI2 XML test also requires the original extracted ITALYS1.XML in
ps2-research/data/ui2/. Full workstation regression used that existing private
fixture; it is excluded from this archive. PS2_UI_CORPUS likewise points at private
previously extracted HUD assets, never a file shipped by the bundle.

## Recreate source comparisons

From the bundle root, replace the three external roots as appropriate. This is
an example command; command-log.md distinguishes actual runs from recipes:

    python ps2-research/tools/geometry_delta.py --course TURKEY3 --ps2-root "D:/Game/Master Rallye PS2" --pc-root "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked" --sdk "D:/Game/Master Rallye/master-rallye-re-course" --profile baseline --output ps2-research/data/geom1/TURKEY3.json --svg ps2-research/data/geom1/TURKEY3.svg

Repeat with FRANCE1 and ITALY_S1. Explicit course selection resolves canonical
PackFS paths and the independently paired PC course folder; a similarly named
unverified input is rejected. Use --profile strict or relaxed and a different
output filename for sensitivity analysis. Full mesh-derived reports/visuals must
stay under ignored ps2-research/data/geom1/. Never package them as content assets.
After the three baseline reports exist, copy the supplied independently checked
ordinary-anchor metadata into the diagnostic folder, then build the compact
selected inventory:

    python -c "import shutil; shutil.copyfile('ps2-research/geom1/nonwater-anchors.json', 'ps2-research/data/geom1/nonwater-anchors.json')"

    python ps2-research/tools/build_geometry_report.py --directory ps2-research/data/geom1 --output ps2-research/data/geom1/geometry-delta-map.json

That report is reviewable metadata; copying it to research documentation is a
manual scoped review step. Full per-face relation logs and timings are excluded
from deterministic core hashes. The known WATER1 and ordinary-ground anchors
are integration tests. All three baseline core reports were reproduced byte for
byte; hashes are in reproducibility.json.

## Visualization and optional tools

SVG generation needs no external graphics dependency or Blender. Pillow is
optional for the local PNG helper. Blender is not required; no add-on is supplied
or installed. SVG/PNG use decoded source positions, not screenshot fitting, and
do not establish live LOD, draw order, instance poses or pixel parity.

Existing ELF query tools may need a separate Ghidra/bridge setup for their own
commands. GEOM1 did not execute new ELF queries or require Ghidra. Its geometry
and tests reuse prior executable-derived layout evidence.

## Integrity

MANIFEST.json records each payload size/SHA-256 and the actual source commit.
The outer ZIP receipt is local ZIP_SHA256.json alongside the archive. The
manifest has no recursive self-hash; the outer receipt covers it. Archive creation
verifies ZIP CRC and every payload hash. The recorded isolated test run used the
same supplied source/fixture selection, with external roots unset. Documentation
updates after that run do not change tested algorithm or fixture bytes.
