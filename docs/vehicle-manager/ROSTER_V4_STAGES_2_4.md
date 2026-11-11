# Roster V4: Forklift from PS2, PS2 models, DEMO model row, loader-independent profile

Candidate host `.research-output/hosts/host-roster-v4-01` (`Launch-roster-v4-01.cmd`), derived from the
owner-tested `host-roster-fix-03` by `tools/roster_v4_host.py`. Saves, options and the EXE are copied unchanged.

| File | SHA-256 (8) | Built from |
|---|---|---|
| d3d8.dll | 12d69d47 | integration/base + two PS2 fleet families (`tools/ps2_fleet_new_families.py --apply`) |
| dinput8.dll | 97d5ad63 | roster-independent loader (`build_extra_capacity_candidate.py --menu-builder`, no `--sdk-runtime`) |
| MRallyeRandomizerRuntime.dll | 9146493e | unchanged |
| roster.mrvr | c93f3aac | fix-03 transaction, MRVR v2 with the MRLP loader profile |

## 1. Forklift (ID25) from the PS2 files

* **Collision.** The PS2 `VEHICLES\FORKLIFT\CAR.PSM` and the PC `forklift\car.dx` share their model space (visual bounds
  equal to 1 mm). PS2 stores the hull as the same tag-101 record; `tools/ps2_collision_hull.py` replaces the PC record
  (non-finite base vertex, empty representation B) with the PS2 one (24 vertices, 28 faces). Every byte before the hull
  and the trailing tag-0x53B bounds record (visual AABB) stay identical.
* **Physics.** `tools/ps2_vehicle_physics.py` converts the flat PS2 `GAME.XML Vehicles2/Forklift` descriptor into the PC
  `Vehicles/Forklift/<Group>/<Key>` block. The name mapping is proven by `--self-check` on all 31 families both
  platforms share (e.g. Cherokee/Trooper/Custom: 144 of 147 values equal). 45 values change (mass 1890 kg, wheelbase
  1.05 m, track 0.95/1.00 m, wheel radius 0.32 m, torque curve, gears, suspension, damage). `--pc-platform` applies
  the two changes the PC port made to every car (HandBrakeTorque x2 on 29/29 pairs, SuspAppPointOffsetVert 0.30 ->
  0.50 on 27/31); PC-only keys (TyreType) keep the PC value; the PS2 bonnet camera has no PC key.

## 2. PS2 models for Forklift and ForesterSTI

`tools/ps2_fleet_new_families.py` runs the accepted VEHICLE-CONTINUITY2 converters unchanged for two new pairs and
appends the rows after the 25 existing families (index-keyed lamp/wheel/damage tables keep their meaning):

| PC family | PS2 model | Race CAR | Menu COMPLETE |
|---|---|---|---|
| forklift | FORKLIFT | 12 meshes / 1033 tris, replaces all 10 PC draws | existing profile (complete.dx unchanged) |
| ForesterSTI | FORESTER (not WOOLDAND) | 11 meshes / 1852 tris, replaces 16 PC draws; the 8 brake-lamp records stay native | 13 meshes / 4051 tris, 15 PC draws |

No damage map exists for them (stock damage fallback), wheels stay native. PS2 FORESTER is 2-4 % smaller than the PC
Demo Forester per axis: a different revision of the same car, drawn as authored.

## 3. MODEL row PS2 / PC / DEMO, name follows the model

`MRMods/Vehicles/active/variants.ini` (roster data) lists Demo variants; dinput8 Extra Options shows DEMO as a third
MODEL choice for those families. Choosing DEMO points the CarID's registry folder (row +0x24, read by every model and
physics loader) at the variant folder; the menu car AI (vtable slot 0x69021C -> 0x44C4C0, which rebuilds
`Vehicles/<folder>/complete` only when its cached ID at +0x0C changes) is told to reload; the native name publisher
0x4819B0 (ManufacturerName = loc group 0x33, ModelName = 0x34, run only on car change) is overridden after it, and
re-run when DEMO is left.

| Family | DEMO folder | Source | Demo name (retail name) |
|---|---|---|---|
| megane | Heritage841megane | PC Demo 8.4.1 (Heritage Garage build) | SCHLESSER MEGANE 2001 (same) |
| LandCruiser | Heritage841LandCruiser | PC Demo 8.4.1 | TOYOTA LANDCRUISER (TOMMEK DIRTBEAST) |
| Tata | HeritageTata | PC Demo 9.3.1, rev131->135 set | TATA SAFARI (same) |
| NewRav | HeritageNewRav | former ID34 resources | TOYOTA RAV4 PICKUP (REECE PICKUP) |

Each variant gets a physics/modification block cloned from its family (owner rule: the DEMO model keeps the family
physics). All textures referenced by the variant models are present (offline check). Limits: the registry row is
global, so the last DEMO/PC choice for a CarID applies to every car with that ID (AI included) and to both players;
after a game start the stored choice is applied at the first Vehicle Select or Setup screen.

## 4. Loader independence (MRLP in roster.mrvr)

Owner log of fix-03: `BOOT_B_FAILED partial, mismatched or capacity-incompatible SDK profile` - the dinput8 build
carried the V-CAP3 SDK/G1 composition profile (265 operations) while the V4 roster has 276, so the Randomizer's
Challenge composition was refused. `tools/roster_loader_profile.py` now derives that profile from the roster itself
(every RVP operation as installed, the two Challenge hook mappings validated by the accepted `propose()`, the
payload immutable ranges, the SDK vehicle list from the MRVC class tables with AI masks by physical ID, retired ID34
left out) and writes roster.mrvr v2 (format: `src/native/rmod1/roster_loader_profile.hpp`; header 248/252 = section
offset/size, covered by the body digest). The VehicleRoster module parses it before the first write; the F3 boot reads
it instead of compiled data. The loader keeps only its own replay-stub addresses. v1 rosters still install; without a
profile the composition is refused as before. Tests: `tests/rmod1/roster_profile_tests.cpp` (PASS),
`vehicle_roster_tests.cpp` (PASS).

## Owner test

1. Boot logs: `MRallyeVehicleRoster.log` shows `loader_profile=roster`; `MRallyeRandomizer-boot.log` shows
   `SDK_BINDING_PROFILE_MATCH` instead of `BOOT_B_FAILED`; `MRallyeExtraOptions.log` shows `VARIANTS_LOADED count=4`.
2. Forklift: drive it (wheelbase/handling from PS2), hit walls/cars (hull), MODEL = PS2 in menu and race.
3. ForesterSTI: MODEL = PS2 shows the PS2 FORESTER in menu and race, brake lamps still work.
4. megane, LandCruiser, Tata, NewRav: MODEL row has DEMO; the menu car changes at once; LandCruiser and NewRav names
   change to TOYOTA LANDCRUISER / TOYOTA RAV4 PICKUP and back; a race with DEMO uses the Demo model.
