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
