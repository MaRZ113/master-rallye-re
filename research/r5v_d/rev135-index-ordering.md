# Revision 135 vehicle DX index-ordering audit

This report separates exact local/global sequence equality from per-draw oriented topology equivalence.
Build family is not inferred from revision. Directory provenance is retained as a label.

## Summary

- Revision 135 resources parsed: 93
- Exact sequence: 81
- Structurally valid ordering divergence: 12
- Structural failures: 0

## By source set

| Source set | Files | Exact | Order-equivalent | Structural failures |
|---|---:|---:|---:|---:|
| demo-inputs | 15 | 3 | 12 | 0 |
| retail | 78 | 78 | 0 | 0 |

## By directory group

Directory labels organize the supplied files; they do not prove which cooker produced them.

| Source set | Directory group | Files | Exact | Order-equivalent | Structural failures |
|---|---|---:|---:|---:|---:|
| demo-inputs | `9.10.0_Jump` | 3 | 3 | 0 | 0 |
| demo-inputs | `9.10.0_Simmbugghini` | 3 | 0 | 3 | 0 |
| demo-inputs | `9.10.0_Wildcat` | 3 | 0 | 3 | 0 |
| demo-inputs | `9.10.0_dxForester` | 3 | 0 | 3 | 0 |
| demo-inputs | `9.10.0_dxTrooper` | 3 | 0 | 3 | 0 |
| retail | `Astero` | 3 | 3 | 0 | 0 |
| retail | `Bruno` | 3 | 3 | 0 | 0 |
| retail | `ChevyBlazer` | 3 | 3 | 0 | 0 |
| retail | `Forester` | 3 | 3 | 0 | 0 |
| retail | `Frontera` | 3 | 3 | 0 | 0 |
| retail | `IceCream` | 3 | 3 | 0 | 0 |
| retail | `Jump` | 3 | 3 | 0 | 0 |
| retail | `Kamaz` | 3 | 3 | 0 | 0 |
| retail | `Kangoo` | 3 | 3 | 0 | 0 |
| retail | `KiaSportage` | 3 | 3 | 0 | 0 |
| retail | `LandCruiser` | 3 | 3 | 0 | 0 |
| retail | `Mattserati` | 3 | 3 | 0 | 0 |
| retail | `Navara` | 3 | 3 | 0 | 0 |
| retail | `NewRav` | 3 | 3 | 0 | 0 |
| retail | `Pajero` | 3 | 3 | 0 | 0 |
| retail | `Patrol` | 3 | 3 | 0 | 0 |
| retail | `RMonster` | 3 | 3 | 0 | 0 |
| retail | `SeatBuggy` | 3 | 3 | 0 | 0 |
| retail | `Simmbugghini` | 3 | 3 | 0 | 0 |
| retail | `Tata` | 3 | 3 | 0 | 0 |
| retail | `Terrano` | 3 | 3 | 0 | 0 |
| retail | `Ufo` | 2 | 2 | 0 | 0 |
| retail | `WildCat` | 3 | 3 | 0 | 0 |
| retail | `Xtrail` | 3 | 3 | 0 | 0 |
| retail | `forklift` | 3 | 3 | 0 | 0 |
| retail | `megane` | 4 | 4 | 0 | 0 |

## Resources

| Source set | Directory group | Resource | Role | Vertices | Triangles | Draws | Sequence | Topology | Mismatches | First | Index coverage | Collision |
|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---|---|
| demo-inputs | `9.10.0_dxForester` | `!other_research/9.10.0_dxForester/car.dx` | RACE BODY | 2459 | 1864 | 15 | diverged | equal | 5449 | 0x0 | complete-disjoint | 101 |
| demo-inputs | `9.10.0_dxForester` | `!other_research/9.10.0_dxForester/complete.dx` | PRESENTATION | 2649 | 2328 | 15 | diverged | equal | 6644 | 0x0 | complete-disjoint | 102 |
| demo-inputs | `9.10.0_dxForester` | `!other_research/9.10.0_dxForester/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | diverged | equal | 675 | 0x3 | complete-disjoint | 102 |
| demo-inputs | `9.10.0_dxTrooper` | `!other_research/9.10.0_dxTrooper/car.dx` | RACE BODY | 2310 | 1911 | 22 | diverged | equal | 5552 | 0x0 | complete-disjoint | 101 |
| demo-inputs | `9.10.0_dxTrooper` | `!other_research/9.10.0_dxTrooper/complete.dx` | PRESENTATION | 2500 | 2375 | 20 | diverged | equal | 6730 | 0x0 | complete-disjoint | 102 |
| demo-inputs | `9.10.0_dxTrooper` | `!other_research/9.10.0_dxTrooper/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | diverged | equal | 675 | 0x3 | complete-disjoint | 102 |
| demo-inputs | `9.10.0_Jump` | `9.10.0_Jump/car.dx` | RACE BODY | 2361 | 1808 | 22 | exact | equal | 0 | — | complete-disjoint | 101 |
| demo-inputs | `9.10.0_Jump` | `9.10.0_Jump/complete.dx` | PRESENTATION | 2551 | 2272 | 19 | exact | equal | 0 | — | complete-disjoint | 102 |
| demo-inputs | `9.10.0_Jump` | `9.10.0_Jump/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| demo-inputs | `9.10.0_Simmbugghini` | `9.10.0_Simmbugghini/car.dx` | RACE BODY | 2460 | 1916 | 22 | diverged | equal | 5585 | 0x0 | complete-disjoint | 101 |
| demo-inputs | `9.10.0_Simmbugghini` | `9.10.0_Simmbugghini/complete.dx` | PRESENTATION | 2650 | 2380 | 22 | diverged | equal | 6795 | 0x0 | complete-disjoint | 102 |
| demo-inputs | `9.10.0_Simmbugghini` | `9.10.0_Simmbugghini/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | diverged | equal | 675 | 0x3 | complete-disjoint | 102 |
| demo-inputs | `9.10.0_Wildcat` | `9.10.0_Wildcat/car.dx` | RACE BODY | 2687 | 1966 | 21 | diverged | equal | 5730 | 0x0 | complete-disjoint | 101 |
| demo-inputs | `9.10.0_Wildcat` | `9.10.0_Wildcat/complete.dx` | PRESENTATION | 2877 | 2430 | 21 | diverged | equal | 6926 | 0x0 | complete-disjoint | 102 |
| demo-inputs | `9.10.0_Wildcat` | `9.10.0_Wildcat/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | diverged | equal | 675 | 0x3 | complete-disjoint | 102 |
| retail | `Astero` | `Astero/car.dx` | RACE BODY | 2543 | 2021 | 32 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Astero` | `Astero/complete.dx` | PRESENTATION | 2657 | 2423 | 24 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Astero` | `Astero/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Bruno` | `Bruno/car.dx` | RACE BODY | 2455 | 2014 | 21 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Bruno` | `Bruno/complete.dx` | PRESENTATION | 2593 | 2434 | 16 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Bruno` | `Bruno/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `ChevyBlazer` | `ChevyBlazer/car.dx` | RACE BODY | 2713 | 2156 | 36 | exact | equal | 0 | — | complete-disjoint | 101, 102 |
| retail | `ChevyBlazer` | `ChevyBlazer/complete.dx` | PRESENTATION | 2911 | 2566 | 24 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `ChevyBlazer` | `ChevyBlazer/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Forester` | `Forester/car.dx` | RACE BODY | 2573 | 1845 | 27 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Forester` | `Forester/complete.dx` | PRESENTATION | 2713 | 2271 | 17 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Forester` | `Forester/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `forklift` | `forklift/car.dx` | RACE BODY | 1621 | 1037 | 10 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `forklift` | `forklift/complete.dx` | PRESENTATION | 1655 | 1460 | 12 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `forklift` | `forklift/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Frontera` | `Frontera/car.dx` | RACE BODY | 2719 | 2079 | 34 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Frontera` | `Frontera/complete.dx` | PRESENTATION | 2841 | 2491 | 24 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Frontera` | `Frontera/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `IceCream` | `IceCream/car.dx` | RACE BODY | 4174 | 2317 | 29 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `IceCream` | `IceCream/complete.dx` | PRESENTATION | 2417 | 2130 | 23 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `IceCream` | `IceCream/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Jump` | `Jump/car.dx` | RACE BODY | 2401 | 1838 | 30 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Jump` | `Jump/complete.dx` | PRESENTATION | 2551 | 2272 | 19 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Jump` | `Jump/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Kamaz` | `Kamaz/car.dx` | RACE BODY | 2749 | 2464 | 33 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Kamaz` | `Kamaz/complete.dx` | PRESENTATION | 2963 | 2896 | 26 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Kamaz` | `Kamaz/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Kangoo` | `Kangoo/car.dx` | RACE BODY | 2897 | 2165 | 29 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Kangoo` | `Kangoo/complete.dx` | PRESENTATION | 3015 | 2571 | 21 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Kangoo` | `Kangoo/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `KiaSportage` | `KiaSportage/car.dx` | RACE BODY | 2594 | 2323 | 35 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `KiaSportage` | `KiaSportage/complete.dx` | PRESENTATION | 2769 | 2725 | 26 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `KiaSportage` | `KiaSportage/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 4 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `LandCruiser` | `LandCruiser/car.dx` | RACE BODY | 2984 | 2323 | 33 | exact | equal | 0 | — | complete-disjoint | 101, 102 |
| retail | `LandCruiser` | `LandCruiser/complete.dx` | PRESENTATION | 3102 | 2725 | 24 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `LandCruiser` | `LandCruiser/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Mattserati` | `Mattserati/car.dx` | RACE BODY | 2314 | 1872 | 26 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Mattserati` | `Mattserati/complete.dx` | PRESENTATION | 2416 | 2248 | 20 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Mattserati` | `Mattserati/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `megane` | `megane/car.dx` | RACE BODY | 2944 | 2072 | 33 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `megane` | `megane/complete.dx` | PRESENTATION | 3064 | 2477 | 26 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `megane` | `megane/sus.dx` | AUXILIARY | 48 | 48 | 1 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `megane` | `megane/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Navara` | `Navara/car.dx` | RACE BODY | 3248 | 2366 | 37 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Navara` | `Navara/complete.dx` | PRESENTATION | 3397 | 2761 | 26 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Navara` | `Navara/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 4 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `NewRav` | `NewRav/car.dx` | RACE BODY | 2593 | 1972 | 35 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `NewRav` | `NewRav/complete.dx` | PRESENTATION | 2717 | 2382 | 20 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `NewRav` | `NewRav/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Pajero` | `Pajero/car.dx` | RACE BODY | 2852 | 2193 | 33 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Pajero` | `Pajero/complete.dx` | PRESENTATION | 2980 | 2607 | 25 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Pajero` | `Pajero/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Patrol` | `Patrol/car.dx` | RACE BODY | 2557 | 1998 | 34 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Patrol` | `Patrol/complete.dx` | PRESENTATION | 2689 | 2414 | 26 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Patrol` | `Patrol/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `RMonster` | `RMonster/car.dx` | RACE BODY | 2489 | 1842 | 33 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `RMonster` | `RMonster/complete.dx` | PRESENTATION | 2474 | 2165 | 24 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `RMonster` | `RMonster/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `SeatBuggy` | `SeatBuggy/car.dx` | RACE BODY | 2419 | 1879 | 33 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `SeatBuggy` | `SeatBuggy/complete.dx` | PRESENTATION | 2566 | 2302 | 25 | exact | equal | 0 | — | complete-disjoint | 101, 102 |
| retail | `SeatBuggy` | `SeatBuggy/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Simmbugghini` | `Simmbugghini/car.dx` | RACE BODY | 2548 | 2004 | 26 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Simmbugghini` | `Simmbugghini/complete.dx` | PRESENTATION | 2650 | 2380 | 22 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Simmbugghini` | `Simmbugghini/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Tata` | `Tata/car.dx` | RACE BODY | 2272 | 2022 | 39 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Tata` | `Tata/complete.dx` | PRESENTATION | 2482 | 2470 | 31 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Tata` | `Tata/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 4 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Terrano` | `Terrano/car.dx` | RACE BODY | 2800 | 2169 | 33 | exact | equal | 0 | — | complete-disjoint | 101, 102 |
| retail | `Terrano` | `Terrano/complete.dx` | PRESENTATION | 2934 | 2591 | 20 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Terrano` | `Terrano/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Ufo` | `Ufo/car.dx` | RACE BODY | 1537 | 1246 | 12 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Ufo` | `Ufo/complete.dx` | PRESENTATION | 837 | 670 | 6 | exact | equal | 0 | — | complete-disjoint | none |
| retail | `WildCat` | `WildCat/car.dx` | RACE BODY | 2732 | 1998 | 29 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `WildCat` | `WildCat/complete.dx` | PRESENTATION | 2875 | 2430 | 21 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `WildCat` | `WildCat/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 5 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Xtrail` | `Xtrail/car.dx` | RACE BODY | 2348 | 2066 | 32 | exact | equal | 0 | — | complete-disjoint | 101 |
| retail | `Xtrail` | `Xtrail/complete.dx` | PRESENTATION | 2555 | 2487 | 24 | exact | equal | 0 | — | complete-disjoint | 102 |
| retail | `Xtrail` | `Xtrail/wheel.dx` | WHEEL TEMPLATE | 220 | 252 | 4 | exact | equal | 0 | — | complete-disjoint | 102 |

## Interpretation

Only resources with complete disjoint draw coverage and matching per-draw oriented triangle multisets are classified as `VALID_WITH_INDEX_ORDERING_DIVERGENCE`.
A row with a topology mismatch, invalid range, or coverage failure remains structurally invalid.
The cooker identity is not encoded in the revision field; source directory names are evidence labels only.
