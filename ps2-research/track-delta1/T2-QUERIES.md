# T2 queries: PS2 BSP versus PC tag100 on Turkey3 ground (first G-COLL measurements)

Scripts: `bsp_query.py` (classify point, segment traversal, PS2 polygon hits), `bsp_orientation.py`, `bsp_ps2_ray_check.py`,
`gcoll_columns.py`. Columns are centroids of PS2 visual ground triangles with upward normal (Y up). Heights are relative to the visual
surface; "first contact" marches down from 3 units above to 6 below.

## PC tag100 is a clean solid/empty model of the visual ground
| Height above visual ground | Empty | Solid |
|---|---:|---:|
| +30 | 99.7% | 0.3% |
| +8 | 98.3% | 1.7% |
| +0.3 | 98.1% | 1.9% |
| -0.3 | 0.7% | 99.3% |
| -8 | 0.1% | 99.9% |

On the 1,605 columns of ground triangles that match PC visuals exactly, the first solid contact lies within 0.05 of the visual surface on
all 1,605 (100%). So a vertical first-contact query on tag100 reproduces the PC ground height. (EVIDENCE: measured, `gcoll_columns.py`.)

## PS2 BSP: not yet reproduced
With the same query and the rule "solid leaf, or a polygon hit in a payload leaf", the PS2 first contact is within 0.05 of the visual
surface on 790 of 1,656 exact-match columns (48%). Against PC on the same columns: 798 of 1,605 within 0.05, 937 within 0.25, 1,145 within 1.0;
10% of columns differ by -0.6 or more and 10% by +3.0 (the start of the ray: PS2 reports solid at the top of the column).
Non-exact (candidate extra) ground columns: PS2 within 0.05 of visual on 171 of 495, PC on 72 of 477.
Reading: either the payload-leaf semantics are incomplete (likely, see T2-BSP-FORMAT.md) or the PS2 collision genuinely differs from its
visual surface in many places. The data do not yet separate these two.

## What this means for G-COLL
- The PC side of the gate is ready: tag100 first contact reproduces the ground to 0.05 where visuals match.
- The PS2 side needs the engine's own tree walk (ELF) before any agreement or disagreement can be called a physics difference.
- Until then no claim that PS2 and PC collision match or differ is supported; G-COLL stays OPEN.

## Reproduce
    python -X utf8 ps2-research/track-delta1/gcoll_columns.py "D:/Game/Master Rallye PS2" "<PC>/Data.sma_unpacked" "<course-sdk>" ps2-research/data/track-bsp/TURKEY3.BSP

(`TURKEY3.BSP` is extracted locally by `bsp_census.py`'s PackFS reader into the ignored `ps2-research/data/track-bsp/`.)
