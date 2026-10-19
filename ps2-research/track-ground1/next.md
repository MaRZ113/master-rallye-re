# TRACK-GROUND1: next phase, TRACK-COLL1 (recommendation only, not started)

## Recommended first bounded region
Rank 1 of `collision-regions.json`: class invisible_block, centre (2173.6, 16.5), sampled columns bounded by x 2148.5 to 2196.5 and z 1.73 to 25.73 (11 columns of the 6-unit grid, 396 units2; use the box plus a 6-unit margin, y from 12 below the lowest contact to 3 above the highest). PS2 BSP contact heights 18.4 to 23.5, patched PC heights 0.28 to 1.07 higher (mean 0.54).
Why it suits a controlled PS2 BSP to PC tag100 experiment (all CONFIRMED_BY_BYTES from `collision-diagnostics.md`):
- No PS2 solid exterior or void column within 36 units (104 agree and 11 invisible-block columns around it), so the PS2 leaves in the box describe ground, not the shell the policy excludes.
- Single layer: no visible multilayer column, no overhang, no BSP second surface in its columns, so a carve-and-fill of the box cannot cut a passage or fill one.
- Isolated: 252 units from the next mismatch region, 240 from the nearest converted object, so a mistake or a success is attributable to this box only.
- Reachable: 58 units from the RaceLine, on visible patched ground (about 10 PS2 replacing and 10 neutralised PC ground triangles in the box plus margin, counted on the box 2154 to 2196 by -6 to 36).
- Clean baseline: retail and patched tree give the same contact heights in every column (the slab pass did not touch it), so the transplant is the only change to observe.
Weakness: the error is small (0.3 to 1.1), so a driving impression alone will not decide it; TRACK-COLL1 needs a measurement (see below). Second choice after a pass: rank 3, the mound at (2628, 499) with a 3 to 6+ unit bump, but it has 16 PS2 exterior columns within 36 units and must be clipped away from the shell. Rank 2 (3 columns at (2318, 474), 3.8 to 5.2 units) lies next to 46 exterior columns.

## Proposed TRACK-COLL1 scope (bounded)
1. PS2 leaf polyhedra: from `ps2_bsp` nodes, for the box, collect the solid leaves (plain solid leaf, or payload leaf = leaf cell cut by the payload planes behind them, empty run = solid) and clip each against the box with an incremental convex-polyhedron clipper (the O(n^4) `tag100_tree.polytope` is too slow for 30 plus ancestor planes).
2. Apply with the existing tree API: carve the box (solid to empty), then fill each clipped leaf polyhedron (`Tree.apply_prepared`, normals toward the empty side, valid plane codes taken from the ground plane code on the PC descent path, never `0xFFFFFFFF`).
3. Offline acceptance before any runtime: first-contact heights from the patched tree equal the PS2 BSP within 0.05 on a 2-unit grid inside the box; classification unchanged at deterministic points outside the box (including the 6-unit margin ring); tag100 count invariants; round trip; no plane code that is negative as int32; tree growth reported.
4. Measurement at runtime: read the chassis position (body +0xA0) of the resting human car at the three probe columns through the existing physics observer reading path (read-only, no new hook) and compare with the PS2 contact heights, plus the usual A/B screenshots. This is the part that makes a 1-unit difference decidable.
5. Stop conditions: any crash, any car stuck or launched at the box edge, tree growth above what the box explains.

## Other open items (not part of COLL1)
- Noise detail on replaced ground: needs a course-DX writer or proof about the PS2 +28/+32 pair plus the noise2 A/B result.
- PS2 void blocks and the PS2 exterior shell: policy decisions (port or not), no work until decided.
- Multilayer ground (178 columns, arch near (2610, -844)): needs the exact transplant, not slabs; a later region class.
- All 36 courses: `texture_audit.py`, `collision_diag.py`, `package_checks.py` take the course name or paths; the object lists and the PSM path constants in `ps2_course_objects.py` / `ps2_obj_to_dx.py` are still Turkey3 specific and need a per-course configuration step.
