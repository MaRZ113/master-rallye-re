# PORT3 wheel source contract

24 playable wheeled families have independently decoded original WHEEL.PSM resources and exact protected-PC wheel.dx source certificates. UFO intentionally has no wheels and no asset was synthesized. PS2 FORESTER is excluded; PC Forester maps to WOOLDAND only.

All 24 PS2 and PC wheel-local XYZ bounds match exactly. There is no scale fitting, pivot translation or chassis-fixed wheel transform. Native source-record counts are 4 for KiaSportage/Navara/Tata/Xtrail and 5 for the other 20 families; these are records PER MODEL, not wheel instance counts. Total 116 native source records. PS2 private mesh counts are independent of native source count (Xtrail has 3 PS2 meshes and 4 PC records).

The assets retain all source vertices, normals, colors, UVs, geometry indices and original GXI textures. Primary source V orientation remains the established runtime 1-V conversion. Tread U-wrap is source-selected; reflective wheel metal uses original carshiny effective render-target selection while rubber remains non-mixed. Patrol/WOOLDAND authored shader names are unregistered generic names: the existing verified original constructor source-presence/texture-flag rule yields mode 3, with rubber preserved and chrome mapped to the established render target. This does not grant reflection to every wheel surface.

`prepare_fleet_wheels.py` reuses the accepted converter with explicit family parameters and distinct private output names. It checks original PC/PS2 SHA-256 before conversion. `manifest.json` pins every generated asset, original source and texture. `fleet_wheel_registry.hpp` is a renderer-ready draft; main owns integration. Existing Kia/Xtrail assets and paths are unchanged.

## Native owner qualification

Source-ready does not mean runtime-confirmed. Current native owner must be distinct from chassis, point to its own complete certified model and supply the current finite WORLD; current resource generations/revisions and all source records must match before suppression. The independently moving native WORLD supplies spin, steering and suspension. A known source family name or global draw ordinal grants nothing. Whole wheel source cohort must be suppressed atomically, with fail-closed native fallback for stale/private/unknown wheel geometry.

The protected `DataGame/vehicles.xml` contains front/rear dimensions, tyre and suspension parameters, but no explicit wheel model placement/owner count. A bounded search for wheel.dx references in protected XML found none. Therefore this pass does not infer four wheel OWNERS from four records, four tyres visible in a screenshot, or front/rear parameter labels. Kamaz likewise has no source-proven ownercount here. Runtime discovery must collect distinct current owner instances, complete per-owner source cohorts and the current set of submitted native wheel owners. Xtrail/Kia retain their already runtime-qualified implementations.

Wheel damage is not granted by chassis damage compatibility. A private wheel source requires its own exact original-source/UV/material proof; otherwise keep that wheel cohort Stock. Race restart invalidates owner tokens; Reset releases/recreates private resources and requalifies live tokens. No native physics memory is modified.

## Validation

Five focused Python tests pass against all 24 private assets and all 116 source-record fixtures. Fixture streams preserve original XYZ/UV and native index winding; white diffuse is explicitly synthetic fixture scaffolding only. No CMake builds, renderer source changes, game deployment or live runtime claims were made by this workstream.
