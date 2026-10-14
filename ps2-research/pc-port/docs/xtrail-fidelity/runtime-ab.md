# X-Trail-only A/B

Close the game and install the new PS2-enabled DLL manually, retaining the accepted
DLL as rollback. Keep existing local reflection/grass/water assets and settings.
Do not replace the full working INI with a shortened example.

1. Select X-Trail in a race with the same lighting/settings/Free Camera bookmark.
   Keep ReflectionMode4, ReflectionCoverage1, RaceModelMode1, FoliageMode0,
   PixelProbe0. Set XtrailFidelityDiagnostics1 and XtrailFidelityMode0. Capture F10
   and a side/front view where the169number plate is readable.
2. Close/relaunch with only XtrailFidelityMode1 changed. Capture that same bookmark,
   then another angle showing the number plate and adjacent paint. Expect a body-like
   environment contribution on the14decal surfaces, without a second silhouette
   or changed number/UV/tint/placement. The effect may be angle-dependent.
3. Inspect `ps2_xtrail_decal`: source_upload_verified=true, override_applied=true,
   native_target_draws=1, triangles14, successful apply/draw/restore HRESULTs and
   restore_pending=false. F10 includes the logical original DIP and the explicitly
   native-only replacement UP event; that is not two rendered target draws.
4. Perform a real window Reset, race restart and return to menus; repeat the view.
   Use your working4×MSAA/16-bit target, optionally repeat with32-bit or2×. Unsupported
   driver/context/source attributes must stay Stock; no silent MSAA disable.

Should change: X-Trail number sticker reflective contribution only. The red side
body/hood/trim remain as the working RaceModelMode1/Mode4 result. Wheels, tire rubber,
headlight covers/lamp overlays, windshield, driver, other cars and menu models
must retain their previous behavior in this comparison.

Regressions: stretched/mirrored number, lost alpha/geometry, duplicate plate outline,
new tyre/glass reflection, changed adjacent draw state, disappeared headlights,
window Reset leak, menu FPS/HUD stutter or native restoration failure. Restore
XtrailFidelityMode0 and retain logs/screenshots. A failed upload guard means no
validated new override; it does not prove a visually successful port.

The supplied PS2 menu image uses COMPLETE; compare race detail against the cropped
race image separately. Different skies/cameras/lighting prevent exact brightness
or pixel-parity claims. No new PCSX2/runtime result for this DLL is claimed yet.

Frontend next capture, separately: X-Trail VehicleSelect with two rotations, current
CarModel/en3d owner/cache and upload hashes. No frontend replacement is enabled by
XtrailFidelityMode. Do not treat Forester menu observations as X-Trail evidence.
