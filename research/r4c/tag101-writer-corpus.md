# R4C tag-101 writer corpus

Generated from external read-only vehicle resources. Modified dry-run bytes were retained only in memory.

## Summary

- Tag-101 resources / structurally parsed: **28 / 28**.
- Source-validated / static-only outliers: **27 / 1**.
- Zero-edit tag-101 byte-identical: **28/28**.
- Zero-edit full DX byte-identical: **28/28**.
- Translation pass / skipped / failed: **27 / 1 / 0**.
- Unexpected failures: **0**.

Forklift is serialized exactly but is skipped for translation because its known non-finite coordinates remain validation failures.

## Resources

| Resource | Bytes | Zero tag101 | Zero DX | Translation | Changed bytes | Evidence |
|---|---:|---|---|---|---:|---|
| `Astero/car.dx` | 5296 | PASS | PASS | PASS | 299 | PC_VEHICLE_CORPUS |
| `Bruno/car.dx` | 3904 | PASS | PASS | PASS | 248 | PC_VEHICLE_CORPUS |
| `ChevyBlazer/car.dx` | 3232 | PASS | PASS | PASS | 210 | PC_VEHICLE_CORPUS |
| `Forester/car.dx` | 4228 | PASS | PASS | PASS | 271 | PC_VEHICLE_CORPUS |
| `forklift/car.dx` | 108 | PASS | PASS | SKIPPED | - | STATIC_FORMAT_ONLY_OUTLIER |
| `Frontera/car.dx` | 5236 | PASS | PASS | PASS | 285 | PC_VEHICLE_CORPUS |
| `IceCream/car.dx` | 3316 | PASS | PASS | PASS | 230 | PC_VEHICLE_CORPUS |
| `Jump/car.dx` | 4912 | PASS | PASS | PASS | 281 | PC_VEHICLE_CORPUS |
| `Kamaz/car.dx` | 4636 | PASS | PASS | PASS | 261 | PC_VEHICLE_CORPUS |
| `Kangoo/car.dx` | 4468 | PASS | PASS | PASS | 270 | PC_VEHICLE_CORPUS |
| `KiaSportage/car.dx` | 3292 | PASS | PASS | PASS | 193 | PC_VEHICLE_CORPUS |
| `LandCruiser/car.dx` | 4972 | PASS | PASS | PASS | 281 | PC_VEHICLE_CORPUS |
| `Mattserati/car.dx` | 4204 | PASS | PASS | PASS | 247 | PC_VEHICLE_CORPUS |
| `megane/car.dx` | 3052 | PASS | PASS | PASS | 207 | PC_VEHICLE_CORPUS |
| `megane/sus.dx` | 3256 | PASS | PASS | PASS | 224 | PC_VEHICLE_CORPUS |
| `Navara/car.dx` | 3232 | PASS | PASS | PASS | 192 | PC_VEHICLE_CORPUS |
| `NewRav/car.dx` | 5356 | PASS | PASS | PASS | 309 | PC_VEHICLE_CORPUS |
| `Pajero/car.dx` | 5032 | PASS | PASS | PASS | 271 | PC_VEHICLE_CORPUS |
| `Patrol/car.dx` | 5296 | PASS | PASS | PASS | 304 | PC_VEHICLE_CORPUS |
| `RMonster/car.dx` | 4264 | PASS | PASS | PASS | 251 | PC_VEHICLE_CORPUS |
| `SeatBuggy/car.dx` | 3760 | PASS | PASS | PASS | 251 | PC_VEHICLE_CORPUS |
| `SeatBuggy/complete.dx` | 3760 | PASS | PASS | PASS | 251 | PC_VEHICLE_CORPUS |
| `Simmbugghini/car.dx` | 3820 | PASS | PASS | PASS | 236 | PC_VEHICLE_CORPUS |
| `Tata/car.dx` | 4264 | PASS | PASS | PASS | 241 | PC_VEHICLE_CORPUS |
| `Terrano/car.dx` | 3556 | PASS | PASS | PASS | 229 | PC_VEHICLE_CORPUS |
| `Ufo/car.dx` | 6556 | PASS | PASS | PASS | 426 | PC_VEHICLE_CORPUS |
| `WildCat/car.dx` | 3316 | PASS | PASS | PASS | 229 | PC_VEHICLE_CORPUS |
| `Xtrail/car.dx` | 3940 | PASS | PASS | PASS | 228 | PC_VEHICLE_CORPUS |
