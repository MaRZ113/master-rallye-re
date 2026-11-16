# Roster RCX 01: four Rally Championship Xtreme cars in category classes (2026-11-16)

Host `master-rallye-re-base/.research-output/hosts/host-rcx-01` (copy of host-evo-tracks-01, same DLLs:
renderer 9c502589 line, loader vehicle-options, core 9146493e; Evo 2 tracks kept) + `Launch-rcx-01.cmd`.

| ID | Family | RCX car | bhp | Class | Mass kg | PeakTorque Nm |
|---|---|---|---|---|---|---|
| 38 | RcxImpreza2000 | Subaru Impreza WRC 2000 | 300 | WRC | 1430 | 403.8 |
| 39 | RcxAstraKitCar | Vauxhall Astra Kit Car | 280 | KIT CAR | 1160 | 376.9 |
| 40 | RcxSaxo | Citroen Saxo | 215 | KIT CAR | 1150 | 289.4 |
| 41 | RcxMiniCooper | Mini Cooper | 115 | CLASSIC | 870 | 154.8 |

Pilots: research/import-exclusives da25c17+ (`source_adapters/rcx.py`, `rcx_classic_pilot.py`), outputs in
`master-rallye-re-import/.research-output/rcx/pilot-*`. Physics donor retail Megane, standard MR rally tyre
(harddirt), mass from the PS2 CAR_DEFINITION table, torque = 350 Nm x bhp / 260, final drive scaled by wheel radius.

## Chain (master-rallye-re-v-cap/.research-output/vehicles/rcx-class-01)

1. `mrtool.py addon project-build` x4 (`*-build2`, PASS).
2. `build_vehicle_registry.py` with `registry-build.json` (evo-class-01 manifest + IDs 38-41, 42 records,
   previous roster = evo-class-01 identity) -> `candidate2`.
3. `roster_v4.py` with the Evo spec + IDs 38-41 in T2 (stats from the power classes) -> `runtime-v4`.
4. `vehicle_roster_build.py` -> `compiled-new`; old = evo-class-01 `compiled-new`.
5. `roster_rebase.py` (fix: records without marker colour slots) -> `rebased-base`; `roster_loader_profile.py` -> v2.
6. `vehicle_manager.py import-base --force`, frontend classes `4X4 EVO`, `WRC` (38), `KIT CAR` (39, 40),
   `CLASSIC` (41), `apply`. (A first power split A-D was replaced by these category classes at the owner's request.)

Checks: `verify_frontend_classes.py` PASS (counts [8, 13, 13, 3, 1, 2, 1]),
`verify_course_layer.py` PASS. Smoke start: `INSTALLED operations=350 records=42`, `SDK_BINDING_PROFILE_MATCH`,
`BOOT_B_READY`. Not tested in a race.

Limits: records stay in race class T2 (opponents, Results, championships); 7 of 8 frontend class slots are used (one left
for trucks). Race markers of IDs 35-41 use the default colour.
## Engine audio (roster RCX 02, same host)

Each car has an `audio-profile.json` (import 320bbcc, `rcx_classic_pilot.add_engine_audio`): the RCX 4000 rpm
on-throttle exterior loop, whole file, -1 dB, DC removed, native Megane tuning 18 (author slot 27, rebound to 38-41).
Impreza = `sub`, Astra = `vaux`, Saxo = `peu` (RCX has no Citroen folder; Peugeot 106 is the same 1600 16v class),
Mini = `mini`. `build_vehicle_registry.py` (v-cap 67122ff) now composes the SDK engine-name wrapper for added IDs:
one wrapper on the Megane intern site 0x40989C for CarIDs 38-41 (Lancer ID 28 keeps its own at 0x4093A0).
Chain as above with `*-build3` -> `candidate3` -> `runtime-v4b` -> `compiled-new3` -> `rebased-base3` ->
`roster-v3.mrvr` -> `base-v3`, import-base + apply. Smoke start: `INSTALLED operations=351 records=42`,
`SDK_BINDING_PROFILE_MATCH`, `BOOT_B_READY`. Not heard in a race yet.

## Roster RCX 04 (set 3, 2026-11-16)

Owner test of set 2 found: RCX cars sit low in the frontend, rear windows crack on the wrong triangles, and the Puma
is the test car for a native drive layout and a sixth gear.

* **Frontend height**: retail `complete.dx` (Vehicle Select / Quick Race model) is the body raised so that the lowest
  wheel point is at Y = 0 (Megane: body raised 0.461 m; the same for Forester, Jump, Kangoo, Navara, WildCat).
  The TXR3-based pilots (RCX) wrote it in the `car.dx` frame (wheels down to -0.34 m). Import
  `master_rallye.complete_ground.lift_complete_dx` shifts every vertex by -min(Y) and recomputes the marker-1339
  bounds (collision bytes unchanged); `txr3_classic_pilot` applies it.
* **Glass panes**: `_split_glass` put the upper rear window and the outer windscreen of slanted RCX glass into the
  side panes (front = within .55 m of the foremost glass point, rear = within .35 m of the rearmost), so those
  triangles cracked with the side window. Now a pane is a side window only when its face normal is clearly lateral
  (|nx| > 1.25 |nz|) and it lies away from the centre line (|x| > .45 of the glass half width); everything else is
  windscreen / rear window, split at the middle of the glass Z range. Mini (box glass) is unchanged.
* **DRIVE1 pilot, Ford Puma (ID 42)**: `Engine/DriveType` = 2 (FWD) and the full RCX 6-speed box
  (`Engine/Gears` = 8: R, N, 6 forward; retail Megane shift points, 88 % for the added step).
  - Drive layout, from the retail code: 0043C350 maps DriveType 0/1/2 to internal 0/2/1; 0043D480 internal 1 drives
    the wheels whose LSD bias is `FrontLSDBias` (0043CF10 stores it at +0x24) and leaves the rear free, internal 2 the
    opposite. So 0 = 4WD, 1 = RWD, 2 = FWD.
  - Gear count, from the retail code: 0049CEF0 allocates Gear%d / ChangeUpRevs%d / ChangeDownRevs%d by
    `Engine/Gears` and 0043C350 copies them by it; the only fixed per-gear buffers are the engine's two 11-byte flag
    arrays (+0x7C, +0x87). The SDK (v-cap `addon_sdk/physics_profile.py`) now resizes the three arrays for
    `Engine/Gears` in [3, 11] (rows cloned from the last index, values from the profile); the torque table count
    stays fixed.
  - Not verified in game: HUD gear digit, GEARBOX set-up page, AI shifting, replay and ghost with 6 forward gears.
  The other RCX cars keep the donor drive layout and the 5-speed compression until the owner accepts the pilot.

Chain as set 2 with `*-build6` -> `registry-build5.json` -> `candidate5` -> `runtime-v4d` -> `compiled-new5` ->
`rebased-base5` -> `roster-v5.mrvr` -> `base-v5`, import-base + frontend classes + apply.

**Developer menu**: EXTRA-SET2 stages `DataGame/dev.xml` with `Menues/Enabled=False` in the roster overlay, which wins
over the game's loose `DataGame/dev.xml`; Broker tools (Observatory) then find no developer menu. `vehicle_manager.py
dev-menu on|off` (stored in `roster.json`, applied by `apply`) stages it enabled on test hosts.
