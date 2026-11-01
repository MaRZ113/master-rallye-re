# COLLISION-DEBUG1: course collision overlay in the render proxy

Opt-in `CollisionDebug=1` in PS2Port.ini (DIAGNOSTIC). The default 0 is Stock: nothing is loaded or drawn and no other
feature changes. Base: the COURSE-ALIVE2 build (bb95fda, the newest renderer build) plus c5d5a80 (Observatory only).

In a race the proxy draws the collision surface of the course over the scene. A hotkey (`CollisionDebugKey`, default
**F11**) cycles the overlay; **Shift+F11** goes back. A legend (top centre, over the HUD; see round 2) shows the mode, the colours with
the share of the visible triangles, the source (RETAIL asset or LOOSE DX) and the triangle count.

| # | Mode | What it shows |
|---|---|---|
| 0 | OFF | nothing |
| 1 | SURFACE | translucent fill coloured by `$surfacetype` |
| 2 | WIRE | the collision triangle edges, coloured by surface, hidden behind closer geometry |
| 3 | X-RAY | the same edges through everything (depth test ALWAYS) |
| 4 | SLOPE | steepness of the collision plane: 0-20 deg green, 20-35 yellow, 35-60 orange, 60-90 red (walls) |
| 5 | FACING | which side faces the camera: cyan = front (the solid, drivable side), red = back. One-sided walls and upside-down faces show red from the side you would pass through |
| 6 | SOLID | opaque collision with a fixed top light and dark edges, depth written: where the render geometry has no collision underneath, the scene shows through (holes) |

Surface colours: TARMAC grey-blue, GRAVEL orange, HARDDIRT brown, GRASS green, MUD purple, WATER blue,
OTHER (a named type not in this list) yellow, NO TYPE (materials without `$surfacetype`, e.g. roof, walls, waterfall
objects) magenta.

## What the collision data is (new evidence)

R5T-F.2.1 delimited the course DX tag1400 section (40-byte header, a `scalar`-metre XZ cell grid, a string table and
56-byte records) without assigning meanings. COLLISION-DEBUG1 checked every record of the 36 retail courses
(`tools/prepare_collision_debug.py`, `corpus.json`):

- record = triangle `v0,v1,v2` (9 floats) + string index + plane `n,d`; for 967,716 of 967,735 records `|n| = 1`,
  `n.v + d = 0` for all three vertices and `n` has the direction of `cross(v1-v0, v2-v0)` (0 exceptions);
- the other 19 records (Spain1, SpainM, SpainS1, SpainS1Flip, SpainW, SpainWFlip: 3 each; Turkey3: 1) are degenerate
  triangles (collinear or repeated vertices) with an all-NaN plane; they are not drawn;
- strings = the course materials: `$surfacetype(gravel|grass|harddirt|tarmac|mud|water)` plus shader tags; objects
  without a surface type (`roof`, `walls`, `waterfall`) also occur;
- cells: `dimension_0 x dimension_1` cells of `scalar` (20 m in retail) over `vector_a..vector_b`, each a list of record
  indices (every index < record count);
- ground planes point down (-Y): the drivable side is `-n` (FACING mode).

So tag1400 is the course's triangle collision surface with surface types, with a 20 m spatial grid. The physical
runtime consumer (wheel/surface queries) is **not traced** here; the overlay shows the data the course file gives to
the game. The tag100 plane tree, which R5T-F.2.1 proved carries the `COLLIDE_finishline03` collider, holds planes
without polygons and is **not drawn** (finish gate posts and similar compiled colliders are therefore missing).

## Course source at runtime

1. Landscape of the race (certificate course id, e.g. `RaceTest/France1`): a loose `DataScene/<id>.xml` wins (the
   first `course\<dir>\<name>` in it), else the asset table (from the retail race XML, same rule).
2. A loose `DataGx/Course/<dir>/<name>.dx` (converted PS2 courses, new courses) is parsed in place: every offset with
   u32 1339 followed 44 bytes later by u32 1400 is a candidate and **exactly one** must pass the full tag1400
   validation (all counts in range, every cell index < records, every string index valid, every record plane-consistent
   or degenerate, u32 1500 right after the records). Retail Turkey_s2 has one false candidate inside its tag100 tree; it
   fails the header checks.
3. Otherwise the retail asset `CourseCollision.mrcoll` (Data.sma is not read by the proxy).

## Verification

| Check | Result |
|---|---|
| C++ raw-byte search == loader-guided Python parse (render prefix -> tag100 -> tag1339 -> tag1400), digest of all triangles, planes, material indices and names | 36/36 retail course DX |
| C++ asset decode == Python parse | 37/37 races |
| Loose converted courses in `D:\Game\Master Rallye Pristine` (France1, France_M, Italy_W2, Spain_S2, Turkey2, Turkey3) | 6/6 parse, one candidate each |
| `collision_debug_tests` (synthetic DX with a false candidate, ambiguity, broken plane, truncation, asset layout, modes, geometry, legend font) | pass |
| `course_object_transaction_tests` (new `z_func`: ALWAYS applied/restored, other values rejected) | pass |
| In game | **PENDING_USER** |

Asset: `CourseCollision.mrcoll`, 35,146,786 bytes, SHA-256
`5e9426549fa10fd93791cfe4b2813aa27a8be54785a192930466e85520bebbdc` (pinned in `collision_debug_pilot.hpp`; a
different file is ignored and only loose courses are drawn). Regenerate with:

```
python ps2-research/pc-port/tools/prepare_collision_debug.py --verify <build>/Release/collision_debug_tests.exe --loose-root "D:\Game\Master Rallye Pristine"
```

## Render integration

| Part | File |
|---|---|
| Portable core: tag1400 parse, asset, surfaces, modes, overlay geometry, legend font | `renderer/collision_debug.hpp` |
| Pilot: INI, asset, course resolution, hotkey, white texture, reset | `renderer/collision_debug_pilot.hpp/.cpp` |
| Native seam: gameplay VIEW/PROJECTION of the frame, draw at the pre-UI boundary, repair | `renderer/collision_debug_native_integration.hpp` |
| Asset generator and corpus verifier | `tools/prepare_collision_debug.py` |
| Contracts | `tests/collision_debug_tests.cpp` |

- Drawn at the typed pre-UI boundary after the course, water, spline objects, birds and the late reflection capture
  (so the overlay never enters the car reflection), before the HUD. Single camera races only.
- Fixed `CourseObjectTransaction` (captured and restored around each pass): identity WORLD, the verified gameplay
  VIEW/PROJECTION, a 1x1 white texture x vertex colour, source-alpha blend, no cull, no lighting, no fog. The shared
  material state gained `z_func` (default LESSEQUAL, so every other effect is unchanged; ALWAYS for X-RAY and the legend).
- Depth fighting with coplanar render ground: overlay vertices are moved toward the camera by
  `CollisionDebugDepthPull` (default 0.003 = 0.3 % of their distance; edges 1.5x).
- Only triangles within `CollisionDebugRange` (default 500 m) of the camera are built, once per frame.
- Patch 0001 gained 9 lines (include, observe_transform, before_ui, repair in `visual_wrappers.cpp`; config/initialise,
  reset, shutdown in `wrappers.cpp`; the pilot source and the test in `CMakeLists.txt`); the baseline lock holds its
  new SHA-256.

Session log records: `collision_debug_config`, `collision_debug_course` (status, source, DX path and SHA-256,
triangles, grid, materials), `collision_debug_mode` (every switch), `collision_debug_gate` (first rejection),
`collision_debug_draw` (first frame of each mode).

## Round 2: joined courses, modified EXEs, legend over the HUD

User game test of round 1: works on the retail EXE. Round 2 requests: work with the invitation concept
(`master-rallye-re-course`, joined course sections) and with test/mod EXEs (`MRallye_cook_spain_extream.exe` runs the
joined `RaceTest/InvSpainGX`), and move the legend away from the race-position HUD.

**Why it was off on mods.** The baseline sets `target = (EXE SHA-256 == retail)`; for any other EXE the race observer
(race certificate, course id) is never installed and the PS2 extension is Stock (`build":"UNKNOWN_BUILD"`, no
`collision_debug_config`). The owner's mods are in-place edits: same size (3,121,214), image base and section table
(only `.rdata`/`.text` VirtualSize grew), 3..11 of 763 changed 4 KiB pages (`tools/prepare_retail_layout.py --check`):

| EXE | changed pages |
|---|---|
| MRallye_invitation_p0 | 3 (0x0, 0x59000, 0x2ad000) |
| MRallye_cook_spain | 5 |
| MRallye_cook_spain_extream | 6 (+0x5b000) |
| MRallye_invitation5 / _mech | 11 |
| MRallye_patched (relinked, other layout) | rejected |

**RetailDerivativeBuilds=1** (PS2Port.ini, default 0): the proxy compares the running EXE with a pinned page table of
the retail EXE (`renderer/retail_layout_table.hpp`, FNV-1a 64 per page, generated by `tools/prepare_retail_layout.py`)
and accepts same size + image base + section table + at most 64 changed pages as `RETAIL_DERIVATIVE`. The session log
gets `"build":"RETAIL_DERIVATIVE"` and a `retail_derivative` record listing the changed pages. The baseline then treats
it as the retail target: every hook installer still checks its own bytes and fails closed, and the compatibility
inspector keeps its fingerprint path (only the exact retail EXE takes the known-build path). The PS2 extension runs
**only CollisionDebug** with every race mode certified (Invitation/Challenge); `RetailDerivativeEffects=1` would
enable all PS2 features as well (not verified on mods).

**Joined courses.** A joined course race XML places several landscapes, each an entity with
`en3d Model Name = course\<dir>\<name>` and an `en3d Matrix` (row vectors, Row3 = translation): InvSpain has 4,
InvGrandFinal 4 (three rotated and moved), InvSpainGX 1. The overlay loads every landscape (loose DX or retail asset),
places it with its matrix (planes rotated, `d` recomputed), merges them and keeps equal (path, matrix) pairs once. The
legend source reads e.g. `LOOSE DX 4/4 PARTS`; the session record `collision_debug_course` lists each landscape with
its status, source, DX SHA-256 and triangle count. That the game moves the tag1400 surface with the entity matrix is an
assumption (it is how the render model is placed); all owner joined courses except InvGrandFinal use the identity.

**Cooked DX without tag1500.** `invspaingx.dx` (Demo cooker output) ends the file with the last tag1400 record; the
parser now accepts the end of file in place of tag1500 (44,143 triangles, 3 degenerate). Retail stays 36/36 equal to
the loader-guided parse, all 21 loose course DX in `D:\Game\Master Rallye\DataGx\Course\inv*` parse.

**Legend.** Built at the pre-UI boundary, drawn by the following Present with the HUD layer (`PS2HudLayer::draw_strips`,
own state capture/restore, outside the scene) over the finished frame, HUD included.
`CollisionDebugLegendPosition=TOPCENTER` (default: two compact lines, the colours side by side), `TOPLEFT`, `TOPRIGHT`,
`BOTTOMCENTER`.


## Round 3: object collision (tag100 BSP), Data.sma, car position, free camera and HUD hide in every race

User game test of round 2 (MRallye_cook_spain_extream.exe, RaceTest/InvSpainGX): the overlay works, but a collider at the
end of a bridge and the collision of objects (banners and others) are not shown in any mode. Also requested: the player
car position in the overlay, and HUD hide / free camera on the invitation build.

**tag100 is the course BSP (new RE, retail EXE).** The loader 0x57e2d0 logs "BSP memory %d". Node classes: plane node
(vtable 0x69cd10, 36 bytes: plane +8..+0x14, code +0x18, links +0x1c/+0x20) and two leaf classes (0x69cc68 in the
first link, value -1; 0x69ccbc in the second, value 1). The point query 0x61ff90: `s = n.p + d; s < 1e-4 (0x6e7b54)
-> link +0x1c (the parser's "child") else link +0x20 (the parser's "next sibling")`. The serializer 0x57e3a0 recurses
into the child and iterates the next link, so the "sibling chain" of R5T-F.2 is really the second child of a binary
BSP: France1 has 175,896 plane nodes and 175,897 leaves (= planes + 1). Leaf -1 = solid, 1 = empty, checked on
COLLIDE_finishline03 (France1): post centre -1, 2 m beside it and 3 m above it 1, high air 1, under the terrain -1.
Planes with code 0xffffffff are pure splitters; the nearest-face query 0x61fff0 only reports code >= 0.

**Drawing it.** The course box (tag1339 min/max) is clipped down the tree (child side `s <= 0`, next side `s >= 0`,
a cap polygon per split); every solid leaf cell contributes its faces on real planes (code >= 0) on its inside, i.e.
the outward collision faces. France1: 74,198 solid cells, 260,082 faces; on the finish post the eight vertical faces of
the octagonal post come out. Faces whose code has a face coplanar with any tag1400 triangle are ground (shown by
tag1400); the rest are objects. Ground and object codes are disjoint (France1 24,316 / 16,559; 0 shared), so the split
is clean. Object faces: France1 92,758 polygons, InvSpainGX 36,191. A Python prototype gave the same counts within the
clipping tolerance (74,164 cells / 260,670 faces). Objects are white `OBJECT` in every mode; mode 7 `OBJECTS` shows
only them (opaque, shaded, dark polygon edges; fan diagonals hidden). The BSP build takes 1.4..2 s per landscape, so
courses load on a background thread (the overlay appears when it is ready, logged with `load_ms`).

**Data.sma instead of the asset.** Data.sma is a ZIP of local headers (no usable central directory). The proxy now
indexes the local headers and inflates members itself (`renderer/sma_archive.hpp`, stored/deflate, CRC-32 checked):
7,595/7,595 files equal to `Data.sma_unpacked`, 0 mismatches. Retail courses (DX and race XML) are read from it, with
the BSP objects; `CourseCollision.mrcoll` is now an optional surface-only fallback and is not shipped.

**Car position.** The legend's third line (yellow): `CAR X Y Z` of Broker `Car0` -> `gaVehicleOutputData` +0xec..+0xf4
(the reader the spline objects already use), plus `GROUND <surface> Y <height> (+<car above it>)`: the highest
tag1400 triangle under the car (BSP objects excluded), or `NO GROUND UNDER CAR`.

**Free camera and HUD hide.** The session log of the InvSpainGX race: `certificate_reason":"unsupported_race_or_player_configuration"`
(baseline `check_race_context`: only Race/Type 1/2, one player, FinishingType 0), `freecam_admission_reason":"camera_owner_invalid"`,
HUD hide `committed_scene_not_race_hud`. The baseline accepts only single races without opponents; the build is not the
cause (retail races with opponents behave the same). `BaselineAllRaceModes=1` (PS2Port.ini; default 1 on a
RETAIL_DERIVATIVE EXE, 0 otherwise): patch 0001 turns `live_race_certificate` / `live_race_hud_context` in
`race_observer.cpp` into wrappers of their strict versions that forward to the PS2 normalising certifier
(`ps2_race_certificate`, `ps2_race_hud_context`, all race modes) while the option is on; the PS2 certifier and the
race snapshot read the strict versions (no recursion). The free camera, Clean View and HUD hide code is unchanged.


## Round 4: vehicle collision hulls and race markers

User test of round 3: object collision is well visible. Requested: vehicle collision bounds, and every race marker
(RaceLine, RaceLimits and the rest) on a separate key.

**Vehicle hulls (`CollisionDebugCars=1`, with every collision mode).** Participants come from the FLEET-ALL-CARS1
resolver (egg `Car<N>` -> en3d model `vehicles\<CarName>\car`, the race certificate of the PS2 certifier, so races
with opponents and every mode are covered). Each car's hull is the R4B tag101 representation B of
`DataGx/Vehicles/<CarName>/car.dx` (loose file first, else Data.sma): the closed convex hull, drawn as its face polygons
(primary vertex loops). Parser: the unique `u32 101` with a 1-vertex/0-triangle base block that parses fully up to a
tag102 or tag1339; equal to the R4B parse (offset and hull vertex count) on 27/27 valid retail tag101 resources,
forklift (non-finite, R4B outlier) rejected. Pose: Broker `Car<N>` -> `gaVehicleOutputData`, 4x4 block at +0xbc
(rows x, y, forward +0xdc, position +0xec; the forward and position fields are the ones the GPS and HUD feeds already
read). The 3x3 part is used only when orthonormal (within 2e-3); otherwise the hull follows the forward yaw with world
up and the legend shows `YAW`. **Unverified in game:** that +0xbc/+0xcc are the car's x/y axes and that the physics
origin equals the car.dx origin; the overlay itself shows any offset. Drawn with depth ALWAYS (through the body):
player car yellow, others orange. Session record `collision_debug_hulls` (participants, drawn, exact matrices, loaded
and failed hull files).

**Race markers (`CollisionDebugMarkersKey`, default F12: OFF -> ON -> X-RAY, Shift = back).** Every `<MarkerLists>`
list of the race XML that the course load already reads (loose or Data.sma): consecutive markers joined (StartArea and
FinishArea closed), a 1.5 m post at every marker and a 2 m tick along its "Marker Dir". Colours: RaceLine yellow,
L-INNER cyan, L-OUTER blue, R-INNER orange, R-OUTER red, StartArea green, FinishArea white, Cameras magenta (posts
only), other lists a stable hash colour. Range = max(200 m, 2 x CollisionDebugRange). The legend lists each marker list
with its marker count, also while the collision overlay is OFF; long legends wrap at 90% of the screen width.


## Round 5: vehicle collision on its own key, render-instance pose, wheel cylinders

User test of round 4 (screenshot, Simmbugghini): the hull is too high, and the car does not touch the wall where the
hull crosses it, so the drawn placement was wrong; wheel collision missing; the hull jittered. Round 4 placed the hull
with the gaVehicleOutputData block at +0xbc; its position (+0xec) is about 0.7 m above the ground (screenshot: car Y
29.23, ground 28.50), close to the hull centre height in car.dx (0.5..0.7 m), i.e. the physics position is the body
centre, not the car.dx origin, so the hull was lifted by that offset.

**Pose = the render instance world matrix (new RE).** The shared model emitter 0x576970 receives the instance
(en3d+0x74, the instance the FLEET-ALL-CARS1 chain already proves per participant) and calls
`0x561a40(instance+0x44, ...)`, which copies the 4x4 to the device cache and calls `IDirect3DDevice8::SetTransform`
(vtable +0x94) with state 0x100 = D3DTS_WORLD. So `instance+0x44` is exactly the world matrix the car body is drawn
with, and each wheel egg's instance holds its wheel's matrix. The overlay reads them at the pre-UI boundary of the same
frame (after the car draws): the hull sits on the drawn body without lag. tag101 and the render vertices share the
car.dx local space (docs/vehicle-bounds.md), and R4C/R4G runtime tests moved and widened wall contact through tag101.

**Wheels.** wheel.dx ends with tag102 `(0.4, 0.2)` right before tag1339 on 25/25 retail wheels; every wheel mesh is
thin along local X (+-0.147) with radius 0.39. Drawn as a cylinder of radius 0.4 and width 0.2 around local X (green).
The radius/width reading is an inference from the data.

**Own key.** `CollisionDebugCarsKey` (default F9; F8 is the free camera key): OFF -> ON (through the body) -> depth
tested; independent of the collision mode. The round 4 vehicle-output pose reader and its YAW fallback are removed.


## Round 6: vehicles of any resource root, effects after the opponents finish

User test of round 5: vehicle collision correct. Two issues: the new vehicles of the vehicles SDK candidate
(`master-rallye-re-vehicles/.research-output/vehicles/v-def3/delivery/workshop/builds/first/candidate`) get no hull,
and every proxy effect stops after all opponents finish.

**Any vehicle, any launcher.** The session log said `collision_debug_hulls ... "loaded":2,"failed":2`: the two new cars
(DefForester, DefRav4, ...) were not found. Their car.dx/wheel.dx parse with the same rules (7/7 car.dx tag101, 7/7
wheel.dx tag102 at the tail). The SDK launcher (`runtime_launcher/src/main.cpp`) starts the retail MRallye.exe with
`CreateProcessW(..., workingDirectory = <bundle>/resource-root)`; the game opens its relative `DataGx/...` paths there
(that folder has its own Data.sma and loose DataGx), while the proxy looked only next to its PS2Port.ini. Every game
file the overlay reads (race XML, course DX, car.dx, wheel.dx) now resolves like the game: the process working
directory first (loose file, then that folder's Data.sma), then the proxy folder (loose, Data.sma). The hull log adds
`missing_car_dx` and `game_roots`.

**Effects after the opponents finish (new finding).** The baseline certificate needs every participant RaceState in
{0, 2}; a finished car is 3. RACE-FINISH1's PS2 finished phase accepted 3 only when the local driver had finished as
well (`ps2_local_participant_not_finished`). In a race where every AI finishes first the states are e.g. [3,3,3,2]: the
certificate was refused and every effect that follows it (PS2 features, and with BaselineAllRaceModes the free
camera, Clean View and HUD hide; the collision overlay) went Stock until the next race. The finished phase now accepts
the local driver in 0/2/3 as long as every participant is in 0/2/3 (the startup state 1 stays refused); covered by
`ps2_race_certificate_contracts.hpp`. With BaselineAllRaceModes=0 the baseline free camera / HUD hide still follow the
strict baseline rule.

## Limits

- BSP faces are cell fragments (no polygon merge). Wheel collision (wheel.dx) is not drawn.
- Split-screen races and frames without a HUD draw (the pre-UI boundary is the first UI draw) show nothing.
- The hotkey is read only during race frames.
