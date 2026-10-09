# Pending controlled runtime validation

**RUNTIME_VALIDATION: NOT_PERFORMED.** No trusted active PCSX2/debugger session was available. No original ELF was patched. This phase did not start an emulator automation project.

Use ItalyS1 for one haybale and Turkey1 for one tumbleweed. Record canonical ELF/disc hashes, exact emulator version/configuration, course, entity source ID, frame and camera identity. Runtime pointers must be obtained from the live entity, owner+0c, manager prop vector and collision carrier; do not invent static body addresses.

1. Read-only break at19ff18/171c78: associate authored record with renamed entity, body pointer, mass+20, local inertia+28 and shape instance body+10. Record initial entity and body matrices, collision hull A/B and COM.
2. Before interaction, inspect body+00 pause, owner+2c/+30/+34/+38, first two201350 views, their+c0 positions and200550 predicate. Move camera/vehicle separately; test whether proximity retains initially paused state.
3. During one controlled strike, observe16e498 pair result and the paused flag/rest counter write. Capture contact point/normal, body pointers, solver-selected lambda entering25da08 and response commit23e968. This will close magnitude/material coefficient semantics for that case, not all vehicle physics.
4. Capture consecutive173b68/173cc8 invocations, actual halfstep,13-value state and force callback. Record real scheduler delta and effective Physics/RigidBody/MaxClampTime. Distinguish substep frequency from wall clock.
5. Break267f60/1e3f50 and265d18: compare published Broker key/matrix with all16 words in the same entity en3d+20..5c. Correlate with a labeled frame of that exact object.
6. Observe settling and one far->near sequence; verify the60-invocation decay, contact sleep and resumption. For tumbleweed, observe uncontacted intervals and any additional force accumulator writer before asserting wind or autonomous motion.

A screenshot supports visual identity; it cannot establish lambda, hull selection, friction or matrix producer. Runtime outputs/RAM/screenshots stay ignored. Only a future controlled capture can claim CONFIRMED_BY_RUNTIME.
