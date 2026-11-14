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
* `LEVELS/*.LVL`: heightmap / colour / texture-list names, water height and RGBA, detail texture, light vector.
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
  The start/finish gate of the lap is dropped; every other gate is a native checkpoint (`gaRaceSplitTimeAI`, radius =
  half the gate width, 18..40 m) with extra time for the next leg at about 40 km/h plus 25 s.
* **Surfaces.** Evo class -> MR Surface.xml: cement -> tarmac, dirt -> harddirt, mud -> mud, sand -> gravel, grass ->
  grass, gravel -> gravel, ice -> harddirt, snow -> gravel, metal -> metal, wood -> harddirt, rock -> rock.
* **Objects.** SMF models are drawn (textures shelf-packed into 1024 pages when their UVs stay in 0..1, own texture
  otherwise; alpha textures -> cutout). Collision: CCollisionBox and CCollide type 0 -> oriented boxes; CCollide
  type 1 -> convex hull of the model. Every proxy is grounded (underside 0.5 m below the terrain; fully buried ones
  dropped): proxies reaching deep under the terrain produced phantom solids in the BSP union, and the models themselves
  as land polygons with overhangs inflated the tree to 2.3-2.7 million planes (retail courses: 100k-190k).
* **Water.** LVL water height -> flat ROLE_WATER over cells below it (Evo `waterx00` texture, LVL alpha).
* **Environment.** A retail RaceTest scene supplies sky, physics, cameras and HUD (keyword table in `to_course.py`).

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
