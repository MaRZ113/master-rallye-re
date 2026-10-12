# R-CAM1-A3j.3 — Teleport implementation decision

## Outcome: `READ_ONLY_PHYSICS_PROBE_READY`

Do not ship a write-enabled teleport prototype in this phase. The confirmed chain is valuable: stock recovery resolves `Controller/CarN`, its adapter points to the same backing object held at physics-controller `+0x74`, and the controller consumes the transform before reaching the chassis setter. That establishes the native routing for stock recovery. It does not establish the full physical invariants needed to turn a Freecam location into a safe arbitrary relocation.

The decision follows the task's write gate. Several required conditions fail closed:

- **Motion policy:** no verified linear/angular velocity, wheel angular velocity, force accumulator, or post-recovery policy. Unknown fields must not be zeroed by guessed offsets.
- **Wheel and suspension state:** the stock helper clears selected wheel fields but does not directly set wheel poses or prove suspension/contact consistency.
- **Collision state:** construction registration is known; a post-relocation broadphase/contact/manifold refresh transaction is not. The conditional collision path may adjust the chassis, which itself can diverge from previously synchronized state.
- **Safe phase and pause:** only local order inside the physics wrapper is established. Reset-manager versus physics-job order, owning thread, and paused behavior are unknown. The camera scheduler is not a valid substitute.
- **Destination:** there is no verified arbitrary position-to-physical-ground, normal, chassis clearance, or obstacle/other-car overlap query. Stock RaceLine selection is not a Freecam destination API, and the exact reset query service returns false in that path.
- **Race coherence and recovery:** `ResetNo` is a camera discontinuity marker, not a full race-state relocation contract; no safe Undo/rollback is proven.
- **Startup alternative:** `StartArea` and the optional `Physics/Car0/Transform` path are initialization clues only; their body input alias and order are not certified.

Therefore neither live arbitrary relocation nor startup-only placement is presently a safe fallback. The native Reset route is stronger as a controlled observation source, not as permission to inject a destination.

## Observer delivered

The opt-in `[PhysicsObserver] Enabled=1` probe is exact-pristine gated, default-off, bounded, and read-only for game data. It wraps the statically checked consumer and substep callsites, records raw validated snapshots and timing/thread IDs, and restores owned call bytes at device release when safe. It does not invoke Reset, alter the camera, change pause, or write physics/race memory. Its full scope and limits are documented in [`complete-relocation-analysis.md`](complete-relocation-analysis.md).

The observer is enough to answer the shortest remaining dynamic question: what the exact retail game does to the proven controller/body/wheel samples when the human triggers an ordinary recovery. It is not an arbitrary teleport validator. Unknown velocity/contact/broadphase field semantics stay unknown unless separately established from exact consumers.

## Runtime decision gate

After one successful capture, update only claims supported by that capture. A future write-enabled design would still require all of these before a road test: verified human owner and live generation; proven one-shot commit boundary; deliberate velocity policy; complete wheel/suspension/contact and broadphase coherence; verified destination ground/clearance and other-car rejection; race-state synchronization; safe rollback; exact build gating. Do not enable a teleport key until every item has evidence.

## Next step

Run the single normal stock-recovery capture specified in [`complete-relocation-analysis.md`](complete-relocation-analysis.md): exact pristine France1 offline race, observer enabled, normal driving, one stock recovery, short settling drive, normal exit, and provide the single bounded session JSONL. This is the only requested human action for A3j.3.
