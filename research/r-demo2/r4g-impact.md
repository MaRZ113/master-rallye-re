# R4G implications from original cooker evidence

- **Bounds:** the shipped and regenerated 9.3.1 marker-1339 bounds differ by float32-scale values. R4G should target safe enclosing bounds and runtime behavior, not historical byte identity. The runtime-visible 9.3.1 source-edit differential confirms the original cooker updated marker-1339 center/radius/maximum when one render position moved. The existing R4G conservative `compute_bounds1339` follows the same semantic policy. On the custom DX positions plus unchanged tag101-B, its center and extrema match the cooker output and its radius is only `2.384185791015625e-7` larger; complete 44-byte identity is absent and should not be the SDK target. This is a read-only comparison, not a retail writer change.
- **Collision:** 9.3.1 `$chull` source maps numerically to regenerated tag101 B, and source triangle triples are retriangulated. The original cooker can become an oracle for future controlled edits. The crashing hull candidate prohibits treating source position edits alone as safe.
- **Normals:** original-vs-regenerated normal differences are tiny, but the precise normal algorithm is unknown. The baseline-vs-modified regeneration now shows every normal byte unchanged for one 0.15-unit visible position edit; do not infer a universal normal rule from one vertex. No R4G normal-policy change is justified.
- **Topology/materials:** render local/global index arrays and raw draw/material bytes are identical in the current pair. These sections also remain byte-identical in the controlled visible source edit, supporting stable ownership/topology for this one original-cooker mapping. It is not a general cooker guarantee or a reason to rewrite the retail draw grammar.
- **Vehicle SDK:** the existing runtime-confirmed retail R4G writer remains unchanged. Source-era cooker output should inform later semantic validation; byte-level DX noise and unresolved secondary descriptor ordering should not become automatic SDK rewrite targets.

Development-era course GXM may later serve as an original compiler oracle for R5T. This phase does not parse or modify course resources.

## What the original cooker changes mean for R4G

- Treat generated DX as the source→compiled semantic oracle, not a historical-byte template. Fixed-source 9.3.1 rebuild A/B is byte-identical, while shipped historical DX is not.
- Bounds are demonstrably cooker-derived: the safe visible edit recalculated marker-1339 center/radius/maximum.
- Tag101 is demonstrably derived from same-build `$chull` source geometry, with point mapping and cooker retriangulation. Source-only hull translation is unsafe in the tested runtime.
- Runtime explicitly writes compiled DX then reopens it through the normal reader; future SDK output comparisons should use this persistent compiled boundary.
- The controlled position differential preserved normals and all draw/index/collision bytes. This is one safe edit, not a universal compiler contract.

These findings do not start or alter R4G implementation.

## R-DEMO2.2 collision bounds refinement

A four-vehicle 9.3.1 comparison found that Rep-A is an 8-corner box with extrema matching the mapped hull source/Rep-B extrema to float32-scale error, and the tag101 base scalar is exactly reproduced as a float32 radius from the tag101 base center to a Rep-A corner. Marker-1339 comparisons reject render-only and Rep-B-only bounds sets; render positions plus tag101-B reproduce the stored block exactly for Jump and within one float32 ULP for NewRav, Tata and regenerated Trooper. The evidence sharpens the semantic comparison only; no R4G code was changed. It does not justify treating a source `$chull` translation as safe or imply that a hull-only edit updates marker-1339.

## R-DEMO2.9 controlled collision-oracle update

The original 9.3.1 Trooper cooker pair now includes baseline A/B and a generated +0.10-X `$chull` candidate. A/B are byte-identical. The controlled candidate changes tag101 Rep B by +0.10 X with core connectivity preserved, and moves the Rep-A box accordingly. Marker-1339 min/max and center match the render-plus-Rep-B point-set formula within one float32 ULP; positive X changes from render-dominated to collision-dominated while negative X stays render-dominated. Jump, NewRav and Tata controls reproduce min/max and center exactly; stored radii equal nearest float32 rounding exactly, while the Trooper radius is one ULP lower than the direct recomputation.

This strengthens the existing bounds policy from corpus association to **CONFIRMED_BY_CONTROLLED_ORACLE** for the tested Trooper pair and **CORPUS_SUPPORTED** across four 9.3.1 assets. `compute_bounds1339` remains an outward, enclosing policy and may be one ULP above a stored radius. No production code changed. The source-to-Rep-B hull algorithm and secondary face descriptor generation remain unresolved; this result supports bounds recomputation when detailed Rep B is already available, not a full source-to-DX cooker.
