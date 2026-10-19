# TRACK-GROUND1: collision diagnostics (PS2 BSP vs retail tag100 vs patched tag100), Turkey3

Code: `collision_diag.py` (deterministic, no random sampling), tests `test_collision_diag.py`; data `collision-regions.json` (summary, ranking, all 48 regions). The patched tree is the one of the default package `t4-terrain-g1` (loose `turkey3.dx` SHA-256 prefix `6652692e39cb`; the noise2 package has the identical tree). No slab heuristic was extended and no transplant was made in this phase.

## 1. Method (SYNTHETIC tooling over CONFIRMED_BY_BYTES inputs)
- Domain: a fixed 6-unit grid over the PS2 ground bounding box; a column is used when its centre is covered by a PS2 ground triangle (66,684 columns). Grid origin and order are fixed, so a re-run gives the same bytes (two runs over the first 2,500 columns produced identical output files).
- Per column, three exact vertical segment queries from `h_vis + 6` down to `h_vis - 12` (`h_vis` = highest visible PS2 ground height): first solid contact in the PS2 BSP (leaf solidity rule of the PS2 leaf classes), in the retail PC tag100 and in the patched PC tag100. The queries traverse leaves exactly; nothing is inferred from triangle centroids or from visual meshes (the visual height only places the query window).
- Flags: PS2 solid exterior (solid at `h_vis + 3` or a solid query start), PS2 void (no solid anywhere in the window), visible layers (ground triangles at one XZ more than 0.5 apart), overhang (empty at +0.3 above the first PS2 contact and solid again within 8), BSP second surface (empty gap then solid again below the first contact, evaluated for the columns of mismatch regions).
- Classes against the PS2 BSP with tolerance 0.25: `agree`, `missing_support` (patched surface missing or lower: the car sinks or falls), `invisible_block` (patched surface higher or a solid start where the PS2 has none: the car meets an invisible bump), `ps2_exterior`, `ps2_void`.
- Limits: the window caps an invisible-block error at 6.0 (a query that starts inside solid reports exactly 6.0, so such an error is 6.0 or more); a 6-unit grid can miss features narrower than 6 units; only the first contact per column is compared.

## 2. Results (`collision-regions.json`, summary)
| Class | Retail PC tree | Patched PC tree |
|---|---:|---:|
| agree | 38,466 | 39,031 |
| missing_support | 325 | 114 |
| invisible_block | 717 | 363 |
| ps2_exterior (excluded) | 24,244 | 24,244 |
| ps2_void (excluded) | 2,932 | 2,932 |
Flows: 211 missing-support and 354 invisible-block columns became agree, none got worse (`agree` stays `agree`), 114 and 363 remain. Visible ground layers above one: 178 columns; BSP second surface: 2 mismatch regions; overhang from the top surface: 0 columns (the test starts at the top surface, so arches and caves show up as layers and BSP second surfaces instead); columns where the PS2 BSP surface is more than 0.5 away from the visible PS2 height outside the exterior: 39.

### What the classes mean here
- `ps2_exterior` (36 percent of the columns): the PS2 solid shell above the corridor. It is PS2 behaviour, the policy so far is not to port it (`T2-BEHAVIOR.md`); it also hides the real ground collision of those columns, so a corridor-zone transplant must stay clear of it.
- `ps2_void` (2,932 columns, 4.4 percent; six regions of 1,453, 733, 624, 91, 20 and 11 columns, 134 to 239 units from the road): the PS2 BSP has no solid in the whole window although a visible ground mesh exists; the PC has a surface there. This is PS2 behaviour (collision void under visible ground), not a transfer error, and must not be "fixed".
- `invisible_block` (25 regions, 13,068 units2 in total): the patched tree is solid above the PS2 surface. Typical: PC terrain or a PC-only solid higher than the PS2 ground (heights up to the 6.0 cap).
- `missing_support` (23 regions, 4,104 units2): the patched surface is absent or lower than the PS2 one (largest errors 11.98 and 8.7), mostly the carve/fill slabs that were skipped (no PC twin, thicker than 8 units, near-vertical).
- Multilayer / overhang: 178 visible-layer columns and 2 regions with a BSP second surface; they are excluded from candidate regions.

## 3. Regions
48 regions (8-connected, one class each). Large ones: invisible_block 154 columns at (2630, -858), 107 at (3086, -18), 34 at (2628, 499); missing_support 29 at (2553, -866), 22 at (2727, -942). Ineligibility reasons over all regions (a region can have several): not isolated 33, size outside 3 to 60 columns 29, far from the road 6, near a converted object 5, error too small to observe 4, multilayer or BSP second surface 3, unresolved columns (PS2 has no surface) 2.
Eligibility for a controlled experiment: 3 to 60 columns, no unresolved column, no layer/overhang/BSP second surface, at most 80 units from the RaceLine, at least 60 from a converted object, at least 30 from the next mismatch region, mean error at least 0.5. Three regions pass. Ranking puts regions without PS2 exterior or void columns within 36 units first, then orders by a score (isolation + 20 x mean error - columns - 0.5 x road distance).

| Rank | Class | Centre (x, z) | Columns / area | Error mean / max | Road | Isolation | Exterior within 36 | Retail = patched |
|---|---|---|---|---|---:|---:|---|---|
| 1 | invisible_block | (2173.6, 16.5) | 11 / 396 | 0.54 / 1.07 | 58.5 | 252.5 | none (104 agree, 11 block) | yes (slabs did not touch it) |
| 2 | invisible_block | (2318.5, 473.7) | 3 / 108 | 3.72 / 5.22 | 55.4 | 226.9 | 46 exterior columns | yes |
| 3 | invisible_block | (2628.2, 499.2) | 34 / 1,224 | 3.26 / 6.0+ | 44.0 | 43.0 | 16 exterior columns | yes |
Probe positions (x, z, PS2 BSP contact height, retail contact, patched contact) for the ranked regions are in `collision-regions.json` (`ranking[*].columns_table`, `probes`). Examples, rank 1: (2148.5, 25.73) 19.965 / 20.254 / 20.254; (2172.5, 13.73) 18.367 / 19.438 / 19.438; (2196.5, 1.73) 23.505 / 23.787 / 23.787. Rank 2: (2316.5, 469.73) 14.599 / 19.823 / 19.823; (2316.5, 475.73) 16.494 / 20.254 / 20.254.

## 4. Status of findings
- CONFIRMED_BY_BYTES: the three-way surface heights above for every listed column; the class counts; the PS2 void and exterior counts.
- SYNTHETIC: the classification, region and ranking code (tests), determinism of the run.
- HYPOTHESIS: that the PS2 void blocks are intentional PS2 behaviour (they sit far from the road and are bounded by rectangular patches as in the T2 map); that the rank 1 skin of 0.3 to 1.1 units is a PC terrain surface slightly above the PS2 one (heights say so, the cause is not established).
- UNKNOWN: how the vehicle code treats a 1-unit invisible bump in practice (needs the runtime check); whether the plane code of PS2 leaves (not used here) means anything in the PC tree.
