# DAMAGE2: why 22 fleet cars fall back to Stock after a collision

Status: research only; no renderer change. Data: `surface-audit.json`
(`surface_audit.py`, hash-pinned PS2 assets and PC car.dx).

## Mechanism

When the PC game damages a car, its renderer switches to a private deformed copy
of the PC body (`private_tree`). PORT3 keeps the PS2 CAR model only if every
referenced PS2 vertex can follow that deformation. `car/prepare_contracts.py`
admits a vertex only when an original PC vertex lies within 1e-5, or through two
proven neighbours of an original triangle within 0.005. Only Kia, UFO and the
separate X-Trail route meet this. For the other 22 families
`fleet_damage_registry.hpp` has `eligible=false` and empty mappings, so any
private tree produces `unsupported_private_tree` → native damaged PC body
(Mode 4 reflection on wholly reflective records since fix1).

## Finding: the PS2 body is a different mesh, not crew/interior only

Unresolved PS2 vertices per family. The distance is to the nearest healthy PC
source triangle of the same family; units are model metres (cars are 4–5.4 m long).

| family | referenced | exact | unresolved | ≤5 mm | 5 mm–2 cm | 2–5 cm | >5 cm | >5 cm in root.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Astero | 3121 | 2240 | 881 | 158 | 241 | 385 | 97 | 73 |
| Bruno | 3119 | 2233 | 886 | 208 | 388 | 173 | 117 | 71 |
| ChevyBlazer | 3316 | 2532 | 784 | 118 | 283 | 280 | 103 | 85 |
| Forester | 3135 | 3131 | 4 | 0 | 0 | 4 | 0 | 0 |
| Frontera | 3389 | 2513 | 876 | 210 | 456 | 155 | 55 | 55 |
| IceCream | 3611 | 2191 | 1420 | 326 | 756 | 338 | 0 | 0 |
| Jump | 3168 | 2109 | 1059 | 180 | 351 | 425 | 103 | 103 |
| Kamaz | 3862 | 3201 | 661 | 58 | 158 | 265 | 180 | 150 |
| Kangoo | 3517 | 2906 | 611 | 112 | 298 | 167 | 34 | 34 |
| LandCruiser | 3953 | 2767 | 1186 | 316 | 395 | 437 | 38 | 38 |
| Mattserati | 2912 | 1864 | 1048 | 236 | 490 | 237 | 85 | 69 |
| Navara | 4010 | 3244 | 766 | 81 | 253 | 308 | 124 | 82 |
| NewRav | 3246 | 2436 | 810 | 121 | 329 | 290 | 70 | 70 |
| Pajero | 3497 | 2591 | 906 | 151 | 291 | 400 | 64 | 0 |
| Patrol | 3146 | 2290 | 856 | 300 | 428 | 128 | 0 | 0 |
| RMonster | 3036 | 2153 | 883 | 165 | 277 | 389 | 52 | 52 |
| SeatBuggy | 3017 | 2314 | 703 | 167 | 382 | 150 | 4 | 0 |
| Simmbugghini | 3146 | 2116 | 1030 | 224 | 470 | 320 | 16 | 16 |
| Tata | 3158 | 2527 | 631 | 99 | 177 | 144 | 211 | 192 |
| Terrano | 3467 | 2619 | 848 | 193 | 434 | 219 | 2 | 2 |
| WildCat | 3388 | 2465 | 923 | 130 | 279 | 342 | 172 | 161 |
| megane | 3494 | 2489 | 1005 | 295 | 527 | 163 | 20 | 20 |

About 600–800 unresolved vertices per family sit in `root.0`, the main body. PS2
re-authored the body near the PC surface (mostly 5 mm–5 cm), not just added a
crew. No exact correspondence exists for them, at any tolerance that would not
be an invented alias. That is why the strict policy can never admit these cars.

## Options (decision required)

**A. Surface-bound deformation transfer (proposed).** Exact vertices keep their
exact per-vertex PC deltas, as today. For each unresolved vertex within a bound
(5 cm proposed), an offline generator pins the nearest healthy PC triangle:
source slot, its three native vertex indices and barycentric weights. At runtime
the vertex moves by the weighted sum of those three current-minus-healthy native
deltas. That is the same displacement field the PC body applies to that patch of
surface. Vertices beyond the bound: a component with no exact vertex (PS2-only,
for example crew) stays rigid as in Kia; otherwise the family stays Stock until
reviewed. All runtime identity gates stay unchanged: owner, race/lifetime,
complete source set, per-record material token, loader-winding UV/index, and
agreement of multi-candidate deltas. Output events must state
`deformation_transfer=SURFACE_BARYCENTRIC` and the max pinned distance. They
must not claim identity for those vertices.
Expected coverage at a 5 cm bound: Forester, IceCream, Patrol, Pajero (if its
>5 cm vertices are PS2-only components), Terrano/SeatBuggy after component
review. Others then depend on how their >5 cm root.0 vertices are classified.

**B. Keep the strict policy.** 22 families stay Stock after damage, as now.
Mode 4 continuity on the native damaged body remains.

A is an approximation for the unresolved vertices. It is bounded and reported,
and does not weaken any identity check. Exact pixel or deformation parity
with PS2 is not claimed for those vertices under either option.
