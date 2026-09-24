# Source collision directives versus compiled DX

## `$chull(Jump)` numeric case

`demo-9.3.1:DataGx/Vehicles/Jump/car.txt` names `moMesh(Name [$chull(Jump)] Index 1808 Size 64)`. The same-build GXM has 1,872 validated ten-word records; this sidecar range is its final 64 records. Their vector-C index triples refer to 34 unique points. After `(x,y,z) -> (x,z,-y)`, a convex-hull vertex test with a `1e-6` plane tolerance identifies 26 extreme points.

`retail:Data.sma_unpacked/DataGx/Vehicles/Jump/car.dx` tag101 Representation B geometry A has 26 vertices and 48 triangles. Each of the 26 source extreme points has a retail B nearest neighbour within `6.20e-7`, and vice versa. The source point AABB and retail Representation A box bounds differ by at most `4.10e-8` on any axis. The retail tag101 base scalar is `2.394742727`; the maximum base-to-box-corner distance is `2.394742835` (difference about `1.1e-7`). This is **CONFIRMED_BY_CORPUS** numeric correspondence across the named demo and retail resources, with the cross-build caveat.

`demo-8.4.1:DataGx/Vehicles/Jump/car.gxm` has the same sidecar range and 34 unique points, but four of its hull points differ from retail; only 22/26 hull vertices match within `1e-4`. The November source is the closer match. This is evidence of an asset revision, not a fallback from November during September analysis.

The numbers strongly support `$chull` source geometry feeding the compiled convex representation and AABB/radius derivation. They do not prove the exact historical compiler algorithm or runtime collision selection from source names alone.

## `$cylinder` numeric case

The demo Jump complete/wheel source names include `wheel $cylinder_0.766_0.39` and, in complete, variants ending `_0.40`, `_0.41`, and `_0.42`. Both demo-8.4.1 and demo-9.3.1 `Jump/{complete,wheel}.dx` have a structurally parseable tag102 at the 56-byte tail: two float32 values approximately `(0.4, 0.2)`, followed by a recognized 44-byte bounds section. Retail Jump complete/wheel has the same tag102 values.

Therefore the textual numbers do **not** map by direct byte-for-byte numeric equality to tag102. A half-size or rounded compiler rule is plausible (`0.39/2 ≈ 0.195`), but the four source variants and constant compiled values do not identify an exact formula. Keep the transformation **UNKNOWN** until more source-to-DX pairs or loader/compiler evidence are available.
