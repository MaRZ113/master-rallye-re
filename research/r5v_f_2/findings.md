# R5V-F.2 — Mercedes ID26 audit

**Decision: the retail Mercedes cook route is closed; the final ID26 static candidate is prepared, with P0/P1 human acceptance still pending.** The final profile preserves ID0–25 and adds the Mercedes identity at physical ID26 / T1 local7. The owner-reported F.1 cleanup pass remains a separate earlier result.

The historical distinct Mercedes DX files are revision 127, but the exact Mercedes GXM inputs have now been cooked by the retail executable into revision-135 `complete.dx`, `car.dx`, and `wheel.dx`. Cook A and Cook B match byte-for-byte for all three roles. The final profile, executable, and portable package are prepared and statically validated; P0/P1 acceptance of the exact integrated candidate remains pending.

## What is established

| Area | Finding | Status |
|---|---|---|
| Retail slot | Physical ID26 is T1 local7; final static candidate has T1=8, T2=7, T3=12. | Static candidate; final P0 pending |
| Mercedes internal identity | Demo-8.4.1 and demo-9.3.1 both register literal `Mercedes` as ID2 / class0. | Static registry evidence |
| Visible historic name | Both demos contain `MERCEDES ML-320`; final candidate supplies ID26-only Vehicle Select and Quick Race strings. | Static wrapper verified; P0 pending |
| Distinct model source | Demo-8.4.1 `Copy of Mercedes` has car/complete/wheel DX, GXM, sidecars, and all referenced DXT. | Static inventory |
| Retail Mercedes model output | Retail native cooker produced all three rev135 DX roles; independent Cook A/B SHA-256 match 3/3. | Hash and modern parser PASS; final runtime pending |
| Registered demo folder | Demo-8.4.1 `Mercedes/car.dx` and `wheel.dx` are byte-identical to `LandCruiser`; it is not the distinct model source. | Hash-confirmed |
| MercedesAlpha | Partial alternate assets; no registry identity, no physics family, and no complete model package. | Static inventory |
| Retail physics | `Vehicles/Mercedes` passes the current retail semantic schema validator: 144 fields, six gears, six torque entries. | Static compatible; final P1 pending |
| Authentic collision | The distinct source `Copy of Mercedes/car.dx` tag101 parses, has finite values and closed convex representations, and passes a byte-identical zero-edit tag101 serializer round-trip. Supplied prompt reports prior collision/damage runtime success. | Structural PASS; earlier runtime owner-reported; final P1 pending |
| Textures | All 25 referenced unique textures parse and hash-match; final package resolves all 69 bindings. | Static dependency PASS; final P0/P1 pending |
| Vehicle Select icon | Demo ID2 / T1 local2 maps through `T1_Car3` to frame4; final T1_Car8 maps to the same historic slot frame. | Static mapping; P0 render pending; not exclusive to Mercedes |
| SmallCarSheet | Historical field-to-sheet semantics remain unproven; final profile retains frame9. | Documented fallback; frontend history partial |

## Current acceptance gate

The final hash-locked executable and merged Data.sma pass static validation. The runtime overlay contains three rev135 DX, 25 DXT, and no Mercedes GXM/GXI/TXT. The package diff retains all original archive file members, adds 28 Mercedes files, and changes only the VehicleSelect scene. Run the prepared isolated build through the final P0/P1 checklist before calling it a runtime-confirmed 27th vehicle.

The supplied prompt reports earlier cache-only portability and collision/damage runtime success; the local F.2d manifest still says its human log is waiting. Those earlier claims remain owner-reported here. The native tag101's 36-byte secondary face-descriptor delta remains semantically unresolved; do not label those descriptors understood. See [R5V-F.2e findings](../r5v_f_2e/findings.md) for exact hashes and evidence boundaries.

## Next

Run P0 on `research-output/r5v_f_2e/runtime/MRallye.exe`; stop before the race and report each checklist item. After P0 PASS, continue to offline P1. A failed P0 item should be classified before any patch change. Do not alter the existing cleanup or cook-harness profiles.
