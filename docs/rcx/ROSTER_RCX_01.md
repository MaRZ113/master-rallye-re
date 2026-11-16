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
Engine audio: RCX loops (22 kHz PCM16) pass the SDK audio compiler; not yet in the roster (stock Megane sound).
