# V-SDK2 — stock COW and per-CarID camera experiments

2026-10-25, `research/vehicles`. [Native mapping, schema and CLI](stock-camera.md).
This phase does not claim live gameplay qualification. Its three independent
controls retain the previous V-PAJERO2 c-final-ride baseline; the separate
[Pajero cleanup](../vpajero3/README.md) is not mixed into camera experiments.

## Run independent controls

Under `.research-output/vehicles/vsdk2/`, run `Launch-SDK-Roster.cmd` in:

| Candidate | Explicit change |
| --- | --- |
| `candidate-camera-r2` | Lancer CarID28 only: follow extent half-length2.25 m, height1.50 m |
| `candidate-camera-megane-r2` | Original Megane CarID18 only: half-length2.00 m, height1.30 m |
| `candidate-stock-material` | Original Megane whitepaint DXT red channel x0.9; no camera adapter |

Values are authored calibration examples, not recovered original ideal camera
positions. The follow initializer adds these extents to its existing settings.
There are no per-CarID FOV, smoothing, focus/target-offset or replay-camera
parameters in this implementation. Shared camera XML, model bounds and physics
remain unchanged. This preserves antenna/donor collision geometry while removing
their extent contribution to the selected follow camera's framing.

The camera helper patches three exact getter callsites, validates the model
key before native broker access, resolves canonical scene `CarN` to physical ID,
then requires all44 original model-bounds bytes before returning private immutable
camera bounds. It caches no owner pointer. CarID0 is rejected because a missing
broker key may return zero. Stock authoring registration is currently qualified
only for Pajero/1 and Megane/18; unsupported pairs fail closed.

The native broker getter uses mutable scratch strings; it is not a pure read.
Synchronous native target setup and ABI were verified; actual scene/broker
execution, replay, split-screen and teardown remain gameplay qualification gates.

## Stock editing and reverting

Use `python tools/vehicle_sdk.py stock-project --help` to create/build/restore.
Projects copy a user-supplied family into private resources and pin originals.
Zero-edit Megane and Pajero projects emit no overrides. Only changed, parsed
DX/DXT resources are admitted; foreign paths, family/ID mismatches, source drift,
links, added/deleted resources, invalid formats and conflicts are rejected.

Roster JSON accepts explicit `stock_resource_projects` and `camera_profiles`
path lists. A stock camera needs its validated stock project to supply pinned
source bounds. Build a new sealed candidate through `roster-build`. Omitting
the stock project/profile or launching the previous candidate restores original
passthrough. No original retail installation is modified.

Stock and addon geometry/material authoring can reuse the existing DX/DXT tools.
Stock physics/audio profile editing is not newly qualified here; addon independent
physics/audio continues unchanged. Registration/class/unlock/AI/save identity
editing remains outside scope. Extending all stock families requires additional
verified registry pairs, not guessed names.

## Validation

- 778 synthetic tests:777 passed,1 skipped, `vsdk2/tests-delivery.txt`.
- Both camera R2 packages deterministically reproduce and preserve366/366 game
  resources against their baseline. Launcher integrity/environment/W^X allocation
  preflights pass. Existing bulk-read and shared native capacity hooks remain.
- 18 original-initializer x86 cases per camera use the actual delivered full
  payload: selected ID, shared model under another ID, stock passthrough,
  malformed/unknown target, absent broker, disabled extents and model mismatch.
  Stack, EDI, source bounds, native getter counts and x87 stack are checked.
  Name/broker/bounds services are typed stubs; this does not prove their live
  lifetime or game camera trajectories.
- Root delivered-capacity replay and original EXE/DLL SHA256 checks pass in
  `delivery-regression.json`. Additional independent review evidence is in
  `camera-guard-review-native.json`.
- Stock material control adds exactly one sealed resource,
  `DataGx/Vehicles/Megane/whitepaint-tga.dxt`; existing native payload is identical
  to baseline. No-edit controls emit zero resources; restore is tested.

Private evidence paths above are relative to `.research-output/vehicles/`.
No extracted game models, images, textures or original binaries are bundled in
the changed-source archive. No commit/push/publication was performed.

## Gameplay checklist

Compare each camera control to unmodified c-final-ride with identical options.
Inspect the selected car, then switch to unrelated stock/Subaru/Pajero/Lancer
IDs. Test follow modes, rear view, jumps, damage, split-screen, replay and
race teardown/re-entry. Confirm only the selected ID's follow framing changes.
FOV/smoothing changes should not be expected. Test material control separately,
then omit its project to verify reversible native appearance.

New experimental runtime candidates are ready for these owner tests; offline
acceptance is not gameplay confirmation.
