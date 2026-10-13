# Single-build-root migration and cleanup proposal

13October2026 follow-up: the user approved the four conservative candidates.
All5792files were preserved and hash-verified, then only those four roots were
removed. Net reclaimed736033975bytes (~702MiB); complete local preservation
ZIP remains ignored in dist/cleanup. Details: cleanup-first-pass.json.
The originally proposed list below is retained as provenance. No other legacy
root was deleted. The committed HUD baseline adoption is separately documented
under hud-baseline-adoption/; current public builds use its clean locked tree.

Permanent locations: .build/baseline, .build/ps2-enabled, matching .staging
sources, dist/current releases. The initial canonical build is necessarily
fresh; later runs must retain caches and unchanged input timestamps. No legacy
root is used as a new build configuration.

Synthetic tests cover incremental staging, preserved timestamps/objects,
changed/removed owned sources, unowned/user-modified staged files, canonical
root enforcement and concurrent workflow locking. Exact Git/patch/generator
checks remain mandatory. Historical reports retain their original provenance.

During this task four unrelated HUD edits appeared in modernization/renderer.
The public builder correctly refused the dirty baseline. The user approved a
ONE-OFF build solely from previous immutable Git objects; the original four
working files are excluded and their before/after hashes are recorded. The
public gate remains strict, with no dirty-source bypass option. The user then
approved adopting those HUD changes as a separate staged-only third patch for
PS2-enabled builds; the baseline variant remains the old immutable source.
Future public builds require a clean locked renderer. A new baseline revision
needs an independently reviewed tree lock/patch revalidation.

The user subsequently committed those exact four HUD changes as
`0bddf7c7bc5e95831f98714ff6231da05ab073ea`. The current lock adopts its renderer
tree `e33386bcf682db6983380c499e4928726c758fe0` after independently reproducing
all four Git blobs with the previously approved HUD patch. The seven-file
PS2 integration patch was rebased exactly; generator patch stayed byte-identical.
Both variants now inherit the approved HUD fix. The old third HUD patch is
retired, preserved with the previous lock/patch and audit in
`hud-baseline-adoption/`. No original renderer file was edited by migration;
strict clean-source/tree/patch/generated-output gates remain mandatory.

## Inventory and conservative cleanup list

legacy-inventory.json records 19 legacy directories, approximately 4.15 GiB,
sizes, final DLL hashes, source snapshots, saved reports and process command
matches. No process command line referred to these legacy roots at inventory
time. This is NOT proof of no open handles or future use. No deletion performed.

After explicit approval and a fresh activity check, initial candidates are:

- .build-overlay-course-objects-check: 20.09 MiB.
- .build-overlay-course-objects-final: 376.76 MiB.
- .build-overlay-pilot14: 10.07 MiB.
- .build-overlay-reflection1-final: 466.81 MiB.

Approximately 873.73 MiB on this first conservative list. Inspected source,
final DLL and report hashes are covered by current source or existing handoff
members. Other roots include distinct/unarchived reports, DLLs or PS2 source
snapshots and remain PRESERVE pending review/archival. OBJ/PDB/compiler cache
contents are size-inventoried, not exhaustively checked by a preservation
oracle. Before approved cleanup: verify resolved paths inside pc-port, recheck
active builds, preserve required unique evidence. This report removes nothing.
