# Vegetation extension — bounded manual control

Existing Turkey3 `GrassMode=1`/`ShrubsMode=1` remains the fallback. All defaults
are0. New Mode2 admits only Turkey3, France1 and ItalyS1, with current certified
course/race/camera and exact full artifact hashes. Inventory of36 courses is
not runtime support for36 courses.

Four new private source artifacts are under ignored `pc-port/.assets/grass`.
They must not be distributed in Git or this source handoff. Manually copy your
local six `.ps2grass` files into a `PS2Grass` folder next to PS2Port.ini:
Turkey3/France1/ItalyS1, each Grass and Shrubs. Retain your current ENV/puddle
resources and existing options. For a controlled first vegetation A/B use:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
ReflectionMode=0
GrassMode=2
ShrubsMode=2
GrassConfigVersion=1
ShrubsConfigVersion=1
GrassAsset=PS2Grass/Turkey3Grass.ps2grass
ShrubsAsset=PS2Grass/Turkey3Shrubs.ps2grass
GrassAssetDirectory=PS2Grass
GrassSpriteHalfSize=0.33
ShrubsSpriteHalfSize=0.4
GrassDiagnostics=1
ShrubsDiagnostics=1
```

Compare Modes0/0 vs2/2 from the same bookmark on France1, then ItalyS1. Current
course IDs are `RaceTest/France1` and `RaceTest/ItalyS1`, never Italy_S1. Test
grass and shrubs separately if an artifact appears. Check Turkey3 retains both
accepted types. In one session: France1 race restart → exit → ItalyS1 → exit →
Turkey3 → an unsupported course. The last course must receive no new detail
draws. Missing/corrupt/wrong-course assets fail closed for that course/category.

Check menus immediately after cold launch, repeated HUD hide/show, Free Camera,
race restart and window-mode Reset. Look for distant fade, floating/underground
points, unexpected carpet-like density and frame-time spikes. Keep one F10 and
bounded category draw/gate records per course; source-derived full-triangle
population does not reproduce PS2 incremental clipping/history. One France1
grass face and21 ItalyS1 shrub faces are excluded for nonexact PC correspondence.
No points are borrowed from Turkey3; neither source variants nor wind are invented.
The existing cap16384 visible points/category rejects an overflowing batch
instead of silently thinning it. A new live source-population/culling parity
claim requires original PS2 evidence; this is an opt-in visual approximation.
