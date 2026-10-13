# Turkey3 grass + shrubs A/B

Install the new `dist/current/ps2-enabled/d3d8.dll` manually into the separate
test game. Keep the previous DLL/INI for rollback. No DLL was automatically
installed. The newly reconstructed private input stays outside the handoff.

Keep first GrassMode and GrassAsset settings that already worked. Add to
the existing `[PS2Port]` section in PS2Port.ini:

```ini
ShrubsMode=1
ShrubsConfigVersion=1
ShrubsAsset=D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\.assets\grass\Turkey3Shrubs.ps2grass
ShrubsSpriteHalfSize=0.4
ShrubsDiagnostics=1
```

Restart after each config change. First use GrassMode1/ShrubsMode0 as the
known working control. Then GrassMode0/ShrubsMode1 to isolate the branching
BUSH1 category. Finally GrassMode1/ShrubsMode1. These two modes are independent;
all defaults in the example remain0. Keep FoliageMode0, PixelProbe0 and
ReflectionMode0 during this check; puddles may stay at the previously accepted
setting as long as it is identical in each run.

Use Turkey3 and the same Free Camera bookmark near the settlement/checkpoint
region from the supplied screenshot, then drive beyond it. Look for short
branching details vs upright tufts, source-surface transitions, depth overlap,
distance fade and near-ground placement. HUD H should remain smooth. Also
check cold menus BEFORE entering any race, another course, race exit/restart,
and window/device reset. Record a session/F10 frame if a layer disappears.

One-shot `ps2_grass_config`, `ps2_grass_build`, `ps2_grass_draw` records include
`detail_category`=`grass` or `shrubs`, independent source count/hash, generated
sprite count and capture/apply/draw/restore HRESULTs. At most one private
batch per admitted category per frame. Original application draw is preserved.
If a native restore remains pending, submissions are blocked until repaired.

The existing default grass PC half-size is0.33, shrubs0.4. For another explicit
grass size, use shrub size approximately grassSize×(0.4/0.33) if retaining the
source category ratio. This is a PC size mapping; exact PS2 projected pixels,
56-unit cap, incremental activation history, GS alpha normalization and live
VU residency are not yet reproduced. The new category has no collision and
no invented wind/random-size animation. Physical tumbleweed is a separate
scene model, not this material category.

Runtime acceptance of SECOND category remains pending the user's game test.
First grass and removed frontend/HUD freezes are USER_RUNTIME_OBSERVATION.
