# Vehicle research status

Canonical vehicle research lives under `research/vehicles/` on the single
active branch `research/vehicles` in `master-rallye-re-vehicles`. Older
`research/r5v-*`, `e0.1`, and retired-worktree material is historical evidence.

## Current phase

**R5V-G.1 Vehicle Unlock + Frontend Identity Architecture — FULL PASS / CLOSED.**
Mercedes ID26 remains a distinct physical T1 vehicle at local index 7, mirrors
the native ID3/T1 Cup unlock gate, displays native locked presentation, and
cannot be committed while locked. Natural unlock enables the normal Mercedes
slot. Qualified frontend identity channels, including Master Rallye and Rallye
Cup Race Details, show the correct Mercedes strings. The final candidate is
`722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`; final
capture integrity and results are in [runtime-captures.json](unlock/runtime-captures.json)
and the architecture is frozen in [G.1 closeout](unlock/closeout.md).

| Behavior | Final evidence |
|---|---|
| ID26 availability mirrors `Progress/UnlockedCars/T1CupCar1` | `CONFIRMED_BY_RUNTIME` |
| Native locked branch and requirement text | `CONFIRMED_BY_RUNTIME` |
| Locked slot art | `HUMAN_RUNTIME_PASS` |
| Disabled commit control / normal accept blocked | `CONFIRMED_BY_RUNTIME` |
| Natural unlock and selectable Mercedes state | `CONFIRMED_BY_RUNTIME` |
| Vehicle Select / Quick Race / Race Options identity | `CONFIRMED_BY_RUNTIME` |
| Vehicle Setup identity | `CONFIRMED_BY_RUNTIME` (prior qualified channel) |
| Master Rallye Race Details | `CONFIRMED_BY_RUNTIME` |
| Rallye Cup Race Details | `CONFIRMED_BY_RUNTIME` |
| Stock ID0 Race Details regression | `PASS` (owner-reported human runtime) |
| Full stage and Results on final candidate | `PASS` (owner-reported human runtime) |
| Physical identity | CarID 26, T1, Mercedes runtime family preserved |
| Normal qualified Mercedes frontend `GALOCAL UNKNOWN` | none observed |

The full-stage report does not by itself claim a frontend return test. No human
split-screen Race Details test is claimed; all three bounded ID26 writer
branches are statically covered. Challenge and Trophy identity consumers were
not changed or qualified for ID26.

## Roadmap

The immediate next phase is **R5V-G.2 — Vehicle Audio Identity / Sound Family
Architecture**. A previously observed `gaAiVehicleSound` warning for CarID 26
is the entry point; no audio tracing or implementation is included in G.1.
Catalog/order refinement is deferred until multiple add-on vehicles make it
useful. Later phases are R5V-H AI opponent pools, R5V-I multi-slot registry
expansion with a real additional T2 vehicle, and R5V-J generic Addon Vehicle
SDK. Audio-family configurability and T2 qualification remain prerequisites
for calling the generic SDK complete.

No ordering, audio, AI pool, T2 expansion, ID27+, or SDK work is included in
the G.1 closeout.
