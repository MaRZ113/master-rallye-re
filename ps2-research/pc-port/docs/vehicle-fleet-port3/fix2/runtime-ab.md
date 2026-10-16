# PORT3 fix2 runtime check

Manually replace only `d3d8.dll` in the test installation (Master Rallye
Pristine). Keep every PS2Vehicles file and INI setting from the fix1 kit:
RacePS2FleetMode=1, RacePS2ModelMode=1, RacePS2WheelMode=1, ReflectionMode=4,
ReflectionCoverage=1, BrakeGlowMode=1, RacePS2FleetCapture=1. Keep diagnostics
enabled so lamp rejections reach the session log. No automatic installation.

Fleet replacement is single-car only: Quick Race/Time Trial **without opponents**.

1. NewRav, healthy: F10 with the brake released. Expected in the race-fleet
   sidecar: `fleet_lamp_continuity` layer OFF with reason
   `original_ps2_off_mesh_current_owned_deformation`, plus
   `fleet_private_off_submission` with draw_hresult=0 and restore_hresult=0.
   Inspect the formerly flat OFF lamp region.
2. NewRav: apply and release the brake. ON_CORE and ADDITIVE_GLOW must stay
   separate and unchanged.
3. NewRav damaged: F10 brake released. The OFF event shows
   private_damage_tree=true, or a named rejection. Fallback stays Stock.
4. Bruno and Mattserati: one brake-released F10 each. Report the OFF reason from
   the sidecar or session log, whether accepted or rejected.
5. Control: one race with opponents. No PS2 fleet replacement is expected. The
   session should no longer show fleet costs (needs the timing build).

Report the car, brake state, healthy or damaged state, F10 frame numbers and the
OFF reason strings. Pixel parity and full PS2 deformation are not claimed.
