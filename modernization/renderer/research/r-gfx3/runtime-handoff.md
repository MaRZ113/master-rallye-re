> Closed by the user's final short retest on DLL44a76a3a…; see ../r-gfx4/r-gfx3-final-baseline.json. The following records the preceding preparation and remains historical.

# Short retest for the final R-GFX3 fixes

Status READY_FOR_SHORT_RETEST. Do not repeat the full A–F protocol. Previous observations belong to DLL307a5fe4c83d95bd14d460cf767aa751e94b7f0a8e962c8c29c67681f2c17313; final candidate SHA25644a76a3a3e96573393b7ee1e492734b62d9c2ef8baae369711ce7c419615efef, size1016320, PE32/I386. Candidate: modernization/renderer/.build-msvc/Release/d3d8.dll. No deployment was performed by this task. Preserve existing game EXE/assets and use the already established human test installation; verify the session header matches this candidate hash before accepting results.

Read MRRRenderer.ini beside DLL once at startup; ConfigVersion=1, tracing and frame summaries enabled. Restart between A and B.

1. **A — AF MIN-only:** AnisotropicFiltering=true, MaxAnisotropy=16, GameplayFOV=false, Shadows.Mode=Stock. Visit Quick Race menu and race; one F10 in race. PASS: eligible stage0 LINEAR MIN becomes ANISOTROPIC (caps clamped); MAG logical==effective for every observed setter/draw, MIP and stage1 unchanged; POINT MIN unchanged. Inspect textures, menu and alpha cards for regression. FAIL: any MAG override, stage1 change or visual regression. MAX may differ for eligible AF MIN.
2. **B — preview exclusion and five race cameras:** AF=false, GameplayFOV=true, VerticalFOVDegrees=80.0, shadowStock. Compare Quick Race 3D preview with Stock: it must remain unchanged. In race cycle default,cam1,cam2,cam3,cam4: all should use80 VFOV; HUD unchanged. One menu F10 and one race F10 suffice; no five separate captures unless a camera fails. PASS trace: preview original/effective matrices identical and no FOV feature bit; race original90 source-family receives80 effective VFOV, original aspect retained and all14 other coefficients bit-identical. FAIL: preview changes, race camera misses override, HUD/Z/aspect changes.

Optional lightweight1920x1027 check: preview remains source45 stock, race source90 becomes80. Existing pristine Reset and shadow validation remain recorded against the pre-fix hash; full rerun is not required. The native regression suite covers unchanged contracts, but does not constitute a new human visual PASS.

Record new DLL hash, config, menu/race observations and F10 filenames. CLOSED only after A and B human PASS. After that, next proposed phase is R-GFX4 — Vehicle Reflection / Lighting Inputs; it is not started here.
