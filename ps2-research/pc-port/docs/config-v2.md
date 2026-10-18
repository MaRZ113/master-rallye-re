# PS2Port.ini v2 (implemented in fix8)

User decision 2026-10-17: drop `PS2` from race keys and the `Mode` suffix everywhere. Implemented by
`renderer/ps2_config.hpp`: a v2 key wins when present; a historical key is read only when its v2 key is absent.
Final key names: Reflection, ReflectionCoverage, ReflectionTargetPrecision, ReflectionSourceGXI, RaceFleet,
RaceModelAssetDirectory, BrakeGlow, BrakeGlowAsset, FrontendModel, FrontendModelAsset,
FrontendModelAssetDirectory, PS2ContentFixes, Grass, Shrubs, GrassAssetDirectory, CourseObjects,
CourseObjectsAsset, Foliage, Diagnostics. PS2-COLOR1 adds `PS2Color` (0/1) and `PS2ColorCurve` (k_R,k_G,k_B), see docs/ps2-color1. COURSE-LIGHT1 adds `GroundDetail` (0/1) and `GroundDetailAsset`, see docs/ground-detail1. PS2-OUTPUT1 adds `PS2Output` (0/1), see docs/ps2-output1. DIAG-REFLECTION2 adds `PS2MotionBlur` (0/1), `PS2MotionBlurStrength` (default 0.195) and `ReflectionDebug` (0, 1 = quadrant pattern, 2 = env target view), see docs/diag-reflection2. HUD-PORT2 adds `PS2HudDamage` (0/1) and `PS2HudAssetDir` (default PS2Hud), see docs/hud-port2. HUD-PORT3 adds `PS2HudMap` (0/1), see docs/hud-port3. HUD-PORT4 adds `PS2HudTemplate` (0/1) and `PS2HudHidePcOnly` (0/1), see docs/hud-port4. HUD-PORT5 adds `PS2HudTimeDiffs` (0/1), see docs/hud-port5. HUD-PORT6 adds `PS2HudSplitFlash` (0/1); PS2HudMap gains split crossbars and opponent marks, PS2HudTemplate draws ticks/finish over the bar, see docs/hud-port6. FLEET-ALL-CARS1 adds `PS2FleetAllCars` (0/1, needs `RaceFleet=1`): PS2 cars for every race participant and Attract, see docs/fleet-all-cars. RACE-MODES1 adds `PS2RaceAllModes` (0/1: Master Rallye, Rallye Cup, Challenge, Invitation, replay) and `PS2FrontendAllCars` (0/1, needs `FrontendModel=2`: one PS2 COMPLETE model per car shown at once), see docs/race-modes1. SPLIT-SCREEN1 adds `PS2SplitScreen` (0/1): two-player split-screen races, see docs/split-screen1. PERF2 adds diagnostic `PS2PerfTiming` (0/1) and `PS2PerfWindow` (frames, default 300), see docs/perf2. `FrontendGeometryDiagnostics` (forces buffer mirroring) is not part
of `Diagnostics`; it remains a legacy-only research probe. The table below is the original proposal.

Inventory: every `[PS2Port]` key the renderer reads today, grouped by the decision.
"Fixed" means the code stops reading the key and uses the stated value.

## Kept (user-facing features)

| Key | Values | Note |
|---|---|---|
| `ReflectionMode` | 0 / 4 | (1–3 were diagnostic variants; keep accepting 4 only + 0) |
| `ReflectionCoverage` | 0 / 1 | |
| `ReflectionTargetPrecision` | 0 / 1 | 16/32-bit target choice stays (driver dependent) |
| `ReflectionSourceGXI` | path | asset |
| `RacePS2FleetMode` | 0 / 1 | **umbrella for all race cars**: implies the former RacePS2ModelMode, RacePS2WheelMode, RacePS2ModelParts, RacePS2CrewMode, XtrailFidelityMode, RaceModelMode |
| `RacePS2ModelAssetDirectory` | dir | asset directory for all CAR/WHEEL/OFF assets |
| `FrontendModelMode` | 0 / 1 / 2 | kept as requested |
| `FrontendModelAsset` | file | kept as requested |
| `FrontendModelAssetDirectory` | dir | kept |
| `BrakeGlowMode` | 0 / 1 | |
| `BrakeGlowAsset` | path | |
| `GrassMode`, `ShrubsMode` | 0 / 1 / 2 | |
| `GrassAssetDirectory` | dir | |
| `CourseObjectsMode` | 0 / 1 | |
| `CourseObjectsAsset` | path | |
| `FoliageMode` | 0 / 1 | (2/3 were diagnostic alpha/depth variants → removed) |
| `PS2ContentFixes` | 0 / 1 | **new**: opt-in corrections of original PS2 content defects (Navara co-driver face, Tata CAR right window, Kamaz COMPLETE right window). 0 = original PS2 content |
| `Diagnostics` | 0 / 1 | **single switch** replacing every per-feature `*Diagnostics` and the F10 capture flags |

## Removed

| Key(s) | Reason | Fixed value |
|---|---|---|
| `*Version` (Reflection/VehicleModel/XtrailFidelity/XtrailGlass/BrakeGlow/FrontendModel/RacePS2Model/RacePS2Wheel/CourseObjects/Grass/Shrubs) | internal schema gates | 1 |
| `ReflectionDiagnostics`, `VehicleModelDiagnostics`, `XtrailFidelityDiagnostics`, `XtrailGlassDiagnostics`, `BrakeGlowDiagnostics`, `FrontendModelDiagnostics`, `FrontendGeometryDiagnostics`, `RacePS2ModelDiagnostics`, `RacePS2WheelDiagnostics`, `CourseObjectsDiagnostics`, `GrassDiagnostics`, `ShrubsDiagnostics` | per-feature debug | = `Diagnostics` |
| `RacePS2FleetCapture`, `RacePS2FleetDamageCapture`, `RacePS2DamageCapture` | F10 sidecar debug | = `Diagnostics` |
| `PixelProbe`, `PixelX`, `PixelY`, `PixelLaterDrawOrdinal` | pixel readback debug | off |
| `RacePS2ModelMode`, `RacePS2WheelMode`, `RacePS2ModelParts`, `RacePS2CrewMode`, `XtrailFidelityMode`, `RaceModelMode` | X-Trail/pilot-selective switches | = `RacePS2FleetMode` |
| `RacePS2ModelAsset` (=XTRAIL-CAR), `RacePS2WheelAsset` (=XTRAIL-WHEEL-DRAW) | X-Trail-only filenames | built-in names, looked up in `RacePS2ModelAssetDirectory` |
| `XtrailGlassMode`, `XtrailGlassAsset` | superseded X-Trail headlight pilot (user has 0) | off (removed path stays dead code until deleted) |
| `KiaBrakeOnAsset` | Kia-only filename | built-in name in asset directory |
| `GrassAsset`, `ShrubsAsset` | Turkey3-only single files (directory covers all 36 courses) | directory lookup |
| `GrassSpriteHalfSize`, `ShrubsSpriteHalfSize` | tuning constants | 0.33 / 0.4 |
| `DrawTiming`, `DrawTimingWindow` | perf build only | not in release builds |

## Compatibility

Old keys are ignored (not errors). The session log records `ps2_port_config` with
the effective values once per device so an old INI is visibly mapped. A new
`PS2Port.ini.example` and a migrated copy of the user's current INI are shipped.
