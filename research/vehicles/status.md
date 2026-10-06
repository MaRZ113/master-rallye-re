# Vehicle research status

Canonical vehicle research lives under `research/vehicles/` on branch
`research/vehicles`. Earlier `research/r5v-*` documents and the `e0.1` checkout
are historical evidence; this correction does not edit them.

## Current phase

**R5V-G.1 finalization — Race Details localization candidate ready for runtime.**
The corrected staged package has passed the human locked-state test: ID26
shows the stock locked art and requirement, `UI/Enabled=False`, and normal
accept cannot commit it. After satisfying the native unlock requirement, ID26
becomes selectable and shows its normal Mercedes presentation. The remaining
work is the new display-only Race Details fix for Master Rallye and Rallye Cup.
The candidate is staged in the same verified runtime Root; follow
`unlock/runtime-handoff.md` for the final two-mode UI check and race smoke.

| Behavior | Current evidence |
|---|---|
| ID26 mirrors ID3 / `T1CupCar1` availability | `CONFIRMED_BY_RUNTIME` |
| Native ID26 locked branch runs when progress and cheats are false | `CONFIRMED_BY_RUNTIME` |
| ID26 locked requirement text equals stock ID3 | `CONFIRMED_BY_RUNTIME` |
| ID26 locked thumbnail and disabled commit control | `CONFIRMED_BY_RUNTIME` with corrected package Root and overlay |
| ID26 normal accept blocked while locked | `CONFIRMED_BY_RUNTIME` |
| ID26 unlocks after native T1 Cup requirement | `CONFIRMED_BY_RUNTIME` |
| Vehicle Setup displays `MERCEDES ML-320` | prior channel remains passed; not reopened here |
| Quick Race Mercedes localization | prior channel remains passed; not reopened here |
| Race Details producer | shared `FUN_0047C080`, group `0x35`, absolute `RaceData/CompetitorN/CarID`; static trace complete |
| Race Details Mercedes localization | old failure captured in both modes; new candidate `READY FOR HUMAN RUNTIME` |
| Physical ID26 Mercedes model and core gameplay | prior `CORE GAMEPLAY PASS`; short regression smoke is part of this candidate handoff |
| Full stage/results/return on this exact candidate | `UNKNOWN` |

No vehicle ordering, audio, AI pool, T2 expansion, ID27+, or generic SDK work is
included.

## Candidate

The final Race Details EXE, overlay, and coherent staged runtime tree are under
ignored `.research-output/vehicles/unlock/`. Their hashes and patch operations
are recorded in `unlock/id26-policy.json`, `unlock/runtime-root-profile.json`,
and generated manifests. The package updater replaces only `MRallye.exe` and
the package manifest; it preserves existing PlayerState/options state. No
candidate EXE, archive, asset, profile save, or raw capture is committed.

## Next gate

Run the package verifier with `--allow-runtime-state`, launch from the staged
package root, and visit Race Details in Master Rallye and Rallye Cup using the
already unlocked profile. Confirm `MERCEDES ML-320`, preserve each mode's
normal race text, check one stock-vehicle control, then do a short ID26 race
smoke. G.1 remains open until this exact candidate passes; catalog/ordering
work has not started.
