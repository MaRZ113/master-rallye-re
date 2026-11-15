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
  their own Evo tile (shadow tile when present) in at most two 1024x1024 atlas pages (2 px gutter; the tile size is the
  largest of 64/48/40/32/24 px that fits the corridor's distinct tiles, Pikes Peak: 977 tiles -> 40 px); the remaining
  map is drawn only, in 2x2-cell blocks with one 512x512 overview texture and skirts where blocks meet single cells.
* **UV origin.** Course Studio UVs are bottom-origin (FEED rows are stored bottom-up and uploaded as-is: v = 0 is the
  last PNG row). Evo UVs and the atlas rectangles are top-origin, so v is flipped once per mesh at the end of
  `build_project`. batch-02 had no flip: in the game every texture was upside down and atlas lookups landed in the
  mirrored page region (black gate towers, wrong terrain tiles), while the Blender previews flipped v themselves and
  looked right. The previews now export the Course Studio UVs unchanged.
* **Texture budget.** MR creates course textures as A8R8G8B8 with a full mip chain in the managed pool and keeps them
  in the model cache with the course DX, the collision pools and every car. batch-02 Pikes Peak needed ~53 MB of
  textures (ten 1024 pages); in the race the cache evicted and re-created ~125 textures per frame
  (`CreateTexture` from 0x5589D0, renderer session log: 38,000 creations in six seconds, a Retail race: none) and the
  game crawled. Builds now fail above 24 MB (`TEXTURE_BUDGET_BYTES`); objects use at most 128 px per texture (one
  shelf page on Pikes Peak). Pikes Peak: 17.3 MB.
* **Draw records** (`render_batches.py`, wraps the Course Studio DX builder at build time). Course Studio splits a
  material only at 65,536 local vertices; Retail courses have ~1,000 records of at most ~2,000 vertices / ~4,700 indices.
  batch-02 records reached 39,536 vertices / 85,752 indices and rendered scrambled in the game (object parts and
  checkpoint banners scattered over the map) while Blender showed the same project correctly. Records are now cut at
  2,000 vertices / 4,800 indices (Pikes Peak: 19 -> 73 records).
* **Limits** (`safe_limits`, manual lists). gaLimitsAI picks the nearest marker of each list separately (3-D) and
  tests the car against the region between them. The first builds used Course Studio "auto" offsets of 90/140 m: on the
  inside of tight Evo turns those lines crossed the AI line and lay next to other legs, the nearest "left" marker could
  be on the right, and cars were reset while driving on the road (owner test 2). Now Retail-sized targets (inner 45 m,
  outer 75 m; Retail medians 29/48 m), reduced per station until the offset point is still nearest (3-D) to its own
  part of the route and on its own side, smoothed, outer >= inner + 10 m. Level or near-level crossings of the route
  with itself stay narrow (down to 12 m outer) over about 30 m.
* **Ground tile orientation.** An Evo ground tile's top row faces +Z (cell j+1): an edge-continuity score over the
  8 orientations picks "flip v" on all six tested maps (Pikes Peak 9.96 vs 13.65 as mapped before). The first builds
  mapped the top to -Z: roads became saw-tooth stripes (owner test 2). The overview texture follows the same rule.
* **Checkpoint boards.** The Course Studio boards (four native checkpoint boards per gate) are off: the Evo gate models
  are the visible gate, and Studio places the boards at the gate centre height (under the slope) and turned 90 deg.
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
* **Bridges and decks.** Evo bridges are visual-only models (Autumn Leaves: AUTCB covered bridge, AUTOB overpass) with
  CCollisionBox / CCollide type-0 boxes as their deck, walls and rails. The first builds grounded every box down to the
  terrain: a deck became a block under the bridge, the route sweep removed it, and cars fell through the bridges. Now:
  boxes whose underside is over 1 m above the terrain float as authored (an overpass leaves the road under it open);
  route heights come from `settle_route`, a least-total-climb choice per route point between the terrain and every
  elevated box or drivable-model top (a bridge keeps the road level over a valley; an overpass of another leg would be
  a jump of metres). Only the surfaces the route settles on are decks: boxes standing on them (rails, walls) get their
  floor raised onto the deck so they never merge with it, and a drivable model used as a deck becomes 0.8 m slabs of
  6 m (`deck_slabs`) instead of one hull that would fill the space under its arch. Most elevated drivable models are
  cliffs, rocks and huts and keep their grounded hull. Before this the AI line, the gates and the finish trigger of a
  route over a bridge sat on the river bed under it (the finish was never crossed; bots drove into the water).
* **Decks through the Course Studio checks.** The Course Studio route checks measure "above the ground" from
  ROLE_TERRAIN only, so a route over a bridge was swept from the river bed, the deck was reported as a wall and
  `build_track` removed it again (owner test 4: still no bridge collision). `object_bsp.install` now adds the used
  deck tops to the probes' height field (`terrain_triangles` for validation only; the BSP and land records are
  unchanged), which also makes the hole probes check the decks, and reports route-sweep hits at 3.4 m and more above
  the ground (the 3.5 m chase-camera sample) as clear: Evo underpasses are lower than that and the overpass is the
  deck of the other leg. Used decks never merge; a solid that reaches into one from at most 1.5 m below its top (end
  rails, walls on the deck edge, abutment rocks) gets its floor raised onto it (a rail touching the covered bridge's
  deck by 3 cm merged deck, rail and walls into one hull without the deck). Autumn Leaves: all four decks solid in the
  built BSP, the road under the overpass open.
* **Deck intersections and fallback.** A solid that really intersects a used deck (face-normal separating-axis test)
  is lifted onto it when it starts at most 1.5 m under its top, otherwise capped 5 cm under its underside (piers,
  rocks): Course Studio's exact BSP needs disjoint solids (Treasure Bay's 137 m bridge was empty with a pier through
  it). Deck solids are never dropped as route obstacles (`extras.evo2_deck_solids`, honoured by `drop_solids_at`).
  A race that still fails the Course Studio checks with decks (deck-end steps of ~0.5 m on the approach, objects
  beside the deck) is rebuilt without them (`bridges=False`, the previous behaviour: elevated boxes float, the route
  follows the terrain); `extras.evo2.bridges` records which build shipped. batch-07: decks on Autumn Leaves,
  Treasure Bay, Quarry Lake, Mediterranean, Black Gold, Bayou Flats; fallback on Construction Junction, Castle Rock,
  Thailand Rally, Tibet Cliffside, Vulture Canyon, Arizona (next: ramps at deck ends).
* **Finish.** Every Retail course is a loop with the finish 38-135 m from the start area, so circuits now end
  `FINISH_GAP_M` = 40 m before the start (was 150 m: the last 110 m of the lap had no RaceLine, bots left the road
  there and cars were reset beyond its end). Autumn Leaves: route 2060 m for the 2050 m Evo lap.
* **Solid merging.** Intersecting proxies are merged into the hull of their union unless that hull would close the
  AI line while the two alone do not (a covered bridge's wall and an entrance rail): then the smaller one is dropped.
* **Tyre tracks.** Surface.xml names `misc/tracks/<surface>` for every surface, but Retail ships only grass, gravel,
  harddirt, mud, tarmac and water. On rock and metal ground the game drew the missing-texture checker as tyre marks.
  The pack adds rock (gravel), metal and rubber (tarmac) and hay (grass) to `DataGx/Misc/Tracks` in the overlay.
* **Water.** LVL water height -> flat ROLE_WATER over cells below it (Evo `waterx00` texture, LVL alpha).
* **Environment.** A retail RaceTest scene supplies sky, physics, cameras and HUD (keyword table in `to_course.py`).

## Results (batch-02 2026-11-14; batch-03 2026-11-15 rebuilt all 30 with the UV, texture-budget and draw-record fixes, pack 799 MB)

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
| 0x47E605 | mode list: append the category label when the eight retail modes are present; +0x50 = appended. The object is read from the local `[esp+14h]`: EBX is not the object here (BL is reused as a bool at 0x47E51F/0x47E5A4). The first version wrote through EBX: heap corruption next to the object and an uninitialised position[8] (the "invalid race/menu/stage index" stop on the first scroll into the category) |
| 0x53BA99 | model cache budget 32 -> 96 MB |

The category is listed only when all eight retail modes are open (the mode index is the list position), like the extra
Vehicle Select classes. Race Select art: two frames per race appended to `RaceSelect/screenshotsheet`, one category
banner appended to `RaceSelect/logos` (256x64), all in the roster overlay. Every Retail logos frame is opaque art in the
left 196x64 of the 256x64 frame (transparent beyond, which the card does not show); the default category banner follows
that layout (the first one filled 256 px and was cut on the right).

Race buttons of the category row: the Retail row is one `RaceSelect.xml` egg per race (Masters, cups, challenges,
Invitation: `gaFrontendXYButtonAI`, `Y ID` = mode, `X ID` = position, `Button<X>XPos` published by 0x47ECB0 for every
position of the mode, image = a `frontend
aceselectlagsheet` frame). The Vehicle Manager appends one flagsheet
frame per course race (the race screenshot over the Invitation 1 icon's bottom band, its number box repainted) and
clones the Invitation 1 egg per race with `Y ID` 8. Without them the category row was empty.

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
