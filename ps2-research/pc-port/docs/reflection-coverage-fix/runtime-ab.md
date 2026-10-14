# Controlled reflection coverage A/B

Use only the PS2-enabled DLL from this handoff. Installation is manual; preserve
your previous DLL and configuration. Reuse the already verified local original
environment GXI and existing course/grass assets. None are distributed here.
Place the settings in the existing `[PS2Port]` section beside `MRRRenderer.ini`:

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
ReflectionMode=4
ReflectionConfigVersion=1
ReflectionCoverage=1
ReflectionTargetPrecision=1
ReflectionSourceGXI=PS2EnvSource64x64.gxi
ReflectionDiagnostics=1
```

Keep your valid local GXI path if it differs. Precision1 preserves the accepted
16-bit private target setting; no new image conversion is introduced. All
default values in the general example remain Stock. Invalid or missing source,
unsupported native layout/state, unknown current resources or invalid live race
certificate leave the draw unchanged.

1. Restart with `ReflectionMode=0`. Select UFO first, enter an actual race and
   wait for course admission. Save a Free Camera bookmark; capture roof/front/
   side views and one F10 frame. Record car/paint, course, AA, lighting and camera.
2. Restart with `ReflectionMode=4`, `ReflectionCoverage=1`; load the same car,
   paint, course and bookmark. Capture the same views and F10 frame after a few
   seconds of stable race state. Compare entire painted panels, not only trim.
3. Repeat for IceCream, Tata and Forester, then the other nine listed families.
   Do not change camera, lighting, AA or precision between paired images.
4. As a negative control, check a previously working Kia and ordinary scenery/
   UI. Restart the race and switch vehicle once to test resource invalidation.

Logs remain capped to one rejected and one applied record per vehicle/device.
`ps2_port_reflection_identity` includes vehicle, exact geometry hash,
`identity_authority`, rejection reason, actual override result and native draw/
restore HRESULT. Authority is either `LEGACY_VEHICLE_BODY_PROOF` or
`EXACT_SOURCE_MATERIAL_AND_CURRENT_NATIVE_CONTEXT`. A cold rejected event can
precede an applied event; it does not by itself characterize later frames.
Because logs are bounded, one successful event does not prove every panel was
modified. The paired images and F10 resource/layout records remain necessary.

Return the paired screenshots, session log and F10 capture for panels still
missing reflection. Distinguish: override rejected, override applied but weak,
and only some regions covered. No test here implies pixel-accurate PS2 parity.
