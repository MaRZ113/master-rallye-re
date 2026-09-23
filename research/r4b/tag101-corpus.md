# R4B tag-101 vehicle corpus

Generated from the canonical bounds-checked parser over external read-only vehicle assets.

## Summary

- DX resources: **78**; parsed: **78**; failed: **0**.
- Tag 100 / 101 / 102: **0 / 28 / 53**.
- Tag-101 validated / validation-failed: **27 / 1**; non-empty PC-style hulls: **27**.
- Base 1v/0t: **28**; representation-A AABB: **27**.
- Base scalar equals center-to-AABB-corner radius: **27/27**.
- Representation-B closed / Euler=2 / convex: **27 / 27 / 27**.
- Face scalar equals polygon area, A/B: **27 / 27**.

Forklift is retained as `STATIC_FORMAT_ONLY_OUTLIER`, not PC runtime evidence. Its tag-101 boundary parses exactly, but nine stored coordinate components are non-finite, so it is the one validation-failed tag-101 resource.

## Tag-101 resources

| Resource | Bytes | Base | Scalar | A V/T/E/F | B V/T/E/F | Remaining | Evidence |
|---|---:|---|---:|---|---|---:|---|
| `Astero/car.dx` | 5296 | 1/0 | 2.51602 | 8/12/12/6 | 28/52/67/41 | 44 | PC_VEHICLE_CORPUS |
| `Bruno/car.dx` | 3904 | 1/0 | 2.98223 | 8/12/12/6 | 22/40/45/25 | 44 | PC_VEHICLE_CORPUS |
| `ChevyBlazer/car.dx` | 3232 | 1/0 | 2.69501 | 8/12/12/6 | 16/28/35/21 | 44 | PC_VEHICLE_CORPUS |
| `Forester/car.dx` | 4228 | 1/0 | 2.48962 | 8/12/12/6 | 24/44/50/28 | 44 | PC_VEHICLE_CORPUS |
| `forklift/car.dx` | 108 | 1/0 | 0 | 0/0/0/0 | 0/0/0/0 | 44 | STATIC_FORMAT_ONLY_OUTLIER |
| `Frontera/car.dx` | 5236 | 1/0 | 2.57945 | 8/12/12/6 | 28/52/66/40 | 44 | PC_VEHICLE_CORPUS |
| `IceCream/car.dx` | 3316 | 1/0 | 2.88495 | 8/12/12/6 | 18/32/36/20 | 44 | PC_VEHICLE_CORPUS |
| `Jump/car.dx` | 4912 | 1/0 | 2.39474 | 8/12/12/6 | 26/48/61/37 | 44 | PC_VEHICLE_CORPUS |
| `Kamaz/car.dx` | 4636 | 1/0 | 4.30487 | 8/12/12/6 | 28/52/56/30 | 44 | PC_VEHICLE_CORPUS |
| `Kangoo/car.dx` | 4468 | 1/0 | 2.45215 | 8/12/12/6 | 24/44/54/32 | 44 | PC_VEHICLE_CORPUS |
| `KiaSportage/car.dx` | 3292 | 1/0 | 2.72724 | 8/12/12/6 | 16/28/36/22 | 44 | PC_VEHICLE_CORPUS |
| `LandCruiser/car.dx` | 4972 | 1/0 | 2.5518 | 8/12/12/6 | 26/48/62/38 | 44 | PC_VEHICLE_CORPUS |
| `Mattserati/car.dx` | 4204 | 1/0 | 2.08375 | 8/12/12/6 | 22/40/50/30 | 44 | PC_VEHICLE_CORPUS |
| `megane/car.dx` | 3052 | 1/0 | 2.47199 | 8/12/12/6 | 16/28/32/18 | 44 | PC_VEHICLE_CORPUS |
| `megane/sus.dx` | 3256 | 1/0 | 2.47199 | 8/12/12/6 | 18/32/35/19 | 44 | PC_VEHICLE_CORPUS |
| `Navara/car.dx` | 3232 | 1/0 | 2.92008 | 8/12/12/6 | 16/28/35/21 | 44 | PC_VEHICLE_CORPUS |
| `NewRav/car.dx` | 5356 | 1/0 | 2.33024 | 8/12/12/6 | 28/52/68/42 | 44 | PC_VEHICLE_CORPUS |
| `Pajero/car.dx` | 5032 | 1/0 | 2.52879 | 8/12/12/6 | 26/48/63/39 | 44 | PC_VEHICLE_CORPUS |
| `Patrol/car.dx` | 5296 | 1/0 | 2.88133 | 8/12/12/6 | 28/52/67/41 | 44 | PC_VEHICLE_CORPUS |
| `RMonster/car.dx` | 4264 | 1/0 | 2.60517 | 8/12/12/6 | 22/40/51/31 | 44 | PC_VEHICLE_CORPUS |
| `SeatBuggy/car.dx` | 3760 | 1/0 | 2.41388 | 8/12/12/6 | 20/36/43/25 | 44 | PC_VEHICLE_CORPUS |
| `SeatBuggy/complete.dx` | 3760 | 1/0 | 2.41388 | 8/12/12/6 | 20/36/43/25 | 44 | PC_VEHICLE_CORPUS |
| `Simmbugghini/car.dx` | 3820 | 1/0 | 2.19241 | 8/12/12/6 | 20/36/44/26 | 44 | PC_VEHICLE_CORPUS |
| `Tata/car.dx` | 4264 | 1/0 | 2.86863 | 8/12/12/6 | 22/40/51/31 | 44 | PC_VEHICLE_CORPUS |
| `Terrano/car.dx` | 3556 | 1/0 | 2.56321 | 8/12/12/6 | 18/32/40/24 | 44 | PC_VEHICLE_CORPUS |
| `Ufo/car.dx` | 6556 | 1/0 | 2.3938 | 8/12/12/6 | 43/82/85/44 | 44 | PC_VEHICLE_CORPUS |
| `WildCat/car.dx` | 3316 | 1/0 | 2.30228 | 8/12/12/6 | 18/32/36/20 | 44 | PC_VEHICLE_CORPUS |
| `Xtrail/car.dx` | 3940 | 1/0 | 2.76894 | 8/12/12/6 | 20/36/46/28 | 44 | PC_VEHICLE_CORPUS |

`Bytes` includes the four-byte tag. Parsing stops structurally before optional tag 102 and the preserved non-collision remainder; no signature search or resynchronization is used.
