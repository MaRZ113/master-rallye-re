# Surface equivalence and limitations

Project candidate triangles into the dominant source-plane coordinate pair using
a local origin to reduce cancellation. Subtract each convex triangle from the
remaining convex fragments. Each cut partitions into outside pieces and a retained
inside piece; the inside is removed. Remaining area divided by source area gives
uncovered fraction. This measures union, not summed pairwise overlap. Explicit
fragment/index budgets reject an oversized job instead of fabricating coverage.

Synthetic opposite diagonals, four-face fans, T-junctions, merged/split coverage,
duplicates, partial/disjoint polygons and vertical planes validate the method.
Parallel surfaces at different heights and sloped/crossed surfaces fail the3D
equivalence gate. A mirrored shape is not silently registered.

SAME_SURFACE_DIFFERENT_TRIANGULATION means directional equivalent surface coverage
at the declared profile despite no corner match. It does not prove a historical
compiler intentionally retriangulated the model: float32 boundary differences,
alternative source records or merged draw groups can also explain it. Full group
extent equivalence requires reciprocal evidence, and no bijection is asserted.
Plane/normal gates are conservative; tiny/sloping targets can remain ambiguous.
Unsigned surface area may include repeated or oppositely wound source records.
