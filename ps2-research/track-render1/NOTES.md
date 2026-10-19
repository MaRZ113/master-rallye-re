# W2 / W3 working notes: course DX render section and its dependent structures

Status: research and writer groundwork. Nothing here has been run in the game.

## Writer (step 1, done)
`src/master_rallye/course_render_writer.py` reads a course DX into plain dataclasses (vertex arrays, local u16 indices, root records, batches of
draws and containers, raw suffix) and writes it back. `roundtrip_corpus.py`: all 36 retail course DX files come back byte for byte
(`roundtrip-corpus.json`). On write it recounts container child counts and checks that index ranges are inside their vertex ranges, do not
overlap, and cover the whole index array.

## What the render section contains (Turkey3, checked on the corpus where noted)
- 54,589 vertices, 2 UV sets (base, noise), 126,711 local indices, one root tag-4 record without children, 220 batches (153 empty), 939 draws.
- **Batches are spatial clusters.** Each non-empty batch covers a 100 to 450 unit XZ area.
- **Containers:**
  - tag 5 holds a bounding sphere of its subtree: centre = mean of the subtree's index-referenced vertices, radius = max distance. This is exact on
    one of three checked subtrees; on the others the centre is ~0.7 off, but the sphere still contains all vertices.
  - tag 6 holds a sort plane (unit normal, d) with two children: one child lies on the plane (its polygon), the other in front of it. This is a
    back-to-front BSP for alpha-blended geometry.
  - tag 1 is a plain group.
  - In Turkey3 only the alpha-blended telegraph wires and one fence gate sit under tag 5/6. Every other draw is a top-level tag-2 record of a batch.
- **tag1500 (after tag1400) is the sector table.** Grammar checked on 36/36 courses (consumed exactly, `tag1500_probe.py`):
  `u32 1500, u32 S, per sector: u32 n, n x (f32 x, f32, f32 z, f32, f32, f32, u32 link), u32 a, a x u32 sector id`.
  - S = batches + 1 = the first control word of the root tag-4 record.
  - Sector i's polygon (world XZ) is the outline of render batch i-1. Sector 0 belongs to the root.
  - `link` is the neighbouring sector across that polygon edge, or 0xFFFFFFFF. The id list is the sector itself plus the sectors it sees or
    neighbours. This is consistent with a portal / visibility list per sector.
  - The three middle floats are constants per course family (0.392 = 100/255, 0.784, 0.588; probably colours of a debug or map overlay). Their
    meaning is unknown.
- **tag1339 (between the tag100 tree and tag1400) is the course bounds.**
  - x/z min/max equal the bounding box of all sector polygon points, min y the lowest render vertex, centre the middle of min/max.
  - The source of max y (634.8 on Turkey3) and the radius rule are not known yet.

## Consequence for W2 (PS2 render in the PC course DX)
Keep the PC batch and sector partition and put every PS2 draw into the batch whose sector polygon contains it. Then tag1500 and tag1339 x/z stay
valid, and that is checked per triangle, not assumed. Triangles outside every sector polygon go to the root record. PC does the same: all root
triangles of France1, FranceM, Turkey2 and Italy2 lie outside every sector, and 99.98 percent of batch triangles lie inside their own sector.
For draws:
- tag 5 spheres are recomputed from the new vertices (mean + max distance, always containing);
- tag 6 sort trees are reused where the alpha-blended PS2 geometry equals the PC one, and built from polygon planes otherwise;
- tag1339 is kept unless the new vertices leave it, then extended.

## Draw fields from PS2 material directives (W3, `material_map.py`, Turkey3; all 36 courses in `material-map-36.json`)
Derived from 28,443 triangles shared by PS2 and PC Turkey3. Every group maps to one combination; exceptions are under 0.1 percent.
| PS2 directives | flags +0x20 | w14 | w24 | slots | sorted |
|---|---|---|---|---|---|
| shader(ground) + noise texture | 00 00 01 01 | clamp: none 1, u 2, v 4, uv 0 | 11 | (base, Null, noise-tga) | no |
| shader(ground) without noise | 00 00 01 01 | 1 | 3 | (base, Null, Null) | no |
| shader(object) / sign / metal | 00 00 01 01 | by $clamp as above | 3; 7 when slot 1 holds a second texture (metal: whitepaint, aluminium) | (base, Null/second, Null) | no |
| $alphatest + shader(treeblend / tree) | 01 01 01 01 | by $clamp | 3 | (base, Null, Null) | no |
| $alphablend + shader(wires) | 01 00 00 01 | by $clamp | 1 | (base, Null, Null) | yes (tag 5/6) |
| shader(tree) fence without alphatest | 01 00 01 01 | 1 | 7 | (base, aluminium-tga, Null) | yes |
Byte meaning (docs/formats/dx.md, vehicle research): byte0 alpha enable, byte1 alpha-test selector, byte2 vertex diffuse, byte3 source UV.
Words +0x18 = 0 and f32 +0x1C = 1.0 in every Turkey3 draw.

Vertex alpha: the PS2 colour word byte at +16 is 255 on every Turkey3 vertex, ground, foliage, wires and puddles included, and equals the PC
colour byte 3 on every shared vertex. Rule: PC colour = PS2 bytes (+17, +18, +19, +16). The byte is copied, not forced to 255.

## Open
- tag1339 max y and radius rule; the rule that draws sector polygons; meaning of the three per-point constants of tag1500.
- PS2-only materials without a PC example (puddle, alphatest object): the table above gives the fields by directive; the puddle shader has no
  PC course counterpart (PS2OBJ01 overlay remains the route for water).
- Noise UV for PS2 ground triangles without a PC twin. A global affine fit base UV -> noise UV per texture is poor: median error 2.5 UV, so it
  was rejected. The PC noise UV is a planar XZ projection per mesh: the XZ map of the nearest other PC noise triangle predicts the PC noise UV of
  held-out vertices exactly modulo 1 (median, p75 and p90 error 0.0 over 1,315 Turkey3 samples; the earlier "not planar" finding of TRACK-GROUND1
  ignored the wrap). `build_render.py --noise local` uses it. It stays EXPERIMENTAL because new PS2 geometry is an extrapolation.
