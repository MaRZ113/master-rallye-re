# W2 / W3: PS2 render in the PC course DX (Turkey3 first)

Part of the full PS2 course conversion. Offline only; nothing has been run in the game. Working notes with the format findings: `NOTES.md`.

## Result
- `src/master_rallye/course_render_writer.py` writes the render section of a revision-135 course DX. All 36 retail course DX files round-trip
  byte for byte (`roundtrip_corpus.py`, `roundtrip-corpus.json`). Root tests: `tests/synthetic/test_course_render_writer.py`.
- `build_render.py --course <name> --suffix-from <W1 DX>` builds the render section from the PS2 landscape. For Turkey3:
  - the output holds exactly the PS2 triangle set (40,828; multiset of positions equal);
  - the parser validates the file (complete, disjoint index coverage);
  - every texture slot resolves;
  - 8,650 retail triangles that the PS2 landscape does not have are gone;
  - 60,687 vertices and 1,136 draws (retail: 54,589 and 939).
- Full candidate: `research-output\course-port-turkey3-v1` (PS2 render + PS2 collision + PS2 surface grid + 4 PS2-only textures). Its
  collision was checked again on the packaged file: 50,000 random points and 16,676 columns agree with the PS2 BSP. The RaceTest XML is not part of
  this package (W4); the retail XML stays in use.

## How a PS2 triangle becomes a PC draw
- **Same triangle in PC with the same base texture** (20,959 on Turkey3): normal, colour, both UV sets and the corner order are copied from
  PC, and so are the draw fields.
- **Otherwise** (19,869):
  - **attributes:** PS2 position, PS2 normal, colour = PS2 bytes (+17, +18, +19, +16), PS2 UV as is. PC uses the raw PS2 UV on every shared
    vertex; v1 flipped V by mistake, see `GAME-TEST-1.md`;
  - **corner order:** PC's own order when PC has the same triangle single-sided with another texture; otherwise the face normal points
    against the vertex normals. The normal rule reproduces the PC order on all but one shared single-sided ground triangle of Turkey3. That one
    lies in a fold under a rock, where the visible face looks down; the rule flipped it, PC culled it, and the sky colour showed through
    (seventh test, `GAME-TEST-1.md`). A PS2-only ground triangle whose order runs its shared edges the same way as its neighbours gets both
    sides (11 on 36 courses). PC's order changes 169 triangles on 27 courses.
  - **two-sided materials** (foliage, wires, fences: groups that PC stores twice) get a reversed copy in the same draw.
  - **draw fields:** from the PC draw of the matched triangles of the same PS2 mesh, else from the first PC draw with the same texture tuple,
    else from the PC draw with that tuple and the right alpha class, else from the directive table. The PC draw must have the alpha class
    that the PS2 material asks for (`$alphatest` gives alpha test, `$alphablend` gives blend, neither gives opaque). Before the seventh test,
    the first PC draw with the tuple was taken whatever its alpha class: the ItalyW2 `$alphatest` gate got the opaque gate01 draw. The table was derived from
    1.2 million triangles shared by PS2 and PC on 36 courses (`material_map.py`, `material-map-36.json`, table in `NOTES.md`):
    - `$clamp` gives word +0x14;
    - `$alphatest` / `$alphablend` give the flag bytes;
    - ground with noise gives word +0x24 = 11, a second texture gives 7, wires 1;
    - puddle/water give +0x18 = 1 and +0x24 = 19 (PC has such draws on other courses).
- **Texture names.** The PS2 texture name is checked against the PC file by the TRACK-GROUND1 policy:
  - same image: the PC 128x128 file (62);
  - renamed on PC (2): plating2 is tanky, i2a_planks2 is wood_01;
  - PS2 only, converted (4): brickhouse, caravan, shrubtrig2, water.

  Where PS2 used a different texture on the same geometry (for example `grass to roc2` instead of `grass to roc1`, PS2 shrubs `shrubtrig2`), the
  PS2 texture is kept. That is PS2 content.
- **Vertex alpha.** Copied from PS2, not forced. On Turkey3 every PS2 alpha byte is 255, and on all 36 courses it equals the PC byte on shared
  vertices.
- **Noise UV (second set):**
  - per vertex from a PC noise-draw vertex at the same position (4,343 triangles);
  - if a vertex has none (3,848 triangles), the triangle goes to a noise-less ground draw, using fields PC itself uses for ground without noise;
  - `--noise local` instead takes the planar XZ map of the nearest PC noise triangle. On held-out PC vertices it predicts the PC noise UV
    exactly modulo 1 (NOTES.md). This is EXPERIMENTAL and not in v1; the variant package is `course-port-turkey3-v1-noise-local`.
- **Batches.** The PC batch / sector partition is kept, so tag1500 needs no change.
  - A triangle goes to the batch whose tag1500 sector polygon contains its centroid (Turkey3: 40,796 of 40,828).
  - A triangle outside every sector goes to the root record. This is where PC keeps exactly such triangles: every PC root triangle lies outside
    all sector polygons on France1, FranceM, Turkey2 and Italy2, while 99.98 percent of PC batch triangles lie inside their own sector.
  - On Turkey3 that is 32 triangles at most 2.9 units outside (gaps). On Italy1, whose PC landscape is a different file (`track01`), it is
    2,382 triangles up to 174 units outside the PC sectors.
- **Alpha-blended geometry** (telegraph wires) gets a tag-5 bounding sphere (mean centre, max distance) and a tag-6 sort tree split on polygon
  planes, the structure PC uses (5 clusters on Turkey3).
- **tag1339** (course bounds) is widened downward because PS2 ground goes to y = 11.42 (retail 13.40). Its x/z come from the unchanged sector
  polygons.

## After the first game test
v1 showed three faults: wrong surface record orientation, flipped V, and missing two-sided copies. The causes were measured and fixed (v2);
details in `GAME-TEST-1.md`.

## Limits and open points
- The tag-6 sort trees are built by a simple rule (first polygon's plane, front/back partition, no splitting). Wrong back-to-front order shows only
  on overlapping transparent wires.
- tag1339 max y and radius rule, the rule PC uses to draw sector polygons, and three per-point constants in tag1500 are not decoded. They do not
  change in v1.
- The 3,848 noise-less triangles in v1 (9 percent of the PS2 ground) look flatter than their neighbours (no fine grain). The `--noise local`
  variant gives all of them a noise UV and is the experiment for that.
- PS2 water/puddle draws use the PC puddle fields; whether the PC water shader animates them like PS2 is a runtime question.
- Engine limits are not checked by running the game. Within the retail range: 1,136 draws (retail courses 367 to 1,558, `roundtrip-corpus.json`) and
  60,687 vertices (retail maximum 87,479 on FranceM).

## Files
`build_render.py`, `material_map.py`, `tag1500_probe.py`, `roundtrip_corpus.py`, `test_render1.py` (8 tests, includes the Turkey3 build),
`NOTES.md`, data `material-map-36.json`, `roundtrip-corpus.json`.
