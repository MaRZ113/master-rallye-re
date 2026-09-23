# R4B tag-101 geometry analysis

## Base point and scalar

For every one of the 27 finite, non-empty hulls, the single base point equals
the centre of representation A's axis-aligned box. The adjacent scalar equals
the greatest distance from this point to an AABB corner. Maximum absolute
error: `2.0006425671681427e-7` source units.

Result: **CONFIRMED_BY_CORPUS — bounding-sphere radius for representation A.**
The reader/writer code proves only that this is a float; the semantic label is
therefore a corpus result rather than a decompiler-derived fact.

## Representation A

All 27 finite hulls use 8 vertices and 12 triangles, and their unique
coordinate combinations are exactly the corners of their own AABB. Their six
face descriptors have four primary vertices. Face scalars equal the six box
face areas.

Result: **HIGH — AABB/coarse collision representation.** Exact runtime use is
unresolved.

## Representation B

All 27 finite hulls satisfy:

- every triangle edge has exactly two incident triangles;
- Euler characteristic `V - E + F = 2`;
- every triangle plane is supporting within `5e-5` source units;
- triangle count equals `2V - 4`;
- variable face descriptors reconstruct polygon faces over the same vertices.

Result: **HIGH — detailed closed convex polyhedron.** The tolerance is stated
explicitly because float32 construction produces a maximum measured
supporting-plane deviation of about `2.98e-5` in Frontera.

## Face scalar

The scalar following all per-face edge loops equals the 3D polygon area
computed from each descriptor's primary vertex loop:

- representation A: 27/27 resources, max error
  `4.610241433056217e-7`;
- representation B: 27/27 resources, max error
  `4.800475483790478e-7`.

Result: **CONFIRMED_BY_CORPUS — face area.** It is not a plane constant.

## Relationship between A and B

A and B are not a primal/dual pair: counts and reference topology do not show
the inverse vertex/face relationship that hypothesis predicts. The supported
interpretation is coarse AABB helper plus detailed convex hull. The exact
runtime collision algorithm and the role of each nested `geometry_b` point
remain **UNKNOWN**.

## Relationship to `$chull(...)`

Twenty-seven tag-101 resources have at least one same-folder sidecar candidate
containing a literal `$chull(...)`; there are 34 candidates because discovery
retains alternates. R4A already showed exact source-span reconciliation in 24
standard cars and identified SeatBuggy complete as the complete-model outlier.
R4B now locates the compiled non-render structure at tag 101.

This is **HIGH** linkage evidence, not proof that every sidecar `$chull`
triangle maps one-to-one to representation B's compiled triangulation.

## SeatBuggy identical-payload control

The complete serialized tag-101 ranges in `SeatBuggy/car.dx` and
`SeatBuggy/complete.dx` are byte-identical despite living at different file
offsets. Both are 3,760 bytes and hash to
`ea8ddbde932c548fbb09a6557caecb077094843abf228c860b3c28733569d8eb`.

The independently observed successful SeatBuggy complete-to-race substitution
preserved collision and damage. This supplies **HIGH_CONFIDENCE_INFERENCE**
that the compiled tag-101 payload is central to the race-collision binding.
Other resource structure or runtime conditions may still participate, so
sufficiency is not claimed.
