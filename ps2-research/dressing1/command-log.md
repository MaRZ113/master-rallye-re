# Executed commands and recipes

Active repo D:/Game/Master Rallye/master-rallye-re-general, branch master.
Git commands use its exact per-command safe.directory; no global setting changed.
Preflight/status/HEAD and the read-only SDK were independently recorded.

Actually executed public reconstruction (two byte-identical final runs):

```powershell
python ps2-research/tools/dressing_runtime.py --ps2-root "D:/Game/Master Rallye PS2" --pc-root "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked" --sdk "D:/Game/Master Rallye/master-rallye-re-course" --output ps2-research/data/dressing1/inventory-final.json --compact-output ps2-research/data/dressing1/inventory-final-compact.json
python ps2-research/tools/dressing_runtime.py --ps2-root "D:/Game/Master Rallye PS2" --pc-root "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked" --sdk "D:/Game/Master Rallye/master-rallye-re-course" --output ps2-research/data/dressing1/inventory-final-repeat.json
```

The public SVG command in diagnostic-visualization.md was executed for both
mandatory maps. The Turkey SVG was rasterized locally and visually inspected;
maps/PNG remain ignored. Compact reports were reviewed before copying selected
source counts/bounds/provenance into dressing1. The independent boat check uses
all six corner permutations against125 PC draw records and records113 unique
correspondences in boat-congruency.json; full pair IDs remain ignored.

Fresh ELF queries used the existing data/refl1/query.ps1 profile wrapper, always
passing --track dressing1, the latest observed12.1.4 D: install and installed
ghidra-ai-bridge exporter. Windows queried were391d38..392acc,3a5ee0..3a60a0,
3b9398..3b9600,3b9258..3b9398,3c1038..3c2100,3c1148..3c1eb0,
200550..200900,390960..390f40,3c7458..3c7750,26bc78..26be00 and1df2b0..1df500.
The attempted --ee-scalar selection query rejected HI/LO consumers, correctly
failing closed. --ee-sqrt-only then normalized only SQRT operands and preserved
MULT/HI/LO. Query transactions were rolled back; incomplete EE predicates remain
UNKNOWN. Original JAL/vtable/return/branch words were checked independently.

Full suite commands, with all four external variables in HANDOFF configured:

```powershell
python -X utf8 -m unittest discover -s ps2-research/tests -v
python -X utf8 -m pytest ps2-research/tests -q -p no:cacheprovider
python -m compileall -q ps2-research/tools ps2-research/tests
git diff --check
```

Workstation pytest uses PYTHONPATH=ignored data/cdelta1/python. A failed first
unittest pointed PS2_UI_CORPUS at incomplete data/validation; two missing GXI
subtests failed. The corrected final runs use complete ui1/extracted, with240
unittest successes and240 pytest successes. Runtime/Blender recipes were not run.

Isolation uses package_dressing_handoff.py --check-dir and unsets external roots,
then repeats unittest/pytest from that isolated directory. ZIP creation occurs
after the scoped commit, via --archive; CRC, size and each payload SHA are checked.
Exact isolated counts and archive receipt provenance are in validation.md.

Closeout includes fresh four-file PS2 hashes, relevant PC file hashes, preserved
GEOM1 report hashes, SDK status/HEAD, PC renderer/proxy diffs, explicit scoped
staging and staged diff review. Commit message:
`research: reverse PS2 course dressing ownership and LOD`. No push.
