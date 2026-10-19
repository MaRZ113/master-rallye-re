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

## Third game test (v3)
The owner compared v3 with PCSX2 screenshots of the same places (GS dumps in `C:\Games\PCSX2_Nightly\snaps`, 2026-10-19 17:41 and 17:43, not
needed in the end).

**1. The see-through fence was solid.**
- The mesh is `fence $shader(tree)` with `fencegate-tga`: 52 percent of the texture is transparent, and the PS2 mesh flag 0 (alpha on) is set,
  but the material has no `$alphatest` / `$alphablend` directive. The v3 rule table looked only at directives and made it opaque.
- Measured on 36 courses (PS2 mesh flag 0 against the PC alpha byte on shared triangles):
  - flag 0 set without a directive: PC draws 91 percent of these triangles with alpha, mostly blended;
  - flag 0 clear: PC is opaque on 99.9 percent.
- **Fix in v4.** A mesh with flag 0 and no directive takes PC's own material of the same base texture when that is an alpha material.
  `fencegate` gets (fencegate, aluminium) blended and sorted, exactly as PC draws its gate. Otherwise it gets alpha blend with sorting.

**2. A rock still had a gap at its foot** (PS2 shows it closed). Ruled out with data:
- The built triangle set equals the decoded PS2 scene exactly.
- T-junctions: PS2 132, retail PC 133.
- The ADC strip rule was verified earlier against the VU microcode.

What remains is the PS2 "no culling" effect on geometry that PC also has: through the open foot of the rock PS2 shows the rock's inner (back)
faces, PC culls them and shows the far terrain.

**Fix in v4 (mode `all`).** Every object (except signs and water) and every steep or downward-facing ground triangle gets both sides,
whether PC has it or not. Turkey3: 6,052 object and 3,141 ground triangles; 168,681 indices, inside the retail maximum of 227,061. A course that
would leave the retail vertex or index range falls back to the v3 rule (PS2-only geometry) and the report says so.

## Fourth game test (v4)
Owner result (2026-10-19):
- The fence is see-through now. It shows the PC material (fencegate + aluminium) rather than the PS2 look; accepted, not worth more work for
  one fence.
- **The gap at the rock foot got larger.** The screenshot shows a white wedge (sky colour) at the rock base, so nothing at all is drawn there,
  not even the far terrain behind it.

So the v4 hypothesis (missing back faces behind an open foot) is wrong or incomplete. If back faces were the cause, the wedge would show the
rock's inside; instead nothing is drawn, and two-sided copies made it worse. Leads, not yet checked:
- a draw or sector culled too early, for example by its tag5 sphere or by the sector polygon of the triangles at the foot;
- depth or sort trouble between the reversed copies and the alpha-sorted draws.

As agreed with the owner, this stays open and moves into the later phases; the PCSX2 GS dumps of the spot are available for it. Packages keep
the v4 rule for now.

## Fifth game test (36 packages with the W4 XML)
Owner result (2026-10-19):
- the courses load with the long limit lists, the OFF COURSE border is clearly wider, races finish normally;
- the reset timing difference is accepted as is;
- replay cameras: PS2 drives them with its own logic, which is a separate port. The PS2 camera positions are therefore off by default
  again (`build_logic.py --cameras` turns them on);
- the FranceM airship stand-in loads and looks right;
- **Turkey2:** straight seams in the ground grain, and lighter grass than PS2 where PS2 added trees.

**Cause of both Turkey2 findings: the noise layer was missing on PS2-only ground.** Turkey2 v4 had 5,527 PS2-only noise triangles without
the layer (2,995 got it from a PC vertex at the same position). Without it the ground has no fine grain and looks lighter, and the border to
triangles that do have it is a straight seam.

**Fix: the noise UV comes from the PS2 data.** The PS2 vertex pair at +28, so far marked "unexplained", is the noise UV. On every PC noise
vertex of a triangle shared with PS2:
- PC noise UV = PS2 pair + (0.5, 0.5) + an integer;
- checked on 36 courses: 1,711,740 vertices in 570,580 triangles;
- the integer is the same for all three corners of every triangle;
- the noise texture wraps, so the integer does not change the image.

`ps2_mesh.noise_uv` and `build_render.py --noise ps2` (now the default) use it for every PS2-only noise triangle, so no triangle loses the
layer. The experimental `local` fit is no longer needed. Turkey2: 8,522 triangles get the PS2 noise UV, and all package checks pass.
Not yet confirmed in the game: whether this also brings the darker PS2 grass under the trees, or whether that area differs for another reason.

## Sixth game test (36 packages: PS2 noise UV, PS2 vertex colour, collision fix)
Owner result (2026-10-19), Turkey2:
- the hard light/dark edge in the grass under the PS2 trees is gone: the PS2 vertex colour on the triangles shared with PC was the fix
  (`afadb23`). The PS2 noise UV removed the grain seams (`cd36c64`);
- the invisible one-sided wall next to the fence is gone (`cba0008`, `../track-coll2/REPORT.md`, section on invisible walls).
Still open from earlier tests: the gap at the Turkey3 rock foot (fourth test).
