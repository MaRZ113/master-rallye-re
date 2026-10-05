# R-AI1.2 — mode coverage and roster persistence

Current status: **CLOSED / CONFIRMED_BY_RUNTIME**. Human gameplay and native
fresh-process persistence are recorded in [runtime closeout](runtime-closeout.md).
Starting branch research/r-ai2, HEAD 7adca41; this phase uses
research/r-ai1-2. Baseline: 316 synthetic tests passed, zero failed/skipped;
compileall/diff-check passed. Existing 94 generalized and 44 five-car native
cases and exact candidate verifiers passed.

The old randomizer rejected count!=3 at 68E324 and ESI>3 at 68E33B. Its
Quick Race-only caller contract did not cover campaign builders. New policy
receives the actual native first/count/slot, bounded to one human and at most
four AI; it does not create participants or alter NumCars.

[Mode map](mode-map.md), [policy](policy.md), [persistence](persistence.md),
[deployment](deployment.md), [validation](validation.md), and
[human handoff](runtime-handoff.md) define separate static and runtime gates.
The earlier R-AI1/R-AI1.1 four-car proofs and R-AI2 five-car proof stay closed.
Six/seven/eight/generic-N remain UNKNOWN and were not tested.

The research verdict is **RESEARCH_EXE_FIRST**: modular config/policy DLL,
small exact-build EXE bridge, original game assets and save format unchanged.
An original-EXE runtime loader/proxy is deferred. This package is not a public
patched-EXE distribution proposal.

Five target modes are mapped with separate generation seams. Mixed uses native
class pools; Diverse shuffles eligible classes per cycle. Challenge is explicit
opt-in only. Cup/Invitation stage transitions reuse RaceData identities; Master
save/load already transfers exact per-participant IDs/classes/drivers. No
sidecar or save format change is required by the traced path. Actual Master
fresh-process persistence, tested mode gameplay and count1..4 coverage are now
CONFIRMED_BY_RUNTIME. Challenge preview sync is non-blocking polish; exact
stock Challenge DriverID preservation is NOT IMPLEMENTED / NOT CONFIRMED.

Final verification: 334 synthetic, 2534 compiled native policy/config/ABI checks,
824 bounded native x86 cases, legacy94 and five-car44 regressions; no failures
or skips. [Build summary](build-summary.json) pins two exact EXEs and a DLL;
two independent output directories reproduced all three files byte-identically.
Current proprietary/generated artifacts stay ignored in this phase folder.
