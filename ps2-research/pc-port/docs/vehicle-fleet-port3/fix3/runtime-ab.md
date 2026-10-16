# PORT3 fix3 runtime check

Replace `d3d8.dll` and add `PS2Vehicles/port3-JUMP-OFF.ps2model` from the kit.
Keep every other fix1 PS2Vehicles file and the INI (diagnostics on).
Single-car race without opponents.

1. Jump healthy, brake released: F10. Expected `fleet_private_off_submission`
   with draw_hresult=0. The OFF region shows the original PS2 carshiny material.
2. Jump: apply and release the brake. ON_CORE and ADDITIVE_GLOW must be unchanged.
3. Optional regression check: one F10 of NewRav, Bruno or Mattserati with the brake released.
4. Optional coverage: one brake-released F10 per family not yet captured
   (ChevyBlazer, Frontera, IceCream, Kangoo, LandCruiser, Navara, Pajero,
   RMonster, SeatBuggy, Simmbugghini, Tata, Terrano). Note any OFF zone that
   looks wrong.
