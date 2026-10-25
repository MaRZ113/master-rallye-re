# V-PAJERO3 — focused headlamp backing and native rear brake lights

2026-10-25, `research/vehicles`. Private runtime candidate:
`.research-output/vehicles/vpajero3/candidate-final/Launch-SDK-Roster.cmd`.
This continues c-final-ride, not the optional physical-dimensions candidate.
No new fitment, physics, reflection assignment or frontend loader changes.

## Changes

- Approved `rear_cap` profile removes16 generated housing sidewall triangles
  from each body model. Both black rear backings remain; source glass, lenses,
  wheelwell keepout, UVs and existing texture bytes remain. Both oblique front
  Previewer captures show no previous rectangular protrusion.
- Source callback0 selects off shape24 and on shapes27/26. Shape27 is an
  alpha-tested core, not a blended lens. It retains original texture/UVs;
  only blended lens26 creates the confined lit/halo surfaces. Unsupported GT4
  external effects25/28 are explicitly not used as recovered effect textures.
- Native `blight` uses existing MR brake state (case1 up to0.1, case2 above0.1).
  No constant emission, new timer, wheel glow or custom runtime brake hook.
  Generated halo follows the lens with about1 mm maximum offset. Its optional
 32-pixel resolution is an explicit MR effect approximation; source textures
  and existing livery are unchanged. Default Lancer behavior is preserved.

See [housing evidence](headlamp-backing.md) and [light qualification](brake-lights.md).

## Reproducibility and evidence

Private source profile `vpajero3/source-profile-r2.json`, full-source build
`build-final-r2`, quality-preserving output `balanced-final-r2/assets`, project
`author-final/project`, build `author-build-final`, roster `roster-final.json`.
Use existing `build_gt4_vehicle.py`, explicit Balanced normalization and
`vehicle_sdk.py build-project`/`roster-build` commands with your local GT4 inputs.
Extracted GT4 resources remain private and are not in the source archive.

`final-roster-regression.json` passes source reproduction and sealed resource
checks; launcher verifies resources, launch environment and native allocation.
`final-preservation.json` confirms283 non-Pajero files, physics XML and wheel
bytes unchanged against V-PAJERO2 c-final-ride. Original EXE/DLL hashes match.
Native controller replay executes original x86 threshold/setter for five inputs;
resource getters are controlled mocks, not gameplay evidence.

Pajero texture charge13,086,724 bytes. The four-addon race sequence with a
**synthetic8 MiB** world/UI reserve charges33,542,404 bytes with no steady LRU
eviction, only12,028 bytes below32 MiB. This is tight and is not a measured
track-residency or FPS guarantee. Native cache size and lossless bulk reader are
unchanged. Initial rejected build had redundant brake atlases; use candidate-final.

Final bundled Previewer captures `final-brake-off.bmp`/`final-brake-on.bmp`
were inspected: red lens illumination switches, amber sections and adjacent body
remain unlit. `cap-left.bmp`/`cap-right.bmp` show both front sides. These are
offline diagnostics, not confirmation of actual game draw ordering or appearance.

## Owner gameplay check

1. Inspect intact front-left and front-right views for the former black plate.
2. Brake/release while viewing both lower rear lamps; check no permanent glow
   or spill into body/amber areas. Front lights are not brake lights.
3. Recheck reflection ON/OFF, collision damage, current50/50 mm setup and wheels.
4. Select/re-enter menu; stock/Subaru/Lancer and mixed AI race/Results/re-entry.

Gameplay confirmation remains pending. No original retail file was modified;
previous candidates remain available to revert by launching their own package.
