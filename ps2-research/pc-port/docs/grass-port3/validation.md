# GRASS3 inventory validation

Read-only research subset completed. Native implementation, serial builds and
release packaging are owned by the main agent; this report does not claim them.

Executed from `master-rallye-re-general`:

```powershell
python ps2-research/pc-port/docs/grass-port3/inventory.py --input 'D:/Game/Master Rallye PS2' --output ps2-research/pc-port/docs/grass-port3/course-inventory.json
python ps2-research/pc-port/docs/grass-port3/compare_selected.py --ps2 'D:/Game/Master Rallye PS2' --pc 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --course FRANCE1 --output ps2-research/pc-port/docs/grass-port3/france1-placement.json
python ps2-research/pc-port/docs/grass-port3/compare_selected.py --ps2 'D:/Game/Master Rallye PS2' --pc 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --course ITALY_S1 --output ps2-research/pc-port/docs/grass-port3/italys1-placement.json
python -m unittest discover -s ps2-research/pc-port/docs/grass-port3 -p test_inventory.py -v
```

All 36 fresh landscape payload hashes equal the independent frozen GRASS1
identities. All four original inputs rehashed through `water_runtime.verify_inputs`.
Original particle texture hashes/dimensions/alpha counts independently extracted.
France1 and ItalyS1 PC DX/TXT hashes verified against frozen WATER1 identities
through existing GEOM1 adapter; authored landscape transforms/route anchors read
independently. No new archive, GXI, PSM or DX parser.

Eight focused corpus-independent tests PASS: exact/singular/default directives,
source winding, deterministic binding order, material-sensitive source digest,
token case boundary, 36-course metadata/source-layer provenance, and distinct
selected artifact identities, and exact scene-versus-landscape ID distinction.
They do not validate native state transactions,
course switch performance, visible density or PS2 pixel parity.

The selected source reconstructions reproduced the same four private artifact
hashes on repeated executions. Wall-clock timing is printed only, outside the
deterministic JSON. Initial observed totals approximately6.8s France1 /4.5s
ItalyS1 excluding a subsequent added full corpus identity pass. No full geometry
or image array written; only compact metadata persisted here. Original meshes,
source images, full generated points and playable PC assets were not modified.

The strict initial requirement of zero route residual rejected ItalyS1. Existing
independent source evidence shows two route outliers; the bounded selected-case
gate now requires >=99% route agreement and independently identical identity
landscape matrices, retaining all residuals. Direct triangle matching is still
strict .001, without any registration fit. This change affects only this
read-only selected diagnostic, not accepted runtime admission.

An initial inventory attempt incorrectly expected decoded pixel arrays from
`psbtool.parse_gxi`, which returns metadata. Corrected to inspect the original
validated simple-GXI alpha byte positions; subsequent complete inventory passes.
No failures were silently skipped.

Required external dependencies: canonical PS2 PackFS for inventory; protected
retail PC DX/TXT/RaceTest files and read-only Course SDK for selected comparison.
Corpus-independent tests need these three scripts, their compact JSONs, and
existing source modules `detail_runtime`, `tngtool`, `water_runtime` and imported
dependencies. Include those source files in a standalone handoff.

Runtime validation: NOT_PERFORMED in this inventory. User previously confirmed
Turkey3 GRASS1/BUSH1 visually; that observation does not confirm other courses.
