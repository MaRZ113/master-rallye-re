# R5V-F.2 — Mercedes ID26 audit

**Decision: Mercedes P0 and P1 are BLOCKED. No Mercedes candidate was generated.** The existing cleanup proof stays intact: the owner reports a FULL PASS for the hash-locked F.1 candidate, with T1=8, T2=7, T3=12, ID26 separate, and the red ID26 marker visible.

The historical data contains a distinct Mercedes model candidate, but it is only revision 127. The current retail parser rejects it, and the project converter accepts revision 131 only. The known original 9.10 cooker path has runtime evidence for other cars, but its exact source build, Mercedes input/output hashes, and reproducible invocation were not recorded. R5V-F.2 therefore stops before executable-profile changes, asset overlays, or a runtime candidate.

## What is established

| Area | Finding | Status |
|---|---|---|
| Retail slot | Physical ID26 remains T1 local7; the F.1 owner-reported cleanup P0 is FULL PASS. | Runtime-reported |
| Mercedes internal identity | Demo-8.4.1 and demo-9.3.1 both register literal `Mercedes` as ID2 / class0. | Static registry evidence |
| Visible historic name | Both demo executables contain `MERCEDES ML-320`. Retail has no `Mercedes` text literal. | Static string evidence; no retail selector reused |
| Distinct model source | Demo-8.4.1 `Copy of Mercedes` has car/complete/wheel DX, GXM, sidecars, and all referenced DXT. | Static inventory |
| Registered demo folder | Demo-8.4.1 `Mercedes/car.dx` and `wheel.dx` are byte-identical to `LandCruiser`; it is not the distinct model source. | Hash-confirmed |
| MercedesAlpha | Partial alternate assets; no registry identity, no physics family, and no complete model package. | Static inventory |
| Retail physics | `Vehicles/Mercedes` passes the current retail semantic schema validator: 144 fields, six gears, six torque entries. | Static compatible; runtime not tested |
| Authentic collision | The distinct source `Copy of Mercedes/car.dx` tag101 parses, has finite values and closed convex representations, and passes a byte-identical zero-edit tag101 serializer round-trip. | Static structural evidence only |
| Textures | The selected source's sidecar references resolve to existing DXT files; all 25 referenced unique textures parse as DXT wrappers. | Static container/dependency evidence; retail runtime not tested |
| Vehicle Select icon | Demo ID2 / T1 local2 maps through `T1_Car3` to carsheet frame4 in both demos. Demo-9.3.1 frame4 is byte-identical to retail frame4. | Static slot mapping; identity is not exclusive to Mercedes |
| SmallCarSheet | Demo-9.3.1 ID2 has raw final integer 0, but that build's field-to-sheet semantics were not independently traced. | Unproven; keep donor frame9 for any later controlled P0 |

## Exact hard stop

The best distinct source package, `demo-8.4.1/DataGx/Vehicles/Copy of Mercedes`, has revision 127 for all three DX roles. Retail's typed parser rejects each at its draw-record interpretation, and `upgrade_dx_131_to_135_with_report` rejects revision 127 with `expected 131`. The source DX therefore cannot be made into a retail model using the currently proven converter. No exact, repeatable original-cooker route was established for these exact files.

The collision gate is statically promising and retail physics is schema-compatible, but neither repairs the missing retail-compatible model build. No code/profile, Data.sma overlay, or executable candidate was changed in this phase. Full file hashes and dependency metadata are in [mercedes-source-inventory.json](mercedes-source-inventory.json).

## Next

Close the specific missing link: reproduce a deterministic, provenance-recorded route from the exact `Copy of Mercedes` GXM/GXI source to retail revision-135 `complete.dx`, `car.dx`, `wheel.dx`, while preserving/validating the authentic car collision and all model textures. Only then validate the generated output with the current SDK and prepare ID26 P0. Do not change the proven cleanup profile or start P1 first.
