# V-SDK4C — native glass ownership, qualified texture slots and offline Help

25 October 2026. Branch `research/vehicles`. V-SDK4B has not been started.
Material/Help work is independently committed as `c3c0b12`; see VSDK4A2_RESULTS.

## Native evidence and cause

Retail PC/x86 SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra 12.1.4 immutable source analysis, exact instruction reads and independent
GNU objdump disassembly were used. Evidence remains private in ignored
`vehicles_scratch/vsdk4c/rea/`, including the REA snapshot and source hashes.

Confirmed instructions:

- Literal `screenfront` at `006E7178`, PUSH references `004C40ED` and `004CFEC3`.
  The initialization sequence at `004C4030` binds rear/front/left/right group IDs
  to controller fields `+30/+34/+38/+3C` and records their declared maxima at
  `+48/+4C/+50/+54`. These are build-specific controller fields, not physics.
- Getter `004D3C30` reads a bounded group index from the current-value vector at
  `this+4`; setter `004D3C50` accepts nonnegative values up to the per-group
  maximum vector at `this+14`, bounded by the group count at `this+20`.
- Front-window transition `004C4878..004C48AB` increments only its selected group.
  Isolated replay of **original x86 instructions**, including getter/setter,
  changes `[rear,front,left,right]=[1,1,1,1]` to `[1,2,1,1]`; repeated attempts
  remain there because the source group maximum is 2. Other groups stay intact.
- The radial vertex deformer `005893F0`, called through `005892E0`, separately
  changes positions, RGB and alpha. Pane switching and vertex alpha are distinct.
- REA did not identify complete function boundaries for the two large routines
  containing the string references. Their ranges above are therefore reported
  as instruction sequences, corroborated by exact bytes and objdump, not invented
  decompiler functions. `0058BF40` was examined and is a generic vector enqueue,
  not the glass controller.

Navara has four logical zones with paired intact/broken geometry; front/right
groups place case 1 first, rear/left place case 2 first. Megane has front and two
side groups. The damaged alternative references the real stock
`windscreenc32-tga` texture. These assets prove a two-case intact/broken treatment.
A third independently authored cracked-then-shattered stage is **not qualified**.
Side groups may own multiple physical panes, as in stock Navara: per-door pane
independence must not be claimed from the four-zone mechanism.

The Subaru baseline `car.dx` SHA256 is
`acfd863771e5a5dd76cf11f20acc3931927ad807cf8913e1a204facb83fe72c5`.
Its `screenfront` draw 35 owns **156 triangles**: 44 window triangles and 112
front lamp/lens triangles. All other pane alternatives, including its broken
front draw 36, are hidden one-triangle fillers. The original converter explicitly
assigned glass to donor draw 35; this limitation was already recorded in V-MESH4.
Selecting native front case 2 therefore removes unrelated windows and lamp glass.
The diagnostic reproduces that source-state disappearance; it is not a replay of
the owner's exact collision or a new live-game observation.

Lancer comparison: current race model has no `screen*` native groups. Its GT4
glass/decals use independent alpha-bearing draws and the earlier damage-alpha
adapter. It is not silently upgraded to native pane damage in this phase.
Frontend models have ordinary draws rather than the race pane-switch hierarchy.

## Isolated Subaru correction

`glass_authoring.redistribute_glass` uses an explicit hash-pinned editable profile,
existing native groups and the shared topology writer. It requires exact triangle
accounting and refuses to replace non-filler target geometry. No material-name
heuristic assigns panes. The Subaru profile is in
`research/vehicles/vsdk4c/subaru-glass-profile.json`.

- Right zone: source triangles 0..3; left: 37..40; rear: 18 explicit triangles;
  front: 18 explicit triangles. Sign convention matches stock source geometry.
- The 112 lamp triangles move to existing ordinary filler draw 21, with the exact
  glass material tail copied from draw 35. They no longer depend on windscreen
  damage. All intact triangle attributes/materials are unchanged.
- Native broken alternatives receive the corresponding pane geometry. Their
  existing stock broken-glass texture remains byte-identical. Its per-pane planar
  UV projection is an **explicit MR adaptation**, not recovered GT3 damage art.
- Native tags, group controls, brake groups, other geometry and collision suffix
  remain preserved. `complete.dx`, wheel resources and every texture are unchanged.
- Render cost changes from 4,777 to 4,813 vertices and 3,301 to 3,337 triangles;
  physical draw count stays 37. No shader, executable or graphics-DLL patch.

Optional roster `base_glass_profiles` maps a verified base addon ID to its profile
path. It runs **after** the existing frozen-base pin checks; it cannot target stock
or unknown addon IDs. Default configurations produce no repair. This does not
weaken baseline verification, expand IDs or alter registration/capacity.

Preview profiles now accept `glass_states`, for example
`{"screenfront":2,"screenleft":1}`. Only present named source groups and cases
1/2 are accepted. These are explicit source-case inspections, **not impact
simulation**. Global generic-case preview remains an approximation.

## Validation and Windows evidence

Private results: `.research-output/vehicles/vsdk4c/`.

- `native-switch-replay.json`: original native switch CPU replay passes, including
  independent counters and rejection of state 3 for two-case source data.
- `glass-acceptance/validation.json`: original native deformation gives identical
  results at every preserved source position before/after; no coincident-position
  splits. Collision suffix is byte-identical. Intact triangle-attribute multisets
  and material flags/bindings match exactly.
- 64 actual native Previewer D3D9 captures: stock Navara, Subaru before/after and
  Lancer, individual supported pane cases, front/three-quarter views, reflections
  on/off. Undamaged appearance remains coherent; the repaired front broken case
  leaves side/rear zones and lamp glass present. Crack appearance is the MR stock
  texture adaptation. No actual collision threshold or native GPU parity claimed.
- `candidate-resource-regression.json`: 368 resources compared with the current
  three-car baseline; **only `DataGx/Vehicles/ImprezaProto/car.dx` changed**.
  `native-extension.bin`, `native-patch-ops.rvp`, `addon-plan.json` identical.
  Runtime state files are excluded by the established state-file policy.
- Original EXE and graphics DLL hashes unchanged; DLL SHA256 remains
  `eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.
- Candidate manifest, resource index, native allocation and launch-environment
  preflights pass. Full suite results are recorded in `tests-release.txt`.
- Actual Windows slot picker/addon/stock/restore validation and offline Help are
  described in VSDK4A2_RESULTS. The Studio native build succeeds and continues
  using the versioned executable if the owner has the canonical viewer open.

## Reproduction with private local inputs

1. Run `tools/inspect_vehicle_glass.py car.dx --output audit.json` for the source.
2. Author a source-hash-pinned pane profile. Account for every source triangle;
   classify static glass separately; preserve stock zone/case ordering.
3. Add that profile to a copy of a qualified roster config under
   `base_glass_profiles`, keyed by the existing base addon ID.
4. Run `tools/build_sdk_roster.py --config CONFIG --output NEW_CANDIDATE`.
5. Run `tools/validate_native_glass.py --help`; supply baseline/repaired families,
   stock and another import, exact retail EXE and the local Previewer. Inputs
   remain user-provided; no retail/GT assets are part of SDK source archives.

## Owner gameplay checklist / remaining boundaries

Launch `.research-output/vehicles/vsdk4c/candidate-glass/Launch-SDK-Roster.cmd`.
Use a fresh isolated candidate state. Check Subaru before damage, then front,
rear and each side impact separately. Confirm only the appropriate native zone
changes, other zones and headlights remain visible, and native deformation and
brake illumination remain normal. Compare reflections on/off and race re-entry.
Side front/rear panes can share the stock side-zone controller by design.

The native trigger thresholds and actual collision-to-zone classification were
not replayed end to end. Actual damage rendering, glass draw sorting, gameplay
state persistence and repeated race transitions still require the owner's test.
The candidate is ready for that test; it is not labelled gameplay-qualified.
