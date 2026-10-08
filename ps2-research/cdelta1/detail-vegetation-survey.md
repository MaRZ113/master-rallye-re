# Detail vegetation survey

Status: material metadata confirmed; spawning and final appearance remain UNKNOWN.

All 36 actual PS2 landscape PSM payloads contain `$detail(grass)`, `$detail(shrubs)` and `$detail(none)`. `$detail(stones)` occurs in the seven France resource families. Turkey_S1 additionally contains the singular `$detail(shrub)` spelling; the executable's known plural interface does not establish whether this spelling is accepted. The 36 canonical PC course TXT sidecars were parsed with the existing Course SDK reader; none contains those `$detail(...)` directives. This is NOT_FOUND_IN_SCANNED_PC_CORPUS for the scanned material names, not proof that the PC executable cannot generate vegetation.

`materials-evidence.json` records per-course source hashes, first byte offsets of distinct strings, and directive presence. A repeated material-like name in a compiled PSM is counted as a printable byte occurrence only. Compiled partitions, duplicated materials and collision metadata may repeat names. These counts do not measure grass blades, bushes, trees, material records or visible instances.

| Representative PS2 landscape | First decoded payload offset | Exact metadata |
| --- | ---: | --- |
| Italy_S1 | 3,618,444 | `$surfacetype(harddirt) $shader(ground) $clamp(u) $detail(grass)Rock LNoise Pass` |
| Italy_S1 | 3,620,533 | `$surfacetype(grass) $shader(ground) $detail(shrubs)$grnd:grass_soft_wetNoise Pass` |
| France1 | 3,504,511 | `$surfacetype(gravel) $clamp(u) $shader(ground) $detail(grass)$grnd(gravel)Noise Pass` |
| France1 | 3,504,771 | `$surfacetype(grass) $shader(ground) $detail(shrubs)$grnd(grass)Noise Pass` |
| France1 | 3,512,235 | `$surfacetype(harddirt) $clamp(u) $shader(ground) $detail(stones)$grnd(harddirt)Noise Pass` |
| Turkey1 | 3,422,127 | `$surfacetype(harddirt) $shader(ground) $clamp(u) $detail(grass)$grnd:surface_grass_hardNoise Pass` |
| Turkey_S1 | 4,447,107 | `$surfacetype(harddirt) $shader(ground) $clamp(u) $detail(shrub)$grnd:grass_hardNoise Pass` |

The matching PC France1 sidecar already has material 3 `$surfacetype(grass) $shader(ground)$grnd(grass)Noise Pass` with grass-tga and noise-tga textures, and material 21 uses grass-treedirt-tga. Italy_S1 material 38 retains grass surface/ground metadata and grass/noise textures; Turkey1 similarly retains surface/ground materials. Thus the delta is an added detail interface on an existing terrain/material family, not merely an extra grass texture filename.

PackFS confirms `PARTICLES/GRASS1.GXI` and `PARTICLES/BUSH1.GXI`; the prior executable audit confirms their string tokens together with `$detail(grass/shrubs/stones/none)`. Course metadata plus this interface is STATIC_INFERENCE for material-driven or procedural detail. The exact consumer, density, culling, random seed, geometry source and wind behavior were not reversed here. Explicit authored placement and generated vegetation must remain separate.

## Additional foliage and thin-geometry renderer leads

`$shader(treeblend)` occurs in 14 PS2 landscape models (France's seven and Turkey's seven except Turkey2); `$shade(treeblend)` also appears in Turkey_M and Turkey_S2. These exact directives were not found in the 36 PC sidecars. PS2 France1 at decoded offset 3,509,264 names `bush $alphatest() $clamp(uv) $shader(treeblend)`, whereas PC France1 material 105 names `bush $alphatest() $clamp(uv) $shader(tree)` and uses bush01-tga. This is DIFFERENTLY_USED, classified RENDERER_SEMANTICS; a higher bush population is UNKNOWN. The spelling `$shade` may be accepted, ignored, or a source typo.

PS2 `$shader(wires)` occurs in 19 models, `$shader(wire)` in three Turkey models, `$alphablend()` in six Turkey models, and `$shader(signtest)` in France_S2/France_W/France_W_flip. PC has existing wire textures and object/metal materials, so absence of those exact directive names is not absence of wires. For example PC Turkey3 material 91 names `telegraph wires $shader(object)`. No wind, weather or reflection-specific material directive was newly established by this scan. These rendering differences may affect substantial scenery, but their visual effect is UNKNOWN until their consumers are reversed.

## Per-landscape authored interface

| Landscape resource family | PS2 detail values | PC detail values |
| --- | --- | --- |
| FRANCE1 | grass, none, shrubs, stones | not found in parsed material names |
| FRANCE2 | grass, none, shrubs, stones | not found in parsed material names |
| FRANCE_M | grass, none, shrubs, stones | not found in parsed material names |
| FRANCE_S1 | grass, none, shrubs, stones | not found in parsed material names |
| FRANCE_S2 | grass, none, shrubs, stones | not found in parsed material names |
| FRANCE_W | grass, none, shrubs, stones | not found in parsed material names |
| FRANCE_W_FLIP | grass, none, shrubs, stones | not found in parsed material names |
| ITALY1 | grass, none, shrubs | not found in parsed material names |
| ITALY2 | grass, none, shrubs | not found in parsed material names |
| ITALY3 | grass, none, shrubs | not found in parsed material names |
| ITALY_M1 | grass, none, shrubs | not found in parsed material names |
| ITALY_M1_FLIP | grass, none, shrubs | not found in parsed material names |
| ITALY_M2 | grass, none, shrubs | not found in parsed material names |
| ITALY_S1 | grass, none, shrubs | not found in parsed material names |
| ITALY_S2 | grass, none, shrubs | not found in parsed material names |
| ITALY_S3 | grass, none, shrubs | not found in parsed material names |
| ITALY_S3_FLIP | grass, none, shrubs | not found in parsed material names |
| ITALY_S4 | grass, none, shrubs | not found in parsed material names |
| ITALY_W1 | grass, none, shrubs | not found in parsed material names |
| ITALY_W2 | grass, none, shrubs | not found in parsed material names |
| SPAIN1 | grass, none, shrubs | not found in parsed material names |
| SPAIN2 | grass, none, shrubs | not found in parsed material names |
| SPAIN_M | grass, none, shrubs | not found in parsed material names |
| SPAIN_S1 | grass, none, shrubs | not found in parsed material names |
| SPAIN_S1_FLIP | grass, none, shrubs | not found in parsed material names |
| SPAIN_S2 | grass, none, shrubs | not found in parsed material names |
| SPAIN_W | grass, none, shrubs | not found in parsed material names |
| SPAIN_W_FLIP | grass, none, shrubs | not found in parsed material names |
| TURKEY1 | grass, none, shrubs | not found in parsed material names |
| TURKEY2 | grass, none, shrubs | not found in parsed material names |
| TURKEY3 | grass, none, shrubs | not found in parsed material names |
| TURKEY_M | grass, none, shrubs | not found in parsed material names |
| TURKEY_S1 | grass, none, shrub, shrubs | not found in parsed material names |
| TURKEY_S2 | grass, none, shrubs | not found in parsed material names |
| TURKEY_S2_FLIP | grass, none, shrubs | not found in parsed material names |
| TURKEY_W | grass, none, shrubs | not found in parsed material names |

Recommended deferred deep phase: PS2-GRASS1. Recover `$detail` consumer, primitive generation and surface selection before choosing asset port, Course SDK extension or D3D8 proxy rendering. The wider CDELTA1 priority is decided in next.md.
