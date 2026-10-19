# Erratum to TRACK-GROUND1 collision diagnostics (found in TRACK-COLL1A)

`collision_diag.py` counted solid PC leaves about 1e-7 units thick as a first contact. A vertical query that runs along a cell edge (the 6-unit grid hits such edges) reported a false surface up to about 1 unit above the real one. The tool now ignores PC solid leaves thinner than 1e-4 units (`MIN_SOLID`, test `GrazingLeafTests`); `--requery-pc` repeats the PC queries on a cached column file.

Corrected course totals (`../track-coll1a/collision-regions-corrected.json`): patched agree 39,061 (was 39,031), missing_support 116 (114), invisible_block 331 (363), retail agree 38,463; regions 37 (48).

What this changes in the TRACK-GROUND1 documents:
- Rank 1 (2173.6, 16.5) and rank 2 (2318.5, 473.7) are not mismatches in the patched tree. The patched tree agrees with the PS2 BSP there (largest first-contact difference 0.0003 on a 2-unit grid). "Retail = patched in every column" and the 0.28 to 1.07 error in `collision-diagnostics.md` and `next.md` are wrong for rank 1. The original retail tree does differ there, the slab pass fixed it.
- The runtime points 4 to 7 in `runtime-validation.md` therefore compare nothing at rank 1 and 2. Rank 3 (the mound at 2628, 499) is real and is the corrected rank 1.
- Everything else in the TRACK-GROUND1 report (texture parity, material policy, packages) is unaffected.
