# LOD0 versus LOD1 (GT3 sb0097 `model0`) - structure and what V-MESH4.1 does with it

Numbers: `reports/lod-comparison.json` of the V-MESH4.1 build (areas in target-frame m2 after the 1.163 scale). LOD1 is classified with the
V-MESH4 rules, LOD0 with the content-driven classifier.

| | LOD1 | LOD0 |
|---|---|---|
| triangles / positions | 2263 / 3289 | 3435 / 4849 |
| objects / materials (with texture file) | 24 / 41 (39) | 25 / 46 (44) |
| faces with UV / with normals | 1335 / 2047 | 2007 / 3114 |
| wheel openings | none (alpha cut-outs on solid panels) | real openings with wheel-house tubes |
| body triangles whose centroid lies in the four arch discs (tyre + 3 cm) | 12 triangles, 1.163 m2 (to be cut) | 52 triangles, 0.232 m2 (liner surfaces; no body panel) |
| paint / black trim | 618 / 293 | 1006 / 452 |
| glazing panes (translucent dark Mat6) | 38 (`Mat6_Tex10`) | 44 (`Mat6_Tex37`) |
| head lamp / tail lamp | 102 / 32 | 104 / 38 |
| cabin shell (textured Mat-1) | 178 | 277 |
| excluded: env-map reflection shells | 928 | 1428 |
| excluded: lit tail-lamp duplicates / untextured shells | 36 / 38 | 42 / 44 |
| thin 25 %-alpha glass-strip overlay material | `Mat4_Tex5`, 80 tris | `Mat6_Tex41`, 114 tris |
| texture index numbering | per LOD | per LOD (not comparable) |

## Per source class: preserved, excluded, remapped (LOD0)

| Source | Triangles | Disposition | Donor draw (car / complete) |
|---|---|---|---|
| paint class (`Mat1`, incl. arch panels, wing, mirrors) | 1006 emitted (+84 unsupported overlays kept) | preserved, source vertices unchanged | paint 3 / 3 |
| trim (`Mat6`, wheel-house tubes, underbody, vents) | 452 emitted | preserved | black 9 / 9 |
| translucent dark pane (`Mat6_Tex37`) | 44 | remapped to the alpha-blended glass draw | 35 / 24 |
| front-corner lamp units, cut-out lens | 104 | remapped | head lamp 25 / 25 |
| `*tail_lamp_off` | 38 | remapped | 24 / 16 |
| textured `Mat-1` cabin shell | 277 | preserved, shrunk 3 cm inside the paint shell | 0 / 0 |
| mostly-transparent overlay on another surface (decals, strips, vents) | 166 | excluded (recorded with UVs in `dropped-overlays.json`) | - |
| `*reflection*` env-map shells | 1428 | excluded (GT environment-mapping duplicates) | - |
| `*_tail_lamp_on` lit duplicates | 42 | excluded | - |
| untextured `Mat-1` duplicate shell | 44 | excluded | - |

Emitted: 1755 triangles per file (3435 - 1514 excluded - 166 dropped). Unused donor draws are the same hidden fillers as before.

## Why not simply reuse the LOD1 rules

* LOD1 rules identified window panes, head lamps and the cabin shell by *material index* (`Mat6_Tex10`, `Tex26-28`, `Mat-1_Tex35`);
  those indices mean something else in LOD0.
* "Drop mostly-transparent materials" is correct for LOD1's small decals but would delete LOD0 surfaces that exist only through such
  materials; the support test replaces it.
* "Carve texture cut-outs at the wheels" and "analytic arch cut" are unnecessary and would damage the source arches.
