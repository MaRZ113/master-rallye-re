# R-AI1.1 — mixed-class generalization

Status: **R-AI1.1 — PLAYER-INDEPENDENT RANDOMIZED MIXED-CLASS: CLOSED /
CONFIRMED_BY_RUNTIME**. All three AI slots, repeated fresh-race class/ID
variation, simultaneous T1/T2/T3 and the composed hardened runtime passed.
[Final closeout](runtime-closeout.md) distinguishes four fresh generations
from the fifth Restart capture; uniform RNG is not proven. Fixed R-AI1 is
separately CLOSED / CONFIRMED_BY_RUNTIME. The [handoff](runtime-handoff.md)
is completed; no Opponent Capacity work began.

Starting main checkout: branch `research/r-ai1`, HEAD `73ccb37`, tracked tree
clean. This phase uses `research/r-ai1-1` at that HEAD. Existing untracked
Ghidra project and ZIP remain untouched. No worktrees, sibling edits, push,
assets, materials, registry or capacity changes. NumCars remains four.

## Static gate

| Question | Evidence-backed result |
|---|---|
| Stock Attract owner | `0x449E90`, Type14 branch `0x44A128..0x44A16D`, chooser `0x4584F0(false)` |
| Why Attract mixes classes | One broad absolute-ID pool; class is derived after each ID draw. It does not first choose a random class |
| Reuse verdict | **PARTIALLY REUSABLE**: common pool/shuffle/driver/publication helpers; whole chooser would overwrite Car0 |
| Quick Race owner | `0x47B780 -> 0x458090`; player class filters the original AI pool |
| Generalized seam | Per-AI loop `0x458379`, reusing inline native pool cases at `0x458112` and the existing draw/publication path |
| Class policy | MIXED calls native range(0,3) once independently at Car1, Car2, Car3; DIVERSE emulation uses2/1/0; STOCK is byte-identical pristine |
| ID/class | Stock pool produces absolute ID; `0x458449` reads registry class; `0x458435/456/468` publish ID/class/driver |
| Driver | Original single driver pool and `0x458980` remain; class does not filter drivers |
| Downstream delta | Same per-slot identity/physics/model/result loops; player balance scalar/race title remain T1. No new array indexing or allocation |
| Data-only | Quick Race overwrites AI identities; no consumed independent-class data/callback seam found in this path |
| No-EXE verdict | **EXTERNAL_RUNTIME_MOD_REQUIRED** for this Quick Race policy; design only, no loader implemented |

Native choices are **CONFIRMED_BY_EXE** on pristine SHA
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Generalized gameplay is confirmed in the bounded full-race context above.
Native emulation executes the actual
pool branches, draw, erase, CRT RNG, driver choice and publication, with explicit
synthetic Broker/heap/TLS/game-range boundaries; it does not materialize actors.

## Existing runtime evidence

Raw-bound fixed capture: IDs **0/14/4/1**, classes **0/2/0/0**, PlayerTypes
**1/2/2/2**, DriverIDs **30/7/1/2**. Human observations establish model, driving,
physics, contacts/damage, progress, Wildcat finish and result identity/icon.
The separate matched fixed-selection control was not supplied (non-blocking);
clean-stock reproduction of the native Dump crash is confirmed separately.

Raw-bound pristine Attract capture: NumCars4, NumPlayers0, Type14,
AttractMode=True, RecordReplay=False, PlaybackReplay=False. IDs **1/5/12/14**,
classes **0/0/1/2**, PlayerTypes all2, drivers **4/1/3/2**. This confirms stock
live AI selection across classes; it does not replace the new Quick Race test.

## Candidate and boundaries

Original runtime-tested candidate: `.research-output/r-ai1-1/randomized-candidate/MRallye.exe`.
SHA256 `f9e8e556842602252ec39b2174e796f6cb67651d8f573f2565f9d2e5569bd9ac`;
size3,121,214. Five bounded modified ranges,355 bytes of research code, no
section/raw/image/page-count growth. [Policy and patch](generalized-class-policy.md).
It is temporary instrumentation, not a proprietary binary distribution format.

The fresh-profile proof uses ID0/T1 human and ordinary stock AI pools
T1 IDs0..6, T2 IDs7..13, T3 IDs14..20. T3 bonus IDs21..24 retain native unlock
checks; no frontend unlock patch is needed. Duplicate classes are allowed;
already configured CarIDs are excluded when a class pool is rebuilt.

[Attract](attract-chooser.md), [comparison](quickrace-vs-attract.md), [RNG](rng.md),
[no-EXE design](no-exe-feasibility.md), [Dump limitation](observatory-limitations.md),
[validation](validation.md), [human handoff](runtime-handoff.md).
The original un-hardened handoff is [SUPERSEDED](runtime-handoff-unhardened.md)
for same-process sampling; its post-results Dump remains unsafe. The new
composed candidate is documented in [hardening](hardening.md), not a chooser
redesign. Hardening/repeated-sampling human validation is complete; R-AI2
remains separately deferred. [Final runtime evidence](runtime-closeout.md).
