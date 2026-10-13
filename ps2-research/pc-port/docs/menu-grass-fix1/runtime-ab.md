# Manual cold-start and Turkey3 check

Install dist/current/ps2-enabled/d3d8.dll manually in the test installation,
keeping the previous DLL for rollback. Keep existing private .ps2grass/.ps2obj
paths beside PS2Port.ini valid; no asset conversion or replacement is needed.

Start each case from a completely closed game, same graphics/Free Camera
settings and HUD preference. FoliageMode0, PixelProbe0, ReflectionMode0.

1. GrassMode0, CourseObjectsMode0: cold menu control.
2. GrassMode1, CourseObjectsMode0, GrassDiagnostics1: cold menus BEFORE any
   race, then Turkey3. Verify grass and log ps2_grass_build/ps2_grass_draw.
3. GrassMode0, CourseObjectsMode1, CourseObjectsDiagnostics1: same menu path,
   then Turkey3 puddle control.
4. Both layers1: same bookmark; then enter another course and exit to menus.
5. Toggle H on/off in a race to compare the staged HUD cache correction.

Do not first enter a race to hide the cold-menu symptom. Capture one F10 frame
in slow/normal menus and one in Turkey3 with grass. Send latest session files
and brief FPS/stutter observations. Diagnostics are bounded one-shot records,
not per-UI-draw logs. Defaults remain all0. No PS2 visual parity claim.
