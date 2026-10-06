# R-AI1 / R-AI1.1 — final runtime closeout, 2026-10-04

**R-AI1 — MIXED-CLASS OPPONENTS: CLOSED / CONFIRMED_BY_RUNTIME.**
**R-AI1.1 — PLAYER-INDEPENDENT RANDOMIZED MIXED-CLASS: CLOSED /
CONFIRMED_BY_RUNTIME.** The exact composed hardened research runtime is also
**CONFIRMED_BY_RUNTIME**. This closes four existing participants only.

The human's explicit closeout report supplies movement, physical/model identity,
finish/results, survival and lifecycle observations. Pinned Observatory parsing
supplies raw-bound state evidence. These evidence levels remain separate:
automatic oracles still return state/sampling matches, never runtime FULL PASS.
[Machine-readable summary](runtime-closeout-summary.json) contains exact IDs,
classes, capture names/hashes and bounded claims. Raw dumps remain ignored.

## Fixed and generalized full-race proofs

Fixed R-AI1: Car0 ID0/T1 human Landcruiser; Car1 ID14/T3 AI Bowler Wildcat;
Car2 ID4/T1 and Car3 ID1/T1 stock controls. NumCars4/NumPlayers1.
Human confirmed Wildcat model, AI driving, physics, collisions/damage, progress,
full race completion and correct result driver identity/icon.
[Fixed evidence](../r-ai1/runtime-result.md).

Generalized full race: Car0 ID0/T1 human; Car1 ID15/T3 Simmbugghini;
Car2 ID17/T3 Kangoo; Car3 ID7/T2 Navara. Human confirmed three independent models
and physics, normal AI driving, contacts/damage, progress, finish and correct
result names/icons. The semantic result is independent Car1/2/3 class selection
from Car0 class, followed by stock class pool and registry-derived CarClass.
[Representative evidence](runtime-validation.md). No capacity/registry claim.

## Repeated generation and Restart

Exact image SHA256
`603f0c06ca2a502367baa7e49fcaeab9e2ab9a7d6c47dd46ed82ca27cb9840a1`;
all seven new captures identify **one process ID34240**, size3,121,214,
`retail-r-ai1-1-hardened`, `native_hardened`, command-proven fresh complete Dump.
Each JSON reproduces its raw sidecar entries and selected block through the
unchanged pinned parser. Car0 stays ID0/T1/human; active captures have NumCars4,
NumPlayers1, Type2 and AttractMode=False. Named physics/family/wheel checks pass.

| Race | Creation | Car1 | Car2 | Car3 |
|---|---|---|---|---|
| 1 | Fresh Quick Race | ID18 Megane / T3 | ID1 Pajero / T1 | ID12 Newrav / T2 |
| 2 | Restart of race1 | ID18 Megane / T3 | ID1 Pajero / T1 | ID12 Newrav / T2 |
| 3 | Fresh Quick Race | ID11 Patrol / T2 | ID13 Kiasportage / T2 | ID19 Mattserati / T3 |
| 4 | Fresh Quick Race | ID17 Kangoo / T3 | ID1 Pajero / T1 | ID3 Terrano / T1 |
| 5 | Fresh Quick Race | ID12 Newrav / T2 | ID3 Terrano / T1 | ID11 Patrol / T2 |

**Five active captures, four fresh generations.** Race2 preserves/reuses the
current participant composition and is **not** an independent random draw.
Fresh changes occur after returning to Quick Race frontend and making a new
race. This corrects the historical plan's expectation of five fresh generations;
the actual four fresh compositions establish the requested observed variation.

Automated summarizer: `ai_class_assignments_vary`, `ai_ids_vary`,
`two_non_player_class_outcomes`, `simultaneous_mixed_classes` are all true;
status **BROKER_SAMPLING_MATCH_ONLY**, runtime_full_pass=false. It accepts five
distinct labels, so the human creation history is necessary to interpret them.
Fresh AI class/ID variation, player-class independence, all three AI slots and
simultaneous T1/T2/T3 composition are **CONFIRMED_BY_RUNTIME**. Mathematical
uniformity, exact class probability1/3 and arbitrary class/count/ID support are
**NOT PROVEN**. No implementation or tests were changed to alter this verdict.

## Hardened runtime and stock Dump bug

Race1 completed, followed by native Dump on normal Race Results. Human reports
the game remained alive and Dump continued past PointsList. Verified Results
capture `20261004-183422_mixed-hardened-results` returns
**BROKER_RESULTS_DUMP_MATCH_ONLY**, runtime_full_pass=false, **21 following
entries**, first `Frontend/RaceResults/Car0`.

NULL StringList crash prevention, native continuation and post-results game
survival are **CONFIRMED_BY_RUNTIME**, using the human survival observation
with complete raw-bound output. Hardened `{ }` represents either a NULL list
payload or an allocated empty list; textual output does not distinguish them.
The legitimate NULL PointsList producer/unsafe pristine formatter is established
statically. Clean stock retail reproduced the same crash according to the human:
canonical attribution is **STOCK NATIVE BROKER DEBUG->DUMP BUG**, independent of
mixed-class AI, Observatory and vehicle physics.

Restart then produced race2 with Type2, AttractMode=False and NumPlayers1.
**LEGACY LOADING->ATTRACT FALSE TRIGGER HARDENING: CONFIRMED_BY_RUNTIME.**
Separate legitimate idle-main-menu Attract owner/Type14/stock chooser are
unchanged statically. Human idle Attract preservation was not explicitly tested.

The base-only hash `bbb9f0a8bb2523adf125582d16512c25f9b51db7a4104ee5edf8f7251865ae00`
was not separately launched: its Loading/StringList hardening components were
validated inside the exact composed image above. The additional XmlData NULL
guard retains static/emulation evidence; a specific NULL-XML runtime trigger
was not isolated. No universal Dump-safety claim is made.

## Replay lifecycle

Capture `20261004-183900_mixed-random-race-2_REPLAY_MODE`: PlaybackReplay=True,
RecordReplay=False, AttractMode=False, Type2, NumCars4/NumPlayers1; IDs0/18/1/12
and classes0/2/0/1 retained. Human reports normal post-race Replay on this image.
**POST-RACE REPLAY LIFECYCLE: CONFIRMED_BY_RUNTIME.** Exact causal attribution
to a particular patch is **UNKNOWN / NON-BLOCKING**, with no isolated A/B test.

## Deferred Results-capacity clue

**CAPACITY CLUE — NOT RUNTIME PARTICIPANT-CAPACITY PROOF.**
The hardened Results Dump exports `Frontend/RaceResults/Car0..Car7`, with
values **9/11/14/17/12/12/12/12**. This demonstrates Broker Results storage/paths
for at least eight slots. Their payload semantics are not reconstructed here
and must not be equated with `Race/CarN/CarID`. PositionList/TimeList each have
only **four** entries, corresponding to the actual four-participant result.

This does not prove eight engine actors, native participant capacity8, physics/
controller/network capacity8, HUD capacity8 or eight valid result rows. Paths
may persist and unused slot values are not actors. Preserve this for **R-AI2**;
no allocation/loop investigation, Car4 runtime or five-car candidate was begun.

Earlier pristine Attract evidence (NumCars4, NumPlayers0, mixed T1/T2/T3,
PlaybackReplay=False) remains a separate stock engine proof. Its legitimate
chooser is distinct from the neutralized legacy Loading failure trigger.

## Deployment and closeout validation

Data-only remains insufficient at the audited Quick Race seam. Final user mod
remains **EXTERNAL_RUNTIME_MOD_REQUIRED**: unchanged on-disk MRallye.exe,
removable narrow hooks/config, STOCK/MIXED/DIVERSE, exact build verification,
unknown builds fail closed. Research hardening is quality-of-life; randomized
patch is a proof implementation. No public EXE distribution or runtime mod
implementation is proposed in this closeout.

Synthetic302 passed/0 failed/0 skipped; compileall and diff-check PASS.
Fixed, original generalized, hardened base and composed candidate verifiers
PASS. Existing Results checker/tests PASS; seven new raw/JSON pairs PASS,
Results continuation21 and sampling checks verified. No test/code edits.
The earlier static/emulation counts remain historical and are not runtime proof.
One coherent local documentation/derived-evidence commit; no push.
**Next: R-AI2 — Opponent Capacity, separately authorized. STOP here.**
