# Roster EVO 01: three 4x4 Evo vehicles on the Roster V4 base (2026-11-14)

Host `master-rallye-re-base/.research-output/hosts/host-evo-01` (copy of host-grime-g0-01: renderer 9c502589 with
grime G3.3, VehicleGrime.ini, frame pacing; loader vehicle-options-03 3b425dc4, core 9146493e).

| ID | Family | Source | Pilot (research/import-exclusives) |
|---|---|---|---|
| 35 | Evo1FordSportTrac | 4x4 Evo 1 FEST43 (prepared) | `.research-output/evo1-collection/fest43-pilot` |
| 36 | Evo2JeepCherokeeRace | 4x4 Evo 2 JGCRSUV | `.research-output/evo2-collection/jgcrsuv-pilot` |
| 37 | StillenSilverado | 4x4 Evo 2 GC SMT (GC-only monster) | `.research-output/evo2-gc/smt-pilot` |

All three are temporarily in T2 (record and menu class); the 4X4 EVO frontend class is the next step.

## Build chain

1. `mrtool.py addon project-build` per pilot (master-rallye-re-v-cap, all PASS).
2. `build_vehicle_registry.py` with `evo-class-01/registry-build.json` (v-cap3 manifest + IDs 35-37, 38 records).
   The packaged parent Data.sma no longer exists; the builder now accepts the retail archive for it (v-cap a873963).
3. `roster_v4.py` with the runtime-02 spec plus the three IDs in T2.
4. `vehicle_roster_build.py` for both the previous runtime (runtime-02) and the new one, into a scratch game.
5. `tools/roster_rebase.py`: the installed manager/base = runtime-02 + owner fixes; the tool replays the fixes on the
   new runtime. Native: race-marker colours of IDs 0-34, record pushes (Trooper small icon) and the Forklift
   locked-description branch (`vehicle_lamp_authoring.unlock_description`); the replay on runtime-02 reproduces the
   installed base byte for byte (checked by the tool). Resources: 52 fix files kept, 361 from the new runtime,
   3 XML merged with `git merge-file` (HeritageNewRav lines dropped: retired ID34, now a DEMO package).
6. `roster_loader_profile.py` (MRVR v2), `vehicle_manager.py import-base --force`, `apply`.

Smoke start: `INSTALLED operations=276 records=38`, `SDK_BINDING_PROFILE_MATCH`, `BOOT_B_READY`,
`REGISTRY_READY count=38`. Not tested in game.
