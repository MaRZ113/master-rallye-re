# Vehicle marker-1339 spatial bounds

Every protected vehicle DX in the 78-resource corpus has a final 44-byte block after the parsed collision tags:

| Offset | Wire field | R4G meaning |
|---|---|---|
| 0 | u32 1339 | marker |
| 4 | 3 x f32 | center |
| 16 | f32 | covering radius/scalar |
| 20 | 3 x f32 | minimum XYZ |
| 32 | 3 x f32 | maximum XYZ |

Across 78/78 resources, extrema from render vertices plus detailed tag101 Representation B vertices agree with stored min/max within 1e-6; center agrees with the midpoint within 1e-5. Radius from the same point set agrees within 1e-5 for 77/78 and is exact at float32 for 57/78 under double-distance then float32 rounding. All 25 wheel resources agree within 1e-5. Representation A's AABB helper is excluded from radius calculation. The AABB half-diagonal and render-only radius fail on many vehicles.

WildCat/car.dx stores a radius about 0.00019169 smaller than the radius of its farthest detailed collision vertex. This is much larger than float32 arithmetic order/rounding. The source block may contain a stale pre-export value, but that explanation is not proven. A targeted executable byte search found one plausible push-1339 site at VA 0x553C07, but its radius calculation was not recoverable from the available text exports. No exact original compiler algorithm is claimed.

The R4G writer preserves the original 44 bytes at zero edit and in the published R4F in-bounds mode. Its explicit recompute mode derives extrema, midpoint and a float32 radius rounded outward enough to contain every selected point. It rejects non-finite or implausibly large coordinates, reparses the whole DX, and permits new geometry outside the donor AABB. A direct recompute of the original corpus matches full footer bytes in 26/78, so byte-exact reproduction is not claimed. See research/r4g/bounds-corpus.json for every error and candidate formula.

Blender topology export chooses recomputation when a compiled vertex exceeds donor min/max or stored sphere coverage. B1 later passed original-game testing: the triangle beyond donor bounds was visible and deformed with damage, while primary collision and physics stayed normal. See ../research/r4g/runtime-results.md.
