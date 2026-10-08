# Source eligibility

`357628` supplies direct executable conditions; original PSM source records
supply their inputs. The executable reads three **position** vectors from
shared model vertices, computes a cross product and normalizes its Y component.
It does not use the authored vertex normal for this decision.

Let `AB=B-A`, `AC=C-A`, `N=AB×AC`, in source triangle order. The exact Y
expression is `AB.z*AC.x - AB.x*AC.z`. If `N·N <= 2^-23`
(`1.1920929e-7`), tested in the original FPU branch, Y is set to zero.
Otherwise `ny = N.y*(1/sqrt(N·N))`. Only **strict `ny > float32(.975)`**
continues. Reversed/downward winding and degenerate triangles fail. Interpreting
the threshold as approximately 12.84° from up is `MATHEMATICALLY_EQUIVALENT`,
not a second slope rule.

The next comparison is the detail ID from proxy `+0x98` against owner grass
and shrubs IDs. Shrubs selects 0, grass 1, all other values leave `-1` and skip
the point producer. Surface-type IDs at proxy `+0x8c` do **not** participate in
these comparisons. Harddirt and gravel can therefore select grass, while a
grass-labeled surface can select shrubs or none.

| Condition | Exact source / code | Consequence | Grade |
|---|---|---|---|
| Model has spatial proxy | Model +2c in 3375a0 | Detail integration is available | CONFIRMED_BY_EXE |
| Camera-region source query | 2d3540 cells using proxy grid | Obtain source triangle/material refs | CONFIRMED_BY_BOTH |
| Triangle winding/near-flat cross | 357628 source indices and positions | ny must be strictly > .975 | CONFIRMED_BY_BOTH |
| Recognized generating category | Proxy +98 vs owner +102c/+1030 | Select grass/shrubs pool only | CONFIRMED_BY_BOTH |
| Non-empty activation intersection | 357628 invokes 358e98, polygon count >2 | Scan clipped polygon | CONFIRMED_BY_EXE |
| Render radial cutoff | 3597e0 integer LUT index <1023 | Emit input record; does not create source points | CONFIRMED_BY_EXE |

The source is **spatial/collision triangles sharing visual positions**, not
visual strip traversal, authored decoration points, reused mesh vertices or a
terrain height-grid sample. Source cells index triangles, not tuft centers.
No separate altitude, collision-surface type, precomputed grass flag or
per-vertex normal condition is found in this bounded generator.
This negative evidence does not classify all world/renderer visibility rules.

Counts in [case evidence](case-evidence.json) use
`FLOAT32_RECONSTRUCTION`; no PS2 FPU equality is asserted. The positive/negative
France1 controls both include many slope-passing triangles, separating category
suppression from slope suppression.
