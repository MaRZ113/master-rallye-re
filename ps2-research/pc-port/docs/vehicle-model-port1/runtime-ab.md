# One bounded user test

Close the game before replacing the proxy manually. The new PS2-enabled DLL is
`dist/current/ps2-enabled/d3d8.dll`; keep a copy of your accepted DLL. No installer
or automatic deployment is provided. Preserve your working PS2Port.ini grass,
water, reflection asset paths, renderer options and Free Camera bookmarks.

1. Start with Xtrail in the same race/lighting/bookmark. Set ReflectionMode4,
   ReflectionCoverage1, RaceModelMode0, VehicleModelDiagnostics1. FoliageMode0,
   PixelProbe0. Capture screenshot/F10. This retains the accepted old path.
2. Close/relaunch with only RaceModelMode changed to1. Capture the same view and F10.
   The expected current source record has195 shiny faces and14 flat faces. Only the
   shiny faces receive the new Mode4 partition; the14flat faces intentionally keep
   PC Stock. Look for `ps2_vehicle_material_partition`, exact source digest,
   successful HRESULT, `state_restore_pending=false` and the two actual subranges.
3. Repeat for LandCruiser, Bruno, SeatBuggy, ChevyBlazer and Forester if step2 is
   stable. Check windows/rubber/decals, an unaffected car, race restart, menu exit,
   real window Reset, and your working MSAA settings. Keep comparable screenshots.
   A missing partition record means admission was not confirmed, not success.
4. Optional menu observation: restart with FrontendGeometryDiagnostics1 and select
   Forester. F10, rotate, F10. Collect `ps2_frontend_upload_identity` records plus
   those captures. No model replacement should occur. Diagnostics stop after128
   attempts; no recurring per-frame Broker reads. Disable after this one test.

The first live evidence for this DLL must confirm actual source hashes and subdraws.
Current unit tests are not a visual PASS. COMPLETE will remain PC stock even if all17
source hashes appear until the exact owner/cache/submission join is proved.

Logs are bounded: at most one material-partition record per each of nine registered
source records/device, at most17 frontend source records. Existing reflection
diagnostics have their previous bounded policy. ReflectionMode4 remains an
approximation to the proved PS2 source; no pixel-parity claim.
