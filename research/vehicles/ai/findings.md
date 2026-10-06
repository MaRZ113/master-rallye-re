# R5V-H — AI opponent vehicle pools

## Phase status

**Static Quick Race pool analysis: CONFIRMED_BY_EXE.**
**Forced Car1=ID26 materialization candidate: READY_FOR_HUMAN_RUNTIME.**
**Natural T1 pool inclusion: NOT STARTED; gated on the forced AI runtime pass.**

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

The first candidate composes exact pristine retail -> G.1 -> G.2 profile 0,
then changes only the final selected CarID at the participant publication
boundary. Its guard requires the exact single-player Quick Race return address,
Car1, a T1 class, Car0 physical ID0, and three AI slots. It substitutes the
selected absolute CarID with 26 after the normal vehicle and driver choices;
the native participant writer then publishes CarID and derives CarClass from
the ID26 registry record. It does not write CarClass, DriverID, NumCars, or
other participant IDs.

The guard replays the displaced retail `mov eax,[esp+14h]; push eax` and jumps
back to the original `push esi` at `0x0045842D`. A near-call return-address guard
limits this diagnostic to the one-human `FUN_0047B780` call at `0x0047B96E` and
excludes the split-screen call at `0x0047B93D`.

The proof candidate is **not** a natural AI pool integration. Its generated
binary is ignored under
`.research-output/vehicles/ai/forced-id26-proof/MRallye.exe`; the source,
manifest logic, and tests are committed separately.

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

`READY_FOR_HUMAN_RUNTIME`: exact forced ID26 candidate and Broker checker.

`NOT_YET_CONFIRMED_BY_RUNTIME`: AI Mercedes model/wheels/physics, AI control,
collision, damage, progress, finish, Results, and AI audio. No natural ID26
pool selection is claimed.

The current branch's Ghidra 12.1.4 exports and exact pristine retail bytes were
used for the pool trace. Ghidra 12.1.4 headless analysis of the generated H
candidate also independently decodes the entry hook, all six guards, the ID26
local write, replay of the displaced `MOV/PUSH`, and the return to
`0x0045842D`; the output is summarized in [validation](validation.md).
