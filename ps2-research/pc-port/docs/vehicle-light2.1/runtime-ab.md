# VEHICLE-LIGHT2.1

LIGHT2 runtime (user): body reflection close to PS2. Regression: with the v2 INI (`Grass=1`,
no `GrassAsset`/`ShrubsAsset`) grass and shrubs disappeared. Cause: the Turkey3 base asset
defaulted to a path beside the INI; without it the whole multi-course chain stays off.
Fix: the base file (and, for robustness, the X-Trail race/wheel/COMPLETE single assets) now
default to their asset directories (`GrassAssetDirectory`, `RaceModelAssetDirectory`,
`FrontendModelAssetDirectory`). Explicit legacy keys still win.
Replace only `d3d8.dll`; grass and shrubs must be back with `Grass=1`, `Shrubs=1`.
