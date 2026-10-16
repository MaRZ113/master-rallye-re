# PORT3 fix8.2

fix8.1 user-confirmed: all four PS2ContentFixes load and are visible; UFO OFF confirmed (fix8).
fix8.2 only changes the v2 meaning of `Grass`/`Shrubs`: `1` = PS2 terrain detail on every verified
course (the historical mode 2). The legacy `GrassMode=1` Turkey3 pilot is unchanged.
Replace `d3d8.dll`, set `Grass=1` and `Shrubs=1` (see the commented `PS2Port.ini.migrated-pristine`).
