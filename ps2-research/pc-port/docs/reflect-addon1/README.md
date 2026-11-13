# REFLECT-ADDON1 — PS2 reflections on every car

Status: **BUILT (DLL d9774313), awaiting the owner's race review** (2026-11-13). Owner request: make the PS2 reflections available for all cars, current
and future add-ons included.

## Before

The PS2 reflection (`reflection_pilot.cpp` `reflection_identity_for_hash`) admitted a draw only when its geometry had an exact entry in
`kReflectionMaterials`. That table holds 212 hashes of the retail cars' PS2 "carshiny" groups: 25 families, Astero … megane. The reflection snapshot
(`ps2integration::snapshot`) also refused every draw whose triangle and vertex counts were not in that table. Add-on cars never matched, so they kept the PC
reflection.

## Change

* **A second admission authority**, the registered paint body. `atmospherebody::registered_paint_authority` (`atmosphere_body_general.hpp`, installed through
  `ps2integration::paint_authority_hook` in `reflection_paint_authority.hpp`) checks:
  * the draw is fleet-owned (`atmosphereintegration::vehicle_draw_probe`, then the owner walk);
  * its resource is `vehicles/<family>/car`;
  * the family has no entry in `kReflectionMaterials`, so retail cars keep exactly their PS2-verified groups;
  * its BodyMaterials role is paint (registry row or the naming contract for unregistered add-ons) and it is not crew.

  The answer is remembered per race and draw. Log: `ps2_reflection_addon_family` once per family.
* **Admission**: the snapshot carries the interned family (`ReflectionSnapshot::paint_family`).
  * It is admitted without a table layout, with a 1–8192 vertex/triangle bound.
  * `reflection_identity_for_hash` uses a per-draw material for that family.
  * The vehicle proof comes from the owner walk.
  * Every other rule is unchanged: supported build, current device/reset, complete buffer mirror, `0x152`/36, live race certificate, stock
    coordinate policy, native states known and matching, 2D textures with generations, opaque body render states, and the exact
    `MODULATE` / `MODULATEALPHA_ADDCOLOR` camera-space-normal env stages.
  * Reason `registered_paint_native_opaque_environment_material`.
* Because the authority uses the material, not the geometry, dented add-on panels keep the reflection.

Test (`tests/reflection_pilot_tests.cpp`): an add-on body is refused without the authority and accepted with it under the family name. It is still refused
without a live race, with non-opaque render states, and above 8192 vertices.
