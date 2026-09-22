# R4A vehicle resource matrix

All paths are relative to the external read-only `DataGx/Vehicles` tree.

## Summary

- Vehicle folders: **26**.
- DX resources: **78**; validated: **78**; failures: **0**.
- `car.dx`: 26; `complete.dx`: 26; `wheel.dx`: 25.
- Car/complete pairs: 26.

## Resource presence

| Vehicle | car | complete | wheel | Other DX | Warnings |
|---|:---:|:---:|:---:|---|---:|
| Astero | yes | yes | yes | — | 0 |
| Bruno | yes | yes | yes | — | 0 |
| ChevyBlazer | yes | yes | yes | — | 1 |
| Forester | yes | yes | yes | — | 0 |
| forklift | yes | yes | yes | — | 0 |
| Frontera | yes | yes | yes | — | 0 |
| IceCream | yes | yes | yes | — | 1 |
| Jump | yes | yes | yes | — | 0 |
| Kamaz | yes | yes | yes | — | 1 |
| Kangoo | yes | yes | yes | — | 0 |
| KiaSportage | yes | yes | yes | — | 1 |
| LandCruiser | yes | yes | yes | — | 0 |
| Mattserati | yes | yes | yes | — | 0 |
| megane | yes | yes | yes | `sus.dx` | 0 |
| Navara | yes | yes | yes | — | 1 |
| NewRav | yes | yes | yes | — | 0 |
| Pajero | yes | yes | yes | — | 1 |
| Patrol | yes | yes | yes | — | 1 |
| RMonster | yes | yes | yes | — | 1 |
| SeatBuggy | yes | yes | yes | — | 1 |
| Simmbugghini | yes | yes | yes | — | 0 |
| Tata | yes | yes | yes | — | 1 |
| Terrano | yes | yes | yes | — | 0 |
| Ufo | yes | yes | — | — | 0 |
| WildCat | yes | yes | yes | — | 0 |
| Xtrail | yes | yes | yes | — | 1 |

## Named and geometry evidence

- Car resources with a literal `$chull(...)` sidecar mesh: 25.
- Complete resources with a literal `$chull(...)` sidecar mesh: 1.
- Car resources with literal crew-associated mesh names: 26.
- Complete resources with literal crew-associated mesh names: 0.
- Complete resources with literal non-spare wheel mesh names: 25.
- Complete resources containing 100% of the separate wheel edge signature: 22.
- Complete resources with a four-copy lower bound for every wheel edge-signature element: 22.
- TXT source triangle spans are retained as diagnostics, but are not treated as compiled-table offsets.
- Car resources whose opaque trailing section starts with raw u32 `101`: 26.
- Car resources where TXT span minus render triangles exactly equals the named `$chull` span: 24.

Counts and names are static evidence; runtime semantics are documented separately.

## Per-resource structure

| Vehicle/resource | Sidecar | V | T | Draws/groups | Tags | UV | Slots | Trailing | AABB min .. max | Warnings |
|---|---|---:|---:|---:|---|---:|---:|---|---|---:|
| `Astero/car.dx` | `car.txt` | 2543 | 2021 | 32/27 | 2,7,8 | 1 | 96 | opaque (5340) | -1.018,-0.229,-2.154 .. 1.018,1.410,2.164 | 0 |
| `Astero/complete.dx` | `complete.txt` | 2657 | 2423 | 24/24 | 2 | 1 | 72 | footer56-bounds (56) | -1.018,-0.001,-2.154 .. 1.018,1.851,2.164 | 0 |
| `Astero/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Bruno/car.dx` | `car.txt` | 2455 | 2014 | 21/19 | 2,7,8 | 1 | 63 | opaque (3948) | -1.095,-0.202,-2.717 .. 1.095,1.393,2.639 | 0 |
| `Bruno/complete.dx` | `complete.txt` | 2593 | 2434 | 16/16 | 2 | 1 | 48 | footer56-bounds (56) | -1.095,-0.001,-2.717 .. 1.095,1.857,2.639 | 0 |
| `Bruno/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.165,-0.468,-0.475 .. 0.165,0.468,0.475 | 0 |
| `ChevyBlazer/car.dx` | `car.txt` | 2713 | 2156 | 36/32 | 2,7,8 | 1 | 108 | opaque (3288) | -1.055,-0.166,-2.476 .. 1.053,1.653,2.138 | 1 |
| `ChevyBlazer/complete.dx` | `complete.txt` | 2911 | 2566 | 24/24 | 2 | 1 | 72 | footer56-bounds (56) | -1.055,-0.010,-2.476 .. 1.053,2.027,2.138 | 0 |
| `ChevyBlazer/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Forester/car.dx` | `car.txt` | 2573 | 1845 | 27/21 | 2,7,8 | 1 | 81 | opaque (4272) | -1.095,-0.132,-2.183 .. 1.098,1.437,2.142 | 0 |
| `Forester/complete.dx` | `complete.txt` | 2713 | 2271 | 17/17 | 2 | 1 | 51 | footer56-bounds (56) | -1.095,-0.002,-2.183 .. 1.098,1.827,2.142 | 0 |
| `Forester/wheel.dx` | `ForesterWheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `forklift/car.dx` | `car.txt` | 1621 | 1037 | 10/10 | 2 | 1 | 30 | opaque (152) | -0.445,-0.085,-0.804 .. 0.444,1.680,1.213 | 0 |
| `forklift/complete.dx` | `complete.txt` | 1655 | 1460 | 12/12 | 2 | 1 | 36 | footer56-bounds (56) | -0.587,-0.011,-0.828 .. 0.583,1.979,1.213 | 0 |
| `forklift/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.118,-0.310,-0.314 .. 0.118,0.310,0.314 | 0 |
| `Frontera/car.dx` | `car.txt` | 2719 | 2079 | 34/28 | 2,7,8 | 1 | 102 | opaque (5280) | -1.104,-0.137,-2.358 .. 1.104,1.471,2.038 | 0 |
| `Frontera/complete.dx` | `complete.txt` | 2841 | 2491 | 24/24 | 2 | 1 | 72 | footer56-bounds (56) | -1.104,0.003,-2.358 .. 1.104,1.859,2.038 | 0 |
| `Frontera/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `IceCream/car.dx` | `car.txt` | 4174 | 2317 | 29/25 | 2,7,8 | 1 | 87 | opaque (3360) | -1.070,-0.004,-2.604 .. 1.071,2.487,1.977 | 1 |
| `IceCream/complete.dx` | `complete.txt` | 2417 | 2130 | 23/23 | 2 | 1 | 69 | footer56-bounds (56) | -1.088,0.005,-2.322 .. 1.089,2.818,2.339 | 0 |
| `IceCream/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.114,-0.300,-0.304 .. 0.114,0.300,0.304 | 0 |
| `Jump/car.dx` | `car.txt` | 2401 | 1838 | 30/25 | 2,7,8 | 1 | 90 | opaque (4956) | -0.965,-0.228,-2.218 .. 0.965,1.348,1.928 | 0 |
| `Jump/complete.dx` | `complete.txt` | 2551 | 2272 | 19/19 | 2 | 1 | 57 | footer56-bounds (56) | -0.965,-0.002,-2.218 .. 0.965,1.799,1.928 | 0 |
| `Jump/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Kamaz/car.dx` | `car.txt` | 2749 | 2464 | 33/29 | 2,7,8 | 1 | 99 | opaque (4680) | -1.570,-0.057,-3.711 .. 1.574,3.052,3.752 | 1 |
| `Kamaz/complete.dx` | `complete.txt` | 2963 | 2896 | 26/26 | 2 | 1 | 78 | footer56-bounds (56) | -1.093,-0.003,-2.447 .. 1.095,2.563,2.725 | 0 |
| `Kamaz/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.239,-0.627,-0.637 .. 0.239,0.627,0.637 | 0 |
| `Kangoo/car.dx` | `car.txt` | 2897 | 2165 | 29/24 | 2,7,8 | 1 | 87 | opaque (4512) | -1.134,-0.184,-2.064 .. 1.134,1.472,2.066 | 0 |
| `Kangoo/complete.dx` | `complete.txt` | 3015 | 2571 | 21/21 | 2 | 1 | 63 | footer56-bounds (56) | -1.134,0.001,-2.064 .. 1.134,1.857,2.066 | 0 |
| `Kangoo/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `KiaSportage/car.dx` | `car.txt` | 2594 | 2323 | 35/31 | 2,7,8 | 1 | 105 | opaque (3336) | -1.113,-0.123,-2.369 .. 1.114,1.635,2.247 | 1 |
| `KiaSportage/complete.dx` | `complete.txt` | 2769 | 2725 | 26/26 | 2 | 1 | 78 | footer56-bounds (56) | -1.113,-0.006,-2.329 .. 1.114,2.013,2.247 | 0 |
| `KiaSportage/wheel.dx` | `wheel.txt` | 220 | 252 | 4/4 | 2 | 1 | 12 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `LandCruiser/car.dx` | `car.txt` | 2984 | 2323 | 33/28 | 2,7,8 | 1 | 99 | opaque (5028) | -1.028,-0.206,-2.455 .. 1.028,1.552,2.038 | 0 |
| `LandCruiser/complete.dx` | `complete.txt` | 3102 | 2725 | 24/24 | 2 | 1 | 72 | footer56-bounds (56) | -1.028,0.002,-2.455 .. 1.028,2.054,2.038 | 0 |
| `LandCruiser/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Mattserati/car.dx` | `car.txt` | 2314 | 1872 | 26/23 | 2,7,8 | 1 | 78 | opaque (4248) | -0.962,-0.280,-1.741 .. 0.962,1.377,1.688 | 0 |
| `Mattserati/complete.dx` | `complete.txt` | 2416 | 2248 | 20/20 | 2 | 1 | 60 | footer56-bounds (56) | -0.962,-0.003,-1.741 .. 0.962,1.864,1.688 | 0 |
| `Mattserati/wheel.dx` | `MattWheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `megane/car.dx` | `car.txt` | 2944 | 2072 | 33/28 | 2,7,8 | 1 | 99 | opaque (3096) | -1.176,-0.246,-2.255 .. 1.176,1.244,1.875 | 0 |
| `megane/complete.dx` | `complete.txt` | 3064 | 2477 | 26/26 | 2 | 1 | 78 | footer56-bounds (56) | -1.176,0.001,-2.255 .. 1.176,1.705,1.875 | 0 |
| `megane/sus.dx` | `sus.txt` | 48 | 48 | 1/1 | 2 | 1 | 3 | opaque (3300) | 0.074,-0.146,-0.466 .. 0.782,0.433,0.040 | 0 |
| `megane/wheel.dx` | `Sbuggywheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Navara/car.dx` | `car.txt` | 3248 | 2366 | 37/32 | 2,7,8 | 1 | 111 | opaque (3276) | -1.009,-0.069,-2.800 .. 1.028,1.542,2.350 | 1 |
| `Navara/complete.dx` | `complete.txt` | 3397 | 2761 | 26/26 | 2 | 1 | 78 | footer56-bounds (56) | -1.009,-0.003,-2.800 .. 1.028,1.935,2.350 | 0 |
| `Navara/wheel.dx` | `wheel.txt` | 220 | 252 | 4/4 | 2 | 1 | 12 | footer56-bounds (56) | -0.146,-0.383,-0.389 .. 0.146,0.383,0.389 | 0 |
| `NewRav/car.dx` | `car.txt` | 2593 | 1972 | 35/29 | 2,7,8 | 1 | 105 | opaque (5400) | -0.971,-0.075,-2.089 .. 0.971,1.372,1.887 | 0 |
| `NewRav/complete.dx` | `complete.txt` | 2717 | 2382 | 20/20 | 2 | 1 | 60 | footer56-bounds (56) | -0.971,-0.004,-2.089 .. 0.971,1.753,1.887 | 0 |
| `NewRav/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Pajero/car.dx` | `Pajero.txt` | 2852 | 2193 | 33/29 | 2,7,8 | 1 | 99 | opaque (5076) | -1.018,-0.182,-2.395 .. 1.018,1.434,1.918 | 1 |
| `Pajero/complete.dx` | `complete.txt` | 2980 | 2607 | 25/25 | 2 | 1 | 75 | footer56-bounds (56) | -1.018,0.003,-2.395 .. 1.018,1.822,1.918 | 0 |
| `Pajero/wheel.dx` | `PajeroWheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Patrol/car.dx` | `car.txt` | 2557 | 1998 | 34/30 | 2,7,8 | 1 | 102 | opaque (5340) | -1.046,-0.270,-2.783 .. 1.046,1.454,2.318 | 1 |
| `Patrol/complete.dx` | `complete.txt` | 2689 | 2414 | 26/26 | 2 | 1 | 78 | footer56-bounds (56) | -1.046,-0.005,-2.783 .. 1.046,1.952,2.318 | 0 |
| `Patrol/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `RMonster/car.dx` | `car.txt` | 2489 | 1842 | 33/28 | 2,7,8 | 1 | 99 | opaque (4308) | -1.038,-0.356,-2.415 .. 1.038,1.383,2.009 | 1 |
| `RMonster/complete.dx` | `complete.txt` | 2474 | 2165 | 24/24 | 2 | 1 | 72 | footer56-bounds (56) | -1.038,-0.003,-2.415 .. 1.038,1.916,2.009 | 0 |
| `RMonster/wheel.dx` | `RMonsterWheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `SeatBuggy/car.dx` | `car.txt` | 2419 | 1879 | 33/29 | 2,7,8 | 1 | 99 | opaque (3804) | -1.176,-0.193,-2.007 .. 1.176,1.222,1.962 | 1 |
| `SeatBuggy/complete.dx` | `complete.txt` | 2566 | 2302 | 25/25 | 2 | 1 | 75 | opaque (3816) | -1.176,0.002,-2.007 .. 1.176,1.608,1.962 | 0 |
| `SeatBuggy/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Simmbugghini/car.dx` | `car.txt` | 2548 | 2004 | 26/23 | 2,7,8 | 1 | 78 | opaque (3864) | -0.962,-0.280,-1.880 .. 0.962,1.240,1.741 | 0 |
| `Simmbugghini/complete.dx` | `complete.txt` | 2650 | 2380 | 22/22 | 2 | 1 | 66 | footer56-bounds (56) | -0.962,-0.001,-1.880 .. 0.962,1.758,1.741 | 0 |
| `Simmbugghini/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Tata/car.dx` | `car.txt` | 2272 | 2022 | 39/35 | 2,7,8 | 1 | 117 | opaque (4308) | -1.023,-0.004,-2.618 .. 1.081,1.650,2.224 | 1 |
| `Tata/complete.dx` | `complete.txt` | 2482 | 2470 | 31/31 | 2 | 1 | 93 | footer56-bounds (56) | -1.023,-0.004,-2.618 .. 1.081,1.944,2.224 | 0 |
| `Tata/wheel.dx` | `wheel.txt` | 220 | 252 | 4/4 | 2 | 1 | 12 | footer56-bounds (56) | -0.146,-0.382,-0.388 .. 0.146,0.382,0.388 | 0 |
| `Terrano/car.dx` | `car.txt` | 2800 | 2169 | 33/28 | 2,7,8 | 1 | 99 | opaque (3612) | -1.043,-0.001,-2.281 .. 1.043,1.606,2.024 | 0 |
| `Terrano/complete.dx` | `complete.txt` | 2934 | 2591 | 20/20 | 2 | 1 | 60 | footer56-bounds (56) | -1.043,0.001,-2.281 .. 1.043,1.866,2.024 | 0 |
| `Terrano/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Ufo/car.dx` | `car.txt` | 1537 | 1246 | 12/9 | 2,7,8 | 1 | 36 | opaque (6600) | -1.500,-0.029,-1.427 .. 1.500,1.653,1.427 | 0 |
| `Ufo/complete.dx` | `complete.txt` | 837 | 670 | 6/6 | 2 | 1 | 18 | opaque (44) | -1.500,0.363,-1.427 .. 1.500,2.208,1.427 | 0 |
| `WildCat/car.dx` | `car.txt` | 2732 | 1998 | 29/24 | 2,7,8 | 1 | 87 | opaque (3360) | -1.028,-0.287,-1.927 .. 1.028,1.355,1.915 | 0 |
| `WildCat/complete.dx` | `complete.txt` | 2875 | 2430 | 21/21 | 2 | 1 | 63 | footer56-bounds (56) | -1.028,-0.005,-1.927 .. 1.028,1.851,1.915 | 0 |
| `WildCat/wheel.dx` | `wheel.txt` | 220 | 252 | 5/5 | 2 | 1 | 15 | footer56-bounds (56) | -0.147,-0.385,-0.391 .. 0.147,0.385,0.391 | 0 |
| `Xtrail/car.dx` | `car.txt` | 2348 | 2066 | 32/28 | 2,7,8 | 1 | 96 | opaque (3984) | -1.157,-0.066,-2.395 .. 1.148,1.632,2.362 | 1 |
| `Xtrail/complete.dx` | `complete.txt` | 2555 | 2487 | 24/24 | 2 | 1 | 72 | footer56-bounds (56) | -1.157,-0.003,-2.220 .. 1.148,2.009,2.536 | 0 |
| `Xtrail/wheel.dx` | `wheel.txt` | 220 | 252 | 4/4 | 2 | 1 | 12 | footer56-bounds (56) | -0.145,-0.381,-0.387 .. 0.145,0.381,0.387 | 0 |
