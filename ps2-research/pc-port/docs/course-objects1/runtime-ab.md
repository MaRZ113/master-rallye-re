# Turkey3 source-layer A/B

Use the separately built PS2-enabled DLL in an isolated PC setup; installation
is manual. The original supported MRallye.exe SHA is
bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
Use unmodified retail Turkey3 data. Keep the previous reflection test DLL/logs.

The private asset is already generated locally at
ps2-research/pc-port/.assets/course-objects/Turkey3Puddles.ps2obj.
It is excluded from Git/handoff. To reproduce it from your original PS2 corpus:

```powershell
python ps2-research/pc-port/tools/prepare_course_objects.py `
  --ps2-input-root 'D:\Game\Master Rallye PS2' `
  --asset-out ps2-research/pc-port/.assets/course-objects/Turkey3Puddles.ps2obj `
  --report-out ps2-research/pc-port/docs/course-objects1/source-contract.json
```

Put PS2Port.ini beside MRRRenderer.ini, with an absolute private asset path:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
ReflectionMode=0
CourseObjectsMode=0
CourseObjectsVersion=1
CourseObjectsAsset=D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\.assets\course-objects\Turkey3Puddles.ps2obj
CourseObjectsDiagnostics=1
```

1. Start Turkey3 normally. Save a Free Camera bookmark over the candidate region.
   Overall source bounds are X1957.56..3436.29, Y19.01..37.96, Z-818.29..534.19
   in game coordinates; this is a broad surface region, not a camera pose.
   Capture Mode0 with fixed lighting, resolution and settings.
2. Restart with only CourseObjectsMode=1 changed. Restore the same bookmark.
   Capture the same view and one closer view. Compare the ground, cars, HUD and
   nearby scenery. Record both logs and optionally one F10 frame per mode.
3. Check ps2_course_objects_config effective_mode=1 and one
   ps2_course_objects_draw with additional_native_draws=1, all successful
   capture/apply/draw/restore HRESULTs, and the exact private artifact SHA.
   Each device logs at most one admission rejection and one attempted addition;
   restoration failures are always reported. No F10 capture is required to
   activate the layer.
4. Leave CourseObjectsMode=1 and load another course, then return to Turkey3.
   There must be no additions on other courses. Check window-mode change/Reset
   and Free Camera HUD hiding if practical. Keep logs if a gate refuses drawing.

If there is no successful additional draw, retain its gate reason rather than
loosening course/target/camera proof. If a surface is hidden, inspect from another
view while preserving original heights; PC terrain differs and may cover it.
Do not judge the static material preview as PS2 water appearance. Source alpha
is opaque; PS2 runtime ground-gap color, UV animation, secondary pass and LOD
selection are not implemented here. Runtime visibility and state/Reset behavior
still require this user test.
