# PORT3 fix8.1 runtime check

fix8 runtime (PID22340): UFO OFF confirmed by the user. All four content fixes logged
`content_fix_unavailable`: the corrected files were not in PS2Vehicles (the fix8 kit had them only
inside runtime-kit.zip). fix8.1 also places them in `assets/`.

1. Replace `d3d8.dll`. Copy every file from `assets/` (or `runtime-kit.zip` → `PS2Vehicles/`) into
   the game's `PS2Vehicles` folder, especially the four *-CREWFACE1 / *-WINDOW1 models.
2. Use the new commented `PS2Port.ini.migrated-pristine` as `PS2Port.ini`
   (FrontendModelAsset and CourseObjectsAsset are no longer needed; the puddle asset is now found in
   GrassAssetDirectory).
3. Session log must show `ps2_content_fix … "status":"loaded"` for NAVARA-CREWFACE1, TATA-WINDOW1,
   KAMAZ-CAR-WINDOW1, KAMAZ-COMPLETE-WINDOW1. Check Navara co-driver face and the right windows.
