# Roster V4 — owner requests of 2026-11-11 and execution plan

Base: V-CAP3 35-record roster, installed by the dinput8 VehicleRoster module (owner-confirmed working,
`host-roster-01`). Owner decisions: ID25 becomes the Forklift; the Demo Forester folder is `ForesterSTI`.

## Findings that shape the plan

* Physical ID25 is the hidden retail record. Its native family/physics name is `Trooper` (retail
  `Vehicles/Trooper/*` block in `vehicles.xml`), its frontend identity is "STEEL MONKEYS FORKLIFT"
  (R5V-E0, docs/format-status.md in research/v-cap), and V-CAP3 currently shows the restored demo-9.3.1
  Trooper model there. Renaming `HeritageTrooper` to `Trooper` therefore requires ID25 to stop using the
  name `Trooper` first.
* PS2 `TNG.PAK` holds `VEHICLES\FORKLIFT\{CAR,COMPLETE,WHEEL}.PSM` and a separate
  `VEHICLES\FORESTER\{CAR,COMPLETE,WHEEL}.PSM` next to `WOOLDAND` (the PC Forester). PS2
  `DATAGAME\GAME.XML` has a complete `Vehicles2/Forklift` `gaVehicleDescriptorXml` (mass 1890 kg, wheelbase
  1.05 m, 7 gears, torque curve, ...) plus `Vehicles2/Modifications/Forklift/Player1|2`. The PC schema is the
  flat `Vehicles/<Family>/<Group>/<Key>` form, so a descriptor converter is needed.
* The PC `forklift/car.dx` collision hull is the known non-finite outlier; the PS2 CAR.PSM is the collision
  source for the Forklift.
* The retail registry has no `HeritageNewRav` meaning of its own: retiring ID34 makes the save fallback
  (`ROSTER_FALLBACK_ID0`) mandatory before that roster ships.

## Stages (in order)

1. **Save safety (loader).** `ROSTER_FALLBACK_ID0` read-time mapping of saved CarIDs the active roster does
   not provide; competition guard as the launcher had it. Required before any ID is retired.
2. **Registry composition V4** (V-CAP builder input, new runtime `v-cap4`):
   * ID25 Forklift: folder `forklift`, physics `Vehicles/Forklift` converted from PS2 `Vehicles2/Forklift`
     (+ modifications), collision from PS2 `FORKLIFT\CAR.PSM`, PS2 CAR/COMPLETE/WHEEL fleet models.
   * ID29 `HeritageTrooper` -> `Trooper` (folder + physics block; replaces the retail Trooper values),
     T2 order: directly after Navara.
   * ID30 `DefForester` -> `ForesterSTI`; its PS2 variant is the PS2 `FORESTER` model (not `WOOLDAND`).
   * ID31 `DefRav4` -> `Rav4`, ID32 `DefTomcat` -> `Tomcat`.
   * ID34 `HeritageNewRav` retired (tombstone); it becomes the DEMO variant of retail NewRav (ID12).
   * For every added vehicle (Mercedes has the least data and comes first): Vehicle Select height (several
     SDK cars stand lower than retail ones), driver names from the demos (or real Master Rallye / Dakar
     drivers, never dev/debug strings), stat bars, CarSheet icons, display names, Vehicle Select icon order.
3. **DEMO display mode.** MODEL row PS2 / PC / DEMO for families with a demo variant (megane, Tata, NewRav
   = former HeritageNewRav, LandCruiser = Demo LandCruiser on ID0, owner decision 2026-11-11: no new ID):
   the loader serves the demo resource set for that family through the roster overlay when DEMO is selected,
   and the displayed vehicle name follows the selected model (e.g. the demo name of the NewRav variant).
4. **Loader independence.** Move the SDK/G1 Challenge composition (`extra_sdk_profile.hpp`) into
   `roster.mrvr`, so one dinput8 build serves every roster.
5. **Vehicle Manager (Vehicle SDK).** Packages, install/remove/order UI, atomic apply; the V-CAP3 cars and the
   V4 changes become packages.

## Status (2026-11-11)

Stages 2-5 implemented as candidates: ROSTER_V4_STAGES_2_4.md (Forklift from PS2, PS2 models of Forklift and
ForesterSTI, MODEL = PS2/PC/DEMO with Demo names, roster-carried loader profile) and VEHICLE_MANAGER.md (Manager v1).
Test host: `.research-output/hosts/host-roster-v4-01`. Owner test pending.
