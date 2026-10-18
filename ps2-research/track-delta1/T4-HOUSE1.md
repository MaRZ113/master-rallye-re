# T4a: Turkey3 "House 1" as a loose PC model (data channel B, no AI, no collision)

Goal of the slice: prove the PS2 object to PC data path end to end: PS2 mesh to DX rev135 model, GXI to DXT texture, Egg in the loose RaceTest XML. Everything is loose files; the retail `Data.sma` stays untouched.
Script `ps2_obj_to_dx.py`. Output folders (untracked): `D:\Game\Master Rallye\research-output\t4-house1` and `...\t4-house1-flipv` (V mirrored).

## What is generated
| File | Content |
|---|---|
| `DataGx/Misc/PS2Port/house1/house1.dx` | template `haybaletest.dx` with its render draw replaced (`topology_writer.rebuild_topology`, bounds recomputed); texture slot renamed `hay-tga` to `brk-tga` (same length); the template's hay collision hull is still inside the file but unused (no AI) |
| `DataGx/Misc/PS2Port/house1/brk-tga.dxt` | `BRICKHOUSE-TGA.GXI` 64x64, RGBA to BGRA, header words copied from `hay-tga.dxt` |
| `DataScene/RaceTest/Turkey3.xml` | retail PC XML plus Egg `ps2_house1` in `IContManager`, model `misc\ps2port\house1\house1`, translation = mesh centroid (1971.71, 39.12, -113.11) |
Source: PS2 PSM mesh `root.0.65.1` ("House 1", 33 triangles after strip/ADC filtering, shader object). Vertices are stored relative to the centroid. Every triangle is written in both windings (66 triangles) because the PS2 strip winding is not resolved; flat normals; white vertex colour (the PS2 tint is not reproduced).

## Run
1. Copy `research-output\t4-house1\DataGx\Misc\PS2Port` to `D:\Game\Master Rallye Pristine\DataGx\Misc\PS2Port` and `research-output\t4-house1\DataScene\RaceTest\Turkey3.xml` to `D:\Game\Master Rallye Pristine\DataScene\RaceTest\Turkey3.xml` (replace the previous candidate). Keep `[Diagnostics] CrashLog=1`.
2. Start Turkey3, teleport next to the house: `Point1=2000.0,33.0,-111.7,0` (house is 26 units ahead of this point toward +X, 52 units from the road).
3. Record: course loads; house visible; position and size plausible (compare with the PS2 screenshots); texture orientation (if the bricks look mirrored or upside down, repeat with `t4-house1-flipv`); lighting (too bright or flat is expected); culling (any missing walls).
4. Remove `DataGx\Misc\PS2Port` and the XML to return to stock.

## Known limits
No collision, no PS2 tint or lighting, placeholder winding policy, template bounds recomputed but other template metadata unchanged. One object only; the other 22 MISSING_ON_PC meshes (caravans) are the same recipe with other mesh paths and textures.

## Update 1 (user result and fixes)
Result of the first run (user, 2026-10-19): the house loads and draws in the right place, bricks and roof look correct; lighting is flat (white vertex colours) and there is no collision.
- Lighting: the PS2 vertex word at +16 holds bytes (A, c1, c2, c3); for the 48,406 vertices that exist in both PS2 and PC Turkey3 the PC course DX colour is (c1, c2, c3, 255), equal within 1 and with no x2 scaling. The converter now copies the PS2 tint as is (198 vertices, 66 triangles).
- Collision: PC course collision is the tag100 BSP at the end of `turkey3.dx` (not per object). `tag100_patch.py` inserts the convex hull of the mesh (33 planes) as a solid brush: every empty leaf whose cell overlaps the hull (82 leaves) becomes a chain of the hull planes. Tests in `test_tag100_patch.py` (synthetic trees; hull planes; outside unchanged; two-cell straddle) pass. On retail Turkey3: 118 of 118 random points inside the hull are solid, 0 of 29,882 other points around it change class, and the patched tree keeps all count invariants (nodes 235,089 to 240,501). The 1.9 MB that follows the tree in the same suffix is carried over unchanged.
- The patched `DataGx/Course/Turkey3/turkey3.dx` is 10,180,083 bytes (retail suffix + 124,476 bytes). It is a loose override of the course DX; the other course files are still read from `Data.sma`.
Run: copy `research-output	4-house1\DataGx\Course` as well (new folder in the test install). Expected: the car stops at the house walls. If the game rejects the file or crashes on load, remove `DataGx\Course` first (the model and Egg are independent of it).
