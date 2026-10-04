# R-AI2 — exactly five offline participants

**READY FOR HUMAN RUNTIME / PREPARED_RUNTIME_UNTESTED.** The capacity map and
bounded native emulation support one five-car experiment. No five-car game run
has occurred. R-AI1/R-AI1.1 remain closed for four participants.

Starting checkout: `master-rallye-re`, branch `research/r-ai1-1-hardening`,
HEAD `6b30a48`; tracked tree clean. Research continues on `research/r-ai2`.
Pre-existing local Ghidra project/archive artifacts are preserved and excluded.
No worktree operation, sibling-checkout edit, asset change or push occurred.

The ordinary stock limit originates in the Quick Race frontend's three opponent
choices. `47B780` obtains that choice twice: first to publish opponents+1 as
`Race/NumCars`, then to pass the AI count into the stock chooser. The examined
five-car path uses dynamic physics/controller/progress storage and authored
Car0..7 scene/HUD templates. This establishes a static path for five; it does
not establish a general engine maximum or runtime eight-car support.

The first candidate promotes those two reads from3 to4 only for normal Race,
one human, ID0/T1, Track10 (`RaceTest/ItalyS4`) and ghost off. The visible
frontend choice stays **Opponents3**; this is a documented research trigger.
The stock code consequently publishes NumCars5 and selects four ordinary T1 AI.
There is no direct global NumCars patch, array relocation, loop-bound edit,
Broker-core edit, HUD edit or Results edit.

Car4 uses the normal unique T1 pool, IDs1..6. Its precise model/driver varies
through stock vehicle RNG; four distinct AI drivers come from the normal ten
profiles. Reserving a deterministic Car4 ID would require another intervention
and duplicate avoidance. The smaller first experiment keeps this proven stock
selection path, with randomized **class** logic disabled. Player ID0 and the
first three vehicle draws match native four-car controls for the emulated seeds.
The extra draw can change subsequent driver RNG outcomes; fixed DriverIDs for
Car1..3 are not promised.

Composition: exact pristine + existing Loading/Dump hardening **base only** +
R-AI2 getter shim. The R-AI1.1 mixed-class patch is absent. Hardened components
were runtime-confirmed in the earlier composed four-car candidate; this new
composition and fifth participant still require human validation.

Evidence is divided among [pipeline](participant-pipeline.md),
[capacity matrix](capacity-map.md), [native storage and teardown](native-storage.md),
[literal classification](loop-bound-map.md), [intervention](five-car-intervention.md),
[runtime handoff](runtime-handoff.md) and [validation](validation.md).
Machine-readable [capacity map](capacity-map.json), [manifest](patch-manifest.json)
and [static evidence index](static-evidence-index.json) contain derived metadata;
[emulation summary](emulation-summary.json) records the44 native proof cases
and94/52 regression cases. Synthetic tests:316 passed,0 failed,0 skipped.
Raw decompilation, emulator traces, game EXE and captures stay ignored.

The final user mod still targets an exact-build external runtime hook with the
original EXE unchanged on disk. The two setup call sites appear hookable without
structural relocation. No public runtime mod is implemented here.

Stop at the human five-car test. No six-car experiment, generic N, registry
expansion, course reconstruction, Ghost Mode or material work is authorized here.
