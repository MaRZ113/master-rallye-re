# R4A car.dx versus complete.dx

This comparison is generated from the canonical parser and structural TXT evidence.
Positive deltas mean `complete.dx` contains more than `car.dx`.

## Corpus classification

- **CONSISTENT_ACROSS_CORPUS:** all 26 pairs exist; every car trailing section is opaque and starts with raw u32 `101`; every complete uses tag 2 only; every complete has no literal crew mesh name.
- **COMMON:** 25/26 cars use tags 2/7/8; 25/26 complete files have named embedded wheels; 24/26 complete files have more triangles; 23/26 have more vertices; 25/26 have fewer draws.
- **VEHICLE_SPECIFIC:** forklift has tag 2 only and two more complete draws; IceCream and Ufo complete files have fewer triangles; IceCream, RMonster, and Ufo complete files have fewer vertices; SeatBuggy complete retains `$chull(Seatbuggy)` and trailing marker `101`.
- **UNKNOWN:** control-word semantics and the exact structures stored after raw trailing marker `101`.

## Pair matrix

| Vehicle | ΔV | ΔT | Δdraw | Car tags | Complete tags | Car crew | Complete wheels | Car hull | Complete hull | Wheel signature |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|---|
| Astero | 114 | 402 | -8 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| Bruno | 138 | 420 | -5 | 2,7,8 | 2 | 6 | 5 | 1 | 0 | 1.000; min×4 |
| ChevyBlazer | 198 | 410 | -12 | 2,7,8 | 2 | 6 | 5 | 1 | 0 | 1.000; min×4 |
| Forester | 140 | 426 | -10 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| forklift | 34 | 423 | 2 | 2 | 2 | 2 | 4 | 0 | 0 | 1.000; min×4 |
| Frontera | 122 | 412 | -10 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| IceCream | -1757 | -187 | -6 | 2,7,8 | 2 | 3 | 4 | 1 | 0 | 0.000; min×0 |
| Jump | 150 | 434 | -11 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| Kamaz | 214 | 432 | -7 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 0.000; min×0 |
| Kangoo | 118 | 406 | -8 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| KiaSportage | 175 | 402 | -9 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| LandCruiser | 118 | 402 | -9 | 2,7,8 | 2 | 6 | 5 | 1 | 0 | 1.000; min×4 |
| Mattserati | 102 | 376 | -6 | 2,7,8 | 2 | 6 | 5 | 1 | 0 | 1.000; min×4 |
| megane | 120 | 405 | -7 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| Navara | 149 | 395 | -11 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 0.000; min×0 |
| NewRav | 124 | 410 | -15 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| Pajero | 128 | 414 | -8 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| Patrol | 132 | 416 | -8 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| RMonster | -15 | 323 | -9 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| SeatBuggy | 147 | 423 | -8 | 2,7,8 | 2 | 6 | 4 | 1 | 1 | 1.000; min×4 |
| Simmbugghini | 102 | 376 | -4 | 2,7,8 | 2 | 6 | 5 | 1 | 0 | 1.000; min×4 |
| Tata | 210 | 448 | -8 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| Terrano | 134 | 422 | -13 | 2,7,8 | 2 | 6 | 5 | 1 | 0 | 1.000; min×5 |
| Ufo | -700 | -576 | -6 | 2,7,8 | 2 | 1 | 0 | 1 | 0 | n/a |
| WildCat | 143 | 432 | -8 | 2,7,8 | 2 | 6 | 4 | 1 | 0 | 1.000; min×4 |
| Xtrail | 207 | 421 | -8 | 2,7,8 | 2 | 6 | 5 | 1 | 0 | 1.000; min×4 |

## Interpretation boundaries

`complete.dx` is not simply a higher-detail `car.dx`: it normally adds four presentation wheels while omitting crew, collision-hull source content, and tag-7/tag-8 state groups. Conversely, car commonly has more draws despite fewer triangles because it retains runtime-switchable structures.

The wheel signature is a quantized multiset of triangle edge lengths. It is invariant under rigid transforms and reflection. It supports repeated geometry, but it is not a byte-level identity proof and does not assign individual compiled triangles to TXT source spans.
