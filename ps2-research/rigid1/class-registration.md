# Class selection and construction

Canonical ELF string `gaAiRigidBody` is at **0x00472360**. The shared owner factory is **0x0015b190**; its prop branch calls **0x0019fcd0 at 0x0015d014**, following a 0x3c allocation. `factory_prop` in instruction-probes contains original words. Selection and construction are `CONFIRMED_BY_EXE`; authored matching records establish the bounded `CONFIRMED_BY_BOTH` connection.

Owner+0x08 points to vtable **0x00473820**. The GCC-style table has 8-byte adjustment/function pairs. Relevant callback offsets are:

| Function-pointer offset | Entry | Role |
|---|---|---|
| +0x0c | 0x001cfe90 | destructor |
| +0x14 | 0x001cfec0 | allocate a fresh default owner |
| +0x1c | 0x0019fdb0 | property schema/write direction |
| +0x24 | 0x0019fe98 | authored property reader |
| +0x2c | 0x001a0258 | update |
| +0x34 | 0x0019ff18 | entity initialization |

The AI is not the physical body. Initialization resolves the scene `gaPhysicsManager`, creates a separately allocated body through `171c78`, and stores its pointer at owner+0x0c. The constructor does not initialize that pointer. Missing manager resolution logs a hatch-priority warning and requests deferred entity removal through `21e4f0`; it is not a silently working body fallback.

Construction interns `RigidBody0`..`RigidBody62` name leads. Initialization selects `RigidBody%d` with global counter 0x0048e1d4 masked by 63 and increments the counter. This finite naming scheme is not an authored object cap or a duplicate-removal proof. Reset of that global and behavior of name collisions require runtime/lifecycle evidence.

`vtable-evidence.json` records original table target words. Function boundaries and bounded direct callers are in `elf-functions.json`; none are derived solely from neighboring strings.
