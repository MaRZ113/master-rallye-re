# New course entries, Invitation and combined tracks (R5T-INV concept)

Status: **3-slot Invitation retarget CONFIRMED_BY_RUNTIME (P0); five-race patch, combined scenes and SFL synthesis NOT RUNTIME-TESTED.**
Retail EXE SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

This page answers: can a course be replaced or added as a *new* entry, how
does that interact with Invitation (whose courses are shared with other
championships), and can the Retail tracks be combined into full-country
courses and a five-race Invitation finale.

## 1. Race registry: how a race finds its course (CONFIRMED_BY_EXE)

`FUN_00458CD0` constructs the singleton at `[0x6F5ED4]` (`operator new(0xC00)`
at `0x45A3DF`). It holds two fixed arrays:

| Offset | Records | Size | Content |
|---|---:|---:|---|
| `+0x004` | 26 (`0x1A`) | `0x34` | vehicle registry (see R5V) |
| `+0x54C` | 39 (`0x27`) | `0x2C` | race registry, IDs 0..38; ends exactly at `0xC00` |

`FUN_004598D0` fills the race array: each record pushes a
`RaceTest/<name>` string and calls `FUN_0045A330(id, a, b, c, ...)`. The
RaceTest name is the only course link: `DataScene/RaceTest/<name>.xml` names
the landscape model (`en3d Model Name`, e.g. `course\france_s1\frances1`), its
`.hnt` lists dependencies, and `gaIContAIManager/AI DataSet Name` names the
`ICont/<name>.sfl` AI field.

| Race IDs | Owner | Courses |
|---|---|---|
| 0..9 | Master Rallye legs | France1, France2, Italy1..3, Spain1..2, Turkey1..3 |
| 10..24 | Rallye Cups (5 cups x 3) | ItalyS4 ... FranceS1 |
| 25..35 | Challenges 1..11 | ItalyS3, SpainM, TurkeyS1, SpainS2, ItalyM1, *Flip variants |
| **36..38** | **Invitation** | **FranceS1, Turkey3, ItalyM1** (string pointers shared with IDs 24, 9, 29) |

`FUN_0045B170` advances multi-race events; Invitation is case 5 with range
`0x24..0x26` (`mov edi, 26h` at `0x45B1F3`). The frontend shows Invitation
races through `RaceSelect.xml` eggs `Invitation1..3` and progress keys
`Won_Invitation1..3` / `BestTime_Invitation1..3`.

### Replacing Invitation courses without touching other championships

Because Invitation only *points at* shared strings, three `push imm32`
operands (`0x459F5E`, `0x459F8C`, `0x459FBA`) can point at new strings and give
Invitation its own scenes. `tools/patch_invitation_entries.py` does exactly
that on a **copy** of the pristine EXE (new strings in the zero tail of
`.rdata`, `.rdata` VirtualSize `0x1E432 -> 0x1F000`).

**P0: CONFIRMED_BY_RUNTIME (owner, 2026-10-27).** Stock scenes copied as loose
files `DataScene/RaceTest/InvFrance|InvTurkey|InvItaly.xml/.hnt` next to the
EXE (no `Data.sma` repack) replaced Invitation races 1..3, and the original
FranceS1/Turkey3/ItalyM1 entries elsewhere loaded as usual.

### Five Invitation races (implemented, NOT RUNTIME-TESTED)

`patch_invitation_entries.py --names A,B,C,D,E` adds Race IDs 39 and 40:

| Site | Change |
|---|---|
| `0x45A3E0` | registry allocation `0xC00 -> 0xC58` (records 39, 40 at `+0xC00`, `+0xC2C`) |
| `0x458D0F`, `0x458E29` | race array vector ctor/dtor count `0x27 -> 0x29` |
| `0x459FD7` -> cave `0x68E384` | after race 38, register IDs 39/40 exactly like `FUN_004598D0` (params `id, 0, stage 3/4, 2, 0, 0, 0, string, -1, -1`) |
| `0x45B1F4` | `FUN_0045B170` Invitation last race `0x26 -> 0x28` |
| `0x47F3B6` | `FUN_0047F320` race-to-mode map: Invitation `< 0x27 -> < 0x29` |
| `0x4AF5F0` -> cave `0x68EFC0` | `FUN_004AF4F0` Won key index `stage + 0x6A`: stages 4/5 clamp to index 109 `__IGNORE` (index 110 would be `BestTime_Master_Stage1`) |
| `0x45B477` -> cave `0x68EFD4` | `FUN_0045B3F0` BestTime index = race ID: 39/40 map to 40 `__NO_SAVE` (39 would be `BestTime_Master`) |
| `.text` header | VirtualSize `0x28D294 -> 0x28E000` |

The two caves avoid every range used by the vehicle-slot and R-AI patches
(`0x68E2A0..0x68E383`, `0x68E400..0x68EFBF`). Known gaps: the race select
screen still shows three flags; stages 4/5 keep no separate Won/BestTime
values; race-details screens read `BestTime_Master`/`__NO_SAVE` for IDs 39/40
(display only). Proper keys need relocated key tables (`0x6F65C8`, `0x6F6780`)
and their registration functions `FUN_004AE7A0`/`FUN_004AF0E0`.

Runtime packages:

* `tools/invitation_mech_pack.py` + `--names InvMech1..5`: stock scenes with
  FinishArea moved about 200 m after the start; checks stage advance 1..5.
* `tools/invitation_runtime_pack.py` + `--names InvFrance,InvItaly,InvSpain,InvTurkey,InvGrandFinal`:
  full-country scenes with several `landscape` eggs (one per used stage
  model, identity matrix) and a Grand Final whose 6 km country windows are
  placed by `en3d Matrix` and joined end-to-start. Neither several landscape
  eggs nor a non-identity landscape matrix occurs in any Retail scene.

## 2. Retail courses are corridors of four master maps (CONFIRMED_BY_CORPUS)

All stages of a country share one world frame. Overlapping corridors use
bit-identical DX vertex positions, and RaceLines share road:

| Country | Stages | Sum of stage triangles | Union (deduplicated) | Union / sum |
|---|---:|---:|---:|---:|
| France | 6 | 412,697 | 108,807 | 0.26 |
| Italy | 11 | 569,797 | 149,436 | 0.26 |
| Spain | 6 | 312,938 | 88,918 | 0.28 |
| Turkey | 7 | 378,291 | 128,838 | 0.34 |

(*Flip stages are the same roads driven backwards and are excluded.) The
largest single Retail stage has 75.7k render triangles; a full country map is
1.2–2.0x that. This makes "full France/Italy/Spain/Turkey" a recombination of
existing geometry, not a modelling job.

## 3. SFL is the AI heading field (HIGH_CONFIDENCE, corpus geometry)

`ICont/<name>.sfl`, owned by `gaIContAIManager`, decodes as:

* header `<fIIff>` = cell size (3.0 in all 36), width (X), height (Z), origin X,
  origin Z; the grid encloses the RaceLine X/Z bounds plus ~60 units;
* payload **column-major** `payload[x * height + z]`;
* byte = `round(256 * atan2(-dx, dz) / 2pi) mod 256`; far from the road it
  aims at the nearest RaceLine sample (median error 1.2 bytes), on the road it
  follows the local route direction.

`master_rallye.course_sfl_field.synthesize_heading_field` regenerates a field
from any RaceLine. Against all 37 Retail scene/SFL pairs the median wrapped
error is 1–8 bytes (1.4–11 degrees), best on point-to-point stages and worst on
closed circuits. Runtime AI behaviour with a synthesized field is untested.

## 4. Concept package (`tools/invitation_concept.py`)

Output in ignored `research-output/invitation_concept/`:

| Entry | Route (m) | Legs (stage, F/R) | Max join gap | Self-overlap | Corridor tris (r=300) |
|---|---:|---|---:|---:|---:|
| InvFrance | 17,724 | France2 F, FranceM R, France1 F, FranceS2 R, FranceW R | 0.05 | 0 | 108,508 |
| InvItaly | 16,658 | ItalyW1 F, ItalyM2 R, ItalyS3 F, Italy2 R, ItalyW2 F, ItalyS4 F, Italy3 R | 32.3 | 0 | 111,530 |
| InvSpain | 12,145 | SpainW F, Spain2 F, SpainM F, SpainS1 R | 0.0 | 0 | 75,590 |
| InvTurkey | 16,822 | TurkeyS2 F, TurkeyM R, Turkey1 F, TurkeyW R | 0.95 | 0 | 101,418 |
| InvGrandFinal | 25,798 | 6 km signature window per country + 3 liaison roads | authored | 0 | 174,073 |

Route rules (`course_atlas.stitch_routes`): legs join at the closest sample
pair without a turn sharper than 120 degrees, and a leg is clipped where it
would rejoin road already driven, because `gaRaceLineAI` progress uses the
nearest sample and the SFL is single-valued per cell. Retail stages are
5.6–9 km; the country routes are roughly two stages long.

Per entry the package contains: a stitched RaceLine (JSON + OBJ polylines
with every source RaceLine), a full union atlas and a 300 m corridor atlas as
OBJ/MTL grouped by texture (`--textures` decodes DXT to PNG), a synthesized
SFL, a generated RaceTest XML and an HNT. The generated scene keeps every
template component, rebuilds RaceLine/limits, re-anchors StartArea, Cars and
StartSplitTime to the new start and FinishArea to the new end, places split
eggs by route fraction, and transfers pace notes (direction-checked),
cameras and environment sounds from the stages the route actually uses.

InvGrandFinal places the four windows end-to-start in one world, each yawed to
continue the previous heading with at least 600 m clearance between 300 m
corridors, and inserts Hermite liaison polylines (600 m) where a border
transition (tunnel/bridge/forest cut) has to be authored in Blender. Its
scene has no pace notes or cameras yet.

OBJ coordinates are course/DX space; Blender's default OBJ axes (forward -Z,
up Y) yield the repository's `(X, -Z, Y)` convention, so atlases line up with
the existing course importer.

## 5. What is still missing for full Blender -> game course authoring

| Layer | Status | Needed |
|---|---|---|
| RaceTest XML (start/finish/splits) | runtime-confirmed G0 | — |
| RaceLine / limits Marker Pos | G1.1, Blender->runtime check pending | runtime check; topology-changing lists (new marker counts) |
| Marker Dir, Cameras, pace notes, sounds, water, birds, sky | read-only / unknown | semantics + authoring |
| SFL AI field | **decoded here**, synthesizer approximate | runtime AI test; corridor-band model fit |
| Render geometry (DX rev135) | read-only; vehicle topology writer exists | course draw/material writer or cooker path |
| Collision tag100 | tree carrier confirmed (F.2.1), parser read-only | writer or cooker path; `$bsp`/`COLLIDE_*` semantics |
| Surfaces (gravel/tarmac/grass) | unknown (`$grnd*`, `$landdb` labels) | locate in source/tag100 |
| Source GXM v7 + TXT | reader complete | **writer** (main blocker for the cooker route) |
| GXI textures | not decoded | reader/writer, or confirm the cooker accepts existing DXT |
| Demo 9.10 cooker | works; render output varies per run; BSP warnings | scale test on a 100k+ triangle map; cooked DX retail-load confirmed once (France1) |
| EXE entries | 3-slot retarget built (untested); 5-slot design above | P0 runtime test; 5-slot patch |
| Frontend | not started | race names/flags/loading text, Progress rows |

Recommended order: **E0** run the P0 package (patched EXE copy + stock scenes
renamed `InvFrance/InvTurkey/InvItaly`) to prove the entry mechanism; **E1**
GXM v7 + TXT writer from an atlas (start with a Retail corridor round-trip:
DX render -> GXM -> cook -> compare); **E2** cook InvSpain (smallest) in the
Demo 9.10 runtime and load it in Retail with the generated scene and SFL;
**E3** five-slot Invitation patch; **E4** Grand Final liaison geometry.

## 6. Branch issues found during this review

* Fixed: `course_route.py` now collects markers and curves in one pass per
  depsgraph update and records `mr_polyline_refresh_status`; the marker panel
  shows a stale polyline (for example duplicated helpers) as an error line.
* Fixed: `_format_float` expands the shortest round-trip decimal positionally
  (`1e-05 -> 0.00001`); Retail XML never uses exponents.
* Fixed: docs no longer describe SFL as semantically unknown.
* The owner restored Retail France1 in the live install (the probe DX/XML
  noted earlier is gone).
* Still open: `research/g1_1/runtime-handoff.md` Blender -> runtime check of the
  G1.1 RaceLine/limit writer.
* Retail data: `Turkey_s2_flip.hnt` references missing
  `course\turkey_s2_flip\pathesport-tga` (harmless so far).

## 7. Runtime results E1 / E1.1 (owner, 2026-10-27)

* `MRallye_invitation5.exe` crashed at the end of loading InvFrance (five
  landscape eggs): access violation in the land-database query
  `FUN_006068A0` (grid cell `x * H + z`, cell size `+0x4C`, origin
  `+0x58/+0x60`) on a corrupt grid object.
* Single-factor scenes as Invitation race 1 all loaded, AI drove:
  two different landscape eggs (diag1) and the same egg twice (diag2) work;
  the generated InvFrance scene with one landscape and a synthesized SFL
  (diag3) works; a synthesized SFL on stock FranceM (diag4) works.
* diag5 (landscape `en3d Matrix` +1000 X, all scene positions and the SFL
  origin moved with it): **collision moves with the matrix** and the car
  drives, but ground textures are missing. Working hypothesis: ground
  textures use projected/world-space texture coordinates that the landscape
  matrix does not move.
* Truncated RaceLine (15 samples) with splits and FinishArea at its end ends
  the race early: completion needs RaceLine progress, not FinishArea alone,
  and a RaceLine with a different marker count is accepted at runtime.
* Next bisection: 3/4/5/6 landscape eggs on stock FranceM (diag6..9) and the
  five-egg scene with the LARGE_ADDRESS_AWARE flag (`MRallye_diag8_laa.exe`).
* Bisection result: 3, 4, 5 and 6 landscape eggs (diag6..9) all crashed, also
  with LARGE_ADDRESS_AWARE, at varying sites (land-database query, render
  sort-list relink `FUN_00509750`): heap/table corruption, not address space.
  HNT texture totals: diag1 177 (loads), diag6 274 (crashes) suggest a fixed
  ~256-entry texture table. diag10 (FranceM x3, 99 textures) and diag11
  (TurkeyM + Turkey1, 254 textures) separate landscape count from textures.
* After race 1 every multi-race Invitation run fell into AttractMode: the
  second Loading screen's `<CD>:\SETUP.DLL` check (`0x464F69`). All EXEs from
  `patch_invitation_entries.py` now apply the R-AI1.1 redirect
  `68 84 1F 6B 00 -> E9 D8 FF FF FF` unless `--keep-cd-attract` is given.

### E1.2 results and fixes (2026-10-27)

* diag10 (FranceM landscape x3, 99 textures) and diag11 (TurkeyM + Turkey1,
  254 HNT textures) both load: the landscape count is not the limit; total
  textures between 254 and 274 are (likely a 256-entry table).
* Retail DX texture slots store bare names (`grass-tga`); the folder comes
  from the model path. `invitation_runtime_pack.py` now copies each country's
  stage DX files into one loose folder `DataGx/Course/inv<country>` with one
  shared DXT set (first stage wins on the few name collisions: 2D trees,
  sponsor banners). Referenced textures: France 124, Italy 96, Spain 76,
  Turkey 175. A four-country Grand Final needs 285..373 and is reduced to
  France + Italy + Spain (238); its first window keeps the identity matrix.
* Mech run reached race 4 and crashed after its results writing Won index 109
  (`__IGNORE` is not a usable key). The patch now skips the Won and BestTime
  writes of `FUN_0045B3F0` for stages 4/5 (hooks `0x45B433`, `0x45B477`,
  caves `0x68EFC0`/`0x68EFE0`); `0x4AF5F0` is no longer patched.

### E1.3 root cause: 32 MB model cache (2026-10-27)

`FUN_0053BA80` initialises the model cache budget to 32 MB
(`mov [edi+14h], 2000000h` at `0x53BA96`). `FUN_0053BE70` adds each loaded
model's size and, while the total exceeds the budget, frees the least
recently used models, including landscapes of the scene being loaded. The
land-database query then reads freed memory. This matches every result:
FranceM x3 (one cached model) and two models of ~26 MB loaded; three France
models (~44 MB) and the five-model country scenes crashed at varying sites
after a long load. The patch tool now sets the budget to 384 MB
(`--model-cache-mb`) and LARGE_ADDRESS_AWARE (`--no-laa` to skip). The
earlier texture-limit reading is withdrawn as the crash cause; the shared
per-country texture folders are kept because they cut texture memory.

Race 5 crashed on Start in `FUN_004B0000` (BestTime getter, index = race ID;
index 40 is the `__NO_SAVE` sentinel, not a string). A guard cave at
`0x68E3E4` maps indices above 39 to 38 before the original prologue.

### E1.4: first full run, limits and z-fighting (2026-10-27)

With the 384 MB model cache all five Invitation races load and finish
(owner). Two defects remained:

* **Repeated vehicle resets** at one spot. Generated limits were constant
  lateral offsets of the template stage; at a junction about 2.3 km into
  InvFrance (near `x=670, z=527`) LeftOuterLimit markers sat on the road
  (offsets -2..+6). `course_entry.transfer_limits` now rebuilds all four lists
  from the Retail stages the route drives: each route sample is owned by the
  nearest stage RaceLine running the same way (both stage orientations are
  candidates, Left/Right swap when reversed), markers must lie on their own
  side at least 8 units from the route, and holes over 150 units are filled by
  interpolated offsets that pass the same side test. No marker of the four
  country scenes now lies on or across the route (Retail scenes show 0..7 such
  markers by the same metric); the Grand Final has one.
* **Flickering** where stage models overlap. `course_atlas.degenerate_shared_triangles`
  zeroes the area of every render triangle an earlier model already draws
  (same rounded positions and primary texture) by writing its first uint16
  local index three times in the copied DX; file size, collision and land
  database stay unchanged, and duplicates inside one model (double-sided
  faces) are kept. Grand Final stages are processed first so the models it
  loads alone stay complete. All 20 patched DX files pass course render
  validation. Overlap whose BSP split differs between stages can still flicker.

### E1.5: gaLimitsAI emulation, Observatory captures (2026-10-27)

Owner captures (Observatory 0.3.0, InvFrance, Race ID 36) gave the player at
`(633, 532)`, `(1178, 411)`, `(1216, 323)` with `Race/Car0/LimitState = 2`
while AI cars stayed at 0. Reconstructed `FUN_004CD9B0` / `FUN_004CE140`:
the nearest marker of each list is searched in 3D (window of +-24 ordinals,
full scan every 15 ticks), the selection steps back one when the next marker
is nearer the selected one than the car, and markers `c, c+1, c+2` form two
X/Z segments; the car is outside-left when both left crosses are negative and
outside-right when both right crosses are positive. `course_limits_emulator`
implements this. It reports 0 outside samples on Retail scenes and reproduces
the three tested reset points (2332, 3303, 3541 m) exactly.

Causes and fixes:

* interleaved markers of different stages made near-lateral segments;
  limits are now one smooth monotonic polyline per list (25-unit stations,
  corridor width taken from the owned Retail markers, median-smoothed);
* where another route portion is near (hairpin legs, parallel roads) the full
  scan picked its markers; the width is capped at 45% of the clearance to
  route parts more than 200 units away (inner at 80% of the cap, outer at
  least 4 beyond inner, never under 12/15 units);
* `validated_limits` reruns generation with local narrowing until the
  emulator finds no outside sample on and 4 units beside the RaceLine;
* InvSpain is re-stitched with `--keep-clear 45` so legs stop where they
  would pass within 45 units of earlier road (12,095 m).

Result: no emulated LimitState 2 on the RaceLine in all five scenes.

Visual fixes in the copied stage DX (`degenerate_shared_triangles`): near
duplicates (same texture, centroid within 0.5, similar area: doubled
billboard trees) and start/finish dressing (`checks`, `stpf`, `masterlogo`,
`go` textures within 60 units of a used stage's StartArea/FinishArea, except
within 200 units of the new route's own start/finish) are hidden. Ground
without collision/lighting near the InvFrance start is most likely Retail
backdrop terrain outside the stage corridors; banner walls without collision
are expected to match Retail behaviour (not verified).

### E1.6: only the first landscape collides (2026-10-27)

Owner captures after E1.5: `ResetNo = 0` and `LimitState = 0` everywhere;
new issues at InvFrance 3.4–7.9 km. The impassable invisible wall is at
`(-834, 319)`, 7.84 km. Along the route the scene's models' render terrain
starts/ends at: FranceM and FranceS2 exit at 759 m, FranceW exits at 4010 m,
France1 enters at 7254 m, **France2 (the first landscape egg) exits at
7891 m**. No wall appeared at the earlier exits; the wall is exactly where
France2's terrain ends. Together with the owner's "ground without
collision" near the start (another model's ground where France2 has none),
start dressing with collision only at France2's own start, and banners of
other stages without collision, the evidence says **collision comes from the
first landscape model only; later landscape eggs are render-only**
(`HIGH_CONFIDENCE_INFERENCE`, runtime-consistent, not yet isolated by a
dedicated test). Manual reset (R) at the wall crashed in `FUN_0050EC50`
with a NULL pooled contact record from `FUN_004FFDE0`; the reset target lies
outside France2's collision, so the car drops into the void (same contact
pool path as the earlier PS2 hay-bale probe).

Consequence: several landscape eggs give a combined picture but not a
combined course. A drivable combined course needs **one DX per course** with
merged render, tag100 collision tree (180k planes / 360k nodes per Retail
stage, binary plane tree with leaf terminals) and tag1400 land database
(surface strings such as `$surfacetype(gravel) $shader(ground)$grnd(gravel)`
are stored there). Practical route: GXM v7 + TXT writer from the country
atlas and the Demo 9.10 cooker, which builds BSP, land database and draws.

Also found: tag1400 is the land database (20-unit grid, 56-byte ground
triangle records, surface-type strings); tag1500 is a 58-node X/Z graph with
neighbour lists in France2 (role unknown).

## E2.1 First cook runtime result and collision rebuild (2026-10-27)

* Retail `MRallye.exe` cooks a course GXM on cache miss: `invspaingx.dx` (23 MB)
  appeared after the first load. Demo builds could not cook these sources (owner).
* Owner captures `collision-troubles` / `unexpected-finish`: AI cars fell
  through at the start (Car1/Car3 Y -16000..-21000, Car2 NaN), collision wrong
  in many places, finish counted at 3.6 km.
* Finish: the stitched Spain route passes 47 units from its own FinishArea at
  markers 182/183; progress jumped to the last marker. `clear_route_end` now
  shortens routes until the last 120 units are 200+ units away from route parts
  500+ units earlier (Spain 11.97 → 11.68 km, France and Turkey also trimmed).
* Cooked tag1400 matched the union of the stage land databases (45 110 of
  45 488), so the land DB was not the problem. Retail sources build tag100 from
  `$bsp`: the land surface (`$draw $landdb`, manifold, Italy1 adds a `$skirt`
  rising from the boundary) plus closed `$nodraw` proxies (12-triangle boxes,
  24-triangle tree cylinders). E2 put 26 k open render meshes into `$bsp` and a
  union of corridor land databases that overlaps on every seam (332 non-manifold
  edges). Rebuild: `merge_land_surfaces` (route order, later stage triangles
  dropped where they lie on an earlier stage's surface; 44 319 triangles, 28
  non-manifold edges, no uncovered samples), render objects moved to `$objects`,
  `collision_boxes` → 1318 oriented box proxies (skipped: flat, longer than 40,
  within 2.5 of the route centreline at drivable height).

## E2.2 Holes and one-sided wall (2026-10-27)

Owner: almost no wall problems; holes along the route (mostly at old start
points with posts and tyres), sloped "floor" inside them; one one-sided wall.

* Cooked tag100 decoded for probing (`tools/course_bsp_probe.py`): plane node
  `s = n.p + d`, `s <= 0` → first child, else sibling; leaf `field_0` 1 = empty,
  0xFFFFFFFF = solid; plane `code` = source triangle index (0xFFFFFFFF = axis
  split). Retail SpainW: 0 of 1010 probes 0.7 below ground empty. E2.1 cook:
  132 of 2950 — 111 decided by box-proxy faces (bottom/sides of boxes reaching
  under the terrain), the rest probe artefacts at roofs.
* Above-ground solid on the route at (1945, 347) / (2015, 493): decided by the
  23 undrawn steep land records (`$landdb fill`) — the invisible blockers that
  close a Retail stage at its ends. Dropped.
* Box proxies are now 4-unit tiles standing 0.1 above the highest terrain under
  a 5x5 probe grid (roofs/walls ignored), so no proxy plane is below ground.
  Retail proxies do reach below the terrain (tree cylinders 0.2–0.7, forests up
  to 18), but off-road; the classification artefact is local to the proxy.

## E2.3 Beach wall, truck, ground tear, finish line (2026-10-27)

Probe on the E2.2 cook: underground-empty 132 → 5 of 2950; above-ground solid
only at the owner's two reports, both explained:

* Beach "another-collision" (2105, 85..120): palm trees use an opaque
  `$shader(object)` material, so the box covered the whole crown over the road.
  Box tiles now shrink to the object's surface within 3 units above the ground
  inside each tile (sampled every 0.75), i.e. the trunk.
* Truck across the road (2752, -39): body is `$shader(metal)` (was render-only),
  only tyres/wheels got boxes. `clear_road` removes object clusters (connected
  components joined by touching bounding boxes, ≤ 40 units) with any surface
  point within 3.5 of the centreline and lower than 2 above ground (1334
  triangles: old start/finish dressing on the new route); overhead banners stay.
  `$shader(metal)` objects are now solid (box proxies).
* Ground tear (2633, -187): SpainW's terrain there is 1.5–4 units off the other
  three stages; stage-order merge kept SpainW plus a second layer where the
  difference exceeded 3. `merge_land_surfaces` now prefers the stage whose leg
  the route drives (`route_owner`, within 150) and drops other-stage triangles
  within 8 units of height. Surface check along the route (±12 lateral, 30 k
  probes): 0 gaps; 75 stacked samples are Retail bridges/overhangs.
* Finish line: the trimmed end was 214 past Spain2's finish gantry.
  `snap_route_end` ends the route at the latest Retail Start/FinishArea centre
  within 30 of the route and 400 of its end that keeps the 200/500 clearance
  (Spain 11.50 km, FinishArea entry at the gantry).

## E2.4 Own collision tree (tag100) and dressing cleanup (2026-10-27)

* The retail cooker builds tag100 without clipping spanning polygons: Retail
  stages already show 0.1–0.5 % wrong cells (solid above / holes) off the
  road; the merged course had them on the road (beach "one-sided surface":
  a single slope plane, triangle 12040, decided a 20 x 40 area 3.5 above the
  sand).
* `master_rallye.course_bsp`: tag100 encoder (byte-identical round trip of the
  cooked invspaingx tree and Retail SpainW), solid-leaf BSP builder with
  polygon clipping (axis median splits while > 64 polygons), `close_land`.
  Grammar: back = child slot (leaf field_0 0xFFFFFFFF solid), front = sibling
  slot (leaf 1 empty), header = (child leaves, sibling leaves, planes, planes, 0).
* Open land breaks any solid-leaf BSP: Retail stages are corridors closed by
  `$nodraw $skirt` walls (Italy1 source) that compiled DX does not keep. With a
  rebuilt skirt the own builder is clean on Retail SpainW/SpainM/Spain2 (1
  questionable riverbed sample each). Merged land: skirt on the map edge and
  between corridors, fans for small holes, vertical step faces where seams join
  stage terrains of different height, crack seams left open.
* Different stages never stack: other-stage land over accepted land is dropped
  at any height (route-owner priority); bridges inside one stage stay.
* `tools/course_bsp_patch.py` replaces the tree in a cooked DX (rest byte for
  byte); `tools/course_bsp_watch.py` waits for the game's cook and patches.
  Area census (10-unit grid, 37.5 k points): 16 holes (hills 500 from the
  route), 66 solid-above (box proxies); route ±6: 2 questionable at the bridge.
* Build changes: `$shader(sign)` (banners, arrows) and fence gates are solid;
  box tiles checked against the road per tile, no flat/large component skips
  (fence rails, long fences); old start/finish zones (radius 100) lose all
  dressing (banners, posts, tyres, tents, trucks, crates, drums, gantries) and
  their non-land ground pieces; gentle non-land ground 0.3–4 off the land is
  dropped; undrawn land is drawn with a same-surface material; clear_road never
  removes vegetation.

## E2.5 Rocks, camp remnants, fence boxes (2026-10-27)

Owner on the own tree: seam invisible, collision almost right. Remaining:
* sea rocks with missing faces: non-land ground pieces 1–4 above the seabed were
  dropped by the "floating terrain" rule; now only pieces inside old start/
  finish zones are removed;
* camp remnant at (2780, -43): a yacht piece; `yaught`/`sweede boat` joined
  the dressing list (old zones only);
* fences snagged and stood at varying distance: per-component tiles along the
  component's axis left 0.6 gaps, duplicated boxes for rails and posts and
  widened on curves. Now components whose bounding boxes touch are joined,
  boxes are made per 3-unit world tile with the tile's own orientation from
  the object's surface within 3 above the land, the long axis stretched to the
  tile border where the object continues, top = highest surface in the tile
  (grey fence: chain of 0.3-0.5 x 3.3 boxes).

## E3 AI: difficulty levels and the heading field (2026-10-28)

### Difficulty (CONFIRMED_BY_EXE, Retail SHA above)

* Five AI levels, named by `ICont/<Level>/Min|Max` (`DataGame/ICont.xml`):
  0 VEasy (0/-5), 1 Easy (0/0), 2 Medium (0/10), 3 Hard (7/14), 4 Extream (10/30).
* AI controller init `FUN_0042CDB0` stores the level at +0x40 and applies it in
  `FUN_0042DEF0` (controller car +0x74 "TyreType" = level), `FUN_0042DF50`
  (Min/Max range) and `FUN_0042E020` (+0x3C class factor 1.4/1.3/1.2, default
  1.5, minus 0/0.1/0.3/0.7/0.8 by level). Spawn `0x42A97C` reads
  `Race/DifficultyLevel` (default 3 when missing); setter `FUN_004AC4D0`.
* Who sets it: Quick Race = menu index + 1 (Easy/Medium/Hard = 1..3) at
  `0x47B8C8`; Challenge = table `0x6B2E7C` per event `1,2,2,2,2,3,2,3,2,3,4`
  (Challenge 11 is the only Extream event); Master Rallye `0x4523C0` random by
  `MasterRallye/VehicleClass` (T1 0: Medium 30 %/Easy 60 %/VEasy 10 %; T2 1: Easy
  20 %/Medium 60 %/Hard 20 %; T3 2: Medium 70 %/Hard 30 %); Rallye Cups `0x45BFD4`
  tier base 1/2 with a random ±1; **Invitation (Cup 5) `0x45BFB6`: 2 + (rand
  1..10 >= 3) = Hard 80 % / Medium 20 %** (owner captures: 3 and 2); `0x465C2A`
  fixed Medium.
* `patch_invitation_entries.py --invitation-difficulty N` replaces the
  Invitation pick with a fixed level (`mov esi, N` + 8 NOPs at 0x45BFB6).

### Heading field

* `ICont/*.sfl` is the only per-course AI data. Measured on SpainW/France1/
  Italy1 the Retail field steers back to the line: the heading deviates from
  the road direction by 10–15° at 3 units off the line, ~30° at 6, 45–60° at 10
  (towards the line). The old synthesis was parallel to the road up to 8 units
  off the line, so a car drifting wide never came back (owner: AI hits walls).
* `synthesize_pursuit_field` aims every cell at the route point 12 units past
  its nearest point (2-unit polyline): median error vs Retail at 10 units off
  the line 18–22 (old 28–39), at 6 units 11–15 (old 19–21). Merged Spain vs the
  owning Retail stage fields at 8 units off the route: 16/24 (old 33/44).
