# Separate X-Trail validation

Decal: CLOSED by the user's new DLL runtime observation. No new decal tuning.
Body: preserve your successful ReflectionMode=4 and its format/MSAA options.

1. Manually install the PS2-enabled DLL only after preserving your accepted DLL.
   Copy the local ignored `.assets/vehicles/XtrailHeadlight.ps2glass` beside
   PS2Port.ini, or set XtrailGlassAsset to its absolute path. The 6920-byte file
   SHA256 is4a7dce3c248cfbf621c8565f85c15058d4eddcb3f7daa498a2070aa7f48fe91e.
   This original-texture-derived private asset is deliberately absent from ZIP.
2. XtrailGlassMode=0: X-Trail race, same course/weather/Free Camera bookmark,
   photograph front three-quarter and closer lamp cover. Keep XtrailFidelityMode=1.
3. Restart the process with XtrailGlassMode=1 and XtrailGlassDiagnostics=1.
   Repeat the identical bookmark/settings. Expect only the front cover to change:
   source PS2 UV/image, translucent primary and static normal-oriented highlight.
   Inner lamp layers, rear lamps, grille, body, decal and wheels are not targets.
4. Press F10 once; retain `ps2_xtrail_headlight_glass` event and current frame.
   The event must have source_upload_verified=true, successful primary/highlight/
   restore HRESULTs, restore_pending=false. One failure and one success maximum
   per device/reset. Absence of success means identity/preflight/asset admission
   did not pass; do not infer a working pilot from screenshots alone.
5. Rotate camera, drive/steer, restart race, switch car, then window-reset and
   MSAA2x/4x where supported. Body/decal must remain accepted; cover should reload
   after a real successful Reset. Menu models are unchanged.

Regressions: dark/missing front cover, reflected grille or rear lamps, detached
highlight, leaked alpha/depth behavior on adjacent draws, broken body/decal after
Reset, unexpected menu changes. Fall back to GlassMode0, preserve trace and view.
This is an alpha/sampling approximation, not pixel-exact PS2 parity.

Next evidence for brake/model admission (separate captures, no replacement yet):
- Same X-Trail race and fixed rear view: one F10 with brake released, then one
  while held; record which frame is which. These supply current light draw/state/
  texture differences; a controller-owner join is still required if native
  lighting changes cannot identify the brake source safely.
- X-Trail VehicleSelect: two F10 captures at different rotation angles; keep menu
  open for a bounded current owner/cache/VB/IB join. Historical race captures
  cannot grant COMPLETE suppression permission.
