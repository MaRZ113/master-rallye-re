# PORT3 fix4 runtime check

Replace `d3d8.dll`; add `PS2Vehicles/port3-JUMP-OFF.ps2model` if fix3 was not
installed. Keep all other fix1 PS2Vehicles files and the INI (diagnostics on).
Single-car race without opponents.

1. Pick one or two of NewRav, Bruno, Patrol and IceCream. Drive into walls until
   damage is visible, then F10. Expected in the race-fleet sidecar:
   `fleet_car_private_submission` with private_damage_tree=true,
   deformation_transfer=SURFACE_BARYCENTRIC, draw_hresult=0 and
   restore_hresult=0. There should be no `unsupported_private_tree`. Visually
   the car stays the PS2 model and the dents follow the PC damage.
2. Mattserati or Tata, damaged: still the Stock damaged body with Mode 4
   reflections. That is expected for these two.
3. Report anything that looks torn, floating (driver or details) or flickers on
   the damaged PS2 body, with the frame number.
4. Jump: brake-released F10 for the OFF check from fix3.
