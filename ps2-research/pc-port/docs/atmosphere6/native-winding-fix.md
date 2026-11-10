# Atmosphere 6.19: native winding regression

This candidate corrects the missing Kangoo/Mattserati rear glints in 6.18.
It retains the universal course material resolver, automatic lamp solver,
current geometry deformation and centre-depth occlusion.

## Confirmed failure

The owner gameplay session `session-20261110-022206-24404.jsonl` identifies the
6.18 DLL SHA256 `6c527b886b7fec98660760b586202fe967ea641ba520fb8f43ec2a2226419c14`.
Its attachment catalogue is ready with all 20 rows. At frame 5111 it reports
12,858 candidates, 12,858 signature misses, zero owner misses and zero applied
points. Both car rigs are recognised. The loss occurs before ownership resolve.

LPA1 anchors and expanded UV digests use the parser's source-DX corner order.
The native PC compiler swaps the first two corners of every triangle. Existing
fleet source fixtures and the runtime-backed damage source certificates already
record this conversion; see `../vehicle-damage-fix1/damage/findings.md` and
`../vehicle-fleet-port1/prepare_native_car_fixtures.py` (relative to the docs root).
The 6.18 collector expanded the native index stream without undoing that swap.
Consequently every intended UV signature differed. Managed points had no static
fallback, so their glints disappeared.

The original integration probe mistakenly submitted the parser's source order
as native indices, reproducing the author's assumption instead of the loader.
Its eight passing cases did not establish compatibility with the game's indices.

## Correction and regression evidence

`lamp_attachment_geometry` now converts native triangle corners into the LPA1
source order before expanding both positions and UVs. Converting only the digest
would leave barycentric weights and normals attached to the wrong corners.
The existing 6.18 `lamp_attachments.lpa` is unchanged and remains required.
No weak texture/count match, per-car exception or static point was introduced.

`tools/atmosphere_lamp_runtime_probe.py` independently reads each model's stored
raw local index stream, rather than `draw_global_indices`. The corrected fixture
fails the old renderer with exit code 6 (UV mismatch). After the fix, all ten
points resolve in every OFF/ON, rest, first-observation translation,
first-observation rotation and local triangle damage case. Maximum position
error is below 2.4e-7 game metres. Native contract tests cover both 24-byte and
36-byte vertex layouts, asymmetric barycentric weights, local vertex reindexing
and rejection of the former incorrectly ordered input.

This is a reproduced regression and offline correction. A new gameplay run must
confirm actual capture and ownership after the signature gate; no new gameplay
acceptance is claimed. Expect attachment `points_total` to increase for these
cars, rather than every candidate becoming a `signature_miss`.

## Installation in a copied test game

Use the package root `d3d8.dll`. Preserve the existing Atmosphere configuration,
course packages and lamp masks. The included `Atmosphere/vehicles` files are the
unchanged 6.18 sidecar and its exact matching rig; leave them in place if already
installed. No original EXE or archive is changed. The package includes the
observed installed DLL for rollback and the exact 6.18 DLL for comparison.

Repeat tail/brake/reverse, collision, camera, covered-lens, rival and reset tests
on both cars. Geometry without depth writes remains outside depth-mask occlusion.
