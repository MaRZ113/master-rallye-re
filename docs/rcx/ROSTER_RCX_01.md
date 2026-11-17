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

## Roster RCX 07 (cars set 7, 2026-11-17)

Owner test of host-rcx-01 found three car problems. All of them have the same kind of cause: the converter did not
follow a retail MR convention. The conventions, with their evidence, are in import
`master_rallye/retail_vehicle_contract.py`.

* **Snags on Clashin Darroch / Fire Rock (RCX cars only, not FPS):**
  - Retail hulls (tag101) end well above the body. The Megane body goes down to -0.246 m, its hull only to -0.002 m.
  - At rest a retail hull is 0.34-0.50 m above the tyre contact (hub Y = -RideHeight, minus the wheel radius). That
    leaves 0.09-0.20 m above MaxBounce (0.25-0.30 m).
  - The RCX pilots fitted the donor hull to the paint draws, so the hull bottom sat on the sills (-0.10 .. -0.17 m).
    With the real RCX wheels (radius 0.25-0.34 m), the hull was 0.20-0.35 m above the contact, which is a margin of
    -0.10 .. +0.05 m.
  - So the hull reached the course BSP on every compression.
  - Fix: SDK `collision_fit` takes an optional `floor_y_m` (import and v-cap `addon_sdk/physics_collision.py` and
    `physics_profile.py`, guard ±1 m). `txr3_classic_pilot` sets that floor to the donor's hull clearance above the
    tyre contact: 0.468 m, which leaves a margin of 0.168 m for every RCX car.
  - The 4x4 Evo hulls were already +0.22 .. +0.29 m.
* **Too bright in Vehicle Select, and dust too bright:**
  - Every retail car.dx and complete.dx vertex carries a baked grey,
    `round(255*(0.4+0.3*sqrt(max(0,n.y))))`, with R = G = B. It matches exactly on 99.8-100 % of the vertices of
    Megane, Forester, Pajero, Navara and X-Trail. Only the brake glow card is 255.
  - The converters wrote 255 everywhere, so RCX and Evo cars were about 1.8x brighter in the frontend and in race.
  - The R-SURFACE1 grime pass is `DIFFUSE x tint`, so the dust on those cars was too bright as well.
  - Fix for RCX: `txr3_classic_pilot` applies `prelight_dx` to car.dx and complete.dx.
  - Fix for the 4X4 EVO cars (35-37): `tools/vehicle_prelight.py` patches the colour bytes in the roster base. Their
    resources carry later lamp work. The brake-lamp registry digests cover positions and UVs only, so they stay
    valid.
* **No tail or brake glints at night:**
  - Glints are drawn for cars that have a lamp rig in `Atmosphere/vehicles/lamp_rigs.txt`. The host file listed the
    25 retail families only.
  - A rig is matched by a lens draw, and lenses are found by texture name (light | lamp | indicat | *bl). The brake
    layer is found by the name `breaklightson`.
  - RCX textures were content hashes (`uvs-<sha>`), and the brake layers were named `stop-lit` / `stop-glow`.
  - Fix (`lens_textures` in the RCX spec):
    - the head and brake lamp parts get power-of-two crops of their atlas, named `<family>-headlight[N]-tga` and
      `<family>-brakelight-tga`;
    - the brake layers are named `<family>-breaklightson-tga` and `<family>-breaklightsonglow-tga`;
    - `tools/addon_lamp_rigs.py` solves the rigs with `atmosphere_lamp_rig.py` and merges them into the host file,
      together with the night lens masks.
  - Puma: the solver finds no white headlamp texels, so it has tail and brake glints only.

Chain: build.py (`build-set7.log`) -> `*-build7` -> `registry-build6.json` -> `candidate6` -> `runtime-v4e` ->
`compiled-new6` -> `rebased-base6` -> `roster-v6.mrvr` -> `base-v6`. Then `vehicle_prelight.py base-v6` for the
three 4X4 EVO families, `import-base --force`, `apply` (`apply-cars07.log`), `seed-course-progress`, and
`addon_lamp_rigs.py` (rigs in `rcx-class-01/lamp-rigs-07`).

Checks: verify_course_layer PASS, verify_frontend_classes PASS, all 9 project-builds PASS, record_count 47.
Not tested in game.
