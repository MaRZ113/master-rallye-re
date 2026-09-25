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
