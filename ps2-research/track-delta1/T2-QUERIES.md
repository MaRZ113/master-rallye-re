# T2 queries: PS2 BSP versus PC tag100 on Turkey3 (first G-COLL measurements)

Scripts: `bsp_query.py`, `gcoll_columns.py`, `gcoll_solid_columns.py`, `bsp_orientation.py`; result file `gcoll-columns-turkey3.json`.
Columns are centroids of PS2 visual ground triangles (upward normal, Y up), thinned to at most 1,500 per group. The query is a vertical
first-solid-contact marching from 3 units above to 6 below the visual surface. PS2 solidity follows the engine rule recovered from the ELF
(`T2-BSP-FORMAT.md`). PC uses the first solid leaf of tag100. Heights are differences in the same world frame (identity transform).

## PC tag100 reproduces the visual ground
Points above the visual ground are empty in 98 to 99.7% of samples and points below are solid in 99.3 to 99.9% (heights +30 to -8).
For the 1,605 exact-match ground columns the first solid contact is within 0.05 of the visual surface in all 1,605.

## PS2 versus PC, first-contact height difference
| Column group | Columns | Both hit | Within 0.05 | Within 1.0 | Notes |
|---|---:|---:|---:|---:|---|
| Exact-match ground, within 30 units of the RaceLine | 965 | 965 | 963 (99.8%) | 963 | agree |
| Exact-match ground, beyond 30 units | 691 | 680 | 414 (61%) | 414 | 266 columns: PS2 is solid from 3 units above ground; PC is not |
| Non-exact (PS2-only visual) ground, within 30 | 125 | 125 | 29 | 91 | contact differs by up to about 3 |
| Non-exact ground, beyond 30 | 370 | 370 | 62 | 218 | |

## Solid space off the track
On the exact-match columns where PS2 reports solid space from 3 units above the ground (420 of 2,196 contacts, a larger sample), the median
distance to the RaceLine is 128 units (10th percentile 33, 90th 254) against 15 units (5 and 66) for the other columns; only 36 of the 420 lie
within 30 units of the route. The solid column extends at least 200 units upward for more than half of them (the probe stops at 200).
This reads as PS2 collision that is solid outside the driving corridor, while PC tag100 is open there (PC relies on its limit lists).
It is an observed, quantified difference on Turkey3, not yet cross-checked at runtime. Whether it is an invisible wall, a terrain shell or
an artefact of how the tree encloses unreachable space is UNKNOWN.

## What this means for G-COLL
- Driving corridor ground (within 30 units of the RaceLine, matching visuals): PS2 and PC agree to 0.05 on 99.8% of sampled columns.
- Off-corridor space: PS2 collision differs from PC (solid versus open).
- PS2-only ground (the non-exact visual groups): the collision differs from PC contact heights too, so those surfaces are likely collidable
  extra ground, not decoration. This should be confirmed with the surface-type id and a runtime probe.
- Not covered yet: horizontal rays and convex sweeps along the RaceLine, hull penetration depth for the car and for props, surface-type ids,
  other courses, and the runtime checks on PC and PCSX2 required by the policy. G-COLL stays OPEN; this is the first of its geometric queries.

## Reproduce
    python -X utf8 ps2-research/track-delta1/gcoll_columns.py "D:/Game/Master Rallye PS2" "<PC>/Data.sma_unpacked" "<course-sdk>" ps2-research/data/track-bsp/TURKEY3.BSP
    python -X utf8 ps2-research/track-delta1/gcoll_solid_columns.py <same arguments>

(`TURKEY3.BSP` is extracted into the ignored `ps2-research/data/track-bsp/`; `bsp_census.py` shows how to read it with `tngtool`.)
