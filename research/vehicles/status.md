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

## Current phase

**R5V-H — AI Opponent Vehicle Pools: FULL PASS / CLOSED.** The exact H.2
candidate `de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9`
passed natural ID26 T1 eligibility in newly generated Rallye Cup and Master
Rallye rosters. Cup stage transitions reused its generated roster. Master
Rallye stored the roster natively and restored the exact ID26/DriverID entry
after a full process exit and fresh-process resume. Quick Race H.1 remains
runtime-confirmed. Invitation's tested route is T3-only, so T1 ID26 eligibility
there is `NOT_APPLICABLE`; Challenge remains authored and Practice has no
distinct stock AI roster owner in the bounded audit. Full capture identities
and raw SHA256 values are in [H runtime results](ai/runtime-results.md).

| Mode | ID26 policy | Runtime status |
|---|---|---|
| Quick Race | Dynamic T1 pool `[0,1,2,3,4,5,6,26]` | `CONFIRMED_BY_RUNTIME` (H.1) |
| Rallye Cup | Dynamic T1 pool at new Cup roster creation; native stage reuse | `CONFIRMED_BY_RUNTIME` (H.2) |
| Master Rallye | Dynamic T1 pool at new competition creation; native save/load reuse | `CONFIRMED_BY_RUNTIME` (H.2) |
| Invitation | Tested normal path is T3-only; physical T1 ID26 is out of scope | `NOT_APPLICABLE` |
| Challenge | Authored/event-specific; no automatic injection | unchanged |
| Practice | No distinct stock AI roster owner found in bounded audit | `NOT_APPLICABLE` |

Native DriverID selection remains independent from ID26's display-only Results
identity `JEAN-PIERRE STRUGO`. The fixed label is not used to select or alter
AI behavior. Player unlock state also remains independent from AI eligibility.

## Current phase — R5V-I multi-slot registry expansion

**R5V-I.0 second-slot proof: FULL PASS / CLOSED.** Four verified Observatory
JSON/raw pairs from the exact I.0 executable confirm physical ID27 at T2
local7, a single-player T2 race participant, and simultaneous ID27/T2 plus
ID26/T1 SplitScreen participants. The owner observed normal ID27 donor-model,
wheel, movement, HUD and progress behavior. This is a slot proof; the I.0
Navara donor is not a distinct vehicle identity. Capture/raw hashes and
bounded human observations are in [the I runtime ledger](multislot/runtime-results.md).

**R5V-I.1 authored independent-family T2 qualifier: READY FOR HUMAN RUNTIME.**
The exact candidate keeps physical ID27/T2 local7 while naming its runtime,
model, wheel and physics family `R5VQualifier`. Its ignored package gives that
family its own `DataGx/Vehicles/R5VQualifier` assets and
`Vehicles/R5VQualifier` physics/modification paths, with a magenta body-DXT
canary. This is intentionally authored SDK qualification content, not a
historical vehicle; collision/model topology and most assets remain
Navara-derived. Runtime status is still pending. See the
[I.1 qualification and handoff](multislot/i1-qualification.md).

Future non-bonus T3 addons must qualify Invitation's ordinary T3 pool
explicitly; class membership alone does not imply eligibility in every mode.
Bonus/special T3 vehicles must not be added to that pool automatically.

## Roadmap

R5V-I closes only after the exact I.1 candidate proves independent family
routing in human runtime and its natural T2 AI eligibility. R5V-J generic Addon
Vehicle SDK remains out of scope until that qualification is complete.

## H.2 historical pre-runtime status (superseded)

**Static Quick Race pool map: CONFIRMED_BY_EXE.** The retail pool uses absolute
CarIDs; T1 originally enumerates 0–6 and does not include sparse frontend
mapping `T1 local7 -> ID26`. Player availability and AI pool eligibility are
separate.

**Forced Car1=ID26 materialization proof: CONFIRMED_BY_RUNTIME** for one
single-player T1 Quick Race with three AI. The active-race capture confirms
Car1 ID26/T1/DriverID8 with Mercedes `CarType` and `WheelType`; the human
observed its model, AI driving, progress, finish, and Results-row presence.
The H.0.1 forced-ID26 Results display and post-Results NULL StringList Dump
survival are **CONFIRMED_BY_RUNTIME**. Its separate XmlData NULL guard and the
exact legacy Loading->Attract trigger remain unisolated/`UNKNOWN`.

**H.1 natural Quick Race T1 pool: CONFIRMED_BY_RUNTIME.** In the 2026-10-07
capture, physical ID26 appeared naturally as AI Car2 while the player remained
T1/ID1 and `T1CupCar1=False`. The completed Results capture shows ID26 at Rank
2 and the fixed display-only name `JEAN-PIERRE STRUGO`, classified
`REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER`; exact ML-320 pairing is unproven.
Native DriverID selection was unchanged. See [the H.1 result](ai/natural-t1-pool.md)
and [runtime evidence](ai/runtime-results.md).

**At the time of the H.2 candidate handoff: STATICALLY VERIFIED / READY_FOR_HUMAN_RUNTIME.**
The current-branch executable trace identifies a shared dynamic Rallye
Cup/Invitation T1 generator and a separate new Master Rallye generator. A
fail-closed candidate extends only those two T1 source-pool exits with physical
ID26. It preserves Quick Race H.1, native exclusions/DriverID selection,
participant counts, and existing Cup/Invitation stage and Master Rallye
save/load roster paths. Human testing must create new Cup/Invitation rosters
and a new Master Rallye competition; old all-stock rosters are expected to
remain unchanged. Challenge stays authored. The bounded mode audit found no
separate Practice AI-pool owner. See [mode map](ai/mode-consumers.md),
[H.2 trace and patch](ai/mode-aware-t1-eligibility.md), and
[human handoff](ai/mode-aware-runtime-plan.md).

This historical handoff status is superseded by the H.2 runtime closeout above.
