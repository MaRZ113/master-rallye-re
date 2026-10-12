# R-CAM1-A3j.3 — Complete relocation safety analysis

## Decision

**`READ_ONLY_PHYSICS_PROBE_READY`.** The pristine retail image contains a verified route from the stock recovery manager through the `Controller/CarN` Broker adapter to the controller backing block, and from that block to the physical chassis pose helper. It does not establish a complete arbitrary relocation transaction. In particular, velocity policy, wheel and suspension reconciliation, collision caches, safe cross-job scheduling, pause behavior, destination validation, and undo remain unresolved. This phase therefore adds a default-off observer for one ordinary stock recovery; it adds no teleport control or physics write.

The observer can record whether a nonzero controller apply flag reaches the existing controller update, how many consecutive controller updates see it, when a clear is observed, the controller and substep thread/timing context, raw chassis current/previous position words, selected opaque chassis words, and selected wheel words. It deliberately does not label unknown fields as velocity, suspension, or contacts.

## Exact target and evidence boundary

| Field | Value |
|---|---|
| File | `MRallye.exe` |
| Size | 3,121,214 bytes |
| SHA-256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| PE | PE32 / I386; timestamp `0x3C02695D` |
| ImageBase | `0x00400000` |
| Entry | VA `0x005C4602`, RVA `0x001C4602` |
| Static tool | Ghidra 12.1.4; isolated scratch at `D:\CodexScratch\A3j3` |

The SHA and size were rechecked against the available executable during this phase. `CONFIRMED_BY_EXE` means a direct exact-image instruction/dataflow observation. `CONFIRMED_BY_EXISTING_RESEARCH` refers to cited prior project evidence. `STATIC_INFERENCE` is an interpretation of the confirmed code path. `UNPROVEN` means the evidence does not answer the claim. There is no `CONFIRMED_BY_RUNTIME` result yet; the observer has not been exercised in-game.

All addresses below are VAs; RVAs are shown alongside them. Full machine-readable claims and provenance are in [`physics-transaction-map.json`](physics-transaction-map.json). The prior A3j.1 `CarN` attribution correction and A3j.2 Broker proof remain in [`broker-transform-routing.md`](broker-transform-routing.md); those source documents were not edited.

## Ownership: participant through physics state

The object roles are distinct:

```text
Race participant / PlayerType
  -> visual car actor
  -> per-car physics handle
       +0x14 -> controller
       +0x0C -> four wheel records, stride 0x188
       +0x08 -> actor link; actor +0x04 -> chassis body
  -> controller +0x74 -> shared reset backing P
  -> camera target (separate ownership path)
```

`0x0044A320` (RVA `0x0004A320`) assigns `Race/CarN/PlayerType` using the configured human participant count; its AttractMode branch forces that count to zero. In the supported one-human offline race, participant type 1 is the human candidate and type 2 is an AI candidate. `0x0043F020` (RVA `0x0003F020`) reads the participant key and creates/links the physics handle and four wheel records; `0x0043E4C0` (RVA `0x0003E4C0`) inserts the handle and registers collision entries; `0x0043ED00` (RVA `0x0003ED00`) attaches the wheel records. The observer enumerates live handles and logs `PlayerType`; it does not assume Car0 is always the player. `CONFIRMED_BY_EXE` for this routing; current in-process pointer lifetime and exact human selection still need the capture.

The handle, actor, chassis body, controller, wheel array, and camera must not be substituted for each other. The observer validates reciprocal controller/handle links and logs the full pointer tuple as an observation identity. Its local generation increments when that tuple changes. Identical allocator address reuse with an identical tuple cannot be distinguished without a native lifetime generation; the single-session procedure avoids scene changes and the report will retain that limitation.

## Stock recovery transaction

`ResetManager_Constructor_004CC5F0` (VA `0x004CC5F0`, RVA `0x000CC5F0`) binds separate participant paths for `Controller/CarN`, `CarN`, `Progress`, `LastMarker`, `LimitState`, `ResetNo`, `Finished`, and `Resetting`. The manager update is the vtable callback at VA `0x004CCAF0` (RVA `0x000CCAF0`), vtable `0x00691508` slot `+0x10`.

The update examines per-participant state and timer arrays. State value 1 reaches `0x004CD4A0` (RVA `0x000CD4A0`), which considers reset/limit state, the controller apply flag, the car data flag, and reset conditions before assigning a duration. State value 2 reaches `0x004CD550` (RVA `0x000CD550`), which uses a speed-magnitude threshold and a bounded 300-sample accumulation path before selecting another duration. The numeric states and several gates are not assigned semantic names here because their full game-level meaning is not established.

The update's per-participant flow is visible in `0x004CCAF0`: it iterates `manager+0x14`; tests the entry in the gate array at `+0x34` and a second Broker-backed state at `+0x28`; and, when those gates reject the entry, zeros manager entries at `+0x4C`, `+0x44`, and `+0x50` and clears the participant's `P+0x33`. Otherwise it evaluates the `+0x18` state and, when timer `+0x50[i]` is positive, decrements it, zeros `+0x44[i]`, and calls `0x004CD1B0`. That helper clears `P+0x33`; while the decremented timer remains active it also writes constants to `P+0x1C`, `P+0x20`, `P+0x24`, and `P+0x28`. If the decrement reaches zero, the update calls `0x004CCC90(i,1)` to publish the recovery transform. If the timer was already zero on entry, it takes the mode-0 clear path. Additional flags depend on comparisons with manager `+0x0C` and `+0x10`; their application-level labels remain unresolved. These writes are evidence of a managed recovery state machine, but the numeric states and backing words are not relabeled as driver controls without their consumers.

`0x004CCC90` (RVA `0x000CCC90`) is the transaction endpoint. Mode 0 clears `P+0x33`. Mode 1 selects a RaceLine sample from `Progress`/`LastMarker`, checks nearby participant positions through `0x004CD200` (RVA `0x000CD200`), prepares a transform, sets `P+0x33 = 1`, and copies 16 dwords into `P+0x34..P+0x73`. It writes four distinct vectors to the `CarN` race-output payload at `+0xBC`, `+0xCC`, `+0xDC`, and `+0xEC`, and increments `ResetNo`. Those four vectors and `ResetNo` are not the physics apply flag/matrix. `ResetNo` is confirmed as a camera discontinuity input at `0x004B7DE0` / `0x000B7DE0` and `0x004B82A0` / `0x000B82A0`; it is not a proven physics trigger.

The reset routine's collision-service call does not validate its selected point in this exact path: its queried boolean method at vtable `+0x18` returns false, so the hit-position and normal getters are skipped. The route point is therefore a recovery heuristic, not evidence of a general arbitrary-world ground or clearance query.

## Broker route and controller consumption

The A3j.2 correction resolves the prior path ambiguity. `0x004CCC90` resolves `Controller/CarN` through the `ControllerCarBrokerAccess` adapter `Q`; `Q+0x08` points to backing object `P`. The physics controller constructor at `0x004442A0` / RVA `0x000442A0` stores the same `P` at controller `O+0x74` (store at `0x004443FD` / RVA `0x000443FD`). This is a pointer-identity route, not an assumed copy between similarly shaped Broker values. `CONFIRMED_BY_EXE`; see the prior A3j.2 evidence JSON.

`PerCarControllerUpdate_00444AE0` (VA `0x00444AE0`, RVA `0x00044AE0) reads `P+0x33` and, when active, calls `ApplyControllerTransform_00444D50` at `0x00444BB8`. The helper copies the 64-byte block and calls `ResetChassisAndWheelState_00443740` (VA `0x00443740`, RVA `0x00043740), which calls `SetPhysicsBodyPose_0043A020` (VA `0x0043A020`, RVA `0x0003A020). The native controller consumer does not clear `P+0x33`; a reset-manager clear path does. The flag is a shared level, so one publication may be observed on multiple controller updates until another writer clears it. How many updates occur in a real reset is a runtime question.

## Chassis, wheels, collision, and motion state

`0x0043A020` writes body position at `+0xA0..+0xA8` and copies that position to prior-step fields `+0x144..+0x14C`; it also rebuilds orientation-derived data and updates additional body state. `0x00443740` then zeroes one dword at `+0x120` in each of four wheel records, calls `0x0043C310`, calls `0x004437B0(0)`, and conditionally enters `0x0043B800`.

The helper therefore performs real but bounded reset work. It does not directly set four wheel poses or expose a complete suspension/contact reconciliation contract. `0x0043C310` writes controller fields `+0x78`, `+0x24`, and `+0x28`; names and full effects are not established. `0x004437B0(0)` clears a chassis byte, one byte per wheel, and a controller byte. Its nonzero branch also clears wheel `+0x120` words and changes controller values, but stock relocation invokes mode 0. `0x0043B800` can call a collision service repeatedly and directly adjust chassis current position; this is not proof that every broadphase pair, contact manifold, or solver warm-start value is invalidated.

No confirmed code path establishes linear velocity, angular velocity, accumulated-force, wheel angular velocity, suspension, or contact semantics after recovery. The observer samples only documented current/previous position words, the controller flag/matrix, known reset bytes/word locations, and a bounded six-dword body region explicitly labeled `opaque`. It does not reinterpret those words as velocity. **Velocity policy is unknown.**

## Scheduler, pause, rendering, and lifecycle

The physics manager's per-car iteration at `0x0043F5D0` (RVA `0x0003F5D0) calls `0x00443820` (RVA `0x00043820). That per-car function calls the controller consumer at `0x00443827` before its five wheel-record routines and later control/surface helper. The manager's substep function `0x0043F890` (RVA `0x0003F890) runs two iterations. Each begins with `0x0043F650` (RVA `0x0003F650), which synchronizes selected body current values to prior-step storage; then executes the force/integration and collision-stage helpers; the tail `0x0043FE00` (RVA `0x0003FE00) runs before the loop decrement. `0x0043F2E0` calls the manager update `0x0043F310` and then `0x0043F890`, so that particular wrapper orders controller iteration before the two substeps. `CONFIRMED_BY_EXE` for this local call sequence.

The reset manager and physics manager's relative scheduler/job order, actual worker ownership, same-thread guarantees, whether pause stops either job, and whether a request can be queued through pause are **UNPROVEN**. The camera/freecam scheduler is not a certified physics write boundary. Rendering/visual actor synchronization after a stock reset is not proven by the chassis call chain. The observer records `QPC` and thread IDs at its sampled boundaries to help resolve timing; it does not change pause or scheduling.

## Destination, startup fallback, and Undo

There is no validated general arbitrary-XYZ terrain-height, surface-normal, vehicle-clearance, obstacle-overlap, or other-car footprint query established for this task. Visible geometry and physical collision geometry cannot be conflated. The stock reset line selector can avoid nearby participant positions but uses a race-line location and the reset service queried by it returns false in this path. It does not make the Freecam camera position a safe car position.

At race entry, `0x0048EB40` (RVA `0x0008EB40) publishes `Race/CarN/Transform` from `StartArea`; an optional `Race/Debug` path reads `Physics/Car0/Transform`. Physics-handle construction reaches the shared pose helper before registration completes. The exact key-to-body initialization route and order are not proven, so startup placement is also not ready as a safe fallback. No reversible native undo or rollback sequence is proven.

## Observer contract

The new observer is opt-in under `[PhysicsObserver] Enabled=1`; the example config keeps it off. It is exact-pristine gated and verifies the executable hash upstream, image base `0x00400000`, and surrounding instruction context before installing three five-byte call wrappers:

| Hook site | Target retained | Observation |
|---|---|---|
| VA `0x00443827`, RVA `0x00043827` | `0x00444AE0` | Controller snapshot before and after the native transform consumer; records apply-flag transitions and pointer identity |
| VA `0x0043F8AD`, RVA `0x0003F8AD` | `0x0043F650` | Substep boundary before/after previous-state synchronization |
| VA `0x0043F8ED`, RVA `0x0003F8ED` | `0x0043FE00` | Boundary before/after the final substep stage |

The Win32 x86 bridges preserve flags and general registers around observer calls and invoke each verified native target. The controller bridge uses a balanced private stack word only to carry the “before accepted this controller” token across the native call, then removes it before returning to the game. The native controller target has no stack parameters at this call site; its exact body was inspected to validate that it does not consume this observer token. The substep bridges retain the original ECX manager and argument stack. This is static ABI review, not a live hook run.

Snapshots and events are fixed-capacity (`8` controller identities, `64` events, a `24`-event substep window after a flag rise); callbacks do no file I/O or heap allocation. A process-session summary and bounded events are written on device release. The module is pinned so an unremovable pass-through bridge cannot point into unloaded code. Install/restore uses exact-byte ownership checks and thread suspension; any foreign byte change fails closed. `Enabled=0` by default. The observer makes no game-state writes and does not invoke recovery automatically. In-memory callsite wrappers are code instrumentation; they are restored at device release when safe.

The observer's measurements can show a controller flag reached the native consumer and correlate the observed body/wheel words with substep boundaries. It cannot establish unknown-field semantics, all contact/broadphase internals, an arbitrary destination query, or write safety. It also cannot distinguish same-address allocator reuse with an identical pointer tuple. Those remain explicit limitations, not implied passes.

## Single runtime handoff

Use the exact pristine executable and the A3j.3 renderer build. Set `[PhysicsObserver] Enabled=1` and `Trace.Enabled=1`. Start one supported offline France1 race, drive normally on clear road, invoke the game's ordinary recovery once, allow the car to settle, drive briefly, then exit normally so device release flushes the bounded session log. Do not pause, restart the race, change scenes, or use any teleport/experimental control during this capture. Supply the one `physics_probe` session JSONL from `MRRRenderer/logs`.

The capture passes observation if it includes the live participant/controller chain, at least one flag rise at the consumer, before/after native consumer snapshots, bounded substep events for that rise, and a later clear or an explicit explanation that the flag remained set through process exit. Thread IDs and QPC order must be internally consistent. A missing flag rise, invalid manager links, dropped events, or absent after snapshots is a capture failure and does not authorize writes. A successful capture can resolve only the observed normal-reset timing and sampled state changes; it cannot alone authorize arbitrary relocation.
