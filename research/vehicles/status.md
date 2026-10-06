# Vehicle research status

Canonical vehicle research lives under `research/vehicles/` on the single
active branch `research/vehicles` in `master-rallye-re-vehicles`. Older
`research/r5v-*`, `e0.1`, and retired-worktree material is historical evidence.

## Current phase

**R5V-G.2 Vehicle Audio Identity / Sound Family — FULL PASS / CLOSED.**
Human runtime A/B confirmed that physical Mercedes ID26 remains CarID26 while
selecting a stock engine-audio profile. Canonical Mercedes policy is
`stock_audio_profile_id=0` (Landcruiser, historical-compatible `rev9` / curve
A profile); ID19/Mattserati is a confirmed bass-heavy diagnostic oracle. The
generic selector now supports only matrix-verified tuned stock IDs 0..24.
Capture hashes, physical-identity comparison and exact binary-diff proof are
in [G.2 runtime results](audio/runtime-results.md); architecture and limits
are in [G.2 findings](audio/findings.md).

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
| ID26 tuned engine audio profile | ID0 ordinary profile `HUMAN_RUNTIME_OBSERVATION`; ID19 bass-heavy A/B oracle `HUMAN_RUNTIME_OBSERVATION` |
| Normal qualified Mercedes frontend `GALOCAL UNKNOWN` | none observed |

The full-stage report does not by itself claim a frontend return test. No human
split-screen Race Details test is claimed; all three bounded ID26 writer
branches are statically covered. Challenge and Trophy identity consumers were
not changed or qualified for ID26.

## Roadmap

## Current phase: R5V-H — AI Opponent Vehicle Pools

**Static Quick Race pool map: CONFIRMED_BY_EXE.** The retail pool uses absolute
CarIDs; T1 enumerates 0–6 and does not include sparse frontend mapping
`T1 local7 -> ID26`. Player availability and AI pool eligibility are separate.

**Forced Car1=ID26 materialization proof: WAITING_FOR_CORRECTED_HUMAN_RUNTIME.**
The first H run failed: the locked thumbnail/commit behavior regressed in that
test environment and forced Car1=ID26 was not observed; missing runtime
provenance leaves the cause unresolved. H.0 now has a hash-verified package
composing the closed G.1 resources and G.2 profile-0 build, plus a minimal
Car1/T1/three-AI publication guard. The corrected package still requires the
fresh-profile lock canary and human AI test. See [H runtime results](ai/runtime-results.md),
[findings](ai/findings.md), and [runtime plan](ai/runtime-plan.md).

**Natural T1 pool inclusion: NOT STARTED; gated on forced runtime pass.** The
next candidate will append ID26 to the explicit T1 pool only after the forced
participant proves model, wheels, physics, AI, collision, and damage behavior.

Later phases are R5V-I multi-slot registry expansion with a real additional T2
vehicle, then R5V-J generic Addon Vehicle SDK. Catalog/order refinement remains
deferred. Do not begin ID27+, T2 expansion, or SDK work during this H gate.
