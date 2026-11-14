# 4x4 Evolution 2 courses in Master Rallye (COURSE-IMPORT1)

Branch `feature/evo2-tracks` (from `feature/vehicle-options`). Every Evo 2 race SIT is converted by the same code; the
races are new registrations in their own Quick Race category ("4X4 EVO"); no retail race, scene, menu row, competition
or save key is replaced.

## Pipeline

| Step | Tool | Output |
|---|---|---|
| Read the Evo 2 race | `tools/evo2_tracks/evo2_track.py` | `Track`: SIT, LVL, height/colour/shadow grids, TEX list, textures, SMF models |
| Convert | `tools/evo2_tracks/to_course.py` | Course Studio project (`master_rallye.studio.CourseProject`, reopenable in the Blender Course Studio) |
| Build | `tools/evo2_tracks/build_track.py` (Course Studio `build_course`) | native course: DX (render + tag100 BSP + land DB), FEED textures, RaceTest XML/HNT, ICont SFL |
| Menu art | `tools/evo2_tracks/previews.py` | two 128x128 Race Select screenshots per race (Blender EEVEE render of the project) |
| Pack | `tools/course_pack.py make` | `course-pack.json` + `resources/` + `art/` |
| Install | `tools/vehicle_manager.py course-pack-add` + `apply` | roster.mrvr with the course layer, resources in the roster overlay |
| Verify | `tools/verify_course_layer.py <game>` | Unicorn emulation of the native layer on the installed roster |

Course Studio core is used from `master-rallye-re-course/src` (PYTHONPATH), the Vehicle SDK frame assets from
`master-rallye-re-v-cap/src` (as the Vehicle Manager already does).

```
set PYTHONPATH=D:\Game\Master Rallye\master-rallye-re-course\src;tools\evo2_tracks
python tools/evo2_tracks/build_track.py --pod <Evo2>\DVALLEY.POD --work .research-output\evo2-tracks\work --resource-root <retail tree>
python tools/evo2_tracks/previews.py .research-output\evo2-tracks\work\projects\DVALLEY --out .research-output\evo2-tracks\work\previews\DVALLEY
python tools/course_pack.py make --name EVO2 --label "4X4 EVO" --out <pack> --course <work>\builds\Evo2Dvalley --title "Deadman's Gulch" --shots <work>\previews\DVALLEY --distance-km 7.1
python tools/vehicle_manager.py --game <game> course-pack-add <pack>
python tools/vehicle_manager.py --game <game> apply
python tools/vehicle_manager.py --game <game> seed-course-progress
python tools/verify_course_layer.py <game>
```

## Evo 2 format facts (PC, POD2; GameCube 4x4.elf symbols for the loader semantics)

* One race = `WORLD/<name>.SIT` (text). Header: `Race Track Name`, `Track Race Type` (2 race, 3 hill climb, 6 obstacle
  park / mission), `track length` (feet, lap length). Then 8 start vehicles (vehicle 1 = player start, `wOrient` third
  value = heading, radians, 0 = +Z), boxes, course, paths, backdrop.
* Boxes `{ n Kind ... } Kind`: `staticName` (SMF), `size` (full extents, feet; equals the model bounding box: SMF models
  are centred), `wPos` (centre), `wOrient` = (pitch, bank, heading); matrix = `CMatrix::genMatrix` with v0 = pitch,
  v1 = heading, v2 = bank. Kinds: CCollide (collisionType 0 = box, 1 = polygon: docks, bridges, cliffs), CNonCollide,
  CCollisionBox (invisible), CCheckpoint (gate: 240 ft x height, ordered along the race), CTree, CTrain, CFlyingObject,
  CTreasure, CTriggerBox.
* `*** Course ***`: the AI course as straight segments (`cstart`, `cend`, width); arcs between them are implicit.
* `LEVELS/*.LVL`: heightmap / colour / texture-list names, water height and RGBA, detail texture, light vector. The
  water height is in half feet: value / 2 gives lakes, rivers and seas on 4-21 % of the maps with a dry AI line (fords
  on up to 4 %) across ten races; read as feet it floods 60-100 % of every map and the AI lines run 40 m under water.
* `DATA/<lvl>.RAW` 256x256 u16 heights, `height_ft = value / 32`, 32 ft cells, row index = z (checked against the
  gates: centre = ground + half height). `.CLR` per-cell ground texture (low 12 bits) into the TEX list; `.SDW` per-cell
  baked shadow texture (0x8000 / 0x4000 = none; drawn instead of the ground tile); `.RTD` ray data (unused).
* `DATA/<lvl>.TEX`: `textureCount,shadowTextureCount`, then `terrainType,scrubDensity,NAME.RAW`. Terrain class =
  type // 100 in the 4x4.elf table Default, Cement, Dirt, Mud, Sand, Grass, Gravel, Ice, Snow, Metal, Wood, Rock;
  1300 = water (CGround::getTypeActions). Scrub density None/Sparse/Medium/Dense.
* Textures: `ART/*.RAW` 8-bit indexed (square) + `.ACT` 768-byte palette + optional `.OPA` alpha; `*.TIF`.

## Conversion decisions

* **Frame.** Evo 2 is left-handed (+X right, +Z front, +Y up; TRK wheel positions). Master Rallye's world is
  right-handed (+X left): the captured gameplay VIEW has det = -1 with an LH projection (`_34 = 1`), see
  `ps2-research/pc-port/docs/menu-grass-fix1/final-report.md`, and the Vehicle SDK maps "MR +X left / +Z front". Every
  output point is mirrored X -> -X and every triangle re-wound, so curves keep their direction and text is not
  mirrored. (The R-SURFACE1 grime note calling MR left-handed is a comment, not a measurement.)
* **Units.** feet x 0.3048.
* **Terrain.** Cells within `--corridor` (190 m) of the AI route, the gates and the start are solid ROLE_TERRAIN with
  their own Evo tile (shadow tile when present) in 1024x1024 atlas pages (64 px tiles, 2 px gutter); the remaining map
  is drawn only, in 2x2-cell blocks with one 1024x1024 overview texture and skirts where blocks meet single cells.
* **Limits.** Native gaLimitsAI resets at 90 m (inner) / 140 m (outer) from the AI line: free driving across open terrain
  between the gates, always inside the solid corridor.
* **Race.** Start = vehicle 1. Circuits (closed courses) are one lap: the AI route starts at the start line and the
  finish is placed 150 m before it (the grid stands behind the start; a finish on the start line would trigger at once).
  The start/finish gate of the lap is dropped; every other gate is a native checkpoint (`gaRaceSplitTimeAI`) with extra
  time for the next leg at about 40 km/h plus 25 s. Radius = half the gate width (18..40 m), enlarged to the gate's
  offset from the AI line + 8 m (at most 45 m; gates further out move towards the line) so the AI trigger it too.
* **Surfaces.** Evo class -> MR Surface.xml: cement -> tarmac, dirt -> harddirt, mud -> mud, sand -> gravel, grass ->
  grass, gravel -> gravel, ice -> harddirt, snow -> gravel, metal -> metal, wood -> harddirt, rock -> rock.
* **Objects.** SMF models are drawn (textures shelf-packed into 1024 pages when their UVs stay in 0..1, own texture
  otherwise; alpha textures -> cutout). Collision near the AI line and the gates (40 m): CCollisionBox and CCollide
  type 0 -> oriented boxes (at least 0.4 m thick), CCollide type 1 -> convex hull of the model (the models as land
  polygons with overhangs inflated the tree to 2.3-2.7 million planes; retail courses have 100k-190k). Proxies are
  grounded (underside 0.5 m below the terrain, fully buried ones dropped), hulls at most 60 faces, intersecting hulls
  (face-normal separating-axis test) merged, and a solid that reaches into the AI line sweep (+-1.5 m, 0.3..2.4 m) is
  dropped; build_track.py also removes any solid the Course Studio route sweep still reports and builds again.
* **Object BSP** (`object_bsp.py`, wraps Course Studio at build time, no Course Studio file changed): Course Studio's
  `build_solid_bsp` axis-splits cells over 64 polygons and gives a polygon-free sub-cell the axis side state (back =
  solid) - correct for terrain, wrong for separate objects (empty space between rocks became solid, thousands of
  phantom samples and a blocked AI line); and `collision_polygons` drops proxy faces that lie under the terrain, which
  left grounded convex solids open. The wrapper groups object polygons by their source solid (recorded in
  `project.extras["evo2_solids"]`), separates the solids by kd planes between them and builds every solid from its
  complete hull. With it Deadman's Gulch (305 solids) validates with zero phantoms and a free AI line.
* **Water.** LVL water height -> flat ROLE_WATER over cells below it (Evo `waterx00` texture, LVL alpha).
* **Environment.** A retail RaceTest scene supplies sky, physics, cameras and HUD (keyword table in `to_course.py`).

## Results (batch-02, 2026-11-14)

All 30 Evo 2 races with checkpoints (race type 2 and the Pikes Peak hill climb) convert, build and pass the Course
Studio validation (collision probes, AI line sweep, checkpoints, start/finish). Mission maps (Alaska, El Norte, Skull
Island, The River, Washington, Obstacle Park: type 6, no gates) are not races and are skipped. Build time 25 s - 5 min
per race (6 in parallel). The pack (`course_pack.py`, 30 races, 1.3 GB) is installed in the test host
`master-rallye-re-base/.research-output/hosts/host-evo-tracks-01` (copy of host-evo-brake-01); smoke start:
`INSTALLED operations=350 ... RESOURCE_OVERLAY files=1045`, `SDK_BINDING_PROFILE_MATCH`, `BOOT_B_READY`; gameplay is
an owner test.

| Race | SIT | Layout | AI line km | Gates | Collision solids | DX MB | Water |
|---|---|---|---:|---:|---:|---:|---|
| Arctic Wasteland | SHTARTC | circuit | 2.1 | 6 | 40 | 9.4 | yes |
| Arizona | ZONA | circuit | 2.1 | 5 | 65 | 9.4 |  |
| Autumn Leaves | AUTUMN | circuit | 1.9 | 8 | 153 | 13.5 | yes |
| Baja Beach | BAJBEACH | circuit | 5.1 | 16 | 259 | 28.3 | yes |
| Bayou Flats | SHTSWAM | circuit | 1.1 | 4 | 29 | 5.4 | yes |
| Black Gold | OILFLD | circuit | 1.6 | 7 | 58 | 9.3 | yes |
| Castle Rock | CASTLE | circuit | 2.3 | 6 | 73 | 15.4 | yes |
| Construction Junction | CON2 | circuit | 2.7 | 8 | 106 | 9.5 | yes |
| Costa Rica Rally | COSTRICA | circuit | 5.0 | 20 | 142 | 20.2 | yes |
| Crazy 2001 | CZ2000 | circuit | 1.7 | 6 | 129 | 7.3 | yes |
| Deadman's Gulch | DVALLEY | circuit | 7.1 | 16 | 305 | 27.0 |  |
| Desert Run | DESERT | circuit | 1.4 | 5 | 129 | 8.6 | yes |
| Egypt | EGYPT | circuit | 3.7 | 7 | 131 | 15.5 | yes |
| Farm Road 109 | FM109 | circuit | 1.3 | 3 | 126 | 5.9 | yes |
| Final Destination | DEVIL | circuit | 2.0 | 7 | 108 | 8.4 |  |
| Laguna del Sol | SHTBAJA | circuit | 1.2 | 7 | 79 | 12.5 | yes |
| Mediterranean | MEDI | circuit | 1.7 | 6 | 110 | 6.9 |  |
| Motocross | MCROSS | circuit | 3.3 | 11 | 228 | 9.4 |  |
| Pikes Peak | PEAK | point-to-point | 3.8 | 16 | 304 | 14.3 | yes |
| Quarry Lake | QUARRY | circuit | 2.4 | 9 | 143 | 11.5 | yes |
| Restricted Area | SHRTAIR | circuit | 1.6 | 7 | 106 | 6.9 |  |
| Salvage Wasteland | JYARD | circuit | 1.7 | 5 | 364 | 9.4 | yes |
| Silverton Pass | ASPEN | circuit | 2.2 | 8 | 67 | 7.4 | yes |
| Thailand Rally | THAI | circuit | 2.6 | 7 | 90 | 10.6 | yes |
| Tibet Cliffside | TIBET | circuit | 3.2 | 10 | 242 | 11.3 |  |
| Treasure Bay | ISLAND2 | circuit | 3.6 | 10 | 29 | 18.7 | yes |
| Tri Baja 250 | TRIBAJA | circuit | 7.6 | 10 | 254 | 29.7 |  |
| Truck Stop 101 | THEHILL | circuit | 3.4 | 9 | 68 | 11.4 |  |
| Vulture Canyon | VULTURE | circuit | 3.0 | 8 | 65 | 9.9 | yes |
| Yukon | YUKON | circuit | 4.0 | 13 | 169 | 20.4 | yes |

## Native layer (tools/course_layer.py)

COURSE-CAP2 `append_native` (owner-tested StudioFranceEdit) is applied to the Vehicle Manager roster image (the dinput8
VehicleRoster module installs it), plus a ninth Quick Race mode:

| Site | Change |
|---|---|
| 0x458D0E / 0x458E28 / 0x6867AB / 0x459FD7 / 0x45A3E0 | race registry count, lifetime and the new records (CAP2) |
| 0x47F2B0 / 0x47F320 | forward / reverse menu maps over nine groups (count[8] written at +0x74) |
| 0x47ED04 / 0x47ED53 | position bound and screenshot pairs (CAP2) |
| callers of 0x4B0000 / 0x4AFF80 | best times of new races under `Progress/BestTimes/CourseRegistryV1/<key>`; a missing key reads as 86400 s |
| 3 callers of 0x47ED10 | details wrapper: race title, `Frontend/RaceSelect/Logo` = category logo frame, `ModeRightArrow` = mode < 8 |
| 0x47EA6B / 0x47EA9D / 0x47EAF6 | admission: new races are offline single-player Quick Race only (CAP2) |
| 0x45B1FA / 0x45B22C | explicit stage lists for retail cups / Invitation (CAP2) |
| 0x47E206 | RaceSelect object 0x74 -> 0x78 (position[8] = +0x34, a retail gap; count[8] = +0x74) |
| 0x47E605 | mode list: append the category label when the eight retail modes are present; +0x50 = appended |
| 0x53BA99 | model cache budget 32 -> 96 MB |

The category is listed only when all eight retail modes are open (the mode index is the list position), like the extra
Vehicle Select classes. Race Select art: two frames per race appended to `RaceSelect/screenshotsheet`, one category
banner appended to `RaceSelect/logos` (256x64), all in the roster overlay.

## Rally Trophy and Rally Championship Xtreme (assessment)

* **Rally Championship Xtreme**: 24 stages (`Data/Levels/<country><n>.rcx`, Kenya, Arctic, Manx, Scottish, USA, Welsh)
  in the RCX v4 container that `source-formats/rcx/rcx_extract.py` already decodes (Astra pilot). A level holds
  `<stage>.map` (about 9 MB, a binary chunk tree with matrices and bounds), `config.cfg` (TCFG: ENVO, MESH instances of
  `<stage>\<n>\<n>.msh` with matrices, INSU records), skybox/environment MSH and about 160 TEX textures (TEX already
  decodes). Pace notes are separate (`Data/Pacenotes/*.pn`). Next: decode the `.map` chunk tree (likely QTO-like vertex
  streams, as in the car QTO v7.2) and the route/checkpoint data; then the same Course Studio path as Evo 2 applies
  (closed corridor stages, not open terrain).
* **Rally Trophy**: 5 tracks (`Data/Tracks/track1..5/{data,models,textures}.bzf`). BZF = Bugbear archive, signature
  `bbzf 01 20 06 06`, payload compressed/obfuscated; no existing decoder. Next: recover the BZF reader from
  RallyTrophy.exe (PE x86, REA/Ghidra), then models/textures and `data.bzf` (route, checkpoints).
* Both are classic closed rally stages: the course side (corridor terrain, limits, checkpoints, AI line, menu category)
  is the same as for Evo 2 once their geometry and route are decoded.
