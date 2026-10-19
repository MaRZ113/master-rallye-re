# First game test of Turkey3 v1 and the fixes in v2

The owner ran `course-port-turkey3-v1` and the noise-local variant on 2026-10-19.

**What worked:**
- the course loads (slower than retail) and stays stable;
- the PS2 geometry, collision and borders are there;
- no difference in ground grain between v1 and noise-local.

**Problems reported, cause and fix** (each cause measured on the data, not guessed):

## 1. Splashes on dry ground, endless "RECOVERING VEHICLE" on the bridge, car shadow missing on some ground
- **Cause.** Orientation of the surface records (tag1400).
  - On retail courses 97 percent of ground records and 100 percent of water records have a downward plane normal (wire order: face normal
    against the vertex normals). The engine evidently decides above/below a surface with that normal.
  - v1 built the records in PS2 strip order: 14,731 up and 12,390 down on Turkey3, water 416 up and 329 down. With a water record facing up,
    a car above the river counts as under water. That explains the bridge (the deck and walls are `$surfacetype(gravel)` records, the river below
    is `water $surfacetype(water) $shader(puddle)`) and the splashes beside the river; the shadow on flipped ground records fits the same cause.
- **Fix.** `surface_grid.ps2_records` writes records in PC corner order (`course-port/ps2_mesh.pc_order`). Turkey3 v2: 96.8 percent face down,
  retail 96.8 percent. `build_course.py` now checks this for every course (`surface_records_face_down`).

## 2. Banners and the red caravan upside down
- **Cause.** The PC course uses the raw PS2 UV.
  - On every vertex shared by PS2 and PC Turkey3 the PC UV equals the PS2 UV, for every texture (ground, tyres, boats, huts, banners...), never
    1 - v. v1 flipped V. That is invisible on tiling ground and on PC-copied triangles, wrong on banners and on `newtex` (red caravan).
  - The texture audit of TRACK-GROUND1 was right about the image rows (PC DXT bottom-up, GXI top-down). The UV is simply not flipped; a texture
    converted from PS2 must have its rows flipped instead. T4 wrote top-down rows and flipped V, which gives the same picture for PS2 textures.
- **Fix.** Raw UV everywhere; PS2-only textures are written with bottom-up rows (`ps2_mesh.convert_gxi_rows`). The v2 banners have the PC UV
  handedness on all 684 triangles.

## 3. Banner "tearing", one-sided foliage
- **Cause.** Two-sided materials. PS2 draws without back-face culling; the PC compiler made two-sided materials by storing each triangle twice
  with opposite order (same normals, UV and colour, same draw).
- **Measured on 36 courses** (`orientation_map.py`, `orientation-map-36.json`):
  - two-sided on PC: `treeblend` 99.8 percent, alpha-tested `tree` 78 percent, every `wires` / `wire` / `signtest` / `glass` / alpha-blend group;
  - single-sided: ground, water, puddle, sign, most objects.
- **Fix.** Triangles of a two-sided group get the reversed copy (Turkey3: 6,206). For single-sided triangles the corner order "face normal
  against the PS2 vertex normals" reproduces the PC order on 100 percent of the shared triangles of every group, and the PC order is copied
  wherever the triangle exists on PC.

Not yet explained: the reported banner tearing could also come from two PS2 banner meshes at nearly the same place. v2 has to show whether it
remains.

Packages: `research-output\course-port-turkey3-v2` (+ `-noise-local`), all 36 rebuilt in `research-output\course-port-36`.

## Second game test (v2, same day)
- **Confirmed fixed by the owner:** banners, caravans, bridge, splashes, shadow.
- **Ground grain:** hard to see; on screenshots the rock looks more uniform without the experimental noise. The plain variant stays the default.
- **Remaining fault: holes in some walls (the concrete walls near the brick house) and in a rock.**
  - Corner order inside each mesh is consistent: of 38,666 shared edges only 4 are walked the same way by both triangles. So the holes are not
    flipped neighbours.
  - They are open shells that PC does not have. Example: `rustic Hut` near the house has 103 triangles, none of them on PC, and 33 open edges.
    PS2 shows the back side of such a shell, because it does not cull; PC culls it away.
  - Geometry that PC has was made culling-proof by the PC artists and keeps its PC sidedness.
- **Fix in v3.** Triangles that PC does not have get a reversed copy:
  - PS2-only objects (non-ground, except signs): 3,649 on Turkey3. Signs stay single-sided: PC keeps 99 percent of them single-sided, and a
    two-sided banner shows mirrored text and fights with a banner mounted back to back;
  - PS2-only ground where it is steep or faces down (outward normal y < 0.5): 690. Flat ground is never seen from below.

  Turkey3 v3: 1,149 draws, 61,019 vertices, 154,119 indices, inside the retail maximum (227,061 indices, FranceM). The new package check
  `within_retail_vertex_and_index_range` covers this.
