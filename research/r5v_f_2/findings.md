# R5V-F.2 — Mercedes ID26 audit

**Decision: the retail Mercedes cook route is closed; final ID26 P0/P1 remain gated on the cache-only human test.** No final Mercedes identity candidate has been generated. The existing cleanup proof stays intact: the owner reports a FULL PASS for the hash-locked F.1 candidate, with T1=8, T2=7, T3=12, ID26 separate, and the red ID26 marker visible.

The historical distinct Mercedes DX files are revision 127, but the exact Mercedes GXM inputs have now been cooked by the retail executable into revision-135 `complete.dx`, `car.dx`, and `wheel.dx`. Cook A and Cook B match byte-for-byte for all three roles. The final profile and executable remain gated until those outputs load from a package with no Mercedes GXM/GXI and no authoring Junction.

## What is established

| Area | Finding | Status |
|---|---|---|
| Retail slot | Physical ID26 remains T1 local7; the F.1 owner-reported cleanup P0 is FULL PASS. | Runtime-reported |
| Mercedes internal identity | Demo-8.4.1 and demo-9.3.1 both register literal `Mercedes` as ID2 / class0. | Static registry evidence |
| Visible historic name | Both demo executables contain `MERCEDES ML-320`. Retail has no `Mercedes` text literal. | Static string evidence; no retail selector reused |
| Distinct model source | Demo-8.4.1 `Copy of Mercedes` has car/complete/wheel DX, GXM, sidecars, and all referenced DXT. | Static inventory |
| Retail Mercedes model output | Retail native cooker produced all three rev135 DX roles; independent Cook A/B SHA-256 match 3/3. | Runtime cook evidence; final cache-only runtime check pending |
| Registered demo folder | Demo-8.4.1 `Mercedes/car.dx` and `wheel.dx` are byte-identical to `LandCruiser`; it is not the distinct model source. | Hash-confirmed |
| MercedesAlpha | Partial alternate assets; no registry identity, no physics family, and no complete model package. | Static inventory |
| Retail physics | `Vehicles/Mercedes` passes the current retail semantic schema validator: 144 fields, six gears, six torque entries. | Static compatible; runtime not tested |
| Authentic collision | The distinct source `Copy of Mercedes/car.dx` tag101 parses, has finite values and closed convex representations, and passes a byte-identical zero-edit tag101 serializer round-trip. | Static structural evidence only |
| Textures | The selected source's sidecar references resolve to existing DXT files; all 25 referenced unique textures parse as DXT wrappers. | Static container/dependency evidence; retail runtime not tested |
| Vehicle Select icon | Demo ID2 / T1 local2 maps through `T1_Car3` to carsheet frame4 in both demos. Demo-9.3.1 frame4 is byte-identical to retail frame4. | Static slot mapping; identity is not exclusive to Mercedes |
| SmallCarSheet | Demo-9.3.1 ID2 has raw final integer 0, but that build's field-to-sheet semantics were not independently traced. | Unproven; keep donor frame9 for any later controlled P0 |

## Current hard stop

Cooker reproducibility, rev135 parsing, tag101 structural integrity, and 25/25 DXT closure are established. The cache-only package is assembled and the exact authoring Junction is removed while the authoring source remains preserved. The only gate before adding the final profile is a human DebugView test proving preview and race car/wheel load with the isolated cache-only package.

The native tag101's 36-byte secondary face-descriptor delta remains semantically unresolved, but is bounded and accepted for cache-only and controlled runtime P1. Do not label the descriptors understood. Full file hashes and dependency metadata are in [mercedes-source-inventory.json](mercedes-source-inventory.json); Cook A/B and package details are in the R5V-F.2b research.

## Next

Run the prepared cache-only human test using `research-output/r5v_f_2b/cache-only/CACHE_ONLY_TEST_INSTRUCTIONS.md`. After a full cache-only PASS, implement the separate `mercedes-final` ID26 profile and prepare P0. A failed preview/race load returns to asset-path research. Do not alter the existing cleanup or cooker profiles while waiting.
