# T4c: PS2 ground delta of Turkey3 carried to the PC course (visual + collision, loose files)

Scripts: `ps2_terrain.py` (visual models, neutralising, collision slabs), `tag100_tree.py` (in-memory tag100 with exact serializer), `ps2_course_objects.py --terrain` (builds everything, objects included), `terrain_verify.py` (checks), `ground_clusters.py`, `ground_delta_probe.py`, `ground_delta_regions.py` (measurements). Output (untracked): `D:\Game\Master Rallye\research-output\t4-terrain`.

## What differs (measured)
Ground = PS2 PSM meshes with shader(ground) / PC course-DX draws whose third texture slot is noise-tga. Exact = the other side has a triangle with the same three vertices (0.001).
- PS2 ground 27,121 triangles, 4,020 non-exact; PC ground 26,286, 3,512 non-exact (about 15 percent of the ground).
- 3,424 of the 4,020 share the XZ footprint of a PC triangle, and 2,694 of those with identical heights: only UV, colour or texture differ (that is the ground texture around the house in the PS2 screenshot).
- About 730 have different heights (up to 19 units), about 600 have no PC twin. Height-field comparison on a 6-unit grid: 4.1 percent of the cells differ (2,233 below, 474 above), 141 regions; the trench under red caravan 4 is one of them (PS2 lower by up to 6.6 units over about 60 x 20 units).

## What is built
Visual: the 3,512 PC non-exact ground triangles are neutralised in `turkey3.dx` (their three local indices point to one vertex: zero area, no structural change); the 4,020 PS2 ones are added as 21 static models, one per texture (`DataGx/Misc/PS2Port/terrain/terrainNN`, template DX, GXI to DXT with flipped V, PS2 tint and UV, faces oriented up), one Egg each. The PC noise detail layer is not reproduced.
Collision (tag100): per PS2 triangle a fill slab (solid between the PC surface and the PS2 surface where PS2 is higher) and a carve slab (empty where it is lower); planes carry a valid ground code and normals toward the empty side (`tag100_tree.py`, round trip on retail Turkey3 is byte exact). 2,569 triangles with identical heights need nothing; 515 fill and 850 carve brushes replaced 10,317 and 20,313 leaves. 237 near-vertical triangles are skipped. Tree 5.4 MB to 17.8 MB (header words 143,551 / 202,249 / 345,799), loose `turkey3.dx` 20.5 MB.
Objects: the T4b objects are back at their PS2 positions (no snapping); with the PS2 ground their lowest vertices sit within 0.5 of the ground (before: red caravan 1 +2.3, red caravan 4 -3.3 against the PC ground).

## Checks (offline)
- At 3,000 random PS2 non-exact triangle centroids a surface (solid just below, empty just above) is present in the collision tree: 72.1 percent before, 93.3 percent after. 2 of 3,000 centroids regressed (steep triangles next to cliffs), the rest of the failures were failures before (steep or multi-layer ground).
- Random columns over the course box whose collision ground changed: 84 of 3,694 (the patched areas only).
- Tree counts and round trip checks pass (`test_tag100_tree.py`, 5 tests).

## Run
Copy from `research-output\t4-terrain`, keeping paths, into the test install: `DataGx\Misc\PS2Port` (now with `terrain`), `DataScene\RaceTest\Turkey3.xml`, `DataGx\Course\Turkey3\turkey3.dx`. Check: terrain around the house (texture, fence area), the trench near red caravan 4, seams where PS2 and PC ground meet, objects standing on the ground at their original place, driving over patched areas (no falling through, no invisible bumps), load time and three race restarts. If anything misbehaves, remove `DataGx\Course` first (that restores the PC collision and ground; models then show on top of the PC ground), then the rest.

## Known gaps
Steep or vertical PS2 triangles (237) and multi-layer ground (caves, overhangs) are not handled; walls are approximated by the slab under the triangle's XZ projection. The PC noise detail texture is missing on the added ground. Fences, huts, shrubs and boats (PLACEMENT_DIFFERS) are still not carried over; only ground-shader triangles are.

## Update 1 (user run, 2026-10-19): holes and collision problems
User result of the first build: sky-coloured holes in many places (one large triangle at a rock arch) and collision problems where terrain changed. Causes found and fixed:
1. Culling holes: steep, vertical and downward-facing PS2 triangles (cliffs, rock undersides) were written in a single winding oriented "up", so half of them were back-face culled. Now only gentle slopes (|ny| > 0.7) are single-sided, every other triangle is written in both windings.
2. Hole at the arch near (2600, 85, -845): 6 PC triangles were neutralised although the PS2 has no triangle near them (the PS2 arch is a different mesh). `with_replacement()` now neutralises a PC triangle only when a PS2 added triangle has its centroid within 0.75 x the longest edge (3D); 3,506 of 3,512 are neutralised, 6 stay.
3. Collision slabs were wrong where the PS2 ground has several layers (arches, overhangs, rock undersides): the slab between the PC top surface and a lower layer cut a passage, the slab under an arch top filled the way under it. Slabs are now only made for the top-most PS2 surface at the triangle centroid, only where a PC triangle with the same footprint gives the exact PC surface (no estimates from sampled heights), and not thicker than 8 units; 612 triangles without a twin, 50 lower-layer and 21 too-thick triangles are left to the PC collision. Result: 189 fill and 466 carve brushes (before 515 and 850), tree 13.8 MB (before 17.8), loose `turkey3.dx` 16.5 MB.
Offline check at 4,000 PS2 columns: solid 0.6 above the PS2 top surface (blocking) 578 retail, 381 patched; empty 0.6 below it (falling) 337 retail, 248 patched. Collision ground changed in 54 of 3,694 random columns.
Known: places where the PS2 geometry is multi-layer or much thicker than 8 units keep the PC collision, so the visible PS2 terrain and the collision differ there (an exact transfer needs the PS2 BSP leaves, not the visual triangles).

## Update 2 (user run, 2026-10-19): holes gone, texture quality differs, collision still off in changed places
Textures: the PS2 GXI files are 64x64, the PC course textures of the same names are 128x128 (the added terrain looked blurrier than the PC ground around it). `texture_dxt()` now prefers the PC DXT of the same name when it exists and shows the same image (PC image box-filtered to 64x64, rows flipped, mean channel difference at most 14 of 255): all 21 terrain textures and `newtex` (red caravan) use the PC 128x128 file; brickhouse and caravan exist only on the PS2 and stay 64x64. The PC noise detail layer is still missing on the added ground, and PS2-only textures cannot be sharper than 64x64; a global fix means replacing the whole PS2 course render data (not only the delta), which is a separate decision.
Collision: the visible PS2 terrain and the PC collision still differ where the slabs were skipped (612 triangles without a PC twin, 50 lower-layer, 21 thicker than 8 units, 195 near-vertical). The exact fix is to transplant the PS2 BSP solid leaves into the PC tree for the changed regions (carve the region, fill with the PS2 leaf polyhedra), restricted to regions that are not inside the PS2 solid exterior shell.
