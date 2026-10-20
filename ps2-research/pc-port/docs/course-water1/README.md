# COURSE-WATER1: PS2 water, puddles and waterfalls on PC

Opt-in `PS2Water=1` (PS2Port.ini). Default 0 = Stock: nothing is loaded, every PC water draw stays as it is.

With `PS2Water=1` every native course draw whose triangles are PS2 water surfaces is replaced by the two PS2 passes of
its PS2 shader. All 34 courses with PS2 water are covered by the converted course packages (Italy1 and Turkey1 have no
water on either platform); stock PC course draws that equal the PS2 surfaces are covered too.
Inventory: [inventory.json](inventory.json) (coordinate-free). Runtime check of the contract against PCSX2 GS dumps:
[gs-validation.json](gs-validation.json) (tool `gs_water_check.py`).

## 1. What PS2 does (recovered)

Sources: SLES_509.06 decompiled with Ghidra EER (addresses below), the earlier static contract in
`ps2-research/water1/`, and 20 PCSX2 GS dumps of the owner (17 contain water passes; the puddles identify the course of 16:
15 Turkey2, 1 France1).

Each water strip is drawn twice on the same vertices, in landscape order (no separate water pass at the end):

| | Primary (GS context 1) | Secondary (GS context 2) |
|---|---|---|
| texture | course map (`water-tga`, `i2a_water-tga`), uploaded CT16: alpha bit = 1.0 | `CommonTextures/WATERSURFACE2` (64x64 CT32, alpha = GXI alpha >> 1) |
| colour | texture x vertex colour (MODULATE, 128 = 1.0) | the same |
| puddle (mode 9) | (Cs-Cd)*As+Cd, fog, Z test GEQUAL, **Z write** | **Cs*56/128+Cd**, TCC 0, no fog, no Z write |
| water (mode 10) | (Cs-Cd)*As+Cd, fog, Z write | (Cs-Cd)*As+Cd, TCC 1, fog, no Z write |
| waterfall (19) | `WATERFALL-TGA`, (Cs-Cd)*As+Cd, fog, Z write | `WATERFALL2-TGA`, (Cs-Cd)*As+Cd, fog, Z write |

Alpha test is off in every pass; TEST ZTE = 1 (depth test on) is confirmed by the dumps (TEST 0x51000 / 0x5040c), the
primary ZBUF has ZMSK 0 and the secondary ZMSK 1 (ZBUF 0x2000050 / 0x102000050).

Vertex colour and UV (float32, order of the EE code; `tools/ps2_water_model.py`):

- **Puddle colour, at load (320938):** for each vertex the ground query 2d4618 (tag-103 grid cell, XZ point-in-triangle,
  vertical intersection, hits sorted top to bottom) gives the lowest hit whose material has no `water` substring;
  RGBA = clamp(int((1 - 1/(2d+1)) * 255), 2, 254) with d = |vertex y - hit y|; 254 if fewer than two hits. The packet
  halves it. Shallow puddle edges therefore fade out (alpha and colour), deep water is opaque.
- **Water colour, at load (320f90):** RGBA 254.
- **Phase (316808):** T = counter / 150, unchanged while Game/PauseMenuEnabled is set.
- **Puddle UV, every frame (320c78):** a = .1x + 1.61368T, b = .1z + T,
  A = L(1.13a) - L(1.78b + 1/4 turn), B = L(2.19a + 1/4 turn) + L(2.93b) (L = 4096-entry sine table 328c90).
  Primary = (.05x + .05A, .05z + .05B). Secondary = env mapping of the perturbed normal (n.x + .6A, n.y, n.z + .6B) by the
  camera rows 42dc00 (written by the camera setter 343458): u = .5 + .5 p.x_cam + .02x, v = .5 - .5 p.y_cam + .02z
  (PS2 camera x right, y down).
- **Water UV, once at load (321098):** the same with frequency .05, primary (.01x + .05A, .01z + .05B), the camera
  rows replaced by the fixed rows (1,0), (0,1), (0,0); each component minus the integer of its mesh mean.
- **Waterfall UV, every frame (321838):** U = authored U in both layers; V = .05y + frac(2T) (primary) and
  .05y + frac(4T) (secondary) minus floor(.05 y_first + 6).

No geometry is generated or deformed: the surfaces are authored PSM strips. No render target or dynamic reflection is
connected; the "reflection" look is the static WATERSURFACE2 image mapped by the camera-space normal.

### Runtime confirmation (GS dumps, `gs-validation.json`)

- All 1,044 puddle strips of the 16 dumps with puddles match the computed 320938 weights // 2 bit for bit (one GS run =
  one strip); this also identifies the course of each dump (Turkey2, France1).
- Turkey2 puddles, two dumps: T = 11056/150 and 10600/150 solve all 2,044 and 516 vertices; primary UV residual <= 0.0021
  and 0.0043 (ST/Q precision). The secondary layer gives the camera columns (0.754, 0.000, -0.658) / (0.191, -0.957, 0.219)
  and (-0.852, -0.003, 0.540) / (-0.138, -0.966, -0.215): unit length, orthogonal, y down, i.e. the camera rotation.
- Turkey2 water: all 228 runs map to strips by the secondary V alone; load phase 7615/150; 5,932 vertices, residual
  5.7e-5 (primary) and 8.8e-5 (secondary).
- France1 waterfall (dump 20261020100436, owner, after the first version ran too fast in the game): both layers use the
  common WATERFALL-TGA / WATERFALL2-TGA (1,011 of 1,024 texels in VRAM), ALPHA 0x44, fog, Z write in both contexts;
  20/20 strips match 321838 (U = authored U within 1e-7, V - .05y constant per strip, frac(4T) = 2 frac(2T)).
- **Speed.** A dump holds four fields. The waterfall dump shows two rendered frames, each for two fields, and frac(2T)
  grows by 0.01318 between them: the counter advances by 0.99, i.e. **once per rendered frame**, not per field. Over the
  16 race dumps PS2 shows a new frame on 27 of 48 field changes (`frame_rate` in gs-validation.json): about 28 frames per
  second. The port advances the counter 28 times per second (first version: 50, 1.8 times too fast in the game).

## 2. What PC does

The converted packages (and retail PC water) draw these surfaces with `shader/base_water` (565da0 -> class 585290,
pass 5854d0): stage 0 texture x diffuse (alpha = diffuse), stage 1 ADD `misc/water/watersurface3` (feature bit 0x10,
577620), opaque in the packages (flags 00 00 01 01, feature 19). No second blended layer, no gap transparency, no
camera-space UV and no animation: fixed-function D3D8 cannot express the PS2 UV (world xz plus a perturbed camera-space
normal) without per-vertex CPU work. This is why Turkey2/Turkey3 puddles look solid on PC and why the PC river lacks the
PS2 surface layer.

## 3. Implementation

| Part | File | Depends on |
|---|---|---|
| reference model | `tools/ps2_water_model.py` | Python only |
| asset generator, inventory | `tools/prepare_ps2_water.py` | PS2 corpus, course-port, `research-output/course-port-36`, retail PC course DX |
| portable core (asset, math, clock, passes) | `renderer/ps2_water.hpp` | C++17 standard library only |
| D3D pilot (textures, key cache, state transaction) | `renderer/ps2_water_pilot.hpp` | proxy SDK, provenance |
| native seam | `renderer/ps2_water_native.hpp`, patch 0001 (draw hook, repair, reset, shutdown, config) | the PS2 port extension seams |
| tests | `tests/ps2_water_tests.cpp` (ctest `ps2_water_contracts`), `tests/test_ps2_water.py` | built test binary, asset |
| runtime check | `docs/course-water1/gs_water_check.py` | GS dumps, `course-light1/gsdump.py` |

**Generator.** For each course it takes the PSM meshes of the three water shaders, applies the course-port triangle rule
(so the set equals the converted course), computes the puddle weights and the static water UV, and matches every draw of
the package DX and the retail DX: a draw is claimed only when all its triangles are PS2 water triangles (corners within
0.001, each PS2 triangle claimed once). Its key is the triangle count plus the SHA-256 of the sorted canonical triangle
positions (corner and triangle order free). Textures: the PC 128x128 course map where it shows the PS2 image (mean error
0.86/255 after the PS2 row order) with the PS2 alpha (1.0), else the PS2 GXI; WATERSURFACE2 and the two waterfall maps
from PS2 (no PC counterpart). Rows are in D3D order (row 0 = v 0 = the last GXI row, as the GS samples it).

**Runtime (`PS2Water=1`).** In `draw_indexed_at`, before every other course-draw replacement: a TRIANGLELIST draw with a
triangle count that occurs in the asset, inside a certified race, is identified by buffer identity (cached per buffer
generation and mirror revision) or, the first time, by the SHA of its mirrored positions. A match is not submitted; its
PS2 parts are drawn with `DrawPrimitiveUP` (two passes each) at the same point of the frame, with the native transforms,
depth buffer and fog. The world matrix must be identity; the camera rows come from the native view matrix (y column
negated: D3D y up, PS2 y down). One fixed state transaction captures and restores 31 native states (tracked shadow
first) and stream 0. Managed textures with box mip chains survive Reset; the key cache is dropped on Reset.

**One rendering path.** A surface is either the native PC draw (no key, PS2Water=0) or the PS2 passes — never both.
The PS2OBJ01 puddle preview (`CourseObjects=1`, Turkey3) yields with `superseded_by_ps2_water` once PS2Water draws that
course in the race.

**Other PS2 systems.** Lighting, fog colour/range, grass, ground detail, reflections, birds and HUD are untouched: the
water draws only its own surfaces with its own states and restores everything. The COURSE-ALIVE1 boats are drawn later
(pre-UI boundary) against the depth the water primary wrote, so a submerged hull is hidden below the surface; the car,
splashes and other later draws are depth tested against it the same way, as on PS2 where water is part of the
landscape pass.

## 4. Configuration

```ini
PS2Water=1
; optional:
PS2WaterAsset=PS2Grass/PS2Water.ps2wtr
Diagnostics=1   ; ps2_water_config, one ps2_water_course record per course, gate reasons
```

## 5. Verification (automatic)

- Generator: 34/34 water courses, every PS2 water triangle in a claimed package draw, no mixed draw
  ([inventory.json](inventory.json)); 590 keys; asset `2480f84d...` (13.5 MB, pinned in `ps2_water_pilot.hpp`).
- C++ core = Python model bit for bit over every asset vertex at five counters (`test_ps2_water.py`).
- ctest `ps2_water_contracts`: table, conversions, colours, materials, asset layout and rejections, order-free key,
  clock, transaction layout.
- GS dumps: section 1.
- Overlay build on master `a6b7c31` + this change: ctest baseline 24/24, PS2 41/41 (new `ps2_water_contracts`),
  unittest 147 OK, compileall; PS2-enabled DLL `61e90675...` (`dist/current`). Patch 0001 gained only the water seams; its
  hash in `overlay/baseline-lock.json` is updated (baseline unchanged). In-game kit: `dist/course-water1/`
  (`overlay/package_course_water1.py`), steps in [runtime-ab.md](runtime-ab.md).
- Not verified: anything in the game (status PENDING_USER).

## 6. Limits

- The PS2 LOD (TEX1 K -3.5 per strip, CT16 5-bit course map) is replaced by D3D trilinear filtering of the 8-bit PC map.
- 56/128 of the puddle second layer becomes 112/255 (0.4392 instead of 0.4375).
- The EE FPU rounding mode is not reproduced (IEEE round to nearest); the dumps show UV residuals of 5.7e-5 to 2e-3.
- The counter rate is the mean PS2 frame rate of the dumps (28 per second); on PS2 it follows the frame rate of the scene
  (25 when every frame takes two fields, up to 50), so a heavy or light PS2 scene animates slightly slower or faster.
- Water draws the engine culls are not drawn (as on PC); PS2 culls by its own scene tree.
- Order between PS2 Eggs (boats) and the landscape water is not reversed; with the water primary writing depth, a hull
  below the surface is hidden, not seen through a translucent puddle.
- A course DX rebuilt with different water draws needs a regenerated asset (the keys fail closed: native water stays).
- Split-screen: drawn in both views (camera rows per view); not tested.
