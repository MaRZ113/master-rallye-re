# R5V-H — AI opponent vehicle pools

## Phase status

**Static Quick Race pool analysis: CONFIRMED_BY_EXE.**
**First forced Car1=ID26 human run: FAILED / package provenance unresolved.**
**Corrected H.0 package: READY_FOR_CORRECTED_HUMAN_RUNTIME.**
**Natural T1 pool inclusion: NOT STARTED; gated on corrected H.0 runtime pass.**

The G.1 Mercedes registry/unlock and G.2 profile-0 audio work remain closed and
are composed unchanged. R5V-H asks whether physical ID26 can be safely used by
an existing AI participant before changing the natural stock pool.

## Answer to the pool question

The Quick Race owner `FUN_0047B780` calls `FUN_00458090`, which builds a
class-specific vector of **absolute physical CarIDs**. T1 is directly
constructed from IDs 0–6, T2 from 7–13, and T3 from 14–20 plus four individually
progress-gated vehicles (IDs 21–24). ID25 is not in the current T3 pool. The
T1 frontend mapping `local7 -> physical ID26` is not called by this AI chooser.

The stock T1 AI list therefore has a sparse-ID issue: a plain bound increase
from seven to eight would insert ID7, which is T2. The later natural design
must append physical ID26 explicitly. This pool change is intentionally not
included in the first candidate.

The chooser excludes the player vehicle (and a second human vehicle for its
split-screen branch), then removes selected vehicles from a shuffled working
list until that list is exhausted. This preserves the stock no-repeat behavior
for the tested three-AI setup. No participant count is changed.

## Forced materialization proof

The H.0 candidate composes exact pristine retail -> G.1 -> G.2 profile 0, then
changes only the final selected CarID at the participant publication boundary.
The corrected guard checks only ESI/current slot Car1, EBP/exclusive end slot
Car4 (three AI), and the retained T1 class argument. It does not require a
particular player CarID, deep return-address sentinel, or either exclusion
argument. The native participant writer then publishes CarID and derives
CarClass from the ID26 registry record. DriverID has already been selected and
is preserved; H does not write CarClass, NumCars, or other participant IDs.

At `0x00458428`, the hook replays the displaced retail
`mov eax,[esp+14h]; push eax` and resumes at the original `push esi` at
`0x0045842D`. Fresh Ghidra 12.1.4 analysis of pristine retail found exactly two
callers of `FUN_00458090`, both inside `FUN_0047B780`: single-human starts at
slot 1 (`0x0047B96E`) and split-screen starts at slot 2 (`0x0047B93D`). Thus
ESI==1 structurally excludes split-screen. At the publication site EBP is
reloaded as `start + count`, so EBP==4 bounds the three-AI experiment. The
class argument is read from `[ESP+0x8C]` for the pool switch and is not written
in the inspected function. Exclusion stack positions are copied into registers
and then reused as scratch, so they are not stable late guards. Register and
stack derivation is recorded in [validation.md](validation.md).

The first handoff used a non-self-contained EXE-only candidate and reported
stock-looking opponents plus a G.1 locked-state regression. Exact running
resource provenance was not captured, and the player CarID is not available in
that report; therefore neither the package cause nor the hook as a runtime
cause is claimed. The old candidate is historical and superseded. H.0 now
stages a new candidate with the exact G.1 overlay and profile-pinned resources
into `.research-output/vehicles/ai/forced-id26-proof/runtime-package/`, drops
PlayerState files, and verifies EXE/XML/assets before launch. Full evidence is
in [runtime-results.md](runtime-results.md) and the [corrected handoff](runtime-plan.md).

The proof candidate is **not** a natural AI pool integration. Neither the
candidate nor proprietary package resources are committed.

## Unlock and audio axes

The AI pool builder does not call the general player-vehicle availability
predicate. Stock T1 IDs 3–6 are present in the AI candidate list independently
of that player's lock state. T3 reward vehicles 21–24 are exceptional: the
pool builder appends them only after checking their specific progress flags.
Thus player unlock policy and AI pool membership are related only where retail
explicitly couples them; they are not one general predicate.

G.1 keeps ID26's player unlock behavior separate. The forced proof bypasses
pool membership for one participant without changing the player unlock state.
G.2's per-participant sound constructor still reads physical `Race/CarN/CarID`
and resolves ID26 to canonical stock profile 0. That AI audio route remains a
runtime hypothesis until this candidate is tested.

## Evidence boundary

`CONFIRMED_BY_EXE`: Quick Race pool construction, absolute-ID representation,
excluded-player behavior, post-choice registry-derived class write, separate
driver-selection call, and the exact bounded proof-hook layout.

`READY_FOR_CORRECTED_HUMAN_RUNTIME`: exact forced ID26 candidate, coherent
runtime package, and provenance-enforcing Broker checker.

`NOT_YET_CONFIRMED_BY_RUNTIME`: AI Mercedes model/wheels/physics, AI control,
collision, damage, progress, finish, Results, and AI audio. No natural ID26
pool selection is claimed.

The current branch's Ghidra 12.1.4 headless analysis and exact pristine retail
bytes were used to rederive the pool frame and caller bounds. The candidate
builder's exact-byte verifier and the synthetic x86 interpreter check the
three-guard stub, ID26 local write, unchanged DriverID, replay of the displaced
`MOV/PUSH`, and return to `0x0045842D`. This is static evidence only; see
[validation](validation.md).
