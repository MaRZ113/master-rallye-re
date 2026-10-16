# PORT3 fix5 runtime check

Replace only `d3d8.dll` (fix4 assets and INI unchanged, diagnostics on).
Single-car race without opponents.

1. IceCream healthy: the car is the PS2 model. F10 with the brake released, then
   with the brake applied. Expected: `ps2_fleet_car_replacement` for IceCream,
   and ON_CORE/ADDITIVE_GLOW `healthy_exact_source` with the brake applied.
2. IceCream after collisions: F10. Expected `fleet_car_private_submission` with
   private_damage_tree=true and deformation_transfer=SURFACE_BARYCENTRIC.
3. Optional regression: one damaged NewRav or Bruno F10.
