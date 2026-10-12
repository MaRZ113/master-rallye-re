# R-CAM1-A3j.1 — Relocation feasibility

## Decision

**Outcome B: partial native relocation helper, with the exact reset-to-controller edge still unproven.** The exact retail executable contains a chassis pose setter reachable from the per-car physics controller. It synchronizes previous-step position, clears selected per-wheel/controller/chassis fields, and can invoke a collision-service path. The stock reset routine separately publishes a matrix and flag into a `CarN` Broker object. Since the controller consumes `Controller/CarN`, current evidence does not establish that stock recovery activates the setter.

Even if the Broker edge is proven, this is not yet a complete relocation transaction. The wheel fields are unnamed; direct wheel poses, suspension/contact state, linear/angular velocities, broadphase invalidation, safe scheduler phase, and rollback are not fully established.

## Established

- `FUN_004CCC90` derives the stock recovery pose from the route line and writes 16 words at `CarData+0x34`, setting `CarData+0x33`.
- `FUN_00444AE0` consumes a similarly shaped flag/matrix from the distinct `Controller/CarN` data path and conditionally calls `FUN_00444D50`.
- `FUN_00444D50 -> FUN_00443740 -> FUN_0043A020` can apply a matrix to the physical chassis and synchronize its previous position.
- `FUN_00443740` affects four wheel records and related state, but the recovered body does not directly write wheel poses.
- `ResetNo` is a camera discontinuity marker in the identified consumer, not a proven physics trigger.
- Startup code writes `Race/CarN/Transform`, while physics construction calls the common pose helper before collision registration. This is a plausible startup seam, not a validated connection to the start-placement output.

## Open requirements

1. Prove whether reset's `CarN` object aliases or propagates to controller's `Controller/CarN` object.
2. Certify the human participant and live chassis pointer generation for pristine retail runtime.
3. Establish velocity, wheel/suspension, solver contact, broadphase, and registration state after relocation.
4. Establish a safe phase relative to reset-manager scheduling and both physics substeps.
5. Prove startup-placement key linkage and ordering if considering a startup-only fallback.

## Teleport decision

Do not add a Freecam teleport key, write `Race/CarN/Transform` or `Physics/Car0/Transform`, alter `ResetNo`, or invoke the helper from injected code. A visually correct chassis pose alone is not physical relocation proof.

The highest-value next step is static tracing of `ControllerCarBrokerAccess` and Broker key routing. Only if that cannot establish the data edge is a bounded read-only observation of a normal user-triggered stock reset warranted. No write-enabled runtime build is justified by the current result.

## Startup-only alternative

Race-start placement remains a candidate for a later controlled physics experiment because physics construction invokes the common pose helper before registration completes. It is not yet a supported fallback: the Broker key linkage and startup order are unproven, and the optional `Race/Debug` path has not been runtime-validated.
