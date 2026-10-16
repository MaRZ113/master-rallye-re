# PORT3 fix6 runtime check

Replace `d3d8.dll` and add `PS2Vehicles/port3-UFO-OFF.ps2model` (keep everything
else from fix5). Single-car race without opponents, diagnostics on.

1. UFO healthy, brake released: F10. Expected `fleet_private_off_submission` for
   Ufo with draw_hresult=0. Apply and release the brake: ON/glow unchanged.
2. Mattserati and Tata after collisions: F10. Expected
   `fleet_car_private_submission` with private_damage_tree=true and
   deformation_transfer=SURFACE_BARYCENTRIC. The car stays the PS2 model.
3. Report anything torn or floating on Mattserati's root.2 pieces or around Tata.
