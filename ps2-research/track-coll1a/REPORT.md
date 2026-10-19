# TRACK-COLL1A: regional PS2 BSP to PC tag100 conversion

Prototype on Turkey3, region "rank 1" of TRACK-GROUND1 (centre 2173.6, 16.5). Built on commit 6df05cd. Nothing here has been run in the game.

## What came out

A reusable converter that replaces the collision inside a box of the PC tag100 tree with the solid volume of the PS2 BSP, rebuilt from exact geometry. For Turkey3 rank 1 it produced `research-output\t4-terrain-coll1a` (the TRACK-GROUND1 package with only `turkey3.dx` replaced; `t4-terrain-g1` and `t4-terrain-g1-noise2` are byte-identical to before). The package is not installed anywhere.

The converter reproduces the PS2 collision in the box to within 0.0003 units. It does not change much for the game, because of a finding that matters more than the converter itself:

**The TRACK-GROUND1 diagnosis of this region was wrong.** The patched tree (`t4-terrain-g1`) already agrees with the PS2 BSP in the whole of rank 1: on a 2-unit grid (540 columns) the largest first-contact difference is 0.0003. The 0.3 to 1.1 "invisible bump" came from the diagnostic: the `g1` tree contains solid leaves about 1e-7 thick (a vertical query on a 6-unit grid line touches the edge of a cell), and the query reported them as the first contact. `collision_diag.py` now ignores solid leaves thinner than 1e-4 units (test added) and the cached columns were queried again (`collision-regions-corrected.json`, `ERRATUM-COLL1A.md` in `track-ground1`). The original retail tree really does differ here (376 of 540 columns higher than PS2, mean 0.33, max 1.14); the slab pass of TRACK-GROUND1 had already corrected it.

Effect of the correction on the whole course: patched columns agree 39,061 (was 39,031), invisible-block 331 (363), missing-support 116 (114); regions 37 (48). Old rank 1 and rank 2 disappear. What remains are the 155-column area at (2630, -858), the 107-column area at (3086, -18), the mound at (2628, 499) and a few smaller ones.

## Algorithm

1. **PS2 solid inside a box.** Walk the PS2 BSP carrying a convex cell (`ConvexCell`, faces kept with the plane equation they came from, so clipping never recomputes a plane). Back is the child link, front the sibling link (n.p + d >= 0). A plain solid leaf gives its whole cell, an empty leaf nothing. A payload leaf gives its cell cut by the run planes, solid where n.p + d <= -1e-4 for every plane, and a run with no planes is solid, exactly the rule of the original leaf classes. Rank 1: 45 leaves visited, 37 convex solids, volume 33,217 units³.
2. **Replacement in the PC tree** (`bsp_graft.py`). Walk the PC tree with each node's cell and that cell cut by the box:
   - cell outside the box: untouched;
   - cell entirely inside the box: the whole subtree is replaced by the PS2 BSP restricted to that cell (no box planes needed, the path already bounds it);
   - leaf cell crossing the box: a chain of the box faces that actually cut it. Outside keeps the old leaf class, inside gets the PS2 content restricted to cell and box;
   - plane node crossing the box: kept, children handled recursively.
   New nodes are created with `Tree.new_node`; plane equations are the PS2 float32 planes or the box walls, with PS2 orientation (normal toward the empty side). The PS2 binary nodes are not copied.
3. **Plane codes.** Every new plane carries a non-negative code taken from the PC descent path at the cell (the nearest ground code), never 0xFFFFFFFF, which gives no contact in the engine. PS2 plane codes are not used, their meaning is unknown.
4. **Serialization and rollback.** The existing `Tree.serialize`, which recounts the header words. A failure at any point restores the tree to its previous state (`Snapshot`). Same input gives identical bytes.

I first built the obvious version (carve the box with `apply_brush`, then fill each PS2 solid with `apply_prepared`; `bsp_region.transplant_brush`). It passes the same checks but adds 134,432 nodes (+26 percent, 13.8 to 16.6 MB) because the PC tree is very fragmented near the ground: 1,611 solid and 8,131 empty leaves overlap the box, and each gets a chain. The cell-restricted graft above gives the same collision with 256 changed links, 2,220 allocated nodes, and a net change of -222 reachable nodes (tree 13,767,364 to 13,762,258 bytes). The brush version is kept for comparison.

## Results for rank 1

Box x 2142.5 to 2202.5, y 6.37 to 26.51, z -4.27 to 31.73 (rank 1 bounds with a 6-unit margin, y from 12 below the lowest PS2 contact to 3 above the highest).

| | original PC | TRACK-GROUND1 | candidate |
|---|---|---|---|
| first contact within 0.05 of PS2, 540 columns (2-unit grid) | 164 | 540 | 540 |
| largest / mean first-contact difference | 1.135 / 0.331 | 0.0003 / 0.0000 | 0.0001 / 0.0000 |
| solid/empty mismatches at 6,680 points around the PS2 surface and in random positions | 564 | 0 | 0 |

Further checks on the candidate: 20,000 seeded random points and a 2,160-column grid offset from the construction grid show 0 mismatches (largest first-contact difference 0.00014). 240 horizontal, diagonal and steep rays across the box walls: inside the box the first solid agrees with the PS2 BSP, outside the box the solid intervals equal the TRACK-GROUND1 tree exactly. Outside the box, 72,667 points up to 80 units around it and 139,098 points on shells 0.001 to 1 unit outside each face are classified identically, and every changed link belongs to a node whose cell touches the box. Round trip serialize/parse is identical, header counts hold, the data after the tree and the whole course render section of the DX are byte-identical, the XML and all other package files are identical. Added plane nodes use 36 distinct non-negative codes.

The same conversion on the *retail* tree (the case that really changes something) brings the 0.33 mean error to 0.0000 and passes the same checks, with a 0.52-unit step at the box wall where the retail ground differs from the PS2 ground outside the box. On the TRACK-GROUND1 base that step is 0.07.

## Limitations

- The box is replaced completely. If the box contains PS2 solid exterior (the shell above the corridor) or PS2 void, those are copied too. The mound at (2628, 499) shows it: 9 of its 98 columns are exterior, and a transplant there gives differences of up to 27 units against the old tree because the shell is imported. The converter has no exterior/void mask yet; it needs a policy before it is used there. For that reason only rank 1 was packaged.
- A transplant leaves a step at the box wall wherever the surrounding PC surface differs from the PS2 one. It is invisible on the current base here (0.07) but a bounded region cannot remove it.
- Solid volumes smaller than 1e-4 units³ are dropped (none in rank 1), and the payload test keeps the original 1e-4 inset.
- Surface material identity: PS2 plane codes are unknown, so the whole region uses the ground code found on the PC path. Surfaces that differ in the PS2 data are not distinguished.
- Python speed: about 25 seconds including validation for one 60 × 36 unit box; large regions or whole courses need the walk moved to a faster implementation or more careful pruning.
- Tag100 trees with list blocks are refused by `Tree`, as before.
- No runtime check. This region no longer has a difference to observe on the current base, so an in-game test of this package will mainly confirm that nothing broke.

## Using it on other courses

```
python region_transplant.py --bsp <COURSE>.BSP --retail-dx <retail course dx> --current-dx <dx to patch> \
    --box x0 x1 y0 y1 z0 z1   (or --ranking collision-regions.json --rank N --margin 6) \
    --out <dir> [--base-package <package to copy>] [--dx-relpath DataGx/Course/<Course>/<course>.dx]
```

It writes `transplant-report.json`, `first-contact-grid.json` and, only when every check passes, the candidate DX or package. It depends only on `ps2_bsp.py`, `tag100_tree.py` and `master_rallye` (no renderer code). Tests: `python -X utf8 test_bsp_region.py` (17 tests: raised and lowered terrain, disconnected solids, clipping at the box, fragmented PC trees with cells inside and across the box, agreement with the brush method, codes, rollback, determinism, round trip, and the real Turkey3 rank 1 from both the retail and the TRACK-GROUND1 base).

## Suggested next step

Re-rank the corrected region list and decide the exterior/void policy; the mound at (2628, 499) and the 155-column area at (2630, -858) are the real remaining differences, both near PS2 exterior. A mask that keeps the PC tree for exterior and void columns would let the converter handle them; that was not started.
