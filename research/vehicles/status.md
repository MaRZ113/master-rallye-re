# Vehicle research status

Canonical vehicle research lives under `research/vehicles/` on branch
`research/vehicles`. Earlier `research/r5v-*` documents and the `e0.1` checkout
are historical evidence; this correction does not edit them.

## Current phase

**R5V-G.1 locked-state integration correction — READY FOR HUMAN RUNTIME.** The
stock-like ID26 availability predicate and native locked branch were observed
in the supplied captures. The current deterministic candidate now carries the
ID3 lock-reason selector, the stock locked slot controls, and a bounded Vehicle
Setup name path. The corrected visual and interaction behavior still needs the
human comparison described in `unlock/runtime-handoff.md`.

| Behavior | Current evidence |
|---|---|
| ID26 mirrors ID3 / `T1CupCar1` availability | `CONFIRMED_BY_RUNTIME` |
| Native ID26 locked branch runs when progress and cheats are false | `CONFIRMED_BY_RUNTIME` |
| ID26 locked requirement text equals stock ID3 | `READY_FOR_HUMAN_RUNTIME` |
| ID26 locked thumbnail and disabled commit control | `READY_FOR_HUMAN_RUNTIME` |
| Vehicle Setup displays `MERCEDES ML-320` | `READY_FOR_HUMAN_RUNTIME` |
| Physical ID26 Mercedes model and core gameplay | prior `CORE GAMEPLAY PASS`; candidate regression pending |
| Full stage/results/return on this exact candidate | `UNKNOWN` |

No vehicle ordering, audio, AI pool, T2 expansion, ID27+, or generic SDK work is
included.

## Candidate

The exact pristine-retail candidate and the XML overlay are built under the
ignored `.research-output/vehicles/unlock/` directory. Their source/output
hashes and patch operations are recorded in `unlock/id26-policy.json` and in
the generated manifests. The EXE and overlay are not committed.

## Next gate

Complete the fresh-profile locked ID3/ID26 comparison, then the naturally
unlocked ID26 Vehicle Select, Vehicle Setup, and short-race regression. Only
after that runtime pass should the phase be closed and catalog/ordering work be
considered.
