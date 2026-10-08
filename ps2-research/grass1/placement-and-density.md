# Placement and quantity

Positions are **generated at camera-region activation** from source triangles.
They are not preauthored instance records and not a once-per-course whole-map
scatter. Frame code calls the updater, but unchanged snapped regions retain
points. A changed region prunes old points and generates newly covered strips.

`357e70` snaps camera X/Z with the original inline integer conversion:
`center = convert(camera/(2*p))*(2*p)`, `p=float32(1.33)`. The stock caller
supplies width 60, producing a square of half-width 30. Independent squared
changes in X, Z **or width** greater than `.1` trigger replenishment; this is
not a summed-distance comparison. First activation offsets the old region.
`2d3540` queries clamped spatial cells, Z then X, and deduplicates triangle IDs.
`357628` clips eligible source triangles against the new/old-region difference
rectangles through `358e98`. Four calls/strip bounds are visible in code.

`356b70` rasterizes the clipped convex polygon in world XZ. The polygon is
provided in original C,B,A direction. Rows derive from `convert(z/p)` and a
second conversion of `(row*p)/p + .1`. Each non-horizontal edge fills a
half-open row interval: increasing Z supplies the right column, decreasing Z
the left. Its first X is the low endpoint X; the step is
`((high.x-low.x)/(high.z-low.z))*p`. There is no fractional-row correction
before the first edge value.

For a row, X starts at `convert(left/p)*p`; the right bound is
`convert(right/p)*p`. While `right-X > float32(.001)`, it emits a sample and
increments X by p with the original float operation order. No area-weighted
triangle choice, barycentric distribution, per-sample RNG or post-jitter
inside-triangle test exists in this path.

For lattice X/Z, the ordered float32 hash is:

```text
h = (X*21.123102 + Z*-34.923172) + (X*(-Z))*184.12938
i = CVT.W.S(h) & 1023
x = X + jitter[i].x*.5
z = Z + jitter[i].y*.5
y = (plane.constant + x*plane.X + z*plane.Z) + category.lift
```

Hash constants are original float words `41a8fc1d/c20bb154/4338211f`.
The table's **second** component affects world Z; the third is unused here.
The original source triangle supplies the height plane via `359318`, using
X/Z/Y rows. The plane helper contains reciprocals of source-origin X/Z;
zero-axis exceptional PS2 arithmetic is not replaced by a convenient modern
solver in the diagnostic. Category lift is shrubs `.4`, grass `.33`.

The exact quantity is the number of loop iterations over the processed
scanline intervals. `1/p² ≈ .5653` points per square coordinate unit is only an
interior lattice asymptote (`MATHEMATICALLY_EQUIVALENT`), not the game's
area-density formula. Edges, clipping, winding, half-open ranges and float
rounding determine actual counts. Grass/shrubs share pitch and count rules;
lift/size and texture differ. Stones does not reach this loop.

Tiny/degenerate sources can fail slope or have no scanline iterations.
World hash jitter can move samples outside source boundaries. Query deduplication
is per source triangle; point append does not deduplicate positions across
adjacent polygons. Thus whole-course counts cannot be obtained by multiplying
area or counting repeated material strings.

Point buffers grow in 1024-aligned groups (`357378`); render records grow in
256-aligned groups (`3597e0`). Initial capacities are not hard limits. Actual
submission groups process at most **30 source points**, emitting at most 30
accepted records. No total fixed point budget or quality-setting writer was
proved; allocation failure policy is outside the bounded algorithm.

`detail_runtime.py` reproduces scanlines only for an explicitly supplied full
original or synthetic polygon. It does **not** implement `358e98` clipping or
the complete camera-history strip lifecycle. Original surfaces used in its
examples therefore carry **SYNTHETIC_FULL_TRIANGLE_ACTIVATION**, not a claim of
original in-game placement/population.
