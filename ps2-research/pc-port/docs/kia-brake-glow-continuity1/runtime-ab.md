# PS2-KIA-BRAKE-GLOW-CONTINUITY1

Close the game. Manually install this d3d8.dll and copy assets/PS2KiaBrakeOn.gxi beside PS2Port.ini (normally the game directory). Keep all previous PS2Vehicles, PS2BrakeGlow.gxi and settings. No automatic deployment.

```ini
[PS2Port]
BrakeGlowMode=1
BrakeGlowDiagnostics=1
KiaBrakeOnAsset=PS2KiaBrakeOn.gxi
RacePS2FleetCapture=1
RacePS2FleetMode=1
RacePS2ModelMode=1
RacePS2WheelMode=1
ReflectionMode=4
```

1. Fresh KiaSportage practice race, same camera/bookmark, MSAA4x. Hold brake and F10; save a rear screenshot. Healthy observation seeds exact ON and glow references.
2. Release brake: verify reflective OFF bases remain. Hit the rear, hold brake and F10 again; save the same rear view. Repeat another rear impact if practical.
3. Reset the window, brake and F10; then release brake and inspect OFF reflection. Restart race and test again. Exit normally to flush session logs.

Expected: smooth original PS2 RGB-fade glow remains after damage, redder/orange ON core instead of PC white/pink core, source-native damaged lamp geometry retained. Chassis, crew, wheels, reflections, FPS and OFF transition should stay unchanged. The halo itself retains original PS2 RGB, not a synthetic red filter. Compare the previous DLL screenshots and a PS2 rear-braking reference at a similar camera/exposure; do not claim pixel parity from different camera/lighting.

F10 sidecar: kia_brake_continuity for ON_CORE and ADDITIVE_GLOW. Require owner_verified=true, override_applied=true and apply/draw/restore_hresult=0; damaged capture additionally requires damaged_branch=true and damaged_branch_matched=true. Healthy reason=healthy_exact_source; damaged reason=damaged_owned_clone_uv_index_match (or healthy_exact_source if that particular lamp did not deform). All rejection reasons are explicit. Raw kia_glow_source_capture is F10-only, at most32 activations,64 records/128KiB per sidecar; no continuous raw buffer logging, GPU readback or controller polling added.

Safe fallback: cold damaged owner without an exact healthy lamp reference, different material/texture generation, changed UV/index topology or missing PS2KiaBrakeOn.gxi. This never weakens the body geometry certificate. A missing ON asset affects only the new ON-core color path; original glow remains available. Do not scale to other cars until this Kia A/B passes.
