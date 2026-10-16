# Fleet PORT3 runtime qualification

Close the game; manually copy d3d8.dll and merge PS2Vehicles from runtime-kit.zip into the game directory. Copy PS2KiaBrakeOn.gxi beside PS2Port.ini. Keep existing COMPLETE/grass/water/reflection/HUD settings and PS2BrakeGlow.gxi. The kit includes all25 pinned CAR candidates,22 newly used wheel assets and accepted Xtrail/Kia dependencies; UFO receives no wheel asset/path. Do not replace original assets.

```ini
[PS2Port]
RacePS2FleetMode=1
RacePS2ModelMode=1
RacePS2WheelMode=1
RacePS2ModelAssetDirectory=PS2Vehicles
ReflectionMode=4
BrakeGlowMode=1
BrakeGlowDiagnostics=1
KiaBrakeOnAsset=PS2KiaBrakeOn.gxi
RacePS2FleetCapture=1
RacePS2FleetDamageCapture=0
```

One DLL covers all25; no per-family experimental builds. Xtrail/Kia are controls. For each other car, fresh single-player practice race: F10 with brake held at start (CAR/crew, complete native-source suppression, wheel owners, ON/glow); drive/steer and release brake, F10 (wheel motion/OFF); collide then hold brake and F10 (damage policy). Restart and inspect recovery. UFO has no wheels. Use one MSAA4x window Reset control, plus at least one5-source wheel family. Note menu/race FPS regressions and duplicated/missing parts; retain screenshots from the same camera/bookmark.

First source family order: Astero, Bruno, ChevyBlazer, Frontera, IceCream, Jump, Kamaz, Kangoo, LandCruiser, Mattserati, megane, Navara, NewRav, Pajero, Patrol, RMonster, SeatBuggy, Simmbugghini, Tata, Terrano, Ufo, WildCat, Forester/WOOLDAND. The same release includes them all; no geometry-name aliases.

Expected healthy25 CAR admission is conditional on exact current native source/owner proof. Wheels are replaced atomically per complete current wheel-owner source cohort (4 or5 PC records), not an invented count of wheel instances. Logs enumerate every observed wheelowner; otherfamilies are not user-runtime-confirmed until captured. Private wheel trees stay Stock. UFO newdamage mapping is source-complete but game acceptance pending;22 other private damaged CAR families deliberately use whole-native-body Stock fallback. No partial native/PS2 chassis combination. Xtrail/Kia damage paths remain accepted controls.

Sidecars race-fleet-PID-dN-fFRAME.jsonl are F10-only. fleet_car_private_submission identifies family/owner/private_tree/fullsource count/asset SHA/generic damage eligibility and draw/restore HRESULT. fleet_wheel_submission enumerates current native owner, actualsource count, unchanged WORLD and draw/restore HRESULT. fleet_wheel_rejected gives exact source/queue/asset/material gate. fleet_lamp_continuity identifies OFF/ON_CORE/ADDITIVE_GLOW, current owner, material token/texture generation, damagedbranch/reason and apply/draw/restore HRESULT; Kia retains kia_brake_continuity. Require allHRESULT0. Unknown branches are Stock with rejection evidence. Diagnostic cap128 F10 activations per process,128records/128KiB per capture; no full-frame raw readback, per-frame scans or controller polling.

Use coverage.json for source/implementation/runtime/fallback distinction. Native source fixtures and synthetic deformation tests are not gameplay confirmation. Return F10s plus visible symptoms; no debugger needed for ordinary qualification.
