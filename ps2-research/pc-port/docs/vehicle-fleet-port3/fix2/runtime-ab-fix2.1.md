# PORT3 fix2.1 runtime check

Replace only `d3d8.dll` with the fix2.1 DLL; keep the fix1 PS2Vehicles assets
and INI (diagnostics on). Single-car race without opponents.

1. NewRav healthy, brake released: F10. Expected `fleet_lamp_continuity` layer
   OFF with reason `original_ps2_off_mesh_current_owned_deformation`, plus
   `fleet_private_off_submission` with draw_hresult=0 and restore_hresult=0.
   Visually, the formerly flat OFF region shows the original PS2 carshiny material.
2. Same for Bruno and Mattserati (one brake-released F10 each).
3. Apply and release the brake: ON_CORE and ADDITIVE_GLOW must stay unchanged.
4. NewRav damaged, brake released: F10. Report the OFF event or the named rejection.

Report F10 frame numbers per car and state, plus anything that looks wrong on the lamps.
