# Controlled course comparisons

All selected PSMs are freshly decoded through the existing hash-locked PackFS
implementation. PC `.dx` and material sidecars are read through the unmodified
Course SDK at `4244fa0c4d878523c9947f54816bf377cdfb2589`.

| Course | PS2 water-related visual mesh modes | Source triangles | PC comparison |
|---|---|---:|---|
| TURKEY3 | 17 puddle | 745 | 0/745 triangle matches against all 42,237 PC triangles |
| FRANCE1 | 12 puddle,2 water,2 waterfall | 3,586 | 3,586/3,586 matched; 16 PC water-related draws |
| ITALY_S1 | 10 puddle | 1,329 | 1,329/1,329 matched; PC candidates use water |
| TURKEY1 | None | 0 | No local water-related group; zero PC material/texture candidates |
| SPAIN_S2 | 10 puddle,19 water,4 waterfall | 2,058 | Bounded spelling control; PC waterfall material spells waterall |

France1 provides an independent geometric check on the scene decoder and
vertex-control suppression: draw236 matches **182** triangles, draw287 matches
**350**, and all 16 matched draws total 3,586. Maximum matched corner error is
**0.00008010864**; all 2,264 PS2 water-related XYZ positions match PC vertices.
Unsigned PS2/PC candidate areas are **320743.52032646 / 320743.52018935**.
The complete draw-count map is committed in `case-evidence.json`.

Italy_S1's 10 source groups yield 877 distinct XYZ positions and two diagnostic
components (823 and506 triangles). Every face and position matches a PC water
candidate; maximum corner error **0.00004577637**. Areas are
**37786.22693236 / 37786.22683052**. This supports material reinterpretation on
shared content, not an additional-geometry explanation for all PS2 puddles.

Turkey1 has 1,034 visual mesh records but no recognized water/puddle/waterfall
group. Its 1,295 PC draws likewise have no name-based water candidate. This
is a local negative control. Common resources may be globally preloaded;
absence of local metadata does not prove that `WATERSURFACE2` is never loaded
or that every conceivable water effect is absent.

Spain_S2 confirms the literal cross-platform spellings: PS2 waterfall,
PC `$shader(waterall) $scroll(v,+1)`. The PS2 ELF registers **both** names,
so its waterall acceptance is executable evidence, not silent normalization.
The PS2 controls contain 33 water-related groups. Their source count2,058
differs from the bounded PC candidate count1,926 despite nearly equal unsigned
area. A full Spain correspondence or tiny-triangle/LOD investigation is outside
this spelling control; that difference is not classified as extra water bodies.

No equal-depth 36-course visual reconstruction was performed. CDELTA1's
36-course presence counts remain metadata-presence facts and are not promoted
to mesh, water-body or runtime-draw counts.
