# Deterministic match hierarchy

1. Position agreement separately counts float32 bitwise, numeric and max-coordinate
   tolerance equality. Signed zero is retained by the bitwise bank.
2. Exact triangle candidates use a centroid hash(cell100*vertex epsilon); all27
   neighboring cells are visited. All six corner permutations are compared using
   maximum coordinate error. Raw permutation parity and duplicate multiplicity
   survive in ignored per-face evidence. No one-to-one match is forced.
3. Unmatched faces query a3D AABB hash(cell32 source units). Normal absolute dot
   and maximum target-vertex plane distance gate candidates. Dominant-axis polygon
   subtraction measures union coverage; duplicates/overlap cannot inflate area.
4. Partial coplanar coverage is PARTIAL_SURFACE_OVERLAP. Parallel projected overlap
   outside plane tolerance but inside the near window is GEOMETRY_MODIFIED, a
   quantitative changed-surface candidate, not established common author identity.
5. Remaining PS2/PC surfaces receive bounded unmatched candidate labels. No
   exhaustive relocation/shape search is claimed; alternative groups stay uncertain.

Both directions are computed independently. Candidate IDs are sorted; ties use
error/stable source ID. Spatial budgets fail explicitly without skipping groups.
Output contains every decoded group locally. Compact committed selection covers
all water groups, ordinary anchors and largest representative candidate groups.

Baseline: vertex/plane0.001, abs normal dot>=0.99999, coverage>=0.99999,
near distance1 source unit; area cutoff1e-7. Strict/relaxed values and full counts
are in tolerance-sensitivity.json. Strict can be below one float32 ULP at large
course coordinates; it is a diagnostic, not preferred evidence of extra scenery.
Geometry calculations use host double precision, not PS2 FPU emulation.
