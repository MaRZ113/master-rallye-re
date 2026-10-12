# Native Reset transaction correlation

**TRANSACTION_CORRELATION_PROBE_READY.** Build `ROAD-TRANSACTION-CORRELATION-1` is read-only with respect to game physics/Broker data. Its runtime instruction hooks replay the original stores and native calls; no teleport request, key, or game-data write is introduced. New instrumentation has not yet been tested inside the game.

## What the accepted session actually proves

Re-read `session-20261011-120437-42100.jsonl` directly (SHA256 `775a611adc8d377c47b22d0fb9747f80ee2a790447ed8207c42cabccf35b18e6`). There are 524 controller calls, one flagged consumer, one retained timer clear candidate, 522 suppressed zero stores and no capture overflow. The current-human candidate controller/backing match across samples. QPC frequency is 10,000,000.

- Timer store before-observation: QPC 11718304563268, VA `0x004CD1DE`, backing `0x02D04168`, flag 1, native operand 0.
- Later active consumer: QPC 11718339230647; **3466.7379 ms after** that timer observation.
- Subsequent zero consumer: QPC 11718339576883; **34.6236 ms after** the active consumer.

These are not a proved shared transaction. The legacy clear record is a pre-store observation, not a captured post-store result. The old analyzer still returns `NEEDS_CLEAR_ATTRIBUTION_CAPTURE`; the new analyzer cannot retrofit missing publication events and returns `NEEDS_TRANSACTION_CAPTURE`. The earlier probe/validation documents describe that historical build; their pre-store-only statements do not describe this replacement.

## Exact image evidence and actual order

All VAs use ImageBase `0x00400000`; subtract it for RVA. Exact pristine SHA and size remain required. Production additionally verifies the three existing caller contexts and relative targets, the accepted RaceLine getter contract, all seven inline blocks, the input preamble, restore callee and its `ret 4`, matrix-copy call and the entire 103-byte copier.

| Native VA / RVA | Evidence and observation |
|---|---|
| `0x004CCFF1` / `0x000CCFF1` | Mode-1 recovery stores **flag 1 before copying the matrix**. Before/after observer; EBP is destination backing, ESI reset manager, EBX participant byte offset (`index*4`). |
| `0x004CD12C` / `0x000CD12C` | Calls `0x00404E60` with ECX=`P+0x34` and source pointer on stack. Exact unrolled copy writes all 16 DWORDs, destination `P+0x34..P+0x73`, then `ret 4`. |
| `0x004CD131` / `0x000CD131` | Observation immediately after the copy returned. Replays original MOV/MOV/ADD with native ADD flags preserved. It proves complete copy-return contents, not atomic publication across threads. |
| `0x00443827` / `0x00043827` | Existing before/after call bridge to controller `0x00444AE0`; accepted native path reaches transform application `0x00444D50`, chassis/wheel recovery `0x00443740`, pose setter `0x0043A020`. No new pose-setter hook. |
| `0x004CCC70` / `0x000CCC70` | Gate-rejection clear; original block begins `0x004CCC6D`. |
| `0x004CD1A1` / `0x000CD1A1` | Mode-0 recovery clear; original block begins `0x004CD19E`. |
| `0x004CD1DE` / `0x000CD1DE` | Timer-path clear; original block begins `0x004CD1DB`. Historical `timer_expired` label is narrower than actual behavior. This is not consumer acknowledgement. |
| `0x00591345` / `0x00191345` | **Additional writer:** `ForwardInputFields_005912D0` stores source `[ECX+0x78]` through backing `[ECX+0x2C]`. Same live vehicle backing relation must be established by the new capture, not assumed from offset similarity. |
| `0x004CB62A` / `0x000CB62A` | **Additional writer:** packed-state low bit into backing `[ESI+0x33]` in the existing restore path. Hook observes actual store before the following native string operation. Its relocated call forwards the original stack argument to verified `0x004D0580`, then returns `ret 4`. |

The publication sequence is therefore **flag store → intervening Broker/native calls and matrix construction → full matrix copy → copy return → possible later physics consumer**, not matrix-first. A controller can observe the level-triggered flag repeatedly. Timer/gate/mode clears do not test consumer completion; native pause and scheduler serialization remain runtime questions.

A direct `.text` store scan also finds backing-constructor initialization at `0x00508A1A` and unrelated stack-local stores. Initialization is not hooked. Direct-store scanning cannot exhaust generic field setters, aliases, memcpy, or serialization writes. `writer_coverage_exhaustive=false` stays explicit. The available Ghidra-bridge read-only project had no program (`Program missing; available: []`); this pass used hash-locked PE bytes/Capstone plus accepted research, without modifying a database.

## Runtime capture and identity

The unchanged `[PhysicsObserver]` settings enable the integrated observer. New `physics_probe_transaction_event` records have one global observation sequence, native-point QPC before/after, thread, race generation and owner lifetime, current controller/local generation/backing, reset manager when native registers prove it, participant when EBX proves it, source owner for input/restore, branch/phase evidence, actual before/after flag, original store operand/result, full 16-DWORD matrix, digest and translation. Unavailable participant remains null. No new unverified numeric ResetManager state layout is read. Existing bounded physics events retain body/wheel snapshots for application inspection.

The invocation label `reset_transaction_candidate_id` is created on each recovery publication, on external input 0→nonzero, or nonzero restore publication. It is **not a causal certificate**. Backing/current-links rereads reject ambiguous or historical association. Scene certificate changes clear the candidate identities while preserving capture history. No vehicle request exists to survive Reset, device release or teardown.

The production capture model reserves **128 important + 16 diagnostic records**. Routine 0→0 stores and repeated settled-zero consumers are aggregated; each active consumer is counted/captured, repeated nonzero stores use the diagnostic partition. New publication creates a new candidate even for 1→1. Unexpected observed flag changes are explicit `unknown_transition_before`. Important/diagnostic overflow, unresolved before/after pairs, or a store still in flight at release prohibit a complete attribution. Hooks are installed as one owned batch under existing thread suspension/quiescence checks; partial installation rolls back, ownership loss disables observation, unsafe restoration keeps the module pinned.

`tools/analyze_physics_transactions.py SESSION.jsonl` requires the **same race, owner lifetime, current human candidate/controller generation/backing, compatible manager/participant publication phases, exact 64-byte transform content, actual store result, and ordered complete-copy → active consumer → clear → later zero**. Candidate ID alone and QPC proximity are insufficient. Cross-thread observations and overlapping native observation windows are rejected rather than assigned an invented happens-before edge. Repeated applications are reported; even `STOCK_TRANSACTION_CORRELATED` always retains `one_shot_guaranteed=false` and `teleport_authorized_by_this_report=false`.

## Why no teleport writes

The decisive unproved invariant is **exclusive single-use ownership of the backing apply flag across recovery, input forwarding and restore writers**. One successful stock interval cannot establish a safe injected protocol. Approach A still obtains its destination from native progress/neighborhood, not an external marker argument. Approach B lacks a certified complete-before-consume publication/owned clear boundary. No manually cleared flag, physical field mutation, progress override, render-callback physics setter or native unpause was added.

The live France1 RaceLine selector remains intact: 448 markers, stride `0x48`, position `+0x38`, current scene generation. Marker ordinal 2 from the earlier capture is not hardcoded. A selected marker is geometry only; arbitrary selected-marker placement, road/chassis height, heading, obstruction checks and relocation range remain uncertified. Stock current-progress recovery remains the safe placement path.

## Exactly one human session

Back up the previous DLL and install the linked Win32 Release DLL. Fully restart using **pristine retail**, with existing Freecam/certificate settings retained. Set:

```ini
[PhysicsObserver]
Enabled=1
RoadTargetPreviewEnabled=1
```

Start offline France1 → drive briefly → perform **one ordinary native Reset** → wait for recovery → drive briefly → exit normally → supply the single session JSONL. No teleport key or special pause experiment is required; keep other settings unchanged. Expect `physics_probe_setup.installed=true`, reason `exact_callsites_installed_read_only`, phase `ROAD-TRANSACTION-CORRELATION-1`, then bounded transaction events and summary with restored hooks. PASS for capture means a lossless same-identity publication/copy/consumer/clear/zero interval with its actual writer identified. Missing publication, identity/content mismatch, unknown transition or overflow is a precise failed capture, not permission to weaken verification.
