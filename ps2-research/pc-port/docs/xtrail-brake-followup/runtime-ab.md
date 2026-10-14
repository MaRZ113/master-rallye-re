# Manual A/B and next model capture

Preserve the accepted DLL and config. Install the new PS2-enabled DLL manually.
Keep ReflectionMode=4, ReflectionCoverage=1, existing MSAA/precision settings,
resource paths and XtrailFidelityMode=1. Restart the game between config changes.
No new texture asset is required for these two controls.

## Terrano: same course, camera bookmark and settings

1. A: RaceModelMode=0, BrakeGlowMode=0. Capture the rear with brake released and held.
2. B: RaceModelMode=1, BrakeGlowMode=0. Only the 22 rear lamp faces should retain
   their native PC material instead of the mixed framebuffer contribution.
   The other 36 lamp faces and body retain Mode 4. Native lamps can still reflect:
   this control does not promise that every highlight disappears.
3. C: RaceModelMode=1, BrakeGlowMode=1, BrakeGlowDiagnostics=1. Release, then hold
   the brake. Expect the original off/on switching and an additive authored glow
   while braking. The original PC glow texture and geometry remain unchanged.
4. Capture F10 and retain the `ps2_brake_glow` event. Success requires
   current_upload_verified=true, override_applied=true, successful HRESULTs and
   restore_pending=false. A failed signature must keep Stock behavior.

Check `ps2_vehicle_material_partition` for Terrano: the 58-face source should
have Stock rear runs, successful HRESULT and state_restore_pending=false.
Brake input must update in live simulation; pause/Free Camera only after the
chosen brake state has reached the original engine. Use the same bookmark and
lighting for visual comparison. The supplied frames proved switching/states,
but had different view/world matrices and were not a pixel A/B.

Also test brake release, race restart, switching cars, a real window Reset and
2x/4x MSAA where supported. Regressions include a persistent glow after release,
doubled lamps, body/decal/glass loss or leaked alpha/depth/fog on nearby draws.
The on lens remains native. No X-Trail brake override is enabled in this DLL.

## Next X-Trail frontend capture

Set FrontendGeometryDiagnostics=1 before a cold game start. Select X-Trail in
VehicleSelect, press F10, wait for rotation, press F10 again, then select away
and return. Leave the menu open. This is read-only; the model remains PC.

The observer records current source hashes, resource generations and W/V/P only
on F10 captures, with at most two frames per source and a lifetime attempt cap.
These captures do not authorize model suppression. The current native owner/cache
join remains necessary; the precise next observation point is in model-readiness.md.
Diagnostics OFF performs no frontend geometry rescanning.
