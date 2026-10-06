# Vehicle research status

Canonical vehicle research lives under `research/vehicles/` on branch
`research/vehicles`. Earlier `research/r5v-*` documents and the `e0.1` checkout
are historical evidence; this correction does not edit them.

## Current phase

**R5V-G.1 locked-state integration correction — RUNTIME RETEST REQUIRED.** The
candidate EXE's locked predicate and locked requirement text passed human
testing. The first retest did not deploy the generated VehicleSelect overlay
under the resource Root named by the captures, so the slot-art and commit
control result is not a valid test of the appended XML controls. A corrected,
hash-verified runtime package is being staged; follow
`unlock/runtime-handoff.md`.

| Behavior | Current evidence |
|---|---|
| ID26 mirrors ID3 / `T1CupCar1` availability | `CONFIRMED_BY_RUNTIME` |
| Native ID26 locked branch runs when progress and cheats are false | `CONFIRMED_BY_RUNTIME` |
| ID26 locked requirement text equals stock ID3 | `CONFIRMED_BY_RUNTIME` |
| ID26 locked thumbnail and disabled commit control | `NOT_VALIDLY_TESTED`; tested resource Root lacked the overlay |
| Vehicle Setup displays `MERCEDES ML-320` | prior channel remains passed; not reopened here |
| Quick Race Mercedes localization | prior channel remains passed; not reopened here |
| Race Details Mercedes localization | `FAIL_OBSERVED` in Master Rallye and Rallye Cup; producer tracing deferred until scene deployment is proven |
| Physical ID26 Mercedes model and core gameplay | prior `CORE GAMEPLAY PASS`; exact G.1 package regression pending |
| Full stage/results/return on this exact candidate | `UNKNOWN` |

No vehicle ordering, audio, AI pool, T2 expansion, ID27+, or generic SDK work is
included.

## Candidate

The exact EXE, overlay, and coherent staged runtime tree are built under the
ignored `.research-output/vehicles/unlock/` directory. Their hashes and patch
operations are recorded in `unlock/id26-policy.json`,
`unlock/runtime-root-profile.json`, and generated manifests. No candidate EXE,
archive, asset, profile save, or raw capture is committed.

## Next gate

Run `vehicle_unlock_runtime_package.py verify` and launch only from the staged
package root. Confirm the capture's `Root` equals that root, then repeat the
fresh-profile ID3/ID26 comparison and unlocked short-race smoke. Once the exact
scene is proven active, address the observed Race Details name path. G.1 is not
closed and catalog/ordering work has not started.
