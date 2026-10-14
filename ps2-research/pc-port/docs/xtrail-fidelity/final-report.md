# X-Trail race fidelity closeout

Phase: PS2-VEHICLE-MODEL-PORT1 X-Trail focused follow-up
Branch: master
Starting HEAD:10af03a2acafc7e0a9c6c098a2bb8b09cb86c8b3
Status: IMPLEMENTED_PENDING_USER_RUNTIME for decal; PARTIAL overall fidelity
Frozen renderer tree:e33386bcf682db6983380c499e4928726c758fe0, unchanged
Baseline:24/24CTest PASS; PS2-enabled:32/32CTest PASS
Port Python:126/126PASS; source research10/10PASS
Exports, exact patches, twice-run generators, compileall and diff-check:PASS
Baseline DLL:011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138
PS2 DLL:48ef98febc0f1a53e4bed09096a1e486a32b0814fe42d683a858c31ae6d17e4c
New game runtime:NOT_PERFORMED
Deployment/push:none

## Race

Prior logs prove the working195shiny/14flat body partition with successful native
submission/restoration. Screenshots correlate with changed side paint, but skies,
camera and lighting differ; no pixel-level parity claim. The number is a separate
14face source record13, not those14flat faces. Its original PC upload lacks normals
and an environment stage. New opt-in XtrailFidelityMode1 reconstructs validated
source normals on the exact current decal geometry/UV/diffuse and submits it once
with the accepted Mode4 source. Default0 preserves the accepted implementation.
All native changed states and possible UP stream/index side effects are retained
and restored, with failed-apply rollback and no full-draw replay after submission.
Stock coordinate policy, current race/resource generations and driver gates fail closed.

All eight existing Xtrail whole-draw reflection registry entries are entirely
carshiny under the new source audit. Existing mixed CAR1 flat subgroup stays Stock.
No new wheel, headlight, window, driver or other-car override was added.
Detailed source draw/subrange/hash/material mapping is in race-material-map.md.

## Wheel and headlight decision

Race wheel geometry matches252/252PS2faces; a mesh transplant is not needed for
that shape. Correct rim appearance needs authentic image plus UV mapping and a
proved current rotating wheel owner. Rubber remains excluded. No wheel change.
Front headlight cover matches18/18PS2carglass mode20, with different primary image
and UVs. It needs blended primary plus static0.75highlight, not the Mode4 mixed
framebuffer source. Later lamp layers remain separate. No speculative shiny/glass
state substitute was implemented. These are precise next fidelity dependencies.

## Frontend readiness

PS2COMPLETE4636faces/24meshes vs PC2487faces/24records; all24PCsource hashes unique
within78vehicleDX. Strict local-frame matches0/2487; diagnostic bounds-derived Z
translation still0strict and1098relaxed. That is not a proved runtime transform.
Current Xtrail CarModel/en3d name/cache-to-mirroredVBIB join is absent. LatestF10s
are Turkey2race, older frontend captures are Forester. Replacement remains NO-GO;
source preparation and bounded separate pilot plan are ready in frontend/findings.md.

## Validation limits and next

First native test run intentionally injected a failure that landed in restore,
while its assertion expected success. The injection range was corrected and an
explicit restoration-failure/retry case retained. First new Python check used a
wrong expected category label; fixed to original frozen evidence, not changed
source evidence. Final full serial builds/suites pass. Original assets/SDK and
renderer are unchanged; no new build roots, physics, HUD or course work.

Next: one same-bookmark XtrailFidelityMode0/1 A/B, confirm ps2_xtrail_decal current
source upload and restoration before beginning authenticated rim/glass conversion.
