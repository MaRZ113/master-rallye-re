# TRACK-GROUND1: material parity of the transferred ground

Scope: Turkey3, reusable for the 36 courses. Code: `track-delta1/ps2_terrain.py` (`texture_dxt`, `choose_texture`, `texture_difference`, `make_dxt`, `refine`, `noise_mean_factor`, `visual_models`), `track-delta1/ground_material.py`, audits in this folder (`texture_audit.py`, `ps2_vertex_fields.py`, `package_checks.py`). Evidence labels: CONFIRMED_BY_BYTES (derived from the original files), SYNTHETIC (unit tests / built data), HYPOTHESIS, UNKNOWN. Nothing here is RUNTIME_CONFIRMED.

## 1. Texture parity

### 1.1 Findings (CONFIRMED_BY_BYTES, `texture-audit-turkey3.json`)
- The PS2 PSM of Turkey3 references 69 textures. 65 have a PC `.dxt` in `DataGx/Course/Turkey3`; 4 are PS2-only (`brickhouse`, `caravan`, `shrubtrig2`, `water`).
- Orientation: GXI rows are top-down, PC DXT rows bottom-up. With the PC image box-filtered to the PS2 size and its rows flipped, the mean RGB difference is 0.30 to 0.38 (of 255) for the 64x64 versus 128x128 pairs and 0.0 for equal-size pairs; flipped columns or unflipped rows are always worse. The expected orientation is the best of four in 63 of 63 genuine matches (the two exceptions are the two different-artwork cases below, where no orientation fits).
- Same-name matches measure at most 6.56 (`newtex`, the red caravan texture: the PC file is the same artwork, sharper), the first different-artwork pair measures 11.77. The old tolerance 14 therefore accepted a wrong pair.
- Two PS2 textures exist on the PC under another name: PS2 `plating2` equals PC `tanky` (difference 0.0, the PC `plating2` is different art at 11.77) and PS2 `i2a_planks2` equals PC `wood_01` (0.0, same-name PC file 26.0).
- DXT header: word_0x08 is the CRC32 of the pixel payload in 65 of 65 PC files (and in 25 of 25 earlier checked). The first converters copied the haybale value into every converted texture (house, caravans, 21 terrain textures). Whether the engine keys anything on it is UNKNOWN (all textures looked right in the earlier runs), but the files are now correct.
- Mip levels: the DXT format is level 0 only (20-byte header + BGRA rows), same for PC and converted files; filtering and mip generation therefore follow the engine's normal path for PC textures. A PS2-only texture is 64x64 and cannot be sharper.

### 1.2 Policy implemented
`choose_texture(base, rgba, w, h, header, pc_dir, tolerance=8.0, rename_tolerance=2.0)`:
1. same-name PC file within 8.0 -> the PC file as is, source `pc`;
2. else another PC file of the course within 2.0 of the PS2 image -> `pc_renamed:<name>`;
3. else the PS2 GXI converted (RGBA to BGRA, V flipped by the caller, header CRC), source `ps2`;
4. PS2 file unreadable but PC file exists -> `pc_unchecked` (reported, never silent); neither -> none.
The source of every texture is in `report.json` (`texture_source`). Genuinely different PS2 artwork is never replaced by a same-name PC file.
Result for Turkey3 (`texture-audit-turkey3.json`): 63 `pc`, 2 `pc_renamed`, 4 `ps2_only`. In the built package: 18 terrain textures all `pc` (128x128), `newtex` `pc`, house and caravan `ps2` (64x64).
SYNTHETIC: `test_ground1.py` covers CRC header, orientation preference, same-name, different artwork, renamed file, missing files, unreadable PS2 file, and the retail header CRC and noise factor.

### 1.3 UV and vertex tint (CONFIRMED_BY_BYTES, carried from T4)
Vertex tint: the PS2 vertex word at +16 holds bytes (A, c1, c2, c3); the PC course vertex has (c1, c2, c3, 255) for the same position (48,406 shared vertices, equal within 1). UV: V is flipped (`1 - v`) because the PC DXT is bottom-up; the audit above is the independent check of that choice. Texture wrap: 1,706 of the 1,723 same-geometry same-texture ground triangles whose UV differs from the PC triangle differ by one integer offset that is the same for all three vertices, which is identical sampling under wrap addressing.

## 2. Ground material

### 2.1 Native PC ground (CONFIRMED_BY_BYTES for the data, existing GROUND-DETAIL1 research for the stage contract)
A PC ground draw has the texture tuple (base, 'Null', 'noise-tga'); stage 0 is TEXTURE x DIFFUSE, stage 1 is CURRENT x TEXTURE with MODULATE2X using `noise-tga` (128x128, identical in all 36 courses) on the second UV set, no texture transform. The course DX stores two global UV arrays (54,589 vertices each); array 1 is the noise UV. `noise-tga` mean x 2 = 0.9537 (measured), which matches the 0.954 average of the earlier research.
Generic model DX files (all 117 parsed) have exactly one UV set and never use slot 2.

### 2.2 What the PS2 data can and cannot give (CONFIRMED_BY_BYTES, `ps2-vertex-fields-turkey3.json`)
- The noise UV is not a planar function of position (least-squares fit residual 1.3 to 1.6 UV units over 2,000 ground vertices) and its edge length ratio to the base UV is 0.257 / 0.537 / 0.938 (p10 / p50 / p90): it is authored per mesh, so it cannot be derived for new geometry.
- The PS2 vertex has an unexplained float pair at +28/+32; it does not equal the PC noise UV or the PC base UV at 16,845 paired vertices (not even modulo 1). Its edge ratio to the base UV is 0.168 / 0.439 / 0.930, the same order as the noise ratios. HYPOTHESIS: this is the PS2 noise UV; UNKNOWN whether it tiles like the PC one.
- Triangles that need replacing are by definition those whose geometry, base texture or UV mapping differs from the PC triangle, so the PC noise UV of a twin cannot be reused for them.

### 2.3 Implemented (smallest reusable solution)
1. Keep the native triangle where it is equivalent (`ps2_terrain.refine`): a PS2 ground triangle with the same XZ footprint, height within 0.01, same base texture name and the same UV (exact or one common integer offset) is not added and its PC twin is not neutralised, so it keeps the native PC material including the noise stage and the PC prelight. Turkey3: of 4,020 position-non-exact PS2 ground triangles, 2,104 are equivalent (398 exact UV, 1,706 integer offset), 1,916 replace (679 geometry, 473 base texture, 17 UV mapping, 747 without a PC footprint). The earlier build replaced all 4,020.
2. Replaced triangles are added as PS2 geometry with the PS2 base texture (PC 128x128 file when the artwork matches), PS2 vertex tint and UV, double-sided for steep faces. They have no noise stage, so their vertex tint is multiplied by the measured mean noise factor 0.9537 (`noise_mean_factor`): average brightness matches the PC ground, the noise detail is absent. This is a measured average, not a shader emulation.
3. 1,402 PC triangles are neutralised (zero-area, the indices point at one vertex); 6 PC triangles near the rock arch stay because no PS2 triangle replaces them.

### 2.4 Experimental option `--ground-detail noise2` (HYPOTHESIS, not default)
`ground_material.two_uv_noise_template()` builds a generic-DX template with a second UV array and slot 2 = `noise-tga` (the rebuilt template is byte-identical through `topology_writer`, validated by the parser); the added ground models then carry the PS2 +28/+32 pair as UV set 1 and a copy of the PC `noise-tga.dxt` in their folder, without the tint. Whether the engine applies the noise stage to a model Egg, and whether the +28/+32 pair is a usable noise UV, are both unproven; the package `t4-terrain-g1-noise2` exists only for a runtime A/B (see `runtime-validation.md`). Its collision tree is byte-identical to the default package.

### 2.5 Not done (and why)
Exact noise parity for replaced triangles needs either a course-DX writer (to put the triangles into native `base_noise` draws; excluded in this phase) or proof about the PS2 noise UV plus engine behaviour for model draws (noise2 A/B). The PS2's own ground noise (subtractive, unfogged, `CommonTextures/NOISE`) is a separate existing option (`GroundDetail=1`) and is not touched.

## 3. Checks on the built package (SYNTHETIC, `package-checks-default.json`, `package-checks-noise2.json`)
21 models parse and validate, every texture slot resolves in its folder, all DXT headers carry the payload CRC; no duplicate Egg names that we added (the only duplicate, `AttractMode`, is in the retail XML); the loose `turkey3.dx` differs from retail only in 2,808 bytes of the local index array (1,402 triangles made degenerate) and the tag100 suffix; no render prefix byte outside the index array changed; no added PS2 ground triangle is coplanar (0.03) with a remaining PC triangle at its centroid (0 of 1,916: no z-fighting from duplicates); all seven object hull brushes are solid at their centroids; tag100 count invariants hold.
