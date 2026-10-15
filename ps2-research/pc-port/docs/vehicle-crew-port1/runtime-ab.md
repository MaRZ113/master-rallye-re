# Crew, COMPLETE fleet and rear-lamp A/B

New implementation is **pending user runtime**. Static/source/native mock tests do not confirm appearance, menu FPS or MSAA on the user's GPU. No DLL or asset has been installed automatically.

Use the release DLL named in `validation.json`, keeping a copy of the currently accepted DLL. Keep existing grass, water, reflection, camera and HUD settings. Restart the game after changing PS2Port.ini; these selectors are read at device construction.

## 1. X-Trail static crew

Keep the already installed original-derived XTRAIL CAR and WHEEL assets. Use the same X-Trail race, Free Camera bookmark and lighting for both runs:

```ini
[PS2Port]
ReflectionMode=4
RacePS2ModelMode=1
RacePS2ModelVersion=1
RacePS2ModelParts=1
RacePS2ModelDiagnostics=1
RacePS2ModelAsset=XTRAIL-CAR.ps2model
RacePS2WheelMode=1
RacePS2WheelVersion=1
RacePS2WheelAsset=XTRAIL-WHEEL-DRAW.ps2model
RacePS2CrewMode=1
```

Compare CrewMode=0 and 1. Mode 0 retains the preceding native PC crew fallback. Mode 1 submits 544 original PS2 crew triangles: two faces 48+48, bodies 252, helmets 148, visor/head inserts 48. Suppression applies only to verified PC crew records (444 triangles), with their current chassis WORLD. Seats, dashboard and wheel physics remain native/unchanged. Body and decal reflection, headlight glass, independently steering wheels and tread wrapping should retain their accepted appearance.

Take F10 outside the windshield and from both side windows. Check original helmet/face textures, shoulder belts, exactly one driver and one codriver, correct depth through glass, no detached heads or floating pieces. Drive, steer, restart the race and reset the window with MSAA 4x. Save F10 after each lifetime change. `ps2_race_model_part` identifies source verification, source PS2 root, submitted faces, draw and restore HRESULTs. It is capped per device/reset. For crew parts expect root0 face draws48/48/body252, root8 helmets148 and the PC17 boundary's combined52 (48 crew +4 trim). A missing current identity retains its native PC part; do not call that a successful replacement.

## 2. Frontend fleet COMPLETE

Mode 1 remains the user-confirmed X-Trail frontend fallback. Mode 2 enables the 20 exact profiles listed in `coverage.md`. Manually copy only the admitted `*-COMPLETE-FLEET.ps2model` files listed in `private-assets.json` from the repository's ignored `.assets/vehicles/` into a separate `PS2Vehicles` folder beside the game INI. The release source ZIP excludes original/converted proprietary model bytes.

```ini
[PS2Port]
FrontendModelMode=2
FrontendModelVersion=1
FrontendModelAssetDirectory=PS2Vehicles
FrontendModelDiagnostics=1
ReflectionMode=4
```

First compare X-Trail Mode1 vs Mode2, then LandCruiser and ChevyBlazer Mode0 vs Mode2. Rotate the whole model, switch away/back, reset the window and return to the menu after a race. Verify wheels, glass, UV orientation, full suppression and no duplicate body. Check stationary menu frame pacing. Only one family's private CPU/GPU resources are retained; invalid/missing files are negatively cached until Reset/restart. A full prior-frame/current-upload certificate is required before any source suppression. Logs name the actual family and verified/suppressed record counts. A gate/fallback is Stock, not proof of a PS2 model.

Kia, Tata, Mattserati, Simmbugghini, UFO and PC Forester/PS2 WOOLDAND remain excluded for the exact material gaps in the matrix. PS2 FORESTER is not aliased to PC Forester; MOONBUGGY/TANK have no paired PC owner.

## 3. Rear lamps and glow

On X-Trail with ReflectionMode=4, inspect the **two upper rear OFF lamp regions**, then hold/release the brake. Only the verified six OFF triangles get the existing mixed reflection path. ON triangles and additive glow retain their separate native submission order. Equal OFF/ON position geometry is insufficient; the exact position+UV signature is mandatory. No entire-light reflective/emissive override is added.

Compare BrakeGlowMode=0 vs1 with the existing `BrakeGlowAsset=PS2BrakeGlow.gxi`, `BrakeGlowVersion=1`, `BrakeGlowDiagnostics=1`. The original RGB-fade asset SHA is `b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09`. The existing additive ONE/ONE policy now admits 20 exact source geometry+UV profiles. It submits the original native glow draw once, with its original geometry, UV, WORLD and returned HRESULT; the glow transaction disables depth writes and restores all altered states. Native brake timing remains authoritative; no new controller reads exist.

Check OFF, sustained ON, release, near/far cameras, restart and Reset. Terrano is a useful prior-path regression control; X-Trail checks new coverage. `ps2_brake_glow` names the family and reports current-upload verification and apply/draw/restore HRESULTs, at most one successful and one failed record per profile/reset (plus one unknown profile). Unsupported native state/layout stays Stock.

Reject the candidate on duplicate crew/body, flipped textures, floating parts, nonsteering wheels, persistent glow after release, changed body/decal reflection, lost window occlusion or restore errors. Save the INI, DLL SHA and F10 for the failing state. No PS2 pixel parity is claimed.
