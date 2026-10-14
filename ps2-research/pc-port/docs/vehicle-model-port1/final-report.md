Phase: PS2-VEHICLE-MODEL-PORT1
Repository: D:/Game/Master Rallye/master-rallye-re-general
Branch: master
Starting HEAD: a6daf3b17d32043c948e3ed9a843b1a5b3258f16
Ending HEAD: local phase commit recorded in archive release-provenance.json and final reply
Preflight: frozen renderer clean; pre-existing port docs/config edits preserved
Canonical ELF: b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2
Canonical PS2 sources: four canonical hashes verified; original inputs unchanged
PC Retail corpus:78DX source uniqueness audit;26COMPLETE+6CAR rehashed at closeout
Course SDK: unchanged clean4244fa0c4d878523c9947f54816bf377cdfb2589
Frozen renderer: e33386bcf682db6983380c499e4928726c758fe0, unchanged
Immutable staging commit:0bddf7c7bc5e95831f98714ff6231da05ab073ea
COMPLETE decoder:29/29 supported, terminal102 original consumer proved
Private visual conversion:29/29, original vertices/materials/strips/GXI; all textures resolved
WOOLDAND/PC Forester: paired source family, PS2 FORESTER remains distinct
Live frontend owner: layout/rotation observed; Egg/en3d/cache-to-buffer join unresolved
Frontend replacement: BLOCKED; no geometry suppression enabled
Race material implementation: nine exact source records, six families,1327shiny faces
Other faces in those records:199Stock,1526total; no blanket carshiny override
Native CAR geometry: original buffers/attributes/winding/index order retained
Native submission: contiguous original-IB subdraws; no replay/extra geometry pass
ReflectionMode4: preserved, preflight source and existing native state transaction
Stock default: RaceModelMode0, FrontendGeometryDiagnostics0
Lights: original blight threshold/selector modes1/14 research; implementation deferred
Reset/MSAA: existing lifecycle/capture preserved; automated contracts pass
Baseline build: Win32 Release PASS,24/24CTest
PS2-enabled build: Win32 Release PASS,31/31CTest
Python:123/123port tests plus35new research tests PASS
Pytest: default interpreter unavailable, No module named pytest; no install
Compileall: PASS
Diff-check: PASS
Exports: both proxy variants PASS
Baseline DLL:011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138
PS2-enabled DLL:1f7c99dae931955f2c6441f5959aee7a11fa405eb1f8f935c81dcedd6aed2c79
Runtime new implementation: PENDING_USER; no visual parity claim
Original game assets changed: none
Native physics/HUD implementation: none
Commit: bounded phase sources/evidence only; actual identity in packaged provenance
Push: none
Overall status: PARTIAL — race pilot implemented; COMPLETE owner admission blocked

## Main result

The remaining body material problem is no longer addressed by a whole-draw override.
The new opt-in partitions exact live upload geometry into proved `carshiny` and Stock
subranges, without changing the original model. Each original face is submitted once
in original order. Current native states/resources and race admission are mandatory.
Only approved source material subsets use the accepted Mode4 texture/compositing path.
The concrete changes, failure semantics and performance bounds are in
`design-and-implementation.md`; source-backed coverage is in `vehicle-coverage.json`.

| Vehicle | New shiny faces | Preserved Stock faces | Original source records |
|---|---:|---:|---|
|LandCruiser|588|129unmatched|8,9|
|Bruno|229|3unmatched|4|
|SeatBuggy|165|4unmatched|7|
|ChevyBlazer|60|10glass|7|
|Xtrail|195|14flat|1|
|Forester/WOOLDAND|90|39untagged|8,9,2|

These are source-record/material counts, not native draw ordinals. Current exact
CPU-mirror hashes, not recorded counts/textures, admit the replacement submission.
No live events for this new DLL exist yet. Success with all1327faces remains a
runtime question. Unknown parts are intentionally not guessed or forced reflective.

## Frontend result and exact blocker

The current two menu captures contain all17Forester COMPLETE draw layouts sharing
one rotating world transform and unchanged view/projection. Their source hashes are
unique across the78DX corpus. Those captures do not contain geometry bytes/digests.
Original x86 instructions independently prove the mover's model selection and cached
resource invalidation. Desired selection is insufficient for actual loaded ownership.

The missing chain is current CarModel Egg/gaFrontendCarMoverAI → en3dname+0xc and
loaded cache+0x74 → current COMPLETE model → current mirrored VB/IB submissions.
The added read-only bounded upload observer can establish the current exact source
digests without using historical pointers/ranges as constants; it cannot create that
owner certificate. Frontend suppression is therefore disabled. This is a precise
NO-GO boundary, not an implemented replacement awaiting screenshots.

Replacing only a root by texture/name is also unsafe: PS2 WOOLDAND side root has484
faces versus PC400,357exact/.001 matches and364/.005 matches, with overlaps against
other PC groups. The grille has0exact matches. A full model replacement must preserve
whole-owner suppression, wheel/window/rotation/lifetime contracts first.

All29COMPLETE sources now have safe decoded trees and private source-format assets,
including exact GXI resources. Terminal102 is a post-tree two-float wheel-cylinder
auxiliary, rejected for non-wheel ownership; it is not a guessed visual node. Tag101
collision trailers stay opaque. No collider or physical object is created. Authored
hierarchy counts are not live visibility/polygon budgets.

## Lamps and acceptance boundary

The original PS2 brake-light AI resolves namedblight and writes selector2 above
float32(.1), otherwise1. Source branches use on/glow modes1/14; child ordering varies
between vehicles. Actual controller ownership, complete mode14GS contract and PC
braking/resource mapping remain unknown. No lamp/glow override was implemented.

Acceptance: Git/input/parser/source inventory/conversion/material separation/native
transactions/regressions/exports/handoff gates PASS; frontend live owner/suppression
BLOCKED; new live CAR/Reset/MSAA/menu performance and visual assessment PARTIAL pending
user testing. Existing physics/HUD remain paused. No scenery/water expansion began.

The single next recommendation is the targeted vehicle-admission A/B in `next.md`.
